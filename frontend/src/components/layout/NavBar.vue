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
  </nav>

  <SystemPromptModal v-if="showPromptModal" @close="showPromptModal = false" />
</template>

<script setup>
import { ref } from 'vue'
import SystemPromptModal from '@/components/modals/SystemPromptModal.vue'

const showPromptModal = ref(false)
</script>
