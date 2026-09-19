<template>
  <UiCard>
    <div class="flex items-end justify-between gap-gutter">
      <div class="min-w-0">
        <p class="text-label text-fg-muted">{{ label }}</p>
        <h2 class="mt-1 text-lg font-semibold text-fg">좌석 점유 현황</h2>
      </div>
      <p class="flex shrink-0 items-baseline gap-2 tabular-nums">
        <span class="text-metric-sm text-state-occupied">{{ occupied }}</span>
        <span class="text-xl text-fg-muted">/ {{ total }}석</span>
      </p>
    </div>

    <p v-if="unknown" class="mt-2 text-right text-sm text-state-unknown">판정 불가 {{ unknown }}석</p>

    <div
      class="mt-4 h-2 overflow-hidden rounded-full bg-line"
      role="progressbar"
      :aria-valuenow="pct"
      aria-valuemin="0"
      aria-valuemax="100"
      :aria-label="`${label} 점유율`"
    >
      <div class="h-full rounded-full bg-state-occupied transition-[width] duration-500" :style="{ width: `${pct}%` }" />
    </div>
  </UiCard>
</template>

<script setup>
import { computed } from 'vue'
import UiCard from '@/components/ui/UiCard.vue'

// 분석 한 번의 좌석 점유 요약. 점유는 점유색, 판정하지 못한 좌석 수는 판정 불가색으로만 쓴다.
const props = defineProps({
  label: { type: String, required: true }, // 'YOLO 분석' | 'YOLO+LLM 분석'
  occupied: { type: Number, required: true },
  total: { type: Number, required: true }, // 점유율의 분모(판정 가능한 좌석 수)
  unknown: { type: Number, default: 0 },
})

const pct = computed(() => (props.total ? Math.round((props.occupied / props.total) * 100) : 0))
</script>
