<template>
  <div class="ds-root h-full overflow-y-auto bg-canvas p-section">
    <div class="mx-auto flex w-full max-w-[1680px] flex-col gap-section">

      <!-- 헤더 -->
      <div class="flex flex-col gap-gutter">
        <router-link to="/face" class="text-sm text-fg-muted transition-colors hover:text-fg">
          ← 얼굴 인식
        </router-link>
        <div class="flex items-center justify-between gap-3">
          <div>
            <div class="mt-1 flex items-center gap-2">
              <h1 class="text-3xl font-bold tracking-tight text-fg">카메라 설정</h1>
              <span v-if="mockActive" class="rounded-full border border-state-unknown/30 bg-state-unknown/10 px-2 py-0.5 text-xs font-semibold text-state-unknown">목데이터</span>
            </div>
            <p class="mt-1 text-lg text-fg-muted">{{ place?.name }}의 PTZ 카메라 접속 정보</p>
          </div>
          <button
            @click="toggleMock"
            class="shrink-0 rounded-lg border px-3 py-2 text-sm font-medium transition-colors"
            :class="mockActive
              ? 'border-state-unknown bg-state-unknown text-canvas hover:opacity-90'
              : 'border-line text-fg-muted hover:bg-line/40 hover:text-fg'"
          >{{ mockActive ? '🧪 목데이터 끄기' : '🧪 목데이터로 보기' }}</button>
        </div>
      </div>

      <div v-if="!place" class="text-center py-12 text-neutral-400 dark:text-neutral-600">불러오는 중...</div>

      <div v-else class="w-full max-w-5xl rounded-card border border-line bg-card p-card shadow-card">
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

        <div class="border-t border-line pt-6">
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

        <div class="mt-8 flex items-center gap-2 border-t border-line pt-6">
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
  @apply mb-1.5 block text-xs font-medium text-fg-muted;
}
.input {
  @apply w-full rounded-lg border border-line bg-canvas px-3 py-2 text-sm text-fg placeholder:text-fg-muted focus:outline-none focus-visible:border-fg-muted;
}
.hint {
  @apply mt-1 text-[11px] text-fg-muted;
}
.btn-primary {
  @apply rounded-lg bg-fg px-4 py-2 text-sm font-semibold text-canvas transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50;
}
.btn-ghost {
  @apply rounded-lg border border-line px-4 py-2 text-sm font-medium text-fg-muted transition-colors hover:bg-line/40 hover:text-fg disabled:opacity-50;
}
</style>
