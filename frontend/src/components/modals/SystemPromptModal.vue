<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/55 p-4" @click.self="emit('close')">
    <div class="ds-text flex max-h-[90vh] w-full max-w-2xl flex-col overflow-hidden rounded-card border border-line bg-card shadow-xl">
      <div class="flex items-start justify-between gap-4 border-b border-line px-card py-5">
        <div>
          <p class="text-xs font-semibold uppercase tracking-wide text-fg-muted">프롬프트</p>
          <h2 class="mt-1 text-xl font-bold text-fg">시스템 프롬프트 설정</h2>
          <p class="mt-1 text-sm text-fg-muted">모든 교실에 공통으로 적용되는 Claude 지침입니다.</p>
        </div>
        <button type="button" class="icon-button" aria-label="닫기" @click="emit('close')">×</button>
      </div>

      <div v-if="loadState === 'loading'" class="flex flex-1 items-center justify-center py-16 text-sm text-fg-muted">
        불러오는 중...
      </div>

      <div v-else-if="loadState === 'error'" role="alert" class="flex flex-1 flex-col items-center justify-center gap-3 px-card py-16 text-center">
        <p class="text-sm font-medium text-state-alert">프롬프트를 불러오지 못했습니다.</p>
        <p class="break-all text-xs text-fg-muted">{{ loadError }}</p>
        <button type="button" class="btn-ghost" @click="load">다시 불러오기</button>
      </div>

      <div v-else class="flex-1 space-y-5 overflow-y-auto px-card py-5">
        <label class="block">
          <span class="text-sm font-semibold text-fg">시스템 프롬프트</span>
          <span class="ml-2 text-xs font-normal text-fg-muted">Claude의 역할과 행동 지침</span>
          <textarea
            v-model="form.system_prompt"
            rows="4"
            placeholder="예: 당신은 교실 CCTV를 분석하는 AI입니다. 정확한 숫자만 간결하게 답하세요."
            class="textarea mt-2 w-full"
          />
        </label>

        <label class="block">
          <span class="text-sm font-semibold text-fg">기본 사용자 프롬프트</span>
          <span class="ml-2 text-xs font-normal text-fg-muted">교실별 프롬프트가 없을 때 사용</span>
          <textarea
            v-model="form.default_user_prompt"
            rows="4"
            placeholder="예: 이 이미지에서 좌석에 앉아있는 사람이 몇 명인지 숫자만 답하세요."
            class="textarea mt-2 w-full"
          />
        </label>
      </div>

      <p v-if="saveError" role="alert" class="px-card pb-2 text-sm text-state-alert">저장하지 못했습니다: {{ saveError }}</p>
      <div class="flex justify-end gap-2 border-t border-line bg-canvas px-card py-4">
        <button type="button" class="btn-ghost" @click="emit('close')">취소</button>
        <button type="button" class="btn-primary" :disabled="loadState !== 'ready' || store.saving" @click="handleSave">
          {{ store.saving ? '저장 중...' : '저장' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue'
import { usePromptStore } from '@/stores/promptStore.js'

const emit = defineEmits(['close'])
const store = usePromptStore()

const form = ref({ system_prompt: '', default_user_prompt: '' })
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
.icon-button {
  @apply grid h-9 w-9 place-items-center rounded-lg border border-transparent text-2xl leading-none text-fg-muted transition-colors hover:border-line hover:bg-line/40 hover:text-fg;
}

.textarea {
  @apply resize-none rounded-lg border border-line bg-canvas px-3 py-2.5 font-mono text-sm leading-6 text-fg placeholder:text-fg-muted focus:outline-none focus-visible:border-fg-muted;
}

.btn-primary {
  @apply rounded-lg bg-fg px-5 py-2.5 text-sm font-semibold text-canvas transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50;
}

.btn-ghost {
  @apply rounded-lg border border-line px-5 py-2.5 text-sm font-medium text-fg-muted transition-colors hover:bg-line/40 hover:text-fg;
}
</style>
