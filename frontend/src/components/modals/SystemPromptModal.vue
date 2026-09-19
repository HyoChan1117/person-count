<template>
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="$emit('close')">
    <div class="bg-white dark:bg-neutral-900 rounded-2xl shadow-xl w-full max-w-2xl mx-4 flex flex-col max-h-[90vh]">
      <!-- 헤더 -->
      <div class="flex items-center justify-between px-6 py-4 border-b border-neutral-100 dark:border-neutral-800">
        <div>
          <h2 class="font-bold text-neutral-800 dark:text-neutral-100">시스템 프롬프트 설정</h2>
          <p class="text-xs text-neutral-400 dark:text-neutral-600 mt-0.5">모든 교실에 공통으로 적용되는 Claude 지침</p>
        </div>
        <button @click="$emit('close')" class="text-neutral-400 dark:text-neutral-600 hover:text-neutral-600 text-xl leading-none">✕</button>
      </div>

      <!-- 본문 -->
      <div v-if="loadState === 'loading'" class="flex-1 flex items-center justify-center py-12 text-neutral-400 dark:text-neutral-600 text-sm">
        불러오는 중...
      </div>

      <!-- 조회에 실패한 채 저장하면 서버의 프롬프트가 빈 값으로 덮어써지므로, 실패하면 폼을 열지 않는다 -->
      <div v-else-if="loadState === 'error'" role="alert" class="flex-1 flex flex-col items-center justify-center gap-3 px-6 py-12 text-center">
        <p class="text-sm text-red-600 dark:text-red-400">프롬프트를 불러오지 못했습니다.</p>
        <p class="text-xs text-neutral-500 dark:text-neutral-400 break-all">{{ loadError }}</p>
        <button type="button" class="btn-ghost" @click="load">다시 불러오기</button>
      </div>

      <div v-else class="flex-1 overflow-y-auto px-6 py-5 space-y-5">
        <!-- 시스템 프롬프트 -->
        <div>
          <label class="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-1">
            시스템 프롬프트
            <span class="ml-2 text-xs font-normal text-neutral-400 dark:text-neutral-600">Claude의 역할·행동 지침 (비워두면 미사용)</span>
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
          <label class="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-1">
            기본 사용자 프롬프트
            <span class="ml-2 text-xs font-normal text-neutral-400 dark:text-neutral-600">교실별 프롬프트가 없을 때 사용</span>
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
      <p v-if="saveError" role="alert" class="px-6 pb-2 text-sm text-red-600 dark:text-red-400">저장하지 못했습니다: {{ saveError }}</p>
      <div class="flex gap-2 justify-end px-6 py-4 border-t border-neutral-100 dark:border-neutral-800">
        <button @click="$emit('close')" class="btn-ghost">취소</button>
        <button @click="handleSave" :disabled="loadState !== 'ready' || store.saving" class="btn-primary">
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

// 'loading' → 'ready' | 'error'. 저장은 'ready'일 때만 가능하다.
const loadState = ref('loading')
const loadError = ref('')
const saveError = ref('')

async function load() {
  loadState.value = 'loading'
  loadError.value = ''
  try {
    await store.fetch()
    form.value = { ...store.config }
    loadState.value = 'ready'
  } catch (e) {
    loadError.value = e.response?.data?.detail ?? e.message
    loadState.value = 'error'
  }
}

onMounted(load)

watch(() => store.config, (val) => {
  form.value = { ...val }
}, { deep: true })

async function handleSave() {
  if (loadState.value !== 'ready') return
  saveError.value = ''
  try {
    await store.save(form.value)
    emit('close')
  } catch (e) {
    saveError.value = e.response?.data?.detail ?? e.message
  }
}
</script>

<style scoped>
.textarea {
  @apply border border-neutral-200 dark:border-neutral-800 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400 resize-none font-mono;
}
.btn-primary {
  @apply bg-blue-600 text-white text-sm px-5 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 transition;
}
.btn-ghost {
  @apply bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300 text-sm px-5 py-2 rounded-lg hover:bg-neutral-200 dark:hover:bg-neutral-600 transition;
}
</style>
