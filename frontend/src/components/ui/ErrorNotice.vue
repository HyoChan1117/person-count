<template>
  <div
    role="alert"
    class="flex items-start gap-3"
    :class="legacy
      ? 'rounded-xl border border-red-200 dark:border-red-500/30 bg-red-50 dark:bg-red-500/10 px-4 py-3 text-red-700 dark:text-red-300'
      : 'rounded-card border border-line bg-card px-card py-gutter text-fg'"
  >
    <div class="min-w-0 flex-1">
      <p class="font-semibold" :class="legacy ? 'text-sm' : ''">{{ title }}</p>
      <p v-if="message" class="mt-0.5 break-words" :class="legacy ? 'text-xs opacity-80' : 'text-sm text-fg-muted'">{{ message }}</p>
    </div>
    <button
      v-if="retryable"
      type="button"
      class="shrink-0 rounded-lg border px-3 py-1.5 text-sm font-medium transition-colors focus-visible:outline focus-visible:outline-2"
      :class="legacy
        ? 'border-red-300 dark:border-red-500/40 text-xs hover:bg-red-100 dark:hover:bg-red-500/20 focus-visible:outline-red-400'
        : 'border-line text-fg hover:border-fg-muted/60 focus-visible:outline-fg-muted'"
      @click="emit('retry')"
    >{{ retryLabel }}</button>
  </div>
</template>

<script setup>
// 조회 실패 안내. 상태색(경고/판정 불가 등)은 다른 용도로 쓸 수 없어 토큰형은 중립색만 쓰고,
// 리디자인 전 화면(legacy)은 그 화면들이 이미 쓰는 빨간 박스 모양을 따른다.
defineProps({
  message: { type: String, default: '' },
  title: { type: String, default: '불러오지 못했습니다' },
  legacy: { type: Boolean, default: false },
  retryable: { type: Boolean, default: true },
  retryLabel: { type: String, default: '다시 시도' },
})
const emit = defineEmits(['retry'])
</script>
