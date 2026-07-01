<template>
  <div class="h-full overflow-y-auto bg-slate-50 p-6">
    <div class="max-w-3xl mx-auto">
      <div class="flex items-center justify-between mb-6">
        <h1 class="text-xl font-bold text-slate-800">교실 목록</h1>
        <button @click="showForm = true" class="btn-primary">+ 새 교실 추가</button>
      </div>

      <div v-if="store.loading" class="text-center py-12 text-slate-400">불러오는 중...</div>

      <div v-else-if="store.classrooms.length === 0" class="text-center py-16 text-slate-400">
        <div class="text-4xl mb-3">🏫</div>
        <p class="text-sm">등록된 교실이 없습니다. 새 교실을 추가해보세요.</p>
      </div>

      <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <div
          v-for="c in store.classrooms"
          :key="c.id"
          class="bg-white rounded-xl border border-slate-200 p-5 hover:shadow-md transition group"
        >
          <div class="flex items-start justify-between mb-3">
            <h2 class="font-semibold text-slate-800">{{ c.name }}</h2>
            <button
              @click.stop="deleteClassroom(c.id)"
              class="text-slate-300 hover:text-red-400 opacity-0 group-hover:opacity-100 transition"
            >✕</button>
          </div>

          <div class="text-xs text-slate-500 mb-1">
            CCTV {{ c.cameras.length }}대
            <span v-if="roiCount(c)" class="ml-2 text-green-600">/ ROI {{ roiCount(c) }}개</span>
          </div>

          <!-- 교실별 프롬프트 상태 표시 -->
          <div class="text-xs mb-4">
            <span
              v-if="c.prompt"
              class="inline-flex items-center gap-1 text-blue-600"
              :title="c.prompt"
            >
              💬 커스텀 프롬프트 설정됨
            </span>
            <span v-else class="text-slate-400">💬 기본 프롬프트 사용</span>
          </div>

          <div class="flex gap-2 flex-wrap">
            <router-link
              :to="`/classrooms/${c.id}/setup`"
              class="flex-1 text-center text-xs bg-blue-600 text-white py-1.5 rounded-lg hover:bg-blue-700 transition"
            >카메라 설정</router-link>
            <button
              @click="openPromptModal(c)"
              class="text-xs bg-slate-100 text-slate-700 px-3 py-1.5 rounded-lg hover:bg-slate-200 transition"
              title="교실 프롬프트 편집"
            >프롬프트</button>
            <router-link
              :to="`/dashboard/${c.id}`"
              class="flex-1 text-center text-xs bg-slate-100 text-slate-700 py-1.5 rounded-lg hover:bg-slate-200 transition"
            >대시보드</router-link>
          </div>
          <div class="mt-2">
            <router-link
              :to="`/classrooms/${c.id}/map`"
              class="block text-center text-xs bg-emerald-50 text-emerald-700 py-1.5 rounded-lg hover:bg-emerald-100 transition border border-emerald-200"
            >🗺 맵 에디터</router-link>
          </div>
        </div>
      </div>
    </div>

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

    <!-- 교실별 프롬프트 모달 -->
    <ClassroomPromptModal
      v-if="promptTarget"
      :classroom="promptTarget"
      @close="promptTarget = null"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useClassroomStore } from '@/stores/classroomStore.js'
import { usePromptStore } from '@/stores/promptStore.js'
import ClassroomPromptModal from '@/components/modals/ClassroomPromptModal.vue'

const store = useClassroomStore()
const promptStore = usePromptStore()
const showForm = ref(false)
const form = ref({ name: '' })
const promptTarget = ref(null)

onMounted(() => {
  store.fetchAll()
  promptStore.fetch()
})

function roiCount(classroom) {
  return classroom.cameras.filter(c => c.roi_polygon?.length >= 3).length
}

function openPromptModal(classroom) {
  promptTarget.value = classroom
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
