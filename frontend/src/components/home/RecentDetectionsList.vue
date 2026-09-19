<template>
  <UiCard class="flex min-h-0 flex-1 flex-col">
    <SectionHeader title="최근 감지 로그" description="얼굴은 기본 블러 · 클릭하면 공개" />

    <ul v-if="items.length" class="mt-card flex min-h-0 flex-1 flex-col gap-2 overflow-hidden">
      <li
        v-for="d in items"
        :key="d.key"
        class="flex items-center gap-3 rounded-lg border-l-2 bg-canvas/40 py-1.5 pl-3 pr-2"
        :class="d.name == null ? 'border-state-alert' : 'border-line'"
      >
        <BlurredImage
          :src="`/api/face/detections/${d.id}/photo`"
          :alt="`${d.zone_name} 감지`"
          class="h-10 w-16 shrink-0"
          @reveal="emit('reveal', d.key)"
        />
        <div class="min-w-0 flex-1">
          <p class="truncate text-base font-semibold" :class="d.name == null ? 'text-state-alert' : 'text-fg'">{{ d.name ?? '미등록 인물' }}</p>
          <p class="truncate text-sm text-fg-muted">{{ d.placeName }} · {{ d.zone_name }}</p>
        </div>
        <div class="shrink-0 text-right">
          <p class="text-base font-semibold tabular-nums text-fg">{{ timeOf(d.ts) }}</p>
          <p class="text-sm tabular-nums text-fg-muted">유사도 {{ d.score.toFixed(2) }}</p>
        </div>
      </li>
    </ul>
    <p v-else class="mt-card text-sm text-fg-muted">아직 감지 기록이 없습니다.</p>
  </UiCard>
</template>

<script setup>
import UiCard from '@/components/ui/UiCard.vue'
import SectionHeader from '@/components/ui/SectionHeader.vue'
import BlurredImage from '@/components/ui/BlurredImage.vue'

defineProps({
  items: { type: Array, required: true }, // [{ key, id, placeName, zone_name, name|null, score, ts }]
})
const emit = defineEmits(['reveal'])

const timeOf = (ts) => (ts || '').slice(11, 16)
</script>
