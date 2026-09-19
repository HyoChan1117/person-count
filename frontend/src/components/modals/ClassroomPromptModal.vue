<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/55 p-4" @click.self="emit('close')">
    <div class="ds-text flex max-h-[90vh] w-full max-w-2xl flex-col overflow-hidden rounded-card border border-line bg-card shadow-xl">
      <div class="flex items-start justify-between gap-4 border-b border-line px-card py-5">
        <div>
          <p class="text-xs font-semibold uppercase tracking-wide text-fg-muted">AI 분석 설정</p>
          <h2 class="mt-1 text-xl font-bold text-fg">YOLO+LLM 설정</h2>
          <p class="mt-1 text-sm text-fg-muted">{{ classroom.name }}의 모델, 임계값, 카운팅 지침을 설정하세요.</p>
        </div>
        <button type="button" class="icon-button" aria-label="닫기" @click="emit('close')">×</button>
      </div>

      <div class="flex-1 space-y-6 overflow-y-auto px-card py-5">
        <section class="space-y-3">
          <h3 class="section-title">YOLO 감지 모델</h3>
          <div class="grid gap-2 sm:grid-cols-2">
            <label
              v-for="opt in YOLO_MODEL_OPTIONS"
              :key="opt.value"
              class="model-option"
              :class="{ 'model-option--selected': selectedYoloModel === opt.value }"
            >
              <input v-model="selectedYoloModel" type="radio" :value="opt.value" class="sr-only" />
              <span class="text-sm font-semibold text-fg">{{ opt.label }}</span>
              <span class="mt-1 block text-xs text-fg-muted">{{ opt.desc }}</span>
            </label>
          </div>
        </section>

        <section class="space-y-3">
          <h3 class="section-title">LLM 모델</h3>
          <div class="grid gap-2 sm:grid-cols-2">
            <label
              v-for="opt in LLM_MODEL_OPTIONS"
              :key="opt.value"
              class="model-option"
              :class="{ 'model-option--selected': selectedLlmModel === opt.value }"
            >
              <input v-model="selectedLlmModel" type="radio" :value="opt.value" class="sr-only" />
              <span class="text-sm font-semibold text-fg">{{ opt.label }}</span>
              <span class="mt-1 block text-xs text-fg-muted">{{ opt.desc }}</span>
            </label>
          </div>
        </section>

        <section class="space-y-2">
          <div class="flex items-center justify-between gap-3">
            <h3 class="section-title">YOLO 감지 임계값</h3>
            <div class="flex items-center gap-2">
              <span class="font-mono text-sm font-semibold text-fg">{{ confThreshold.toFixed(2) }}</span>
              <button type="button" class="reset-link" @click="confThreshold = 0.35">기본값 0.35</button>
            </div>
          </div>
          <input
            v-model.number="confThreshold"
            type="range"
            min="0.10"
            max="0.90"
            step="0.05"
            class="w-full accent-fg"
          />
          <div class="flex justify-between text-[11px] text-fg-muted">
            <span>0.10 민감</span>
            <span>0.90 보수적</span>
          </div>
        </section>

        <div class="h-px bg-line" />

        <section class="space-y-3">
          <h3 class="section-title">카운트 제외 대상</h3>
          <div class="flex gap-2">
            <input
              v-model="exclusionInput"
              type="text"
              class="field flex-1"
              placeholder="예: 모니터 화면 속 사람"
              @keydown.enter.prevent="addExclusionItem"
            />
            <button type="button" class="btn-add" :disabled="!exclusionInput.trim()" @click="addExclusionItem">추가</button>
          </div>
          <div v-if="exclusionItems.length" class="flex flex-wrap gap-2">
            <span v-for="(item, i) in exclusionItems" :key="i" class="chip">
              {{ item }}
              <button type="button" class="text-fg-muted hover:text-fg" aria-label="제외 대상 삭제" @click="exclusionItems.splice(i, 1)">×</button>
            </span>
          </div>
          <p v-else class="text-xs text-fg-muted">제외 대상이 없습니다. 필요하면 위에서 항목을 추가하세요.</p>
        </section>

        <section class="space-y-2">
          <h3 class="section-title">기타 지침 <span class="font-normal text-fg-muted">(선택)</span></h3>
          <textarea
            v-model="extraNotes"
            rows="5"
            class="textarea w-full"
            placeholder="각 사람이 좌석에 앉아 있는지(seated), 서 있는지(standing) 판단하세요."
          />
        </section>

        <section v-if="promptStore.config.default_user_prompt" class="rounded-lg border border-line bg-canvas px-4 py-3">
          <p class="text-xs font-semibold text-fg">기본 프롬프트</p>
          <p class="mt-2 whitespace-pre-wrap text-xs leading-5 text-fg-muted">{{ promptStore.config.default_user_prompt }}</p>
        </section>
      </div>

      <div class="flex items-center justify-end gap-2 border-t border-line bg-canvas px-card py-4">
        <button v-if="isDirty" type="button" class="btn-ghost mr-auto" @click="resetAll">초기화</button>
        <button type="button" class="btn-ghost" @click="emit('close')">취소</button>
        <button type="button" class="btn-primary" :disabled="saving" @click="handleSave">
          {{ saving ? '저장 중...' : '저장' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useClassroomStore } from '@/stores/classroomStore.js'
import { usePromptStore } from '@/stores/promptStore.js'

const YOLO_MODEL_OPTIONS = [
  { value: 'yolo26x', label: 'YOLO26x', desc: '강의실 사람 몸 감지 (고정밀)' },
]

const LLM_MODEL_OPTIONS = [
  { value: 'claude-sonnet-5', label: 'Sonnet 5', desc: '빠름 / 저비용 (기본값)' },
  { value: 'claude-opus-5', label: 'Opus 5', desc: '정확 / 고비용' },
]

const EXCLUSION_HEADER = '# 카운트 제외 대상'
const SEAT_HEADERS = ['# 카메라별 좌석', '# 카메라별 자릿수']

const props = defineProps({
  classroom: { type: Object, required: true },
})
const emit = defineEmits(['close'])

const classroomStore = useClassroomStore()
const promptStore = usePromptStore()

function extractListSection(text, header) {
  const idx = text.indexOf(header)
  if (idx === -1) return { items: [], rest: text }
  const before = text.slice(0, idx).trim()
  const after = text.slice(idx + header.length)
  const lines = after.split('\n')
  const items = []
  const leftover = []
  let inList = true

  for (const line of lines) {
    const trimmed = line.trim()
    if (!trimmed) continue
    if (inList && trimmed.startsWith('- ')) {
      items.push(trimmed.slice(2).trim())
    } else {
      inList = false
      leftover.push(line)
    }
  }

  return { items, rest: [before, ...leftover].filter(Boolean).join('\n').trim() }
}

function parsePrompt(text) {
  const result = { exclusions: [], extra: '' }
  if (!text) return result

  let remaining = text

  for (const deadHeader of ['# 카운트 방식', '# 카운팅 방식', '# 대상 카메라', '# 대표 카메라']) {
    const idx = remaining.indexOf(deadHeader)
    if (idx !== -1) {
      const before = remaining.slice(0, idx).trim()
      const after = remaining.slice(idx + deadHeader.length)
      const lines = after.split('\n')
      const leftover = []
      let inList = true

      for (const line of lines) {
        const trimmed = line.trim()
        if (!trimmed) continue
        if (inList && trimmed.startsWith('- ')) continue
        inList = false
        leftover.push(line)
      }

      remaining = [before, ...leftover].filter(Boolean).join('\n').trim()
    }
  }

  const seatHeader = SEAT_HEADERS.find(header => remaining.includes(header))
  if (seatHeader) {
    const seatIdx = remaining.indexOf(seatHeader)
    const before = remaining.slice(0, seatIdx).trim()
    const after = remaining.slice(seatIdx + seatHeader.length)
    const lines = after.split('\n')
    const leftover = []
    let inList = true

    for (const line of lines) {
      const trimmed = line.trim()
      if (!trimmed) continue
      if (inList && trimmed.startsWith('- ')) continue
      inList = false
      leftover.push(line)
    }

    remaining = [before, ...leftover].filter(Boolean).join('\n').trim()
  }

  const excl = extractListSection(remaining, EXCLUSION_HEADER)
  result.exclusions = excl.items
  result.extra = excl.rest

  return result
}

function serializePrompt(exclusions, extra) {
  const parts = []
  if (exclusions.length) {
    parts.push(EXCLUSION_HEADER)
    exclusions.forEach(item => parts.push(`- ${item}`))
  }
  if (extra.trim()) parts.push(extra.trim())
  return parts.join('\n').trim()
}

const DEFAULT_EXTRA = '각 사람이 좌석에 앉아 있는지(seated), 서 있는지(standing) 판단하세요.'
const parsed = parsePrompt(props.classroom.prompt ?? '')

const selectedYoloModel = ref(props.classroom.yolo_llm_yolo_model ?? 'yolo26x')
const selectedLlmModel = ref(props.classroom.yolo_llm_model ?? 'claude-sonnet-5')
const confThreshold = ref(props.classroom.yolo_llm_conf_threshold ?? 0.35)
const exclusionItems = ref([...parsed.exclusions])
const extraNotes = ref(parsed.extra || DEFAULT_EXTRA)
const exclusionInput = ref('')
const saving = ref(false)

const isDirty = computed(() => exclusionItems.value.length > 0 || extraNotes.value.trim())

function addExclusionItem() {
  const val = exclusionInput.value.trim()
  if (val && !exclusionItems.value.includes(val)) {
    exclusionItems.value.push(val)
  }
  exclusionInput.value = ''
}

function resetAll() {
  exclusionItems.value = []
  extraNotes.value = ''
}

async function handleSave() {
  saving.value = true
  try {
    await classroomStore.saveClassroom(props.classroom.id, {
      prompt: serializePrompt(exclusionItems.value, extraNotes.value) || null,
      yolo_llm_yolo_model: selectedYoloModel.value,
      yolo_llm_model: selectedLlmModel.value,
      yolo_llm_conf_threshold: confThreshold.value,
    })
    emit('close')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.section-title {
  @apply text-sm font-semibold text-fg;
}

.icon-button {
  @apply grid h-9 w-9 place-items-center rounded-lg border border-transparent text-2xl leading-none text-fg-muted transition-colors hover:border-line hover:bg-line/40 hover:text-fg;
}

.field,
.textarea {
  @apply rounded-lg border border-line bg-canvas px-3 py-2.5 text-sm text-fg placeholder:text-fg-muted focus:outline-none focus-visible:border-fg-muted;
}

.textarea {
  @apply resize-none leading-6;
}

.model-option {
  @apply cursor-pointer rounded-lg border border-line bg-card p-3 transition-colors hover:bg-line/40;
}

.model-option--selected {
  @apply !border-slate-400 !bg-slate-100/70 dark:!border-slate-500 dark:!bg-slate-800/70;
}

.chip {
  @apply inline-flex items-center gap-1.5 rounded-full border border-line bg-canvas px-3 py-1.5 text-xs font-medium text-fg;
}

.reset-link {
  @apply text-xs font-medium text-fg-muted underline underline-offset-2 transition-colors hover:text-fg;
}

.btn-add,
.btn-primary {
  @apply rounded-lg !bg-slate-900 px-4 py-2.5 text-sm font-semibold !text-white transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40 dark:!bg-slate-100 dark:!text-slate-950;
}

.btn-primary {
  @apply px-5;
}

.btn-ghost {
  @apply rounded-lg border border-line px-5 py-2.5 text-sm font-medium text-fg-muted transition-colors hover:bg-line/40 hover:text-fg;
}
</style>
