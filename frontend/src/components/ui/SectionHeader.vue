<template>
  <div class="flex items-end justify-between gap-gutter">
    <div class="min-w-0">
      <h2 class="truncate text-lg font-semibold text-fg">{{ title }}</h2>
      <p v-if="description" class="mt-1 text-sm text-fg-muted">{{ description }}</p>
    </div>
    <div v-if="$slots.actions" class="flex shrink-0 items-center gap-2">
      <slot name="actions" />
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: { type: String, required: true },
  description: { type: String, default: '' },
})
</script>
