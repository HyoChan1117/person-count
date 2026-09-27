<template>
  <header class="flex items-end justify-between gap-section">
    <div class="flex min-w-0 items-center gap-6">
      <img :src="emblemUrl" alt="영진전문대학교 엠블럼" class="h-24 w-auto shrink-0" />
      <!-- 2xl 이상: 공식 학교명 글자(한글·영문)를 엠블럼 옆에 크게 둔다.
           글자가 흰색 이미지라 라이트 테마(.dark 없음)에서는 어둡게 바꾼다. 엠블럼은 별도 이미지라 영향 없음 -->
      <img :src="wordmarkUrl" alt="영진전문대학교 YEUNGJIN UNIVERSITY" class="hidden h-[50px] w-auto shrink-0 brightness-[.07] dark:brightness-100 2xl:block" />
      <div class="hidden h-16 w-px shrink-0 bg-line 2xl:block" aria-hidden="true" />
      <div class="min-w-0">
        <!-- 2xl 미만: 공식 글자가 들어갈 자리가 없어 작은 학교명 줄로 대신한다 -->
        <p class="mb-1 flex items-center gap-2.5 text-base font-semibold text-fg-muted 2xl:hidden">
          <span>영진전문대학교</span>
          <span class="h-1 w-1 rounded-full bg-fg-muted" aria-hidden="true" />
          <span class="text-sm font-medium tracking-[0.14em]">YEUNGJIN UNIVERSITY</span>
        </p>
        <h1 class="text-3xl font-bold tracking-tight text-fg">스마트 강의실 도우미</h1>
        <!-- 갱신에 실패해 낡은 숫자를 보여 주는 중이면 부제 자리에 알린다(높이는 그대로) -->
        <p v-if="stale" role="status" class="mt-1 flex items-center gap-3 text-lg">
          <span class="rounded-full border border-fg-muted/60 px-3 py-0.5 text-base font-semibold text-fg">데이터가 오래되었습니다</span>
          <span class="truncate text-base text-fg-muted">마지막 정상 갱신 {{ lastOkText }}</span>
          <button type="button" class="shrink-0 rounded-md px-2 py-0.5 text-base text-fg-muted underline underline-offset-4 transition-colors hover:text-fg focus-visible:outline focus-visible:outline-2 focus-visible:outline-fg-muted" @click="emit('refresh')">지금 갱신</button>
        </p>
        <p v-else class="mt-1 text-lg text-fg-muted">CCTV 기반 좌석 점유 + 얼굴인식 순찰 관제</p>
      </div>
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
import emblemUrl from '@/assets/yju-emblem.png'
import wordmarkUrl from '@/assets/yju-wordmark.png'

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
