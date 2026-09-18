<template>
  <BlurredImage
    v-if="src"
    :src="src"
    :alt="name || '얼굴'"
    :rounded="false"
    class="shrink-0 rounded-full"
    :style="boxStyle"
  />
  <span
    v-else
    class="relative inline-flex shrink-0 items-center justify-center overflow-hidden rounded-full border border-line bg-canvas text-fg-muted"
    :style="boxStyle"
    :title="name"
  >
    <svg viewBox="0 0 40 40" class="absolute inset-0 h-full w-full" aria-hidden="true">
      <circle cx="20" cy="15" r="7" fill="currentColor" opacity="0.35" />
      <path d="M6 38c0-8 6.3-13 14-13s14 5 14 13z" fill="currentColor" opacity="0.35" />
    </svg>
    <span v-if="initial" class="relative text-xs font-semibold text-fg">{{ initial }}</span>
  </span>
</template>

<script setup>
import { computed } from 'vue'
import BlurredImage from './BlurredImage.vue'

// 실루엣/이니셜 아바타. 목 데이터에는 실제 얼굴 사진을 쓰지 않는다(개인정보 지침).
const props = defineProps({
  name: { type: String, default: '' },
  src: { type: String, default: '' },
  size: { type: Number, default: 40 },
})

const initial = computed(() => (props.name ? props.name.trim().slice(0, 1) : ''))
const boxStyle = computed(() => ({ width: `${props.size}px`, height: `${props.size}px` }))
</script>
