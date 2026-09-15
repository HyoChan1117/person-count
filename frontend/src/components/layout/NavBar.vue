<template>
  <nav class="h-16 bg-white border-b border-slate-200 flex items-center px-6 gap-1.5 shrink-0">
    <router-link to="/classrooms" class="flex items-center gap-1.5 font-bold text-base text-slate-800 mr-3">
      📹 교실 인원 카운트
    </router-link>
    <router-link
      to="/classrooms"
      class="text-base px-3.5 py-2 rounded-full text-slate-500 hover:bg-slate-100 hover:text-slate-700 transition"
      active-class="bg-blue-50 text-blue-600 font-medium"
    >
      교실 목록
    </router-link>

    <button
      @click="showPromptModal = true"
      class="ml-auto text-sm text-slate-500 hover:bg-slate-100 hover:text-slate-700 transition flex items-center gap-1 px-3.5 py-2 rounded-full"
    >
      ⚙ 시스템 프롬프트
    </button>

    <div class="flex items-center gap-2 ml-2 pl-4 border-l border-slate-200">
      <span class="text-sm bg-emerald-50 text-emerald-700 border border-emerald-200 px-3 py-1.5 rounded-full font-medium">🔓 관리자 모드</span>
      <button
        @click="auth.logout()"
        class="text-sm text-slate-400 hover:text-red-500 transition ml-1 px-2.5 py-1.5"
        title="로그아웃"
      >
        로그아웃
      </button>
    </div>
  </nav>

  <SystemPromptModal v-if="showPromptModal" @close="showPromptModal = false" />
</template>

<script setup>
import { ref } from 'vue'
import SystemPromptModal from '@/components/modals/SystemPromptModal.vue'
import { useAuthStore } from '@/stores/authStore'

const showPromptModal = ref(false)
const auth = useAuthStore()
</script>
