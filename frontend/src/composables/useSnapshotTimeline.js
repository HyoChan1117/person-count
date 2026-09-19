import { ref, computed, watch } from 'vue'
import api from '@/api'
import { seatStatesFor, hasSnapshotRecord } from '@/utils/seatSnapshot'

const STEP_MS = 1500 // 자동 재생: 1.5초에 한 칸
const IDLE_RESUME_MS = 15000 // 슬라이더를 직접 움직인 뒤 이 시간 동안 조작이 없으면 자동 재생 재개

// 실서버 백엔드에는 10분 단위 스냅샷 엔드포인트가 없다(정각 스냅샷만 제공). 한 번 404를 받으면 다시 묻지 않는다.
let snapshotsUnsupported = false

// 교실의 하루치 스냅샷을 슬롯 목록으로 만들고, 슬라이더 위치/자동 재생 상태를 관리한다.
// 슬롯 간격은 데이터에서 유도한다(데모 10분, 실서버 폴백 60분).
export function useSnapshotTimeline({ classroomId, dateStr, seatIds }) {
  const slots = ref([]) // [{ ts, time, seats: { id: 'occupied'|'empty' } | null }]
  const intervalMin = ref(10)
  const loading = ref(false)
  const index = ref(0)
  const playing = ref(true)
  let manualPause = false
  let stepTimer = null
  let resumeTimer = null
  let loadToken = 0

  const current = computed(() => slots.value[index.value] ?? null)
  const isLatest = computed(() => slots.value.length > 0 && index.value === slots.value.length - 1)

  // 현재 슬롯의 좌석별 상태. 그 시각 기록이 없거나 스냅샷에 빠진 좌석은 판정 불가.
  const seatStates = computed(() => seatStatesFor(current.value?.seats, seatIds.value))
  // 스냅샷 자체가 없는 시각(미래 시각, 수집 누락)은 "판정 불가"가 아니라 "기록 없음"으로 보여 주기 위한 플래그
  const hasRecord = computed(() => hasSnapshotRecord(current.value))

  function fromHourly(hours, date) {
    return hours.map((h) => ({
      ts: `${date}T${h.time}:00`,
      time: h.time,
      seats: h.occupied == null
        ? null
        : Object.fromEntries(seatIds.value.map((sid) => [sid, (h.seats ?? []).includes(sid) ? 'occupied' : 'empty'])),
    }))
  }

  async function load() {
    const token = ++loadToken
    const id = classroomId.value
    const date = dateStr.value
    loading.value = true
    let next = []
    let interval = 10
    try {
      if (!snapshotsUnsupported) {
        try {
          const { data } = await api.get(`/analysis/${id}/occupancy-snapshots`, { params: { date } })
          next = data.snapshots.map((s) => ({ ts: s.ts, time: s.ts.slice(11, 16), seats: s.seats }))
          interval = data.interval_minutes || 10
        } catch (e) {
          if (e.response?.status !== 404) throw e
          snapshotsUnsupported = true
        }
      }
      if (snapshotsUnsupported) {
        const { data } = await api.get(`/analysis/${id}/occupancy-hourly`, { params: { date } })
        next = fromHourly(data.hours, date)
        interval = 60
      }
    } catch {
      next = []
    }
    if (token !== loadToken) return // 더 최근 요청이 있으면 버린다
    slots.value = next
    intervalMin.value = interval
    index.value = 0
    loading.value = false
  }

  function scheduleResume() {
    clearTimeout(resumeTimer)
    resumeTimer = setTimeout(() => { playing.value = true }, IDLE_RESUME_MS)
  }

  // 사용자가 슬라이더를 직접 움직였을 때
  function scrub(i) {
    index.value = Math.max(0, Math.min(slots.value.length - 1, i))
    if (manualPause) return
    playing.value = false
    scheduleResume()
  }

  function togglePlay() {
    clearTimeout(resumeTimer)
    if (playing.value) {
      manualPause = true
      playing.value = false
    } else {
      manualPause = false
      playing.value = true
    }
  }

  function start() {
    stop()
    stepTimer = setInterval(() => {
      if (document.hidden || !playing.value || slots.value.length < 2) return
      index.value = (index.value + 1) % slots.value.length
    }, STEP_MS)
  }

  function stop() {
    clearInterval(stepTimer)
    clearTimeout(resumeTimer)
    stepTimer = null
    resumeTimer = null
  }

  watch(dateStr, load)

  return { slots, index, current, isLatest, seatStates, hasRecord, playing, loading, intervalMin, load, scrub, togglePlay, start, stop }
}
