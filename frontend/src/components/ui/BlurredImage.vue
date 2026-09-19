<template>
  <div
    class="group relative overflow-hidden bg-canvas"
    :class="[rounded ? 'rounded-lg' : '', revealed ? 'cursor-zoom-in' : 'cursor-pointer']"
    role="button"
    tabindex="0"
    :aria-label="revealed ? '이미지 확대' : '이미지 공개'"
    @click="onClick"
    @keydown.enter.prevent="onClick"
  >
    <img
      :src="src"
      :alt="alt"
      class="h-full w-full object-cover transition-[filter] duration-200"
      :class="revealed ? '' : 'scale-110 blur-xl'"
      loading="lazy"
    />
    <span
      v-if="!revealed"
      class="absolute inset-0 flex items-center justify-center bg-canvas/30 text-xs font-medium text-fg opacity-0 transition-opacity group-hover:opacity-100"
    >클릭해서 공개</span>
  </div>
</template>

<script setup>
import { ref, watch, onBeforeUnmount } from 'vue'

// 개인정보 지침: 얼굴이 나올 수 있는 이미지는 기본 블러, 클릭해야 공개.
// 공개 후 autoReblurMs가 지나면 다시 블러 처리한다(전시 환경 기본 15초, 0이면 유지).
const props = defineProps({
  src: { type: String, required: true },
  alt: { type: String, default: '' },
  rounded: { type: Boolean, default: true },
  autoReblurMs: { type: Number, default: 15000 },
})
const emit = defineEmits(['reveal', 'reblur', 'zoom'])

const revealed = ref(false)
let timer = null

function clearTimer() {
  if (timer) { clearTimeout(timer); timer = null }
}

function reveal() {
  revealed.value = true
  emit('reveal')
  clearTimer()
  if (props.autoReblurMs > 0) {
    timer = setTimeout(() => {
      revealed.value = false
      emit('reblur')
    }, props.autoReblurMs)
  }
}

function onClick() {
  if (!revealed.value) reveal()
  else emit('zoom')
}

// 다른 이미지로 바뀌면 다시 블러 상태로 돌아간다
watch(() => props.src, () => { revealed.value = false; clearTimer() })
onBeforeUnmount(clearTimer)
</script>
