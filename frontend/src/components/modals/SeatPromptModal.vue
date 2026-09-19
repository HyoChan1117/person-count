<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/55 p-4" @click.self="emit('close')">
    <div class="ds-text flex max-h-[90vh] w-full max-w-xl flex-col overflow-hidden rounded-card border border-line bg-card shadow-xl">
      <div class="flex items-start justify-between gap-4 border-b border-line px-card py-5">
        <div>
          <p class="text-xs font-semibold uppercase tracking-wide text-fg-muted">AI 분석 설정</p>
          <h2 class="mt-1 text-xl font-bold text-fg">YOLO 설정</h2>
          <p class="mt-1 text-sm text-fg-muted">{{ classroom.name }}의 모델과 감지 임계값을 설정하세요.</p>
        </div>
        <button type="button" class="icon-button" aria-label="닫기" @click="emit('close')">×</button>
      </div>

      <div class="flex-1 space-y-6 overflow-y-auto px-card py-5">
        <section class="space-y-3">
          <h3 class="section-title">YOLO 감지 모델</h3>
          <div class="grid gap-2 sm:grid-cols-2">
            <label
              v-for="opt in MODEL_OPTIONS"
              :key="opt.value"
              class="model-option"
              :class="{ 'model-option--selected': selectedModel === opt.value }"
            >
              <input v-model="selectedModel" type="radio" :value="opt.value" class="sr-only" />
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
              <button type="button" class="reset-link" @click="confThreshold = 0.30">기본값 0.30</button>
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
      </div>

      <div class="flex items-center justify-end gap-2 border-t border-line bg-canvas px-card py-4">
        <button type="button" class="btn-ghost" @click="emit('close')">취소</button>
        <button type="button" class="btn-primary" :disabled="saving" @click="handleSave">
          {{ saving ? '저장 중...' : '저장' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useClassroomStore } from '@/stores/classroomStore.js'

const MODEL_OPTIONS = [
  { value: 'yolo26x-pose', label: 'YOLO26x-pose', desc: '강의실 머리와 몸 전체 감지 (고정밀)' },
]

const props = defineProps({
  classroom: { type: Object, required: true },
})
const emit = defineEmits(['close'])

const classroomStore = useClassroomStore()
const selectedModel = ref(props.classroom.yolo_model ?? 'yolo26x-pose')
const confThreshold = ref(props.classroom.conf_threshold ?? 0.30)
const saving = ref(false)

async function handleSave() {
  saving.value = true
  try {
    await classroomStore.saveClassroom(props.classroom.id, {
      yolo_model: selectedModel.value,
      conf_threshold: confThreshold.value,
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

.model-option {
  @apply cursor-pointer rounded-lg border border-line bg-card p-3 transition-colors hover:bg-line/40;
}

.model-option--selected {
  @apply !border-slate-400 !bg-slate-100/70 dark:!border-slate-500 dark:!bg-slate-800/70;
}

.reset-link {
  @apply text-xs font-medium text-fg-muted underline underline-offset-2 transition-colors hover:text-fg;
}

.btn-primary {
  @apply rounded-lg !bg-slate-900 px-5 py-2.5 text-sm font-semibold !text-white transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40 dark:!bg-slate-100 dark:!text-slate-950;
}

.btn-ghost {
  @apply rounded-lg border border-line px-5 py-2.5 text-sm font-medium text-fg-muted transition-colors hover:bg-line/40 hover:text-fg;
}
</style>
