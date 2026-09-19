<template>
  <header class="flex items-end justify-between gap-section">
    <div class="min-w-0">
      <h1 class="text-3xl font-bold tracking-tight text-fg">교실 인원 카운트</h1>
      <!-- 갱신에 실패해 낡은 숫자를 보여 주는 중이면 부제 자리에 알린다(높이는 그대로) -->
      <p v-if="stale" role="status" class="mt-1 flex items-center gap-3 text-lg">
        <span class="rounded-full border border-fg-muted/60 px-3 py-0.5 text-base font-semibold text-fg">데이터가 오래되었습니다</span>
        <span class="truncate text-base text-fg-muted">마지막 정상 갱신 {{ lastOkText }}</span>
        <button type="button" class="shrink-0 rounded-md px-2 py-0.5 text-base text-fg-muted underline underline-offset-4 transition-colors hover:text-fg focus-visible:outline focus-visible:outline-2 focus-visible:outline-fg-muted" @click="emit('refresh')">지금 갱신</button>
      </p>
      <p v-else class="mt-1 text-lg text-fg-muted">CCTV 기반 좌석 점유 + 얼굴인식 순찰 관제</p>
    </div>

    <div class="flex shrink-0 items-center gap-section">
      <div class="text-right">
        <p class="text-label text-fg-muted">마지막 수집</p>
        <p class="text-metric-sm tabular-nums text-fg">{{ lastText }}</p>
      </div>
      <div class="w-56">
        <div class="flex items-baseline justify-between">
          <p class="text-label text-fg-muted">다음 수집까지</p>
          <p class="text-2xl font-semibold tabular-nums text-fg">{{ remainText }}</p>
        </div>
        <div class="mt-2 h-1.5 overflow-hidden rounded-full bg-line">
          <div class="h-full rounded-full bg-fg-muted transition-[width] duration-1000 ease-linear" :style="{ width: `${progress}%` }" />
        </div>
      </div>
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  lastAt: { type: Date, required: true },
  nextInSec: { type: Number, required: true },
  intervalSec: { type: Number, required: true },
  stale: { type: Boolean, default: false },
  lastOkText: { type: String, default: '' },
})
const emit = defineEmits(['refresh'])

const pad = (n) => String(n).padStart(2, '0')
const lastText = computed(() => `${pad(props.lastAt.getHours())}:${pad(props.lastAt.getMinutes())}:${pad(props.lastAt.getSeconds())}`)
const remainText = computed(() => `${pad(Math.floor(props.nextInSec / 60))}:${pad(props.nextInSec % 60)}`)
const progress = computed(() => Math.max(0, Math.min(100, ((props.intervalSec - props.nextInSec) / props.intervalSec) * 100)))
</script>
