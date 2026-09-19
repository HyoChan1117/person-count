<template>
  <div class="ds-root h-full overflow-y-auto bg-canvas p-section">
    <div class="mx-auto max-w-[1680px]">

      <!-- 헤더 -->
      <div class="mb-section flex flex-col gap-gutter sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 class="text-3xl font-bold tracking-tight text-fg">홈</h1>
          <p class="mt-1 text-lg text-fg-muted">지정한 교실의 YOLO 분석과 모니터링을 한 번에 확인하세요</p>
        </div>

        <div class="flex items-center gap-2">
          <label class="text-xs text-neutral-400 dark:text-neutral-600 shrink-0">표시할 교실</label>
          <select
            v-model="selectedId"
            class="min-w-[9rem] rounded-lg border border-line bg-card px-3 py-2 text-sm text-fg focus:outline-none focus-visible:border-fg-muted"
          >
            <option v-if="!cStore.classrooms.length" :value="null">등록된 교실 없음</option>
            <option v-for="c in cStore.classrooms" :key="c.id" :value="c.id">{{ c.name }}</option>
          </select>
        </div>
      </div>

      <!-- 교실 미지정 -->
      <div v-if="!selectedId" class="flex flex-col items-center justify-center py-28 text-neutral-400 dark:text-neutral-600 gap-3">
        <div class="w-14 h-14 rounded-2xl bg-neutral-100 dark:bg-neutral-800 flex items-center justify-center text-2xl">🏫</div>
        <p class="text-sm">표시할 교실이 없습니다. <router-link to="/classrooms" class="font-medium text-fg underline underline-offset-2">교실을 추가</router-link>해보세요.</p>
      </div>

      <template v-else>
        <!-- YOLO 결과 -->
        <div class="bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-2xl shadow-sm p-6 lg:p-8 mb-6">
          <div class="flex items-center justify-between gap-3 mb-6 flex-wrap">
            <div class="flex items-center gap-3 min-w-0">
              <div class="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-line text-xl">🪑</div>
              <div class="min-w-0">
                <div class="text-xs font-medium uppercase tracking-wide text-fg-muted">YOLO 분석</div>
                <div class="text-base font-semibold text-neutral-800 dark:text-neutral-100 truncate">{{ classroom?.name }} 좌석 점유</div>
              </div>
            </div>
            <button @click="refreshAll" :disabled="seatLoading" class="btn-primary shrink-0">
              {{ seatLoading ? '분석 중...' : '🔄 다시 분석' }}
            </button>
          </div>

          <div v-if="seatLoading && !seatResult" class="flex flex-col items-center justify-center py-20 text-neutral-400 dark:text-neutral-600 text-sm gap-3">
            <div class="h-9 w-9 animate-spin rounded-full border-2 border-line border-t-fg-muted" />
            분석 중...
          </div>

          <div v-else-if="seatResult">
            <div class="flex items-end gap-2 mb-4">
              <span class="text-4xl font-bold leading-none text-state-occupied">{{ seatResult.total_occupied }}</span>
              <span class="text-base text-neutral-400 dark:text-neutral-600 pb-1">/ {{ seatResult.total_seats }}석</span>
            </div>
            <div class="w-full h-2.5 bg-neutral-100 dark:bg-neutral-800 rounded-full overflow-hidden mb-6">
              <div
                class="h-full rounded-full bg-state-occupied transition-all duration-500"
                :style="{ width: seatResult.total_seats ? `${Math.round(seatResult.total_occupied / seatResult.total_seats * 100)}%` : '0%' }"
              />
            </div>

            <div class="flex flex-col lg:flex-row gap-6 items-start">
              <!-- 배치도 -->
              <div v-if="mapData?.objects?.length" class="w-full lg:w-1/2 shrink-0">
                <div class="flex items-center justify-between mb-1">
                  <span class="text-sm font-semibold text-neutral-800 dark:text-neutral-100">교실 배치도</span>
                  <div class="flex items-center gap-3 text-xs text-neutral-500 dark:text-neutral-400 flex-wrap justify-end">
                    <span class="flex items-center gap-1.5"><span class="w-2.5 h-2.5 rounded-full bg-red-400" />점유</span>
                    <span class="flex items-center gap-1.5"><span class="w-2.5 h-2.5 rounded-full bg-neutral-300" />미점유</span>
                    <template v-if="seatFaces">
                      <span class="flex items-center gap-1.5"><span class="w-2.5 h-2.5 rounded-full bg-white border border-neutral-400" />인증</span>
                      <span class="flex items-center gap-1.5"><span class="w-2.5 h-2.5 rounded-full bg-neutral-900" />미인증</span>
                    </template>
                  </div>
                </div>
                <p class="mb-2 text-[11px]" :class="patrolState?.running ? 'text-state-occupied' : 'text-neutral-400 dark:text-neutral-600'">
                  <template v-if="patrolState?.running">
                    얼굴 인식 순찰 중... {{ patrolState.zone_index }}/{{ patrolState.total_zones }} 구역 ({{ patrolState.zone }})
                  </template>
                  <template v-else>좌석을 누르면 담당 카메라의 실시간 화면을 볼 수 있어요</template>
                </p>
                <canvas ref="mapCanvasRef" class="rounded-xl w-full border border-neutral-100 dark:border-neutral-800 cursor-pointer" @click="onMapClick" />
              </div>

              <!-- 카메라별 카드 + 실시간 화면 -->
              <div class="flex-1 w-full flex flex-col gap-3">
                <div class="grid gap-3" :class="mapData?.objects?.length ? 'grid-cols-1 sm:grid-cols-2' : 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3'">
                  <div v-for="cam in seatResult.cameras" :key="cam.camera_id" class="rounded-xl border border-neutral-200 dark:border-neutral-800 p-4">
                    <div class="flex items-center justify-between mb-2.5">
                      <span class="text-sm font-medium text-neutral-600 dark:text-neutral-400">{{ cam.name }}</span>
                      <span class="rounded-full border border-line bg-canvas px-2 py-0.5 text-xs font-bold text-fg">{{ cam.occupied_count }}/{{ cam.total }}석</span>
                    </div>
                    <div class="flex flex-wrap gap-1.5">
                      <span v-for="s in cam.occupied" :key="'occ-'+s" class="text-xs px-2 py-0.5 rounded-md font-medium bg-red-50 text-red-600 border border-red-100">{{ s }}</span>
                      <span v-for="s in cam.empty" :key="'emp-'+s" class="text-xs px-2 py-0.5 rounded-md bg-neutral-50 dark:bg-neutral-950 text-neutral-400 dark:text-neutral-600 border border-neutral-100 dark:border-neutral-800">{{ s }}</span>
                    </div>
                  </div>
                </div>

                <!-- 배치도에서 선택한 CCTV의 실시간 화면 -->
                <div v-if="liveCameraId" class="rounded-xl border border-neutral-200 dark:border-neutral-800 overflow-hidden flex-1 flex flex-col">
                  <div class="px-3 py-2 flex items-center justify-between bg-neutral-50 dark:bg-neutral-950 border-b border-neutral-100 dark:border-neutral-800 shrink-0">
                    <span class="text-xs font-medium text-neutral-600 dark:text-neutral-400 flex items-center gap-1.5">
                      <span class="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse shrink-0" /> {{ liveCameraName }} 실시간
                    </span>
                    <button @click="closeLiveView" class="text-neutral-400 dark:text-neutral-600 hover:text-neutral-600 dark:hover:text-neutral-300 text-xs">✕ 닫기</button>
                  </div>
                  <img :key="liveKey" :src="liveSrc" class="w-full flex-1 aspect-video object-cover bg-neutral-900" />
                </div>
              </div>
            </div>
          </div>

          <div v-else class="flex flex-col items-center justify-center py-20 text-neutral-400 dark:text-neutral-600 gap-2 text-sm text-center">
            <div class="text-2xl">📷</div>
            분석 결과를 불러오지 못했습니다
          </div>
        </div>

        <!-- 모니터링 -->
        <div class="bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-2xl shadow-sm p-6 lg:p-8">
          <div class="flex items-center justify-between gap-3 mb-6 flex-wrap">
            <div class="flex items-center gap-3 min-w-0">
              <div class="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-line text-xl">📊</div>
              <div class="min-w-0">
                <div class="text-xs font-medium uppercase tracking-wide text-fg-muted">모니터링</div>
                <div class="text-base font-semibold text-neutral-800 dark:text-neutral-100">오늘 점유 기록</div>
              </div>
            </div>
            <router-link :to="`/monitoring/${selectedId}`" class="shrink-0 text-sm text-fg-muted transition hover:text-fg">전체 보기 →</router-link>
          </div>

          <div v-if="monLoading" class="flex flex-col items-center justify-center py-20 text-neutral-400 dark:text-neutral-600 text-sm gap-3">
            <div class="w-9 h-9 rounded-full border-2 border-neutral-200 dark:border-neutral-800 border-t-blue-500 animate-spin" />
            불러오는 중...
          </div>

          <div v-else-if="!hasMonitoringData" class="flex flex-col items-center justify-center py-20 text-neutral-400 dark:text-neutral-600 gap-2 text-sm text-center">
            <div class="text-2xl">🕒</div>
            오늘 저장된 점유 기록이 없습니다.
          </div>

          <div v-else class="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <!-- 정각 기준 시간별 -->
            <div>
              <div class="text-xs font-semibold text-neutral-500 dark:text-neutral-400 uppercase tracking-wide mb-3">시간대별 점유</div>
              <div class="flex flex-wrap gap-2 mb-4">
                <button
                  v-for="h in hourlyStats"
                  :key="h.hour"
                  :disabled="!h.scheduled || h.occupied === null"
                  @click="toggleHour(h.hour)"
                  class="w-16 bg-neutral-50 dark:bg-neutral-950 rounded-lg border py-2 text-center transition"
                  :class="[
                    !h.scheduled || h.occupied === null ? 'border-neutral-100 dark:border-neutral-800 text-neutral-300 dark:text-neutral-700 cursor-not-allowed' : 'border-neutral-200 dark:border-neutral-800 hover:border-fg-muted/50',
                    selectedHour === h.hour ? '!border-fg-muted ring-1 ring-fg-muted bg-white dark:bg-neutral-900' : '',
                  ]"
                >
                  <div class="text-xs font-semibold" :class="h.scheduled && h.occupied !== null ? 'text-neutral-700 dark:text-neutral-300' : 'text-neutral-300 dark:text-neutral-700'">{{ h.time }}</div>
                  <div class="text-[10px] mt-0.5" :class="h.scheduled && h.occupied !== null ? 'text-neutral-400 dark:text-neutral-600' : 'text-neutral-300 dark:text-neutral-700'">
                    {{ h.occupied !== null ? `${h.occupied}석` : '-' }}
                  </div>
                </button>
              </div>

              <div v-if="selectedHourData" class="rounded-xl border border-line bg-canvas px-4 py-3">
                <div class="flex items-center gap-2 mb-2">
                  <span class="text-sm font-semibold text-fg">{{ selectedHourData.time }}</span>
                  <span class="text-xs text-neutral-500 dark:text-neutral-400">점유 {{ selectedHourData.occupied }}석 / {{ selectedHourData.total }}석</span>
                </div>
                <div v-if="selectedHourData.seats?.length" class="flex flex-wrap gap-1.5">
                  <span v-for="sid in selectedHourData.seats" :key="sid" class="text-xs px-2 py-0.5 rounded-full bg-red-100 text-red-700 font-medium">{{ sid }}번</span>
                </div>
                <div v-else class="text-xs text-neutral-400 dark:text-neutral-600">이 시간에 점유된 좌석이 없습니다.</div>
              </div>
            </div>

            <!-- 오늘 가장 오래 점유한 좌석 -->
            <div>
              <div class="text-xs font-semibold text-neutral-500 dark:text-neutral-400 uppercase tracking-wide mb-3">오늘 가장 오래 점유한 좌석</div>
              <div v-if="topSeats.length" class="space-y-2.5">
                <div v-for="(row, i) in topSeats" :key="row.seatId" class="flex items-center gap-3">
                  <span
                    class="text-xs font-bold w-9 h-7 shrink-0 rounded-md border flex items-center justify-center"
                    :class="i === 0 && row.occupiedMinutes > 0 ? 'border-red-300 text-red-600 bg-red-50' : 'border-neutral-200 dark:border-neutral-800 text-neutral-400 dark:text-neutral-600 bg-neutral-50 dark:bg-neutral-950'"
                  >{{ row.seatId }}</span>
                  <div class="flex-1 h-3 rounded-full overflow-hidden bg-neutral-100 dark:bg-neutral-800">
                    <div
                      class="h-full rounded-full bg-red-400 transition-all duration-500"
                      :style="{ width: (topSeats[0]?.occupiedMinutes ? Math.round(row.occupiedMinutes / topSeats[0].occupiedMinutes * 100) : 0) + '%' }"
                    />
                  </div>
                  <span class="text-xs w-16 text-right shrink-0 text-neutral-500 dark:text-neutral-400 tabular-nums">{{ formatMinutes(row.occupiedMinutes) }}</span>
                </div>
              </div>
              <p v-else class="text-xs text-neutral-400 dark:text-neutral-600">등록된 좌석이 없습니다.</p>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useClassroomStore } from '@/stores/classroomStore.js'
import api from '@/api'

const cStore = useClassroomStore()
const classroom = computed(() => cStore.current)

const STORAGE_KEY = 'home-classroom-id'
const selectedId = ref(null)
let occupancyEvents = null

onMounted(async () => {
  await cStore.fetchAll()
  const saved = Number(localStorage.getItem(STORAGE_KEY))
  if (saved && cStore.classrooms.some(c => c.id === saved)) {
    selectedId.value = saved
  } else if (cStore.classrooms.length) {
    selectedId.value = cStore.classrooms[0].id
  }
})

watch(selectedId, async (id) => {
  stopOccupancyEvents()
  seatResult.value = null
  mapData.value = null
  seatStats.value = {}
  hourlyStats.value = []
  selectedHour.value = null
  liveCameraId.value = null
  seatFaces.value = null
  clearInterval(patrolTimer)
  patrolState.value = null
  if (!id) return
  localStorage.setItem(STORAGE_KEY, String(id))
  await cStore.fetchOne(id)
  fetchMapData()
  fetchSeatOccupancy()
  fetchMonitoring()
  fetchSeatFaces()
  startOccupancyEvents(id)
})

function stopOccupancyEvents() {
  occupancyEvents?.close()
  occupancyEvents = null
}

function startOccupancyEvents(id) {
  stopOccupancyEvents()
  if (!window.EventSource) return
  occupancyEvents = new EventSource(`/api/analysis/${id}/occupancy-events`)
  occupancyEvents.addEventListener('occupancy', (event) => {
    if (document.hidden || Number(selectedId.value) !== Number(id)) return
    const payload = JSON.parse(event.data)
    applySnapshotOccupancy(payload.seats ?? {})
    fetchMonitoring()
    fetchSeatFaces()
  })
}

function applySnapshotOccupancy(seats) {
  const seatIds = allSeatIds.value
  const occupied = new Set(Object.entries(seats).filter(([, state]) => state === 'occupied').map(([sid]) => sid))
  const total = seatIds.length || Object.keys(seats).length
  const cameras = (classroom.value?.cameras ?? []).map((cam) => {
    const ids = getCameraSeatIds(cam)
    const occ = ids.filter((sid) => occupied.has(sid))
    return {
      camera_id: cam.camera_id,
      name: cam.name,
      total: ids.length,
      occupied_count: occ.length,
      occupied: occ,
      empty: ids.filter((sid) => !occupied.has(sid)),
    }
  })
  seatResult.value = {
    total_occupied: occupied.size,
    total_seats: total,
    cameras,
  }
  drawOccupancyMap()
}

// ── YOLO 좌석 점유 분석 (홈 접속 시 자동 실행) ────────────────────────────────

const seatLoading = ref(false)
const seatResult = ref(null)

async function fetchSeatOccupancy() {
  if (!selectedId.value) return
  if (seatLoading.value) return
  seatLoading.value = true
  try {
    const { data } = await api.get(`/analysis/${selectedId.value}/seat-occupancy`)
    seatResult.value = data
    drawOccupancyMap()
  } catch (e) {
    alert('좌석 점유 분석 실패: ' + (e.response?.data?.detail ?? e.message))
  } finally {
    seatLoading.value = false
  }
}

// '다시 분석': 지금 상황을 보려는 것이므로 좌석 점유와 얼굴 순찰을 함께 돌린다.
// (화면에 들어올 때는 마지막 순찰 결과를 쓰고, 카메라를 움직이지 않는다)
async function refreshAll() {
  fetchSeatOccupancy()
  if (!facePlaceId.value) return
  try {
    await api.post(`/face/places/${facePlaceId.value}/patrol/start`)
    pollPatrol()
  } catch (e) {
    patrolState.value = null   // 구역/카메라가 없으면 순찰 없이 좌석 점유만 갱신된다
  }
}

function pollPatrol() {
  clearInterval(patrolTimer)
  let lastSeatsLogged = patrolState.value?.seats_logged ?? 0
  patrolTimer = setInterval(async () => {
    try {
      const { data } = await api.get(`/face/places/${facePlaceId.value}/patrol/status`)
      const seatsChanged = (data.seats_logged ?? 0) !== lastSeatsLogged
      patrolState.value = data
      if (seatsChanged) {
        lastSeatsLogged = data.seats_logged ?? 0
        await fetchSeatFaces()
      }
      if (!data.running) {
        clearInterval(patrolTimer)
        await fetchSeatFaces()   // 끝난 순찰 결과로 배치도를 갱신
      }
    } catch {
      clearInterval(patrolTimer)
    }
  }, 2000)
}

// ── 배치도 오버레이 ──────────────────────────────────────────────────────────

const mapData = ref(null)
const mapCanvasRef = ref(null)
const seatFaces = ref(null)   // 최근 순찰의 자리번호별 인증 결과 {"30": {verified, name}, ...}
const facePlaceId = ref(null) // 이 교실과 연결된 얼굴 인식 장소
const patrolState = ref(null) // '다시 분석'으로 돌린 순찰의 진행 상태
let patrolTimer = null

// 이 교실과 연결된 얼굴 인식 장소의 최근 순찰 결과를 가져온다
async function fetchSeatFaces() {
  seatFaces.value = null
  try {
    const { data } = await api.get('/face/places')
    const place = data.places.find(p => p.classroom_id === Number(selectedId.value))
    facePlaceId.value = place?.id ?? null
    if (!place) return
    const res = await api.get(`/face/places/${place.id}/seat-logs`, { params: { limit: 1 } })
    seatFaces.value = res.data.snapshots[0]?.seats ?? null
    if (seatFaces.value) drawOccupancyMap()   // 분석 결과보다 늦게 도착해도 반영되도록
  } catch {
    seatFaces.value = null   // 얼굴 인식을 안 쓰는 교실이면 표시하지 않는다
  }
}
const mapScale = ref(1)

async function fetchMapData() {
  try {
    const { data } = await api.get(`/classrooms/${selectedId.value}/map-data`)
    mapData.value = data
    drawOccupancyMap()
  } catch {
    mapData.value = null
  }
}

// 자리에 앉은 사람 표시. 어느 배경에서도 보이도록 테두리를 함께 그린다.
function drawPerson(ctx, cx, cy, size, verified) {
  const r = size * 0.17
  ctx.fillStyle = verified ? '#ffffff' : '#111827'
  ctx.strokeStyle = verified ? '#334155' : '#000000'
  ctx.lineWidth = Math.max(1, size * 0.05)

  ctx.beginPath()                                   // 머리
  ctx.arc(cx, cy - size * 0.22, r, 0, Math.PI * 2)
  ctx.fill(); ctx.stroke()

  ctx.beginPath()                                   // 어깨·상체
  ctx.arc(cx, cy + size * 0.22, size * 0.27, Math.PI, 0)
  ctx.closePath()
  ctx.fill(); ctx.stroke()
}

async function drawOccupancyMap() {
  await nextTick()
  const canvas = mapCanvasRef.value
  if (!canvas || !mapData.value?.objects?.length || !seatResult.value) return

  const { objects, mapW = 900, mapH = 600 } = mapData.value
  const cameras = seatResult.value.cameras ?? []

  const allOccupied = new Set()
  const allEmpty = new Set()
  for (const cam of cameras) {
    for (const s of cam.occupied ?? []) allOccupied.add(s)
    for (const s of cam.empty ?? []) allEmpty.add(s)
  }

  const maxW = Math.min(canvas.parentElement?.clientWidth ?? 500, 560)
  const scale = Math.min(maxW / mapW, 1)
  mapScale.value = scale
  canvas.width = Math.round(mapW * scale)
  canvas.height = Math.round(mapH * scale)

  const ctx = canvas.getContext('2d')
  ctx.clearRect(0, 0, canvas.width, canvas.height)

  const personMarks = []   // 의자에 그릴 사람 표시 (도형을 다 그린 뒤 마지막에 얹는다)
  const MAP = {
    border: '#a9b3c2',
    chair: '#e2e8f1',
    text: '#061735',
    muted: '#53647f',
    occupied: '#147b70',
    occupiedFill: 'rgba(20,123,112,0.18)',
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
        ctx.fillStyle = MAP.chair
        ctx.beginPath(); ctx.roundRect(x, y, w, h, 8 * scale); ctx.fill()
      })
    } else if (obj.type === 'cctv') {
      const x = obj.x * scale, y = obj.y * scale
      const w = obj.w * scale, h = obj.h * scale
      ctx.fillStyle = '#ffffff'
      ctx.strokeStyle = MAP.border
      ctx.lineWidth = 3 * scale
      ctx.beginPath(); ctx.roundRect(x, y, w, h, 12 * scale); ctx.fill(); ctx.stroke()
      ctx.fillStyle = MAP.muted
      const label = obj.label || 'CCTV'
      ctx.font = `700 ${Math.max(10, Math.min(h * 0.24, 22, (w * 0.78) / (label.length * 0.7)))}px sans-serif`
      ctx.textAlign = 'center'; ctx.textBaseline = 'middle'
      ctx.fillText(label, x + w / 2, y + h / 2)
    } else if (obj.type === 'desk') {
      const label = obj.label?.trim()
      const isOcc = label && allOccupied.has(label)
      const isEmpty = label && !isOcc && allEmpty.has(label)
      withRotation(obj, (x, y, w, h) => {
        ctx.fillStyle = isOcc ? MAP.occupiedFill : '#ffffff'
        ctx.strokeStyle = isOcc ? MAP.occupied : MAP.border
        ctx.lineWidth = 3 * scale
        ctx.beginPath(); ctx.roundRect(x, y, w, h, 10 * scale); ctx.fill(); ctx.stroke()
        if (!label) return
        // 좌석 점유가 '점유'로 판정한 자리에만 표시한다. 서 있는 사람의 얼굴이 뒷자리 영역에
        // 잡히는 경우가 있어, 몸통을 보는 좌석 점유로 교차 검증해 걸러낸다.
        const face = isOcc ? seatFaces.value?.[label] : null
        // 사람은 책상이 아니라 그 자리의 의자에 그린다 (책상 위에 앉은 것처럼 보이지 않도록).
        // 의자는 모든 객체를 그린 뒤에 표시해야 다른 도형에 가리지 않는다.
        const chair = face ? nearestChair(objects, obj) : null
        if (chair) personMarks.push({ chair, verified: face.verified })

        ctx.font = `700 ${Math.max(11, Math.min(h * 0.42, 30))}px sans-serif`
        ctx.fillStyle = MAP.text
        ctx.textAlign = 'center'; ctx.textBaseline = 'middle'
        ctx.fillText(label, x + w / 2, y + h / 2)
      })
    }
  }

  for (const { chair, verified } of personMarks) {
    drawPerson(ctx,
      (chair.x + chair.w / 2) * scale,
      (chair.y + chair.h / 2) * scale,
      Math.min(chair.w, chair.h) * scale * 0.95,
      verified)
  }
  ctx.textAlign = 'left'
}

// 책상에 딸린 의자 찾기. 의자는 책상 바로 아래 붙어 있으므로 중심이 가장 가까운 것을 쓴다.
function nearestChair(objects, desk) {
  const dx = desk.x + desk.w / 2
  const dy = desk.y + desk.h / 2
  let best = null
  let bestDist = Infinity
  for (const o of objects) {
    if (o.type !== 'chair') continue
    const dist = (o.x + o.w / 2 - dx) ** 2 + (o.y + o.h / 2 - dy) ** 2
    if (dist < bestDist) { best = o; bestDist = dist }
  }
  // 너무 먼 의자는 다른 자리 것이므로 쓰지 않는다 (책상 크기의 2배 이내만 인정)
  return bestDist <= (desk.w * 2) ** 2 ? best : null
}

// 배치도의 좌석(책상) 클릭 → 그 좌석을 담당하는 CCTV의 실시간 화면 표시
function onMapClick(evt) {
  const canvas = mapCanvasRef.value
  const objects = mapData.value?.objects
  if (!canvas || !objects?.length) return

  const rect = canvas.getBoundingClientRect()
  const scaleX = canvas.width / rect.width
  const scaleY = canvas.height / rect.height
  const clickX = (evt.clientX - rect.left) * scaleX
  const clickY = (evt.clientY - rect.top) * scaleY
  const scale = mapScale.value

  const hit = objects.find(obj => {
    if (obj.type !== 'desk') return false
    const x = obj.x * scale, y = obj.y * scale, w = obj.w * scale, h = obj.h * scale
    return clickX >= x && clickX <= x + w && clickY >= y && clickY <= y + h
  })
  if (!hit) return

  const seatLabel = hit.label?.trim()
  const cctvIds = hit.cctvIds ?? (hit.cctvId != null ? [hit.cctvId] : [])
  if (!cctvIds.length) {
    alert(`${seatLabel ? seatLabel + '번 ' : ''}좌석에 배정된 CCTV가 없습니다. 맵 에디터에서 카메라를 배정해주세요.`)
    return
  }

  const cctvObj = objects.find(o => o.type === 'cctv' && cctvIds.includes(o.id))
  const cctvLabel = cctvObj?.label?.trim()
  const cam = (classroom.value?.cameras ?? []).find(c => c.name === cctvLabel)
  if (!cam) {
    alert(`"${cctvLabel || 'CCTV'}" 이름과 일치하는 카메라를 찾을 수 없습니다. 맵 에디터에서 CCTV 이름을 카메라 이름과 동일하게 설정해주세요.`)
    return
  }
  liveCameraId.value = cam.camera_id
  liveCameraName.value = seatLabel ? `${cam.name} · ${seatLabel}번 좌석` : cam.name
  liveKey.value++
}

const liveCameraId = ref(null)
const liveCameraName = ref('')
const liveKey = ref(0)

function closeLiveView() {
  liveCameraId.value = null
}

const liveSrc = computed(() => `/api/analysis/${selectedId.value}/live/${liveCameraId.value}?t=${liveKey.value}`)

// ── 오늘 모니터링 요약 ────────────────────────────────────────────────────────

function pad(n) { return String(n).padStart(2, '0') }
const todayStr = (() => {
  const d = new Date()
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
})()

const monLoading = ref(false)
const seatStats = ref({})
const hourlyStats = ref([])
const selectedHour = ref(null)
let pendingMonitoringRefresh = false

const selectedHourData = computed(() => hourlyStats.value.find(h => h.hour === selectedHour.value) ?? null)
function toggleHour(hour) {
  selectedHour.value = selectedHour.value === hour ? null : hour
}

async function fetchMonitoring() {
  if (!selectedId.value) return
  if (monLoading.value) {
    pendingMonitoringRefresh = true
    return
  }
  monLoading.value = true
  selectedHour.value = null
  try {
    const [dailyRes, hourlyRes] = await Promise.all([
      api.get(`/analysis/${selectedId.value}/occupancy-stats-daily`, { params: { date: todayStr } }),
      api.get(`/analysis/${selectedId.value}/occupancy-hourly`, { params: { date: todayStr } }),
    ])
    seatStats.value = dailyRes.data.seats ?? {}
    hourlyStats.value = hourlyRes.data.hours ?? []
  } catch (e) {
    seatStats.value = {}
    hourlyStats.value = []
  } finally {
    monLoading.value = false
    if (pendingMonitoringRefresh) {
      pendingMonitoringRefresh = false
      fetchMonitoring()
    }
  }
}

const allSeatIds = computed(() => {
  const ids = new Set()
  for (const cam of classroom.value?.cameras ?? []) {
    for (const sid of getCameraSeatIds(cam)) ids.add(sid)
  }
  return [...ids].sort((a, b) => Number(a) - Number(b))
})

function getCameraSeatIds(cam) {
  const seatIds = cam?.seat_ids?.length
    ? cam.seat_ids
    : Object.keys(cam?.seat_lines ?? {})
  return seatIds.map(String)
}

const hasMonitoringData = computed(() => Object.keys(seatStats.value).length > 0)

function formatMinutes(min) {
  if (min <= 0) return '0분'
  const h = Math.floor(min / 60)
  const m = min % 60
  return h ? `${h}시간 ${m}분` : `${m}분`
}

const topSeats = computed(() => {
  const rows = allSeatIds.value.map(seatId => ({
    seatId,
    occupiedMinutes: seatStats.value[seatId]?.occupied_minutes ?? 0,
  }))
  return rows
    .sort((a, b) => b.occupiedMinutes - a.occupiedMinutes || Number(a.seatId) - Number(b.seatId))
    .slice(0, 5)
})

// 화면을 벗어나면 진행 상황 폴링만 멈춘다 (순찰 자체는 끝까지 돌게 둔다)
onUnmounted(() => {
  clearInterval(patrolTimer)
  stopOccupancyEvents()
})
</script>

<style scoped>
.btn-primary {
  @apply inline-flex items-center gap-1.5 rounded-lg bg-fg px-4 py-2 text-sm font-semibold text-canvas transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50;
}
</style>
