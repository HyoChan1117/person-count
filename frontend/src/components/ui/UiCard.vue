<template>
  <component
    :is="as"
    class="rounded-card border border-line bg-card"
    :class="[padded ? 'p-card' : '', interactive ? 'transition-colors hover:border-fg-muted/40 focus-visible:outline focus-visible:outline-2 focus-visible:outline-fg-muted' : '']"
  >
    <slot />
  </component>
</template>

<script setup>
defineProps({
  as: { type: [String, Object], default: 'div' },
  padded: { type: Boolean, default: true },
  interactive: { type: Boolean, default: false },
})
</script>
