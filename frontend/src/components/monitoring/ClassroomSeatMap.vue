<template>
  <div class="flex h-full min-h-0 flex-col gap-3">
    <svg :viewBox="`0 0 ${map.mapW} ${map.mapH}`" class="min-h-0 w-full flex-1" preserveAspectRatio="xMidYMid meet" role="group" aria-label="교실 배치도">
      <template v-for="o in map.objects" :key="o.id">
        <rect
          v-if="o.type === 'chair'"
          :x="o.x" :y="o.y" :width="o.w" :height="o.h" rx="4"
          class="fill-line/70"
        />
        <g v-else-if="o.type === 'cctv'">
          <rect :x="o.x" :y="o.y" :width="o.w" :height="o.h" rx="6" class="fill-card stroke-fg-muted/50" stroke-width="1.5" />
          <text :x="o.x + o.w / 2" :y="o.y + o.h / 2" text-anchor="middle" dominant-baseline="central" class="fill-fg-muted" font-size="14" font-weight="600">{{ o.label || 'CCTV' }}</text>
        </g>
        <g
          v-else-if="o.type === 'desk'"
          :class="isSeat(o) ? 'cursor-pointer' : ''"
          :role="isSeat(o) ? 'button' : undefined"
          :tabindex="isSeat(o) ? 0 : undefined"
          :aria-label="isSeat(o) ? `${o.label}번 좌석 ${LABELS[stateOf(o)]}` : undefined"
          @click="isSeat(o) && emit('select', o.label)"
          @keydown.enter.prevent="isSeat(o) && emit('select', o.label)"
        >
          <rect
            :x="o.x" :y="o.y" :width="o.w" :height="o.h" rx="6" stroke-width="2"
            class="transition-colors duration-300"
            :class="deskClass(o)"
          />
          <rect
            v-if="selectedId != null && isSeat(o) && o.label === selectedId"
            :x="o.x - 5" :y="o.y - 5" :width="o.w + 10" :height="o.h + 10" rx="9"
            class="fill-none stroke-fg" stroke-width="2.5"
          />
          <text :x="o.x + o.w / 2" :y="o.y + o.h / 2" text-anchor="middle" dominant-baseline="central" class="fill-fg" font-size="20" font-weight="600">{{ o.label }}</text>
        </g>
      </template>
    </svg>

    <ul class="flex shrink-0 items-center gap-5 text-sm text-fg-muted" aria-label="범례">
      <li class="flex items-center gap-2"><span class="h-3 w-3 rounded-sm bg-state-occupied" />점유</li>
      <li class="flex items-center gap-2"><span class="h-3 w-3 rounded-sm bg-state-empty" />빈 좌석</li>
      <li class="flex items-center gap-2"><span class="h-3 w-3 rounded-sm bg-state-unknown" />판정 불가</li>
    </ul>
  </div>
</template>

<script setup>
const LABELS = { occupied: '점유', empty: '빈 좌석', unknown: '판정 불가' }

const props = defineProps({
  map: { type: Object, required: true }, // 맵 에디터 저장 형식 { mapW, mapH, objects[] } (읽기 전용)
  seatStates: { type: Object, required: true }, // { 좌석ID: 'occupied'|'empty'|'unknown' }
  selectedId: { type: String, default: null },
})
const emit = defineEmits(['select'])

// 좌석 상태에 등록된 좌석의 책상만 상태색으로 그린다
const isSeat = (o) => o.label != null && o.label !== '' && o.label in props.seatStates
const stateOf = (o) => props.seatStates[o.label] ?? 'unknown'

// 클래스는 Tailwind가 스캔할 수 있도록 리터럴로 적는다
function deskClass(o) {
  if (!isSeat(o)) return 'fill-transparent stroke-line'
  const s = stateOf(o)
  if (s === 'occupied') return 'fill-state-occupied/25 stroke-state-occupied'
  if (s === 'empty') return 'fill-state-empty/10 stroke-state-empty'
  return 'fill-state-unknown/15 stroke-state-unknown'
}
</script>
