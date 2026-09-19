<template>
  <div class="ds-root flex h-full flex-col overflow-hidden">

    <header class="shrink-0 bg-canvas p-section pb-gutter">
      <div class="mx-auto flex w-full max-w-[1680px] items-end justify-between gap-section">
        <div class="min-w-0">
          <router-link to="/classrooms" class="text-sm text-fg-muted transition-colors hover:text-fg">← 목록</router-link>
          <h1 class="mt-1 text-3xl font-bold tracking-tight text-fg">맵 에디터</h1>
          <p class="mt-1 text-lg text-fg-muted">{{ classroom?.name }}의 좌석 배치와 CCTV 위치를 설정합니다</p>
        </div>
        <div class="flex shrink-0 items-center gap-3 text-xs text-fg-muted">
          <template v-if="seatAssignMode">
            <span class="mr-1 inline-block h-2 w-2 rounded-full" :style="{ background: getCctvColor(assigningCctvId) }" />
            <span class="font-medium text-state-unknown">자리 선택 모드</span>
            책상을 클릭하여 배정 / ESC 종료
          </template>
          <template v-else-if="activeTool">
            <span class="font-medium text-fg">{{ TOOLS.find(t => t.type === activeTool)?.label }}</span>
            선택한 뒤 캔버스를 클릭해 배치
          </template>
          <template v-else>
            클릭 또는 드래그로 객체 선택
          </template>
        </div>
      </div>
    </header>

    <div class="mx-auto grid min-h-0 w-full max-w-[1680px] flex-1 grid-cols-[18rem_minmax(0,1fr)] gap-gutter overflow-hidden bg-canvas p-gutter">

    <!-- Sidebar -->
    <aside class="flex min-h-0 flex-col overflow-hidden rounded-card border border-line bg-card shadow-card">
      <div class="flex-1 overflow-y-auto p-3">
      <section class="space-y-1">
        <h2 class="px-3 pb-2 pt-1 text-sm font-semibold text-fg">객체 배치</h2>

      <button
        v-for="tool in TOOLS"
        :key="tool.type"
        @click="activeTool = activeTool === tool.type ? null : tool.type"
        :class="[
          'relative flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left text-base transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-fg-muted',
          activeTool === tool.type
            ? 'bg-line/60 font-medium text-fg'
            : 'text-fg-muted hover:bg-line/40 hover:text-fg'
        ]"
      >
        <span v-if="activeTool === tool.type" class="absolute inset-y-2 left-0 w-0.5 rounded-full bg-fg" />
        <span
          :class="[
            'flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border transition-colors',
            activeTool === tool.type
              ? 'border-fg/15 bg-card text-fg'
              : 'border-line bg-canvas text-fg-muted'
          ]"
        >
          <NavIcon :name="tool.icon" :size="18" />
        </span>
        <span>{{ tool.label }}</span>
      </button>
      </section>

      <!-- 책상 이름 (책상 선택 시) -->
      <template v-if="selectedDesk">
        <div class="my-4 border-t border-line" />
        <section class="space-y-2 px-3">
        <h2 class="text-sm font-semibold text-fg">책상 이름</h2>
        <input
          v-model="selectedDesk.label"
          placeholder="예: A1, 앞줄 1번"
          class="w-full rounded-lg border border-line bg-canvas px-3 py-2 text-sm text-fg placeholder:text-fg-muted focus:outline-none focus-visible:border-fg-muted"
          @keydown.stop
        />
        <p class="text-xs text-fg-muted">이름을 입력하면 캔버스에 표시됩니다.</p>
        </section>
      </template>

      <!-- CCTV 설정 (CCTV 선택 시) -->
      <template v-if="selectedCCTV">
        <div class="my-4 border-t border-line" />
        <section class="space-y-2 px-3">
        <h2 class="text-sm font-semibold text-fg">CCTV 설정</h2>
        <label class="block text-sm text-fg-muted">이름</label>
        <input
          v-model="selectedCCTV.label"
          placeholder="예: CCTV 1"
          class="w-full rounded-lg border border-line bg-canvas px-3 py-2 text-sm text-fg placeholder:text-fg-muted focus:outline-none focus-visible:border-fg-muted"
          @keydown.stop
        />
        <div class="flex items-center justify-between pt-2">
          <div class="text-sm text-fg-muted">담당 자리</div>
          <div class="flex items-center gap-1.5">
            <div class="w-2.5 h-2.5 rounded-full flex-shrink-0" :style="{ background: getCctvColor(selectedCCTV.id) }" />
            <span class="text-sm font-semibold" :style="{ color: getCctvColor(selectedCCTV.id) }">
              {{ objects.filter(o => o.type === 'desk' && (o.cctvIds ?? (o.cctvId != null ? [o.cctvId] : [])).includes(selectedCCTV.id)).length }}자리
            </span>
          </div>
        </div>
        <button
          @click="seatAssignMode && assigningCctvId === selectedCCTV.id ? exitSeatAssignMode() : enterSeatAssignMode()"
          :class="[
            'w-full rounded-lg px-3 py-2 text-sm font-medium transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-fg-muted',
            seatAssignMode && assigningCctvId === selectedCCTV.id
              ? 'text-white'
              : 'border border-line text-fg-muted hover:bg-line/40 hover:text-fg'
          ]"
          :style="seatAssignMode && assigningCctvId === selectedCCTV.id ? { background: getCctvColor(selectedCCTV.id) } : {}"
        >
          <span class="inline-flex items-center justify-center gap-1.5">
            <NavIcon :name="seatAssignMode && assigningCctvId === selectedCCTV.id ? 'seats' : 'pin'" :size="16" />
            {{ seatAssignMode && assigningCctvId === selectedCCTV.id ? '선택 완료' : '자리 선택 모드' }}
          </span>
        </button>
        </section>
      </template>

      <template v-if="selectedRotatable">
        <div class="my-4 border-t border-line" />
        <section class="space-y-2 px-3">
        <div class="flex items-center justify-between">
          <h2 class="text-sm font-semibold text-fg">각도</h2>
          <span class="text-sm font-medium text-fg-muted">{{ selectedRotatable.angle ?? 0 }}°</span>
        </div>
        <div class="grid grid-cols-2 gap-2">
          <button
            type="button"
            class="rounded-lg border border-line px-3 py-2 text-sm font-medium text-fg-muted transition-colors hover:bg-line/40 hover:text-fg focus-visible:outline focus-visible:outline-2 focus-visible:outline-fg-muted"
            @click="rotateSelected(-15)"
          >-15°</button>
          <button
            type="button"
            class="rounded-lg border border-line px-3 py-2 text-sm font-medium text-fg-muted transition-colors hover:bg-line/40 hover:text-fg focus-visible:outline focus-visible:outline-2 focus-visible:outline-fg-muted"
            @click="rotateSelected(15)"
          >+15°</button>
        </div>
        </section>
      </template>

      <div class="my-4 border-t border-line" />

      <section class="space-y-2 px-3">
      <h2 class="text-sm font-semibold text-fg">맵 크기</h2>
      <label class="block text-sm text-fg-muted">가로 (px)</label>
      <input type="number" v-model.number="mapW" min="900" max="2400" step="50"
        class="w-full rounded-lg border border-line bg-canvas px-3 py-2 text-sm text-fg focus:outline-none focus-visible:border-fg-muted" />
      <label class="block text-sm text-fg-muted">세로 (px)</label>
      <input type="number" v-model.number="mapH" min="840" max="1600" step="50"
        class="w-full rounded-lg border border-line bg-canvas px-3 py-2 text-sm text-fg focus:outline-none focus-visible:border-fg-muted" />
      </section>
      </div>

      <div class="shrink-0 space-y-2 border-t border-line p-4">
      <button
        @click="deleteSelected"
        :disabled="!selectedIds.length"
        class="flex w-full items-center justify-center gap-2 rounded-lg border border-state-alert/30 px-3 py-2.5 text-sm font-medium text-state-alert transition-colors hover:bg-state-alert/10 disabled:cursor-not-allowed disabled:opacity-30"
      ><NavIcon name="trash" :size="16" /> 삭제{{ selectedIds.length > 1 ? ` (${selectedIds.length})` : '' }}</button>
      <button
        @click="clearAll"
        class="w-full rounded-lg border border-line px-3 py-2.5 text-sm font-medium text-fg-muted transition-colors hover:bg-line/40 hover:text-fg"
      >전체 지우기</button>
      <button
        @click="exportImage"
        class="flex w-full items-center justify-center gap-2 rounded-lg bg-fg px-3 py-3 text-sm font-semibold text-canvas transition-opacity hover:opacity-90 focus-visible:outline focus-visible:outline-2 focus-visible:outline-fg-muted"
      ><NavIcon name="image" :size="17" /> 이미지 저장</button>
      </div>
    </aside>

    <!-- Main area -->
    <div class="flex min-w-0 flex-col overflow-hidden rounded-card border border-line bg-card shadow-card">

      <!-- Top bar -->
      <div class="hidden">
        <span class="flex items-center gap-3 text-xs text-fg-muted">
          <template v-if="seatAssignMode">
            <span class="mr-1 inline-block h-2 w-2 rounded-full" :style="{ background: getCctvColor(assigningCctvId) }" />
            <span class="font-medium text-state-unknown">자리 선택 모드</span>
            — 책상을 클릭하여 배정 / 다시 클릭하면 해제 | ESC 종료
          </template>
          <template v-else-if="activeTool">
            <span class="font-medium text-fg">{{ TOOLS.find(t => t.type === activeTool)?.label }}</span>
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
          <span class="text-line">|</span>
          <button @click="undo" :disabled="historyIdx <= 0" class="rounded-md px-2 py-1 transition-colors hover:text-fg disabled:opacity-30" title="되돌리기 (Ctrl+Z)">↩ 되돌리기</button>
          <button @click="redo" :disabled="historyIdx >= history.length - 1" class="rounded-md px-2 py-1 transition-colors hover:text-fg disabled:opacity-30" title="다시실행 (Ctrl+Y)">↪ 다시실행</button>
        </span>
      </div>

      <!-- Canvas scroll area -->
      <div
        ref="scrollEl"
        class="flex flex-1 items-start justify-center overflow-auto bg-canvas p-gutter"
      >
        <div class="relative inline-block">
          <canvas
            ref="canvasEl"
            :width="mapW"
            :height="mapH"
            class="block rounded-card border border-line bg-white shadow-xl"
            :style="{ cursor: cursorStyle }"
            @mousedown="onMouseDown"
            @mousemove="onMouseMove"
            @mouseup="onMouseUp"
            @mouseleave="onMouseUp"
          />
          <div
            class="absolute -bottom-1.5 -right-1.5 h-4 w-4 cursor-nwse-resize rounded-sm border-2 border-fg-muted bg-card"
            title="드래그해서 맵 크기 조절"
            @mousedown="onMapResizeMouseDown"
          />
        </div>
      </div>
    </div>
    </div>

    <ErrorNotice v-if="cStore.error" legacy class="fixed top-4 left-1/2 z-40 w-[28rem] max-w-[90vw] -translate-x-1/2 shadow-lg" title="교실 정보를 불러오지 못했습니다" :message="cStore.error" @retry="cStore.fetchOne(Number(route.params.id))" />

    <!-- 서버 저장 실패 알림: 로컬 캐시에는 저장돼 있지만 서버에는 반영되지 않았다는 뜻 -->
    <div
      v-if="saveError"
      role="alert"
      class="fixed bottom-4 right-4 z-40 max-w-md flex items-start gap-3 rounded-xl border border-red-200 dark:border-red-500/30 bg-red-50 dark:bg-red-500/10 px-4 py-3 text-sm text-red-700 dark:text-red-300 shadow-lg"
    >
      <p class="flex-1">{{ saveError }}<br><span class="text-xs opacity-80">이 브라우저에는 저장됐지만 서버에는 아직 반영되지 않았습니다.</span></p>
      <button type="button" class="shrink-0 rounded-lg border border-red-300 dark:border-red-500/40 px-3 py-1 text-xs font-medium hover:bg-red-100 dark:hover:bg-red-500/20" @click="retryBackendSave">다시 저장</button>
      <button type="button" class="shrink-0 text-red-400 hover:text-red-600 leading-none" aria-label="닫기" @click="saveError = ''">✕</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount, onUnmounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { useClassroomStore } from '@/stores/classroomStore.js'
import ErrorNotice from '@/components/ui/ErrorNotice.vue'
import NavIcon from '@/components/ui/NavIcon.vue'
import api from '@/api'

const TOOLS = [
  { type: 'cctv',  label: 'CCTV', icon: 'camera', defaultW: 72, defaultH: 63 },
  { type: 'desk',  label: '책상',  icon: 'desk',   defaultW: 87, defaultH: 59 },
  { type: 'chair', label: '의자',  icon: 'chair',  defaultW: 51, defaultH: 45 },
]

const HANDLE_R = 6
const CCTV_COLORS = ['#147b70', '#5b6b82', '#9a6a0e', '#c7403d', '#0f766e', '#0369a1', '#b45309', '#4d7c0f']
const MAP_STYLES = {
  border: '#a9b3c2',
  chair: '#e2e8f1',
  text: '#061735',
  mutedText: '#53647f',
  empty: '#5b6b82',
  occupied: '#147b70',
  unknown: '#9a6a0e',
  selected: '#147b70',
}

function getCctvColor(cctvId) {
  const cctvs = objects.value.filter(o => o.type === 'cctv')
  const idx = cctvs.findIndex(o => o.id === cctvId)
  return idx >= 0 ? CCTV_COLORS[idx % CCTV_COLORS.length] : '#94a3b8'
}

const route = useRoute()
const cStore = useClassroomStore()
const classroom = computed(() => cStore.current)

const canvasEl = ref(null)
const DEFAULT_MAP_W = 900
const DEFAULT_MAP_H = 840
const mapW = ref(DEFAULT_MAP_W)
const mapH = ref(DEFAULT_MAP_H)
const objects = ref([])
const selectedIds = ref([])          // 다중 선택 ID 배열
const activeTool = ref(null)
const hoverHandle = ref(null)
const seatAssignMode = ref(false)
const assigningCctvId = ref(null)

// ── 맵 크기 드래그 조절 ──────────────────────────────────────────────────────
const MAP_W_MIN = DEFAULT_MAP_W, MAP_W_MAX = 2400
const MAP_H_MIN = DEFAULT_MAP_H, MAP_H_MAX = 1600
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

const selectedRotatable = computed(() => {
  if (selectedIds.value.length !== 1) return null
  const obj = objects.value.find(o => o.id === selectedIds.value[0])
  return obj && ['desk', 'chair'].includes(obj.type) ? obj : null
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

function normalizeAngle(angle) {
  return ((angle % 360) + 360) % 360
}

function rotateSelected(delta) {
  const obj = selectedRotatable.value
  if (!obj) return
  pushHistory()
  obj.angle = normalizeAngle((obj.angle ?? 0) + delta)
  save()
  redraw()
}

// ── Persistence ───────────────────────────────────────────────────────────────
const storageKey = computed(() => `map_${route.params.id}`)

// 화면을 열면서 서버 배치도를 불러오는 것도 objects 변경이라 watch가 save()를 부른다. 서버 저장(seat-counts)은
// 카메라의 seat_ids를 덮어쓰고 맵에 없는 좌석의 seat_lines를 지우므로, 사용자가 편집하기 전에는 서버로 보내지 않는다.
let _userMayEdit = false

function save() {
  localStorage.setItem(storageKey.value, JSON.stringify({
    objects: objects.value, mapW: mapW.value, mapH: mapH.value,
  }))
  if (_userMayEdit) scheduleBackendSave()
}

// 서버 저장은 편집이 멈춘 1.5초 뒤에 한 번만 보낸다. 세 요청 모두 관리자 전용이라 axios(api)로 보내
// 인터셉터가 Authorization을 붙이게 하고, 실패하면 saveError로 화면에 알린다.
const saveError = ref('')
let _backendSaveTimer = null
let _savePendingId = null   // 아직 서버에 보내지 않은 편집이 있으면 그 교실 id
let _unmounted = false

function scheduleBackendSave() {
  // 화면을 떠나는 중에는 route.params가 다음 화면 값일 수 있어 예약 시점의 교실 id를 붙들어 둔다
  _savePendingId = route.params.id
  clearTimeout(_backendSaveTimer)
  _backendSaveTimer = setTimeout(syncToBackend, 1500)
}

async function syncToBackend() {
  clearTimeout(_backendSaveTimer)
  _backendSaveTimer = null
  const id = _savePendingId ?? route.params.id
  _savePendingId = null

  const jobs = []   // [이름, Promise]

  if (canvasEl.value) {
    const b64 = canvasEl.value.toDataURL('image/png').replace('data:image/png;base64,', '')
    jobs.push(['배치도 이미지', api.post(`/analysis/${id}/map-image`, { image: b64 })])
  }

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
    jobs.push(['자리 배정', api.post(`/analysis/${id}/seat-counts`, { seat_counts: seatCounts, seat_ids: seatIds })])
  }

  // 배치도 JSON 백엔드 동기화 (Slack 전송용)
  jobs.push(['배치도 데이터', api.put(`/classrooms/${id}/map-data`, { objects: objects.value, mapW: mapW.value, mapH: mapH.value })])

  const results = await Promise.allSettled(jobs.map(([, p]) => p))
  const failed = results.flatMap((r, i) => (r.status === 'rejected' ? [{ name: jobs[i][0], reason: r.reason }] : []))
  if (!failed.length) { saveError.value = ''; return }

  const first = failed[0].reason
  const detail = first?.response?.data?.detail ?? first?.message ?? '알 수 없는 오류'
  saveError.value = `서버 저장 실패 (${failed.map(f => f.name).join(', ')}): ${detail}`
  if (_unmounted) console.warn('[map] 화면을 떠나며 저장하지 못했습니다:', saveError.value)
}

function retryBackendSave() {
  _savePendingId = route.params.id
  return syncToBackend()
}

function applyMapData(data) {
  const sourceW = data.mapW ?? DEFAULT_MAP_W
  const sourceH = data.mapH ?? DEFAULT_MAP_H
  const targetW = Math.max(DEFAULT_MAP_W, sourceW)
  const targetH = Math.max(DEFAULT_MAP_H, sourceH)
  const scaleX = targetW / sourceW
  const scaleY = targetH / sourceH

  objects.value = (data.objects ?? []).map(o => ({
    ...o,
    x: Math.round(o.x * scaleX),
    y: Math.round(o.y * scaleY),
    w: Math.round(o.w * scaleX),
    h: Math.round(o.h * scaleY),
  }))
  mapW.value = targetW
  mapH.value = targetH
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
  // 불러오기로 인한 watch 실행이 끝난 뒤부터의 변경만 사용자 편집으로 본다
  nextTick(() => { pushHistory(); redraw(); _userMayEdit = true })
  window.addEventListener('keydown', onKeyDown)
})

// 편집 직후(1.5초 안)에 화면을 떠나도 서버 저장이 사라지지 않도록, 대기 중인 저장이 있으면 캔버스가
// 아직 있는 지금 바로 보내고 타이머는 정리한다. 이 화면은 서버 데이터를 우선 불러오므로 버리면 편집이 사라진다.
onBeforeUnmount(() => {
  _unmounted = true
  const pending = _savePendingId != null
  clearTimeout(_backendSaveTimer)
  _backendSaveTimer = null
  if (pending) syncToBackend()
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
  ctx.fillStyle = '#ffffff'
  ctx.fillRect(0, 0, mapW.value, mapH.value)
  drawCanvasFrame(ctx)
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
    ctx.fillStyle = 'rgba(20,123,112,0.10)'
    ctx.fillRect(rx, ry, rw, rh)
    ctx.strokeStyle = '#147b70'
    ctx.lineWidth = 1
    ctx.setLineDash([4, 3])
    ctx.strokeRect(rx, ry, rw, rh)
    ctx.setLineDash([])
    ctx.restore()
  }
}

function drawGrid(ctx) {
  ctx.strokeStyle = '#eef2f7'
  ctx.lineWidth = 1
  for (let x = 0; x <= mapW.value; x += 40) {
    ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, mapH.value); ctx.stroke()
  }
  for (let y = 0; y <= mapH.value; y += 40) {
    ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(mapW.value, y); ctx.stroke()
  }
}

function drawCanvasFrame(ctx) {
  ctx.save()
  ctx.strokeStyle = '#d8dfea'
  ctx.lineWidth = 1
  ctx.beginPath()
  ctx.roundRect(1, 1, mapW.value - 2, mapH.value - 2, 14)
  ctx.stroke()

  ctx.restore()
}

function drawObject(ctx, obj, isSelected) {
  if (isRotatable(obj) && obj.angle) {
    drawRotatedObject(ctx, obj, isSelected)
    return
  }

  if (obj.type === 'cctv') drawCCTV(ctx, obj, isSelected)
  else if (obj.type === 'desk') drawDesk(ctx, obj, isSelected)
  else if (obj.type === 'chair') drawChair(ctx, obj, isSelected)

  if (isSelected) {
    drawSelection(ctx, obj)
  }
}

function isRotatable(obj) {
  return obj && ['desk', 'chair'].includes(obj.type)
}

function drawRotatedObject(ctx, obj, isSelected) {
  const localObj = { ...obj, x: -obj.w / 2, y: -obj.h / 2 }
  ctx.save()
  ctx.translate(obj.x + obj.w / 2, obj.y + obj.h / 2)
  ctx.rotate((obj.angle ?? 0) * Math.PI / 180)
  if (obj.type === 'desk') drawDesk(ctx, localObj, isSelected)
  else if (obj.type === 'chair') drawChair(ctx, localObj, isSelected)
  if (isSelected) drawSelection(ctx, localObj)
  ctx.restore()
}

function drawSelection(ctx, obj) {
  ctx.save()
  ctx.strokeStyle = '#147b70'
  ctx.lineWidth = 1.5
  ctx.setLineDash([5, 4])
  ctx.strokeRect(obj.x - 4, obj.y - 4, obj.w + 8, obj.h + 8)
  ctx.setLineDash([])

  // 리사이즈 핸들은 단일 선택일 때만
  if (selectedIds.value.length === 1) {
    for (const h of getLocalHandles(obj)) {
      ctx.fillStyle = '#fff'
      ctx.strokeStyle = '#147b70'
      ctx.lineWidth = 1.5
      ctx.beginPath()
      ctx.rect(h.hx - HANDLE_R, h.hy - HANDLE_R, HANDLE_R * 2, HANDLE_R * 2)
      ctx.fill()
      ctx.stroke()
    }
  }
  ctx.restore()
}

function drawDesk(ctx, obj, isSelected) {
  const { x, y, w, h } = obj
  // Body - tint if assigned in assign mode (다중 CCTV 지원, 구버전 cctvId 마이그레이션)
  const cctvIds = obj.cctvIds ?? (obj.cctvId != null ? [obj.cctvId] : [])
  const isAssignedToActive = seatAssignMode.value && cctvIds.includes(assigningCctvId.value)
  ctx.fillStyle = isAssignedToActive ? '#f1f8f6' : '#ffffff'
  ctx.strokeStyle = isSelected ? MAP_STYLES.selected : MAP_STYLES.border
  ctx.lineWidth = 4
  ctx.beginPath(); ctx.roundRect(x, y, w, h, 14); ctx.fill(); ctx.stroke()
  // Label
  ctx.font = `700 ${Math.min(h * 0.42, 34)}px sans-serif`
  ctx.fillStyle = MAP_STYLES.text
  ctx.textAlign = 'center'; ctx.textBaseline = 'middle'
  ctx.fillText(obj.label?.trim() || '책상', x + w / 2, y + h / 2 + 1)
}

function drawChair(ctx, obj, isSelected) {
  const { x, y, w, h } = obj
  ctx.fillStyle = MAP_STYLES.chair
  ctx.strokeStyle = isSelected ? MAP_STYLES.selected : MAP_STYLES.chair
  ctx.lineWidth = isSelected ? 3 : 1
  ctx.beginPath(); ctx.roundRect(x, y, w, h, 9); ctx.fill(); ctx.stroke()
}

function drawCCTV(ctx, obj, isSelected) {
  const { x, y, w, h } = obj
  // Label (이름이 설정되면 이름 표시, 아니면 CCTV)
  const label = obj.label?.trim()
  ctx.fillStyle = '#ffffff'
  ctx.strokeStyle = isSelected ? MAP_STYLES.selected : MAP_STYLES.border
  ctx.lineWidth = 4
  ctx.beginPath(); ctx.roundRect(x, y, w, h, 14); ctx.fill(); ctx.stroke()

  ctx.fillStyle = MAP_STYLES.mutedText
  ctx.font = `700 ${Math.min(h * 0.24, 26)}px sans-serif`
  ctx.textAlign = 'center'; ctx.textBaseline = 'middle'
  ctx.fillText(label || 'CCTV', x + w / 2, y + h / 2)
  ctx.textAlign = 'left'
}

function getHandles(obj) {
  const handles = getLocalHandles(obj)
  if (!isRotatable(obj) || !obj.angle) return handles
  return handles.map(h => ({ ...h, ...rotatePoint(obj, h.hx, h.hy) }))
}

function getLocalHandles(obj) {
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

function rotatePoint(obj, px, py) {
  const cx = obj.x + obj.w / 2
  const cy = obj.y + obj.h / 2
  const rad = (obj.angle ?? 0) * Math.PI / 180
  const cos = Math.cos(rad)
  const sin = Math.sin(rad)
  const dx = px - cx
  const dy = py - cy
  return {
    hx: cx + dx * cos - dy * sin,
    hy: cy + dx * sin + dy * cos,
  }
}

function unrotatePoint(obj, px, py) {
  const cx = obj.x + obj.w / 2
  const cy = obj.y + obj.h / 2
  const rad = -(obj.angle ?? 0) * Math.PI / 180
  const cos = Math.cos(rad)
  const sin = Math.sin(rad)
  const dx = px - cx
  const dy = py - cy
  return {
    x: cx + dx * cos - dy * sin,
    y: cy + dx * sin + dy * cos,
  }
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
    const p = isRotatable(o) && o.angle ? unrotatePoint(o, px, py) : { x: px, y: py }
    if (p.x >= o.x && p.x <= o.x + o.w && p.y >= o.y && p.y <= o.y + o.h) return o
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
    if (['desk', 'chair'].includes(activeTool.value)) newObj.angle = 0
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
