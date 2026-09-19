<template>
  <div class="flex flex-col gap-2">
    <span class="text-label text-fg-muted">{{ label }}</span>
    <div class="flex items-baseline gap-2">
      <span class="tabular-nums" :class="[valueSize, toneClass]">{{ value }}</span>
      <span v-if="unit" class="text-fg-muted" :class="size === 'lg' ? 'text-2xl' : 'text-lg'">{{ unit }}</span>
    </div>
    <span v-if="hint" class="text-sm text-fg-muted">{{ hint }}</span>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  label: { type: String, required: true },
  value: { type: [String, Number], required: true },
  unit: { type: String, default: '' },
  hint: { type: String, default: '' },
  size: { type: String, default: 'md' },   // 'sm' | 'md' | 'lg'
  tone: { type: String, default: 'default' }, // 'default' | 'occupied' | 'alert' (상태 의미가 있을 때만)
})

const valueSize = computed(() => ({ sm: 'text-metric-sm', md: 'text-metric', lg: 'text-metric-lg' }[props.size] ?? 'text-metric'))
const toneClass = computed(() => ({ occupied: 'text-state-occupied', alert: 'text-state-alert' }[props.tone] ?? 'text-fg'))
</script>
