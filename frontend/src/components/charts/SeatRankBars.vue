<template>
  <div>
    <ol v-if="rowsToShow.length" class="flex flex-col gap-3" aria-label="좌석별 누적 점유 시간">
      <li v-for="(row, i) in rowsToShow" :key="row.seatId" class="grid grid-cols-[1.5rem_4.5rem_minmax(0,1fr)_7rem] items-center gap-3">
        <span class="text-sm tabular-nums text-fg-muted">{{ i + 1 }}</span>
        <span class="text-lg font-semibold tabular-nums text-fg">{{ row.seatId }}번</span>
        <div class="h-3 overflow-hidden rounded-full bg-line" role="presentation">
          <div class="h-full rounded-full bg-state-occupied transition-[width] duration-500" :style="{ width: `${row.barPct}%` }" />
        </div>
        <span class="text-right text-base tabular-nums text-fg-muted">{{ row.timeText }}</span>
      </li>
    </ol>
    <p v-else class="text-sm text-fg-muted">표시할 좌석이 없습니다.</p>
  </div>
</template>

<script setup>
import { computed } from 'vue'

// 좌석별 누적 점유 시간 순위(가로 막대). 막대 길이는 1위를 100%로 맞춘 상대 비율(barPct).
// rows: [{ seatId, occupiedMinutes, barPct, timeText }] — 이미 오래 점유한 순으로 정렬돼 들어온다.
const props = defineProps({
  rows: { type: Array, required: true },
  maxItems: { type: Number, default: 8 },
})

const rowsToShow = computed(() => props.rows.slice(0, props.maxItems))
</script>
