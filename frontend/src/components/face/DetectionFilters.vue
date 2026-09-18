<template>
  <div class="flex flex-wrap items-center gap-gutter">
    <div class="flex items-center gap-2">
      <span class="text-label text-fg-muted">기간</span>
      <div class="flex gap-1 rounded-lg border border-line p-1" role="group" aria-label="기간 필터">
        <button v-for="p in PERIODS" :key="p.key" type="button" class="rounded-md px-3 py-1.5 text-sm transition-colors" :class="period === p.key ? 'bg-line text-fg' : 'text-fg-muted hover:text-fg'" :aria-pressed="period === p.key" @click="emit('update:period', p.key)">{{ p.label }}</button>
      </div>
    </div>

    <div class="flex items-center gap-2">
      <label for="det-zone" class="text-label text-fg-muted">구역</label>
      <select id="det-zone" :value="zone" class="rounded-lg border border-line bg-card px-3 py-2 text-sm text-fg focus-visible:outline focus-visible:outline-2 focus-visible:outline-fg-muted" @change="emit('update:zone', $event.target.value)">
        <option value="">전체 구역</option>
        <option v-for="z in zones" :key="z" :value="z">{{ z }}</option>
      </select>
    </div>

    <div class="flex items-center gap-2">
      <span class="text-label text-fg-muted">등록 여부</span>
      <div class="flex gap-1 rounded-lg border border-line p-1" role="group" aria-label="등록 여부 필터">
        <button v-for="r in REGISTRATIONS" :key="r.key" type="button" class="rounded-md px-3 py-1.5 text-sm transition-colors" :class="registration === r.key ? 'bg-line text-fg' : 'text-fg-muted hover:text-fg'" :aria-pressed="registration === r.key" @click="emit('update:registration', r.key)">{{ r.label }}</button>
      </div>
    </div>

    <p class="ml-auto text-sm tabular-nums text-fg-muted">
      <span class="font-semibold text-fg">{{ count }}</span> / {{ total }}건
      <button v-if="isFiltered" type="button" class="ml-3 underline underline-offset-4 hover:text-fg" @click="emit('reset')">필터 초기화</button>
    </p>
  </div>
</template>

<script setup>
import { PERIODS, REGISTRATIONS } from '@/composables/useDetectionFilters'

defineProps({
  period: { type: String, required: true },
  zone: { type: String, required: true },
  registration: { type: String, required: true },
  zones: { type: Array, required: true },
  count: { type: Number, required: true },
  total: { type: Number, required: true },
  isFiltered: { type: Boolean, default: false },
})
const emit = defineEmits(['update:period', 'update:zone', 'update:registration', 'reset'])
</script>
