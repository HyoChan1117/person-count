<template>
  <div class="ds-root h-full overflow-y-auto p-section">
    <div class="mx-auto max-w-[1680px]">

      <!-- 헤더 -->
      <header class="mb-section flex items-end justify-between gap-section">
        <div class="min-w-0">
          <router-link to="/classrooms" class="text-sm text-fg-muted transition-colors hover:text-fg">← 좌석 확인</router-link>
          <div class="mt-1 flex items-center gap-3">
            <h1 class="text-3xl font-bold tracking-tight text-fg">{{ classroom?.name }}</h1>
            <span v-if="mockActive" class="rounded-full border border-line px-2.5 py-0.5 text-xs font-medium text-fg-muted">목데이터</span>
          </div>
          <p class="mt-1 text-lg text-fg-muted">실시간 인원 현황</p>
        </div>

        <div class="flex shrink-0 items-center gap-gutter">
          <button type="button" :class="[BTN_OUTLINE, mockActive ? '!border-fg-muted !bg-line !text-fg' : '']" :aria-pressed="mockActive" @click="toggleMock">
            {{ mockActive ? '목데이터 끄기' : '목데이터로 보기' }}
          </button>

          <div class="flex items-center gap-1 rounded-card border border-line bg-card p-1.5">
            <button type="button" :disabled="seatLoading" :class="BTN_PRIMARY" @click="fetchSeatOccupancy">
              {{ seatLoading ? '분석 중...' : 'YOLO 분석' }}
            </button>
            <button v-if="classroom" type="button" title="좌석 점유 프롬프트 편집" aria-label="좌석 점유 프롬프트 편집" :class="BTN_ICON" @click="seatPromptOpen = true">
              <NavIcon name="settings" :size="18" />
            </button>

            <span class="mx-1 h-6 w-px bg-line" aria-hidden="true" />

            <button type="button" :disabled="yoloLlmLoading" :class="BTN_GHOST" @click="fetchYoloLlm">
              {{ yoloLlmLoading ? '분석 중...' : 'YOLO+LLM' }}
            </button>
            <button v-if="classroom" type="button" title="YOLO+LLM 프롬프트 편집" aria-label="YOLO+LLM 프롬프트 편집" :class="BTN_ICON" @click="yoloLlmPromptOpen = true">
              <NavIcon name="settings" :size="18" />
            </button>

            <span class="mx-1 h-6 w-px bg-line" aria-hidden="true" />

            <button type="button" :class="[BTN_GHOST, liveOn ? '!bg-line' : '']" :aria-pressed="liveOn" @click="toggleLive">
              <span class="h-2 w-2 rounded-full" :class="liveOn ? 'bg-fg' : 'bg-fg-muted/60'" aria-hidden="true" />
              {{ liveOn ? '실시간 종료' : '실시간 탐지' }}
            </button>
          </div>
        </div>
      </header>

      <ErrorNotice v-if="cStore.error" class="mb-section" title="교실 정보를 불러오지 못했습니다" :message="cStore.error" @retry="cStore.fetchOne(Number(route.params.id))" />

      <!-- 실시간 YOLO 탐지 -->
      <section v-if="liveOn" class="mb-section" aria-label="실시간 탐지">
        <p v-if="!liveCameras.length" class="rounded-card border border-line bg-card py-12 text-center text-base text-fg-muted">
          RTSP가 설정된 카메라가 없습니다.
        </p>
        <UiCard v-else :padded="false" class="mx-auto w-full max-w-5xl overflow-hidden">
          <div class="flex items-center justify-between gap-2 border-b border-line px-card py-3">
            <div class="flex items-center gap-2">
              <span class="h-2 w-2 shrink-0 rounded-full bg-fg" aria-hidden="true" />
              <select v-model="liveCameraId" aria-label="카메라 선택" class="rounded-md bg-transparent py-1 text-base font-medium text-fg outline-none focus-visible:outline focus-visible:outline-2 focus-visible:outline-fg-muted">
                <option v-for="cam in liveCameras" :key="cam.camera_id" :value="cam.camera_id">{{ cam.name }}</option>
              </select>
            </div>
            <button type="button" title="전체화면" :class="LINK_QUIET" @click="toggleFullscreen">전체화면</button>
          </div>
          <!-- 실시간 영상에는 얼굴이 나오므로 기본 블러. 스트림은 보는 동안 계속 봐야 해서 자동 재블러 없이 화면을 나가거나 카메라를 바꾸면 다시 블러 -->
          <BlurredImage ref="liveImgRef" :key="liveKey" :src="liveSrc" alt="실시간 카메라 영상" :rounded="false" :auto-reblur-ms="0" class="aspect-video w-full" />
        </UiCard>
        <p class="mx-auto mt-2 max-w-5xl text-sm text-fg-muted">부하를 줄이기 위해 한 번에 카메라 1대만 실시간으로 표시합니다.</p>
      </section>

      <div class="flex flex-col gap-section">

        <!-- 좌석 점유 결과 (YOLO) -->
        <div v-if="seatLoading" role="status" class="flex flex-col items-center justify-center gap-3 py-24 text-base text-fg-muted">
          <div class="h-9 w-9 animate-spin rounded-full border-2 border-line border-t-fg-muted" />
          <p>분석 중...</p>
        </div>

        <section v-else-if="seatResult" class="flex flex-col gap-gutter" aria-label="YOLO 분석 결과">
          <AnalysisSummaryCard label="YOLO 분석" :occupied="seatSummary.occupied" :total="seatSummary.judgeable" :unknown="seatSummary.unknown" />

          <!-- 배치도 + 카메라별 카드 -->
          <div class="grid items-start gap-gutter" :class="hasMap ? 'grid-cols-2' : 'grid-cols-1'">
            <UiCard v-if="hasMap">
              <div class="flex items-center justify-between">
                <h2 class="text-lg font-semibold text-fg">교실 배치도</h2>
                <ul class="flex items-center gap-4 text-sm text-fg-muted" aria-label="범례">
                  <li v-for="l in LEGEND" :key="l.label" class="flex items-center gap-1.5"><span class="h-3 w-3 rounded-sm" :class="l.dot" />{{ l.label }}</li>
                </ul>
              </div>
              <canvas ref="mapCanvasRef" class="mt-card block w-full" aria-label="교실 배치도 점유 현황" />
            </UiCard>

            <div class="grid gap-gutter" :class="hasMap ? 'grid-cols-1 xl:grid-cols-2' : 'grid-cols-2 xl:grid-cols-3'">
              <CameraSeatCard v-for="cam in seatResult.cameras" :key="cam.camera_id" :cam="cam" unknown-on-error />
            </div>
          </div>
        </section>

        <!-- YOLO+LLM 결과 -->
        <div v-if="yoloLlmLoading" role="status" class="flex flex-col items-center justify-center gap-3 py-24 text-base text-fg-muted">
          <div class="h-9 w-9 animate-spin rounded-full border-2 border-line border-t-fg-muted" />
          <p>YOLO+LLM 분석 중...</p>
        </div>

        <section v-else-if="yoloLlmResult" class="flex flex-col gap-gutter" aria-label="YOLO+LLM 분석 결과">
          <!-- 구분선 -->
          <div v-if="seatResult" class="flex items-center gap-3">
            <div class="h-px flex-1 bg-line" />
            <span class="px-2 text-sm font-medium text-fg-muted">YOLO+LLM 분석</span>
            <div class="h-px flex-1 bg-line" />
          </div>

          <AnalysisSummaryCard label="YOLO+LLM 분석" :occupied="yoloLlmResult.total_occupied" :total="yoloLlmResult.total_seats" />

          <div class="grid items-start gap-gutter" :class="hasMap ? 'grid-cols-2' : 'grid-cols-1'">
            <UiCard v-if="hasMap">
              <div class="flex items-center justify-between">
                <h2 class="text-lg font-semibold text-fg">교실 배치도</h2>
                <ul class="flex items-center gap-4 text-sm text-fg-muted" aria-label="범례">
                  <li v-for="l in LEGEND" :key="l.label" class="flex items-center gap-1.5"><span class="h-3 w-3 rounded-sm" :class="l.dot" />{{ l.label }}</li>
                </ul>
              </div>
              <canvas ref="yoloMapCanvasRef" class="mt-card block w-full" aria-label="교실 배치도 점유 현황(YOLO+LLM)" />
            </UiCard>

            <div class="grid gap-gutter" :class="hasMap ? 'grid-cols-1 xl:grid-cols-2' : 'grid-cols-2 xl:grid-cols-3'">
              <CameraSeatCard v-for="cam in yoloLlmResult.cameras" :key="cam.camera_id" :cam="cam" />
            </div>
          </div>
        </section>

        <!-- 빈 상태: 이 화면에서 처음 보게 되는 안내 -->
        <div v-if="!seatResult && !yoloLlmResult && !seatLoading && !yoloLlmLoading" class="flex flex-col items-center justify-center gap-3 py-28 text-center">
          <span class="flex h-14 w-14 items-center justify-center rounded-card border border-line bg-card text-fg-muted">
            <NavIcon name="seats" :size="28" />
          </span>
          <p class="text-lg font-semibold text-fg">분석을 시작하세요</p>
          <p class="max-w-md text-sm text-fg-muted">상단의 'YOLO 분석'이나 'YOLO+LLM'을 누르면 카메라 영상으로 좌석 점유를 계산합니다.</p>
        </div>

      </div>
    </div>

    <!-- 좌석 점유 프롬프트 모달 -->
    <Teleport to="body">
      <SeatPromptModal
        v-if="seatPromptOpen && classroom"
        :classroom="classroom"
        @close="seatPromptOpen = false"
      />
    </Teleport>

    <!-- YOLO+LLM 프롬프트 모달 -->
    <Teleport to="body">
      <ClassroomPromptModal
        v-if="yoloLlmPromptOpen && classroom"
        :classroom="classroom"
        @close="yoloLlmPromptOpen = false"
      />
    </Teleport>

  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useClassroomStore } from '@/stores/classroomStore.js'
import { useThemeStore } from '@/stores/themeStore'
import SeatPromptModal from '@/components/modals/SeatPromptModal.vue'
import ClassroomPromptModal from '@/components/modals/ClassroomPromptModal.vue'
import BlurredImage from '@/components/ui/BlurredImage.vue'
import ErrorNotice from '@/components/ui/ErrorNotice.vue'
import UiCard from '@/components/ui/UiCard.vue'
import NavIcon from '@/components/ui/NavIcon.vue'
import AnalysisSummaryCard from '@/components/dashboard/AnalysisSummaryCard.vue'
import CameraSeatCard from '@/components/dashboard/CameraSeatCard.vue'
import api from '@/api'
import { generateMockImageDataUrl } from '@/utils/mockImage'
import { cssColor } from '@/utils/cssColor'
import { useMockToggle } from '@/composables/useMockToggle'

// 클래스는 Tailwind가 스캔할 수 있도록 전부 리터럴로 적는다.
const FOCUS = 'focus-visible:outline focus-visible:outline-2 focus-visible:outline-fg-muted'
const BTN_OUTLINE = `rounded-lg border border-line px-4 py-2.5 text-sm font-medium text-fg-muted transition-colors hover:border-fg-muted/60 hover:text-fg ${FOCUS}`
const BTN_PRIMARY = `inline-flex items-center gap-1.5 rounded-lg bg-fg px-4 py-2.5 text-sm font-semibold text-canvas transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50 ${FOCUS}`
const BTN_GHOST = `inline-flex items-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium text-fg transition-colors hover:bg-line/60 disabled:cursor-not-allowed disabled:opacity-50 ${FOCUS}`
const BTN_ICON = `flex h-9 w-9 items-center justify-center rounded-lg text-fg-muted transition-colors hover:bg-line/60 hover:text-fg ${FOCUS}`
const LINK_QUIET = `shrink-0 rounded-md px-2 py-1 text-sm text-fg-muted transition-colors hover:text-fg ${FOCUS}`

const LEGEND = [
  { label: '점유', dot: 'bg-state-occupied' },
]

const route = useRoute()
const cStore = useClassroomStore()
const theme = useThemeStore()

const classroom = computed(() => cStore.current)
const seatPromptOpen = ref(false)
const yoloLlmPromptOpen = ref(false)

const seatLoading = ref(false)
const seatResult = ref(null)

// 점유율은 "점유 ÷ 판정 가능 좌석". 캡처에 실패한 카메라는 서버가 좌석 전부를 empty로 돌려주므로
// 빈 좌석이 아니라 판정 불가로 따로 센다(다른 카메라가 같은 좌석을 판정했다면 그 결과를 따른다).
const seatSummary = computed(() => {
  const cams = seatResult.value?.cameras ?? []
  const occ = new Set()
  const emp = new Set()
  const failed = new Set()
  for (const cam of cams) {
    if (cam.error) { (cam.empty ?? []).forEach((s) => failed.add(s)); continue }
    ;(cam.occupied ?? []).forEach((s) => occ.add(s))
    ;(cam.empty ?? []).forEach((s) => emp.add(s))
  }
  emp.forEach((s) => { if (occ.has(s)) emp.delete(s) })
  const unknown = [...failed].filter((s) => !occ.has(s) && !emp.has(s)).length
  return { occupied: occ.size, judgeable: occ.size + emp.size, unknown }
})

const yoloLlmLoading = ref(false)
const yoloLlmResult = ref(null)

const mapData = ref(null)

// ── 목데이터 모드 ────────────────────────────────────────────────────────────

const MOCK_SEAT_IDS = ['1', '2', '3', '4', '5', '6']
const MOCK_CAMERAS = [
  { camera_id: 'MOCK1', name: 'CCTV 1', ip_address: '192.168.0.101', rtsp_url: 'rtsp://mock' },
  { camera_id: 'MOCK2', name: 'CCTV 2', ip_address: '192.168.0.102', rtsp_url: 'rtsp://mock' },
]
const MOCK_MAP_DATA = {
  mapW: 480,
  mapH: 320,
  objects: [
    { id: 1, type: 'cctv', x: 20, y: 20, w: 60, h: 44, label: 'CCTV 1' },
    { id: 2, type: 'cctv', x: 400, y: 20, w: 60, h: 44, label: 'CCTV 2' },
    { id: 3, type: 'desk', x: 60, y: 110, w: 90, h: 55, label: '1' },
    { id: 4, type: 'desk', x: 195, y: 110, w: 90, h: 55, label: '2' },
    { id: 5, type: 'desk', x: 330, y: 110, w: 90, h: 55, label: '3' },
    { id: 6, type: 'desk', x: 60, y: 200, w: 90, h: 55, label: '4' },
    { id: 7, type: 'desk', x: 195, y: 200, w: 90, h: 55, label: '5' },
    { id: 8, type: 'desk', x: 330, y: 200, w: 90, h: 55, label: '6' },
  ],
}

function buildMockAnalysisResult(withActivity) {
  const occupied = MOCK_SEAT_IDS.filter(() => Math.random() > 0.45)
  const cam1Seats = MOCK_SEAT_IDS.slice(0, 3)
  const cam2Seats = MOCK_SEAT_IDS.slice(3)
  const cameras = [
    { camera_id: 'MOCK1', name: 'CCTV 1', total: cam1Seats.length, occupied_count: cam1Seats.filter(s => occupied.includes(s)).length, occupied: cam1Seats.filter(s => occupied.includes(s)), empty: cam1Seats.filter(s => !occupied.includes(s)) },
    { camera_id: 'MOCK2', name: 'CCTV 2', total: cam2Seats.length, occupied_count: cam2Seats.filter(s => occupied.includes(s)).length, occupied: cam2Seats.filter(s => occupied.includes(s)), empty: cam2Seats.filter(s => !occupied.includes(s)) },
  ]
  if (withActivity && occupied.length) {
    const activities = ['공부', '휴대폰', '노트북']
    cameras[0].llm_response = occupied
      .filter(s => cam1Seats.includes(s))
      .map(s => `${s} - ${activities[Math.floor(Math.random() * activities.length)]}`)
      .join('\n')
  }
  return {
    total_occupied: occupied.length,
    total_seats: MOCK_SEAT_IDS.length,
    cameras,
  }
}

function resetAnalysisResults() {
  seatResult.value = null
  yoloLlmResult.value = null
  liveOn.value = false
}

const { mockActive, toggleMock } = useMockToggle(
  () => { resetAnalysisResults(); fetchSeatOccupancy() },
  resetAnalysisResults,
)

// ── 실시간 YOLO 탐지 ─────────────────────────────────────────────────────────

const liveOn = ref(false)
const liveKey = ref(0)
const liveCameraId = ref(null)
const mockLiveImg = ref('')

const liveCameras = computed(() => (mockActive.value ? MOCK_CAMERAS : (classroom.value?.cameras ?? []).filter(c => c.rtsp_url)))

// 목데이터 영상 배경은 디자인 토큰 색을 쓴다(얼굴 사진 없음)
const mockLiveFrame = () => generateMockImageDataUrl('MOCK LIVE FEED', 960, 540, cssColor('canvas'))

function toggleLive() {
  liveOn.value = !liveOn.value
  if (liveOn.value) {
    if (!liveCameraId.value || !liveCameras.value.some(c => c.camera_id === liveCameraId.value)) {
      liveCameraId.value = liveCameras.value[0]?.camera_id ?? null
    }
    liveKey.value++
    if (mockActive.value) mockLiveImg.value = mockLiveFrame()
  }
}

// 카메라를 바꿀 때도 이전 스트림이 남지 않도록 <img>를 완전히 새로 만든다
watch(liveCameraId, () => {
  if (!liveOn.value) return
  liveKey.value++
  if (mockActive.value) mockLiveImg.value = mockLiveFrame()
})

const liveSrc = computed(() => {
  if (mockActive.value) return mockLiveImg.value
  return `/api/analysis/${route.params.id}/live/${liveCameraId.value}?t=${liveKey.value}`
})

const liveImgRef = ref(null)

function toggleFullscreen() {
  if (document.fullscreenElement) document.exitFullscreen()
  else (liveImgRef.value?.$el ?? liveImgRef.value)?.requestFullscreen?.()
}

async function fetchMapData() {
  try {
    const { data } = await api.get(`/classrooms/${route.params.id}/map-data`)
    mapData.value = data
  } catch {
    mapData.value = null
  }
}

onMounted(() => {
  cStore.fetchOne(Number(route.params.id))
  fetchMapData()
  // 실시간 탐지를 켜는 순간 RTSP 연결·모델 로딩을 기다리지 않도록 미리 준비시킨다
  api.get(`/analysis/${route.params.id}/prewarm`).catch(() => {})
})

async function fetchSeatOccupancy() {
  if (mockActive.value) {
    seatLoading.value = true
    seatResult.value = null
    await new Promise(r => setTimeout(r, 300))
    seatResult.value = buildMockAnalysisResult(false)
    seatLoading.value = false
    return
  }
  seatLoading.value = true
  seatResult.value = null
  try {
    const { data } = await api.get(`/analysis/${route.params.id}/seat-occupancy`)
    seatResult.value = data
  } catch (e) {
    alert('좌석 점유 분석 실패: ' + (e.response?.data?.detail ?? e.message))
  } finally {
    seatLoading.value = false
  }
}

async function fetchYoloLlm() {
  if (mockActive.value) {
    yoloLlmLoading.value = true
    yoloLlmResult.value = null
    await new Promise(r => setTimeout(r, 300))
    yoloLlmResult.value = buildMockAnalysisResult(true)
    yoloLlmLoading.value = false
    return
  }
  yoloLlmLoading.value = true
  yoloLlmResult.value = null
  try {
    const { data } = await api.get(`/analysis/${route.params.id}/yolo-llm-count`)
    yoloLlmResult.value = data
  } catch (e) {
    alert('YOLO+LLM 분석 실패: ' + (e.response?.data?.detail ?? e.message))
  } finally {
    yoloLlmLoading.value = false
  }
}

// ── 배치도 점유 오버레이 ──────────────────────────────────────────────────────

const mapCanvasRef = ref(null)
const yoloMapCanvasRef = ref(null)

function getMapData() {
  return mockActive.value ? MOCK_MAP_DATA : mapData.value
}

const hasMap = computed(() => !!getMapData()?.objects?.length)

// LLM 응답 "5 - 공부\n8 - 휴대폰" → Map { '5' → '공부', '8' → '휴대폰' }
function parseLlmActivities(cameras) {
  const map = new Map()
  for (const cam of cameras) {
    if (!cam.llm_response) continue
    for (const line of cam.llm_response.split('\n')) {
      const m = line.match(/^(\d+)\s*-\s*(.+)/)
      if (m) map.set(m[1].trim(), m[2].trim())
    }
  }
  return map
}

const CANVAS_FONT = "'Inter Variable', 'Pretendard Variable', Pretendard, sans-serif"

// 색은 그릴 때마다 디자인 토큰에서 읽는다(테마가 바뀌면 다시 그린다). 좌석 상태색은 ClassroomSeatMap과 같다.
async function drawMapOnCanvas(canvas, cameras, seatActivity = new Map()) {
  const mapData = getMapData()
  if (!canvas || !mapData?.objects?.length) return

  const { objects, mapW = 900, mapH = 600 } = mapData

  const allOccupied = new Set()
  const allEmpty = new Set()
  const allFailed = new Set()
  for (const cam of cameras) {
    for (const s of cam.occupied ?? []) allOccupied.add(s)
    // 캡처에 실패한 카메라는 서버가 좌석을 전부 empty로 돌려주므로 빈 좌석이 아니라 판정 불가로 그린다
    if (cam.error) for (const s of cam.empty ?? []) allFailed.add(s)
    else for (const s of cam.empty ?? []) allEmpty.add(s)
  }
  // LLM이 활동을 응답한 좌석은 점유로 확정
  for (const [sid] of seatActivity) allOccupied.add(sid)

  // 카드 폭에 맞춰 그린다(레티나에서도 또렷하게 화면 배율만큼 해상도를 올린다)
  const cssW = canvas.getBoundingClientRect().width || 480
  const scale = cssW / mapW
  const dpr = window.devicePixelRatio || 1
  canvas.width = Math.round(mapW * scale * dpr)
  canvas.height = Math.round(mapH * scale * dpr)

  const ctx = canvas.getContext('2d')
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
  ctx.clearRect(0, 0, mapW * scale, mapH * scale)

  const C = {
    fg: cssColor('fg'),
    muted: cssColor('fg-muted'),
    mapText: '#061735',
    mapMuted: '#53647f',
    mapBorder: '#a9b3c2',
    chair: '#e2e8f1',
    occ: cssColor('state-occupied'),
    occFill: cssColor('state-occupied', 0.18),
    unk: cssColor('state-unknown'),
    unkFill: cssColor('state-unknown', 0.16),
  }

  function withRotation(obj, draw) {
    if (!obj.angle) return draw(obj.x * scale, obj.y * scale, obj.w * scale, obj.h * scale)
    const cx = (obj.x + obj.w / 2) * scale
    const cy = (obj.y + obj.h / 2) * scale
    ctx.save()
    ctx.translate(cx, cy)
    ctx.rotate(obj.angle * Math.PI / 180)
    draw(-obj.w * scale / 2, -obj.h * scale / 2, obj.w * scale, obj.h * scale)
    ctx.restore()
  }

  for (const obj of objects) {
    if (obj.type === 'chair') {
      withRotation(obj, (x, y, w, h) => {
        ctx.fillStyle = C.chair
        ctx.beginPath(); ctx.roundRect(x, y, w, h, 8 * scale); ctx.fill()
      })
    } else if (obj.type === 'cctv') {
      const x = obj.x * scale, y = obj.y * scale
      const w = obj.w * scale, h = obj.h * scale
      ctx.fillStyle = '#ffffff'
      ctx.strokeStyle = C.mapBorder
      ctx.lineWidth = 3 * scale
      ctx.beginPath(); ctx.roundRect(x, y, w, h, 12 * scale); ctx.fill(); ctx.stroke()
      ctx.fillStyle = C.mapMuted
      const cctvLabel = obj.label || 'CCTV'
      ctx.font = `700 ${Math.max(10, Math.min(h * 0.24, 22, (w * 0.78) / (cctvLabel.length * 0.7)))}px ${CANVAS_FONT}`
      ctx.textAlign = 'center'; ctx.textBaseline = 'middle'
      ctx.fillText(cctvLabel, x + w / 2, y + h / 2)
    } else if (obj.type === 'desk') {
      const label = obj.label?.trim()
      const activity = label ? seatActivity.get(label) : undefined
      const isOcc = label && allOccupied.has(label)
      withRotation(obj, (x, y, w, h) => {
        ctx.fillStyle = isOcc ? C.occFill : '#ffffff'
        ctx.strokeStyle = isOcc ? C.occ : C.mapBorder
        ctx.lineWidth = 3 * scale
        ctx.beginPath(); ctx.roundRect(x, y, w, h, 10 * scale); ctx.fill(); ctx.stroke()
        if (label) {
          const hasActivity = !!activity
          const labelY = hasActivity ? y + h * 0.38 : y + h / 2
          ctx.font = `700 ${Math.max(11, Math.min(h * 0.42, 30))}px ${CANVAS_FONT}`
          ctx.fillStyle = C.mapText
          ctx.textAlign = 'center'; ctx.textBaseline = 'middle'
          ctx.fillText(label, x + w / 2, labelY)
          if (hasActivity) {
            ctx.font = `${Math.min(h * 0.22, 14)}px ${CANVAS_FONT}`
            ctx.fillStyle = C.muted
            ctx.fillText(activity, x + w / 2, y + h * 0.7)
          }
        }
      })
    }
  }
  ctx.textAlign = 'left'
}

async function drawOccupancyMap() {
  await nextTick()
  drawMapOnCanvas(mapCanvasRef.value, seatResult.value?.cameras ?? [])
}

async function drawYoloLlmMap() {
  await nextTick()
  const cameras = yoloLlmResult.value?.cameras ?? []
  const seatActivity = parseLlmActivities(cameras)
  drawMapOnCanvas(yoloMapCanvasRef.value, cameras, seatActivity)
}

watch(seatResult, () => { if (seatResult.value) drawOccupancyMap() })
watch(yoloLlmResult, () => { if (yoloLlmResult.value) drawYoloLlmMap() })

// 캔버스는 그릴 때의 색이 그대로 남으므로 테마가 바뀌면 다시 그린다
watch(() => theme.mode, () => {
  if (seatResult.value) drawOccupancyMap()
  if (yoloLlmResult.value) drawYoloLlmMap()
})
</script>
