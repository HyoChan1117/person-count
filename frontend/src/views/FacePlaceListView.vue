<template>
  <div class="h-full overflow-y-auto bg-neutral-50 p-6 lg:p-8">
    <div class="max-w-6xl mx-auto">

      <!-- 헤더 -->
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
        <div>
          <h1 class="text-2xl font-bold text-neutral-900 tracking-tight">얼굴 인식</h1>
          <p class="text-sm text-neutral-500 mt-0.5">감시 장소를 등록하고 PTZ 카메라와 순찰 구역을 관리하세요</p>
        </div>

        <button
          @click="showForm = true"
          class="inline-flex items-center gap-1.5 bg-violet-600 text-white text-sm font-medium px-4 py-2 rounded-lg hover:bg-violet-700 transition shrink-0 w-fit"
        >+ 장소 추가</button>
      </div>

      <div v-if="loading" class="text-center py-12 text-neutral-400">불러오는 중...</div>

      <div v-else-if="!places.length" class="flex flex-col items-center justify-center py-24 text-neutral-400 gap-3">
        <div class="w-14 h-14 rounded-2xl bg-neutral-100 flex items-center justify-center text-2xl">🙂</div>
        <p class="text-sm">등록된 감시 장소가 없습니다. 장소를 추가해보세요.</p>
        <router-link to="/face/people" class="text-xs text-violet-600 hover:underline">👤 인물 등록하러 가기</router-link>
      </div>

      <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <div
          v-for="p in places"
          :key="p.id"
          class="bg-white rounded-2xl border border-neutral-200 shadow-sm p-5 hover:shadow-md hover:border-violet-200 transition group flex flex-col"
        >
          <div class="flex items-start justify-between mb-3">
            <div class="w-10 h-10 rounded-xl bg-violet-50 flex items-center justify-center text-lg shrink-0">🙂</div>
            <button
              @click="removePlace(p)"
              title="장소 삭제"
              class="text-neutral-300 hover:text-red-400 opacity-0 group-hover:opacity-100 transition text-lg leading-none px-1"
            >⋯</button>
          </div>

          <h2 class="font-semibold text-neutral-800 mb-2">{{ p.name }}</h2>

          <ul class="text-xs text-neutral-500 space-y-1 mb-4">
            <li v-if="classroomName(p)">· 교실 {{ classroomName(p) }}</li>
            <li v-if="p.camera?.ip">· PTZ 카메라 {{ p.camera.ip }}</li>
            <li v-else class="text-neutral-400">· PTZ 카메라 없음</li>
            <li>· 순찰 구역 {{ p.zones?.length ?? 0 }}개</li>
          </ul>

          <div class="flex-1" />

          <div class="flex gap-1.5 flex-wrap border-t border-neutral-100 pt-3">
            <router-link
              :to="`/face/${p.id}/camera`"
              class="flex-1 text-center text-[11px] bg-violet-600 text-white py-1.5 rounded-lg hover:bg-violet-700 transition"
            >카메라 설정</router-link>
            <router-link
              :to="`/face/${p.id}/zones`"
              class="flex-1 flex items-center justify-center text-center text-[11px] bg-neutral-100 text-neutral-700 py-1.5 rounded-lg hover:bg-neutral-200 transition"
            >구역 등록</router-link>
            <router-link
              :to="`/face/${p.id}/monitoring`"
              class="flex-1 flex items-center justify-center text-center text-[11px] bg-neutral-100 text-neutral-700 py-1.5 rounded-lg hover:bg-neutral-200 transition"
            >모니터링</router-link>
            <router-link
              to="/face/people"
              class="w-full text-center text-[11px] bg-violet-50 text-violet-700 py-1.5 rounded-lg hover:bg-violet-100 transition border border-violet-200"
            >👤 인물 등록</router-link>
          </div>
        </div>
      </div>
    </div>

    <!-- 장소 추가 모달 -->
    <div v-if="showForm" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50" @click.self="showForm = false">
      <div class="bg-white rounded-2xl p-6 w-80 shadow-xl">
        <h2 class="font-bold text-neutral-800 mb-4">감시 장소 추가</h2>
        <form @submit.prevent="createPlace">
          <label class="block text-sm text-neutral-600 mb-1">교실 선택</label>
          <select v-model="form.classroomId" class="input w-full mb-3">
            <option v-for="c in classrooms" :key="c.id" :value="c.id">{{ c.name }}</option>
            <option :value="null">직접 입력</option>
          </select>

          <template v-if="form.classroomId === null">
            <label class="block text-sm text-neutral-600 mb-1">장소 이름</label>
            <input v-model="form.name" required placeholder="예: 창조관 301호" class="input w-full mb-2" />
          </template>

          <p class="text-[11px] text-neutral-400 mb-4">추가한 뒤 카메라 설정에서 IP와 계정을 입력해주세요.</p>
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
import { ref, onMounted } from 'vue'
import api from '@/api'

const places = ref([])
const classrooms = ref([])
const loading = ref(true)
const showForm = ref(false)
const form = ref({ name: '', classroomId: null })

function classroomName(place) {
  return classrooms.value.find(c => c.id === place.classroom_id)?.name
}

async function fetchPlaces() {
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
  loading.value = false
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

async function removePlace(place) {
  if (!confirm(`"${place.name}" 장소를 삭제하시겠습니까? 등록된 구역도 함께 삭제됩니다.`)) return
  await api.delete(`/face/places/${place.id}`)
  await fetchPlaces()
}

onMounted(fetchPlaces)
</script>

<style scoped>
.input {
  @apply border border-neutral-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-400;
}
.btn-primary {
  @apply bg-violet-600 text-white text-sm px-4 py-2 rounded-lg hover:bg-violet-700 transition;
}
.btn-ghost {
  @apply bg-neutral-100 text-neutral-700 text-sm px-4 py-2 rounded-lg hover:bg-neutral-200 transition;
}
</style>
