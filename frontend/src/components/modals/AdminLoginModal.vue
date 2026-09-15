<template>
  <div class="fixed inset-0 bg-slate-50 flex items-center justify-center z-50">
    <div class="bg-white rounded-2xl p-6 w-80 shadow-xl">
      <h2 class="font-bold text-slate-800 mb-1">📹 교실 인원 카운트</h2>
      <p class="text-sm text-slate-500 mb-4">관리자 로그인이 필요합니다.</p>
      <form @submit.prevent="submit">
        <input
          v-model="password"
          type="password"
          autofocus
          required
          class="input w-full mb-2"
          placeholder="비밀번호"
        />
        <p v-if="errorMsg" class="text-xs text-red-600 mb-2">{{ errorMsg }}</p>
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
  @apply border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400;
}
.btn-primary {
  @apply bg-blue-600 text-white text-sm px-4 py-2 rounded-lg hover:bg-blue-700 transition disabled:opacity-50;
}
</style>
