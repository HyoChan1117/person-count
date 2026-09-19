<template>
  <div class="ds-root h-full overflow-y-auto bg-canvas p-section">
    <div class="mx-auto flex w-full max-w-[1680px] flex-col gap-section">

      <!-- 헤더 -->
      <div class="flex flex-col gap-gutter sm:flex-row sm:items-end sm:justify-between">
        <div>
          <router-link to="/face" class="text-sm text-fg-muted transition-colors hover:text-fg">
            ← 얼굴 인식
          </router-link>
          <div class="mt-1 flex items-center gap-2">
            <h1 class="text-3xl font-bold tracking-tight text-fg">구역 등록</h1>
            <span v-if="mockActive" class="rounded-full border border-state-unknown/30 bg-state-unknown/10 px-2 py-0.5 text-xs font-semibold text-state-unknown">목데이터</span>
          </div>
          <p class="mt-1 text-lg text-fg-muted">{{ place?.name }}의 PTZ 카메라를 움직여 순찰할 구역을 등록하세요</p>
        </div>
        <div class="flex items-center gap-3 shrink-0">
          <div v-if="position" class="tabular-nums text-sm text-fg-muted">
            현재 좌표 · 팬 {{ position.pan }} · 틸트 {{ position.tilt }} · 줌 {{ position.zoom }}
          </div>
          <button
            @click="toggleMock"
            class="rounded-lg border px-3 py-2 text-sm font-medium transition-colors"
            :class="mockActive
              ? 'border-state-unknown bg-state-unknown text-canvas hover:opacity-90'
              : 'border-line text-fg-muted hover:bg-line/40 hover:text-fg'"
          >{{ mockActive ? '🧪 목데이터 끄기' : '🧪 목데이터로 보기' }}</button>
        </div>
      </div>

      <!-- PTZ 카메라가 없는 장소 -->
      <div v-if="place && !place.camera?.ip" class="rounded-card border border-line bg-card shadow-card">
        <div class="flex flex-col items-center justify-center py-20 text-neutral-400 dark:text-neutral-600 gap-3 text-center px-6">
          <div class="flex h-14 w-14 items-center justify-center rounded-card border border-line bg-canvas text-2xl">📷</div>
          <p class="text-sm">이 장소에는 PTZ 카메라가 없습니다.</p>
          <p class="text-xs">
            구역을 등록하려면
            <router-link :to="`/face/${placeId}/camera`" class="font-medium text-fg underline underline-offset-2">카메라 설정</router-link>에서
            카메라 IP를 입력해주세요.
          </p>
        </div>
      </div>

      <template v-else>
      <div v-if="cameraError" class="mb-6 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
        {{ cameraError }}
      </div>

      <div class="grid grid-cols-1 xl:grid-cols-3 gap-6 items-start">

        <!-- 미리보기 + 제어 -->
        <div class="xl:col-span-2 overflow-hidden rounded-card border border-line bg-card shadow-card">
          <div class="flex items-center justify-between border-b border-line bg-card px-4 py-2.5">
            <span class="text-sm font-medium text-neutral-600 dark:text-neutral-400 flex items-center gap-2">
              <span class="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" /> PTZ 카메라
            </span>
            <span class="text-xs text-neutral-400 dark:text-neutral-600">조준용 미리보기 (탐지 없음)</span>
          </div>
          <!-- 조준용 미리보기에도 얼굴이 나올 수 있어 기본 블러. 조준하는 동안 유지되도록 자동 재블러는 끈다 -->
          <BlurredImage :src="previewSrc" alt="PTZ 카메라 미리보기" :rounded="false" :auto-reblur-ms="0" class="w-full aspect-video" />

          <!-- 방향 제어 (키보드로 조작, 아래 표시는 눌린 키를 보여준다) -->
          <div class="p-5 flex flex-wrap items-center justify-center gap-6">
            <div class="grid grid-cols-3 gap-1.5">
              <span />
              <div class="pad" :class="{ 'pad-on': pressed.has('ArrowUp') }">↑</div>
              <span />
              <div class="pad" :class="{ 'pad-on': pressed.has('ArrowLeft') }">←</div>
              <div class="pad !text-[11px] !text-neutral-400 dark:text-neutral-600">방향키</div>
              <div class="pad" :class="{ 'pad-on': pressed.has('ArrowRight') }">→</div>
              <span />
              <div class="pad" :class="{ 'pad-on': pressed.has('ArrowDown') }">↓</div>
              <span />
            </div>

            <div class="flex flex-col gap-1.5">
              <div class="pad w-20 text-xs" :class="{ 'pad-on': pressed.has('+') }">줌 +</div>
              <div class="pad w-20 text-xs" :class="{ 'pad-on': pressed.has('-') }">줌 −</div>
            </div>

            <div class="flex flex-col gap-2">
              <input
                v-model="newZoneName"
                placeholder="구역 이름 (예: 앞줄 좌측)"
                class="w-52 rounded-lg border border-line bg-canvas px-3 py-2 text-sm text-fg placeholder:text-fg-muted focus:outline-none focus-visible:border-fg-muted"
                @keyup.enter="saveZone"
              />
              <button
                @click="saveZone"
                :disabled="saving"
                class="rounded-lg bg-fg px-4 py-2 text-sm font-semibold text-canvas transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
              >{{ saving ? '저장 중...' : '📍 이 위치 등록' }}</button>
            </div>
          </div>
          <p class="px-5 pb-4 text-[11px] text-neutral-400 dark:text-neutral-600 text-center">
            방향키로 상하좌우, <span class="font-medium">+</span> / <span class="font-medium">−</span> 키로 줌을 조작합니다.
            누르고 있는 동안 움직이고 떼면 멈춥니다. (구역 이름 입력 중에는 동작하지 않습니다)
          </p>
        </div>

        <!-- 등록된 구역 -->
        <div class="rounded-card border border-line bg-card p-card shadow-card">
          <div class="flex items-center justify-between mb-1">
            <span class="text-sm font-semibold text-neutral-800 dark:text-neutral-100">순찰 구역</span>
            <span class="text-xs text-neutral-400 dark:text-neutral-600">{{ zones.length }}개</span>
          </div>
          <p class="text-[11px] text-neutral-400 dark:text-neutral-600 mb-3">
            위에서부터 이 순서대로 돌고 <span class="font-medium text-neutral-500 dark:text-neutral-400">마지막 구역에서 끝납니다</span>. 끌어서 순서를 바꿀 수 있고, 자리 영역이 없는 구역은 이동만 합니다.
          </p>

          <div v-if="!zones.length" class="flex flex-col items-center justify-center py-12 text-neutral-400 dark:text-neutral-600 gap-2 text-sm text-center">
            <div class="text-2xl">📍</div>
            아직 등록된 구역이 없습니다.<br>카메라를 움직여 위치를 등록해보세요.
          </div>

          <div v-else class="space-y-2">
            <div
              v-for="(z, zi) in zones"
              :key="z.id"
              draggable="true"
              @dragstart="dragFrom = zi"
              @dragover.prevent="dragOver = zi"
              @dragend="dragFrom = null; dragOver = null"
              @drop.prevent="dropZone(zi)"
              @click="selectedZoneId = selectedZoneId === z.id ? null : z.id"
              class="rounded-xl border p-3 transition group cursor-pointer"
              :class="[
                selectedZoneId === z.id ? 'border-fg-muted bg-line/40' : 'border-line hover:border-fg-muted/50',
                dragFrom === zi ? 'opacity-40' : '',
                dragOver === zi && dragFrom !== null && dragFrom !== zi ? '!border-fg-muted border-dashed' : '',
              ]"
            >
              <div class="flex items-center gap-2">
                <span class="text-neutral-300 dark:text-neutral-700 cursor-grab select-none shrink-0" title="끌어서 순서 변경">⠿</span>
                <span class="w-5 text-[11px] text-neutral-400 dark:text-neutral-600 tabular-nums shrink-0">{{ zi + 1 }}</span>
                <div class="flex-1 min-w-0">
                  <div class="text-sm font-medium text-neutral-700 dark:text-neutral-300 truncate">{{ z.name }}</div>
                  <div class="text-[11px] text-neutral-400 dark:text-neutral-600 tabular-nums">
                    팬 {{ z.pan }} · 틸트 {{ z.tilt }} · 줌 {{ z.zoom }}
                    <span v-if="z.rois?.length" class="text-state-occupied"> · 자리 {{ z.rois.length }}개</span>
                    <span v-else class="text-neutral-400 dark:text-neutral-600"> · 이동만 (인식 안 함)</span>
                  </div>
                </div>
                <button
                  @click.stop="goto(z)"
                  class="text-xs bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300 px-2.5 py-1.5 rounded-lg hover:bg-neutral-200 dark:hover:bg-neutral-700 transition shrink-0"
                >이동</button>
                <button
                  @click.stop="removeZone(z)"
                  title="구역 삭제"
                  class="text-neutral-300 dark:text-neutral-700 hover:text-red-400 opacity-0 group-hover:opacity-100 transition px-1 shrink-0"
                >✕</button>
              </div>

              <!-- 선택한 구역에서만 ROI 설정 / 테스트 -->
              <div v-if="selectedZoneId === z.id" class="mt-2.5 flex gap-1.5">
                <button
                  @click.stop="openRoiEditor(z)"
                  class="flex-1 rounded-lg bg-fg py-1.5 text-xs font-semibold text-canvas transition-opacity hover:opacity-90"
                >{{ z.rois?.length ? '자리 영역 수정' : '자리 영역 설정' }}</button>
                <button
                  @click.stop="runZoneTest(z)"
                  :disabled="testing"
                  class="flex-1 text-xs bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300 py-1.5 rounded-lg hover:bg-neutral-200 dark:hover:bg-neutral-700 transition disabled:opacity-50"
                >{{ testing === z.id ? '확인 중...' : '인식 테스트' }}</button>
              </div>
            </div>
          </div>
        </div>
      </div>
      </template>
    </div>

    <!-- 인식 테스트 결과 -->
    <div v-if="testResult" class="fixed inset-0 z-50 flex items-center justify-center bg-fg/50 p-6" @click.self="testResult = null">
      <div class="w-full max-w-md rounded-card border border-line bg-card p-card shadow-xl">
        <div class="flex items-start justify-between gap-3 mb-4">
          <div>
            <h2 class="font-bold text-neutral-800 dark:text-neutral-100">{{ testResult.zone }} · 인식 테스트</h2>
            <p class="text-xs text-neutral-500 dark:text-neutral-400 mt-0.5">
              얼굴 {{ testResult.detected }}명 검출<span v-if="testResult.outside_roi"> · 자리 밖 {{ testResult.outside_roi }}명 무시</span>
            </p>
          </div>
          <button @click="testResult = null" class="text-neutral-400 dark:text-neutral-600 hover:text-neutral-600 dark:hover:text-neutral-300 shrink-0">✕</button>
        </div>

        <div v-if="!Object.keys(testResult.seats).length" class="text-sm text-neutral-500 dark:text-neutral-400 py-4">
          이 구역에는 자리 영역이 없어 자리별 결과를 낼 수 없습니다.
          검출된 얼굴은 {{ testResult.detected }}명입니다.
        </div>

        <div v-else class="space-y-1.5 max-h-80 overflow-y-auto">
          <div
            v-for="(v, seat) in testResult.seats"
            :key="seat"
            class="flex items-center justify-between gap-2 rounded-lg border px-3 py-2 text-sm"
            :class="v ? (v.authorized ? 'border-state-occupied/30 bg-state-occupied/10' : 'border-state-alert/30 bg-state-alert/10') : 'border-line bg-canvas/40'"
          >
            <span class="font-medium text-neutral-700 dark:text-neutral-300">{{ seat }}</span>
            <span v-if="!v" class="text-xs text-neutral-400 dark:text-neutral-600">비어있음</span>
            <span v-else class="text-xs" :class="v.authorized ? 'text-emerald-700' : 'text-red-600'">
              {{ v.name ?? '미등록 인물' }} · {{ v.score }}<span v-if="v.name"> · {{ v.authorized ? '허가' : '미허가' }}</span>
            </span>
          </div>
        </div>

        <p class="text-[11px] text-neutral-400 dark:text-neutral-600 mt-4">기록은 남기지 않습니다. 자리 영역을 조정하며 반복해서 확인해보세요.</p>
      </div>
    </div>

    <!-- ROI 편집 -->
    <RoiEditorModal
      v-if="roiZone"
      :place-id="placeId"
      :zone="roiZone"
      @close="roiZone = null"
      @saved="fetchPlace"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import api from '@/api'
import RoiEditorModal from '@/components/modals/RoiEditorModal.vue'
import BlurredImage from '@/components/ui/BlurredImage.vue'
import { generateMockImageDataUrl } from '@/utils/mockImage'
import { useMockToggle } from '@/composables/useMockToggle'

const SPEED = 100

const route = useRoute()
const placeId = route.params.id

// ── 목데이터 모드 ────────────────────────────────────────────────────────────

const mockPreviewImg = ref('')
let mockNextZoneId = 1

function buildMockZones() {
  return [
    { id: mockNextZoneId++, name: '앞줄 좌측', pan: 300, tilt: 100, zoom: 20, rois: [{ points: [] }] },
    { id: mockNextZoneId++, name: '앞줄 우측', pan: 1200, tilt: 100, zoom: 20, rois: [{ points: [] }] },
    { id: mockNextZoneId++, name: '뒷줄 전체', pan: 700, tilt: 250, zoom: 15, rois: [] },
  ]
}

const { mockActive, toggleMock } = useMockToggle(
  () => {
    mockPreviewImg.value = generateMockImageDataUrl('MOCK PTZ PREVIEW', 960, 540, '#18181b')
    place.value = { id: placeId, name: place.value?.name ?? '샘플 감시 장소', camera: { ip: '192.168.0.50' } }
    zones.value = buildMockZones()
    position.value = { pan: 700, tilt: 150, zoom: 20 }
    cameraError.value = ''
  },
  () => {
    fetchPlace()
    fetchPosition()
  },
)

const previewSrc = computed(() => (mockActive.value ? mockPreviewImg.value : `/api/face/places/${placeId}/ptz/preview`))
const place = ref(null)
const position = ref(null)
const zones = ref([])
const newZoneName = ref('')
const saving = ref(false)
const cameraError = ref('')
const selectedZoneId = ref(null)
const roiZone = ref(null)
const testing = ref(null)      // 확인 중인 구역 id
const testResult = ref(null)
const dragFrom = ref(null)     // 끌고 있는 항목 위치
const dragOver = ref(null)     // 놓일 위치

function reportError(e, fallback) {
  cameraError.value = e.response?.data?.detail ?? `${fallback}: ${e.message}`
}

async function fetchPlace() {
  const { data } = await api.get(`/face/places/${placeId}`)
  place.value = data
  zones.value = data.zones
}

async function fetchPosition() {
  try {
    const { data } = await api.get(`/face/places/${placeId}/ptz/position`)
    position.value = data
    cameraError.value = ''
  } catch (e) {
    reportError(e, '카메라 위치를 가져오지 못했습니다')
  }
}

async function move(pan = 0, tilt = 0, zoom = 0) {
  if (mockActive.value) {
    position.value = {
      pan: position.value.pan + pan,
      tilt: position.value.tilt + tilt,
      zoom: Math.max(10, position.value.zoom + zoom),
    }
    return
  }
  try {
    await api.post(`/face/places/${placeId}/ptz/move`, { pan, tilt, zoom })
  } catch (e) {
    reportError(e, '카메라를 움직이지 못했습니다')
  }
}

async function stop() {
  if (mockActive.value) return
  try {
    await api.post(`/face/places/${placeId}/ptz/stop`)
  } catch (e) {
    reportError(e, '카메라를 멈추지 못했습니다')
  }
  fetchPosition()
}

// ── 키보드 조작 ──────────────────────────────────────────────────────────────

// 같은 키의 자동 반복(keydown 연타)으로 카메라에 요청이 쏟아지지 않도록
// 현재 눌려 있는 키를 추적하고, 조합이 바뀔 때만 명령을 보낸다.
const pressed = ref(new Set())

const KEY_MOVES = {
  ArrowUp: { tilt: SPEED },
  ArrowDown: { tilt: -SPEED },
  ArrowLeft: { pan: -SPEED },
  ArrowRight: { pan: SPEED },
  '+': { zoom: SPEED },
  '-': { zoom: -SPEED },
}

// '=' 와 '_' 는 shift 없이 누른 +/- 자리라 같은 동작으로 취급한다
function normalizeKey(key) {
  if (key === '=' || key === '+') return '+'
  if (key === '_' || key === '-') return '-'
  return key
}

function isTyping(target) {
  return target?.tagName === 'INPUT' || target?.tagName === 'TEXTAREA'
}

function sendPressedMove() {
  let pan = 0, tilt = 0, zoom = 0
  for (const key of pressed.value) {
    const m = KEY_MOVES[key]
    pan += m.pan ?? 0
    tilt += m.tilt ?? 0
    zoom += m.zoom ?? 0
  }
  if (!pan && !tilt && !zoom) stop()
  else move(pan, tilt, zoom)
}

function onKeyDown(e) {
  if (isTyping(e.target) || !place.value?.camera?.ip) return
  const key = normalizeKey(e.key)
  if (!KEY_MOVES[key]) return
  e.preventDefault()          // 방향키로 화면이 스크롤되지 않게
  if (pressed.value.has(key)) return   // 자동 반복은 무시
  pressed.value.add(key)
  sendPressedMove()
}

function onKeyUp(e) {
  const key = normalizeKey(e.key)
  if (!pressed.value.delete(key)) return
  sendPressedMove()
}

// 키를 누른 채 창을 벗어나면 keyup을 못 받아 카메라가 계속 돈다
function onBlur() {
  if (!pressed.value.size) return
  pressed.value.clear()
  stop()
}

async function saveZone() {
  const name = newZoneName.value.trim()
  if (!name) return
  if (mockActive.value) {
    zones.value.push({ id: mockNextZoneId++, name, pan: position.value.pan, tilt: position.value.tilt, zoom: position.value.zoom, rois: [] })
    newZoneName.value = ''
    return
  }
  saving.value = true
  try {
    await api.post(`/face/places/${placeId}/zones`, { name })
    newZoneName.value = ''
    await fetchPlace()
  } catch (e) {
    reportError(e, '구역 저장에 실패했습니다')
  } finally {
    saving.value = false
  }
}

async function goto(zone) {
  if (mockActive.value) {
    position.value = { pan: zone.pan, tilt: zone.tilt, zoom: zone.zoom }
    return
  }
  try {
    await api.post(`/face/places/${placeId}/zones/${zone.id}/goto`)
    setTimeout(fetchPosition, 1500)  // 이동이 끝난 뒤 좌표를 다시 읽는다
  } catch (e) {
    reportError(e, '구역으로 이동하지 못했습니다')
  }
}

// 끌어 놓은 자리로 순서를 옮기고 저장한다
async function dropZone(toIndex) {
  const from = dragFrom.value
  dragFrom.value = null
  dragOver.value = null
  if (from === null || from === toIndex) return

  const moved = zones.value.splice(from, 1)[0]
  zones.value.splice(toIndex, 0, moved)

  if (mockActive.value) return
  try {
    await api.put(`/face/places/${placeId}/zones/order`, { zone_ids: zones.value.map(z => z.id) })
  } catch (e) {
    reportError(e, '순서를 저장하지 못했습니다')
    await fetchPlace()   // 저장에 실패하면 화면을 서버 상태로 되돌린다
  }
}

// 한 구역만 즉시 확인 (카메라 이동 + 촬영 + 자리별 인식, 기록은 남기지 않음)
async function runZoneTest(zone) {
  testing.value = zone.id
  if (mockActive.value) {
    await new Promise(r => setTimeout(r, 400))
    const seats = {}
    if (zone.rois?.length) {
      seats['1'] = Math.random() > 0.4 ? { verified: true, name: '김민석', score: 0.71 } : null
      seats['2'] = Math.random() > 0.4 ? { verified: false, name: null, score: 0.0 } : null
    }
    testResult.value = { zone: zone.name, detected: Object.values(seats).filter(Boolean).length, outside_roi: 0, seats }
    testing.value = null
    return
  }
  try {
    const { data } = await api.post(`/face/places/${placeId}/zones/${zone.id}/test`)
    testResult.value = data
  } catch (e) {
    reportError(e, '인식 테스트에 실패했습니다')
  } finally {
    testing.value = null
  }
}

async function removeZone(zone) {
  if (!confirm(`"${zone.name}" 구역을 삭제하시겠습니까?`)) return
  if (mockActive.value) {
    zones.value = zones.value.filter(z => z.id !== zone.id)
    return
  }
  await api.delete(`/face/places/${placeId}/zones/${zone.id}`)
  await fetchPlace()
}

function openRoiEditor(zone) {
  if (mockActive.value) {
    alert('목데이터 모드에서는 자리 영역(ROI) 편집을 지원하지 않습니다. 실제 카메라 연결 후 이용해주세요.')
    return
  }
  roiZone.value = zone
}

onMounted(async () => {
  window.addEventListener('keydown', onKeyDown)
  window.addEventListener('keyup', onKeyUp)
  window.addEventListener('blur', onBlur)
  await fetchPlace()
  // PTZ 카메라가 없는 장소는 카메라를 호출하지 않는다
  if (place.value?.camera?.ip) fetchPosition()
})

// 화면을 벗어날 때 카메라가 계속 움직이고 있지 않도록 확실히 멈춘다
onUnmounted(() => {
  window.removeEventListener('keydown', onKeyDown)
  window.removeEventListener('keyup', onKeyUp)
  window.removeEventListener('blur', onBlur)
  if (!mockActive.value) api.post(`/face/places/${placeId}/ptz/stop`).catch(() => {})
})
</script>

<style scoped>
.pad {
  @apply flex h-12 w-12 select-none items-center justify-center rounded-lg border border-line bg-canvas text-lg text-fg-muted transition-colors;
}
.pad-on {
  @apply border-fg bg-fg text-canvas;
}
</style>
