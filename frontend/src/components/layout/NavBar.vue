<template>
  <nav class="h-12 bg-slate-900 text-white flex items-center px-4 gap-6 shrink-0">
    <router-link to="/classrooms" class="font-bold text-sm tracking-wide">
      📹 교실 인원 카운트
    </router-link>
    <router-link to="/classrooms" class="text-sm text-slate-400 hover:text-white transition" active-class="text-white">
      교실 목록
    </router-link>

    <button
      @click="showPromptModal = true"
      class="ml-auto text-xs text-slate-400 hover:text-white transition flex items-center gap-1"
    >
      ⚙ 시스템 프롬프트
    </button>

    <div v-if="auth.user" class="flex items-center gap-2 ml-2 pl-4 border-l border-slate-700">
      <img v-if="auth.user.picture" :src="auth.user.picture" class="w-6 h-6 rounded-full" referrerpolicy="no-referrer" />
      <span class="text-xs text-slate-400">{{ auth.user.name || auth.user.email }}</span>
      <button
        @click="handleLogout"
        class="text-xs text-slate-500 hover:text-red-400 transition ml-1"
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
import { useRouter } from 'vue-router'
import SystemPromptModal from '@/components/modals/SystemPromptModal.vue'
import { useAuthStore } from '@/stores/authStore'

const showPromptModal = ref(false)
const auth = useAuthStore()
const router = useRouter()

function handleLogout() {
  auth.logout()
  router.push('/login')
}
</script>
