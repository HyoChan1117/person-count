<template>
  <div class="ds-root flex h-full min-h-0 flex-col gap-section overflow-y-auto p-section 2xl:overflow-hidden">
    <DashboardHeader :last-at="store.collect.lastAt" :next-in-sec="store.collect.nextInSec" :interval-sec="store.collect.intervalSec" />

    <section class="grid shrink-0 grid-cols-3 gap-gutter" aria-label="핵심 지표">
      <UiCard>
        <MetricStat label="전체 점유율" :value="store.occupancyPct ?? '–'" :unit="store.occupancyPct == null ? '' : '%'" :hint="occupancyHint" size="lg" tone="occupied" />
      </UiCard>
      <UiCard>
        <MetricStat label="사용 중 교실" :value="store.activeRooms" :unit="`/ ${store.rooms.length}`" :hint="idleHint" size="lg" />
      </UiCard>
      <UiCard class="relative">
        <MetricStat label="미확인 경고" :value="store.unseenAlerts" unit="건" hint="최근 24시간 · 열어보지 않은 미등록 인물 감지" size="lg" :tone="store.unseenAlerts > 0 ? 'alert' : 'default'" />
        <button
          v-if="store.unseenAlerts > 0"
          type="button"
          class="absolute right-card top-card rounded-lg border border-line px-3 py-1.5 text-sm text-fg-muted transition-colors hover:border-fg-muted/60 hover:text-fg focus-visible:outline focus-visible:outline-2 focus-visible:outline-fg-muted"
          @click="store.markAllSeen()"
        >모두 확인</button>
      </UiCard>
    </section>

    <!-- 2xl(1536px) 미만에서는 우측 패널을 카드 그리드 아래로 내려 카드 폭을 확보한다 -->
    <div class="grid flex-none grid-cols-1 gap-section 2xl:min-h-0 2xl:flex-1 2xl:grid-cols-[minmax(0,1fr)_30rem]">
      <section class="grid min-h-[36rem] grid-cols-4 grid-rows-2 gap-gutter" aria-label="교실별 점유율">
        <template v-if="store.rooms.length">
          <ClassroomOccupancyCard v-for="room in store.rooms" :key="room.id" :room="room" />
        </template>
        <UiCard v-else class="col-span-4 row-span-2 flex items-center justify-center">
          <p class="text-fg-muted">{{ store.loading ? '불러오는 중...' : store.error || '등록된 교실이 없습니다.' }}</p>
        </UiCard>
      </section>

      <aside class="grid grid-cols-2 items-start gap-gutter 2xl:flex 2xl:min-h-0 2xl:flex-col 2xl:items-stretch">
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
import { countRoomStatuses, describeRoomCounts } from '@/utils/roomStatus'

const store = useHomeDashboardStore()

// 분모는 판정 가능한 좌석. 판정 불가 좌석은 따로 보여 준다.
const occupancyHint = computed(() => {
  const base = `${store.totalOccupied} / ${store.totalJudgeable}석 사용 중`
  return store.totalUnknown ? `${base} · 판정 불가 ${store.totalUnknown}석` : base
})

// 판정 불가 교실(조회 오류, 좌석 0개 등)은 "비어 있음"에 세지 않고 따로 적는다
const idleHint = computed(() => describeRoomCounts(countRoomStatuses(store.rooms)))

onMounted(() => store.start())
onUnmounted(() => store.stop())
</script>
