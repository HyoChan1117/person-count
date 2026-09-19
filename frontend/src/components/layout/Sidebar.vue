<template>
  <aside class="w-60 shrink-0 h-screen bg-white dark:bg-neutral-950 border-r border-neutral-200 dark:border-neutral-800 flex flex-col">
    <!-- 브랜드 -->
    <div class="h-16 flex items-center px-5 border-b border-neutral-100 dark:border-neutral-800 shrink-0">
      <router-link to="/" class="flex items-center gap-2 font-bold text-neutral-900 dark:text-neutral-100 text-sm leading-tight">
        <span class="text-lg">📹</span>
        교실 인원 카운트
      </router-link>
    </div>

    <!-- 내비게이션 -->
    <nav class="flex-1 overflow-y-auto p-3 space-y-0.5">
      <router-link
        to="/"
        class="flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm text-neutral-600 dark:text-neutral-400 hover:bg-neutral-100 dark:hover:bg-neutral-900 transition"
        active-class="!bg-violet-50 dark:!bg-violet-500/10 !text-violet-700 dark:!text-violet-400 font-medium"
      >
        <span class="text-base">🏠</span> 홈
      </router-link>

      <div
        @mouseenter="hovered = 'seat'"
        @mouseleave="hovered = null"
      >
        <router-link
          to="/classrooms"
          class="flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm text-neutral-600 dark:text-neutral-400 hover:bg-neutral-100 dark:hover:bg-neutral-900 transition"
          active-class="!bg-violet-50 dark:!bg-violet-500/10 !text-violet-700 dark:!text-violet-400 font-medium"
        >
          <span class="text-base">🪑</span> 좌석 확인
        </router-link>

        <div v-show="hovered === 'seat'" class="pl-6 py-1 space-y-0.5">
          <button
            v-for="item in seatMenu"
            :key="item.action"
            @click="goSeat(item.action)"
            class="w-full flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm text-neutral-500 dark:text-neutral-500 hover:bg-neutral-100 dark:hover:bg-neutral-900 hover:text-neutral-800 dark:hover:text-neutral-200 transition text-left"
          >
            <span class="text-sm">{{ item.icon }}</span> {{ item.label }}
          </button>
        </div>
      </div>

      <div
        @mouseenter="hovered = 'face'"
        @mouseleave="hovered = null"
      >
        <router-link
          to="/face"
          class="flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm text-neutral-600 dark:text-neutral-400 hover:bg-neutral-100 dark:hover:bg-neutral-900 transition"
          active-class="!bg-violet-50 dark:!bg-violet-500/10 !text-violet-700 dark:!text-violet-400 font-medium"
        >
          <span class="text-base">🙂</span> 얼굴 인식
        </router-link>

        <div v-show="hovered === 'face'" class="pl-6 py-1 space-y-0.5">
          <button
            v-for="item in faceMenu"
            :key="item.action"
            @click="goFace(item.action)"
            class="w-full flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm text-neutral-500 dark:text-neutral-500 hover:bg-neutral-100 dark:hover:bg-neutral-900 hover:text-neutral-800 dark:hover:text-neutral-200 transition text-left"
          >
            <span class="text-sm">{{ item.icon }}</span> {{ item.label }}
          </button>
        </div>
      </div>

      <button
        @click="showPromptModal = true"
        class="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm text-neutral-600 dark:text-neutral-400 hover:bg-neutral-100 dark:hover:bg-neutral-900 transition text-left"
      >
        <span class="text-base">⚙️</span> 시스템 프롬프트
      </button>
    </nav>

    <!-- 사용자 / 관리자 -->
    <div class="p-3 border-t border-neutral-100 dark:border-neutral-800 shrink-0 space-y-2">
      <button
        @click="theme.toggle()"
        class="w-full flex items-center justify-between px-2 py-2 rounded-lg text-xs text-neutral-500 dark:text-neutral-400 hover:bg-neutral-100 dark:hover:bg-neutral-900 transition"
      >
        <span class="flex items-center gap-2">{{ theme.mode === 'dark' ? '🌙' : '☀️' }} {{ theme.mode === 'dark' ? '다크 모드' : '라이트 모드' }}</span>
        <span class="text-neutral-300 dark:text-neutral-600">전환</span>
      </button>
      <div class="flex items-center justify-between gap-2 px-2 py-2 rounded-lg">
        <span class="text-xs bg-emerald-50 dark:bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-500/20 px-2.5 py-1 rounded-full font-medium shrink-0">🔓 관리자 모드</span>
        <button
          @click="auth.logout()"
          class="text-xs text-neutral-400 dark:text-neutral-500 hover:text-red-500 dark:hover:text-red-400 transition"
          title="로그아웃"
        >로그아웃</button>
      </div>
    </div>
  </aside>

  <SystemPromptModal v-if="showPromptModal" @close="showPromptModal = false" />
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import SystemPromptModal from '@/components/modals/SystemPromptModal.vue'
import { useAuthStore } from '@/stores/authStore'
import { useThemeStore } from '@/stores/themeStore'
import { SEAT_ACTIONS, FACE_ACTIONS } from '@/constants/navActions'

const showPromptModal = ref(false)
const auth = useAuthStore()
const theme = useThemeStore()
const router = useRouter()
const hovered = ref(null)

const seatMenu = SEAT_ACTIONS.map(({ action, icon, label }) => ({ action, icon, label }))

// '인물 등록'은 장소를 먼저 고를 필요 없이 바로 이동하는 전역 기능이라
// FACE_ACTIONS(선택 모드용)에는 없고 사이드바 메뉴에만 추가한다.
const faceMenu = [
  ...FACE_ACTIONS.map(({ action, icon, label }) => ({ action, icon, label })),
  { action: 'people', icon: '👤', label: '인물 등록', direct: '/face/people' },
]

function goSeat(action) {
  hovered.value = null
  router.push({ path: '/classrooms', query: { action } })
}

function goFace(action) {
  hovered.value = null
  const item = faceMenu.find(m => m.action === action)
  if (item?.direct) {
    router.push(item.direct)
    return
  }
  router.push({ path: '/face', query: { action } })
}
</script>
