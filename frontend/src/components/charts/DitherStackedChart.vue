<template>
  <div ref="containerRef" class="relative h-20">
    <canvas ref="canvasRef" class="absolute inset-0 w-full h-full" />
    <div class="relative h-full flex items-stretch gap-1.5">
      <button
        v-for="h in hours"
        :key="h.hour"
        :disabled="!h.scheduled || h.occupied === null"
        @click="$emit('select', h.hour)"
        class="flex-1 h-full"
        :class="(!h.scheduled || h.occupied === null) ? 'cursor-not-allowed' : 'cursor-pointer'"
        :title="!h.scheduled ? '수업 없음' : h.occupied !== null ? `${h.time} · 점유 ${h.occupied}/${h.total}석` : '대기중'"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useThemeStore } from '@/stores/themeStore'

const props = defineProps({
  hours: { type: Array, required: true },
  selectedHour: { type: Number, default: null },
})
defineEmits(['select'])

const theme = useThemeStore()
const containerRef = ref(null)
const canvasRef = ref(null)

// 4x4 오더드 디더링(Bayer matrix) — 값이 클수록 성긴, 작을수록 촘촘한 패턴
const BAYER4 = [
  [0, 8, 2, 10],
  [12, 4, 14, 6],
  [3, 11, 1, 9],
  [15, 7, 13, 5],
]
const CELL = 3
const GAP = 6

function ditherRect(ctx, x, y, w, h, color) {
  ctx.fillStyle = color
  const startCol = Math.floor(x / CELL)
  const endCol = Math.ceil((x + w) / CELL)
  const startRow = Math.floor(y / CELL)
  const endRow = Math.ceil((y + h) / CELL)
  for (let cx = startCol; cx < endCol; cx++) {
    for (let cy = startRow; cy < endRow; cy++) {
      const threshold = (BAYER4[cy & 3][cx & 3] + 0.5) / 16
      const px = Math.max(x, cx * CELL)
      const py = Math.max(y, cy * CELL)
      const pw = Math.min(x + w, (cx + 1) * CELL) - px
      const ph = Math.min(y + h, (cy + 1) * CELL) - py
      if (pw <= 0 || ph <= 0) continue
      if (threshold < densityAt(cy, startRow, endRow)) {
        ctx.fillRect(px, py, pw, ph)
      }
    }
  }
}

// 세로로 갈수록 점점 성겨지는 그러데이션 밀도 (막대 안쪽은 촘촘, 경계는 성김)
function densityAt(cy, startRow, endRow) {
  const rows = Math.max(1, endRow - startRow)
  const rel = (cy - startRow) / rows
  return 0.55 + rel * 0.42
}

function occupiedColor(ratio) {
  if (ratio >= 0.67) return '#ef4444'
  if (ratio >= 0.34) return '#f59e0b'
  return '#147b70'
}

// 균일한 밀도로 찍는 단순 디더 채우기 (미배정/대기중 칸)
function ditherFlat(ctx, x, y, w, h, color, density) {
  ctx.fillStyle = color
  const startCol = Math.floor(x / CELL)
  const endCol = Math.ceil((x + w) / CELL)
  const startRow = Math.floor(y / CELL)
  const endRow = Math.ceil((y + h) / CELL)
  for (let cx = startCol; cx < endCol; cx++) {
    for (let cy = startRow; cy < endRow; cy++) {
      const threshold = (BAYER4[cy & 3][cx & 3] + 0.5) / 16
      if (density <= threshold) continue
      const px = Math.max(x, cx * CELL)
      const py = Math.max(y, cy * CELL)
      const pw = Math.min(x + w, (cx + 1) * CELL) - px
      const ph = Math.min(y + h, (cy + 1) * CELL) - py
      if (pw > 0 && ph > 0) ctx.fillRect(px, py, pw, ph)
    }
  }
}

function drawChart() {
  const canvas = canvasRef.value
  const container = containerRef.value
  if (!canvas || !container) return

  const dpr = window.devicePixelRatio || 1
  const width = container.clientWidth
  const height = container.clientHeight
  canvas.width = width * dpr
  canvas.height = height * dpr
  const ctx = canvas.getContext('2d')
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
  ctx.clearRect(0, 0, width, height)

  const n = props.hours.length
  if (!n) return

  const isDark = theme.mode === 'dark'
  const emptyColor = isDark ? '#52525b' : '#a1a1aa'
  const idleColor = isDark ? '#3f3f46' : '#e4e4e7'

  const colW = (width - GAP * (n - 1)) / n

  props.hours.forEach((h, i) => {
    const x = i * (colW + GAP)

    if (!h.scheduled) {
      ditherFlat(ctx, x, 0, colW, height, idleColor, 0.12)
      return
    }
    if (h.occupied === null) {
      ditherFlat(ctx, x, 0, colW, height, idleColor, 0.22)
      return
    }

    const ratio = h.total ? h.occupied / h.total : 0
    const occH = Math.max(h.occupied > 0 ? 6 : 2, Math.round(ratio * height))
    const emptyH = height - occH

    if (emptyH > 0) ditherFlat(ctx, x, 0, colW, emptyH, emptyColor, 0.28)
    ditherRect(ctx, x, emptyH, colW, occH, occupiedColor(ratio))

    if (props.selectedHour === h.hour) {
      ctx.save()
      ctx.strokeStyle = '#566783'
      ctx.lineWidth = 2
      ctx.beginPath()
      ctx.roundRect(x + 1, 1, colW - 2, height - 2, 3)
      ctx.stroke()
      ctx.restore()
    }
  })
}

let resizeObserver = null

onMounted(async () => {
  await nextTick()
  drawChart()
  resizeObserver = new ResizeObserver(() => drawChart())
  if (containerRef.value) resizeObserver.observe(containerRef.value)
})

onUnmounted(() => resizeObserver?.disconnect())

watch(() => [props.hours, props.selectedHour, theme.mode], () => nextTick(drawChart), { deep: true })
</script>
