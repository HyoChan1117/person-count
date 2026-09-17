<template>
  <div class="h-full overflow-y-auto bg-neutral-50 p-6 lg:p-8">
    <div class="max-w-3xl mx-auto">

      <!-- 헤더 -->
      <div class="mb-8">
        <router-link to="/face" class="inline-flex items-center gap-1 text-xs text-neutral-400 hover:text-neutral-600 transition mb-2">
          ← 얼굴 인식
        </router-link>
        <h1 class="text-2xl font-bold text-neutral-900 tracking-tight">카메라 설정</h1>
        <p class="text-sm text-neutral-500 mt-0.5">{{ place?.name }}의 PTZ 카메라 접속 정보</p>
      </div>

      <div v-if="!place" class="text-center py-12 text-neutral-400">불러오는 중...</div>

      <div v-else class="bg-white border border-neutral-200 rounded-2xl shadow-sm p-6 lg:p-8">
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

        <div class="border-t border-neutral-100 pt-6">
          <label class="label mb-3">PTZ 카메라</label>
          <p class="hint mb-4 -mt-2">IP를 비워 두면 PTZ 카메라가 없는 장소로 처리됩니다</p>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-5">
          <div>
            <label class="label">카메라 IP</label>
            <input v-model="camera.ip" class="input" />
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

        <div class="flex items-center gap-2 mt-8 pt-6 border-t border-neutral-100">
          <button @click="save" :disabled="saving" class="btn-primary">
            {{ saving ? '저장 중...' : '저장' }}
          </button>
          <button v-if="camera.ip" @click="test" :disabled="testing" class="btn-ghost">
            {{ testing ? '확인 중...' : '연결 확인' }}
          </button>
          <span v-if="saved" class="text-xs text-emerald-600">저장됨</span>
        </div>

        <div v-if="testResult" class="mt-4 rounded-xl border px-4 py-3 text-sm"
          :class="testResult.ok ? 'border-emerald-200 bg-emerald-50 text-emerald-700' : 'border-red-200 bg-red-50 text-red-700'">
          <template v-if="testResult.ok">
            연결 성공 · {{ testResult.model }} (펌웨어 {{ testResult.firmware }})<br>
            <span class="text-xs tabular-nums">
              현재 좌표 · 팬 {{ testResult.position.pan }} · 틸트 {{ testResult.position.tilt }} · 줌 {{ testResult.position.zoom }}
            </span>
          </template>
          <template v-else>{{ testResult.message }}</template>
        </div>
        <p class="text-[11px] text-neutral-400 mt-3">연결 확인은 저장된 설정으로 시도합니다. 값을 바꿨다면 먼저 저장해주세요.</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import api from '@/api'

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
  @apply block text-xs font-medium text-neutral-500 mb-1.5;
}
.input {
  @apply w-full border border-neutral-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-400;
}
.hint {
  @apply text-[11px] text-neutral-400 mt-1;
}
.btn-primary {
  @apply bg-violet-600 text-white text-sm font-medium px-4 py-2 rounded-lg hover:bg-violet-700 transition disabled:opacity-50;
}
.btn-ghost {
  @apply bg-neutral-100 text-neutral-700 text-sm font-medium px-4 py-2 rounded-lg hover:bg-neutral-200 transition disabled:opacity-50;
}
</style>
