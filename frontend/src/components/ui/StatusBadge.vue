<template>
  <span
    class="inline-flex items-center gap-2 rounded-full font-medium whitespace-nowrap"
    :class="[styles.box, size === 'lg' ? 'px-3 py-1 text-sm' : 'px-2.5 py-0.5 text-xs']"
  >
    <span class="rounded-full" :class="[styles.dot, size === 'lg' ? 'h-2.5 w-2.5' : 'h-2 w-2']" />
    <slot>{{ label ?? defaultLabel }}</slot>
  </span>
</template>

<script setup>
import { computed } from 'vue'

// 상태색은 4가지 고정. 클래스는 Tailwind가 스캔할 수 있도록 전부 리터럴로 적는다.
const STATUS = {
  occupied: { box: 'bg-state-occupied/15 text-state-occupied', dot: 'bg-state-occupied', label: '점유' },
  empty: { box: 'bg-state-empty/15 text-state-empty', dot: 'bg-state-empty', label: '빈 좌석' },
  unknown: { box: 'bg-state-unknown/15 text-state-unknown', dot: 'bg-state-unknown', label: '판정 불가' },
  alert: { box: 'bg-state-alert/15 text-state-alert', dot: 'bg-state-alert', label: '미등록 인물' },
}

const props = defineProps({
  status: { type: String, required: true },
  label: { type: String, default: null },
  size: { type: String, default: 'md' },
})

const styles = computed(() => {
  if (!STATUS[props.status]) {
    if (import.meta.env.DEV) console.warn(`[StatusBadge] 허용되지 않은 status: "${props.status}" (occupied/empty/unknown/alert만 가능)`)
    return STATUS.unknown
  }
  return STATUS[props.status]
})

const defaultLabel = computed(() => styles.value.label)
</script>
