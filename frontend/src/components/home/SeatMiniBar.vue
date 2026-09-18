<template>
  <div class="grid gap-1" :style="{ gridTemplateColumns: `repeat(${cols}, minmax(0, 1fr))` }" role="img" :aria-label="`좌석 ${seats.length}석 상태`">
    <span
      v-for="s in seats"
      :key="s.id"
      class="h-2.5 rounded-sm"
      :class="COLORS[s.state] ?? COLORS.unknown"
      :title="`${s.id}번 · ${LABELS[s.state] ?? LABELS.unknown}`"
    />
  </div>
</template>

<script setup>
import { computed } from 'vue'

// 상태색 4가지 중 좌석에는 3가지만 쓴다. 클래스는 Tailwind가 스캔할 수 있게 리터럴로 적는다.
const COLORS = {
  occupied: 'bg-state-occupied',
  empty: 'bg-state-empty/50',
  unknown: 'bg-state-unknown',
}
const LABELS = { occupied: '점유', empty: '빈 좌석', unknown: '판정 불가' }

const props = defineProps({
  seats: { type: Array, required: true }, // [{ id, state: 'occupied'|'empty'|'unknown' }]
})

const cols = computed(() => Math.max(1, Math.min(12, props.seats.length)))
</script>
