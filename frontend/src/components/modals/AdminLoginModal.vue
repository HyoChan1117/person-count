<template>
  <div class="ds-root fixed inset-0 z-50 flex items-center justify-center p-4">
    <div class="w-full max-w-sm rounded-card border border-line bg-card p-card shadow-xl">
      <div class="mb-card">
        <p class="text-xs font-semibold uppercase tracking-wide text-fg-muted">관리자</p>
        <h2 class="mt-1 text-xl font-bold text-fg">교실 인원 카운트</h2>
        <p class="mt-1 text-sm text-fg-muted">관리자 로그인이 필요합니다.</p>
      </div>
      <form class="space-y-3" @submit.prevent="submit">
        <input
          v-model="password"
          type="password"
          autofocus
          required
          class="input w-full"
          placeholder="비밀번호"
        />
        <p v-if="errorMsg" class="text-xs text-state-alert">{{ errorMsg }}</p>
        <button type="submit" class="btn-primary w-full" :disabled="loading">
          {{ loading ? '로그인 중...' : '로그인' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useAuthStore } from '@/stores/authStore'

const auth = useAuthStore()

const password = ref('')
const errorMsg = ref('')
const loading = ref(false)

async function submit() {
  loading.value = true
  errorMsg.value = ''
  try {
    await auth.login(password.value)
  } catch {
    errorMsg.value = '비밀번호가 일치하지 않습니다.'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.input {
  @apply rounded-lg border border-line bg-canvas px-3 py-2.5 text-sm text-fg placeholder:text-fg-muted focus:outline-none focus-visible:border-fg-muted;
}

.btn-primary {
  @apply rounded-lg bg-fg px-4 py-2.5 text-sm font-semibold text-canvas transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50;
}
</style>
