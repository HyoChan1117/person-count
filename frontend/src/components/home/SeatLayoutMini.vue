<template>
  <svg
    v-if="box"
    :viewBox="`${box.x} ${box.y} ${box.w} ${box.h}`"
    :style="{ aspectRatio: `${box.w} / ${box.h}` }"
    class="h-full"
    preserveAspectRatio="xMidYMid meet"
    role="img"
    :aria-label="label"
  >
    <rect
      v-for="d in desks"
      :key="d.id"
      :x="d.x" :y="d.y" :width="d.w" :height="d.h"
      :transform="rotation(d)"
      rx="10"
      :class="FILL[stateOf(d)]"
    />
  </svg>
</template>

<script setup>
import { computed } from 'vue'

// 상태색 4가지 중 좌석에 쓰는 3가지. Tailwind가 스캔할 수 있게 클래스는 리터럴로 적는다.
const FILL = {
  occupied: 'fill-state-occupied',
  empty: 'fill-state-empty/35',
  unknown: 'fill-state-unknown/45',
}
const LABELS = { occupied: '점유', empty: '빈 좌석', unknown: '판정 불가' }

const props = defineProps({
  map: { type: Object, required: true },        // 맵 에디터 저장 형식 { mapW, mapH, objects[] } (읽기 전용)
  seatStates: { type: Object, required: true }, // { 좌석ID: 'occupied'|'empty'|'unknown' }
})

// 홈 카드는 높이가 낮아 배치도 전체를 넣으면 좌석이 뭉개진다. 의자·CCTV를 빼고 책상만 그리면
// 가로로 더 넓게 퍼져(정사각형에 가깝던 비율이 완화된다) 좌석 상태가 멀리서도 읽힌다.
const desks = computed(() => (props.map.objects ?? []).filter((o) => o.type === 'desk'))

const stateOf = (d) => props.seatStates[d.label] ?? 'unknown'

// 책상만 감싸는 최소 영역을 viewBox로 잡는다.
const box = computed(() => {
  if (!desks.value.length) return null
  const x = Math.min(...desks.value.map((d) => d.x))
  const y = Math.min(...desks.value.map((d) => d.y))
  const right = Math.max(...desks.value.map((d) => d.x + d.w))
  const bottom = Math.max(...desks.value.map((d) => d.y + d.h))
  const pad = Math.max(...desks.value.map((d) => d.w)) * 0.15
  return { x: x - pad, y: y - pad, w: right - x + pad * 2, h: bottom - y + pad * 2 }
})

function rotation(d) {
  if (!d.angle) return undefined
  return `rotate(${d.angle} ${d.x + d.w / 2} ${d.y + d.h / 2})`
}

const label = computed(() => {
  const counts = desks.value.reduce((acc, d) => {
    const s = stateOf(d)
    acc[s] = (acc[s] ?? 0) + 1
    return acc
  }, {})
  const parts = Object.entries(counts).map(([s, n]) => `${LABELS[s]} ${n}석`)
  return `좌석 배치 · ${parts.join(' · ')}`
})
</script>
