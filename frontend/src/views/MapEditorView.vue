<template>
  <div class="flex h-full overflow-hidden bg-neutral-100 dark:bg-neutral-950">

    <!-- Sidebar -->
    <aside class="w-48 bg-white dark:bg-neutral-900 border-r border-neutral-200 dark:border-neutral-800 flex flex-col p-3 shrink-0">
      <div class="text-[11px] font-semibold text-neutral-400 dark:text-neutral-500 uppercase tracking-wide mb-2">객체 배치</div>

      <button
        v-for="tool in TOOLS"
        :key="tool.type"
        @click="activeTool = activeTool === tool.type ? null : tool.type"
        :class="[
          'flex items-center gap-2 text-sm px-3 py-2 rounded-lg mb-1 transition text-left font-medium',
          activeTool === tool.type
            ? 'bg-violet-600 text-white'
            : 'bg-neutral-50 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300 hover:bg-neutral-100 dark:hover:bg-neutral-700'
        ]"
      >
        <span>{{ tool.icon }}</span>{{ tool.label }}
      </button>

      <!-- 책상 이름 (책상 선택 시) -->
      <template v-if="selectedDesk">
        <div class="border-t border-neutral-100 dark:border-neutral-800 my-3" />
        <div class="text-[11px] font-semibold text-neutral-400 dark:text-neutral-500 uppercase tracking-wide mb-2">책상 이름</div>
        <input
          v-model="selectedDesk.label"
          placeholder="예: A1, 앞줄 1번"
          class="text-xs border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-950 text-neutral-900 dark:text-neutral-100 rounded px-2 py-1.5 w-full focus:outline-none focus:ring-1 focus:ring-violet-400 dark:focus:ring-violet-500"
          @keydown.stop
        />
        <div class="text-[10px] text-neutral-400 dark:text-neutral-600 mt-1">이름을 입력하면 캔버스에 표시됩니다</div>
      </template>

      <!-- CCTV 설정 (CCTV 선택 시) -->
      <template v-if="selectedCCTV">
        <div class="border-t border-neutral-100 dark:border-neutral-800 my-3" />
        <div class="text-[11px] font-semibold text-neutral-400 dark:text-neutral-500 uppercase tracking-wide mb-2">CCTV 설정</div>
        <label class="text-[10px] text-neutral-500 dark:text-neutral-400 mb-0.5 block">이름</label>
        <input
          v-model="selectedCCTV.label"
          placeholder="예: CCTV 1"
          class="text-xs border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-950 text-neutral-900 dark:text-neutral-100 rounded px-2 py-1.5 w-full focus:outline-none focus:ring-1 focus:ring-violet-400 dark:focus:ring-violet-500 mb-3"
          @keydown.stop
        />
        <div class="border-t border-neutral-100 dark:border-neutral-800 mt-3 mb-2" />
        <div class="flex items-center justify-between mb-2">
          <div class="text-[11px] font-semibold text-neutral-400 dark:text-neutral-500 uppercase tracking-wide">담당 자리</div>
          <div class="flex items-center gap-1.5">
            <div class="w-2.5 h-2.5 rounded-full flex-shrink-0" :style="{ background: getCctvColor(selectedCCTV.id) }" />
            <span class="text-[11px] font-bold" :style="{ color: getCctvColor(selectedCCTV.id) }">
              {{ objects.filter(o => o.type === 'desk' && (o.cctvIds ?? (o.cctvId != null ? [o.cctvId] : [])).includes(selectedCCTV.id)).length }}자리
            </span>
          </div>
        </div>
        <button
          @click="seatAssignMode && assigningCctvId === selectedCCTV.id ? exitSeatAssignMode() : enterSeatAssignMode()"
          :class="[
            'text-xs px-3 py-1.5 rounded-lg w-full transition font-medium',
            seatAssignMode && assigningCctvId === selectedCCTV.id
              ? 'text-white'
              : 'bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300 hover:bg-neutral-200 dark:hover:bg-neutral-700 border border-neutral-200 dark:border-neutral-700'
          ]"
          :style="seatAssignMode && assigningCctvId === selectedCCTV.id ? { background: getCctvColor(selectedCCTV.id) } : {}"
        >
          {{ seatAssignMode && assigningCctvId === selectedCCTV.id ? '✓ 선택 완료' : '📍 자리 선택 모드' }}
        </button>
      </template>

      <div class="border-t border-neutral-100 dark:border-neutral-800 my-3" />

      <div class="text-[11px] font-semibold text-neutral-400 dark:text-neutral-500 uppercase tracking-wide mb-2">맵 크기</div>
      <label class="text-xs text-neutral-500 dark:text-neutral-400 mb-0.5">가로 (px)</label>
      <input type="number" v-model.number="mapW" min="400" max="2400" step="50"
        class="text-xs border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-950 text-neutral-900 dark:text-neutral-100 rounded px-2 py-1 mb-2 focus:outline-none focus:ring-1 focus:ring-violet-400 dark:focus:ring-violet-500" />
      <label class="text-xs text-neutral-500 dark:text-neutral-400 mb-0.5">세로 (px)</label>
      <input type="number" v-model.number="mapH" min="300" max="1600" step="50"
        class="text-xs border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-950 text-neutral-900 dark:text-neutral-100 rounded px-2 py-1 mb-1 focus:outline-none focus:ring-1 focus:ring-violet-400 dark:focus:ring-violet-500" />

      <div class="flex-1" />

      <button
        @click="deleteSelected"
        :disabled="!selectedIds.length"
        class="text-sm text-red-500 dark:text-red-400 bg-red-50 dark:bg-red-500/10 hover:bg-red-100 dark:hover:bg-red-500/20 disabled:opacity-30 disabled:cursor-not-allowed rounded-lg px-3 py-1.5 mb-1 transition"
      >🗑 삭제{{ selectedIds.length > 1 ? ` (${selectedIds.length})` : '' }}</button>
      <button
        @click="clearAll"
        class="text-sm text-neutral-500 dark:text-neutral-400 bg-neutral-50 dark:bg-neutral-800 hover:bg-neutral-100 dark:hover:bg-neutral-700 rounded-lg px-3 py-1.5 mb-2 transition"
      >전체 지우기</button>
      <button
        @click="exportImage"
        class="text-sm text-white bg-violet-600 hover:bg-violet-700 rounded-lg px-3 py-2 transition font-medium"
      >📥 이미지 저장</button>
    </aside>

    <!-- Main area -->
    <div class="flex-1 flex flex-col min-w-0">

      <!-- Top bar -->
      <div class="flex items-center justify-between px-4 py-2.5 bg-white dark:bg-neutral-900 border-b border-neutral-200 dark:border-neutral-800 shrink-0">
        <router-link to="/classrooms" class="text-sm text-neutral-500 dark:text-neutral-400 hover:text-neutral-700 dark:hover:text-neutral-200 transition">← 목록</router-link>
        <span class="text-sm font-semibold text-neutral-700 dark:text-neutral-200">{{ classroom?.name }} — 맵 에디터</span>
        <span class="text-xs text-neutral-400 dark:text-neutral-500 flex items-center gap-3">
          <template v-if="seatAssignMode">
            <span class="w-2 h-2 rounded-full inline-block mr-1" :style="{ background: getCctvColor(assigningCctvId) }" />
            <span class="text-amber-600 dark:text-amber-400 font-medium">자리 선택 모드</span>
            — 책상을 클릭하여 배정 / 다시 클릭하면 해제 | ESC 종료
          </template>
          <template v-else-if="activeTool">
            <span class="text-violet-600 dark:text-violet-400 font-medium">{{ TOOLS.find(t => t.type === activeTool)?.label }}</span>
            선택됨 — 캔버스를 클릭해 배치
          </template>
          <template v-else-if="selectedIds.length > 1">
            {{ selectedIds.length }}개 선택됨 — 드래그로 이동 / Delete로 삭제
          </template>
          <template v-else-if="selectedIds.length === 1">
            객체 선택됨 — 드래그 이동 / 핸들 크기 조절
          </template>
          <template v-else>
            클릭으로 선택 또는 빈 곳에서 드래그로 다중 선택
          </template>
          <span class="text-neutral-200 dark:text-neutral-700">|</span>
          <button @click="undo" :disabled="historyIdx <= 0" class="hover:text-neutral-600 dark:hover:text-neutral-300 disabled:opacity-30" title="되돌리기 (Ctrl+Z)">↩ 되돌리기</button>
          <button @click="redo" :disabled="historyIdx >= history.length - 1" class="hover:text-neutral-600 dark:hover:text-neutral-300 disabled:opacity-30" title="다시실행 (Ctrl+Y)">↪ 다시실행</button>
        </span>
      </div>

      <!-- Canvas scroll area -->
      <div
        ref="scrollEl"
        class="flex-1 overflow-auto p-6 flex items-start justify-start"
      >
        <div class="relative inline-block">
          <canvas
            ref="canvasEl"
            :width="mapW"
            :height="mapH"
            class="shadow-xl rounded-lg bg-white block"
            :style="{ cursor: cursorStyle }"
            @mousedown="onMouseDown"
            @mousemove="onMouseMove"
            @mouseup="onMouseUp"
            @mouseleave="onMouseUp"
          />
          <div
            class="absolute -right-1.5 -bottom-1.5 w-4 h-4 rounded-sm bg-white border-2 border-violet-500 cursor-nwse-resize"
            title="드래그해서 맵 크기 조절"
            @mousedown="onMapResizeMouseDown"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { useClassroomStore } from '@/stores/classroomStore.js'
import api from '@/api'

const TOOLS = [
  { type: 'cctv',  label: 'CCTV', icon: '📷', defaultW: 90,  defaultH: 70  },
  { type: 'desk',  label: '책상',  icon: '🪑', defaultW: 130, defaultH: 75  },
  { type: 'chair', label: '의자',  icon: '💺', defaultW: 55,  defaultH: 55  },
]

const HANDLE_R = 6
const CCTV_COLORS = ['#3b82f6', '#22c55e', '#ef4444', '#a855f7', '#f97316', '#06b6d4', '#ec4899', '#84cc16']

function getCctvColor(cctvId) {
  const cctvs = objects.value.filter(o => o.type === 'cctv')
  const idx = cctvs.findIndex(o => o.id === cctvId)
  return idx >= 0 ? CCTV_COLORS[idx % CCTV_COLORS.length] : '#94a3b8'
}

const route = useRoute()
const cStore = useClassroomStore()
const classroom = computed(() => cStore.current)

const canvasEl = ref(null)
const mapW = ref(900)
const mapH = ref(600)
const objects = ref([])
const selectedIds = ref([])          // 다중 선택 ID 배열
const activeTool = ref(null)
const hoverHandle = ref(null)
const seatAssignMode = ref(false)
const assigningCctvId = ref(null)

// ── 맵 크기 드래그 조절 ──────────────────────────────────────────────────────
const MAP_W_MIN = 400, MAP_W_MAX = 2400
const MAP_H_MIN = 300, MAP_H_MAX = 1600
let mapResizeStart = null

function onMapResizeMouseDown(e) {
  e.preventDefault()
  mapResizeStart = { x: e.clientX, y: e.clientY, w: mapW.value, h: mapH.value }
  window.addEventListener('mousemove', onMapResizeMouseMove)
  window.addEventListener('mouseup', onMapResizeMouseUp)
}

function onMapResizeMouseMove(e) {
  if (!mapResizeStart) return
  mapW.value = Math.min(MAP_W_MAX, Math.max(MAP_W_MIN, Math.round(mapResizeStart.w + (e.clientX - mapResizeStart.x))))
  mapH.value = Math.min(MAP_H_MAX, Math.max(MAP_H_MIN, Math.round(mapResizeStart.h + (e.clientY - mapResizeStart.y))))
}

function onMapResizeMouseUp() {
  mapResizeStart = null
  window.removeEventListener('mousemove', onMapResizeMouseMove)
  window.removeEventListener('mouseup', onMapResizeMouseUp)
}

// 단일 선택 편의 computed (resize handle 등에서 사용)
const selectedId = computed(() => selectedIds.value.length === 1 ? selectedIds.value[0] : null)
const selectedDesk = computed(() => {
  if (selectedIds.value.length !== 1) return null
  const obj = objects.value.find(o => o.id === selectedIds.value[0])
  return obj?.type === 'desk' ? obj : null
})

const selectedCCTV = computed(() => {
  if (selectedIds.value.length !== 1) return null
  const obj = objects.value.find(o => o.id === selectedIds.value[0])
  return obj?.type === 'cctv' ? obj : null
})

let nextId = 1
let dragState = null
let rubberBand = null  // { startX, startY, endX, endY }

// ── History ───────────────────────────────────────────────────────────────────
const history = ref([])
const historyIdx = ref(-1)

function pushHistory() {
  history.value.splice(historyIdx.value + 1)
  history.value.push(JSON.stringify(objects.value))
  historyIdx.value = history.value.length - 1
  if (history.value.length > 50) { history.value.shift(); historyIdx.value-- }
}

function undo() {
  if (historyIdx.value <= 0) return
  historyIdx.value--
  objects.value = JSON.parse(history.value[historyIdx.value])
  selectedIds.value = []
}

function redo() {
  if (historyIdx.value >= history.value.length - 1) return
  historyIdx.value++
  objects.value = JSON.parse(history.value[historyIdx.value])
  selectedIds.value = []
}

// ── Clipboard ─────────────────────────────────────────────────────────────────
let clipboard = null  // array of objects

function copySelected() {
  if (!selectedIds.value.length) return
  clipboard = objects.value
    .filter(o => selectedIds.value.includes(o.id))
    .map(o => ({ ...o }))
}

function cutSelected() {
  copySelected()
  if (!clipboard?.length) return
  pushHistory()
  deleteSelected()
}

function pasteClipboard() {
  if (!clipboard?.length) return
  pushHistory()
  const newIds = []
  for (const obj of clipboard) {
    const newObj = { ...obj, id: nextId++, x: obj.x + 20, y: obj.y + 20 }
    objects.value.push(newObj)
    newIds.push(newObj.id)
  }
  selectedIds.value = newIds
}

// ── Cursor ────────────────────────────────────────────────────────────────────
const CURSOR_MAP = {
  nw: 'nw-resize', n: 'n-resize', ne: 'ne-resize',
  e: 'e-resize', se: 'se-resize', s: 's-resize',
  sw: 'sw-resize', w: 'w-resize',
}
const cursorStyle = computed(() => {
  if (seatAssignMode.value) return 'crosshair'
  if (activeTool.value) return 'crosshair'
  if (hoverHandle.value) return CURSOR_MAP[hoverHandle.value] ?? 'pointer'
  return 'default'
})

function enterSeatAssignMode() {
  if (!selectedCCTV.value) return
  assigningCctvId.value = selectedCCTV.value.id
  seatAssignMode.value = true
}

function exitSeatAssignMode() {
  seatAssignMode.value = false
  assigningCctvId.value = null
}

// ── Persistence ───────────────────────────────────────────────────────────────
const storageKey = computed(() => `map_${route.params.id}`)

function save() {
  localStorage.setItem(storageKey.value, JSON.stringify({
    objects: objects.value, mapW: mapW.value, mapH: mapH.value,
  }))
  scheduleBackendSave()
}

let _backendSaveTimer = null
function scheduleBackendSave() {
  clearTimeout(_backendSaveTimer)
  _backendSaveTimer = setTimeout(() => {
    if (!canvasEl.value) return
    const b64 = canvasEl.value.toDataURL('image/png').replace('data:image/png;base64,', '')
    fetch(`/api/analysis/${route.params.id}/map-image`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ image: b64 }),
    }).catch(e => console.warn('[map] 백엔드 저장 실패:', e))

    // 카메라별 담당 자리 수/번호 백엔드 자동 동기화 (라벨 → 카메라명 매칭)
    const cctvObjs = objects.value.filter(o => o.type === 'cctv')
    const seatCounts = {}
    const seatIds = {}
    for (const cctv of cctvObjs) {
      const label = cctv.label?.trim() || 'CCTV'
      const desks = objects.value.filter(o =>
        o.type === 'desk' && (o.cctvIds ?? (o.cctvId != null ? [o.cctvId] : [])).includes(cctv.id)
      )
      seatCounts[label] = desks.length
      seatIds[label] = desks.map(o => o.label).filter(l => l != null && l !== '')
    }
    if (cctvObjs.length > 0) {
      fetch(`/api/analysis/${route.params.id}/seat-counts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ seat_counts: seatCounts, seat_ids: seatIds }),
      }).catch(e => console.warn('[map] 자리 배정 저장 실패:', e))
    }

    // 배치도 JSON 백엔드 동기화 (Slack 전송용)
    fetch(`/api/classrooms/${route.params.id}/map-data`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ objects: objects.value, mapW: mapW.value, mapH: mapH.value }),
    }).catch(e => console.warn('[map] 배치도 데이터 저장 실패:', e))
  }, 1500)
}

function applyMapData(data) {
  objects.value = data.objects ?? []
  mapW.value = data.mapW ?? 900
  mapH.value = data.mapH ?? 600
  nextId = (objects.value.reduce((m, o) => Math.max(m, o.id), 0) ?? 0) + 1
}

async function load() {
  try {
    const { data } = await api.get(`/classrooms/${route.params.id}/map-data`)
    applyMapData(data)
    return
  } catch {}
  // 서버에 저장된 배치도가 없을 때만 로컬 캐시로 폴백
  try {
    const raw = localStorage.getItem(storageKey.value)
    if (!raw) return
    applyMapData(JSON.parse(raw))
  } catch {}
}

onMounted(async () => {
  cStore.fetchOne(Number(route.params.id))
  await load()
  nextTick(() => { pushHistory(); redraw() })
  window.addEventListener('keydown', onKeyDown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', onKeyDown)
  onMapResizeMouseUp()
})

function onKeyDown(e) {
  if (document.activeElement?.tagName === 'INPUT') return

  if (e.ctrlKey || e.metaKey) {
    switch (e.key.toLowerCase()) {
      case 'z': e.preventDefault(); e.shiftKey ? redo() : undo(); break
      case 'y': e.preventDefault(); redo(); break
      case 'c': e.preventDefault(); copySelected(); break
      case 'x': e.preventDefault(); cutSelected(); break
      case 'v': e.preventDefault(); pasteClipboard(); break
      case 'a':
        e.preventDefault()
        selectedIds.value = objects.value.map(o => o.id)
        redraw()
        break
    }
    return
  }

  if (e.key === 'Delete' || e.key === 'Backspace') {
    if (selectedIds.value.length) { pushHistory(); deleteSelected() }
  } else if (e.key === 'Escape') {
    if (seatAssignMode.value) { exitSeatAssignMode(); redraw(); return }
    activeTool.value = null
    selectedIds.value = []
    redraw()
  } else if (selectedIds.value.length) {
    const step = e.shiftKey ? 10 : 1
    const dirs = { ArrowLeft: [-step, 0], ArrowRight: [step, 0], ArrowUp: [0, -step], ArrowDown: [0, step] }
    const d = dirs[e.key]
    if (d) {
      e.preventDefault()
      for (const id of selectedIds.value) {
        const obj = objects.value.find(o => o.id === id)
        if (obj) { obj.x = Math.max(0, obj.x + d[0]); obj.y = Math.max(0, obj.y + d[1]) }
      }
    }
  }
}

watch([objects, mapW, mapH], () => { save(); nextTick(redraw) }, { deep: true })
watch(selectedIds, () => nextTick(redraw), { deep: true })
watch(selectedCCTV, (val) => { if (!val && seatAssignMode.value) exitSeatAssignMode() })

// ── Rendering ─────────────────────────────────────────────────────────────────

function redraw() {
  const canvas = canvasEl.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  ctx.clearRect(0, 0, mapW.value, mapH.value)
  drawGrid(ctx)
  for (const obj of objects.value) {
    drawObject(ctx, obj, selectedIds.value.includes(obj.id))
  }
  // 러버밴드 그리기
  if (rubberBand) {
    const rx = Math.min(rubberBand.startX, rubberBand.endX)
    const ry = Math.min(rubberBand.startY, rubberBand.endY)
    const rw = Math.abs(rubberBand.endX - rubberBand.startX)
    const rh = Math.abs(rubberBand.endY - rubberBand.startY)
    ctx.save()
    ctx.fillStyle = 'rgba(124,58,237,0.08)'
    ctx.fillRect(rx, ry, rw, rh)
    ctx.strokeStyle = '#7c3aed'
    ctx.lineWidth = 1
    ctx.setLineDash([4, 3])
    ctx.strokeRect(rx, ry, rw, rh)
    ctx.setLineDash([])
    ctx.restore()
  }
}

function drawGrid(ctx) {
  ctx.strokeStyle = '#e2e8f0'
  ctx.lineWidth = 1
  for (let x = 0; x <= mapW.value; x += 40) {
    ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, mapH.value); ctx.stroke()
  }
  for (let y = 0; y <= mapH.value; y += 40) {
    ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(mapW.value, y); ctx.stroke()
  }
}

function drawObject(ctx, obj, isSelected) {
  if (obj.type === 'cctv') drawCCTV(ctx, obj, isSelected)
  else if (obj.type === 'desk') drawDesk(ctx, obj, isSelected)
  else if (obj.type === 'chair') drawChair(ctx, obj, isSelected)

  if (isSelected) {
    ctx.save()
    ctx.strokeStyle = '#7c3aed'
    ctx.lineWidth = 1.5
    ctx.setLineDash([5, 4])
    ctx.strokeRect(obj.x - 4, obj.y - 4, obj.w + 8, obj.h + 8)
    ctx.setLineDash([])
    ctx.restore()

    // 리사이즈 핸들은 단일 선택일 때만
    if (selectedIds.value.length === 1) {
      for (const h of getHandles(obj)) {
        ctx.fillStyle = '#fff'
        ctx.strokeStyle = '#7c3aed'
        ctx.lineWidth = 1.5
        ctx.beginPath()
        ctx.rect(h.hx - HANDLE_R, h.hy - HANDLE_R, HANDLE_R * 2, HANDLE_R * 2)
        ctx.fill()
        ctx.stroke()
      }
    }
  }
}

function drawDesk(ctx, obj, isSelected) {
  const { x, y, w, h } = obj
  // Body - tint if assigned in assign mode (다중 CCTV 지원, 구버전 cctvId 마이그레이션)
  const cctvIds = obj.cctvIds ?? (obj.cctvId != null ? [obj.cctvId] : [])
  const isAssignedToActive = seatAssignMode.value && cctvIds.includes(assigningCctvId.value)
  ctx.fillStyle = isAssignedToActive ? '#ede9fe' : '#f8fafc'
  ctx.strokeStyle = isSelected ? '#7c3aed' : (cctvIds.length > 0 ? getCctvColor(cctvIds[0]) : '#cbd5e1')
  ctx.lineWidth = isSelected ? 2.5 : 2
  ctx.beginPath(); ctx.rect(x, y, w, h); ctx.fill(); ctx.stroke()
  // Label
  ctx.font = `bold ${Math.min(h * 0.36, 16)}px sans-serif`
  ctx.fillStyle = '#1e293b'
  ctx.textAlign = 'center'; ctx.textBaseline = 'middle'
  ctx.fillText(obj.label?.trim() || '책상', x + w / 2, y + h / 2)
  // CCTV 배정 색상 도트 (다중 지원)
  if (cctvIds.length > 0) {
    const dotR = 5
    const gap = 13
    cctvIds.forEach((cid, i) => {
      ctx.fillStyle = getCctvColor(cid)
      ctx.beginPath()
      ctx.arc(x + w - 8 - i * gap, y + 8, dotR, 0, Math.PI * 2)
      ctx.fill()
      ctx.strokeStyle = 'white'
      ctx.lineWidth = 1.5
      ctx.stroke()
    })
  }
}

function drawChair(ctx, obj, isSelected) {
  const { x, y, w, h } = obj
  ctx.fillStyle = '#e0f2fe'
  ctx.strokeStyle = isSelected ? '#7c3aed' : '#8fd4f0'
  ctx.lineWidth = isSelected ? 2.5 : 2
  ctx.beginPath(); ctx.roundRect(x, y, w, h, 4); ctx.fill(); ctx.stroke()
}

function drawCCTV(ctx, obj, isSelected) {
  const { x, y, w, h } = obj
  const cx = x + w / 2, cy = y + h / 2

  // Body (단순 사각형 + 렌즈 점)
  ctx.fillStyle = '#e2e8f0'
  ctx.strokeStyle = isSelected ? '#7c3aed' : '#94a3b8'
  ctx.lineWidth = isSelected ? 2.5 : 2
  ctx.beginPath(); ctx.roundRect(x, y, w, h, 4); ctx.fill(); ctx.stroke()
  ctx.fillStyle = '#64748b'
  ctx.beginPath(); ctx.arc(cx, cy, Math.min(w, h) * 0.22, 0, Math.PI * 2); ctx.fill()

  // CCTV 색상 도트
  ctx.fillStyle = getCctvColor(obj.id)
  ctx.beginPath()
  ctx.arc(x + w - 7, y + 7, 5, 0, Math.PI * 2)
  ctx.fill()
  ctx.strokeStyle = 'white'
  ctx.lineWidth = 1.2
  ctx.stroke()

  // Label (이름이 설정되면 이름 표시, 아니면 CCTV)
  const label = obj.label?.trim()
  ctx.fillStyle = '#334155'
  ctx.font = `bold ${Math.min(h * 0.2, 12)}px sans-serif`
  ctx.textAlign = 'center'; ctx.textBaseline = 'alphabetic'
  ctx.fillText(label || 'CCTV', x + w / 2, y + h * 0.98)
  ctx.textAlign = 'left'
}

function getHandles(obj) {
  const { x, y, w, h } = obj
  return [
    { name: 'nw', hx: x,       hy: y       },
    { name: 'n',  hx: x + w/2, hy: y       },
    { name: 'ne', hx: x + w,   hy: y       },
    { name: 'e',  hx: x + w,   hy: y + h/2 },
    { name: 'se', hx: x + w,   hy: y + h   },
    { name: 's',  hx: x + w/2, hy: y + h   },
    { name: 'sw', hx: x,       hy: y + h   },
    { name: 'w',  hx: x,       hy: y + h/2 },
  ]
}

// ── Mouse helpers ─────────────────────────────────────────────────────────────

function getPos(e) {
  const rect = canvasEl.value.getBoundingClientRect()
  return {
    x: (e.clientX - rect.left) * (mapW.value / rect.width),
    y: (e.clientY - rect.top)  * (mapH.value / rect.height),
  }
}

function hitHandle(obj, px, py) {
  for (const h of getHandles(obj)) {
    if (Math.abs(px - h.hx) <= HANDLE_R + 2 && Math.abs(py - h.hy) <= HANDLE_R + 2) return h.name
  }
  return null
}

function hitObject(px, py) {
  for (let i = objects.value.length - 1; i >= 0; i--) {
    const o = objects.value[i]
    if (px >= o.x && px <= o.x + o.w && py >= o.y && py <= o.y + o.h) return o
  }
  return null
}

// ── Mouse events ──────────────────────────────────────────────────────────────

function onMouseDown(e) {
  const { x, y } = getPos(e)

  // 자리 선택 모드: 책상 클릭으로 배정/해제 (다중 CCTV 허용)
  if (seatAssignMode.value) {
    const hit = hitObject(x, y)
    if (hit?.type === 'desk') {
      pushHistory()
      if (!hit.cctvIds) hit.cctvIds = []
      const idx = hit.cctvIds.indexOf(assigningCctvId.value)
      if (idx >= 0) {
        hit.cctvIds.splice(idx, 1)
      } else {
        hit.cctvIds.push(assigningCctvId.value)
      }
      save()
      redraw()
    }
    return
  }

  // 리사이즈 핸들 (단일 선택 시만)
  if (selectedId.value) {
    const sel = objects.value.find(o => o.id === selectedId.value)
    if (sel) {
      const handle = hitHandle(sel, x, y)
      if (handle) {
        pushHistory()
        dragState = { type: 'resize', handle, startX: x, startY: y,
          origX: sel.x, origY: sel.y, origW: sel.w, origH: sel.h }
        return
      }
    }
  }

  // 새 객체 배치
  if (activeTool.value) {
    pushHistory()
    const tool = TOOLS.find(t => t.type === activeTool.value)
    const newObj = {
      id: nextId++,
      type: activeTool.value,
      x: Math.round(x - tool.defaultW / 2),
      y: Math.round(y - tool.defaultH / 2),
      w: tool.defaultW,
      h: tool.defaultH,
    }
    if (activeTool.value === 'desk') newObj.label = ''
    if (activeTool.value === 'cctv') newObj.label = ''
    objects.value.push(newObj)
    selectedIds.value = [newObj.id]
    activeTool.value = null
    return
  }

  const hit = hitObject(x, y)
  if (hit) {
    // Ctrl/Shift+클릭 → 선택 토글
    if (e.ctrlKey || e.metaKey || e.shiftKey) {
      if (selectedIds.value.includes(hit.id)) {
        selectedIds.value = selectedIds.value.filter(id => id !== hit.id)
      } else {
        selectedIds.value = [...selectedIds.value, hit.id]
      }
      redraw()
      return
    }

    // 이미 선택된 객체 클릭 → 전체 이동
    if (!selectedIds.value.includes(hit.id)) {
      selectedIds.value = [hit.id]
    }
    pushHistory()
    dragState = {
      type: 'move',
      startX: x, startY: y,
      origPositions: selectedIds.value.map(id => {
        const o = objects.value.find(obj => obj.id === id)
        return { id, x: o.x, y: o.y }
      }),
    }
  } else {
    // 빈 공간 → 러버밴드 시작
    selectedIds.value = []
    rubberBand = { startX: x, startY: y, endX: x, endY: y }
    redraw()
  }
}

function onMouseMove(e) {
  const { x, y } = getPos(e)

  // 러버밴드 업데이트
  if (rubberBand) {
    rubberBand.endX = x
    rubberBand.endY = y
    redraw()
    return
  }

  // 호버 핸들 (단일 선택 시만)
  if (!dragState && selectedId.value) {
    const sel = objects.value.find(o => o.id === selectedId.value)
    hoverHandle.value = sel ? hitHandle(sel, x, y) : null
  }

  if (!dragState) return

  const dx = x - dragState.startX
  const dy = y - dragState.startY

  if (dragState.type === 'move') {
    for (const orig of dragState.origPositions) {
      const obj = objects.value.find(o => o.id === orig.id)
      if (obj) {
        obj.x = Math.max(0, Math.round(orig.x + dx))
        obj.y = Math.max(0, Math.round(orig.y + dy))
      }
    }
  } else {
    // 리사이즈 (단일)
    const obj = objects.value.find(o => o.id === selectedId.value)
    if (!obj) return
    const { handle, origX, origY, origW, origH } = dragState
    let nx = origX, ny = origY, nw = origW, nh = origH
    const MIN = 24
    if (handle.includes('e')) nw = Math.max(MIN, origW + dx)
    if (handle.includes('s')) nh = Math.max(MIN, origH + dy)
    if (handle.includes('w')) { nx = origX + dx; nw = Math.max(MIN, origW - dx) }
    if (handle.includes('n')) { ny = origY + dy; nh = Math.max(MIN, origH - dy) }
    obj.x = Math.round(nx); obj.y = Math.round(ny)
    obj.w = Math.round(nw); obj.h = Math.round(nh)
  }
  redraw()
}

function onMouseUp() {
  if (rubberBand) {
    const rx1 = Math.min(rubberBand.startX, rubberBand.endX)
    const ry1 = Math.min(rubberBand.startY, rubberBand.endY)
    const rx2 = Math.max(rubberBand.startX, rubberBand.endX)
    const ry2 = Math.max(rubberBand.startY, rubberBand.endY)
    if (rx2 - rx1 > 4 || ry2 - ry1 > 4) {
      selectedIds.value = objects.value
        .filter(o => o.x < rx2 && o.x + o.w > rx1 && o.y < ry2 && o.y + o.h > ry1)
        .map(o => o.id)
    }
    rubberBand = null
    redraw()
    return
  }
  if (dragState) { save(); dragState = null }
}

// ── Actions ───────────────────────────────────────────────────────────────────

function deleteSelected() {
  if (!selectedIds.value.length) return
  objects.value = objects.value.filter(o => !selectedIds.value.includes(o.id))
  selectedIds.value = []
}

function clearAll() {
  if (objects.value.length === 0) return
  if (confirm('모든 객체를 삭제하시겠습니까?')) {
    pushHistory()
    objects.value = []
    selectedIds.value = []
  }
}

function exportImage() {
  const prevSel = selectedIds.value
  selectedIds.value = []
  nextTick(() => {
    redraw()
    const link = document.createElement('a')
    link.download = `map_classroom_${route.params.id}.png`
    link.href = canvasEl.value.toDataURL('image/png')
    link.click()
    selectedIds.value = prevSel
    nextTick(redraw)
  })
}
</script>
