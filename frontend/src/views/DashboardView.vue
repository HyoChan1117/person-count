<template>
  <div class="h-full overflow-y-auto bg-neutral-50 dark:bg-neutral-950 p-6 lg:p-8">
    <div class="max-w-5xl mx-auto">

      <!-- Header -->
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
        <div>
          <router-link to="/classrooms" class="inline-flex items-center gap-1 text-xs text-neutral-400 dark:text-neutral-600 hover:text-neutral-600 dark:hover:text-neutral-300 transition mb-2">
            ← 좌석 확인
          </router-link>
          <div class="flex items-center gap-2">
            <h1 class="text-2xl font-bold text-neutral-900 dark:text-neutral-50 tracking-tight">{{ classroom?.name }}</h1>
            <span v-if="mockActive" class="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-amber-100 dark:bg-amber-500/15 text-amber-700 dark:text-amber-400 border border-amber-200 dark:border-amber-500/30">목데이터</span>
          </div>
          <p class="text-sm text-neutral-500 dark:text-neutral-400 mt-0.5">실시간 인원 현황</p>
        </div>

        <div class="flex items-center gap-2">
          <button
            @click="toggleMock"
            class="text-xs px-3 py-1.5 rounded-lg transition font-medium border shrink-0"
            :class="mockActive
              ? 'bg-amber-500 text-white border-amber-500 hover:bg-amber-600'
              : 'bg-white dark:bg-neutral-900 border-neutral-200 dark:border-neutral-800 text-neutral-600 dark:text-neutral-300 hover:border-neutral-300 dark:hover:border-neutral-700'"
          >{{ mockActive ? '🧪 목데이터 끄기' : '🧪 목데이터로 보기' }}</button>

          <div class="flex items-center gap-1 bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-xl p-1.5 shadow-sm w-fit">
            <button @click="fetchSeatOccupancy" :disabled="seatLoading" class="btn-primary">
              🪑 {{ seatLoading ? '분석 중...' : 'YOLO 분석' }}
            </button>
            <button
              v-if="classroom"
              @click="seatPromptOpen = true"
              title="좌석 점유 프롬프트 편집"
              class="btn-icon-ghost"
            >⚙️</button>

            <div class="w-px h-6 bg-neutral-200 mx-1" />

            <button @click="fetchYoloLlm" :disabled="yoloLlmLoading" class="btn-secondary">
              🤖 {{ yoloLlmLoading ? '분석 중...' : 'YOLO+LLM' }}
            </button>
            <button
              v-if="classroom"
              @click="yoloLlmPromptOpen = true"
              title="YOLO+LLM 프롬프트 편집"
              class="btn-icon-ghost"
            >⚙️</button>

            <div class="w-px h-6 bg-neutral-200 mx-1" />

            <button @click="toggleLive" class="inline-flex items-center gap-1.5 text-xs font-medium px-3.5 py-2 rounded-lg transition"
              :class="liveOn ? 'bg-red-600 text-white hover:bg-red-700' : 'bg-neutral-800 text-white hover:bg-neutral-900'">
              <span class="w-1.5 h-1.5 rounded-full" :class="liveOn ? 'bg-white animate-pulse' : 'bg-neutral-400'" />
              {{ liveOn ? '실시간 종료' : '실시간 탐지' }}
            </button>
          </div>
        </div>
      </div>

      <!-- 실시간 YOLO 탐지 -->
      <div v-if="liveOn" class="mb-8">
        <div v-if="!liveCameras.length" class="text-center py-12 text-neutral-400 dark:text-neutral-600 text-sm bg-white dark:bg-neutral-900 rounded-2xl border border-neutral-200 dark:border-neutral-800">
          RTSP가 설정된 카메라가 없습니다.
        </div>
        <div v-else class="rounded-2xl border border-neutral-200 dark:border-neutral-800 shadow-sm bg-white dark:bg-neutral-900 overflow-hidden">
          <div class="px-4 py-2.5 flex items-center justify-between gap-2 border-b border-neutral-100 dark:border-neutral-800 bg-neutral-50/60 dark:bg-neutral-900/60">
            <div class="flex items-center gap-2">
              <span class="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse shrink-0" />
              <select v-model="liveCameraId" class="text-sm font-medium text-neutral-600 dark:text-neutral-400 bg-transparent outline-none">
                <option v-for="cam in liveCameras" :key="cam.camera_id" :value="cam.camera_id">{{ cam.name }}</option>
              </select>
            </div>
            <button @click="toggleFullscreen" title="전체화면" class="text-xs text-neutral-400 dark:text-neutral-600 hover:text-neutral-700 dark:hover:text-neutral-200 transition px-2 py-1 rounded-lg hover:bg-neutral-100 dark:hover:bg-neutral-700">
              ⛶ 전체화면
            </button>
          </div>
          <!-- 실시간 영상에는 얼굴이 나오므로 기본 블러. 스트림은 보는 동안 계속 봐야 해서 자동 재블러 없이 화면을 나가거나 카메라를 바꾸면 다시 블러 -->
          <BlurredImage ref="liveImgRef" :key="liveKey" :src="liveSrc" alt="실시간 카메라 영상" :rounded="false" :auto-reblur-ms="0" class="w-full aspect-video" />
        </div>
        <p class="text-[11px] text-neutral-400 dark:text-neutral-600 mt-2">부하를 줄이기 위해 한 번에 카메라 1대만 실시간으로 표시합니다.</p>
      </div>

      <!-- 좌석 점유 결과 -->
      <div v-if="seatLoading" class="flex flex-col items-center justify-center py-24 text-neutral-400 dark:text-neutral-600 text-sm gap-3">
        <div class="w-9 h-9 rounded-full border-2 border-neutral-200 dark:border-neutral-800 border-t-violet-500 animate-spin" />
        <div>분석 중...</div>
      </div>

      <div v-else-if="seatResult">
        <!-- 요약 -->
        <div class="bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-2xl p-5 shadow-sm mb-4">
          <div class="flex items-center justify-between gap-4">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-xl bg-violet-50 flex items-center justify-center text-lg shrink-0">🪑</div>
              <div>
                <div class="text-[11px] font-medium text-violet-500 uppercase tracking-wide">YOLO 분석</div>
                <div class="text-sm font-semibold text-neutral-800 dark:text-neutral-100">좌석 점유 현황</div>
              </div>
            </div>
            <div class="text-right shrink-0 flex items-end gap-1.5">
              <span class="text-3xl font-bold text-violet-600 leading-none">{{ seatSummary.occupied }}</span>
              <span class="text-sm text-neutral-400 dark:text-neutral-600 pb-0.5">/ {{ seatSummary.judgeable }}석</span>
              <span v-if="seatSummary.unknown" class="text-sm text-amber-600 pb-0.5">· 판정 불가 {{ seatSummary.unknown }}석</span>
            </div>
          </div>
          <div class="mt-4 w-full h-2 bg-neutral-100 dark:bg-neutral-800 rounded-full overflow-hidden">
            <div
              class="h-full bg-violet-500 rounded-full transition-all duration-500"
              :style="{ width: seatSummary.judgeable ? `${Math.round(seatSummary.occupied / seatSummary.judgeable * 100)}%` : '0%' }"
            />
          </div>
        </div>

        <!-- 배치도 + 카메라별 카드 -->
        <div class="flex flex-col lg:flex-row gap-4 mb-4 items-start">
          <!-- 배치도 오버레이 (절반 크기) -->
          <div v-if="getMapData()?.objects?.length" class="bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-2xl p-5 shadow-sm w-full lg:w-1/2 shrink-0">
            <div class="flex items-center justify-between mb-4">
              <span class="text-sm font-semibold text-neutral-800 dark:text-neutral-100">교실 배치도</span>
              <div class="flex items-center gap-3 text-[11px] text-neutral-500 dark:text-neutral-400">
                <span class="flex items-center gap-1.5"><span class="w-2.5 h-2.5 rounded-full bg-red-400" />점유</span>
                <span class="flex items-center gap-1.5"><span class="w-2.5 h-2.5 rounded-full bg-neutral-300" />미점유</span>
              </div>
            </div>
            <canvas ref="mapCanvasRef" class="rounded-xl w-full" />
          </div>

          <!-- 카메라별 카드 -->
          <div
            class="grid gap-3 flex-1 w-full"
            :class="getMapData()?.objects?.length ? 'grid-cols-1 sm:grid-cols-2' : 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3'"
          >
            <div
              v-for="cam in seatResult.cameras"
              :key="cam.camera_id"
              class="rounded-2xl border border-neutral-200 dark:border-neutral-800 shadow-sm bg-white dark:bg-neutral-900 p-4 hover:border-violet-200 transition-colors"
            >
              <div class="flex items-center justify-between mb-3">
                <span class="text-xs font-medium text-neutral-600 dark:text-neutral-400">{{ cam.name }}</span>
                <span v-if="cam.error" class="text-xs font-bold px-2 py-0.5 rounded-full bg-amber-50 text-amber-700">판정 불가</span>
                <span v-else class="text-xs font-bold px-2 py-0.5 rounded-full bg-violet-50 text-violet-600">{{ cam.occupied_count }}/{{ cam.total }}석</span>
              </div>
              <p v-if="cam.error" class="text-xs text-amber-700">캡처 실패로 {{ cam.total }}석을 판정하지 못했습니다. ({{ cam.error }})</p>
              <div v-else class="flex flex-wrap gap-1.5">
                <span
                  v-for="s in cam.occupied"
                  :key="'occ-'+s"
                  class="text-[10px] px-1.5 py-0.5 rounded-md font-medium bg-red-50 text-red-600 border border-red-100"
                >{{ s }}</span>
                <span
                  v-for="s in cam.empty"
                  :key="'emp-'+s"
                  class="text-[10px] px-1.5 py-0.5 rounded-md bg-neutral-50 dark:bg-neutral-950 text-neutral-400 dark:text-neutral-600 border border-neutral-100 dark:border-neutral-800"
                >{{ s }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- YOLO+LLM 결과 -->
      <div v-if="yoloLlmLoading" class="flex flex-col items-center justify-center py-24 text-neutral-400 dark:text-neutral-600 text-sm gap-3" :class="{ 'mt-6': seatResult }">
        <div class="w-9 h-9 rounded-full border-2 border-neutral-200 dark:border-neutral-800 border-t-blue-500 animate-spin" />
        <div>YOLO+LLM 분석 중...</div>
      </div>

      <div v-else-if="yoloLlmResult" :class="{ 'mt-8': seatResult }">
        <!-- 구분선 -->
        <div v-if="seatResult" class="flex items-center gap-3 mb-6">
          <div class="h-px flex-1 bg-neutral-200" />
          <span class="text-[11px] font-medium text-neutral-400 dark:text-neutral-600 uppercase tracking-wide px-2">YOLO+LLM 분석</span>
          <div class="h-px flex-1 bg-neutral-200" />
        </div>

        <!-- 요약 -->
        <div class="bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-2xl p-5 shadow-sm mb-4">
          <div class="flex items-center justify-between gap-4">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center text-lg shrink-0">🤖</div>
              <div>
                <div class="text-[11px] font-medium text-blue-500 uppercase tracking-wide">YOLO+LLM 분석</div>
                <div class="text-sm font-semibold text-neutral-800 dark:text-neutral-100">좌석 점유 현황</div>
              </div>
            </div>
            <div class="text-right shrink-0 flex items-end gap-1.5">
              <span class="text-3xl font-bold text-blue-600 leading-none">{{ yoloLlmResult.total_occupied }}</span>
              <span class="text-sm text-neutral-400 dark:text-neutral-600 pb-0.5">/ {{ yoloLlmResult.total_seats }}석</span>
            </div>
          </div>
          <div class="mt-4 w-full h-2 bg-neutral-100 dark:bg-neutral-800 rounded-full overflow-hidden">
            <div
              class="h-full bg-blue-500 rounded-full transition-all duration-500"
              :style="{ width: yoloLlmResult.total_seats ? `${Math.round(yoloLlmResult.total_occupied / yoloLlmResult.total_seats * 100)}%` : '0%' }"
            />
          </div>
        </div>

        <!-- YOLO+LLM 배치도 + 카메라별 카드 -->
        <div class="flex flex-col lg:flex-row gap-4 mb-4 items-start">
          <!-- 배치도 오버레이 (절반 크기) -->
          <div v-if="getMapData()?.objects?.length" class="bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-2xl p-5 shadow-sm w-full lg:w-1/2 shrink-0">
            <div class="flex items-center justify-between mb-4">
              <span class="text-sm font-semibold text-neutral-800 dark:text-neutral-100">교실 배치도</span>
              <div class="flex items-center gap-3 text-[11px] text-neutral-500 dark:text-neutral-400">
                <span class="flex items-center gap-1.5"><span class="w-2.5 h-2.5 rounded-full bg-red-400" />점유</span>
                <span class="flex items-center gap-1.5"><span class="w-2.5 h-2.5 rounded-full bg-neutral-300" />미점유</span>
              </div>
            </div>
            <canvas ref="yoloMapCanvasRef" class="rounded-xl w-full" />
          </div>

          <!-- 카메라별 카드 -->
          <div
            class="grid gap-3 flex-1 w-full"
            :class="getMapData()?.objects?.length ? 'grid-cols-1 sm:grid-cols-2' : 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3'"
          >
            <div
              v-for="cam in yoloLlmResult.cameras"
              :key="cam.camera_id"
              class="rounded-2xl border border-neutral-200 dark:border-neutral-800 shadow-sm bg-white dark:bg-neutral-900 p-4 hover:border-blue-200 transition-colors"
            >
              <div class="flex items-center justify-between mb-3">
                <span class="text-xs font-medium text-neutral-600 dark:text-neutral-400">{{ cam.name }}</span>
                <span class="text-xs font-bold px-2 py-0.5 rounded-full bg-blue-50 text-blue-600">
                  {{ cam.occupied_count }}/{{ cam.total }}석
                </span>
              </div>
              <div v-if="cam.total > 0 && !cam.error" class="flex flex-wrap gap-1.5">
                <span
                  v-for="s in cam.occupied"
                  :key="'occ-'+s"
                  class="text-[10px] px-1.5 py-0.5 rounded-md font-medium bg-red-50 text-red-600 border border-red-100"
                >{{ s }}</span>
                <span
                  v-for="s in cam.empty"
                  :key="'emp-'+s"
                  class="text-[10px] px-1.5 py-0.5 rounded-md bg-neutral-50 dark:bg-neutral-950 text-neutral-400 dark:text-neutral-600 border border-neutral-100 dark:border-neutral-800"
                >{{ s }}</span>
              </div>
              <p v-if="cam.error" class="text-xs text-red-400">{{ cam.error }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- 빈 상태 -->
      <div v-if="!seatResult && !yoloLlmResult && !seatLoading && !yoloLlmLoading" class="flex flex-col items-center justify-center py-28 text-neutral-400 dark:text-neutral-600 gap-3">
        <div class="w-14 h-14 rounded-2xl bg-neutral-100 dark:bg-neutral-800 flex items-center justify-center text-2xl">📊</div>
        <div class="text-sm">버튼을 눌러 분석하세요</div>
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
import SeatPromptModal from '@/components/modals/SeatPromptModal.vue'
import ClassroomPromptModal from '@/components/modals/ClassroomPromptModal.vue'
import BlurredImage from '@/components/ui/BlurredImage.vue'
import api from '@/api'
import { generateMockImageDataUrl } from '@/utils/mockImage'
import { useMockToggle } from '@/composables/useMockToggle'

const route = useRoute()
const cStore = useClassroomStore()

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

function toggleLive() {
  liveOn.value = !liveOn.value
  if (liveOn.value) {
    if (!liveCameraId.value || !liveCameras.value.some(c => c.camera_id === liveCameraId.value)) {
      liveCameraId.value = liveCameras.value[0]?.camera_id ?? null
    }
    liveKey.value++
    if (mockActive.value) mockLiveImg.value = generateMockImageDataUrl('MOCK LIVE FEED', 960, 540, '#18181b')
  }
}

// 카메라를 바꿀 때도 이전 스트림이 남지 않도록 <img>를 완전히 새로 만든다
watch(liveCameraId, () => {
  if (!liveOn.value) return
  liveKey.value++
  if (mockActive.value) mockLiveImg.value = generateMockImageDataUrl('MOCK LIVE FEED', 960, 540, '#18181b')
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

async function drawMapOnCanvas(canvas, cameras, seatActivity = new Map()) {
  const mapData = getMapData()
  if (!canvas || !mapData?.objects?.length) return

  const { objects, mapW = 900, mapH = 600 } = mapData

  const allOccupied = new Set()
  const allEmpty = new Set()
  for (const cam of cameras) {
    for (const s of cam.occupied ?? []) allOccupied.add(s)
    // 캡처에 실패한 카메라는 서버가 좌석을 전부 empty로 돌려주므로 빈 좌석으로 그리지 않는다(판정 불가)
    if (!cam.error) for (const s of cam.empty ?? []) allEmpty.add(s)
  }
  // LLM이 활동을 응답한 좌석은 점유로 확정
  for (const [sid] of seatActivity) allOccupied.add(sid)

  const maxW = Math.min(canvas.parentElement?.clientWidth ?? 500, 480)
  const scale = Math.min(maxW / mapW, 1)
  canvas.width = Math.round(mapW * scale)
  canvas.height = Math.round(mapH * scale)

  const ctx = canvas.getContext('2d')
  ctx.clearRect(0, 0, canvas.width, canvas.height)

  for (const obj of objects) {
    const x = obj.x * scale, y = obj.y * scale
    const w = obj.w * scale, h = obj.h * scale

    if (obj.type === 'chair') {
      ctx.fillStyle = '#e2e8f0'
      ctx.beginPath(); ctx.roundRect(x, y, w, h, 3); ctx.fill()
    } else if (obj.type === 'cctv') {
      ctx.fillStyle = '#e2e8f0'
      ctx.strokeStyle = '#94a3b8'
      ctx.lineWidth = 1.5
      ctx.beginPath(); ctx.roundRect(x, y, w, h, 4); ctx.fill(); ctx.stroke()
      ctx.fillStyle = '#334155'
      ctx.font = `bold ${Math.min(h * 0.28, 11)}px sans-serif`
      ctx.textAlign = 'center'; ctx.textBaseline = 'middle'
      ctx.fillText(obj.label || 'CAM', x + w / 2, y + h / 2)
    } else if (obj.type === 'desk') {
      const label = obj.label?.trim()
      const activity = label ? seatActivity.get(label) : undefined
      const isOcc  = label && allOccupied.has(label)
      const isEmpty = label && !isOcc && allEmpty.has(label)
      ctx.fillStyle = isOcc ? '#fee2e2' : isEmpty ? '#f1f5f9' : '#f8fafc'
      ctx.strokeStyle = isOcc ? '#ef4444' : isEmpty ? '#94a3b8' : '#cbd5e1'
      ctx.lineWidth = isOcc || isEmpty ? 2.5 : 1.5
      ctx.beginPath(); ctx.rect(x, y, w, h); ctx.fill(); ctx.stroke()
      if (label) {
        const hasActivity = !!activity
        const labelY = hasActivity ? y + h * 0.38 : y + h / 2
        ctx.font = `bold ${Math.min(h * 0.36, 15)}px sans-serif`
        ctx.fillStyle = isOcc ? '#dc2626' : isEmpty ? '#64748b' : '#1e293b'
        ctx.textAlign = 'center'; ctx.textBaseline = 'middle'
        ctx.fillText(label, x + w / 2, labelY)
        if (hasActivity) {
          ctx.font = `${Math.min(h * 0.26, 11)}px sans-serif`
          ctx.fillStyle = '#dc2626'
          ctx.fillText(activity, x + w / 2, y + h * 0.68)
        }
      }
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
</script>

<style scoped>
.btn-primary {
  @apply inline-flex items-center gap-1.5 bg-violet-600 text-white text-xs font-medium px-3.5 py-2 rounded-lg hover:bg-violet-700 transition disabled:opacity-50 disabled:cursor-not-allowed;
}
.btn-secondary {
  @apply inline-flex items-center gap-1.5 bg-blue-600 text-white text-xs font-medium px-3.5 py-2 rounded-lg hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed;
}
.btn-icon-ghost {
  @apply w-8 h-8 flex items-center justify-center text-xs rounded-lg text-neutral-500 dark:text-neutral-400 hover:bg-neutral-100 dark:hover:bg-neutral-700 transition;
}
</style>
