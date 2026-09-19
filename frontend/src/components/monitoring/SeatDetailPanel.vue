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

      <div class="grid grid-cols-2 gap-2">
        <div class="rounded-lg border border-line bg-canvas/40 p-3">
          <p class="text-label text-fg-muted">하루 점유 시간</p>
          <p class="mt-1 text-xl font-semibold tabular-nums text-fg">{{ minutesText }}</p>
          <p class="mt-1 text-sm text-fg-muted">점유율 {{ stat?.occupied_pct ?? 0 }}%</p>
        </div>
        <div class="rounded-lg border border-line bg-canvas/40 p-3">
          <p class="text-label text-fg-muted">수업 참여</p>
          <p class="mt-1 text-xl font-semibold text-fg">{{ participation?.label ?? '확인 불가' }}</p>
          <p class="mt-1 text-sm text-fg-muted">{{ participation?.detail ?? '수업 시간표 또는 점유 기록이 필요합니다.' }}</p>
        </div>
      </div>

      <div v-if="participation?.hours?.length" class="flex flex-wrap gap-1.5">
        <span
          v-for="hour in participation.hours"
          :key="hour"
          class="rounded-md border border-state-occupied/40 bg-state-occupied/10 px-2 py-0.5 text-sm tabular-nums text-state-occupied"
        >{{ hour }}</span>
      </div>

      <div v-if="participation?.missedHours?.length" class="space-y-2">
        <p class="text-sm font-semibold text-fg">미참여 수업</p>
        <div class="flex flex-wrap gap-1.5">
          <span
            v-for="hour in participation.missedHours"
            :key="hour"
            class="rounded-md border border-state-alert/30 bg-state-alert/10 px-2 py-0.5 text-sm tabular-nums text-state-alert"
          >{{ hour }}</span>
        </div>
      </div>

    </template>

    <div v-else class="flex flex-1 flex-col items-center justify-center gap-2 text-center">
      <p class="text-lg font-semibold text-fg">좌석을 선택하세요</p>
      <p class="text-sm text-fg-muted">배치도의 좌석을 누르면 판정 결과와<br />하루 점유 시간, 수업 참여 여부를 볼 수 있습니다.</p>
    </div>
  </UiCard>
</template>

<script setup>
import { computed } from 'vue'
import UiCard from '@/components/ui/UiCard.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'

const props = defineProps({
  classroomId: { type: Number, required: true },
  seatId: { type: String, default: null },
  state: { type: String, default: 'unknown' },
  hasRecord: { type: Boolean, default: true },
  slot: { type: Object, default: null },
  isLatest: { type: Boolean, default: false },
  camera: { type: Object, default: null },
  stat: { type: Object, default: null },
  participation: { type: Object, default: null },
})

const minutesText = computed(() => {
  const m = props.stat?.occupied_minutes ?? 0
  const h = Math.floor(m / 60)
  const min = m % 60
  return h ? `${h}시간 ${min}분` : `${min}분`
})
</script>
