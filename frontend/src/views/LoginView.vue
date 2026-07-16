<template>
  <div class="min-h-screen flex items-center justify-center bg-slate-100">
    <div class="bg-white rounded-2xl shadow-lg p-10 flex flex-col items-center gap-6 w-full max-w-sm">
      <div class="text-4xl">📹</div>
      <h1 class="text-xl font-bold text-slate-800">교실 인원 카운트</h1>

      <div v-if="errorMsg" class="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-4 py-2 text-center w-full">
        {{ errorMsg }}
      </div>

      <a
        :href="googleLoginUrl"
        class="flex items-center gap-3 px-5 py-3 border border-slate-300 rounded-xl hover:bg-slate-50 transition text-sm font-medium text-slate-700 w-full justify-center"
      >
        <svg class="w-4 h-4" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
          <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
          <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
          <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z" fill="#FBBC05"/>
          <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
        </svg>
        Google로 로그인
      </a>

      <p class="text-xs text-slate-400 text-center">
        @g.yju.ac.kr / @yju.ac.kr 계정으로만 접근 가능합니다
      </p>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || window.location.origin
const googleLoginUrl = `${BACKEND_URL}/auth/google/login`

const errorMessages = {
  unauthorized_domain: '@yju.ac.kr 이메일만 로그인 가능합니다.',
  access_denied: '로그인을 취소했습니다.',
  auth_failed: '인증에 실패했습니다. 다시 시도해 주세요.',
}

const errorMsg = computed(() => errorMessages[route.query.error] || '')

onMounted(() => {
  const token = route.query.token
  if (token) {
    auth.setToken(token)
    router.replace('/')
  }
})
</script>
