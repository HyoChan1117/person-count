<template>
  <div class="ds-root flex h-full min-h-0 flex-col overflow-y-auto p-section 2xl:overflow-hidden">
    <div class="mx-auto flex w-full max-w-[1680px] flex-col gap-section 2xl:min-h-0 2xl:flex-1">
    <DashboardHeader
      :last-at="store.collect.lastAt"
      :next-in-sec="store.collect.nextInSec"
      :interval-sec="store.collect.intervalSec"
      :stale="store.stale"
      :last-ok-text="lastOkText"
      @refresh="store.refresh()"
    />

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
      <!-- 교실마다 가로로 긴 행 하나. 행 높이는 남는 세로를 균등하게 나눠 갖는다 -->
      <section class="grid min-h-[36rem] auto-rows-fr grid-cols-1 gap-gutter" aria-label="교실별 점유율">
        <template v-if="store.rooms.length">
          <ClassroomOccupancyCard
            v-for="room in store.rooms"
            :key="room.id"
            :room="room"
            :analyzing="store.analyzingRooms.has(room.id)"
            @open="openRoom(room.id, $event)"
            @analyze="analyzeRoom(room.id)"
          />
        </template>
        <UiCard v-else class="flex items-center justify-center">
          <p class="text-fg-muted">{{ store.loading ? '불러오는 중...' : store.error || '등록된 교실이 없습니다.' }}</p>
        </UiCard>
      </section>

      <!-- 2xl에서는 교실 카드와 같은 행 높이로 나눈다: 순찰 상태가 카드 한 행, 최근 감지 로그가 나머지 행 -->
      <aside
        class="grid grid-cols-2 items-start gap-gutter 2xl:min-h-0 2xl:grid-cols-1 2xl:items-stretch"
        :class="asideRowsClass"
      >
        <PatrolStatusPanel
          :place="store.patrolPlace"
          :places="store.places"
          :selected-id="store.selectedPlaceId"
          :busy="store.patrolBusy"
          @select="store.selectPlace"
          @start="runPatrol(store.startPatrol)"
          @stop="runPatrol(store.stopPatrol)"
          @toggle-auto="runPatrol((p) => store.setAutoPatrol(p, !(p.autoPatrol ?? true)))"
        />
        <RecentDetectionsList
          :items="store.recentDetections"
          :scope="store.selectedPlaceId == null ? '전체 교실' : (store.patrolPlace?.name ?? '전체 교실')"
          class="2xl:row-start-2 2xl:row-end-[-1]"
          @reveal="store.markSeen"
        />
      </aside>
    </div>
    </div>

    <!-- 교실 카드를 누르면 화면을 옮기지 않고 이 요약 모달을 띄운다 -->
    <Teleport to="body">
      <ClassroomSummaryModal v-if="selectedRoom" :room="selectedRoom" @close="closeRoom" />
    </Teleport>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue'
import { useHomeDashboardStore } from '@/stores/homeDashboardStore'
import UiCard from '@/components/ui/UiCard.vue'
import MetricStat from '@/components/ui/MetricStat.vue'
import DashboardHeader from '@/components/home/DashboardHeader.vue'
import ClassroomOccupancyCard from '@/components/home/ClassroomOccupancyCard.vue'
import PatrolStatusPanel from '@/components/home/PatrolStatusPanel.vue'
import RecentDetectionsList from '@/components/home/RecentDetectionsList.vue'
import ClassroomSummaryModal from '@/components/home/ClassroomSummaryModal.vue'
import { countRoomStatuses, describeRoomCounts } from '@/utils/roomStatus'

const store = useHomeDashboardStore()

// 모달은 교실 id만 기억하고 값은 스토어에서 찾는다(2분마다 갱신되면 열려 있는 모달도 같이 바뀐다).
const selectedRoomId = ref(null)
const selectedRoom = computed(() => store.rooms.find((r) => r.id === selectedRoomId.value) ?? null)

// 닫으면 눌렀던 카드로 포커스를 돌려준다(키보드로 훑어보던 자리를 잃지 않게)
let lastFocused = null
function openRoom(id, el) {
  lastFocused = el ?? document.activeElement
  selectedRoomId.value = id
}
function closeRoom() {
  selectedRoomId.value = null
  nextTick(() => lastFocused?.focus?.())
}

// 우측 패널의 행 높이를 교실 카드와 맞춘다. 클래스는 Tailwind가 스캔할 수 있게 리터럴로 적는다.
// 교실이 1개면 카드 한 장이 세로를 다 쓰므로(감지 로그가 들어갈 자리가 없다) 최소 2행으로 둔다.
const ASIDE_ROWS = { 2: '2xl:grid-rows-2', 3: '2xl:grid-rows-3', 4: '2xl:grid-rows-4', 5: '2xl:grid-rows-5', 6: '2xl:grid-rows-6' }
const asideRowsClass = computed(() => ASIDE_ROWS[Math.min(6, Math.max(2, store.rooms.length))])

// 교실 카드의 '분석' 버튼. 실시간 추론이라 카메라가 응답하지 않으면 오래 걸릴 수 있어 실패를 따로 알린다.
async function analyzeRoom(roomId) {
  try {
    await store.analyzeRoom(roomId)
  } catch (e) {
    alert(`좌석 분석에 실패했습니다 — ${e.response?.data?.detail ?? e.message}`)
  }
}

// 순찰 조작은 스토어가 하고, 실패했을 때 알리는 것만 화면이 맡는다
async function runPatrol(action) {
  const place = store.patrolPlace
  if (!place) return
  try {
    await action(place)
  } catch (e) {
    alert(e.response?.data?.detail ?? e.message)
  }
}

// 분모는 판정 가능한 좌석. 판정 불가 좌석은 따로 보여 준다.
const occupancyHint = computed(() => {
  const base = `${store.totalOccupied} / ${store.totalJudgeable}석 사용 중`
  return store.totalUnknown ? `${base} · 판정 불가 ${store.totalUnknown}석` : base
})

// 마지막으로 모든 요청이 성공한 시각(낡은 데이터 안내용)
const lastOkText = computed(() => {
  if (!store.lastSuccessAt) return ''
  const d = new Date(store.lastSuccessAt)
  return [d.getHours(), d.getMinutes(), d.getSeconds()].map((n) => String(n).padStart(2, '0')).join(':')
})

// 판정 불가 교실(조회 오류, 좌석 0개 등)은 "비어 있음"에 세지 않고 따로 적는다
const idleHint = computed(() => describeRoomCounts(countRoomStatuses(store.rooms)))

onMounted(() => store.start())
onUnmounted(() => store.stop())
</script>
