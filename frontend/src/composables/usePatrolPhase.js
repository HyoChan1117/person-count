import { ref, computed, watch, onUnmounted } from 'vue'

export const PHASE_STEPS = [
  { key: 'move', label: '이동' },
  { key: 'settle', label: '대기' },
  { key: 'shoot', label: '촬영' },
  { key: 'analyze', label: '분석' },
]

// 실서버 patrol.status()에는 단계 필드가 없다. 대기(안정화)·촬영 시간을 참고한
// 경과 시간 경계(초): 이동 → 대기 → 촬영 → 분석. 구역이 바뀔 때마다 처음부터 다시 잰다.
const ESTIMATE_BOUNDS = [2.5, 7, 9.5]

// 순찰 상태와 구역 목록으로 현재 단계를 계산한다.
// 상태 응답에 phase가 있으면 그 값을 쓰고(estimated=false), 없으면 경과 시간으로 추정한다(estimated=true).
export function usePatrolPhase(status, zones) {
  const now = ref(Date.now())
  const zoneChangedAt = ref(Date.now())
  let timer = null

  watch(() => [status.value?.zone_index, status.value?.running], () => { zoneChangedAt.value = Date.now() })

  watch(() => status.value?.running, (running) => {
    clearInterval(timer)
    timer = null
    if (running) timer = setInterval(() => { now.value = Date.now() }, 500)
  }, { immediate: true })

  onUnmounted(() => clearInterval(timer))

  const currentZone = computed(() => (zones.value ?? [])[(status.value?.zone_index ?? 0) - 1] ?? null)
  const nextZone = computed(() => (zones.value ?? [])[status.value?.zone_index ?? 0] ?? null)
  // 자리 영역(ROI)이 없는 구역은 인식 없이 이동만 하고 지나간다
  const passThrough = computed(() => !!currentZone.value && !(currentZone.value.rois?.length))

  const estimated = computed(() => !status.value?.phase)

  const phase = computed(() => {
    if (!status.value?.running) return null
    if (status.value.phase) return status.value.phase
    if (passThrough.value) return 'move'
    const elapsed = (now.value - zoneChangedAt.value) / 1000
    const i = ESTIMATE_BOUNDS.findIndex((b) => elapsed < b)
    return PHASE_STEPS[i === -1 ? 3 : i].key
  })

  return { phase, estimated, currentZone, nextZone, passThrough }
}
