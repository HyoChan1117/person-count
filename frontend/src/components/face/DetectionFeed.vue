<template>
  <div class="flex min-h-0 flex-1 flex-col">
    <ul v-if="visible.length" class="flex min-h-0 flex-1 flex-col gap-2 overflow-y-auto pr-1" aria-label="감지 기록">
      <li
        v-for="d in visible"
        :key="d.id"
        class="group flex items-center gap-4 rounded-lg border-l-2 bg-canvas/40 py-2 pl-3 pr-3"
        :class="d.name == null ? 'border-state-alert' : 'border-line'"
      >
        <BlurredImage
          :src="`/api/face/detections/${d.id}/photo`"
          :alt="`${d.zone_name} 감지`"
          class="h-[4.5rem] w-32 shrink-0"
          @zoom="emit('zoom', d)"
        />
        <div class="min-w-0 flex-1">
          <div class="flex items-center gap-2">
            <p class="truncate text-lg font-semibold" :class="d.name == null ? 'text-state-alert' : 'text-fg'">{{ d.name ?? '미등록 인물' }}</p>
            <StatusBadge v-if="d.name == null" status="alert" label="경고" />
            <span v-else class="shrink-0 text-sm text-fg-muted">{{ d.authorized ? '허가됨' : '미허가' }}</span>
          </div>
          <p class="mt-0.5 truncate text-sm text-fg-muted">{{ d.zone_name }}</p>
        </div>
        <div class="w-28 shrink-0 text-right">
          <p class="text-xl font-semibold tabular-nums text-fg">{{ time(d.ts) }}</p>
          <p class="text-sm tabular-nums text-fg-muted">{{ date(d.ts) }}</p>
        </div>
        <div class="w-24 shrink-0 text-right">
          <p class="text-label text-fg-muted">유사도</p>
          <p class="text-lg font-semibold tabular-nums text-fg">{{ d.score != null ? d.score.toFixed(2) : '–' }}</p>
        </div>
        <button
          type="button"
          class="shrink-0 rounded-md px-2 py-1 text-fg-muted opacity-0 transition-opacity hover:text-fg focus-visible:opacity-100 group-hover:opacity-100"
          title="기록 삭제"
          aria-label="기록 삭제"
          @click="emit('remove', d)"
        >✕</button>
      </li>
      <li v-if="items.length > limit">
        <button type="button" class="w-full rounded-lg border border-line py-2.5 text-sm text-fg-muted transition-colors hover:text-fg" @click="limit += 50">더 보기 ({{ items.length - limit }}건 남음)</button>
      </li>
    </ul>

    <div v-else class="flex flex-1 flex-col items-center justify-center gap-2 text-center">
      <p class="text-lg font-semibold text-fg">{{ empty ? '아직 감지 기록이 없습니다.' : '조건에 맞는 감지 기록이 없습니다.' }}</p>
      <p class="text-sm text-fg-muted">{{ empty ? '순찰을 시작하면 미등록 인물이 촬영된 기록이 여기에 쌓입니다.' : '필터를 바꾸거나 초기화해 보세요.' }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import BlurredImage from '@/components/ui/BlurredImage.vue'

const props = defineProps({
  items: { type: Array, required: true }, // 필터를 거친 감지 기록(최신순)
  empty: { type: Boolean, default: false }, // 전체 기록 자체가 없는가
})
const emit = defineEmits(['zoom', 'remove'])

const limit = ref(50)
const visible = computed(() => props.items.slice(0, limit.value))

const time = (ts) => (ts || '').slice(11, 16)
const date = (ts) => (ts || '').slice(5, 10).replace('-', '/')
</script>
