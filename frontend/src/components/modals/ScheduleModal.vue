<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" @click.self="emit('close')">
    <div class="flex max-h-[90vh] w-full max-w-3xl flex-col rounded-card border border-line bg-card shadow-xl">
      <header class="flex items-start justify-between gap-4 border-b border-line px-card py-4">
        <div>
          <h2 class="text-xl font-semibold text-fg">시간표 설정</h2>
          <p class="mt-1 text-sm text-fg-muted">{{ classroom.name }}의 강의명, 교수명, 수업 시간을 저장합니다.</p>
        </div>
        <button
          type="button"
          class="rounded-md px-2 py-1 text-xl leading-none text-fg-muted transition-colors hover:bg-line/50 hover:text-fg"
          aria-label="닫기"
          @click="emit('close')"
        >x</button>
      </header>

      <div class="min-h-0 flex-1 overflow-auto px-card py-card">
        <form class="grid grid-cols-[7rem_7rem_minmax(0,1fr)_minmax(0,1fr)_auto] items-end gap-2" @submit.prevent="addLesson">
          <label class="space-y-1 text-sm">
            <span class="text-fg-muted">요일</span>
            <select v-model="draft.day" class="field">
              <option v-for="day in DAYS" :key="day.key" :value="day.key">{{ day.label }}</option>
            </select>
          </label>
          <label class="space-y-1 text-sm">
            <span class="text-fg-muted">시간</span>
            <select v-model.number="draft.hour" class="field">
              <option v-for="hour in HOURS" :key="hour" :value="hour">{{ pad(hour) }}:00</option>
            </select>
          </label>
          <label class="space-y-1 text-sm">
            <span class="text-fg-muted">강의명</span>
            <input v-model.trim="draft.title" class="field" placeholder="예: 컴퓨터비전" />
          </label>
          <label class="space-y-1 text-sm">
            <span class="text-fg-muted">교수명</span>
            <input v-model.trim="draft.professor" class="field" placeholder="예: 홍길동" />
          </label>
          <button type="submit" class="rounded-lg bg-fg px-4 py-2.5 text-sm font-semibold text-canvas transition-opacity hover:opacity-90">
            추가
          </button>
        </form>

        <div class="mt-card space-y-4">
          <section v-for="day in DAYS" :key="day.key" class="rounded-lg border border-line">
            <div class="flex items-center justify-between border-b border-line px-4 py-3">
              <h3 class="font-semibold text-fg">{{ day.label }}</h3>
              <span class="text-sm text-fg-muted">{{ lessons[day.key].length }}개 수업</span>
            </div>

            <div v-if="lessons[day.key].length" class="divide-y divide-line">
              <div
                v-for="lesson in sortedLessons(day.key)"
                :key="lesson.id"
                class="grid grid-cols-[6rem_minmax(0,1fr)_minmax(0,1fr)_auto] items-center gap-2 px-4 py-3"
              >
                <select v-model.number="lesson.hour" class="field">
                  <option v-for="hour in HOURS" :key="hour" :value="hour">{{ pad(hour) }}:00</option>
                </select>
                <input v-model.trim="lesson.title" class="field" placeholder="강의명" />
                <input v-model.trim="lesson.professor" class="field" placeholder="교수명" />
                <button
                  type="button"
                  class="rounded-lg border border-state-alert/30 px-3 py-2 text-sm font-medium text-state-alert transition-colors hover:bg-state-alert/10"
                  @click="removeLesson(day.key, lesson.id)"
                >
                  삭제
                </button>
              </div>
            </div>
            <p v-else class="px-4 py-6 text-center text-sm text-fg-muted">등록된 수업이 없습니다.</p>
          </section>
        </div>
      </div>

      <footer class="flex items-center gap-2 border-t border-line px-card py-4">
        <button type="button" class="rounded-lg border border-line px-4 py-2.5 text-sm font-medium text-fg-muted transition-colors hover:bg-line/40 hover:text-fg" @click="clearAll">
          전체 지우기
        </button>
        <div class="flex-1" />
        <button type="button" class="rounded-lg border border-line px-4 py-2.5 text-sm font-medium text-fg-muted transition-colors hover:bg-line/40 hover:text-fg" @click="emit('close')">
          취소
        </button>
        <button
          type="button"
          :disabled="saving"
          class="rounded-lg bg-fg px-5 py-2.5 text-sm font-semibold text-canvas transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
          @click="handleSave"
        >
          {{ saving ? '저장 중...' : '저장' }}
        </button>
      </footer>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useClassroomStore } from '@/stores/classroomStore.js'

const DAYS = [
  { key: 'mon', label: '월요일' },
  { key: 'tue', label: '화요일' },
  { key: 'wed', label: '수요일' },
  { key: 'thu', label: '목요일' },
  { key: 'fri', label: '금요일' },
  { key: 'sat', label: '토요일' },
  { key: 'sun', label: '일요일' },
]
const HOURS = Array.from({ length: 15 }, (_, i) => 8 + i)

const props = defineProps({
  classroom: { type: Object, required: true },
})
const emit = defineEmits(['close'])

const classroomStore = useClassroomStore()
const saving = ref(false)
let nextId = 1

function pad(n) {
  return String(n).padStart(2, '0')
}

function normalizeLesson(item) {
  if (typeof item === 'number') return { id: nextId++, hour: item, title: '', professor: '' }
  return {
    id: nextId++,
    hour: Number(item?.hour ?? 9),
    title: item?.title ?? item?.name ?? '',
    professor: item?.professor ?? '',
  }
}

const lessons = reactive(Object.fromEntries(
  DAYS.map((day) => [day.key, (props.classroom.schedule?.[day.key] ?? []).map(normalizeLesson)])
))

const draft = reactive({
  day: 'mon',
  hour: 9,
  title: '',
  professor: '',
})

function sortedLessons(dayKey) {
  return lessons[dayKey].slice().sort((a, b) => a.hour - b.hour || a.title.localeCompare(b.title))
}

function addLesson() {
  lessons[draft.day].push({
    id: nextId++,
    hour: draft.hour,
    title: draft.title,
    professor: draft.professor,
  })
  draft.title = ''
  draft.professor = ''
}

function removeLesson(dayKey, id) {
  const idx = lessons[dayKey].findIndex((lesson) => lesson.id === id)
  if (idx !== -1) lessons[dayKey].splice(idx, 1)
}

function clearAll() {
  DAYS.forEach((day) => lessons[day.key].splice(0))
}

function serializeLesson(lesson) {
  return {
    hour: Number(lesson.hour),
    title: lesson.title?.trim() ?? '',
    professor: lesson.professor?.trim() ?? '',
  }
}

async function handleSave() {
  saving.value = true
  try {
    const schedule = Object.fromEntries(
      DAYS.map((day) => [
        day.key,
        sortedLessons(day.key)
          .map(serializeLesson)
          .filter((lesson) => Number.isFinite(lesson.hour)),
      ])
    )
    await classroomStore.saveClassroom(props.classroom.id, { schedule })
    emit('close')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.field {
  @apply w-full rounded-lg border border-line bg-canvas px-3 py-2 text-sm text-fg placeholder:text-fg-muted focus:outline-none focus-visible:border-fg-muted;
}
</style>
