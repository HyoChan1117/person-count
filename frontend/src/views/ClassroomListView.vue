<template>
  <div class="h-full overflow-y-auto bg-slate-50 p-6">
    <div class="max-w-6xl mx-auto">

      <!-- 헤더 -->
      <div class="flex items-center justify-between mb-6 gap-4 flex-wrap">
        <h1 class="text-2xl font-bold text-slate-800">교실 목록</h1>

        <div class="flex items-center gap-2 ml-auto">
          <div class="relative">
            <span class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-300 text-sm">⌕</span>
            <input
              v-model="search"
              type="text"
              placeholder="교실 이름으로 검색"
              class="pl-8 pr-3 py-2 text-sm bg-white border border-slate-200 rounded-full w-56 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent"
            />
          </div>
        </div>
      </div>

      <div v-if="store.loading" class="text-center py-12 text-slate-400">불러오는 중...</div>

      <div v-else-if="store.classrooms.length === 0" class="text-center py-16 text-slate-400">
        <div class="text-4xl mb-3">🏫</div>
        <p class="text-sm">등록된 교실이 없습니다. 새 교실을 추가해보세요.</p>
      </div>

      <div v-else-if="filteredClassrooms.length === 0" class="text-center py-16 text-slate-400">
        <p class="text-sm">"{{ search }}"에 해당하는 교실이 없습니다.</p>
      </div>

      <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        <div
          v-for="c in filteredClassrooms"
          :key="c.id"
          class="bg-white rounded-2xl border border-slate-200 p-4 hover:shadow-lg transition group flex flex-col"
        >
          <!-- 아이콘 배지 + 메뉴 -->
          <div class="flex items-start justify-between mb-3">
            <div
              class="w-10 h-10 rounded-xl flex items-center justify-center text-white font-bold text-sm shrink-0"
              :class="badgeColor(c.id)"
            >{{ initials(c.name) }}</div>
            <button
              v-if="auth.isAdmin"
              @click.stop="deleteClassroom(c.id)"
              title="교실 삭제"
              class="text-slate-300 hover:text-red-400 opacity-0 group-hover:opacity-100 transition text-lg leading-none px-1"
            >⋯</button>
          </div>

          <h2 class="font-semibold text-slate-800 mb-2">{{ c.name }}</h2>

          <ul class="text-xs text-slate-500 space-y-1 mb-3">
            <li>· CCTV {{ c.cameras.length }}대<span v-if="seatLineCount(c)"> · 좌석 설정 {{ seatLineCount(c) }}대</span></li>
            <li v-if="c.prompt" class="text-blue-600">· 💬 커스텀 프롬프트 설정됨</li>
            <li v-else>· 💬 기본 프롬프트 사용</li>
          </ul>

          <!-- 설정 진행률 -->
          <div class="mb-3">
            <div class="flex items-center justify-between text-[10px] text-slate-400 mb-1">
              <span>설정 진행률</span>
              <span class="font-semibold text-slate-500">{{ progressPct(c) }}%</span>
            </div>
            <div class="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden">
              <div
                class="h-full rounded-full transition-all duration-500"
                :class="progressPct(c) > 0 ? 'bg-blue-500' : 'bg-slate-200'"
                :style="{ width: progressPct(c) + '%' }"
              />
            </div>
          </div>

          <div class="flex-1" />

          <!-- 카메라 아바타 스택 -->
          <div class="flex items-center -space-x-1.5 mb-3">
            <div
              v-for="(cam, i) in c.cameras.slice(0, 4)"
              :key="cam.camera_id"
              class="w-6 h-6 rounded-full flex items-center justify-center text-[9px] font-semibold text-white ring-2 ring-white"
              :class="badgeColor(c.id + i + 1)"
              :title="cam.name"
            >{{ cam.name?.slice(-1) ?? '?' }}</div>
            <div
              v-if="c.cameras.length > 4"
              class="w-6 h-6 rounded-full flex items-center justify-center text-[9px] font-semibold bg-slate-100 text-slate-500 ring-2 ring-white"
            >+{{ c.cameras.length - 4 }}</div>
            <span v-if="c.cameras.length === 0" class="text-[10px] text-slate-300 pl-1">등록된 카메라 없음</span>
          </div>

          <!-- 액션 버튼 -->
          <div class="flex gap-1.5 flex-wrap border-t border-slate-100 pt-3">
            <router-link
              v-if="auth.isAdmin"
              :to="`/classrooms/${c.id}/setup`"
              class="flex-1 text-center text-[11px] bg-blue-600 text-white py-1.5 rounded-lg hover:bg-blue-700 transition"
            >카메라 설정</router-link>
            <router-link
              :to="`/dashboard/${c.id}`"
              class="flex-1 flex items-center justify-center text-center text-[11px] bg-slate-100 text-slate-700 py-1.5 rounded-lg hover:bg-slate-200 transition"
            >대시보드</router-link>
            <router-link
              :to="`/monitoring/${c.id}`"
              class="flex-1 flex items-center justify-center text-center text-[11px] bg-slate-100 text-slate-700 py-1.5 rounded-lg hover:bg-slate-200 transition"
            >모니터링</router-link>
            <router-link
              v-if="auth.isAdmin"
              :to="`/classrooms/${c.id}/map`"
              class="w-full text-center text-[11px] bg-emerald-50 text-emerald-700 py-1.5 rounded-lg hover:bg-emerald-100 transition border border-emerald-200"
            >🗺 맵 에디터</router-link>
          </div>
        </div>
      </div>
    </div>

    <!-- 새 교실 추가 (플로팅 버튼) -->
    <button
      v-if="auth.isAdmin"
      @click="showForm = true"
      title="새 교실 추가"
      class="fixed bottom-8 right-8 w-14 h-14 rounded-full bg-slate-900 text-white text-2xl flex items-center justify-center shadow-xl hover:bg-slate-700 transition"
    >+</button>

    <!-- 새 교실 추가 모달 -->
    <div v-if="showForm" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50" @click.self="showForm = false">
      <div class="bg-white rounded-2xl p-6 w-80 shadow-xl">
        <h2 class="font-bold text-slate-800 mb-4">새 교실 추가</h2>
        <form @submit.prevent="createClassroom">
          <label class="block text-sm text-slate-600 mb-1">교실 이름</label>
          <input v-model="form.name" required class="input w-full mb-4" placeholder="예: 101호" />
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
import { useClassroomStore } from '@/stores/classroomStore.js'
import { useAuthStore } from '@/stores/authStore'

const auth = useAuthStore()
const store = useClassroomStore()
const showForm = ref(false)
const form = ref({ name: '' })
const search = ref('')

onMounted(() => {
  store.fetchAll()
})

const filteredClassrooms = computed(() => {
  const q = search.value.trim().toLowerCase()
  if (!q) return store.classrooms
  return store.classrooms.filter(c => c.name.toLowerCase().includes(q))
})

function seatLineCount(classroom) {
  return classroom.cameras.filter(c => Object.keys(c.seat_lines ?? {}).length > 0).length
}

// 좌석 라인(seat_lines) 설정이 끝난 카메라 비율
function progressPct(classroom) {
  if (!classroom.cameras.length) return 0
  return Math.round(seatLineCount(classroom) / classroom.cameras.length * 100)
}

const BADGE_COLORS = [
  'bg-blue-500', 'bg-violet-500', 'bg-emerald-500', 'bg-orange-500',
  'bg-pink-500', 'bg-cyan-500', 'bg-rose-500', 'bg-lime-600',
]
function badgeColor(seed) {
  return BADGE_COLORS[seed % BADGE_COLORS.length]
}

function initials(name) {
  return name?.trim()?.slice(0, 2) ?? '?'
}

async function createClassroom() {
  await store.createClassroom({ name: form.value.name })
  showForm.value = false
  form.value = { name: '' }
}

async function deleteClassroom(id) {
  if (!confirm('이 교실을 삭제하시겠습니까?')) return
  await store.deleteClassroom(id)
}
</script>

<style scoped>
.input {
  @apply border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400;
}
.btn-primary {
  @apply bg-blue-600 text-white text-sm px-4 py-2 rounded-lg hover:bg-blue-700 transition;
}
.btn-ghost {
  @apply bg-slate-100 text-slate-700 text-sm px-4 py-2 rounded-lg hover:bg-slate-200 transition;
}
</style>
