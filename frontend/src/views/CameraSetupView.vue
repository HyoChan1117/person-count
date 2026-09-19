<template>
  <div class="ds-root flex h-full flex-col overflow-hidden">

    <!-- Page header -->
    <header class="shrink-0 bg-canvas p-section pb-gutter">
      <div class="mx-auto flex w-full max-w-[1680px] items-end justify-between gap-section">
        <div class="min-w-0">
          <router-link to="/classrooms" class="text-sm text-fg-muted transition-colors hover:text-fg">← 목록</router-link>
          <div class="mt-1 flex items-center gap-2">
            <h1 class="text-3xl font-bold tracking-tight text-fg">카메라 설정</h1>
            <span v-if="mockActive" class="rounded-full border border-state-unknown/30 bg-state-unknown/10 px-2 py-0.5 text-xs font-semibold text-state-unknown">목데이터</span>
          </div>
          <p class="mt-1 text-lg text-fg-muted">{{ classroom?.name }}의 CCTV와 좌석 선을 설정합니다</p>
        </div>
        <div class="flex shrink-0 items-center gap-2">
        <button
          @click="toggleMock"
          class="rounded-lg border px-3 py-1.5 text-sm font-medium transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-fg-muted"
          :class="mockActive
            ? 'border-state-unknown/40 bg-state-unknown/10 text-state-unknown hover:bg-state-unknown/15'
            : 'border-line text-fg-muted hover:bg-line/40 hover:text-fg'"
        >{{ mockActive ? '목데이터 끄기' : '목데이터로 보기' }}</button>
        <router-link :to="`/dashboard/${classroomId}`" class="rounded-lg border border-line px-3 py-1.5 text-sm font-medium text-fg-muted transition-colors hover:bg-line/40 hover:text-fg">
          대시보드
        </router-link>
        </div>
      </div>
    </header>

    <ErrorNotice v-if="cStore.error" legacy class="mx-auto mt-gutter w-full max-w-[1680px] shrink-0" title="교실 정보를 불러오지 못했습니다" :message="cStore.error" @retry="cStore.fetchOne(classroomId)" />

    <!-- Main -->
    <div class="mx-auto grid min-h-0 w-full max-w-[1680px] flex-1 grid-cols-[18rem_minmax(0,1fr)] gap-gutter overflow-hidden bg-canvas p-gutter">

      <!-- Left: camera list -->
      <div class="flex min-h-0 flex-col overflow-hidden rounded-card border border-line bg-card shadow-card">
        <div class="border-b border-line p-4">
          <button @click="showAddForm = true" class="w-full rounded-lg bg-fg px-3 py-2.5 text-sm font-semibold text-canvas transition-opacity hover:opacity-90 focus-visible:outline focus-visible:outline-2 focus-visible:outline-fg-muted">
            + 카메라 추가
          </button>
        </div>
        <div class="flex-1 space-y-1 overflow-y-auto p-3">
          <div
            v-for="(cam, i) in cameras"
            :key="cam.camera_id"
            draggable="true"
            @dragstart="onDragStart(i)"
            @dragover.prevent="onDragOver(i)"
            @drop.prevent="onDrop"
            @dragend="onDragEnd"
            :class="['rounded-lg transition', dragOverIndex === i && dragIndex !== i ? 'ring-2 ring-fg-muted ring-offset-2 ring-offset-card' : '']"
          >
            <button
              @click="selectCamera(cam)"
              :class="['relative flex w-full items-start gap-3 rounded-lg px-3 py-2.5 text-left text-sm transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-fg-muted',
                selectedCam?.camera_id === cam.camera_id
                  ? 'bg-line/60 font-medium text-fg'
                  : 'text-fg-muted hover:bg-line/40 hover:text-fg']"
            >
              <span v-if="selectedCam?.camera_id === cam.camera_id" class="absolute inset-y-2 left-0 w-0.5 rounded-full bg-fg" />
              <span class="mt-1 cursor-grab select-none text-base leading-none text-fg-muted/40">≡</span>
              <span class="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-line bg-canvas text-fg-muted">
                <NavIcon name="camera" :size="17" />
              </span>
              <span class="flex-1 min-w-0">
                <span class="flex items-center gap-1.5">
                  <span class="h-1.5 w-1.5 shrink-0 rounded-full" :class="cam.rtsp_url ? 'bg-state-occupied' : 'bg-state-empty'" />
                  <span class="block font-medium truncate">{{ cam.name }}</span>
                </span>
                <span class="mt-0.5 block truncate font-mono text-xs font-normal text-fg-muted">{{ cam.ip_address || '미설정' }}</span>
                <span v-if="Object.keys(cam.seat_lines ?? {}).length" class="mt-1 block text-xs text-state-unknown">선 {{ Object.keys(cam.seat_lines).length }}개</span>
                <span v-if="cam.view_group" class="mt-1 block text-xs text-fg-muted">뷰 그룹 {{ cam.view_group }}</span>
              </span>
            </button>
          </div>
          <div v-if="!cameras.length" class="py-8 text-center text-sm text-fg-muted">
            카메라가 없습니다
          </div>
        </div>
      </div>

      <!-- Right: snapshot + seat line editor -->
      <div class="flex min-w-0 flex-col overflow-hidden rounded-card border border-line bg-card shadow-card">

        <!-- No camera selected -->
        <div v-if="!selectedCam" class="flex flex-1 items-center justify-center text-fg-muted">
          <div class="text-center">
            <div class="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-lg border border-line bg-card">
              <NavIcon name="camera" :size="24" />
            </div>
            <div class="text-sm">카메라를 선택하거나 추가하세요</div>
          </div>
        </div>

        <!-- Camera selected -->
        <template v-else>
          <!-- Toolbar -->
          <div class="flex shrink-0 flex-wrap items-center gap-3 border-b border-line bg-card px-card py-3">
            <div class="flex items-center gap-1.5">
              <span class="h-1.5 w-1.5 shrink-0 rounded-full" :class="frameImage ? 'bg-state-occupied' : 'bg-state-empty'" />
              <span class="text-sm font-semibold text-fg">{{ selectedCam.name }}</span>
              <button
                @click="showEditForm = true"
                class="ml-2 rounded-lg border border-line px-3 py-1.5 text-sm font-medium text-fg-muted transition-colors hover:bg-line/40 hover:text-fg"
              >수정</button>
            </div>

            <div class="ml-auto flex flex-wrap items-center gap-2">
              <!-- 좌석 선 모드 토글 -->
              <div class="mx-1 h-4 w-px bg-line" />
              <button
                v-if="frameImage"
                @click="seatRoiMode ? exitSeatRoiMode() : enterSeatRoiMode()"
                :class="['rounded-lg border px-3 py-1.5 text-sm font-medium transition-colors',
                  seatRoiMode
                    ? 'border-state-unknown bg-state-unknown text-canvas'
                    : 'border-state-unknown/30 text-state-unknown hover:bg-state-unknown/10']"
              >좌석 선{{ seatRoiMode ? ' 종료' : '' }}</button>

              <button
                v-if="bgHasReference"
                @click="runBgDetect"
                :disabled="detectingBg"
                class="rounded-lg border border-line px-3 py-1.5 text-sm font-medium text-fg-muted transition-colors hover:bg-line/40 hover:text-fg disabled:opacity-50"
                title="저장된 기준과 현재 프레임을 비교"
              >{{ detectingBg ? '분석 중..' : '배경 감지' }}</button>

              <button
                @click="captureSnapshot"
                :disabled="capturing"
                class="inline-flex items-center gap-1.5 rounded-lg border border-line px-3 py-1.5 text-sm font-medium text-fg-muted transition-colors hover:bg-line/40 hover:text-fg disabled:opacity-50"
              ><NavIcon name="camera" :size="15" />{{ capturing ? '캡처 중..' : '스냅샷' }}</button>
              <button @click="deleteCamera(selectedCam.camera_id)" class="rounded-md px-2 py-1 text-sm text-state-alert transition-colors hover:bg-state-alert/10">삭제</button>
            </div>
          </div>

          <!-- 좌석 선 설정 헤더 -->
          <div v-if="seatRoiMode && frameImage" class="flex shrink-0 flex-wrap items-center gap-3 border-b border-state-unknown/20 bg-state-unknown/10 px-card py-2">
            <span class="text-sm font-semibold text-state-unknown">좌석 선 설정</span>
            <span class="text-xs text-state-unknown/80">좌석 선택 → 앞쪽 선 2클릭(주황) → 뒤쪽 선 2클릭(초록) → 자동 완료</span>

            <!-- 좌석 ID 목록 -->
            <div class="flex flex-wrap gap-1">
              <button
                v-for="seatId in seatRoiCandidates"
                :key="seatId"
                @click="selectSeatId(seatId)"
                :class="['text-[10px] px-2 py-0.5 rounded-full border font-medium transition',
                  activeSeatId === seatId
                    ? 'bg-state-unknown text-canvas border-state-unknown'
                    : seatLines[seatId]
                    ? 'bg-state-occupied/15 text-state-occupied border-state-occupied/30'
                    : 'bg-card text-fg-muted border-line hover:border-state-unknown/50']"
              >{{ seatId }}{{ seatLines[seatId] ? ' ✓' : '' }}</button>
            </div>

            <!-- 좌석 ID가 없을 때 수동 입력 -->
            <template v-if="!seatRoiCandidates.length">
              <input
                v-model="manualSeatId"
                placeholder="좌석 번호 입력 (예: A1)"
                class="w-32 rounded border border-state-unknown/30 bg-card px-2 py-1 text-xs text-fg placeholder:text-fg-muted"
                @keydown.enter="selectSeatId(manualSeatId)"
              />
              <button
                @click="selectSeatId(manualSeatId)"
                :disabled="!manualSeatId.trim()"
                class="rounded bg-state-unknown px-2 py-1 text-xs text-canvas disabled:opacity-50"
              >선택</button>
            </template>

            <div class="ml-auto flex gap-2 items-center">
              <span v-if="activeSeatId" class="text-xs font-medium text-state-unknown">선택: {{ activeSeatId }}</span>
              <span v-if="seatLinePoints.length" class="text-[10px]" :class="seatLinePoints.length <= 2 ? 'text-orange-400' : 'text-emerald-400'">
                {{ seatLinePoints.length <= 2 ? `앞선 ${seatLinePoints.length}/2` : `뒷선 ${seatLinePoints.length - 2}/2` }}
              </span>
              <button
                v-if="seatLinePoints.length"
                @click="undoLastPoint"
                class="text-xs text-neutral-400 hover:text-neutral-200 border border-neutral-700 px-2 py-0.5 rounded"
              >↩</button>
              <button
                v-if="seatLinePoints.length >= 4"
                @click="commitSeatLine"
                class="text-xs text-white bg-orange-500 hover:bg-orange-600 px-2 py-0.5 rounded"
              >선 완료</button>
              <button
                v-if="activeSeatId && seatLines[activeSeatId]"
                @click="deleteSeatLine(activeSeatId)"
                class="text-xs text-red-400 hover:text-red-300 border border-red-500/30 px-2 py-0.5 rounded"
              >삭제</button>
              <button
                @click="saveSeatLines"
                :disabled="savingSeatLines || !Object.keys(seatLines).length"
                class="text-xs bg-emerald-600 text-white px-3 py-1 rounded-md hover:bg-emerald-500 disabled:opacity-50 transition font-medium"
              >{{ savingSeatLines ? '저장..' : '전체 저장' }}</button>
            </div>
          </div>

          <!-- Canvas area -->
          <div class="flex flex-1 items-start justify-center overflow-auto bg-canvas p-gutter" ref="canvasContainer">
            <div v-if="capturing" class="text-sm text-fg-muted">스냅샷 캡처 중..</div>
            <div v-else-if="captureError" class="text-sm text-state-alert">{{ captureError }}</div>
            <div v-else-if="!frameImage" class="text-center text-sm text-fg-muted">
              <div class="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-lg border border-line bg-card">
                <NavIcon name="camera" :size="24" />
              </div>
              <div>스냅샷 버튼을 눌러 프레임을 캡처하세요</div>
            </div>
            <canvas
              v-show="frameImage"
              ref="canvasRef"
              :width="canvasW"
              :height="canvasH"
              class="cursor-crosshair rounded-card border border-line shadow-xl"
              @click="onCanvasClick"
              @contextmenu.prevent="undoLastPoint"
              @mousemove="onCanvasMouseMove"
              @mouseleave="onCanvasMouseLeave"
            />
          </div>

          <!-- Instructions -->
          <div v-if="frameImage && seatRoiMode" class="flex shrink-0 gap-6 border-t border-state-unknown/20 bg-state-unknown/10 px-card py-2 text-xs text-state-unknown">
            <span v-if="!activeSeatId">좌석을 먼저 선택하세요</span>
            <template v-else-if="seatLinePoints.length < 2">
              <span class="text-orange-400 font-medium">① 앞쪽 선:</span>
              <span>시작점 클릭 → 끝점 클릭</span>
            </template>
            <template v-else-if="seatLinePoints.length < 4">
              <span class="text-emerald-400 font-medium">② 뒤쪽 선:</span>
              <span>시작점 클릭 → 끝점 클릭 (4번째 클릭 시 자동 저장)</span>
            </template>
            <span v-if="activeSeatId" class="font-semibold">현재: {{ activeSeatId }}</span>
          </div>

          <!-- 배경 차분 결과 -->
          <div
            v-if="bgResult"
            :class="['shrink-0 border-t px-4 py-2 text-xs flex items-center gap-4',
              bgResult.occupied ? 'bg-red-500/10 border-red-500/20 text-red-400' : 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400']"
          >
            <span class="font-bold text-sm">{{ bgResult.occupied ? '⚠ 사람 있음' : '✓ 빈 강의실' }}</span>
            <span>변화 비율: {{ (bgResult.change_ratio * 100).toFixed(2) }}%</span>
            <span class="text-neutral-500">(임계값 2% 기준)</span>
            <button @click="bgResult = null" class="ml-auto text-neutral-500 hover:text-neutral-300">✕</button>
          </div>
        </template>
      </div>
    </div>

    <!-- Add camera modal -->
    <Teleport to="body">
      <div
        v-if="showAddForm"
        class="fixed inset-0 bg-black/40 flex items-center justify-center z-50"
        @click.self="showAddForm = false"
      >
        <div class="ds-text w-96 rounded-card border border-line bg-card p-card shadow-xl">
          <h2 class="mb-4 text-xl font-semibold text-fg">카메라 추가</h2>
          <form @submit.prevent="addCamera">
            <label class="mb-1 block text-sm text-fg-muted">카메라 이름</label>
            <input v-model="form.name" required placeholder="예: CCTV 1" class="input w-full mb-3" />

            <label class="mb-1 block text-sm text-fg-muted">IP 주소</label>
            <input v-model="form.ip" placeholder="예: 192.168.0.100" class="input w-full mb-3" @input="autoFillRtsp" />

            <div class="flex gap-2 mb-3">
              <div class="flex-1">
                <label class="mb-1 block text-sm text-fg-muted">아이디</label>
                <input v-model="form.username" placeholder="예: admin" class="input w-full" @input="autoFillRtsp" />
              </div>
              <div class="flex-1">
                <label class="mb-1 block text-sm text-fg-muted">비밀번호</label>
                <input v-model="form.password" type="password" placeholder="비밀번호" class="input w-full" @input="autoFillRtsp" />
              </div>
            </div>

            <label class="mb-1 block text-sm text-fg-muted">RTSP URL <span class="text-fg-muted/70">(자동 생성)</span></label>
            <input v-model="form.rtsp_url" placeholder="rtsp://..." class="input w-full text-xs mb-3" />

            <label class="mb-1 block text-sm text-fg-muted">뷰 그룹 <span class="text-fg-muted/70">(같은 공간을 여러 카메라로 찍으면 동일한 이름 입력)</span></label>
            <input v-model="form.viewGroup" placeholder="예: A (선택사항)" class="input w-full mb-4" />

            <div class="flex gap-2">
              <button type="button" @click="showAddForm = false" class="flex-1 btn-ghost">취소</button>
              <button type="submit" class="flex-1 btn-primary">추가</button>
            </div>
          </form>
        </div>
      </div>
    </Teleport>

    <!-- Edit camera modal -->
    <Teleport to="body">
      <div
        v-if="showEditForm && selectedCam"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-6"
        @click.self="showEditForm = false"
      >
        <div class="ds-text w-full max-w-lg overflow-hidden rounded-card border border-line bg-card shadow-xl">
          <div class="border-b border-line px-card py-5">
            <p class="text-sm font-semibold text-fg-muted">카메라 정보</p>
            <h2 class="mt-1 text-2xl font-bold text-fg">{{ selectedCam.name }} 수정</h2>
          </div>
          <form class="space-y-4 p-card" @submit.prevent="saveCameraSettings">
            <div>
              <label class="mb-1 block text-sm font-medium text-fg-muted">IP 주소</label>
              <input v-model="editCameraForm.ip" placeholder="예: 192.168.0.100" class="input w-full" />
            </div>

            <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div>
                <label class="mb-1 block text-sm font-medium text-fg-muted">아이디</label>
                <input v-model="editCreds.username" placeholder="예: admin" class="input w-full" />
              </div>
              <div>
                <label class="mb-1 block text-sm font-medium text-fg-muted">비밀번호</label>
                <input v-model="editCreds.password" type="password" placeholder="비밀번호" class="input w-full" />
              </div>
            </div>

            <div>
              <label class="mb-1 block text-sm font-medium text-fg-muted">뷰 그룹</label>
              <input v-model="editingGroup" placeholder="예: A" class="input w-full" />
            </div>

            <div class="flex justify-end gap-2 border-t border-line pt-5">
              <button type="button" @click="showEditForm = false" class="btn-ghost">취소</button>
              <button type="submit" :disabled="savingCameraSettings" class="btn-primary">
                {{ savingCameraSettings ? '저장 중..' : '저장' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { useClassroomStore } from '@/stores/classroomStore.js'
import { useMockToggle } from '@/composables/useMockToggle'
import ErrorNotice from '@/components/ui/ErrorNotice.vue'
import NavIcon from '@/components/ui/NavIcon.vue'
import api from '@/api'

const SEAT_ROI_COLORS = ['#c7403d','#147b70','#9a6a0e','#0f766e','#5b6b82','#0369a1','#b45309','#4d7c0f']

const route = useRoute()
const cStore = useClassroomStore()

const classroomId = computed(() => Number(route.params.id))
const classroom = computed(() => cStore.current)

// 카메라가 없어도 UI를 확인할 수 있는 목데이터 모드
const mockCameraList = ref([
  {
    camera_id: 'MOCK1',
    name: '샘플 카메라 1',
    ip_address: '192.168.0.101',
    rtsp_url: 'rtsp://mock',
    view_group: 'A',
    seat_ids: ['1', '2', '3', '4'],
    seat_lines: {
      '1': [[200, 300], [350, 300], [210, 380], [340, 380]],
      '2': [[420, 300], [570, 300], [430, 380], [560, 380]],
    },
  },
  {
    camera_id: 'MOCK2',
    name: '샘플 카메라 2',
    ip_address: '192.168.0.102',
    rtsp_url: 'rtsp://mock',
    view_group: 'A',
    seat_ids: ['5', '6'],
    seat_lines: {},
  },
])

function resetCameraSelection() {
  selectedCam.value = null
  frameImage.value = null
}

const { mockActive, toggleMock } = useMockToggle(
  () => {
    resetCameraSelection()
    if (mockCameraList.value.length) selectCamera(mockCameraList.value[0])
  },
  resetCameraSelection,
)

const cameras = computed(() => (mockActive.value ? mockCameraList.value : (classroom.value?.cameras ?? [])))

// RTSP URL helpers
function parseRtspCredentials(url) {
  if (!url) return { username: '', password: '' }
  const m = url.match(/^rtsp:\/\/([^:@]+):?([^@]*)@/)
  if (m) return { username: decodeURIComponent(m[1]), password: decodeURIComponent(m[2]) }
  return { username: '', password: '' }
}

function injectCredentials(url, username, password) {
  const bare = url.replace(/^(rtsp:\/\/)[^@]+@/, '$1')
  if (!username) return bare
  const auth = `${encodeURIComponent(username)}:${encodeURIComponent(password || '')}@`
  return bare.replace(/^rtsp:\/\//, `rtsp://${auth}`)
}

function replaceRtspHost(url, ip) {
  if (!ip) return url
  if (!url) return `rtsp://${ip}:554/stream1`
  return url.replace(/^(rtsp:\/\/(?:[^@/]+@)?)([^/:]+)(.*)$/i, `$1${ip}$3`)
}

// Camera selection
const selectedCam = ref(null)
const showEditForm = ref(false)
const editCameraForm = ref({ ip: '' })
const editingGroup = ref('')
const savingGroup = ref(false)
const editCreds = ref({ username: '', password: '' })
const savingCreds = ref(false)
const savingCameraSettings = ref(false)

// 배경 차분 상태
const bgHasReference = ref(false)
const savingBg = ref(false)
const detectingBg = ref(false)
const bgResult = ref(null)

// 좌석 ROI 상태
const seatRoiMode = ref(false)
const activeSeatId = ref(null)
const seatLines = ref({})          // {"A1": [[x1,y1], [x2,y2]]} line in camera frame
const seatLinePoints = ref([])     // 현재 그리는 중인 선 포인트 목록
const mousePos = ref(null)         // rubber band 표시용 마우스 위치
const manualSeatId = ref('')
const savingSeatLines = ref(false)

const seatRoiCandidates = computed(() => selectedCam.value?.seat_ids ?? [])

async function fetchBgStatus(cameraId) {
  try {
    const { data } = await api.get(`/analysis/${classroomId.value}/bg-status/${cameraId}`)
    bgHasReference.value = data.has_reference
  } catch {
    bgHasReference.value = false
  }
}

async function uploadBgReference(e) {
  const file = e.target.files?.[0]
  if (!file || !selectedCam.value) return
  e.target.value = ''
  if (mockActive.value) {
    bgHasReference.value = true
    bgResult.value = null
    alert('(목데이터) 빈 교실 기준 이미지가 저장되었습니다.')
    return
  }
  savingBg.value = true
  try {
    const form = new FormData()
    form.append('file', file)
    const { data } = await api.post(
      `/analysis/${classroomId.value}/bg-reference-upload/${selectedCam.value.camera_id}`,
      form,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    )
    bgHasReference.value = true
    bgResult.value = null
    if (data.image) {
      frameImage.value = data.image
      const img = new Image()
      img.onload = () => { snapshotImg.value = img; nextTick(drawCanvas) }
      img.src = `data:image/jpeg;base64,${data.image}`
    }
    alert('빈 교실 기준 이미지가 저장되었습니다.')
  } catch (err) {
    alert('업로드 실패: ' + (err.response?.data?.detail ?? err.message))
  } finally {
    savingBg.value = false
  }
}

async function saveBgReference() {
  if (!selectedCam.value) return
  if (mockActive.value) {
    bgHasReference.value = true
    bgResult.value = null
    alert('(목데이터) 빈 교실 기준이 저장되었습니다.')
    return
  }
  savingBg.value = true
  try {
    await api.post(`/analysis/${classroomId.value}/bg-reference/${selectedCam.value.camera_id}`)
    bgHasReference.value = true
    bgResult.value = null
    alert('빈 교실 기준이 저장되었습니다.')
  } catch (e) {
    alert('저장 실패: ' + (e.response?.data?.detail ?? e.message))
  } finally {
    savingBg.value = false
  }
}

async function runBgDetect() {
  if (!selectedCam.value) return
  if (mockActive.value) {
    detectingBg.value = true
    bgResult.value = null
    await new Promise(r => setTimeout(r, 400))
    const occupied = Math.random() > 0.5
    bgResult.value = { occupied, change_ratio: occupied ? 0.03 + Math.random() * 0.08 : Math.random() * 0.015 }
    detectingBg.value = false
    return
  }
  detectingBg.value = true
  bgResult.value = null
  try {
    const { data } = await api.get(`/analysis/${classroomId.value}/bg-detect/${selectedCam.value.camera_id}`)
    bgResult.value = data
    if (data.image) {
      frameImage.value = data.image
      const img = new Image()
      img.onload = () => { snapshotImg.value = img; nextTick(drawCanvas) }
      img.src = `data:image/jpeg;base64,${data.image}`
    }
  } catch (e) {
    alert('분석 실패: ' + (e.response?.data?.detail ?? e.message))
  } finally {
    detectingBg.value = false
  }
}

function selectCamera(cam) {
  selectedCam.value = cam
  editCameraForm.value = { ip: cam.ip_address ?? '' }
  editingGroup.value = cam.view_group ?? ''
  const creds = parseRtspCredentials(cam.rtsp_url ?? '')
  editCreds.value = { username: creds.username, password: creds.password }
  seatLines.value = cam.seat_lines ? JSON.parse(JSON.stringify(cam.seat_lines)) : {}
  frameImage.value = null
  captureError.value = null
  bgResult.value = null
  seatRoiMode.value = false
  activeSeatId.value = null
  if (mockActive.value) {
    bgHasReference.value = false
  } else {
    fetchBgStatus(cam.camera_id)
  }
  captureSnapshot()
}

async function saveCameraSettings() {
  if (!selectedCam.value) return
  savingCameraSettings.value = true
  try {
    const ip = editCameraForm.value.ip.trim()
    const rtspWithHost = replaceRtspHost(selectedCam.value.rtsp_url ?? '', ip)
    const rtspUrl = injectCredentials(rtspWithHost, editCreds.value.username, editCreds.value.password)
    const patch = {
      ip_address: ip,
      rtsp_url: rtspUrl,
      view_group: editingGroup.value.trim() || null,
    }

    if (mockActive.value) {
      const cam = mockCameraList.value.find(c => c.camera_id === selectedCam.value.camera_id)
      if (cam) Object.assign(cam, patch)
      selectedCam.value = cam
      showEditForm.value = false
      return
    }

    const updated = cameras.value.map(c =>
      c.camera_id === selectedCam.value.camera_id ? { ...c, ...patch } : c
    )
    await cStore.saveClassroom(classroomId.value, { cameras: updated })
    selectedCam.value = cameras.value.find(c => c.camera_id === selectedCam.value.camera_id)
    showEditForm.value = false
  } catch (e) {
    alert('저장 실패: ' + (e.response?.data?.detail ?? e.message))
  } finally {
    savingCameraSettings.value = false
  }
}

async function applyCredentials() {
  if (!selectedCam.value?.rtsp_url) return
  savingCreds.value = true
  try {
    const newUrl = injectCredentials(
      selectedCam.value.rtsp_url,
      editCreds.value.username,
      editCreds.value.password
    )
    if (mockActive.value) {
      const cam = mockCameraList.value.find(c => c.camera_id === selectedCam.value.camera_id)
      if (cam) cam.rtsp_url = newUrl
      selectedCam.value = cam
      return
    }
    const updated = cameras.value.map(c =>
      c.camera_id === selectedCam.value.camera_id ? { ...c, rtsp_url: newUrl } : c
    )
    await cStore.saveClassroom(classroomId.value, { cameras: updated })
    selectedCam.value = cameras.value.find(c => c.camera_id === selectedCam.value.camera_id)
  } catch (e) {
    alert('저장 실패: ' + (e.response?.data?.detail ?? e.message))
  } finally {
    savingCreds.value = false
  }
}

async function saveViewGroup() {
  if (!selectedCam.value) return
  savingGroup.value = true
  try {
    if (mockActive.value) {
      const cam = mockCameraList.value.find(c => c.camera_id === selectedCam.value.camera_id)
      if (cam) cam.view_group = editingGroup.value.trim() || null
      selectedCam.value = cam
      return
    }
    const updated = cameras.value.map(c =>
      c.camera_id === selectedCam.value.camera_id
        ? { ...c, view_group: editingGroup.value.trim() || null }
        : c
    )
    await cStore.saveClassroom(classroomId.value, { cameras: updated })
    selectedCam.value = cameras.value.find(c => c.camera_id === selectedCam.value.camera_id)
  } catch (e) {
    alert('그룹 저장 실패: ' + (e.response?.data?.detail ?? e.message))
  } finally {
    savingGroup.value = false
  }
}

// Snapshot
const frameImage = ref(null)
const frameW = ref(1)
const frameH = ref(1)
const canvasW = ref(640)
const canvasH = ref(480)
const canvasRef = ref(null)
const canvasContainer = ref(null)
const capturing = ref(false)
const captureError = ref(null)
const snapshotImg = ref(null)

// 목데이터 모드에서 사용할 가짜 프레임(강의실 배치를 흉내낸 캔버스)을 생성
async function loadMockFrame() {
  capturing.value = true
  captureError.value = null
  const w = 960, h = 540
  frameW.value = w
  frameH.value = h

  await nextTick()
  const el = canvasContainer.value
  const maxW = el ? el.offsetWidth - 32 : 900
  const maxH = el ? el.offsetHeight - 32 : 600
  const scale = Math.min(maxW / w, maxH / h, 1)
  canvasW.value = Math.round(w * scale)
  canvasH.value = Math.round(h * scale)

  const off = document.createElement('canvas')
  off.width = w
  off.height = h
  const octx = off.getContext('2d')
  octx.fillStyle = '#3f3f46'
  octx.fillRect(0, 0, w, h)
  octx.fillStyle = '#27272a'
  for (let y = 60; y < h - 40; y += 90) {
    for (let x = 60; x < w - 40; x += 140) {
      octx.fillRect(x, y, 100, 50)
    }
  }
  octx.fillStyle = 'rgba(255,255,255,0.3)'
  octx.font = 'bold 20px sans-serif'
  octx.fillText('🧪 MOCK CAMERA FEED', 24, 34)

  const dataUrl = off.toDataURL('image/jpeg', 0.85)
  frameImage.value = dataUrl.split(',')[1]
  const img = new Image()
  img.onload = () => {
    snapshotImg.value = img
    capturing.value = false
    nextTick(drawCanvas)
  }
  img.src = dataUrl
}

async function captureSnapshot() {
  if (mockActive.value) {
    await loadMockFrame()
    return
  }
  if (!selectedCam.value?.rtsp_url) {
    captureError.value = 'RTSP URL이 없습니다'
    return
  }
  capturing.value = true
  captureError.value = null
  try {
    const { data } = await api.get(`/analysis/${classroomId.value}/frame/${selectedCam.value.camera_id}`)
    frameW.value = data.width
    frameH.value = data.height

    await nextTick()
    const el = canvasContainer.value
    const maxW = el ? el.offsetWidth - 32 : 900
    const maxH = el ? el.offsetHeight - 32 : 600
    const scale = Math.min(maxW / data.width, maxH / data.height, 1)
    canvasW.value = Math.round(data.width * scale)
    canvasH.value = Math.round(data.height * scale)

    frameImage.value = data.image

    const img = new Image()
    img.onload = () => {
      snapshotImg.value = img
      nextTick(drawCanvas)
    }
    img.src = `data:image/jpeg;base64,${data.image}`
  } catch (e) {
    captureError.value = e.response?.data?.detail ?? '캡처 실패'
  } finally {
    capturing.value = false
  }
}

function drawCanvas() {
  const canvas = canvasRef.value
  const img = snapshotImg.value
  if (!canvas || !img) return
  const ctx = canvas.getContext('2d')
  const scale = canvasW.value / frameW.value

  ctx.clearRect(0, 0, canvasW.value, canvasH.value)
  ctx.drawImage(img, 0, 0, canvasW.value, canvasH.value)

  // 좌석 선 그리기
  Object.keys(seatLines.value).forEach((seatId, i) => {
    const poly = seatLines.value[seatId]
    if (!poly || poly.length < 2) return
    const color = SEAT_ROI_COLORS[i % SEAT_ROI_COLORS.length]
    const isActive = seatId === activeSeatId.value
    const scaled = poly.map(([x, y]) => [x * scale, y * scale])
    ctx.save()
    // 앞쪽 선 (주황)
    ctx.beginPath()
    ctx.moveTo(scaled[0][0], scaled[0][1])
    ctx.lineTo(scaled[1][0], scaled[1][1])
    ctx.strokeStyle = color
    ctx.lineWidth = isActive ? 4 : 3
    ctx.setLineDash(isActive ? [6, 3] : [])
    ctx.stroke()
    ctx.setLineDash([])
    // 뒤쪽 선 (초록) — 4점 이상일 때만
    if (scaled.length >= 4) {
      ctx.beginPath()
      ctx.moveTo(scaled[2][0], scaled[2][1])
      ctx.lineTo(scaled[3][0], scaled[3][1])
      ctx.strokeStyle = '#22c55e'
      ctx.lineWidth = isActive ? 4 : 3
      ctx.setLineDash(isActive ? [6, 3] : [])
      ctx.stroke()
      ctx.setLineDash([])
    }
    // 점 표시
    scaled.slice(0, poly.length >= 4 ? 4 : 2).forEach(([px, py], pi) => {
      ctx.beginPath()
      ctx.arc(px, py, 5, 0, Math.PI * 2)
      ctx.fillStyle = pi < 2 ? color : '#22c55e'
      ctx.fill()
      ctx.strokeStyle = '#fff'
      ctx.lineWidth = 1.5
      ctx.stroke()
    })
    // 라벨
    const allPts = scaled.slice(0, poly.length >= 4 ? 4 : 2)
    const minX = Math.min(...allPts.map(p => p[0]))
    const minY = Math.min(...allPts.map(p => p[1]))
    ctx.font = 'bold 11px sans-serif'
    const tw = ctx.measureText(seatId).width
    ctx.fillStyle = color
    ctx.fillRect(minX, minY, tw + 6, 16)
    ctx.fillStyle = '#fff'
    ctx.textAlign = 'left'
    ctx.textBaseline = 'top'
    ctx.fillText(seatId, minX + 3, minY + 2)
    ctx.restore()
  })

  // 현재 그리는 중인 좌석 선 미리보기
  if (seatRoiMode.value && seatLinePoints.value.length) {
    const pts = seatLinePoints.value
    ctx.save()
    // 앞쪽 선 (주황, 점 0-1)
    if (pts.length >= 1) {
      const s0 = [pts[0].x * scale, pts[0].y * scale]
      if (pts.length >= 2) {
        const s1 = [pts[1].x * scale, pts[1].y * scale]
        ctx.strokeStyle = '#f97316'
        ctx.lineWidth = 2
        ctx.setLineDash([5, 3])
        ctx.beginPath()
        ctx.moveTo(s0[0], s0[1])
        ctx.lineTo(s1[0], s1[1])
        ctx.stroke()
        ctx.setLineDash([])
      }
      ;[s0].forEach(([px, py]) => {
        ctx.beginPath(); ctx.arc(px, py, 5, 0, Math.PI * 2)
        ctx.fillStyle = '#ef4444'; ctx.fill()
        ctx.strokeStyle = '#fff'; ctx.lineWidth = 1.5; ctx.stroke()
      })
      if (pts.length >= 2) {
        const s1 = [pts[1].x * scale, pts[1].y * scale]
        ctx.beginPath(); ctx.arc(s1[0], s1[1], 5, 0, Math.PI * 2)
        ctx.fillStyle = '#f97316'; ctx.fill()
        ctx.strokeStyle = '#fff'; ctx.lineWidth = 1.5; ctx.stroke()
      }
    }
    // 뒤쪽 선 (초록, 점 2-3)
    if (pts.length >= 3) {
      const s2 = [pts[2].x * scale, pts[2].y * scale]
      if (pts.length >= 4) {
        const s3 = [pts[3].x * scale, pts[3].y * scale]
        ctx.strokeStyle = '#22c55e'
        ctx.lineWidth = 2
        ctx.setLineDash([5, 3])
        ctx.beginPath()
        ctx.moveTo(s2[0], s2[1])
        ctx.lineTo(s3[0], s3[1])
        ctx.stroke()
        ctx.setLineDash([])
      }
      ;[[pts[2].x * scale, pts[2].y * scale]].forEach(([px, py]) => {
        ctx.beginPath(); ctx.arc(px, py, 5, 0, Math.PI * 2)
        ctx.fillStyle = '#16a34a'; ctx.fill()
        ctx.strokeStyle = '#fff'; ctx.lineWidth = 1.5; ctx.stroke()
      })
    }
    ctx.restore()
  }

  // Rubber band: 다음 클릭 대기 중 마우스 위치 미리보기
  if (seatRoiMode.value && mousePos.value &&
      (seatLinePoints.value.length === 1 || seatLinePoints.value.length === 3)) {
    const last = seatLinePoints.value[seatLinePoints.value.length - 1]
    const isSecondLine = seatLinePoints.value.length === 3
    ctx.save()
    ctx.strokeStyle = isSecondLine ? '#22c55e' : '#f97316'
    ctx.lineWidth = 1
    ctx.setLineDash([4, 3])
    ctx.globalAlpha = 0.5
    ctx.beginPath()
    ctx.moveTo(last.x * scale, last.y * scale)
    ctx.lineTo(mousePos.value.x, mousePos.value.y)
    ctx.stroke()
    ctx.restore()
  }
}

function onCanvasClick(e) {
  const rect = canvasRef.value.getBoundingClientRect()
  const scale = canvasW.value / frameW.value
  const cx = e.clientX - rect.left
  const cy = e.clientY - rect.top
  if (!seatRoiMode.value || !activeSeatId.value) return
  seatLinePoints.value.push({ x: Math.round(cx / scale), y: Math.round(cy / scale) })
  if (seatLinePoints.value.length >= 4) commitSeatLine()
  drawCanvas()
}

function onCanvasMouseMove(e) {
  if (!seatRoiMode.value || !seatLinePoints.value.length) {
    if (mousePos.value) { mousePos.value = null; drawCanvas() }
    return
  }
  const rect = canvasRef.value.getBoundingClientRect()
  mousePos.value = { x: e.clientX - rect.left, y: e.clientY - rect.top }
  drawCanvas()
}

function onCanvasMouseLeave() {
  if (mousePos.value) { mousePos.value = null; drawCanvas() }
}

function undoLastPoint() {
  seatLinePoints.value.pop()
  drawCanvas()
}

function selectSeatId(id) {
  // 다른 좌석으로 이동 시 선 2개(4점)가 완성된 경우만 저장
  if (activeSeatId.value && activeSeatId.value !== id && seatLinePoints.value.length >= 4) {
    seatLines.value[activeSeatId.value] = seatLinePoints.value.slice(0, 4).map(p => [p.x, p.y])
  }
  seatLinePoints.value = []
  mousePos.value = null
  activeSeatId.value = id
  drawCanvas()
}

function commitSeatLine() {
  if (seatLinePoints.value.length < 4 || !activeSeatId.value) return
  seatLines.value[activeSeatId.value] = seatLinePoints.value.slice(0, 4).map(p => [p.x, p.y])
  seatLinePoints.value = []
  mousePos.value = null
  // 다음 좌석으로 자동 이동
  const candidates = seatRoiCandidates.value
  if (candidates.length) {
    const idx = candidates.indexOf(activeSeatId.value)
    if (idx >= 0 && idx + 1 < candidates.length) activeSeatId.value = candidates[idx + 1]
  }
  drawCanvas()
}

// Seat ROI

function enterSeatRoiMode() {
  seatRoiMode.value = true
  activeSeatId.value = seatRoiCandidates.value[0] ?? null
  seatLinePoints.value = []
  mousePos.value = null
  drawCanvas()
}

function exitSeatRoiMode() {
  seatRoiMode.value = false
  activeSeatId.value = null
  seatLinePoints.value = []
  mousePos.value = null
  drawCanvas()
}

function deleteSeatLine(seatId) {
  delete seatLines.value[seatId]
  drawCanvas()
}

async function saveSeatLines() {
  if (!selectedCam.value) return
  if (mockActive.value) {
    const cam = mockCameraList.value.find(c => c.camera_id === selectedCam.value.camera_id)
    if (cam) cam.seat_lines = JSON.parse(JSON.stringify(seatLines.value))
    return
  }
  savingSeatLines.value = true
  try {
    await api.post(`/analysis/${classroomId.value}/seat-lines/${selectedCam.value.camera_id}`, {
      seat_lines: seatLines.value,
    })
    const cam = cameras.value.find(c => c.camera_id === selectedCam.value.camera_id)
    if (cam) cam.seat_lines = JSON.parse(JSON.stringify(seatLines.value))
  } catch (e) {
    alert('좌석 선 저장 실패: ' + (e.response?.data?.detail ?? e.message))
  } finally {
    savingSeatLines.value = false
  }
}

// Add / delete camera
const showAddForm = ref(false)
const form = ref({ name: '', ip: '', username: '', password: '', rtsp_url: '', viewGroup: '' })

function autoFillRtsp() {
  if (!form.value.ip) return
  const auth = form.value.username
    ? `${encodeURIComponent(form.value.username)}:${encodeURIComponent(form.value.password || '')}@`
    : ''
  form.value.rtsp_url = `rtsp://${auth}${form.value.ip}:554/stream1`
}

async function addCamera() {
  const newCam = {
    camera_id: 'C' + Date.now().toString(36).toUpperCase(),
    name: form.value.name,
    ip_address: form.value.ip,
    rtsp_url: form.value.rtsp_url,
    roi_polygon: [],
    seat_lines: {},
    seat_ids: [],
    view_group: form.value.viewGroup.trim() || null,
  }
  if (mockActive.value) {
    mockCameraList.value.push(newCam)
    showAddForm.value = false
    form.value = { name: '', ip: '', username: '', password: '', rtsp_url: '', viewGroup: '' }
    selectCamera(mockCameraList.value[mockCameraList.value.length - 1])
    return
  }
  if (!classroom.value) return
  const updated = [...cameras.value, newCam]
  await cStore.saveClassroom(classroomId.value, { cameras: updated })
  showAddForm.value = false
  form.value = { name: '', ip: '', username: '', password: '', rtsp_url: '', viewGroup: '' }
  selectCamera(cameras.value[cameras.value.length - 1])
}

async function deleteCamera(cameraId) {
  if (!confirm('이 카메라를 삭제하시겠습니까?')) return
  if (mockActive.value) {
    mockCameraList.value = mockCameraList.value.filter(c => c.camera_id !== cameraId)
    selectedCam.value = null
    frameImage.value = null
    return
  }
  const updated = cameras.value.filter(c => c.camera_id !== cameraId)
  await cStore.saveClassroom(classroomId.value, { cameras: updated })
  selectedCam.value = null
  frameImage.value = null
}

// Camera reorder
const dragIndex = ref(null)
const dragOverIndex = ref(null)

function onDragStart(i) { dragIndex.value = i }
function onDragOver(i) { dragOverIndex.value = i }
function onDragEnd() { dragIndex.value = null; dragOverIndex.value = null }

async function onDrop() {
  const from = dragIndex.value
  const to = dragOverIndex.value
  if (from === null || to === null || from === to) return onDragEnd()

  const reordered = [...cameras.value]
  reordered.splice(to, 0, reordered.splice(from, 1)[0])
  if (mockActive.value) {
    mockCameraList.value = reordered
  } else {
    await cStore.saveClassroom(classroomId.value, { cameras: reordered })
  }
  onDragEnd()
}

// Init
onMounted(() => cStore.fetchOne(classroomId.value))
</script>

<style scoped>
.input {
  @apply rounded-lg border border-line bg-canvas px-3 py-2 text-sm text-fg placeholder:text-fg-muted focus:outline-none focus-visible:border-fg-muted;
}
.btn-primary {
  @apply rounded-lg bg-fg px-4 py-2 text-sm font-semibold text-canvas transition-opacity hover:opacity-90;
}
.btn-ghost {
  @apply rounded-lg border border-line px-4 py-2 text-sm font-medium text-fg-muted transition-colors hover:bg-line/40 hover:text-fg;
}
</style>
