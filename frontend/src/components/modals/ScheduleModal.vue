<template>
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="$emit('close')">
    <div class="bg-white dark:bg-neutral-900 rounded-2xl shadow-xl w-full max-w-2xl mx-4 flex flex-col max-h-[90vh]">
      <!-- 헤더 -->
      <div class="flex items-center justify-between px-6 py-4 border-b border-neutral-100 dark:border-neutral-800">
        <div>
          <h2 class="font-bold text-neutral-800 dark:text-neutral-100">시간표 설정 — {{ classroom.name }}</h2>
          <p class="text-xs text-neutral-400 dark:text-neutral-600 mt-0.5">수업이 있는 정각을 선택하세요. 선택하지 않은 시간은 모니터링에서 '수업 없음'으로 표시됩니다.</p>
        </div>
        <button @click="$emit('close')" class="text-neutral-400 dark:text-neutral-600 hover:text-neutral-600 text-xl leading-none">✕</button>
      </div>

      <!-- 본문 -->
      <div class="flex-1 overflow-auto px-6 py-5">
        <table class="border-collapse">
          <thead>
            <tr>
              <th class="w-12" />
              <th
                v-for="h in HOURS"
                :key="h"
                class="text-[10px] font-medium text-neutral-400 dark:text-neutral-600 pb-1.5 px-0.5"
              >{{ h }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="day in DAYS" :key="day.key">
              <td>
                <button
                  @click="toggleDay(day.key)"
                  class="w-11 h-8 text-xs font-semibold rounded-lg mr-1.5 hover:bg-blue-50 text-neutral-600 dark:text-neutral-400 transition"
                >{{ day.label }}</button>
              </td>
              <td v-for="h in HOURS" :key="h" class="p-0.5">
                <button
                  @click="toggleCell(day.key, h)"
                  class="w-8 h-8 rounded-md text-[10px] font-medium transition"
                  :class="isOn(day.key, h)
                    ? 'bg-blue-500 text-white'
                    : 'bg-neutral-100 dark:bg-neutral-800 text-neutral-300 dark:text-neutral-700 hover:bg-neutral-200 dark:hover:bg-neutral-600'"
                >{{ h }}</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 푸터 -->
      <div class="flex gap-2 justify-end px-6 py-4 border-t border-neutral-100 dark:border-neutral-800">
        <button @click="clearAll" class="btn-ghost mr-auto">전체 해제</button>
        <button @click="$emit('close')" class="btn-ghost">취소</button>
        <button @click="handleSave" :disabled="saving" class="btn-primary">
          {{ saving ? '저장 중...' : '저장' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useClassroomStore } from '@/stores/classroomStore.js'

const DAYS = [
  { key: 'mon', label: '월' },
  { key: 'tue', label: '화' },
  { key: 'wed', label: '수' },
  { key: 'thu', label: '목' },
  { key: 'fri', label: '금' },
]
const HOURS = Array.from({ length: 13 }, (_, i) => 9 + i) // 9..21

const props = defineProps({
  classroom: { type: Object, required: true },
})
const emit = defineEmits(['close'])

const classroomStore = useClassroomStore()
const saving = ref(false)

const selected = reactive(
  Object.fromEntries(DAYS.map(d => [d.key, new Set(props.classroom.schedule?.[d.key] ?? [])]))
)

function isOn(dayKey, hour) {
  return selected[dayKey].has(hour)
}

function toggleCell(dayKey, hour) {
  const set = selected[dayKey]
  if (set.has(hour)) set.delete(hour)
  else set.add(hour)
}

function toggleDay(dayKey) {
  const set = selected[dayKey]
  if (set.size === HOURS.length) set.clear()
  else HOURS.forEach(h => set.add(h))
}

function clearAll() {
  DAYS.forEach(d => selected[d.key].clear())
}

async function handleSave() {
  saving.value = true
  try {
    const schedule = Object.fromEntries(
      DAYS.map(d => [d.key, [...selected[d.key]].sort((a, b) => a - b)])
    )
    await classroomStore.saveClassroom(props.classroom.id, { schedule })
    emit('close')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.btn-primary {
  @apply bg-blue-600 text-white text-sm px-5 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 transition;
}
.btn-ghost {
  @apply bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300 text-sm px-5 py-2 rounded-lg hover:bg-neutral-200 dark:hover:bg-neutral-600 transition;
}
</style>
