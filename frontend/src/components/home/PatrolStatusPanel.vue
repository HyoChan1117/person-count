<template>
  <UiCard>
    <SectionHeader title="순찰 상태" :description="place ? place.name : '등록된 장소 없음'">
      <template #actions>
        <span class="rounded-full border border-line px-3 py-1 text-sm font-medium" :class="stateClass">{{ stateText }}</span>
      </template>
    </SectionHeader>

    <template v-if="place">
      <div class="mt-card grid grid-cols-2 gap-gutter">
        <div>
          <p class="text-label text-fg-muted">현재 구역</p>
          <p class="mt-1 truncate text-2xl font-semibold text-fg">{{ current || '–' }}</p>
        </div>
        <div>
          <p class="text-label text-fg-muted">진행 단계</p>
          <p class="mt-1 text-2xl font-semibold tabular-nums text-fg">
            {{ status.zone_index }}<span class="text-fg-muted"> / {{ total }}</span>
            <span v-if="phaseText" class="ml-2 text-base font-medium text-fg-muted">{{ phaseText }}</span>
          </p>
        </div>
      </div>

      <ol class="mt-card flex items-center gap-1.5" aria-label="구역 진행 단계">
        <li v-for="(z, i) in place.zones" :key="z.id" class="h-1.5 flex-1 rounded-full" :class="dotClass(i)" :title="z.name" />
      </ol>
    </template>
  </UiCard>
</template>

<script setup>
import { computed } from 'vue'
import UiCard from '@/components/ui/UiCard.vue'
import SectionHeader from '@/components/ui/SectionHeader.vue'
import { zoneLabel } from '@/utils/patrolZone'

const PHASES = { move: '이동', settle: '대기', shoot: '촬영', analyze: '분석' }

const props = defineProps({
  place: { type: Object, default: null }, // { name, zones[{id,name}], status }
})

const status = computed(() => props.place?.status ?? {})
const total = computed(() => status.value.total_zones || props.place?.zones.length || 0)
const current = computed(() => zoneLabel(status.value, props.place?.zones))
const phaseText = computed(() => (status.value.running ? PHASES[status.value.phase] ?? '' : ''))

const stateText = computed(() => (status.value.running ? '순찰 중' : status.value.completed ? '순찰 완료' : '대기'))
const stateClass = computed(() => (status.value.running ? 'text-fg' : 'text-fg-muted'))

// 완료/진행 구역은 밝게, 현재 구역은 가장 밝게, 남은 구역은 경계선 색
function dotClass(i) {
  const idx = i + 1
  if (status.value.completed) return 'bg-fg-muted'
  if (!status.value.running) return 'bg-line'
  if (idx < status.value.zone_index) return 'bg-fg-muted'
  if (idx === status.value.zone_index) return 'bg-fg'
  return 'bg-line'
}
</script>
