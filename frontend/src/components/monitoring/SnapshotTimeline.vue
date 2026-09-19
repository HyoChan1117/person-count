<template>
  <UiCard class="flex items-center gap-section !py-4">
    <button
      type="button"
      class="flex h-14 w-14 shrink-0 items-center justify-center rounded-full border border-line text-fg transition-colors hover:border-fg-muted/60 focus-visible:outline focus-visible:outline-2 focus-visible:outline-fg-muted"
      :aria-label="playing ? '일시정지' : '재생'"
      @click="emit('toggle')"
    >
      <svg v-if="playing" viewBox="0 0 24 24" class="h-6 w-6 fill-current" aria-hidden="true"><rect x="6" y="5" width="4" height="14" rx="1" /><rect x="14" y="5" width="4" height="14" rx="1" /></svg>
      <svg v-else viewBox="0 0 24 24" class="h-6 w-6 fill-current" aria-hidden="true"><path d="M8 5v14l11-7z" /></svg>
    </button>

    <div class="w-44 shrink-0">
      <p class="text-label text-fg-muted">스냅샷 시각 · {{ intervalMin }}분 단위</p>
      <p class="text-metric-sm tabular-nums text-fg">{{ slots[index]?.time ?? '--:--' }}</p>
    </div>

    <div v-if="slots.length > 1" class="min-w-0 flex-1">
      <input
        type="range"
        class="block h-2 w-full cursor-pointer accent-fg"
        min="0"
        :max="slots.length - 1"
        step="1"
        :value="index"
        aria-label="스냅샷 타임라인"
        @input="emit('scrub', Number($event.target.value))"
      />
      <div class="relative mt-1 h-4">
        <span
          v-for="m in missing"
          :key="`m${m.i}`"
          class="absolute top-0 h-1 w-1 -translate-x-1/2 rounded-full bg-fg-muted/60"
          :style="{ left: `${m.pct}%` }"
          title="기록 없음"
        />
        <span
          v-for="t in ticks"
          :key="t.i"
          class="absolute top-1 -translate-x-1/2 text-xs tabular-nums text-fg-muted"
          :style="{ left: `${t.pct}%` }"
        >{{ t.label }}</span>
      </div>
    </div>
    <p v-else class="flex-1 text-fg-muted">이 날짜에는 표시할 스냅샷이 없습니다.</p>
  </UiCard>
</template>

<script setup>
import { computed } from 'vue'
import UiCard from '@/components/ui/UiCard.vue'

const props = defineProps({
  slots: { type: Array, required: true },
  index: { type: Number, required: true },
  playing: { type: Boolean, required: true },
  intervalMin: { type: Number, default: 10 },
})
const emit = defineEmits(['scrub', 'toggle'])

const pct = (i) => (props.slots.length > 1 ? (i / (props.slots.length - 1)) * 100 : 0)

// 정각 슬롯에만 시각 눈금을 단다
const ticks = computed(() =>
  props.slots.map((s, i) => ({ i, label: s.time.slice(0, 2), pct: pct(i), on: s.time.endsWith(':00') })).filter((t) => t.on),
)
// 그 시각 기록이 없는 슬롯 표시(판정 불가가 아니므로 상태색이 아닌 중립색)
const missing = computed(() => props.slots.map((s, i) => ({ i, pct: pct(i), none: s.seats == null })).filter((m) => m.none))
</script>
