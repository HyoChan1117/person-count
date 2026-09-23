<template>
  <div class="ds-root flex h-full flex-col overflow-hidden bg-canvas p-section">
    <div class="mx-auto flex min-h-0 w-full max-w-[1680px] flex-1 flex-col gap-gutter overflow-hidden">

      <!-- 헤더 -->
      <div class="flex shrink-0 flex-col gap-gutter sm:flex-row sm:items-end sm:justify-between">
        <div>
          <router-link to="/face" class="text-sm text-fg-muted transition-colors hover:text-fg">
            ← 얼굴 인식
          </router-link>
          <div class="mt-1 flex items-center gap-2">
            <h1 class="text-3xl font-bold tracking-tight text-fg">구역 등록</h1>
          </div>
          <p class="mt-1 text-lg text-fg-muted">{{ place?.name }}의 PTZ 카메라를 움직여 순찰할 구역을 등록하세요</p>
        </div>
        <div class="flex shrink-0 flex-wrap items-center gap-3">
          <div v-if="position" class="rounded-lg border border-line bg-card px-3 py-2 font-mono text-xs tabular-nums text-fg-muted">
            현재 좌표 · 팬 {{ position.pan }} · 틸트 {{ position.tilt }} · 줌 {{ position.zoom }}
          </div>
        </div>
      </div>

      <!-- PTZ 카메라가 없는 장소 -->
      <div v-if="place && !place.camera?.ip" class="flex min-h-0 flex-1 rounded-card border border-line bg-card shadow-card">
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
      <div v-if="cameraError" class="shrink-0 rounded-lg border border-state-alert/30 bg-state-alert/10 px-4 py-3 text-sm text-state-alert">
        {{ cameraError }}
      </div>

      <div class="grid min-h-0 flex-1 grid-cols-1 gap-gutter overflow-hidden xl:grid-cols-[minmax(0,1fr)_minmax(22rem,28rem)]">

        <!-- 미리보기 + 제어 -->
        <div class="flex min-h-0 flex-col overflow-hidden rounded-card border border-line bg-card shadow-card">
          <div class="flex shrink-0 items-center justify-between border-b border-line px-card py-3">
            <span class="flex items-center gap-2 text-sm font-semibold text-fg">
              <span class="h-2 w-2 rounded-full bg-state-alert" /> PTZ 카메라
            </span>
            <span class="text-xs text-fg-muted">조준용 미리보기 (탐지 없음)</span>
          </div>
          <!-- 조준용 미리보기에도 얼굴이 나올 수 있어 기본 블러. 조준하는 동안 유지되도록 자동 재블러는 끈다 -->
          <BlurredImage :src="previewSrc" alt="PTZ 카메라 미리보기" :rounded="false" :auto-reblur-ms="0" class="min-h-0 w-full flex-1" />

          <!-- 방향 제어 (키보드로 조작, 아래 표시는 눌린 키를 보여준다) -->
          <div class="grid shrink-0 grid-cols-1 gap-gutter border-t border-line p-card lg:grid-cols-[auto_auto_minmax(14rem,22rem)] lg:items-center lg:justify-center">
            <div class="grid grid-cols-3 gap-1.5 justify-self-center">
              <span />
              <button type="button" class="pad" :class="{ 'pad-on': pressed.has('ArrowUp') }" aria-label="위로 이동" @pointerdown.prevent="pressControl('ArrowUp')" @pointerup.prevent="releaseControl('ArrowUp')" @pointerleave="releaseControl('ArrowUp')" @pointercancel="releaseControl('ArrowUp')">↑</button>
              <span />
              <button type="button" class="pad" :class="{ 'pad-on': pressed.has('ArrowLeft') }" aria-label="왼쪽으로 이동" @pointerdown.prevent="pressControl('ArrowLeft')" @pointerup.prevent="releaseControl('ArrowLeft')" @pointerleave="releaseControl('ArrowLeft')" @pointercancel="releaseControl('ArrowLeft')">←</button>
              <div class="pad !cursor-default !text-[11px] !text-fg-muted">PTZ</div>
              <button type="button" class="pad" :class="{ 'pad-on': pressed.has('ArrowRight') }" aria-label="오른쪽으로 이동" @pointerdown.prevent="pressControl('ArrowRight')" @pointerup.prevent="releaseControl('ArrowRight')" @pointerleave="releaseControl('ArrowRight')" @pointercancel="releaseControl('ArrowRight')">→</button>
              <span />
              <button type="button" class="pad" :class="{ 'pad-on': pressed.has('ArrowDown') }" aria-label="아래로 이동" @pointerdown.prevent="pressControl('ArrowDown')" @pointerup.prevent="releaseControl('ArrowDown')" @pointerleave="releaseControl('ArrowDown')" @pointercancel="releaseControl('ArrowDown')">↓</button>
              <span />
            </div>

            <div class="flex justify-center gap-1.5 lg:flex-col">
              <button type="button" class="pad w-20 text-xs" :class="{ 'pad-on': pressed.has('+') }" aria-label="확대" @pointerdown.prevent="pressControl('+')" @pointerup.prevent="releaseControl('+')" @pointerleave="releaseControl('+')" @pointercancel="releaseControl('+')">줌 +</button>
              <button type="button" class="pad w-20 text-xs" :class="{ 'pad-on': pressed.has('-') }" aria-label="축소" @pointerdown.prevent="pressControl('-')" @pointerup.prevent="releaseControl('-')" @pointerleave="releaseControl('-')" @pointercancel="releaseControl('-')">줌 −</button>
            </div>

            <div class="flex min-w-0 flex-col gap-2">
              <input
                v-model="newZoneName"
                placeholder="구역 이름 (예: 앞줄 좌측)"
                class="w-full rounded-lg border border-line bg-canvas px-3 py-2.5 text-sm text-fg placeholder:text-fg-muted focus:outline-none focus-visible:border-fg-muted"
                @keyup.enter="saveZone"
              />
              <button
                @click="saveZone"
                :disabled="saving"
                class="rounded-lg bg-fg px-4 py-2.5 text-sm font-semibold text-canvas transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
              >{{ saving ? '저장 중...' : '📍 이 위치 등록' }}</button>
            </div>
          </div>
          <p class="shrink-0 px-card pb-4 text-center text-[11px] text-fg-muted">
            방향키로 상하좌우, <span class="font-medium">+</span> / <span class="font-medium">−</span> 키로 줌을 조작합니다.
            누르고 있는 동안 움직이고 떼면 멈춥니다. (구역 이름 입력 중에는 동작하지 않습니다)
          </p>
        </div>

        <!-- 등록된 구역 -->
        <div class="flex min-h-0 flex-col rounded-card border border-line bg-card p-card shadow-card">
          <div class="mb-1 flex shrink-0 items-center justify-between">
            <span class="text-sm font-semibold text-fg">순찰 구역</span>
            <span class="rounded-full border border-line bg-canvas px-2 py-0.5 text-xs font-medium text-fg-muted">{{ zones.length }}개</span>
          </div>
          <p class="mb-3 shrink-0 text-[11px] text-fg-muted">
            위에서부터 이 순서대로 돌고 <span class="font-medium text-neutral-500 dark:text-neutral-400">마지막 구역에서 끝납니다</span>. 끌어서 순서를 바꿀 수 있고, 자리 영역이 없는 구역은 이동만 합니다.
          </p>

          <div v-if="!zones.length" class="flex min-h-0 flex-1 flex-col items-center justify-center gap-2 py-12 text-center text-sm text-fg-muted">
            <div class="text-2xl">📍</div>
            아직 등록된 구역이 없습니다.<br>카메라를 움직여 위치를 등록해보세요.
          </div>

          <div v-else class="min-h-0 flex-1 space-y-2 overflow-y-auto pr-1">
            <div
              v-for="(z, zi) in zones"
              :key="z.id"
              draggable="true"
              @dragstart="dragFrom = zi"
              @dragover.prevent="dragOver = zi"
              @dragend="dragFrom = null; dragOver = null"
              @drop.prevent="dropZone(zi)"
              @click="selectedZoneId = selectedZoneId === z.id ? null : z.id"
              class="group cursor-pointer rounded-lg border p-3 transition"
              :class="[
                selectedZoneId === z.id ? 'border-fg-muted bg-line/40' : 'border-line hover:border-fg-muted/50',
                dragFrom === zi ? 'opacity-40' : '',
                dragOver === zi && dragFrom !== null && dragFrom !== zi ? '!border-fg-muted border-dashed' : '',
              ]"
            >
              <div class="flex items-center gap-2">
                <span class="text-neutral-300 dark:text-neutral-700 cursor-grab select-none shrink-0" title="끌어서 순서 변경">⠿</span>
                <span class="w-5 shrink-0 text-[11px] tabular-nums text-fg-muted">{{ zi + 1 }}</span>
                <div class="flex-1 min-w-0">
                  <div class="truncate text-sm font-medium text-fg">{{ z.name }}</div>
                  <div class="text-[11px] tabular-nums text-fg-muted">
                    팬 {{ z.pan }} · 틸트 {{ z.tilt }} · 줌 {{ z.zoom }}
                    <span v-if="z.rois?.length" class="text-state-occupied"> · 자리 {{ z.rois.length }}개</span>
                    <span v-else class="text-neutral-400 dark:text-neutral-600"> · 이동만 (인식 안 함)</span>
                  </div>
                </div>
                <button
                  @click.stop="goto(z)"
                  class="shrink-0 rounded-lg border border-line px-2.5 py-1.5 text-xs font-medium text-fg-muted transition-colors hover:bg-line/40 hover:text-fg"
                >이동</button>
                <button
                  @click.stop="removeZone(z)"
                  title="구역 삭제"
                  class="shrink-0 px-1 text-fg-muted opacity-0 transition hover:text-state-alert group-hover:opacity-100"
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
                  class="flex-1 rounded-lg border border-line py-1.5 text-xs font-medium text-fg-muted transition-colors hover:bg-line/40 hover:text-fg disabled:opacity-50"
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

const SPEED = 100

const route = useRoute()
const placeId = route.params.id

// ── 로컬 샘플 데이터 ─────────────────────────────────────────────────────────

const mockPreviewImg = ref('')
let mockNextZoneId = 1

function buildMockZones() {
  return [
    { id: mockNextZoneId++, name: '앞줄 좌측', pan: 300, tilt: 100, zoom: 20, rois: [{ points: [] }] },
    { id: mockNextZoneId++, name: '앞줄 우측', pan: 1200, tilt: 100, zoom: 20, rois: [{ points: [] }] },
    { id: mockNextZoneId++, name: '뒷줄 전체', pan: 700, tilt: 250, zoom: 15, rois: [] },
  ]
}

const mockActive = ref(false)

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

function pressControl(key) {
  if (!place.value?.camera?.ip) return
  const normalized = normalizeKey(key)
  if (!KEY_MOVES[normalized] || pressed.value.has(normalized)) return
  pressed.value.add(normalized)
  sendPressedMove()
}

function releaseControl(key) {
  const normalized = normalizeKey(key)
  if (!pressed.value.delete(normalized)) return
  sendPressedMove()
}

function onKeyDown(e) {
  if (isTyping(e.target) || !place.value?.camera?.ip) return
  const key = normalizeKey(e.key)
  if (!KEY_MOVES[key]) return
  e.preventDefault()          // 방향키로 화면이 스크롤되지 않게
  pressControl(key)
}

function onKeyUp(e) {
  releaseControl(e.key)
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
    alert('자리 영역(ROI) 편집은 실제 카메라 연결 후 이용해주세요.')
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
