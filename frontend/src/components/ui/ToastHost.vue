<template>
  <!-- 오른쪽 아래에 쌓이는 알림. 화면을 막지 않고 자동으로 사라진다.
       경고색(빨강)은 "미등록 인물" 전용이라 오류에도 쓰지 않는다 — 종류는 아이콘과 문구로 구분하고 색은 중립 톤을 쓴다. -->
  <div class="pointer-events-none fixed bottom-6 right-6 z-[60] flex w-[26rem] max-w-[calc(100vw-3rem)] flex-col gap-3">
    <div
      v-for="t in toasts"
      :key="t.id"
      :role="t.type === 'error' ? 'alert' : 'status'"
      class="pointer-events-auto flex items-start gap-3 rounded-card border border-l-[3px] border-line border-l-fg bg-card px-4 py-3 text-fg shadow-card"
    >
      <NavIcon :name="ICONS[t.type]" :size="20" class="mt-0.5" />
      <!-- 한글은 단어 단위로만 줄바꿈한다(keep-all). 안 그러면 "실패했/습니다"처럼 단어 중간에서 끊긴다 -->
      <div class="min-w-0 flex-1 [word-break:keep-all]">
        <p class="text-base font-semibold leading-snug">{{ t.title }}</p>
        <p v-if="t.detail" class="mt-0.5 text-sm text-fg-muted">{{ t.detail }}</p>
      </div>
      <button
        v-if="t.action"
        type="button"
        class="shrink-0 rounded-lg border border-line px-3 py-1.5 text-sm font-medium text-fg-muted transition-colors hover:border-fg-muted/60 hover:text-fg focus-visible:outline focus-visible:outline-2 focus-visible:outline-fg-muted"
        @click="run(t)"
      >{{ t.action.label }}</button>
      <button
        type="button"
        class="shrink-0 rounded-md p-1 text-fg-muted transition-colors hover:text-fg focus-visible:outline focus-visible:outline-2 focus-visible:outline-fg-muted"
        aria-label="알림 닫기"
        @click="dismiss(t.id)"
      ><NavIcon name="close" :size="16" /></button>
    </div>
  </div>
</template>

<script setup>
import NavIcon from '@/components/ui/NavIcon.vue'
import { useToast } from '@/composables/useToast'

const { toasts, dismiss } = useToast()

const ICONS = { success: 'check', info: 'info', error: 'warn' }

// 다시 시도 같은 동작을 실행하고 알림은 닫는다
function run(t) {
  dismiss(t.id)
  t.action.onClick()
}
</script>
