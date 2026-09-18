<template>
  <div class="ds-root flex h-full min-h-0 flex-col gap-section overflow-y-auto p-section 2xl:overflow-hidden">
    <DashboardHeader :last-at="store.collect.lastAt" :next-in-sec="store.collect.nextInSec" :interval-sec="store.collect.intervalSec" />

    <section class="grid shrink-0 grid-cols-3 gap-gutter" aria-label="핵심 지표">
      <UiCard>
        <MetricStat label="전체 점유율" :value="store.occupancyPct" unit="%" :hint="`${store.totalOccupied} / ${store.totalSeats}석 사용 중`" size="lg" tone="occupied" />
      </UiCard>
      <UiCard>
        <MetricStat label="사용 중 교실" :value="store.activeRooms" :unit="`/ ${store.rooms.length}`" :hint="idleHint" size="lg" />
      </UiCard>
      <UiCard>
        <MetricStat label="미확인 경고" :value="store.unseenAlerts" unit="건" hint="열어보지 않은 미등록 인물 감지" size="lg" :tone="store.unseenAlerts > 0 ? 'alert' : 'default'" />
      </UiCard>
    </section>

    <div class="grid min-h-0 flex-1 grid-cols-[minmax(0,1fr)_30rem] gap-section">
      <section class="grid min-h-[36rem] grid-cols-4 grid-rows-2 gap-gutter" aria-label="교실별 점유율">
        <template v-if="store.rooms.length">
          <ClassroomOccupancyCard v-for="room in store.rooms" :key="room.id" :room="room" />
        </template>
        <UiCard v-else class="col-span-4 row-span-2 flex items-center justify-center">
          <p class="text-fg-muted">{{ store.loading ? '불러오는 중...' : store.error || '등록된 교실이 없습니다.' }}</p>
        </UiCard>
      </section>

      <aside class="flex min-h-0 flex-col gap-gutter">
        <PatrolStatusPanel :place="store.primaryPatrol" />
        <RecentDetectionsList :items="store.recentDetections" @reveal="store.markSeen" />
      </aside>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted } from 'vue'
import { useHomeDashboardStore } from '@/stores/homeDashboardStore'
import UiCard from '@/components/ui/UiCard.vue'
import MetricStat from '@/components/ui/MetricStat.vue'
import DashboardHeader from '@/components/home/DashboardHeader.vue'
import ClassroomOccupancyCard from '@/components/home/ClassroomOccupancyCard.vue'
import PatrolStatusPanel from '@/components/home/PatrolStatusPanel.vue'
import RecentDetectionsList from '@/components/home/RecentDetectionsList.vue'

const store = useHomeDashboardStore()

const idleHint = computed(() => {
  const idle = store.rooms.length - store.activeRooms
  return idle > 0 ? `${idle}개 교실 비어 있음` : '모든 교실 사용 중'
})

onMounted(() => store.start())
onUnmounted(() => store.stop())
</script>
