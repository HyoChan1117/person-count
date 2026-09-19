<template>
  <div class="relative flex h-full min-h-0 flex-col gap-3">
    <svg :viewBox="`0 0 ${map.mapW} ${map.mapH}`" class="min-h-0 w-full flex-1" preserveAspectRatio="xMidYMid meet" role="group" aria-label="교실 배치도">
      <template v-for="o in map.objects" :key="o.id">
        <g v-if="o.type === 'chair'" :transform="objectTransform(o)">
          <rect
            :x="o.x" :y="o.y" :width="o.w" :height="o.h" rx="8"
            fill="#e2e8f1"
          />
        </g>
        <g v-else-if="o.type === 'cctv'">
          <rect :x="o.x" :y="o.y" :width="o.w" :height="o.h" rx="12" fill="#ffffff" stroke="#a9b3c2" stroke-width="3" />
          <text :x="o.x + o.w / 2" :y="o.y + o.h / 2" text-anchor="middle" dominant-baseline="central" fill="#53647f" :font-size="cctvFontSize(o)" font-weight="700">{{ o.label || 'CCTV' }}</text>
        </g>
        <g
          v-else-if="o.type === 'desk'"
          :transform="objectTransform(o)"
          :class="isSeat(o) ? 'cursor-pointer' : ''"
          :role="isSeat(o) ? 'button' : undefined"
          :tabindex="isSeat(o) ? 0 : undefined"
          :aria-label="isSeat(o) ? `${o.label}번 좌석 ${hasRecord ? LABELS[stateOf(o)] : '기록 없음'}` : undefined"
          @click="isSeat(o) && emit('select', o.label)"
          @keydown.enter.prevent="isSeat(o) && emit('select', o.label)"
        >
          <rect
            :x="o.x" :y="o.y" :width="o.w" :height="o.h" rx="10" stroke-width="3"
            :fill="deskFill(o)"
            :stroke="deskStroke(o)"
          />
          <rect
            v-if="selectedId != null && isSeat(o) && o.label === selectedId"
            :x="o.x - 5" :y="o.y - 5" :width="o.w + 10" :height="o.h + 10" rx="13"
            class="fill-none stroke-fg" stroke-width="2.5"
          />
          <text :x="o.x + o.w / 2" :y="o.y + o.h / 2" text-anchor="middle" dominant-baseline="central" fill="#061735" :font-size="deskFontSize(o)" font-weight="700">{{ o.label }}</text>
        </g>
      </template>
    </svg>
  </div>
</template>

<script setup>
const LABELS = { occupied: '점유', empty: '빈 좌석', unknown: '판정 불가' }

const props = defineProps({
  map: { type: Object, required: true }, // 맵 에디터 저장 형식 { mapW, mapH, objects[] } (읽기 전용)
  seatStates: { type: Object, required: true }, // { 좌석ID: 'occupied'|'empty'|'unknown' }
  selectedId: { type: String, default: null },
  hasRecord: { type: Boolean, default: true }, // false면 그 시각 스냅샷이 없다(좌석을 상태색으로 칠하지 않는다)
})
const emit = defineEmits(['select'])

// 좌석 상태에 등록된 좌석의 책상만 상태색으로 그린다
const isSeat = (o) => o.label != null && o.label !== '' && o.label in props.seatStates
const stateOf = (o) => props.seatStates[o.label] ?? 'unknown'

// 라벨이 박스보다 넓으면 글자 크기를 줄여 안에 담는다(글자 폭은 크기의 약 0.7배로 어림)
function cctvFontSize(o) {
  const chars = Math.max(1, String(o.label || 'CCTV').length)
  return Math.max(10, Math.min(22, (o.w * 0.78) / (chars * 0.7)))
}

function deskFontSize(o) {
  return Math.max(11, Math.min(30, o.h * 0.42))
}

function objectTransform(o) {
  if (!o.angle) return undefined
  return `rotate(${o.angle} ${o.x + o.w / 2} ${o.y + o.h / 2})`
}

function deskFill(o) {
  if (!isSeat(o) || !props.hasRecord) return '#ffffff'
  const s = stateOf(o)
  if (s === 'occupied') return 'rgb(var(--color-state-occupied) / 0.18)'
  return '#ffffff'
}

function deskStroke(o) {
  if (!isSeat(o) || !props.hasRecord) return '#a9b3c2'
  const s = stateOf(o)
  if (s === 'occupied') return 'rgb(var(--color-state-occupied))'
  return '#a9b3c2'
}
</script>
