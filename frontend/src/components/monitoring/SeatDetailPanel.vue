<template>
  <UiCard class="flex h-full min-h-0 flex-col gap-card overflow-hidden">
    <template v-if="seatId">
      <div class="flex items-start justify-between gap-3">
        <div>
          <p class="text-label text-fg-muted">선택한 좌석</p>
          <p class="text-metric-sm tabular-nums text-fg">{{ seatId }}번</p>
        </div>
        <StatusBadge v-if="hasRecord" :status="state" size="lg" />
        <span v-else class="rounded-full border border-line px-3 py-1 text-sm font-medium text-fg-muted">기록 없음</span>
      </div>

      <dl class="grid grid-cols-[6rem_1fr] gap-x-3 gap-y-2 text-sm">
        <dt class="text-fg-muted">판정 결과</dt>
        <dd class="text-fg">{{ verdict }}</dd>
        <dt class="text-fg-muted">스냅샷 시각</dt>
        <dd class="tabular-nums text-fg">{{ slotLabel }}</dd>
        <dt class="text-fg-muted">담당 카메라</dt>
        <dd class="text-fg">{{ camera ? camera.name : '배정된 카메라 없음' }}</dd>
        <template v-if="stat">
          <dt class="text-fg-muted">하루 누적</dt>
          <dd class="tabular-nums text-fg">{{ minutesText }} · 점유율 {{ stat.occupied_pct }}%</dd>
        </template>
      </dl>

      <div class="flex min-h-0 flex-1 flex-col gap-2">
        <p class="text-label text-fg-muted">카메라 스냅샷 <span class="text-fg-muted/70">· 기본 블러, 클릭하면 공개</span></p>
        <div v-if="!canShowImage" class="flex flex-1 items-center justify-center rounded-lg border border-dashed border-line p-4 text-center text-sm text-fg-muted">
          이 시점의 이미지는 저장되지 않습니다.<br />가장 최근 스냅샷에서만 현재 화면을 볼 수 있습니다.
        </div>
        <div v-else-if="!camera" class="flex flex-1 items-center justify-center rounded-lg border border-dashed border-line p-4 text-sm text-fg-muted">배정된 카메라가 없습니다.</div>
        <div v-else-if="error" class="flex flex-1 items-center justify-center rounded-lg border border-dashed border-line p-4 text-sm text-fg-muted">{{ error }}</div>
        <div v-else-if="frame" class="relative">
          <BlurredImage :src="frame.src" :alt="`${seatId}번 좌석 카메라 스냅샷`" class="aspect-video w-full" />
          <svg :viewBox="`0 0 ${frame.width} ${frame.height}`" class="pointer-events-none absolute inset-0 h-full w-full" aria-hidden="true">
            <polygon v-if="polygon" :points="polygon" stroke-width="4" :class="polyClass" />
          </svg>
        </div>
        <div v-else class="flex flex-1 items-center justify-center rounded-lg border border-line text-sm text-fg-muted">불러오는 중...</div>
      </div>
    </template>

    <div v-else class="flex flex-1 flex-col items-center justify-center gap-2 text-center">
      <p class="text-lg font-semibold text-fg">좌석을 선택하세요</p>
      <p class="text-sm text-fg-muted">배치도의 좌석을 누르면 판정 결과와<br />카메라 스냅샷을 볼 수 있습니다.</p>
    </div>
  </UiCard>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import api from '@/api'
import { isDemoMode } from '@/demo'
import UiCard from '@/components/ui/UiCard.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import BlurredImage from '@/components/ui/BlurredImage.vue'
import { convexHull } from '@/utils/convexHull'

const props = defineProps({
  classroomId: { type: Number, required: true },
  seatId: { type: String, default: null },
  state: { type: String, default: 'unknown' },
  hasRecord: { type: Boolean, default: true }, // false면 그 시각 스냅샷이 없다("판정 불가"와 구분)
  slot: { type: Object, default: null }, // { ts, time }
  isLatest: { type: Boolean, default: false },
  camera: { type: Object, default: null }, // { camera_id, name, seat_lines }
  stat: { type: Object, default: null }, // occupancy-stats-daily의 좌석 항목
})

const VERDICTS = { occupied: '점유', empty: '빈 좌석', unknown: '판정 불가 (스냅샷에서 이 좌석을 판정하지 못함)' }
const verdict = computed(() => (props.hasRecord ? VERDICTS[props.state] ?? VERDICTS.unknown : '이 시각 기록 없음'))
const slotLabel = computed(() => (props.slot ? props.slot.ts.replace('T', ' ').slice(0, 16) : '–'))
const minutesText = computed(() => {
  const m = props.stat?.occupied_minutes ?? 0
  const h = Math.floor(m / 60)
  return h ? `${h}시간 ${m % 60}분` : `${m}분`
})

// 실서버는 과거 시점의 프레임을 저장하지 않는다. 데모는 슬롯 시각으로 프레임을 만들어 준다.
const canShowImage = computed(() => isDemoMode || props.isLatest)

const frame = ref(null)
const error = ref('')
let token = 0
let timer = null

async function loadFrame() {
  const my = ++token
  if (!props.seatId || !props.camera || !canShowImage.value) { frame.value = null; return }
  try {
    const { data } = await api.get(`/analysis/${props.classroomId}/frame/${props.camera.camera_id}`, {
      params: isDemoMode && props.slot ? { t: props.slot.ts } : {},
    })
    if (my !== token) return
    frame.value = { src: `data:image/jpeg;base64,${data.image}`, width: data.width, height: data.height }
    error.value = ''
  } catch (e) {
    if (my !== token) return
    frame.value = null
    error.value = e.response?.data?.detail ?? '카메라 화면을 가져오지 못했습니다.'
  }
}

// 자동 재생 중에는 슬롯이 계속 바뀌므로 잠깐 모아서 한 번만 요청한다
watch(() => [props.seatId, props.slot?.ts, props.camera?.camera_id, canShowImage.value], () => {
  clearTimeout(timer)
  timer = setTimeout(loadFrame, 200)
}, { immediate: true })

const polygon = computed(() => {
  const pts = props.camera?.seat_lines?.[props.seatId]
  if (!pts || pts.length < 4) return ''
  // 저장된 점 순서는 일정하지 않으므로 그릴 때만 볼록 껍질 순서로 정렬한다(저장 형식은 그대로)
  return convexHull(pts.slice(0, 4)).map((p) => p.join(',')).join(' ')
})

// 클래스는 Tailwind가 스캔할 수 있도록 리터럴로 적는다
const polyClass = computed(() => {
  if (props.state === 'occupied') return 'fill-state-occupied/25 stroke-state-occupied'
  if (props.state === 'empty') return 'fill-state-empty/15 stroke-state-empty'
  return 'fill-state-unknown/20 stroke-state-unknown'
})
</script>
