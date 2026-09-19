<template>
  <div>
    <!-- 그 날짜에 수업 시간이 하나도 없으면(주말이거나 시간표가 비어 있음) 막대가 비어 고장처럼 보인다. 이유를 알려 준다 -->
    <div v-if="!anyScheduled" role="status" class="flex h-44 flex-col items-center justify-center gap-1 rounded-md border border-dashed border-line px-6 text-center">
      <p class="text-base font-medium text-fg">이 날짜에는 수업 시간이 없습니다</p>
      <p class="text-sm text-fg-muted">시간표는 월~금 기준입니다. 평일인데도 비어 있다면 상단의 '시간표 설정'에서 수업 시간을 등록하세요.</p>
    </div>

    <ul v-else class="flex h-44 items-stretch gap-2" aria-label="시간대별 점유 좌석 수">
      <li v-for="h in hours" :key="h.hour" class="flex min-w-0 flex-1 flex-col gap-2">
        <button
          type="button"
          :disabled="!selectable(h)"
          :aria-pressed="selectedHour === h.hour"
          :title="titleOf(h)"
          class="relative min-h-0 flex-1 overflow-hidden rounded-md transition-shadow focus-visible:outline focus-visible:outline-2 focus-visible:outline-fg-muted"
          :class="[trackClass(h), selectedHour === h.hour ? 'ring-2 ring-fg' : selectable(h) ? 'hover:ring-1 hover:ring-fg-muted' : '', selectable(h) ? 'cursor-pointer' : 'cursor-not-allowed']"
          @click="emit('select', h.hour)"
        >
          <span v-if="hasData(h)" class="absolute inset-x-0 bottom-0 bg-state-occupied" :style="{ height: fillHeight(h) }" />
        </button>
        <span class="text-center text-xs tabular-nums" :class="selectedHour === h.hour ? 'font-semibold text-fg' : 'text-fg-muted'">{{ h.hour }}</span>
      </li>
    </ul>

    <ul v-if="anyScheduled" class="mt-4 flex flex-wrap items-center gap-x-5 gap-y-1 text-sm text-fg-muted" aria-label="범례">
      <li class="flex items-center gap-2"><span class="h-3 w-3 rounded-sm bg-state-occupied" />점유 좌석</li>
      <li class="flex items-center gap-2"><span class="h-3 w-3 rounded-sm bg-state-empty/20" />빈 좌석</li>
      <li class="flex items-center gap-2"><span class="h-3 w-3 rounded-sm border border-dashed border-fg-muted/40" />기록 없음</li>
      <li class="flex items-center gap-2"><span class="h-3 w-3 rounded-sm bg-line/30" />수업 없음</li>
    </ul>
  </div>
</template>

<script setup>
// 정각별 점유 좌석 수 막대 차트. 색은 토큰만 쓰고, 테마가 바뀌어도 다시 그릴 필요가 없도록 HTML/CSS로 그린다.
// hours: [{ hour, time, scheduled, occupied|null, total, seats[] }]
import { computed } from 'vue'

const props = defineProps({
  hours: { type: Array, required: true },
  selectedHour: { type: Number, default: null },
})
const emit = defineEmits(['select'])

const anyScheduled = computed(() => props.hours.some((h) => h.scheduled))

const hasData = (h) => h.scheduled && h.occupied !== null
const selectable = (h) => hasData(h)

// 클래스는 Tailwind가 스캔할 수 있도록 리터럴로 적는다
function trackClass(h) {
  if (!h.scheduled) return 'bg-line/30'
  if (h.occupied === null) return 'border border-dashed border-fg-muted/40'
  return 'bg-state-empty/20'
}

// 점유가 0보다 크면 아주 낮은 비율도 보이도록 최소 4px
function fillHeight(h) {
  if (!h.occupied) return '0'
  const ratio = h.total ? h.occupied / h.total : 0
  return `max(${(ratio * 100).toFixed(1)}%, 4px)`
}

function titleOf(h) {
  if (!h.scheduled) return '수업 없음'
  if (h.occupied === null) return '기록 없음'
  return `${h.time} · 점유 ${h.occupied}/${h.total}석`
}
</script>
