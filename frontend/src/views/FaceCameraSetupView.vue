<template>
  <div class="h-full overflow-y-auto bg-neutral-50 dark:bg-neutral-950 p-6 lg:p-8">
    <div class="max-w-3xl mx-auto">

      <!-- 헤더 -->
      <div class="mb-8">
        <router-link to="/face" class="inline-flex items-center gap-1 text-xs text-neutral-400 dark:text-neutral-600 hover:text-neutral-600 dark:hover:text-neutral-300 transition mb-2">
          ← 얼굴 인식
        </router-link>
        <div class="flex items-center justify-between gap-3">
          <div>
            <p class="text-[10px] font-semibold tracking-widest text-neutral-400 dark:text-neutral-600 uppercase mb-0.5">PTZ Camera</p>
            <div class="flex items-center gap-2">
              <h1 class="text-2xl font-bold text-neutral-900 dark:text-neutral-50 tracking-tight">카메라 설정</h1>
              <span v-if="mockActive" class="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-amber-100 dark:bg-amber-500/15 text-amber-700 dark:text-amber-400 border border-amber-200 dark:border-amber-500/30">목데이터</span>
            </div>
            <p class="text-sm text-neutral-500 dark:text-neutral-400 mt-0.5">{{ place?.name }}의 PTZ 카메라 접속 정보</p>
          </div>
          <button
            @click="toggleMock"
            class="text-xs px-3 py-1.5 rounded-lg transition font-medium border shrink-0"
            :class="mockActive
              ? 'bg-amber-500 text-white border-amber-500 hover:bg-amber-600'
              : 'bg-white dark:bg-neutral-900 border-neutral-200 dark:border-neutral-800 text-neutral-600 dark:text-neutral-300 hover:border-neutral-300 dark:hover:border-neutral-700'"
          >{{ mockActive ? '🧪 목데이터 끄기' : '🧪 목데이터로 보기' }}</button>
        </div>
      </div>

      <div v-if="!place" class="text-center py-12 text-neutral-400 dark:text-neutral-600">불러오는 중...</div>

      <div v-else class="bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-2xl shadow-sm p-6 lg:p-8">
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-5 mb-6">
          <div>
            <label class="label">장소 이름</label>
            <input v-model="name" class="input" />
          </div>
          <div>
            <label class="label">연결된 교실</label>
            <select v-model="classroomId" class="input">
              <option v-for="c in classrooms" :key="c.id" :value="c.id">{{ c.name }}</option>
              <option :value="null">연결 안 함</option>
            </select>
            <p class="hint">좌석 확인에 등록된 교실과 연결하면 어느 교실인지 함께 표시됩니다</p>
          </div>
        </div>

        <div class="border-t border-neutral-100 dark:border-neutral-800 pt-6">
          <div class="flex items-center gap-2 mb-3">
            <span class="w-1.5 h-1.5 rounded-full shrink-0" :class="camera.ip ? 'bg-emerald-400' : 'bg-neutral-300 dark:bg-neutral-700'" />
            <label class="label !mb-0">PTZ 카메라</label>
          </div>
          <p class="hint mb-4 -mt-2">IP를 비워 두면 PTZ 카메라가 없는 장소로 처리됩니다</p>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-5">
          <div>
            <label class="label">카메라 IP</label>
            <input v-model="camera.ip" class="input font-mono" />
          </div>
          <div>
            <label class="label">아이디</label>
            <input v-model="camera.username" placeholder="admin" class="input" />
          </div>
          <div>
            <label class="label">비밀번호</label>
            <input v-model="camera.password" type="password" class="input" />
          </div>
          <div>
            <label class="label">스트리밍 채널</label>
            <input v-model="camera.channel_code" class="input" />
            <p class="hint">TandemVu 기준 101=PTZ 렌즈, 201=광각 렌즈</p>
          </div>
          <div>
            <label class="label">PTZ 제어 채널</label>
            <input v-model.number="camera.control_channel" type="number" class="input" />
            <p class="hint">스트리밍 채널 코드와 다른 값입니다 (보통 1)</p>
          </div>
          <div>
            <label class="label">HTTP 포트</label>
            <input v-model.number="camera.http_port" type="number" class="input" />
          </div>
          <div>
            <label class="label">RTSP 포트</label>
            <input v-model.number="camera.rtsp_port" type="number" class="input" />
          </div>
        </div>

        <div class="flex items-center gap-2 mt-8 pt-6 border-t border-neutral-100 dark:border-neutral-800">
          <button @click="save" :disabled="saving" class="btn-primary">
            {{ saving ? '저장 중...' : '저장' }}
          </button>
          <button v-if="camera.ip" @click="test" :disabled="testing" class="btn-ghost">
            {{ testing ? '확인 중...' : '연결 확인' }}
          </button>
          <span v-if="saved" class="text-xs text-emerald-600 dark:text-emerald-400">저장됨</span>
        </div>

        <div v-if="testResult" class="mt-4 rounded-xl border px-4 py-3 text-sm"
          :class="testResult.ok ? 'border-emerald-200 dark:border-emerald-500/30 bg-emerald-50 dark:bg-emerald-500/10 text-emerald-700 dark:text-emerald-400' : 'border-red-200 dark:border-red-500/30 bg-red-50 dark:bg-red-500/10 text-red-700 dark:text-red-400'">
          <template v-if="testResult.ok">
            연결 성공 · {{ testResult.model }} (펌웨어 {{ testResult.firmware }})<br>
            <span class="text-xs tabular-nums font-mono">
              현재 좌표 · 팬 {{ testResult.position.pan }} · 틸트 {{ testResult.position.tilt }} · 줌 {{ testResult.position.zoom }}
            </span>
          </template>
          <template v-else>{{ testResult.message }}</template>
        </div>
        <p class="text-[11px] text-neutral-400 dark:text-neutral-600 mt-3">연결 확인은 저장된 설정으로 시도합니다. 값을 바꿨다면 먼저 저장해주세요.</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import api from '@/api'
import { useMockToggle } from '@/composables/useMockToggle'

const route = useRoute()
const placeId = route.params.id

const place = ref(null)
const name = ref('')
const camera = ref({})
const classrooms = ref([])
const classroomId = ref(null)
const saving = ref(false)
const testing = ref(false)
const saved = ref(false)
const testResult = ref(null)

// ── 목데이터 모드 ────────────────────────────────────────────────────────────

const { mockActive, toggleMock } = useMockToggle(
  () => {
    testResult.value = null
    place.value = place.value ?? { id: placeId, name: '샘플 감시 장소' }
    name.value = place.value.name
    camera.value = { ip: '192.168.0.50', username: 'admin', password: '', channel_code: '101', control_channel: 1, http_port: 80, rtsp_port: 554 }
  },
  () => {
    testResult.value = null
    fetchPlace()
  },
)

async function fetchPlace() {
  const [placeRes, classroomRes] = await Promise.all([
    api.get(`/face/places/${placeId}`),
    api.get('/classrooms/'),
  ])
  place.value = placeRes.data
  name.value = placeRes.data.name
  camera.value = { ...placeRes.data.camera }
  classroomId.value = placeRes.data.classroom_id ?? null
  classrooms.value = classroomRes.data
}

async function save() {
  if (mockActive.value) {
    saving.value = true
    await new Promise(r => setTimeout(r, 200))
    saved.value = true
    saving.value = false
    return
  }
  saving.value = true
  saved.value = false
  try {
    await api.put(`/face/places/${placeId}`, {
      name: name.value,
      camera: camera.value,
      classroom_id: classroomId.value,
      clear_classroom: classroomId.value === null,
    })
    saved.value = true
    await fetchPlace()
  } catch (e) {
    alert('저장 실패: ' + (e.response?.data?.detail ?? e.message))
  } finally {
    saving.value = false
  }
}

async function test() {
  if (mockActive.value) {
    testing.value = true
    testResult.value = null
    await new Promise(r => setTimeout(r, 400))
    testResult.value = { ok: true, model: 'DS-2DE4425IW-DE (Mock)', firmware: 'V5.7.0', position: { pan: 700, tilt: 150, zoom: 20 } }
    testing.value = false
    return
  }
  testing.value = true
  testResult.value = null
  try {
    const { data } = await api.get(`/face/places/${placeId}/camera/test`)
    testResult.value = data
  } catch (e) {
    testResult.value = { ok: false, message: e.response?.data?.detail ?? e.message }
  } finally {
    testing.value = false
  }
}

onMounted(fetchPlace)
</script>

<style scoped>
.label {
  @apply block text-xs font-medium text-neutral-500 dark:text-neutral-400 mb-1.5;
}
.input {
  @apply w-full border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-950 text-neutral-900 dark:text-neutral-100 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-400 dark:focus:ring-violet-500;
}
.hint {
  @apply text-[11px] text-neutral-400 dark:text-neutral-600 mt-1;
}
.btn-primary {
  @apply bg-violet-600 text-white text-sm font-medium px-4 py-2 rounded-lg hover:bg-violet-700 transition disabled:opacity-50;
}
.btn-ghost {
  @apply bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300 text-sm font-medium px-4 py-2 rounded-lg hover:bg-neutral-200 dark:hover:bg-neutral-700 transition disabled:opacity-50;
}
</style>
