<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" @click.self="emit('close')">
    <div class="flex max-h-[90vh] w-full max-w-5xl flex-col rounded-card border border-line bg-card shadow-xl">
      <header class="flex items-start justify-between gap-4 border-b border-line px-card py-4">
        <div>
          <h2 class="text-xl font-semibold text-fg">시간표 설정</h2>
          <p class="mt-1 text-sm text-fg-muted">강의명과 교수명을 입력한 뒤 수업 시간을 표에서 선택하세요.</p>
        </div>
        <button
          type="button"
          class="rounded-md px-2 py-1 text-xl leading-none text-fg-muted transition-colors hover:bg-line/50 hover:text-fg"
          aria-label="닫기"
          @click="emit('close')"
        >x</button>
      </header>

      <div class="min-h-0 flex-1 overflow-auto px-card py-card">
        <section class="mb-card grid grid-cols-[minmax(0,1fr)_minmax(0,1fr)_auto] items-end gap-3 rounded-lg border border-line bg-canvas/40 p-4">
          <label class="space-y-1 text-sm">
            <span class="text-fg-muted">강의명</span>
            <input v-model.trim="draft.title" class="field bg-card" placeholder="예: 컴퓨터비전" />
          </label>
          <label class="space-y-1 text-sm">
            <span class="text-fg-muted">교수명</span>
            <input v-model.trim="draft.professor" class="field bg-card" placeholder="예: 홍길동" />
          </label>
          <button
            type="button"
            class="rounded-lg border border-line px-4 py-2.5 text-sm font-medium text-fg-muted transition-colors hover:bg-line/40 hover:text-fg"
            @click="clearDraft"
          >
            입력 비우기
          </button>
        </section>

        <div class="overflow-x-auto">
          <table class="min-w-full border-separate border-spacing-1">
            <thead>
              <tr>
                <th class="w-20" />
                <th v-for="hour in HOURS" :key="hour" class="px-1 pb-2 text-xs font-medium text-fg-muted">
                  {{ pad(hour) }}
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="day in DAYS" :key="day.key">
                <th class="pr-2 text-right text-sm font-semibold text-fg-muted">{{ day.label }}</th>
                <td v-for="hour in HOURS" :key="hour" class="p-0">
                  <button
                    type="button"
                    class="h-14 w-16 rounded-lg border text-xs transition-colors"
                    :class="cellClass(day.key, hour)"
                    :title="cellTitle(day.key, hour)"
                    @click="toggleCell(day.key, hour)"
                  >
                    <span class="block font-semibold tabular-nums">{{ pad(hour) }}</span>
                    <span v-if="lessonAt(day.key, hour)?.title" class="block truncate px-1 text-[10px]">
                      {{ lessonAt(day.key, hour).title }}
                    </span>
                    <span v-if="lessonAt(day.key, hour)?.professor" class="block truncate px-1 text-[10px] opacity-80">
                      {{ lessonAt(day.key, hour).professor }}
                    </span>
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <section class="mt-card rounded-lg border border-line bg-canvas/40 p-4">
          <div v-if="selectedLesson" class="grid grid-cols-[9rem_minmax(0,1fr)_minmax(0,1fr)_auto] items-end gap-3">
            <div>
              <p class="text-label text-fg-muted">선택 시간</p>
              <p class="mt-1 font-semibold tabular-nums text-fg">{{ selectedDayLabel }} {{ pad(selectedLesson.hour) }}:00</p>
            </div>
            <label class="space-y-1 text-sm">
              <span class="text-fg-muted">강의명</span>
              <input v-model.trim="selectedLesson.title" class="field bg-card" placeholder="강의명" />
            </label>
            <label class="space-y-1 text-sm">
              <span class="text-fg-muted">교수명</span>
              <input v-model.trim="selectedLesson.professor" class="field bg-card" placeholder="교수명" />
            </label>
            <button
              type="button"
              class="rounded-lg border border-state-alert/30 px-4 py-2.5 text-sm font-medium text-state-alert transition-colors hover:bg-state-alert/10"
              @click="removeSelected"
            >
              선택 해제
            </button>
          </div>
          <p v-else class="text-sm text-fg-muted">
            시간을 선택하면 위 입력값으로 강의가 등록됩니다. 등록된 칸을 다시 선택하면 아래에서 내용을 수정할 수 있습니다.
          </p>
        </section>
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
import { computed, reactive, ref } from 'vue'
import { useClassroomStore } from '@/stores/classroomStore.js'

const DAYS = [
  { key: 'mon', label: '월' },
  { key: 'tue', label: '화' },
  { key: 'wed', label: '수' },
  { key: 'thu', label: '목' },
  { key: 'fri', label: '금' },
]
const HOURS = Array.from({ length: 10 }, (_, i) => 9 + i)

const props = defineProps({
  classroom: { type: Object, required: true },
})
const emit = defineEmits(['close'])

const classroomStore = useClassroomStore()
const saving = ref(false)
const selectedKey = ref(null)
const draft = reactive({ title: '', professor: '' })

function pad(n) {
  return String(n).padStart(2, '0')
}

function keyOf(dayKey, hour) {
  return `${dayKey}:${hour}`
}

function normalizeLesson(item) {
  if (typeof item === 'number') return { hour: item, title: '', professor: '' }
  return {
    hour: Number(item?.hour),
    title: item?.title ?? item?.name ?? '',
    professor: item?.professor ?? '',
  }
}

const lessons = reactive(Object.fromEntries(
  DAYS.map((day) => [
    day.key,
    Object.fromEntries(
      (props.classroom.schedule?.[day.key] ?? [])
        .map(normalizeLesson)
        .filter((lesson) => Number.isFinite(lesson.hour))
        .map((lesson) => [lesson.hour, lesson])
    ),
  ])
))

function lessonAt(dayKey, hour) {
  return lessons[dayKey][hour] ?? null
}

function toggleCell(dayKey, hour) {
  const current = lessonAt(dayKey, hour)
  if (current && selectedKey.value === keyOf(dayKey, hour)) {
    delete lessons[dayKey][hour]
    selectedKey.value = null
    return
  }

  if (current) {
    current.title = draft.title || current.title
    current.professor = draft.professor || current.professor
  } else {
    lessons[dayKey][hour] = { hour, title: draft.title, professor: draft.professor }
  }
  selectedKey.value = keyOf(dayKey, hour)
}

const selectedLesson = computed(() => {
  if (!selectedKey.value) return null
  const [dayKey, hour] = selectedKey.value.split(':')
  return lessonAt(dayKey, Number(hour))
})

const selectedDayLabel = computed(() => {
  if (!selectedKey.value) return ''
  const [dayKey] = selectedKey.value.split(':')
  return DAYS.find((day) => day.key === dayKey)?.label ?? ''
})

function clearDraft() {
  draft.title = ''
  draft.professor = ''
}

function removeSelected() {
  if (!selectedKey.value) return
  const [dayKey, hour] = selectedKey.value.split(':')
  delete lessons[dayKey][Number(hour)]
  selectedKey.value = null
}

function cellClass(dayKey, hour) {
  const on = !!lessonAt(dayKey, hour)
  const selected = selectedKey.value === keyOf(dayKey, hour)
  if (selected) return 'border-fg bg-line text-fg shadow-sm'
  if (on) return 'border-state-occupied/40 bg-state-occupied/10 text-state-occupied hover:bg-state-occupied/15'
  return 'border-line bg-canvas text-fg-muted hover:bg-line/40 hover:text-fg'
}

function cellTitle(dayKey, hour) {
  const lesson = lessonAt(dayKey, hour)
  if (!lesson) return `${pad(hour)}:00`
  return [lesson.title || `${pad(hour)}:00`, lesson.professor].filter(Boolean).join(' · ')
}

function clearAll() {
  DAYS.forEach((day) => {
    for (const hour of Object.keys(lessons[day.key])) delete lessons[day.key][hour]
  })
  selectedKey.value = null
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
        Object.values(lessons[day.key])
          .map(serializeLesson)
          .sort((a, b) => a.hour - b.hour),
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
  @apply w-full rounded-lg border border-line px-3 py-2 text-sm text-fg placeholder:text-fg-muted focus:outline-none focus-visible:border-fg-muted;
}
</style>
