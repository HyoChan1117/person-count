<template>
  <router-link :to="`/dashboard/${room.id}`" class="block h-full focus-visible:outline-none">
    <UiCard interactive class="flex h-full flex-col justify-between">
      <div class="flex items-start justify-between gap-2">
        <h3 class="text-lg font-semibold text-fg">{{ room.name }}</h3>
        <StatusBadge :status="badge.status" :label="badge.label" size="lg" />
      </div>

      <div>
        <div class="flex items-baseline gap-1">
          <span class="text-metric-sm tabular-nums" :class="pct > 0 ? 'text-state-occupied' : 'text-fg-muted'">{{ pct ?? '–' }}</span>
          <span v-if="pct != null" class="text-xl text-fg-muted">%</span>
        </div>
        <p class="mt-1 text-sm text-fg-muted tabular-nums">
          {{ room.occupied }} / {{ room.judgeable }}석
          <span v-if="room.unknown" class="text-state-unknown"> · 판정 불가 {{ room.unknown }}</span>
        </p>
      </div>

      <SeatMiniBar :seats="room.seats" />
    </UiCard>
  </router-link>
</template>

<script setup>
import { computed } from 'vue'
import UiCard from '@/components/ui/UiCard.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import SeatMiniBar from './SeatMiniBar.vue'

const props = defineProps({
  room: { type: Object, required: true }, // { id, name, total, occupied, judgeable, unknown, seats[], error }
})

// 점유율 = 점유 ÷ 판정 가능 좌석. 판정 가능한 좌석이 없으면 null("–")
const pct = computed(() => (props.room.judgeable ? Math.round((props.room.occupied / props.room.judgeable) * 100) : null))

const badge = computed(() => {
  const r = props.room
  if (r.error || (r.total > 0 && r.judgeable === 0)) return { status: 'unknown', label: '판정 불가' }
  if (r.occupied > 0) return { status: 'occupied', label: '사용 중' }
  return { status: 'empty', label: '비어 있음' }
})
</script>
