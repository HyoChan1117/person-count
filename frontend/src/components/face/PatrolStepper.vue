<template>
  <ol class="flex items-start" aria-label="순찰 구역 진행">
    <li v-for="(z, i) in zones" :key="z.id" class="flex min-w-0 flex-1 flex-col items-center gap-2 text-center" :aria-current="running && i + 1 === current ? 'step' : undefined">
      <div class="relative flex w-full items-center justify-center">
        <span v-if="i > 0" class="absolute right-1/2 h-0.5 w-full" :class="isDone(i) || (running && i + 1 === current) ? 'bg-fg-muted' : 'border-t-2 border-dashed border-line'" />
        <span
          class="relative flex h-9 w-9 items-center justify-center rounded-full text-sm font-semibold tabular-nums"
          :class="dotClass(i)"
        >
          <svg v-if="isDone(i)" viewBox="0 0 24 24" class="h-4 w-4 fill-none stroke-current" stroke-width="3" aria-hidden="true"><path d="M5 12l5 5 9-10" /></svg>
          <template v-else>{{ i + 1 }}</template>
        </span>
      </div>
      <span class="w-full truncate px-1 text-sm" :class="running && i + 1 === current ? 'font-semibold text-fg' : 'text-fg-muted'" :title="z.name">{{ z.name }}</span>
    </li>
  </ol>
</template>

<script setup>
const props = defineProps({
  zones: { type: Array, required: true }, // [{ id, name }]
  current: { type: Number, default: 0 }, // 1부터 시작하는 현재 구역 번호
  running: { type: Boolean, default: false },
  completed: { type: Boolean, default: false },
})

const isDone = (i) => (props.completed && !props.running) || (props.running && i + 1 < props.current)

function dotClass(i) {
  if (isDone(i)) return 'bg-fg-muted text-canvas'
  if (props.running && i + 1 === props.current) return 'bg-fg text-canvas ring-4 ring-fg/20'
  return 'border-2 border-line text-fg-muted'
}
</script>
