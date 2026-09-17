<template>
  <aside class="w-60 shrink-0 h-screen bg-white border-r border-neutral-200 flex flex-col">
    <!-- 브랜드 -->
    <div class="h-16 flex items-center px-5 border-b border-neutral-100 shrink-0">
      <router-link to="/" class="flex items-center gap-2 font-bold text-neutral-900 text-sm leading-tight">
        <span class="text-lg">📹</span>
        교실 인원 카운트
      </router-link>
    </div>

    <!-- 내비게이션 -->
    <nav class="flex-1 overflow-y-auto p-3 space-y-0.5">
      <router-link
        to="/"
        class="flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm text-neutral-600 hover:bg-neutral-100 transition"
        active-class="!bg-violet-50 !text-violet-700 font-medium"
      >
        <span class="text-base">🏠</span> 홈
      </router-link>

      <router-link
        to="/classrooms"
        class="flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm text-neutral-600 hover:bg-neutral-100 transition"
        active-class="!bg-violet-50 !text-violet-700 font-medium"
      >
        <span class="text-base">🪑</span> 좌석 확인
      </router-link>

      <router-link
        to="/face"
        class="flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm text-neutral-600 hover:bg-neutral-100 transition"
        active-class="!bg-violet-50 !text-violet-700 font-medium"
      >
        <span class="text-base">🙂</span> 얼굴 인식
      </router-link>

      <button
        @click="showPromptModal = true"
        class="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm text-neutral-600 hover:bg-neutral-100 transition text-left"
      >
        <span class="text-base">⚙️</span> 시스템 프롬프트
      </button>
    </nav>

    <!-- 사용자 / 관리자 -->
    <div class="p-3 border-t border-neutral-100 shrink-0">
      <div class="flex items-center justify-between gap-2 px-2 py-2 rounded-lg">
        <span class="text-xs bg-emerald-50 text-emerald-700 border border-emerald-200 px-2.5 py-1 rounded-full font-medium shrink-0">🔓 관리자 모드</span>
        <button
          @click="auth.logout()"
          class="text-xs text-neutral-400 hover:text-red-500 transition"
          title="로그아웃"
        >로그아웃</button>
      </div>
    </div>
  </aside>

  <SystemPromptModal v-if="showPromptModal" @close="showPromptModal = false" />
</template>

<script setup>
import { ref } from 'vue'
import SystemPromptModal from '@/components/modals/SystemPromptModal.vue'
import { useAuthStore } from '@/stores/authStore'

const showPromptModal = ref(false)
const auth = useAuthStore()
</script>
