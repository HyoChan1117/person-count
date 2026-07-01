<template>
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="$emit('close')">
    <div class="bg-white rounded-2xl shadow-xl w-full max-w-2xl mx-4 flex flex-col max-h-[90vh]">
      <!-- 헤더 -->
      <div class="flex items-center justify-between px-6 py-4 border-b border-slate-100">
        <div>
          <h2 class="font-bold text-slate-800">시스템 프롬프트 설정</h2>
          <p class="text-xs text-slate-400 mt-0.5">모든 교실에 공통으로 적용되는 Claude 지침</p>
        </div>
        <button @click="$emit('close')" class="text-slate-400 hover:text-slate-600 text-xl leading-none">✕</button>
      </div>

      <!-- 본문 -->
      <div v-if="store.loading" class="flex-1 flex items-center justify-center py-12 text-slate-400 text-sm">
        불러오는 중...
      </div>

      <div v-else class="flex-1 overflow-y-auto px-6 py-5 space-y-5">
        <!-- 시스템 프롬프트 -->
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1">
            시스템 프롬프트
            <span class="ml-2 text-xs font-normal text-slate-400">Claude의 역할·행동 지침 (비워두면 미사용)</span>
          </label>
          <textarea
            v-model="form.system_prompt"
            rows="4"
            placeholder="예: 당신은 교실 CCTV를 분석하는 AI입니다. 정확한 숫자만 간결하게 답하세요."
            class="textarea w-full"
          />
        </div>

        <!-- 기본 사용자 프롬프트 -->
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1">
            기본 사용자 프롬프트
            <span class="ml-2 text-xs font-normal text-slate-400">교실별 프롬프트가 없을 때 사용</span>
          </label>
          <textarea
            v-model="form.default_user_prompt"
            rows="4"
            placeholder="예: 이 이미지에서 의자에 앉아있는 사람이 몇 명인지 숫자만 답하세요."
            class="textarea w-full"
          />
        </div>

      </div>

      <!-- 푸터 -->
      <div class="flex gap-2 justify-end px-6 py-4 border-t border-slate-100">
        <button @click="$emit('close')" class="btn-ghost">취소</button>
        <button @click="handleSave" :disabled="store.saving" class="btn-primary">
          {{ store.saving ? '저장 중...' : '저장' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { usePromptStore } from '@/stores/promptStore.js'

const emit = defineEmits(['close'])
const store = usePromptStore()

const form = ref({ system_prompt: '', default_user_prompt: '' })

onMounted(async () => {
  await store.fetch()
  form.value = { ...store.config }
})

watch(() => store.config, (val) => {
  form.value = { ...val }
}, { deep: true })

async function handleSave() {
  await store.save(form.value)
  emit('close')
}
</script>

<style scoped>
.textarea {
  @apply border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400 resize-none font-mono;
}
.btn-primary {
  @apply bg-blue-600 text-white text-sm px-5 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 transition;
}
.btn-ghost {
  @apply bg-slate-100 text-slate-700 text-sm px-5 py-2 rounded-lg hover:bg-slate-200 transition;
}
</style>
