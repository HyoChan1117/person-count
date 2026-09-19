<template>
  <div class="h-full overflow-y-auto bg-neutral-50 dark:bg-neutral-950 p-6 lg:p-8">
    <div class="max-w-6xl mx-auto">

      <!-- 헤더 -->
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
        <div>
          <h1 class="text-2xl font-bold text-neutral-900 dark:text-neutral-50 tracking-tight">얼굴 인식</h1>
          <p class="text-sm text-neutral-500 dark:text-neutral-400 mt-0.5">감시 장소를 등록하고 PTZ 카메라와 순찰 구역을 관리하세요</p>
        </div>

        <button
          @click="showForm = true"
          class="inline-flex items-center gap-1.5 bg-violet-600 text-white text-sm font-medium px-4 py-2 rounded-lg hover:bg-violet-700 transition shrink-0 w-fit"
        >+ 장소 추가</button>
      </div>

      <!-- 장소 선택 모드 배너 -->
      <div v-if="actionMeta" class="mb-6 flex items-center justify-between bg-violet-50 border border-violet-200 rounded-xl px-4 py-3">
        <p class="text-sm text-violet-700"><strong>{{ actionMeta.label }}</strong>을(를) 진행할 장소를 선택하세요.</p>
        <router-link to="/face" class="text-xs text-violet-500 hover:underline shrink-0">선택 취소</router-link>
      </div>

      <div v-if="loading" class="text-center py-12 text-neutral-400 dark:text-neutral-600">불러오는 중...</div>

      <ErrorNotice v-else-if="loadError" legacy class="my-6" title="감시 장소를 불러오지 못했습니다" :message="loadError" @retry="retryPlaces" />

      <div v-else-if="!places.length" class="flex flex-col items-center justify-center py-24 text-neutral-400 dark:text-neutral-600 gap-3">
        <div class="w-14 h-14 rounded-2xl bg-neutral-100 dark:bg-neutral-800 flex items-center justify-center text-2xl">🙂</div>
        <p class="text-sm">등록된 감시 장소가 없습니다. 장소를 추가해보세요.</p>
        <router-link to="/face/people" class="text-xs text-violet-600 hover:underline">👤 인물 등록하러 가기</router-link>
      </div>

      <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <div
          v-for="p in places"
          :key="p.id"
          @click="actionMeta && selectPlace(p)"
          class="bg-white dark:bg-neutral-900 rounded-2xl border border-neutral-200 dark:border-neutral-800 shadow-sm p-5 hover:shadow-md hover:border-violet-200 transition group flex flex-col"
          :class="actionMeta ? 'cursor-pointer hover:ring-2 hover:ring-violet-300' : ''"
        >
          <h2 class="font-semibold text-neutral-800 dark:text-neutral-100 text-lg">{{ p.name }}</h2>
        </div>
      </div>
    </div>

    <!-- 장소 추가 모달 -->
    <div v-if="showForm" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50" @click.self="showForm = false">
      <div class="bg-white dark:bg-neutral-900 rounded-2xl p-6 w-80 shadow-xl">
        <h2 class="font-bold text-neutral-800 dark:text-neutral-100 mb-4">감시 장소 추가</h2>
        <form @submit.prevent="createPlace">
          <label class="block text-sm text-neutral-600 dark:text-neutral-400 mb-1">교실 선택</label>
          <select v-model="form.classroomId" class="input w-full mb-3">
            <option v-for="c in classrooms" :key="c.id" :value="c.id">{{ c.name }}</option>
            <option :value="null">직접 입력</option>
          </select>

          <template v-if="form.classroomId === null">
            <label class="block text-sm text-neutral-600 dark:text-neutral-400 mb-1">장소 이름</label>
            <input v-model="form.name" required placeholder="예: 창조관 301호" class="input w-full mb-2" />
          </template>

          <p class="text-[11px] text-neutral-400 dark:text-neutral-600 mb-4">추가한 뒤 카메라 설정에서 IP와 계정을 입력해주세요.</p>
          <div class="flex gap-2">
            <button type="button" @click="showForm = false" class="flex-1 btn-ghost">취소</button>
            <button type="submit" class="flex-1 btn-primary">추가</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/api'
import { FACE_ACTIONS } from '@/constants/navActions'
import ErrorNotice from '@/components/ui/ErrorNotice.vue'

const route = useRoute()
const router = useRouter()
const places = ref([])
const classrooms = ref([])
const loading = ref(true)
const showForm = ref(false)
const form = ref({ name: '', classroomId: null })

const ACTIONS = Object.fromEntries(FACE_ACTIONS.map(a => [a.action, a]))
const actionMeta = computed(() => ACTIONS[route.query.action] ?? null)

function selectPlace(p) {
  if (!actionMeta.value) return
  router.push(actionMeta.value.path(p.id))
}

// 실패해도 loading을 반드시 끄고 오류를 화면에 보여준다(장소 등록 뒤 목록 갱신에서도 쓰이므로 여기서 예외를 삼킨다)
const loadError = ref('')
async function fetchPlaces() {
  loadError.value = ''
  try {
    const [placeRes, classroomRes] = await Promise.all([
      api.get('/face/places'),
      api.get('/classrooms/'),
    ])
    places.value = placeRes.data.places
    classrooms.value = classroomRes.data
    // 등록된 교실이 있으면 첫 교실을 기본 선택해 둔다
    if (form.value.classroomId === null && classrooms.value.length) {
      form.value.classroomId = classrooms.value[0].id
    }
  } catch (e) {
    loadError.value = e.response?.data?.detail ?? e.message
  } finally {
    loading.value = false
  }
}

function retryPlaces() {
  loading.value = true
  fetchPlaces()
}

async function createPlace() {
  await api.post('/face/places', {
    name: form.value.classroomId === null ? form.value.name : null,
    classroom_id: form.value.classroomId,
  })
  showForm.value = false
  form.value = { name: '', classroomId: classrooms.value[0]?.id ?? null }
  await fetchPlaces()
}

onMounted(fetchPlaces)
</script>

<style scoped>
.input {
  @apply border border-neutral-200 dark:border-neutral-800 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-400;
}
.btn-primary {
  @apply bg-violet-600 text-white text-sm px-4 py-2 rounded-lg hover:bg-violet-700 transition;
}
.btn-ghost {
  @apply bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300 text-sm px-4 py-2 rounded-lg hover:bg-neutral-200 dark:hover:bg-neutral-700 transition;
}
</style>
