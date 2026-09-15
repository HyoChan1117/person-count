<template>
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="$emit('close')">
    <div class="bg-white rounded-2xl shadow-xl w-full max-w-xl mx-4 flex flex-col max-h-[90vh]">
      <!-- 헤더 -->
      <div class="flex items-center justify-between px-6 py-4 border-b border-slate-100">
        <div>
          <h2 class="font-bold text-slate-800">YOLO+LLM 설정 — {{ classroom.name }}</h2>
          <p class="text-xs text-slate-400 mt-0.5">모델, 임계값, AI 카운팅 지침을 설정하세요</p>
        </div>
        <button @click="$emit('close')" class="text-slate-400 hover:text-slate-600 text-xl leading-none">✕</button>
      </div>

      <!-- 본문 -->
      <div class="flex-1 overflow-y-auto px-6 py-5 space-y-5">

        <!-- YOLO 모델 선택 -->
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-2">YOLO 감지 모델</label>
          <div class="grid grid-cols-2 gap-2">
            <label
              v-for="opt in YOLO_MODEL_OPTIONS"
              :key="opt.value"
              class="model-option"
              :class="{ 'model-option--selected': selectedYoloModel === opt.value }"
            >
              <input type="radio" :value="opt.value" v-model="selectedYoloModel" class="sr-only" />
              <div class="font-medium text-sm">{{ opt.label }}</div>
              <div class="text-[11px] text-slate-400 mt-0.5">{{ opt.desc }}</div>
            </label>
          </div>
        </div>

        <!-- LLM 모델 선택 -->
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-2">LLM 모델</label>
          <div class="grid grid-cols-2 gap-2">
            <label
              v-for="opt in LLM_MODEL_OPTIONS"
              :key="opt.value"
              class="model-option"
              :class="{ 'model-option--selected': selectedLlmModel === opt.value }"
            >
              <input type="radio" :value="opt.value" v-model="selectedLlmModel" class="sr-only" />
              <div class="font-medium text-sm">{{ opt.label }}</div>
              <div class="text-[11px] text-slate-400 mt-0.5">{{ opt.desc }}</div>
            </label>
          </div>
        </div>

        <!-- YOLO 감지 임계값 -->
        <div>
          <div class="flex items-center justify-between mb-1.5">
            <label class="text-sm font-medium text-slate-700">YOLO 감지 임계값</label>
            <div class="flex items-center gap-2">
              <span class="text-sm font-mono font-semibold text-blue-600">{{ confThreshold.toFixed(2) }}</span>
              <button
                @click="confThreshold = 0.35"
                class="text-xs text-slate-400 hover:text-slate-600 underline underline-offset-2"
              >기본값 (0.35)</button>
            </div>
          </div>
          <input
            type="range"
            v-model.number="confThreshold"
            min="0.10" max="0.90" step="0.05"
            class="w-full accent-blue-500"
          />
          <div class="flex justify-between text-[10px] text-slate-400 mt-1">
            <span>0.10 — 민감 (오탐 증가)</span>
            <span>0.90 — 보수적 (미탐 증가)</span>
          </div>
        </div>

        <div class="h-px bg-slate-100" />

        <!-- 카운트 제외 대상 -->
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-2">카운트 제외 대상</label>
          <div class="flex gap-2 mb-2">
            <input
              v-model="exclusionInput"
              @keydown.enter.prevent="addExclusionItem"
              type="text"
              placeholder="예: 모니터 화면 속 사람"
              class="input flex-1"
            />
            <button
              @click="addExclusionItem"
              :disabled="!exclusionInput.trim()"
              class="btn-add"
            >추가</button>
          </div>
          <div v-if="exclusionItems.length" class="flex flex-wrap gap-2 mt-2">
            <span
              v-for="(item, i) in exclusionItems"
              :key="i"
              class="inline-flex items-center gap-1.5 bg-red-50 text-red-700 text-xs px-3 py-1.5 rounded-full"
            >
              {{ item }}
              <button @click="exclusionItems.splice(i, 1)" class="text-red-400 hover:text-red-600 leading-none">✕</button>
            </span>
          </div>
          <p v-else class="text-xs text-slate-400 mt-1">제외 대상이 없습니다. 위에서 항목을 추가하세요.</p>
        </div>

        <!-- 기타 지침 -->
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1">기타 지침 <span class="text-slate-400 font-normal">(선택)</span></label>
          <textarea
            v-model="extraNotes"
            rows="5"
            placeholder="각 사람이 좌석에 앉아 있는지(seated), 서 있는지(standing) 판단하세요."
            class="textarea w-full"
          />
        </div>

        <!-- 기본 프롬프트 미리보기 -->
        <div v-if="promptStore.config.default_user_prompt" class="bg-slate-50 rounded-lg px-4 py-3">
          <p class="text-xs font-medium text-slate-500 mb-1">기본 프롬프트 (위의 지침이 이 뒤에 이어붙여짐)</p>
          <p class="text-xs text-slate-600 whitespace-pre-wrap">{{ promptStore.config.default_user_prompt }}</p>
        </div>

      </div>

      <!-- 푸터 -->
      <div class="flex gap-2 justify-end px-6 py-4 border-t border-slate-100">
        <button v-if="isDirty" @click="resetAll" class="btn-ghost mr-auto">초기화</button>
        <button @click="$emit('close')" class="btn-ghost">취소</button>
        <button @click="handleSave" :disabled="saving" class="btn-primary">
          {{ saving ? '저장 중...' : '저장' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useClassroomStore } from '@/stores/classroomStore.js'
import { usePromptStore } from '@/stores/promptStore.js'

const YOLO_MODEL_OPTIONS = [
  { value: 'yolo26x', label: 'YOLO26x', desc: '강의실 — 사람 몸 감지 (고정밀)' },
]

const LLM_MODEL_OPTIONS = [
  { value: 'claude-sonnet-5', label: 'Sonnet 5', desc: '빠름 / 저비용 (기본값)' },
  { value: 'claude-opus-5',   label: 'Opus 5',   desc: '정확 / 고비용' },
]

const EXCLUSION_HEADER = '# 카운트 제외 대상'
const SEAT_HEADER = '# 카메라별 자릿수'

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


const props = defineProps({
  classroom: { type: Object, required: true },
})
const emit = defineEmits(['close'])

const classroomStore = useClassroomStore()
const promptStore = usePromptStore()

function parsePrompt(text) {
  const result = { exclusions: [], extra: '' }
  if (!text) return result

  let remaining = text

  for (const deadHeader of ['# 카운팅 방식', '# 대표 카메라']) {
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

  const seatIdx = remaining.indexOf(SEAT_HEADER)
  if (seatIdx !== -1) {
    const before = remaining.slice(0, seatIdx).trim()
    const after = remaining.slice(seatIdx + SEAT_HEADER.length)
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
  remaining = excl.rest

  result.extra = remaining

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

const isDirty = computed(() =>
  exclusionItems.value.length > 0 ||
  extraNotes.value.trim()
)

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
    const prompt = serializePrompt(
      exclusionItems.value,
      extraNotes.value,
    ) || null

    await classroomStore.saveClassroom(props.classroom.id, {
      prompt,
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
.input {
  @apply border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400;
}
.textarea {
  @apply border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400 resize-none;
}
.btn-add {
  @apply bg-slate-800 text-white text-sm px-4 py-2 rounded-lg hover:bg-slate-700 disabled:opacity-40 transition;
}
.btn-primary {
  @apply bg-blue-600 text-white text-sm px-5 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 transition;
}
.btn-ghost {
  @apply bg-slate-100 text-slate-700 text-sm px-5 py-2 rounded-lg hover:bg-slate-200 transition;
}
.model-option {
  @apply cursor-pointer border border-slate-200 rounded-xl p-3 transition hover:border-blue-300 hover:bg-blue-50;
}
.model-option--selected {
  @apply border-blue-500 bg-blue-50 ring-1 ring-blue-400;
}
</style>
