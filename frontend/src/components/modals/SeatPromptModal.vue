<template>
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="$emit('close')">
    <div class="bg-white rounded-2xl shadow-xl w-full max-w-xl mx-4 flex flex-col max-h-[90vh]">
      <!-- 헤더 -->
      <div class="flex items-center justify-between px-6 py-4 border-b border-slate-100">
        <div>
          <h2 class="font-bold text-slate-800">YOLO 설정 — {{ classroom.name }}</h2>
          <p class="text-xs text-slate-400 mt-0.5">모델 및 감지 임계값을 설정하세요</p>
        </div>
        <button @click="$emit('close')" class="text-slate-400 hover:text-slate-600 text-xl leading-none">✕</button>
      </div>

      <!-- 본문 -->
      <div class="flex-1 overflow-y-auto px-6 py-5 space-y-4">

        <!-- YOLO 모델 선택 -->
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-2">YOLO 감지 모델</label>
          <div class="grid grid-cols-2 gap-2">
            <label
              v-for="opt in MODEL_OPTIONS"
              :key="opt.value"
              class="model-option"
              :class="{ 'model-option--selected': selectedModel === opt.value }"
            >
              <input type="radio" :value="opt.value" v-model="selectedModel" class="sr-only" />
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
              <span class="text-sm font-mono font-semibold text-violet-600">{{ confThreshold.toFixed(2) }}</span>
              <button
                @click="confThreshold = 0.30"
                class="text-xs text-slate-400 hover:text-slate-600 underline underline-offset-2"
              >기본값 (0.30)</button>
            </div>
          </div>
          <input
            type="range"
            v-model.number="confThreshold"
            min="0.10" max="0.90" step="0.05"
            class="w-full accent-violet-500"
          />
          <div class="flex justify-between text-[10px] text-slate-400 mt-1">
            <span>0.10 — 민감 (오탐 증가)</span>
            <span>0.90 — 보수적 (미탐 증가)</span>
          </div>
        </div>

      </div>

      <!-- 푸터 -->
      <div class="flex gap-2 justify-end px-6 py-4 border-t border-slate-100">
        <button @click="$emit('close')" class="btn-ghost">취소</button>
        <button @click="handleSave" :disabled="saving" class="btn-primary">
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
  { value: 'yolo26x-pose', label: 'YOLO26x-pose', desc: '강의실 — 머리+몸 전체 감지 (고정밀)' },
]

const props = defineProps({
  classroom: { type: Object, required: true },
})
const emit = defineEmits(['close'])

const classroomStore = useClassroomStore()
const selectedModel = ref(props.classroom.yolo_model ?? 'yolov8x')
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
.textarea {
  @apply border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-400 resize-none;
}
.btn-primary {
  @apply bg-violet-600 text-white text-sm px-5 py-2 rounded-lg hover:bg-violet-700 disabled:opacity-50 transition;
}
.btn-ghost {
  @apply bg-slate-100 text-slate-700 text-sm px-5 py-2 rounded-lg hover:bg-slate-200 transition;
}
.model-option {
  @apply cursor-pointer border border-slate-200 rounded-xl p-3 transition hover:border-violet-300 hover:bg-violet-50;
}
.model-option--selected {
  @apply border-violet-500 bg-violet-50 ring-1 ring-violet-400;
}
</style>
