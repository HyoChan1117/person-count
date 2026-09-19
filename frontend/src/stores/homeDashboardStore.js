import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api'
import { isDemoMode } from '@/demo'
import { tickInfo } from '@/demo/state'

const SEEN_KEY = 'home-seen-alerts'
const ALERT_WINDOW_MS = 24 * 3600 * 1000
// 백엔드는 시계 기준 정각 단위(기본 600초)로 수집한다. 그 값은 서버 환경변수라 프런트에서 읽을 수 없어 설정값으로 둔다.
const COLLECT_SEC = Number(import.meta.env.VITE_COLLECT_INTERVAL_SEC) || 600
// seat-occupancy는 호출할 때마다 실시간 추론을 돌리므로 실서버에서는 길게 잡는다.
const REFRESH_MS = isDemoMode ? 5000 : 120000

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
  const now = ref(Date.now())
  const seen = ref(loadSeen())
  let clockTimer = null
  let pollTimer = null

  async function loadRoom(c) {
    // 한 좌석이 카메라 두 대의 seat_ids에 함께 들어 있을 수 있다(실제 301호: 4석). 좌석은 한 번만 센다.
    const ids = [...new Set(c.cameras.flatMap((cam) => cam.seat_ids ?? []))]
    const base = { id: c.id, name: c.name, total: ids.length }
    try {
      const { data } = await api.get(`/analysis/${c.id}/seat-occupancy`)
      const occ = new Set()
      const emp = new Set()
      data.cameras.forEach((cam) => {
        // 캡처/추론에 실패한 카메라는 서버가 좌석 전부를 empty로 돌려준다. 빈 좌석이 아니라 판정 불가로 남긴다.
        if (cam.error) return
        cam.occupied.forEach((s) => occ.add(s))
        cam.empty.forEach((s) => emp.add(s))
      })
      const seats = ids.map((id) => ({ id, state: occ.has(id) ? 'occupied' : emp.has(id) ? 'empty' : 'unknown' })).sort(numSort)
      return { ...base, ...tally(seats), seats, error: false }
    } catch {
      // 한 교실이 실패해도 나머지는 계속 보여준다(판정 불가로 표시)
      const seats = ids.map((id) => ({ id, state: 'unknown' })).sort(numSort)
      return { ...base, ...tally(seats), seats, error: true }
    }
  }

  async function loadPlace(p) {
    const [statusRes, detRes] = await Promise.all([
      api.get(`/face/places/${p.id}/patrol/status`),
      api.get(`/face/places/${p.id}/detections`),
    ])
    return {
      id: p.id,
      name: p.name,
      zones: (p.zones ?? []).map((z) => ({ id: z.id, name: z.name })),
      status: statusRes.data,
      detections: detRes.data.detections.map((d) => ({ ...d, key: `${p.id}:${d.id}`, placeId: p.id, placeName: p.name })),
    }
  }

  async function refresh() {
    try {
      const [cRes, pRes] = await Promise.all([api.get('/classrooms/'), api.get('/face/places')])
      if (isDemoMode) {
        rooms.value = await Promise.all(cRes.data.map(loadRoom))
      } else {
        const next = []
        for (const c of cRes.data) next.push(await loadRoom(c))
        rooms.value = next
      }
      places.value = await Promise.all(pRes.data.places.map(loadPlace))
      error.value = ''
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  function start() {
    refresh()
    clockTimer = setInterval(() => { now.value = Date.now() }, 1000)
    pollTimer = setInterval(refresh, REFRESH_MS)
  }

  function stop() {
    clearInterval(clockTimer)
    clearInterval(pollTimer)
    clockTimer = null
    pollTimer = null
  }

  function markSeen(key) {
    if (seen.value.has(key)) return
    seen.value = new Set([...seen.value, key])
    localStorage.setItem(SEEN_KEY, JSON.stringify([...seen.value].slice(-500)))
  }

  const totalJudgeable = computed(() => rooms.value.reduce((n, r) => n + r.judgeable, 0))
  const totalUnknown = computed(() => rooms.value.reduce((n, r) => n + r.unknown, 0))
  const totalOccupied = computed(() => rooms.value.reduce((n, r) => n + r.occupied, 0))
  // 판정 가능한 좌석이 하나도 없으면 0%가 아니라 null(표시는 "–")
  const occupancyPct = computed(() => (totalJudgeable.value ? Math.round((totalOccupied.value / totalJudgeable.value) * 100) : null))
  const activeRooms = computed(() => rooms.value.filter((r) => r.occupied > 0).length)

  const allDetections = computed(() => places.value.flatMap((p) => p.detections).sort((a, b) => (a.ts < b.ts ? 1 : -1)))
  const recentDetections = computed(() => allDetections.value.slice(0, 5))
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
  const primaryPatrol = computed(() => places.value.find((p) => p.status.running) ?? places.value[0] ?? null)

  // 마지막 수집 시각 / 다음 수집까지 남은 시간
  const collect = computed(() => {
    const t = now.value
    if (isDemoMode) {
      const intervalSec = Math.round(tickInfo.intervalMs / 1000)
      const nextInSec = Math.max(0, Math.ceil((tickInfo.last + tickInfo.intervalMs - t) / 1000))
      return { lastAt: new Date(tickInfo.last), nextInSec, intervalSec }
    }
    const d = new Date(t)
    const sinceMidnight = d.getHours() * 3600 + d.getMinutes() * 60 + d.getSeconds()
    const remainder = sinceMidnight % COLLECT_SEC
    return { lastAt: new Date(t - remainder * 1000), nextInSec: COLLECT_SEC - remainder, intervalSec: COLLECT_SEC }
  })

  return {
    rooms, places, loading, error,
    totalJudgeable, totalUnknown, totalOccupied, occupancyPct, activeRooms,
    recentDetections, unseenAlerts, primaryPatrol, collect,
    start, stop, refresh, markSeen, markAllSeen,
  }
})
