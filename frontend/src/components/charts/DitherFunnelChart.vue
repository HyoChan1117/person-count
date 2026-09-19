<template>
  <div ref="containerRef" class="relative" :style="{ height: rowsToShow.length * ROW_H + 'px' }">
    <canvas ref="canvasRef" class="absolute inset-0 w-full h-full" />
    <div class="relative h-full flex flex-col">
      <button
        v-for="row in rowsToShow"
        :key="row.seatId"
        class="w-full flex-1"
        :title="`${row.seatId}번 · 점유 ${row.timeText}`"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useThemeStore } from '@/stores/themeStore'

const props = defineProps({
  rows: { type: Array, required: true },
  maxItems: { type: Number, default: 8 },
})

const theme = useThemeStore()
const containerRef = ref(null)
const canvasRef = ref(null)
const ROW_H = 34
const ROW_GAP = 3

const rowsToShow = computed(() => props.rows.slice(0, props.maxItems))

const BAYER4 = [
  [0, 8, 2, 10],
  [12, 4, 14, 6],
  [3, 11, 1, 9],
  [15, 7, 13, 5],
]
const CELL = 3

function hexToRgb(hex) {
  const v = parseInt(hex.slice(1), 16)
  return [(v >> 16) & 255, (v >> 8) & 255, v & 255]
}
function lerpColor(a, b, t) {
  const [ar, ag, ab] = hexToRgb(a)
  const [br, bg, bb] = hexToRgb(b)
  const r = Math.round(ar + (br - ar) * t)
  const g = Math.round(ag + (bg - ag) * t)
  const bl = Math.round(ab + (bb - ab) * t)
  return `rgb(${r},${g},${bl})`
}

// 사다리꼴 영역을 클리핑한 뒤 디더 패턴으로 채운다
function ditherTrapezoid(ctx, cx, hTop, hBot, rowTop, rowBottom, color) {
  ctx.save()
  ctx.beginPath()
  ctx.moveTo(cx - hTop / 2, rowTop)
  ctx.lineTo(cx + hTop / 2, rowTop)
  ctx.lineTo(cx + hBot / 2, rowBottom)
  ctx.lineTo(cx - hBot / 2, rowBottom)
  ctx.closePath()
  ctx.clip()

  const maxHalf = Math.max(hTop, hBot) / 2
  const x0 = cx - maxHalf
  const x1 = cx + maxHalf
  ctx.fillStyle = color
  const startCol = Math.floor(x0 / CELL)
  const endCol = Math.ceil(x1 / CELL)
  const startRow = Math.floor(rowTop / CELL)
  const endRow = Math.ceil(rowBottom / CELL)
  for (let cx2 = startCol; cx2 < endCol; cx2++) {
    for (let cy2 = startRow; cy2 < endRow; cy2++) {
      const threshold = (BAYER4[cy2 & 3][cx2 & 3] + 0.5) / 16
      const rel = (cy2 * CELL - rowTop) / Math.max(1, rowBottom - rowTop)
      const density = 0.62 + rel * 0.3
      if (density <= threshold) continue
      ctx.fillRect(cx2 * CELL, cy2 * CELL, CELL, CELL)
    }
  }
  ctx.restore()
}

function drawLabel(ctx, cx, y, h, text, sub) {
  ctx.save()
  ctx.font = 'bold 12px ui-monospace, monospace'
  const tw = ctx.measureText(text).width
  const subFont = '10px ui-monospace, monospace'
  ctx.font = subFont
  const sw = ctx.measureText(sub).width
  const pad = 8
  const chipW = Math.max(tw, sw) + pad * 2
  const chipH = h - 8
  const isDark = theme.mode === 'dark'
  ctx.fillStyle = isDark ? 'rgba(9,9,11,0.72)' : 'rgba(255,255,255,0.82)'
  ctx.beginPath()
  ctx.roundRect(cx - chipW / 2, y + 4, chipW, chipH, 6)
  ctx.fill()

  ctx.fillStyle = isDark ? '#f4f4f5' : '#18181b'
  ctx.font = 'bold 12px ui-monospace, monospace'
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'
  ctx.fillText(text, cx, y + 4 + chipH * 0.38)
  ctx.fillStyle = isDark ? '#a1a1aa' : '#71717a'
  ctx.font = subFont
  ctx.fillText(sub, cx, y + 4 + chipH * 0.72)
  ctx.restore()
}

function widthFor(ratio, containerW) {
  const minRatio = 0.22
  return (minRatio + (1 - minRatio) * ratio) * containerW * 0.94
}

let progress = 0
let raf = null

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

  const rows = rowsToShow.value
  const n = rows.length
  if (!n) return

  const maxVal = Math.max(1, rows[0]?.occupiedMinutes ?? 0)
  const cx = width / 2
  const HOT = '#ef4444'
  const COOL = '#147b70'

  // 각 행 경계(위/아래)의 사다리꼴 폭을 계산해 연속적으로 좁아지는 깔때기 모양을 만든다
  const boundaries = rows.map(r => widthFor((r.occupiedMinutes ?? 0) / maxVal, width))
  boundaries.push(boundaries[boundaries.length - 1] * 0.45)

  rows.forEach((row, i) => {
    const rowTop = i * ROW_H + ROW_GAP / 2
    const rowBottom = (i + 1) * ROW_H - ROW_GAP / 2
    const hTop = boundaries[i] * progress
    const hBot = boundaries[i + 1] * progress
    const ratio = (row.occupiedMinutes ?? 0) / maxVal
    const color = lerpColor(COOL, HOT, ratio)
    if (hTop > 1 || hBot > 1) {
      ditherTrapezoid(ctx, cx, hTop, hBot, rowTop, rowBottom, color)
    }
    if (progress > 0.6) {
      drawLabel(ctx, cx, rowTop, ROW_H - ROW_GAP, `${row.seatId}번`, row.timeText)
    }
  })
}

function animate() {
  progress = Math.min(1, progress + 0.06)
  drawChart()
  if (progress < 1) raf = requestAnimationFrame(animate)
}

let resizeObserver = null

onMounted(async () => {
  await nextTick()
  progress = 0
  raf = requestAnimationFrame(animate)
  resizeObserver = new ResizeObserver(() => drawChart())
  if (containerRef.value) resizeObserver.observe(containerRef.value)
})

onUnmounted(() => {
  resizeObserver?.disconnect()
  if (raf) cancelAnimationFrame(raf)
})

watch(() => [props.rows, theme.mode], () => {
  progress = 0
  if (raf) cancelAnimationFrame(raf)
  raf = requestAnimationFrame(animate)
}, { deep: true })
</script>
