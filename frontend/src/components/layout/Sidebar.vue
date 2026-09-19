<template>
  <aside class="ds-text flex h-screen w-60 shrink-0 flex-col border-r border-line bg-card">
    <!-- 브랜드: 무엇을 하는 시스템인지 한 줄로 -->
    <router-link
      to="/"
      class="flex h-[4.5rem] shrink-0 items-center gap-3 border-b border-line px-5 focus-visible:outline focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-fg-muted"
    >
      <span class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-line bg-canvas text-fg">
        <NavIcon name="brand" :size="20" />
      </span>
      <span class="min-w-0">
        <span class="block truncate text-base font-semibold leading-tight text-fg">교실 인원 카운트</span>
        <span class="mt-0.5 block truncate text-xs text-fg-muted">좌석 점유 · 얼굴인식 순찰</span>
      </span>
    </router-link>

    <!-- 내비게이션 -->
    <nav class="flex-1 space-y-1 overflow-y-auto p-3" aria-label="주 메뉴">
      <router-link to="/" :class="[ITEM, isHome ? ITEM_ON : ITEM_OFF]" :aria-current="isHome ? 'page' : undefined">
        <span v-if="isHome" :class="BAR" />
        <NavIcon name="home" /> 홈
      </router-link>

      <!-- 하위 메뉴: 현재 위치한 그룹은 항상 펼치고, 그 외에는 hover / 키보드 포커스로 연다 -->
      <div class="group">
        <router-link to="/classrooms" :class="[ITEM, inSeat ? ITEM_ON : ITEM_OFF]" :aria-current="inSeat ? 'true' : undefined">
          <span v-if="inSeat" :class="BAR" />
          <NavIcon name="seats" /> 좌석 확인
        </router-link>
        <ul :class="[SUB, inSeat ? 'block' : 'hidden group-hover:block group-focus-within:block']">
          <li v-for="item in seatMenu" :key="item.action">
            <button type="button" :class="[SUB_ITEM, seatActive === item.action ? SUB_ON : SUB_OFF]" @click="goSeat(item.action)">{{ item.label }}</button>
          </li>
        </ul>
      </div>

      <div class="group">
        <router-link to="/face" :class="[ITEM, inFace ? ITEM_ON : ITEM_OFF]" :aria-current="inFace ? 'true' : undefined">
          <span v-if="inFace" :class="BAR" />
          <NavIcon name="face" /> 얼굴 인식
        </router-link>
        <ul :class="[SUB, inFace ? 'block' : 'hidden group-hover:block group-focus-within:block']">
          <li v-for="item in faceMenu" :key="item.action">
            <button type="button" :class="[SUB_ITEM, faceActive === item.action ? SUB_ON : SUB_OFF]" @click="goFace(item.action)">{{ item.label }}</button>
          </li>
        </ul>
      </div>

    </nav>

    <div class="shrink-0 p-3">
      <button type="button" :class="[ITEM, ITEM_OFF, 'w-full text-left']" @click="showPromptModal = true">
        <NavIcon name="settings" /> 시스템 프롬프트
      </button>
    </div>

    <!-- 테마 / 관리자 -->
    <div class="shrink-0 space-y-3 border-t border-line p-4">
      <div class="grid grid-cols-2 gap-1 rounded-lg border border-line p-1" role="group" aria-label="화면 테마">
        <button
          v-for="opt in THEMES"
          :key="opt.mode"
          type="button"
          :aria-pressed="theme.mode === opt.mode"
          class="flex items-center justify-center gap-1.5 rounded-md py-1.5 text-sm transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-fg-muted"
          :class="theme.mode === opt.mode ? 'bg-line text-fg font-medium' : 'text-fg-muted hover:text-fg'"
          @click="theme.setMode(opt.mode)"
        >
          <NavIcon :name="opt.icon" :size="16" /> {{ opt.label }}
        </button>
      </div>

      <div class="flex items-center justify-between gap-2">
        <span class="inline-flex items-center gap-1.5 rounded-full border border-line px-3 py-1 text-xs text-fg-muted">
          <NavIcon name="lock" :size="14" /> 관리자
        </span>
        <button
          type="button"
          class="rounded-md px-2 py-1 text-sm text-fg-muted transition-colors hover:text-fg focus-visible:outline focus-visible:outline-2 focus-visible:outline-fg-muted"
          @click="auth.logout()"
        >로그아웃</button>
      </div>
    </div>
  </aside>

  <SystemPromptModal v-if="showPromptModal" @close="showPromptModal = false" />
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import SystemPromptModal from '@/components/modals/SystemPromptModal.vue'
import NavIcon from '@/components/ui/NavIcon.vue'
import { useAuthStore } from '@/stores/authStore'
import { useThemeStore } from '@/stores/themeStore'
import { SEAT_ACTIONS, FACE_ACTIONS } from '@/constants/navActions'

// 클래스는 Tailwind가 스캔할 수 있도록 전부 리터럴로 적는다.
const ITEM = 'relative flex items-center gap-3 rounded-lg px-3 py-2.5 text-base transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-fg-muted'
const ITEM_ON = 'bg-line/60 font-medium text-fg'
const ITEM_OFF = 'text-fg-muted hover:bg-line/40 hover:text-fg'
const BAR = 'absolute inset-y-2 left-0 w-0.5 rounded-full bg-fg'
const SUB = 'ml-[1.625rem] mt-0.5 space-y-0.5 border-l border-line pl-3'
const SUB_ITEM = 'w-full rounded-md px-3 py-1.5 text-left text-sm transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-fg-muted'
const SUB_ON = 'font-medium text-fg'
const SUB_OFF = 'text-fg-muted hover:text-fg'

const THEMES = [
  { mode: 'dark', label: '다크', icon: 'moon' },
  { mode: 'light', label: '라이트', icon: 'sun' },
]

const showPromptModal = ref(false)
const auth = useAuthStore()
const theme = useThemeStore()
const route = useRoute()
const router = useRouter()

// 아이콘(이모지)은 목록 화면의 선택 모드가 함께 쓰는 값이라 사이드바에서만 쓰지 않는다.
const seatMenu = SEAT_ACTIONS.map(({ action, label }) => ({ action, label }))

// '인물 등록'은 장소를 먼저 고를 필요 없이 바로 이동하는 전역 기능이라
// FACE_ACTIONS(선택 모드용)에는 없고 사이드바 메뉴에만 추가한다.
const faceMenu = [
  ...FACE_ACTIONS.map(({ action, label }) => ({ action, label })),
  { action: 'people', label: '인물 등록', direct: '/face/people' },
]

// 화면은 서로 다른 라우트 레코드라 router-link의 active-class로는 그룹 소속을 알 수 없다. 경로로 판단한다.
const path = computed(() => route.path)
const isHome = computed(() => path.value === '/')
const inSeat = computed(() => ['/classrooms', '/dashboard', '/monitoring'].some((p) => path.value.startsWith(p)))
const inFace = computed(() => path.value.startsWith('/face'))

const seatActive = computed(() => {
  if (path.value.startsWith('/dashboard')) return 'dashboard'
  if (path.value.startsWith('/monitoring')) return 'monitoring'
  if (path.value.endsWith('/setup')) return 'setup'
  if (path.value.endsWith('/map')) return 'map'
  return null
})

const faceActive = computed(() => {
  if (path.value.startsWith('/face/people')) return 'people'
  if (path.value.endsWith('/camera')) return 'camera'
  if (path.value.endsWith('/zones')) return 'zones'
  if (path.value.endsWith('/monitoring')) return 'monitoring'
  return null
})

function goSeat(action) {
  router.push({ path: '/classrooms', query: { action } })
}

function goFace(action) {
  const item = faceMenu.find((m) => m.action === action)
  if (item?.direct) {
    router.push(item.direct)
    return
  }
  router.push({ path: '/face', query: { action } })
}
</script>
