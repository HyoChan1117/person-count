<template>
  <div class="fixed inset-0 bg-neutral-50 dark:bg-neutral-950 flex items-center justify-center z-50">
    <div class="bg-white dark:bg-neutral-900 border border-transparent dark:border-neutral-800 rounded-2xl p-6 w-80 shadow-xl">
      <h2 class="font-bold text-neutral-800 dark:text-neutral-100 mb-1">📹 교실 인원 카운트</h2>
      <p class="text-sm text-neutral-500 dark:text-neutral-400 mb-4">관리자 로그인이 필요합니다.</p>
      <form @submit.prevent="submit">
        <input
          v-model="password"
          type="password"
          autofocus
          required
          class="input w-full mb-2"
          placeholder="비밀번호"
        />
        <p v-if="errorMsg" class="text-xs text-red-600 dark:text-red-400 mb-2">{{ errorMsg }}</p>
        <button type="submit" class="w-full btn-primary mt-2" :disabled="loading">로그인</button>
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
  @apply border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-950 text-neutral-900 dark:text-neutral-100 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-400 dark:focus:ring-violet-500;
}
.btn-primary {
  @apply bg-violet-600 text-white text-sm px-4 py-2 rounded-lg hover:bg-violet-700 transition disabled:opacity-50;
}
</style>
