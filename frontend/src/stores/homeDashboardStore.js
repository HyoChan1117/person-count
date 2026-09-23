import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api'

const SEEN_KEY = 'home-seen-alerts'
const ALERT_WINDOW_MS = 24 * 3600 * 1000
// 백엔드는 시계 기준 정각 단위(기본 600초)로 수집한다. 그 값은 서버 환경변수라 프런트에서 읽을 수 없어 설정값으로 둔다.
const COLLECT_SEC = Number(import.meta.env.VITE_COLLECT_INTERVAL_SEC) || 600
// seat-occupancy는 호출할 때마다 실시간 추론을 돌리므로 실서버에서는 길게 잡는다.
const REFRESH_MS = 120000
const PATROL_REFRESH_MS = 1000
// 응답이 오지 않는 요청 하나가 갱신 전체를 붙잡지 않게 요청별로 제한한다(api.js 전역 timeout은 긴 분석 화면을 끊을 수 있어 쓰지 않는다).
// 카메라가 응답하지 않을 때 seat-occupancy 한 번이 약 15초 걸린 실측이 있어 그보다 넉넉하게 잡는다.
const TIMEOUT = { list: 10000, status: 10000, occupancy: 40000 }

function loadSeen() {
  try { return new Set(JSON.parse(localStorage.getItem(SEEN_KEY) || '[]')) } catch { return new Set() }
}

const numSort = (a, b) => Number(a.id) - Number(b.id)

// 점유율의 분모는 "판정 가능한 좌석"(점유 + 빈 좌석)이다. 판정 불가 좌석은 분모에서 빼고 따로 센다.
function tally(seats) {
  const count = (state) => seats.filter((s) => s.state === state).length
  const occupied = count('occupied')
  const empty = count('empty')
  return { occupied, empty, unknown: count('unknown'), judgeable: occupied + empty }
}

export const useHomeDashboardStore = defineStore('homeDashboard', () => {
  const rooms = ref([])
  const places = ref([])
  const loading = ref(true)
  const error = ref('')
  // 마지막으로 모든 요청이 성공한 시각(ms)과 직전 갱신의 실패 여부. 첫 성공 이후 갱신이 실패하면 stale.
  const lastSuccessAt = ref(null)
  const refreshFailed = ref(false)
  const stale = computed(() => refreshFailed.value && lastSuccessAt.value != null)
  const now = ref(Date.now())
  const seen = ref(loadSeen())
  let clockTimer = null
  let pollTimer = null
  let patrolTimer = null

  // 배치도는 맵 에디터에서 저장할 때만 바뀌므로 교실당 한 번만 읽고 캐시한다.
  // 배치도가 없는 교실(404)은 null로 기억해 매번 다시 찾지 않는다.
  const mapCache = new Map()
  async function loadMap(classroomId) {
    if (mapCache.has(classroomId)) return mapCache.get(classroomId)
    let map = null
    try {
      const { data } = await api.get(`/classrooms/${classroomId}/map-data`, { timeout: TIMEOUT.list })
      map = data?.objects?.length ? data : null
    } catch {
      map = null
    }
    mapCache.set(classroomId, map)
    return map
  }

  // seat-occupancy 응답을 화면용 좌석 상태로 바꾼다.
  // 캡처/추론에 실패한 카메라는 서버가 좌석 전부를 empty로 돌려주므로, 빈 좌석이 아니라 판정 불가로 남긴다.
  function seatsFrom(ids, data) {
    const occ = new Set()
    const emp = new Set()
    ;(data.cameras ?? []).forEach((cam) => {
      if (cam.error) return
      cam.occupied.forEach((sid) => occ.add(sid))
      cam.empty.forEach((sid) => emp.add(sid))
    })
    return ids.map((id) => ({ id, state: occ.has(id) ? 'occupied' : emp.has(id) ? 'empty' : 'unknown' })).sort(numSort)
  }

  async function loadRoom(c) {
    // 한 좌석이 카메라 두 대의 seat_ids에 함께 들어 있을 수 있다(실제 301호: 4석). 좌석은 한 번만 센다.
    const ids = [...new Set(c.cameras.flatMap((cam) => {
      const seatIds = cam.seat_ids?.length ? cam.seat_ids : Object.keys(cam.seat_lines ?? {})
      return seatIds.map(String)
    }))]
    const base = { id: c.id, name: c.name, total: ids.length, map: await loadMap(c.id) }
    try {
      const { data } = await api.get(`/analysis/${c.id}/seat-occupancy`, { timeout: TIMEOUT.occupancy })
      const seats = seatsFrom(ids, data)
      return { ...base, ...tally(seats), seats, error: false }
    } catch {
      // 한 교실이 실패해도 나머지는 계속 보여준다(판정 불가로 표시)
      const seats = ids.map((id) => ({ id, state: 'unknown' })).sort(numSort)
      return { ...base, ...tally(seats), seats, error: true }
    }
  }

  // 순찰을 멈추면 카메라를 세워 둘 자리: 자리 영역이 없는 마지막 구역(초기 고정 구역)
  const homeZoneId = (p) => [...(p.zones ?? [])].reverse().find((z) => !(z.rois?.length))?.id ?? null

  async function loadPlace(p) {
    const [statusRes, detRes] = await Promise.all([
      api.get(`/face/places/${p.id}/patrol/status`, { timeout: TIMEOUT.status }),
      api.get(`/face/places/${p.id}/detections`, { timeout: TIMEOUT.status }),
    ])
    return {
      id: p.id,
      name: p.name,
      // rois 개수까지 실어야 단계 추정이 "자리 영역 없는 구역(지나가는 구역)"을 구분할 수 있다
      zones: (p.zones ?? []).map((z) => ({ id: z.id, name: z.name, rois: z.rois ?? [] })),
      // 10분 주기 정기 순찰 대상인지. 설정이 없던 장소는 켜져 있던 것으로 본다.
      autoPatrol: p.auto_patrol ?? true,
      homeZoneId: homeZoneId(p),
      hasCamera: !!p.camera?.ip,
      status: statusRes.data,
      detections: detRes.data.detections.map((d) => ({ ...d, key: `${p.id}:${d.id}`, placeId: p.id, placeName: p.name })),
    }
  }

  // ── 홈에서 하는 순찰 조작 ────────────────────────────────────────────────
  // 얼굴 인식 모니터링 화면의 버튼과 같은 동작을 한다(중지하면 초기 고정 구역으로 되돌림).
  const patrolBusy = ref(false)

  const patchPlace = (placeId, fields) => {
    places.value = places.value.map((p) => (p.id === placeId ? { ...p, ...fields } : p))
  }

  async function returnHome(place) {
    if (!place.homeZoneId) return   // 되돌아갈 고정 구역이 없는 장소는 그대로 둔다
    await api.post(`/face/places/${place.id}/zones/${place.homeZoneId}/goto`, null, { timeout: TIMEOUT.status })
  }

  async function stopPatrol(place) {
    await api.post(`/face/places/${place.id}/patrol/stop`, null, { timeout: TIMEOUT.status })
    await returnHome(place)
  }

  // 조작은 실패를 삼키지 않는다. 호출한 화면이 사용자에게 알린다.
  async function runPatrolAction(fn) {
    if (patrolBusy.value) return
    patrolBusy.value = true
    try {
      await fn()
      await refreshPatrols()
    } finally {
      patrolBusy.value = false
    }
  }

  const startPatrol = (place) => runPatrolAction(() =>
    api.post(`/face/places/${place.id}/patrol/start`, {}, { timeout: TIMEOUT.status }))

  const stopPatrolAction = (place) => runPatrolAction(() => stopPatrol(place))

  const setAutoPatrol = (place, enabled) => runPatrolAction(async () => {
    await api.put(`/face/places/${place.id}/patrol/auto`, { enabled }, { timeout: TIMEOUT.status })
    patchPlace(place.id, { autoPatrol: enabled })
    // 끄는 순간 돌고 있는 순찰이 있으면 그것까지 멈춘다
    if (!enabled && place.status?.running) await stopPatrol(place)
  })

  // 갱신은 겹치지 않는다: 실서버는 교실을 차례로 추론하느라 한 번이 오래 걸릴 수 있어, 진행 중이면 다음 주기를 건너뛴다.
  // 일부 요청이 실패해도 나머지는 갱신하고, 실패한 부분은 이전 값을 유지한 채 stale로 표시한다.
  let patrolRefreshing = false
  async function refreshPatrols() {
    if (patrolRefreshing || !places.value.length) return
    patrolRefreshing = true
    try {
      const settled = await Promise.allSettled(places.value.map(async (p) => {
        const statusRes = await api.get(`/face/places/${p.id}/patrol/status`, { timeout: TIMEOUT.status })
        let detections = p.detections
        if ((statusRes.data.detections ?? 0) !== (p.status?.detections ?? 0)) {
          const detRes = await api.get(`/face/places/${p.id}/detections`, { timeout: TIMEOUT.status })
          detections = detRes.data.detections.map((d) => ({ ...d, key: `${p.id}:${d.id}`, placeId: p.id, placeName: p.name }))
        }
        return { ...p, status: statusRes.data, detections }
      }))
      places.value = places.value.map((p, i) => settled[i]?.status === 'fulfilled' ? settled[i].value : p)
    } finally {
      patrolRefreshing = false
    }
  }

  let refreshing = false
  async function refresh() {
    if (refreshing) return
    refreshing = true
    let failed = false
    let firstError = ''
    const fail = (reason) => { failed = true; firstError ||= reason?.response?.data?.detail ?? reason?.message ?? '알 수 없는 오류' }
    try {
      const [cRes, pRes] = await Promise.allSettled([
        api.get('/classrooms/', { timeout: TIMEOUT.list }),
        api.get('/face/places', { timeout: TIMEOUT.list }),
      ])

      if (cRes.status === 'fulfilled') {
        const next = []
        for (const c of cRes.value.data) next.push(await loadRoom(c))
        rooms.value = next
      } else {
        fail(cRes.reason)
      }

      if (pRes.status === 'fulfilled') {
        const list = pRes.value.data.places
        const settled = await Promise.allSettled(list.map(loadPlace))
        const previous = new Map(places.value.map((p) => [p.id, p]))
        const next = []
        settled.forEach((r, i) => {
          if (r.status === 'fulfilled') { next.push(r.value); return }
          fail(r.reason)
          const old = previous.get(list[i].id)
          if (old) next.push(old)   // 이 장소만 이전 값을 유지한다
        })
        places.value = next
      } else {
        fail(pRes.reason)
      }

      error.value = failed ? firstError : ''
      refreshFailed.value = failed
      if (!failed) lastSuccessAt.value = Date.now()
    } finally {
      refreshing = false
      loading.value = false
    }
  }

  function start() {
    refresh()
    clockTimer = setInterval(() => { now.value = Date.now() }, 1000)
    pollTimer = setInterval(refresh, REFRESH_MS)
    patrolTimer = setInterval(refreshPatrols, PATROL_REFRESH_MS)
  }

  function stop() {
    clearInterval(clockTimer)
    clearInterval(pollTimer)
    clearInterval(patrolTimer)
    clockTimer = null
    pollTimer = null
    patrolTimer = null
  }

  function markSeen(key) {
    if (seen.value.has(key)) return
    seen.value = new Set([...seen.value, key])
    localStorage.setItem(SEEN_KEY, JSON.stringify([...seen.value].slice(-500)))
  }

  // ── 교실 하나만 다시 분석 ────────────────────────────────────────────────
  // 카드의 '분석' 버튼. seat-occupancy는 호출할 때마다 실시간 추론을 돌리므로 교실별로 따로 돌린다.
  const analyzingRooms = ref(new Set())

  async function analyzeRoom(roomId) {
    const room = rooms.value.find((r) => r.id === roomId)
    if (!room || analyzingRooms.value.has(roomId)) return
    analyzingRooms.value = new Set([...analyzingRooms.value, roomId])
    try {
      const ids = room.seats.map((seat) => seat.id)
      const { data } = await api.get(`/analysis/${roomId}/seat-occupancy`, { timeout: TIMEOUT.occupancy })
      const seats = seatsFrom(ids, data)
      rooms.value = rooms.value.map((r) => (r.id === roomId ? { ...r, ...tally(seats), seats, error: false } : r))
    } finally {
      const next = new Set(analyzingRooms.value)
      next.delete(roomId)
      analyzingRooms.value = next
    }
  }

  const totalJudgeable = computed(() => rooms.value.reduce((n, r) => n + r.judgeable, 0))
  const totalUnknown = computed(() => rooms.value.reduce((n, r) => n + r.unknown, 0))
  const totalOccupied = computed(() => rooms.value.reduce((n, r) => n + r.occupied, 0))
  // 판정 가능한 좌석이 하나도 없으면 0%가 아니라 null(표시는 "–")
  const occupancyPct = computed(() => (totalJudgeable.value ? Math.round((totalOccupied.value / totalJudgeable.value) * 100) : null))
  const activeRooms = computed(() => rooms.value.filter((r) => r.occupied > 0).length)

  // 홈 우측 두 패널(순찰 상태·최근 감지 로그)이 함께 따라가는 교실 선택. null이면 전체.
  const selectedPlaceId = ref(null)
  const selectPlace = (id) => { selectedPlaceId.value = id }
  const selectedPlace = computed(() => places.value.find((p) => p.id === selectedPlaceId.value) ?? null)

  const allDetections = computed(() => places.value.flatMap((p) => p.detections).sort((a, b) => (a.ts < b.ts ? 1 : -1)))
  const recentDetections = computed(() => {
    const rows = selectedPlace.value ? selectedPlace.value.detections : allDetections.value
    return [...rows].sort((a, b) => (a.ts < b.ts ? 1 : -1)).slice(0, 5)
  })
  // 미확인 경고 = 최근 24시간의 미등록 인물 감지 중 사진을 열어보지 않은 것.
  // 화면에서 사진을 열 수 있는 건 최근 5건뿐이라, 기간 제한과 "모두 확인"이 없으면 오래된 감지가 영원히 남아 숫자가 줄지 않는다.
  const unseenList = computed(() =>
    allDetections.value.filter((d) => d.name == null && !seen.value.has(d.key) && now.value - new Date(d.ts).getTime() <= ALERT_WINDOW_MS),
  )
  const unseenAlerts = computed(() => unseenList.value.length)

  function markAllSeen() {
    if (!unseenList.value.length) return
    seen.value = new Set([...seen.value, ...unseenList.value.map((d) => d.key)])
    try { localStorage.setItem(SEEN_KEY, JSON.stringify([...seen.value].slice(-500))) } catch { /* 저장 실패해도 화면 상태는 유지 */ }
  }
  // 전체를 보고 있을 때는 순찰 중인 장소를(없으면 첫 장소를) 대신 보여 준다
  const primaryPatrol = computed(() => places.value.find((p) => p.status.running) ?? places.value[0] ?? null)
  const patrolPlace = computed(() => selectedPlace.value ?? primaryPatrol.value)

  // 마지막 수집 시각 / 다음 수집까지 남은 시간
  const collect = computed(() => {
    const t = now.value
    const d = new Date(t)
    const sinceMidnight = d.getHours() * 3600 + d.getMinutes() * 60 + d.getSeconds()
    const remainder = sinceMidnight % COLLECT_SEC
    return { lastAt: new Date(t - remainder * 1000), nextInSec: COLLECT_SEC - remainder, intervalSec: COLLECT_SEC }
  })

  return {
    rooms, places, loading, error, stale, lastSuccessAt,
    totalJudgeable, totalUnknown, totalOccupied, occupancyPct, activeRooms,
    recentDetections, unseenAlerts, primaryPatrol, patrolPlace, selectedPlaceId, collect, patrolBusy, analyzingRooms,
    start, stop, refresh, markSeen, markAllSeen, analyzeRoom, selectPlace,
    startPatrol, stopPatrol: stopPatrolAction, setAutoPatrol,
  }
})
