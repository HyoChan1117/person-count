<template>
  <div class="h-full overflow-y-auto bg-slate-50 p-6">
    <div class="max-w-5xl mx-auto">

      <!-- Header -->
      <div class="flex items-start justify-between mb-6 gap-4">
        <div>
          <router-link to="/classrooms" class="text-xs text-slate-400 hover:text-slate-600">← 목록</router-link>
          <h1 class="text-xl font-bold text-slate-800 mt-1">{{ classroom?.name }} 대시보드</h1>
        </div>
        <div class="flex items-center gap-1.5">
          <button @click="fetchSeatOccupancy" :disabled="seatLoading" class="btn-seat">
            {{ seatLoading ? '분석 중...' : '🪑 YOLO' }}
          </button>
          <button
            v-if="classroom"
            @click="seatPromptOpen = true"
            title="좌석 점유 프롬프트 편집"
            class="btn-seat-config"
          >⚙️</button>

          <div class="w-px h-5 bg-slate-200 mx-0.5" />

          <button @click="fetchYoloLlm" :disabled="yoloLlmLoading" class="btn-yolo-llm">
            {{ yoloLlmLoading ? '분석 중...' : '🤖 YOLO+LLM' }}
          </button>
          <button
            v-if="classroom"
            @click="yoloLlmPromptOpen = true"
            title="YOLO+LLM 프롬프트 편집"
            class="btn-yolo-llm-config"
          >⚙️</button>
        </div>
      </div>

      <!-- 좌석 점유 결과 -->
      <div v-if="seatLoading" class="text-center py-20 text-slate-400 text-sm">
        <div class="text-3xl mb-2 animate-spin inline-block">⟳</div>
        <div>분석 중...</div>
      </div>

      <div v-else-if="seatResult">
        <!-- 요약 -->
        <div class="bg-white border border-violet-200 rounded-xl p-4 shadow-sm mb-3">
          <div class="flex items-center justify-between">
            <div>
              <div class="text-[10px] text-violet-400 uppercase tracking-wide mb-0.5">🪑 YOLO 분석</div>
              <div class="text-sm font-semibold text-slate-700">좌석 점유 현황</div>
            </div>
            <div class="text-right flex items-end gap-1.5">
              <span class="text-2xl font-bold text-violet-600">{{ seatResult.total_occupied }}</span>
              <span class="text-sm text-slate-400 pb-0.5">/ {{ seatResult.total_seats }}석</span>
            </div>
          </div>
          <div class="mt-3 w-full h-1.5 bg-slate-100 rounded-full overflow-hidden">
            <div
              class="h-full bg-violet-400 rounded-full transition-all duration-500"
              :style="{ width: seatResult.total_seats ? `${Math.round(seatResult.total_occupied / seatResult.total_seats * 100)}%` : '0%' }"
            />
          </div>
        </div>

        <!-- 배치도 오버레이 -->
        <div v-if="getMapData()?.objects?.length" class="bg-white border border-violet-200 rounded-xl p-4 shadow-sm mb-3">
          <div class="flex items-center gap-3 mb-3">
            <span class="text-xs font-semibold text-slate-700">교실 배치도</span>
            <div class="flex items-center gap-2 text-[10px]">
              <span class="w-3 h-3 rounded-sm bg-red-200 border border-red-400 inline-block" />
              <span class="text-slate-500 mr-2">점유</span>
              <span class="w-3 h-3 rounded-sm bg-orange-200 border border-orange-400 inline-block" />
              <span class="text-slate-500 mr-2">근접(미착석)</span>
              <span class="w-3 h-3 rounded-sm bg-green-200 border border-green-400 inline-block" />
              <span class="text-slate-500">미점유</span>
            </div>
          </div>
          <canvas ref="mapCanvasRef" class="rounded-lg w-full" />
        </div>

        <!-- 카메라별 카드 -->
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <div
            v-for="cam in seatResult.cameras"
            :key="cam.camera_id"
            class="rounded-xl overflow-hidden border border-violet-200 shadow-sm bg-white"
          >
            <div class="relative bg-slate-800 cursor-pointer hover:opacity-90 transition" style="aspect-ratio:16/9"
              @click="cam.image && openPreview(cam)"
            >
              <img v-if="cam.image" :src="`data:image/jpeg;base64,${cam.image}`" class="w-full h-full object-cover" />
              <div v-else-if="cam.error" class="flex items-center justify-center h-full text-red-400 text-xs p-3 text-center">{{ cam.error }}</div>
              <div v-else class="flex items-center justify-center h-full text-slate-500 text-xs">이미지 없음</div>
              <div v-if="cam.image" class="absolute bottom-1.5 right-1.5 text-[10px] text-white/60 bg-black/30 px-1.5 py-0.5 rounded">클릭 확대</div>
            </div>
            <div class="p-3">
              <div class="flex items-center justify-between mb-2">
                <span class="text-xs font-medium text-slate-600">{{ cam.name }}</span>
                <span class="text-xs text-violet-600 font-bold">{{ cam.occupied_count }}/{{ cam.total }}석</span>
              </div>
              <div class="flex flex-wrap gap-1 mb-2">
                <span
                  v-for="s in cam.occupied"
                  :key="'occ-'+s"
                  class="text-[10px] px-1.5 py-0.5 rounded font-medium bg-red-100 text-red-700"
                >{{ s }}</span>
                <span
                  v-for="s in cam.empty"
                  :key="'emp-'+s"
                  class="text-[10px] px-1.5 py-0.5 rounded bg-slate-100 text-slate-400"
                >{{ s }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- YOLO+LLM 결과 -->
      <div v-if="yoloLlmLoading" class="text-center py-20 text-slate-400 text-sm" :class="{ 'mt-6': seatResult }">
        <div class="text-3xl mb-2 animate-spin inline-block">⟳</div>
        <div>YOLO+LLM 분석 중...</div>
      </div>

      <div v-else-if="yoloLlmResult" :class="{ 'mt-6': seatResult }">
        <!-- 구분선 -->
        <div v-if="seatResult" class="flex items-center gap-3 mb-4">
          <div class="h-px flex-1 bg-slate-200" />
          <span class="text-xs text-slate-400">YOLO+LLM 분석</span>
          <div class="h-px flex-1 bg-slate-200" />
        </div>

        <!-- 요약 -->
        <div class="bg-white border border-blue-200 rounded-xl p-4 shadow-sm mb-3">
          <div class="flex items-center justify-between">
            <div>
              <div class="text-[10px] text-blue-400 uppercase tracking-wide mb-0.5">🤖 YOLO+LLM 분석</div>
              <div class="text-sm font-semibold text-slate-700">좌석 점유 현황</div>
            </div>
            <div class="text-right flex items-end gap-1.5">
              <span class="text-2xl font-bold text-blue-600">{{ yoloLlmResult.total_occupied }}</span>
              <span class="text-sm text-slate-400 pb-0.5">/ {{ yoloLlmResult.total_seats }}석</span>
            </div>
          </div>
          <div class="mt-3 w-full h-1.5 bg-slate-100 rounded-full overflow-hidden">
            <div
              class="h-full bg-blue-400 rounded-full transition-all duration-500"
              :style="{ width: yoloLlmResult.total_seats ? `${Math.round(yoloLlmResult.total_occupied / yoloLlmResult.total_seats * 100)}%` : '0%' }"
            />
          </div>
        </div>

        <!-- YOLO+LLM 배치도 오버레이 -->
        <div v-if="getMapData()?.objects?.length" class="bg-white border border-blue-200 rounded-xl p-4 shadow-sm mb-3">
          <div class="flex items-center gap-3 mb-3">
            <span class="text-xs font-semibold text-slate-700">교실 배치도</span>
            <div class="flex items-center gap-2 text-[10px]">
              <span class="w-3 h-3 rounded-sm bg-red-200 border border-red-400 inline-block" />
              <span class="text-slate-500 mr-2">점유</span>
              <span class="w-3 h-3 rounded-sm bg-orange-200 border border-orange-400 inline-block" />
              <span class="text-slate-500 mr-2">근접(미착석)</span>
              <span class="w-3 h-3 rounded-sm bg-green-200 border border-green-400 inline-block" />
              <span class="text-slate-500">미점유</span>
            </div>
          </div>
          <canvas ref="yoloMapCanvasRef" class="rounded-lg w-full" />
        </div>

        <!-- 카메라별 카드 -->
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <div
            v-for="cam in yoloLlmResult.cameras"
            :key="cam.camera_id"
            class="rounded-xl overflow-hidden border border-blue-200 shadow-sm bg-white"
          >
            <div class="relative bg-slate-800 cursor-pointer hover:opacity-90 transition" style="aspect-ratio:16/9"
              @click="cam.image && openYoloPreview(cam)"
            >
              <img v-if="cam.image" :src="`data:image/jpeg;base64,${cam.image}`" class="w-full h-full object-cover" />
              <div v-else-if="cam.error" class="flex items-center justify-center h-full text-red-400 text-xs p-3 text-center">{{ cam.error }}</div>
              <div v-else class="flex items-center justify-center h-full text-slate-500 text-xs">이미지 없음</div>
              <div v-if="cam.image" class="absolute bottom-1.5 right-1.5 text-[10px] text-white/60 bg-black/30 px-1.5 py-0.5 rounded">클릭 확대</div>
            </div>
            <div class="p-3">
              <div class="flex items-center justify-between mb-2">
                <span class="text-xs font-medium text-slate-600">{{ cam.name }}</span>
                <span class="text-xs text-blue-600 font-bold">
                  {{ cam.occupied_count }}/{{ cam.total }}석
                </span>
              </div>
              <div v-if="cam.total > 0" class="flex flex-wrap gap-1 mb-2">
                <span
                  v-for="s in cam.occupied"
                  :key="'occ-'+s"
                  class="text-[10px] px-1.5 py-0.5 rounded font-medium bg-red-100 text-red-700"
                >{{ s }}</span>
                <span
                  v-for="s in cam.near"
                  :key="'near-'+s"
                  class="text-[10px] px-1.5 py-0.5 rounded font-medium bg-orange-100 text-orange-700"
                >{{ s }}</span>
                <span
                  v-for="s in cam.empty"
                  :key="'emp-'+s"
                  class="text-[10px] px-1.5 py-0.5 rounded bg-slate-100 text-slate-400"
                >{{ s }}</span>
              </div>
              <p v-if="cam.llm_response" class="text-xs text-slate-600 whitespace-pre-wrap leading-relaxed">{{ filterLlmResponse(cam.llm_response) }}</p>
              <p v-else-if="cam.error" class="text-xs text-red-400">{{ cam.error }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- 빈 상태 -->
      <div v-if="!seatResult && !yoloLlmResult && !seatLoading && !yoloLlmLoading" class="text-center py-20 text-slate-400 text-sm">
        버튼을 눌러 분석하세요
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

    <!-- 좌석 점유 확대 모달 -->
    <Teleport to="body">
      <div
        v-if="preview.open"
        class="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4"
        @click.self="closePreview"
      >
        <div class="bg-slate-900 rounded-2xl shadow-2xl max-w-4xl w-full overflow-hidden">
          <div class="flex items-center justify-between px-5 py-3 bg-slate-800">
            <div>
              <span class="text-white font-semibold text-sm">{{ preview.cameraName }}</span>
              <span class="text-slate-400 text-xs ml-2">— {{ preview.subtitle }}</span>
            </div>
            <div class="flex items-center gap-3">
              <span v-if="preview.badge" class="text-sm font-bold" :class="preview.badgeClass">{{ preview.badge }}</span>
              <button @click="closePreview" class="text-slate-400 hover:text-white text-lg leading-none">✕</button>
            </div>
          </div>
          <div class="relative flex items-center justify-center min-h-48 bg-slate-900 p-2">
            <img
              v-if="preview.image"
              :src="`data:image/jpeg;base64,${preview.image}`"
              class="max-w-full max-h-[60vh] rounded object-contain"
            />
            <div v-else class="text-red-400 text-sm py-16">이미지 없음</div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, reactive, watch, nextTick, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useClassroomStore } from '@/stores/classroomStore.js'
import SeatPromptModal from '@/components/modals/SeatPromptModal.vue'
import ClassroomPromptModal from '@/components/modals/ClassroomPromptModal.vue'
import axios from 'axios'

const api = axios.create({ baseURL: '/api' })
const route = useRoute()
const cStore = useClassroomStore()

const classroom = computed(() => cStore.current)
const seatPromptOpen = ref(false)
const yoloLlmPromptOpen = ref(false)

const seatLoading = ref(false)
const seatResult = ref(null)

const yoloLlmLoading = ref(false)
const yoloLlmResult = ref(null)

onMounted(() => cStore.fetchOne(Number(route.params.id)))

async function fetchSeatOccupancy() {
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

// ── 확대 모달 ─────────────────────────────────────────────────────────────────

const preview = reactive({
  open: false,
  cameraName: '',
  subtitle: '',
  image: null,
  badge: null,
  badgeClass: '',
})

function openPreview(cam) {
  preview.open = true
  preview.cameraName = cam.name
  preview.subtitle = '좌석 점유 분석'
  preview.image = cam.image ?? null
  preview.badge = cam.occupied_count != null ? `${cam.occupied_count}석 점유` : null
  preview.badgeClass = 'text-violet-400'
}

function openYoloPreview(cam) {
  preview.open = true
  preview.cameraName = cam.name
  preview.subtitle = 'YOLO+LLM 분석'
  preview.image = cam.image ?? null
  preview.badge = cam.yolo_count != null ? `YOLO ${cam.yolo_count}명` : null
  preview.badgeClass = 'text-blue-400'
}

function closePreview() {
  preview.open = false
}

// ── 배치도 점유 오버레이 ──────────────────────────────────────────────────────

const mapCanvasRef = ref(null)
const yoloMapCanvasRef = ref(null)

function getMapData() {
  try {
    const raw = localStorage.getItem(`map_${route.params.id}`)
    return raw ? JSON.parse(raw) : null
  } catch { return null }
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
  const allNear = new Set()
  const allEmpty = new Set()
  for (const cam of cameras) {
    for (const s of cam.occupied ?? []) allOccupied.add(s)
    for (const s of cam.near ?? []) allNear.add(s)
    for (const s of cam.empty ?? []) allEmpty.add(s)
  }
  // LLM이 활동을 응답한 좌석은 점유로 확정
  for (const [sid] of seatActivity) allOccupied.add(sid)
  for (const s of allOccupied) allNear.delete(s)

  const maxW = Math.min(canvas.parentElement?.clientWidth ?? 500, 480)
  const scale = Math.min(maxW / mapW, 1)
  canvas.width = Math.round(mapW * scale)
  canvas.height = Math.round(mapH * scale)

  const ctx = canvas.getContext('2d')
  ctx.clearRect(0, 0, canvas.width, canvas.height)

  ctx.strokeStyle = '#e2e8f0'
  ctx.lineWidth = 0.5
  for (let x = 0; x <= mapW; x += 40) {
    ctx.beginPath(); ctx.moveTo(x * scale, 0); ctx.lineTo(x * scale, mapH * scale); ctx.stroke()
  }
  for (let y = 0; y <= mapH; y += 40) {
    ctx.beginPath(); ctx.moveTo(0, y * scale); ctx.lineTo(mapW * scale, y * scale); ctx.stroke()
  }

  for (const obj of objects) {
    const x = obj.x * scale, y = obj.y * scale
    const w = obj.w * scale, h = obj.h * scale

    if (obj.type === 'chair') {
      ctx.fillStyle = '#e2e8f0'
      ctx.beginPath(); ctx.roundRect(x, y, w, h, 3); ctx.fill()
    } else if (obj.type === 'cctv') {
      ctx.fillStyle = '#475569'
      ctx.beginPath(); ctx.roundRect(x, y, w, h, 4); ctx.fill()
      ctx.fillStyle = '#fff'
      ctx.font = `bold ${Math.min(h * 0.28, 11)}px sans-serif`
      ctx.textAlign = 'center'; ctx.textBaseline = 'middle'
      ctx.fillText(obj.label || 'CAM', x + w / 2, y + h / 2)
    } else if (obj.type === 'desk') {
      const label = obj.label?.trim()
      const activity = label ? seatActivity.get(label) : undefined
      const isOcc  = label && allOccupied.has(label)
      const isNear = label && !isOcc && allNear.has(label)
      const isEmpty = label && !isOcc && !isNear && allEmpty.has(label)
      ctx.fillStyle = isOcc ? '#fee2e2' : isNear ? '#ffedd5' : isEmpty ? '#dcfce7' : '#f5e9cc'
      ctx.strokeStyle = isOcc ? '#ef4444' : isNear ? '#f97316' : isEmpty ? '#22c55e' : '#c9a55a'
      ctx.lineWidth = isOcc || isNear || isEmpty ? 2.5 : 1.5
      ctx.beginPath(); ctx.roundRect(x, y, w, h, 5); ctx.fill(); ctx.stroke()
      if (label) {
        const hasActivity = !!activity
        const labelY = hasActivity ? y + h * 0.38 : y + h / 2
        ctx.font = `bold ${Math.min(h * 0.36, 15)}px sans-serif`
        ctx.fillStyle = isOcc ? '#dc2626' : isNear ? '#ea580c' : isEmpty ? '#16a34a' : '#5a3e1b'
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

function filterLlmResponse(text) {
  return text.split('\n')
    .map(l => l.replace(/\*\*/g, '').trim())
    .filter(l => !l.startsWith('자세:'))
    .join('\n').trim()
}

watch(seatResult, () => { if (seatResult.value) drawOccupancyMap() })
watch(yoloLlmResult, () => { if (yoloLlmResult.value) drawYoloLlmMap() })
</script>

<style scoped>
.btn-seat {
  @apply bg-violet-600 text-white text-xs px-3 py-1.5 rounded-lg hover:bg-violet-700 transition disabled:opacity-50;
}
.btn-seat-config {
  @apply bg-violet-100 text-violet-700 text-xs px-2 py-1.5 rounded-lg hover:bg-violet-200 transition;
}
.btn-yolo-llm {
  @apply bg-blue-600 text-white text-xs px-3 py-1.5 rounded-lg hover:bg-blue-700 transition disabled:opacity-50;
}
.btn-yolo-llm-config {
  @apply bg-blue-100 text-blue-700 text-xs px-2 py-1.5 rounded-lg hover:bg-blue-200 transition;
}
</style>
