<template>
  <div class="h-full overflow-y-auto bg-neutral-50 dark:bg-neutral-950 p-6 lg:p-8">
    <div class="max-w-6xl mx-auto">

      <!-- 헤더 -->
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
        <div>
          <router-link to="/face" class="inline-flex items-center gap-1 text-xs text-neutral-400 dark:text-neutral-600 hover:text-neutral-600 dark:hover:text-neutral-300 transition mb-2">
            ← 얼굴 인식
          </router-link>
          <div class="flex items-center gap-2">
            <h1 class="text-2xl font-bold text-neutral-900 dark:text-neutral-50 tracking-tight">인물 등록</h1>
            <span v-if="mockActive" class="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-amber-100 dark:bg-amber-500/15 text-amber-700 dark:text-amber-400 border border-amber-200 dark:border-amber-500/30">목데이터</span>
          </div>
          <p class="text-sm text-neutral-500 dark:text-neutral-400 mt-0.5">얼굴을 등록해두면 순찰 중 허가된 사람인지 구분합니다</p>
        </div>

        <div class="flex items-center gap-2 shrink-0">
          <button
            @click="toggleMock"
            class="text-xs px-3 py-2 rounded-lg transition font-medium border"
            :class="mockActive
              ? 'bg-amber-500 text-white border-amber-500 hover:bg-amber-600'
              : 'bg-white dark:bg-neutral-900 border-neutral-200 dark:border-neutral-800 text-neutral-600 dark:text-neutral-300 hover:border-neutral-300 dark:hover:border-neutral-700'"
          >{{ mockActive ? '🧪 목데이터 끄기' : '🧪 목데이터로 보기' }}</button>
          <button
            @click="openForm('recognize')"
            class="inline-flex items-center gap-1.5 bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 text-neutral-700 dark:text-neutral-300 text-sm font-medium px-4 py-2 rounded-lg hover:bg-neutral-50 dark:hover:bg-neutral-800 transition"
          >인식 테스트</button>
          <button
            @click="openForm('enroll')"
            class="inline-flex items-center gap-1.5 bg-violet-600 text-white text-sm font-medium px-4 py-2 rounded-lg hover:bg-violet-700 transition"
          >+ 인물 등록</button>
        </div>
      </div>

      <div v-if="loading" class="text-center py-12 text-neutral-400 dark:text-neutral-600">불러오는 중...</div>

      <ErrorNotice v-else-if="loadError" legacy class="my-6" title="인물 목록을 불러오지 못했습니다" :message="loadError" @retry="retryPeople" />

      <div v-else-if="!people.length" class="flex flex-col items-center justify-center py-24 text-neutral-400 dark:text-neutral-600 gap-3 text-center">
        <div class="w-14 h-14 rounded-2xl bg-neutral-100 dark:bg-neutral-800 flex items-center justify-center text-2xl">👤</div>
        <p class="text-sm">등록된 인물이 없습니다.<br>사진을 올려 등록해보세요.</p>
      </div>

      <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div
          v-for="p in people"
          :key="p.id"
          class="bg-white dark:bg-neutral-900 rounded-2xl border border-neutral-200 dark:border-neutral-800 shadow-sm overflow-hidden group"
        >
          <BlurredImage :src="mockActive ? p.photoUrl : `/api/face/people/${p.id}/photo`" :alt="`${p.name} 등록 사진`" :rounded="false" class="w-full aspect-[4/3]" />
          <div class="p-4">
            <div class="flex items-start justify-between gap-2 mb-2">
              <div class="min-w-0">
                <div class="font-semibold text-neutral-800 dark:text-neutral-100 truncate">{{ p.name }}</div>
                <div class="text-[11px] text-neutral-400 dark:text-neutral-600">사진 {{ p.samples }}장 · {{ p.enrolled_at?.slice(0, 10) }}</div>
              </div>
              <button
                @click="removePerson(p)"
                title="삭제"
                class="text-neutral-300 dark:text-neutral-700 hover:text-red-400 opacity-0 group-hover:opacity-100 transition shrink-0"
              >✕</button>
            </div>

            <button
              @click="toggleAuthorized(p)"
              class="w-full text-xs font-medium py-1.5 rounded-lg transition"
              :class="p.authorized
                ? 'bg-emerald-50 text-emerald-700 hover:bg-emerald-100'
                : 'bg-red-50 text-red-600 hover:bg-red-100'"
            >{{ p.authorized ? '✓ 허가됨' : '✕ 미허가' }}</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 등록 모달 -->
    <div v-if="showForm" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4" @click.self="showForm = false">
      <div class="bg-white dark:bg-neutral-900 rounded-2xl p-6 w-96 shadow-xl">
        <h2 class="font-bold text-neutral-800 dark:text-neutral-100 mb-4">{{ purpose === 'enroll' ? '인물 등록' : '인식 테스트' }}</h2>

        <template v-if="purpose === 'enroll'">
          <label class="block text-sm text-neutral-600 dark:text-neutral-400 mb-1">이름</label>
          <input v-model="form.name" placeholder="예: 김민석" class="input w-full mb-4" />
        </template>
        <p v-else class="text-xs text-neutral-500 dark:text-neutral-400 mb-4">
          촬영한 얼굴이 등록된 인물과 얼마나 일치하는지 확인합니다. 등록되지는 않습니다.
        </p>

        <!-- 촬영 / 업로드 선택 -->
        <div class="flex gap-1.5 mb-3">
          <button type="button" @click="setMode('webcam')" class="tab" :class="{ 'tab-on': mode === 'webcam' }">📷 웹캠 촬영</button>
          <button type="button" @click="setMode('upload')" class="tab" :class="{ 'tab-on': mode === 'upload' }">사진 업로드</button>
        </div>

        <template v-if="mode === 'webcam'">
          <div class="rounded-xl overflow-hidden bg-neutral-900 mb-2">
            <!-- 미리보기는 거울처럼 보이게 뒤집고, 저장되는 사진은 원본 그대로 -->
            <video ref="videoRef" autoplay playsinline muted class="w-full aspect-video object-cover -scale-x-100" />
          </div>

          <div v-if="camError" class="mb-3 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700">
            {{ camError }}
          </div>

          <button
            type="button"
            @click="capture"
            :disabled="!streaming"
            class="w-full bg-neutral-800 text-white text-sm font-medium py-2 rounded-lg hover:bg-neutral-900 transition disabled:opacity-50 mb-2"
          >촬영</button>

          <div v-if="shots.length" class="flex gap-1.5 flex-wrap mb-2">
            <div v-for="(s, i) in shots" :key="s.url" class="relative">
              <BlurredImage :src="s.url" alt="촬영한 사진" class="w-14 h-14 border border-neutral-200 dark:border-neutral-800" />
              <button
                type="button"
                @click="removeShot(i)"
                class="absolute -top-1.5 -right-1.5 w-5 h-5 rounded-full bg-neutral-800 text-white text-[10px] flex items-center justify-center hover:bg-red-500 transition"
              >✕</button>
            </div>
          </div>

          <p class="text-[11px] text-neutral-400 dark:text-neutral-600 mb-4">
            정면을 보고 3장 정도 촬영해주세요. 고개 각도를 조금씩 바꾸면 인식률이 올라갑니다.
          </p>
        </template>

        <template v-else>
          <input type="file" accept="image/*" multiple @change="onFiles" class="w-full text-sm mb-1" />
          <p class="text-[11px] text-neutral-400 dark:text-neutral-600 mb-4">
            여러 장을 올리면 평균을 내어 더 정확해집니다. 각 사진에서 가장 큰 얼굴을 사용합니다.
          </p>
        </template>

        <div v-if="error" class="mb-3 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700">
          {{ error }}
        </div>

        <!-- 인식 테스트 결과 -->
        <div v-if="matchResult" class="mb-3 space-y-1.5">
          <div v-if="!matchResult.faces.length" class="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-700">
            얼굴을 찾지 못했습니다. 정면으로 다시 촬영해보세요.
          </div>
          <div
            v-for="(f, i) in matchResult.faces"
            :key="i"
            class="rounded-lg border px-3 py-2 text-xs"
            :class="f.name
              ? (f.authorized ? 'border-emerald-200 bg-emerald-50 text-emerald-700' : 'border-red-200 bg-red-50 text-red-700')
              : 'border-neutral-200 dark:border-neutral-800 bg-neutral-50 dark:bg-neutral-950 text-neutral-600 dark:text-neutral-400'"
          >
            <span class="font-semibold">{{ f.name ?? '미등록 인물' }}</span>
            <span v-if="f.name"> · {{ f.authorized ? '허가됨' : '미허가' }}</span>
            <span class="tabular-nums"> · 유사도 {{ f.score }}</span>
            <span class="opacity-70"> (기준 {{ matchResult.threshold }})</span>
          </div>
        </div>

        <div class="flex gap-2">
          <button type="button" @click="showForm = false" class="flex-1 btn-ghost">닫기</button>
          <button @click="submit" :disabled="submitting || !imageCount" class="flex-1 btn-primary">
            {{ submitting
              ? (purpose === 'enroll' ? '등록 중...' : '확인 중...')
              : `${purpose === 'enroll' ? '등록' : '인식 확인'}${imageCount ? ` (${imageCount}장)` : ''}` }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted, onUnmounted, watch } from 'vue'
import api from '@/api'
import { generateMockImageDataUrl } from '@/utils/mockImage'
import { useMockToggle } from '@/composables/useMockToggle'
import BlurredImage from '@/components/ui/BlurredImage.vue'
import ErrorNotice from '@/components/ui/ErrorNotice.vue'

// ── 목데이터 모드 ────────────────────────────────────────────────────────────

let mockPersonId = 1

function buildMockPeople() {
  return [
    { id: mockPersonId++, name: '김민석', samples: 3, enrolled_at: new Date().toISOString(), authorized: true, photoUrl: generateMockImageDataUrl('김민석', 480, 360, '#334155') },
    { id: mockPersonId++, name: '이서연', samples: 4, enrolled_at: new Date().toISOString(), authorized: true, photoUrl: generateMockImageDataUrl('이서연', 480, 360, '#334155') },
    { id: mockPersonId++, name: '박도윤', samples: 2, enrolled_at: new Date().toISOString(), authorized: false, photoUrl: generateMockImageDataUrl('박도윤', 480, 360, '#334155') },
  ]
}

const { mockActive, toggleMock } = useMockToggle(
  () => { people.value = buildMockPeople(); loading.value = false },
  fetchPeople,
)

const people = ref([])
const loading = ref(true)
const showForm = ref(false)
const submitting = ref(false)
const error = ref('')
const form = ref({ name: '', files: [] })

// ── 웹캠 촬영 ────────────────────────────────────────────────────────────────

const mode = ref('webcam')
const videoRef = ref(null)
const shots = ref([])        // { blob, url }
const streaming = ref(false)
const camError = ref('')
let stream = null

const imageCount = computed(() => (mode.value === 'webcam' ? shots.value.length : form.value.files.length))

async function startWebcam() {
  camError.value = ''
  // getUserMedia는 보안 컨텍스트(localhost 또는 HTTPS)에서만 동작한다
  if (!navigator.mediaDevices?.getUserMedia) {
    camError.value = '이 브라우저에서는 카메라를 쓸 수 없습니다. localhost 또는 HTTPS로 접속하거나 사진 업로드를 이용해주세요.'
    return
  }
  try {
    stream = await navigator.mediaDevices.getUserMedia({ video: { width: 1280, height: 720 } })
    await nextTick()
    if (videoRef.value) videoRef.value.srcObject = stream
    streaming.value = true
  } catch (e) {
    streaming.value = false
    camError.value = e.name === 'NotAllowedError'
      ? '카메라 권한이 거부되었습니다. 브라우저 주소창의 카메라 아이콘에서 허용해주세요.'
      : e.name === 'NotFoundError'
        ? '사용할 수 있는 카메라를 찾지 못했습니다.'
        : `카메라를 열지 못했습니다: ${e.message}`
  }
}

function stopWebcam() {
  stream?.getTracks().forEach(t => t.stop())
  stream = null
  streaming.value = false
}

function clearShots() {
  shots.value.forEach(s => URL.revokeObjectURL(s.url))
  shots.value = []
}

async function setMode(next) {
  mode.value = next
  if (next === 'webcam') {
    await nextTick()
    if (!stream) await startWebcam()
    else if (videoRef.value) videoRef.value.srcObject = stream
  } else {
    stopWebcam()
  }
}

async function capture() {
  const video = videoRef.value
  if (!video?.videoWidth) return
  const canvas = document.createElement('canvas')
  canvas.width = video.videoWidth
  canvas.height = video.videoHeight
  canvas.getContext('2d').drawImage(video, 0, 0)
  const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/jpeg', 0.92))
  if (blob) shots.value.push({ blob, url: URL.createObjectURL(blob) })
}

function removeShot(index) {
  URL.revokeObjectURL(shots.value[index].url)
  shots.value.splice(index, 1)
}

// 모달을 닫으면 카메라를 확실히 끈다 (촬영 표시등이 계속 켜져 있지 않도록)
watch(showForm, open => {
  if (open) return
  stopWebcam()
  clearShots()
})

const purpose = ref('enroll')      // 'enroll' | 'recognize'
const matchResult = ref(null)

function openForm(next = 'enroll') {
  purpose.value = next
  form.value = { name: '', files: [] }
  error.value = ''
  camError.value = ''
  matchResult.value = null
  showForm.value = true
  setMode(mode.value)
}

function onFiles(e) {
  form.value.files = Array.from(e.target.files)
}

// 실패해도 loading을 반드시 끄고 오류를 화면에 보여준다(호출부가 여러 곳이라 여기서 예외를 삼킨다)
const loadError = ref('')
async function fetchPeople() {
  loadError.value = ''
  try {
    const { data } = await api.get('/face/people')
    people.value = data.people
  } catch (e) {
    loadError.value = e.response?.data?.detail ?? e.message
  } finally {
    loading.value = false
  }
}

function retryPeople() {
  loading.value = true
  fetchPeople()
}

async function submit() {
  if (purpose.value === 'enroll' && !form.value.name.trim()) {
    error.value = '이름을 입력해주세요'
    return
  }
  if (!imageCount.value) {
    error.value = mode.value === 'webcam' ? '촬영 버튼으로 사진을 찍어주세요' : '사진을 한 장 이상 선택해주세요'
    return
  }

  submitting.value = true
  error.value = ''
  matchResult.value = null

  if (mockActive.value) {
    await new Promise(r => setTimeout(r, 300))
    const photoUrl = mode.value === 'webcam' ? shots.value[0]?.url : URL.createObjectURL(form.value.files[0])
    if (purpose.value === 'recognize') {
      const known = Math.random() > 0.4
      matchResult.value = known
        ? { faces: [{ name: '김민석', authorized: true, score: Number((0.5 + Math.random() * 0.4).toFixed(2)) }], threshold: 0.45 }
        : { faces: [], threshold: 0.45 }
      submitting.value = false
      return
    }
    people.value = [{ id: mockPersonId++, name: form.value.name.trim(), samples: imageCount.value, enrolled_at: new Date().toISOString(), authorized: true, photoUrl }, ...people.value]
    showForm.value = false
    submitting.value = false
    return
  }

  const body = new FormData()
  if (purpose.value === 'enroll') body.append('name', form.value.name.trim())
  if (mode.value === 'webcam') {
    shots.value.forEach((s, i) => body.append('images', s.blob, `shot${i + 1}.jpg`))
  } else {
    for (const file of form.value.files) body.append('images', file)
  }

  try {
    if (purpose.value === 'recognize') {
      const { data } = await api.post('/face/recognize', body)
      matchResult.value = data
      return
    }
    const { data } = await api.post('/face/people', body)
    if (data.found < data.total) {
      alert(`${data.total}장 중 ${data.found}장에서만 얼굴을 찾았습니다.`)
    }
    showForm.value = false
    await fetchPeople()
  } catch (e) {
    error.value = e.response?.data?.detail ?? e.message
  } finally {
    submitting.value = false
  }
}

async function toggleAuthorized(person) {
  if (mockActive.value) {
    person.authorized = !person.authorized
    return
  }
  const { data } = await api.put(`/face/people/${person.id}/authorized`, { authorized: !person.authorized })
  person.authorized = data.authorized
}

async function removePerson(person) {
  if (!confirm(`"${person.name}" 등록을 삭제하시겠습니까?`)) return
  if (mockActive.value) {
    people.value = people.value.filter(p => p.id !== person.id)
    return
  }
  await api.delete(`/face/people/${person.id}`)
  await fetchPeople()
}

onMounted(fetchPeople)

onUnmounted(() => {
  stopWebcam()
  clearShots()
})
</script>

<style scoped>
.input {
  @apply border border-neutral-200 dark:border-neutral-800 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-400;
}
.btn-primary {
  @apply bg-violet-600 text-white text-sm px-4 py-2 rounded-lg hover:bg-violet-700 transition disabled:opacity-50;
}
.btn-ghost {
  @apply bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300 text-sm px-4 py-2 rounded-lg hover:bg-neutral-200 dark:hover:bg-neutral-700 transition;
}
.tab {
  @apply flex-1 text-sm py-1.5 rounded-lg border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 text-neutral-600 dark:text-neutral-400 hover:bg-neutral-50 dark:hover:bg-neutral-800 transition;
}
.tab-on {
  @apply !bg-violet-600 !text-white !border-violet-600;
}
</style>
