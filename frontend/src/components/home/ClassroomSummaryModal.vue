<template>
  <div
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/55 p-8"
    @click.self="emit('close')"
  >
    <div
      class="ds-text flex max-h-[88vh] w-full max-w-4xl flex-col rounded-card border border-line bg-card shadow-2xl"
      role="dialog"
      aria-modal="true"
      :aria-labelledby="titleId"
    >
      <!-- 헤더: 어느 교실인지 + 지금 상태 -->
      <header class="flex items-start justify-between gap-gutter border-b border-line px-card py-gutter">
        <div class="min-w-0">
          <div class="flex items-center gap-3">
            <h2 :id="titleId" class="truncate text-2xl font-bold tracking-tight text-fg">{{ room.name }}</h2>
            <StatusBadge :status="badge.status" :label="badge.label" />
          </div>
          <p class="mt-1 text-sm text-fg-muted">지금 좌석 현황과 오늘 하루 통계</p>
        </div>
        <button
          ref="closeRef"
          type="button"
          class="shrink-0 rounded-lg px-2.5 py-1 text-xl leading-none text-fg-muted transition-colors hover:bg-line/50 hover:text-fg focus-visible:outline focus-visible:outline-2 focus-visible:outline-fg-muted"
          aria-label="닫기"
          @click="emit('close')"
        >×</button>
      </header>

      <div class="min-h-0 flex-1 overflow-y-auto px-card py-card">
        <!-- 지금 (대시보드 요약): 홈이 이미 갖고 있는 값이라 열자마자 보인다 -->
        <section class="flex items-center gap-card" aria-label="지금 좌석 현황">
          <MetricStat
            label="지금 점유율"
            :value="pct ?? '–'"
            :unit="pct == null ? '' : '%'"
            :hint="nowHint"
            size="md"
            :tone="pct > 0 ? 'occupied' : 'default'"
          />
          <div v-if="room.map" class="ml-auto h-28 shrink-0">
            <SeatLayoutMini :map="room.map" :seat-states="seatStates" />
          </div>
          <SeatMiniBar v-else-if="room.seats.length" :seats="room.seats" class="ml-auto w-56 shrink-0" />
        </section>

        <div class="my-card h-px bg-line" aria-hidden="true" />

        <!-- 오늘 하루 (모니터링 요약): 모달을 열 때 한 번 불러온다 -->
        <section class="flex flex-col gap-gutter" aria-label="오늘 하루 통계">
          <h3 class="text-lg font-semibold text-fg">
            오늘 하루<span class="ml-2 text-sm font-normal tabular-nums text-fg-muted">{{ todayLabel }}</span>
          </h3>

          <p v-if="loading" role="status" class="py-12 text-center text-sm text-fg-muted">불러오는 중...</p>

          <ErrorNotice
            v-else-if="statsError"
            title="점유 기록을 불러오지 못했습니다"
            :message="statsError"
            @retry="loadStats"
          />

          <p v-else-if="!hasAnyData" class="py-12 text-center text-sm text-fg-muted">
            오늘 저장된 점유 기록이 없습니다.<br />
            <span class="text-fg-muted/80">10분마다 자동으로 좌석 점유 상태가 기록됩니다.</span>
          </p>

          <template v-else>
            <div class="grid grid-cols-3 gap-gutter">
              <UiCard>
                <MetricStat
                  :label="selectedHourData ? `${selectedHourData.time} 점유` : '최고 점유 시간대'"
                  :value="displayHourData ? `${displayHourData.occupied}/${displayHourData.total}` : '–'"
                  :unit="displayHourData ? '석' : ''"
                  :hint="displayHourData && !selectedHourData ? `${displayHourData.time} 기준` : ''"
                  size="sm"
                />
              </UiCard>
              <UiCard>
                <MetricStat
                  label="최다 점유 좌석"
                  :value="hasTopSeat ? `${topSeat.seatId}번` : '–'"
                  :hint="hasTopSeat ? `누적 ${topSeat.timeText}` : ''"
                  size="sm"
                />
              </UiCard>
              <UiCard>
                <MetricStat label="등록 좌석" :value="room.total" unit="석" size="sm" />
              </UiCard>
            </div>

            <div class="grid grid-cols-2 items-start gap-gutter">
              <UiCard>
                <SectionHeader title="시간대별 점유" description="막대를 누르면 그 시각의 점유 좌석 수를 보여 줍니다" />
                <HourlyBarChart class="mt-gutter" :hours="hourlyStats" :selected-hour="selectedHour" @select="toggleHour" />
              </UiCard>

              <UiCard>
                <SectionHeader title="가장 오래 사용된 좌석" :description="`10분마다 확인한 점유 시간을 누적 · 상위 ${rankCount}석`" />
                <SeatRankBars class="mt-gutter" :rows="seatRows" :max-items="5" />
              </UiCard>
            </div>
          </template>
        </section>
      </div>

      <!-- 더 자세히 볼 사람을 위한 길은 남겨 둔다 -->
      <footer class="flex items-center justify-end gap-2 border-t border-line px-card py-gutter">
        <router-link :to="`/dashboard/${room.id}`" :class="BTN_GHOST">대시보드 열기</router-link>
        <router-link :to="`/monitoring/${room.id}`" :class="BTN_GHOST">모니터링 열기</router-link>
        <button type="button" :class="BTN_OUTLINE" @click="emit('close')">닫기</button>
      </footer>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import api from '@/api'
import UiCard from '@/components/ui/UiCard.vue'
import MetricStat from '@/components/ui/MetricStat.vue'
import SectionHeader from '@/components/ui/SectionHeader.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import ErrorNotice from '@/components/ui/ErrorNotice.vue'
import HourlyBarChart from '@/components/charts/HourlyBarChart.vue'
import SeatRankBars from '@/components/charts/SeatRankBars.vue'
import SeatLayoutMini from './SeatLayoutMini.vue'
import SeatMiniBar from './SeatMiniBar.vue'
import { useDailyStats } from '@/composables/useDailyStats'
import { roomStatus } from '@/utils/roomStatus'
import { buildSeatRows, peakHour, todayDateStr } from '@/utils/occupancyStats'

// 클래스는 Tailwind가 스캔할 수 있게 리터럴로 적는다(대시보드 화면의 버튼과 같은 모양).
const FOCUS = 'focus-visible:outline focus-visible:outline-2 focus-visible:outline-fg-muted'
const BTN_GHOST = `inline-flex items-center rounded-lg px-4 py-2.5 text-sm font-medium text-fg transition-colors hover:bg-line/60 ${FOCUS}`
const BTN_OUTLINE = `inline-flex items-center rounded-lg border border-line px-4 py-2.5 text-sm font-medium text-fg-muted transition-colors hover:border-fg-muted/60 hover:text-fg ${FOCUS}`

// 카드와 같은 기준(utils/roomStatus.js)으로 배지를 붙인다
const BADGES = {
  unknown: { status: 'unknown', label: '판정 불가' },
  occupied: { status: 'occupied', label: '사용 중' },
  empty: { status: 'empty', label: '비어 있음' },
}

const props = defineProps({
  // homeDashboardStore의 교실 객체. 부모가 스토어에서 찾아 넘기므로 갱신되면 모달도 같이 바뀐다.
  room: { type: Object, required: true },
})
const emit = defineEmits(['close'])

const titleId = `room-summary-${Math.random().toString(36).slice(2, 9)}`
const closeRef = ref(null)

// ── 지금 (홈이 이미 갖고 있는 값, 추가 조회 없음) ────────────────────────────
const pct = computed(() => (props.room.judgeable ? Math.round((props.room.occupied / props.room.judgeable) * 100) : null))
const badge = computed(() => BADGES[roomStatus(props.room)])
const seatStates = computed(() => Object.fromEntries(props.room.seats.map((s) => [s.id, s.state])))
const nowHint = computed(() => {
  const base = `${props.room.occupied} / ${props.room.judgeable}석 사용 중`
  return props.room.unknown ? `${base} · 판정 불가 ${props.room.unknown}석` : base
})

// ── 오늘 하루 (모니터링 화면과 같은 엔드포인트) ──────────────────────────────
const dateStr = ref(todayDateStr())
const todayLabel = computed(() => {
  const d = new Date(`${dateStr.value}T00:00:00`)
  return `${d.getMonth() + 1}/${d.getDate()} (${['일', '월', '화', '수', '목', '금', '토'][d.getDay()]})`
})

const { seatStats, hourlyStats, loading, error: statsError, load } = useDailyStats({
  fetchDaily: (date) => api.get(`/analysis/${props.room.id}/occupancy-stats-daily`, { params: { date } }).then((r) => r.data),
  fetchHourly: (date) => api.get(`/analysis/${props.room.id}/occupancy-hourly`, { params: { date } }).then((r) => r.data),
  dateStr,
})

async function loadStats() {
  selectedHour.value = null
  await load()
}

const hasAnyData = computed(() => Object.keys(seatStats.value).length > 0)

const selectedHour = ref(null)
const toggleHour = (hour) => { selectedHour.value = selectedHour.value === hour ? null : hour }
const selectedHourData = computed(() => hourlyStats.value.find((h) => h.hour === selectedHour.value) ?? null)
// 고른 시간대가 없으면 점유가 가장 많았던 시간대를 대신 보여 준다
const displayHourData = computed(() => selectedHourData.value ?? peakHour(hourlyStats.value))

const seatIds = computed(() => props.room.seats.map((s) => s.id))
const seatRows = computed(() => buildSeatRows(seatIds.value, seatStats.value))
const rankCount = computed(() => Math.min(5, seatRows.value.length))
const topSeat = computed(() => seatRows.value[0] ?? null)
const hasTopSeat = computed(() => topSeat.value != null && topSeat.value.occupiedMinutes > 0)

// ESC는 포커스가 어디에 있든 닫히도록 문서에서 받는다
function onKeydown(e) {
  if (e.key === 'Escape') emit('close')
}

onMounted(() => {
  document.addEventListener('keydown', onKeydown)
  closeRef.value?.focus()
  loadStats()
})
onUnmounted(() => document.removeEventListener('keydown', onKeydown))
</script>
