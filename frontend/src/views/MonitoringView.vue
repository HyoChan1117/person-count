<template>
  <div class="ds-root h-full overflow-y-auto p-section">
    <div class="mx-auto flex max-w-[1680px] flex-col gap-section">

      <!-- 배치도 + 좌석 상태 + 스냅샷 타임라인: 첫 화면(1920x1080)에 모두 들어오도록 높이를 뷰포트에 맞춘다 -->
      <section class="flex h-[calc(100vh-4rem)] min-h-[44rem] flex-col gap-gutter">
        <header class="flex items-end justify-between gap-section">
          <div class="min-w-0">
            <router-link to="/classrooms" class="text-sm text-fg-muted transition-colors hover:text-fg">← 목록</router-link>
            <h1 class="mt-1 text-3xl font-bold tracking-tight text-fg">{{ classroom?.name || '좌석 모니터링' }}</h1>
            <p class="mt-1 text-lg text-fg-muted">배치도 위 좌석 상태와 {{ intervalMin }}분 단위 스냅샷</p>
          </div>
          <div class="flex shrink-0 items-center gap-gutter">
            <!-- 요일 선택 (매주 월요일 00시에 기록이 초기화되므로 이번 주 요일 단위로 조회) -->
            <div class="flex gap-1 rounded-card border border-line bg-card p-1" role="tablist" aria-label="요일 선택">
              <button
                v-for="day in weekDays"
                :key="day.dateStr"
                role="tab"
                :aria-selected="selectedDateStr === day.dateStr"
                :disabled="day.isFuture"
                class="rounded-lg px-4 py-2 text-center transition-colors"
                :class="day.isFuture ? 'cursor-not-allowed text-fg-muted/40' : selectedDateStr === day.dateStr ? 'bg-line text-fg' : 'text-fg-muted hover:text-fg'"
                @click="selectedDateStr = day.dateStr"
              >
                <span class="block text-sm font-semibold">{{ day.label }}</span>
                <span class="block text-xs tabular-nums">{{ day.shortDate }}</span>
              </button>
            </div>
            <button
              v-if="classroom"
              class="rounded-lg border border-line px-4 py-2.5 text-sm font-medium text-fg-muted transition-colors hover:border-fg-muted/60 hover:text-fg"
              @click="scheduleOpen = true"
            >시간표 설정</button>
          </div>
        </header>

        <ErrorNotice v-if="cStore.error" title="교실 정보를 불러오지 못했습니다" :message="cStore.error" @retry="cStore.fetchOne(classroomId)" />

        <div class="grid min-h-0 flex-1 grid-cols-[minmax(0,1fr)_28rem] gap-gutter">
          <UiCard class="flex min-h-0 flex-col">
            <ClassroomSeatMap
              v-if="mapData"
              :map="mapData"
              :seat-states="seatStates"
              :has-record="hasRecord"
              :selected-id="selectedSeat"
              @select="selectSeat"
            />
            <div v-else class="flex flex-1 flex-col items-center justify-center gap-3 text-center">
              <p class="text-lg font-semibold text-fg">{{ mapLoading ? '배치도를 불러오는 중...' : '배치도가 등록되지 않았습니다.' }}</p>
              <router-link v-if="!mapLoading" :to="`/classrooms/${classroomId}/map`" class="text-sm text-fg-muted underline underline-offset-4 hover:text-fg">맵 에디터에서 배치도 만들기</router-link>
            </div>
          </UiCard>

          <SeatDetailPanel
            :classroom-id="classroomId"
            :seat-id="selectedSeat"
            :state="selectedSeat ? seatStates[selectedSeat] ?? 'unknown' : 'unknown'"
            :has-record="hasRecord"
            :slot="current"
            :is-latest="isLatest"
            :camera="selectedCamera"
            :stat="selectedSeat ? seatStats[selectedSeat] ?? null : null"
          />
        </div>

        <SnapshotTimeline :slots="slots" :index="index" :playing="playing" :interval-min="intervalMin" @scrub="scrub" @toggle="togglePlay" />
      </section>

      <!-- 하루 통계 (첫 화면 아래) -->
      <section class="flex flex-col gap-gutter pb-section" aria-label="하루 통계">
        <h2 class="text-2xl font-bold tracking-tight text-fg">
          하루 통계<span class="ml-3 text-lg font-normal text-fg-muted">{{ selectedDayLabel }}</span>
        </h2>

        <p v-if="loading" class="py-20 text-center text-base text-fg-muted">불러오는 중...</p>

        <!-- 조회 실패를 "저장된 기록 없음"으로 보이지 않게 따로 안내한다 -->
        <ErrorNotice v-else-if="statsError" title="점유 기록을 불러오지 못했습니다" :message="statsError" @retry="fetchStats" />

        <p v-else-if="!hasAnyData" class="py-20 text-center text-base text-fg-muted">
          {{ selectedDayLabel }}에 저장된 점유 기록이 없습니다.<br />
          <span class="text-sm">10분마다 자동으로 좌석 점유 상태가 기록됩니다.</span>
        </p>

        <template v-else>
          <div class="grid grid-cols-3 gap-gutter">
            <UiCard>
              <MetricStat label="등록 좌석" :value="allSeatIds.length" unit="석" size="sm" />
            </UiCard>
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
          </div>

          <div class="grid grid-cols-2 items-start gap-gutter">
            <UiCard>
              <SectionHeader title="시간대별 점유" description="교실 시간표 기준, 정각마다 점유 좌석 수 · 막대를 누르면 그 시각의 좌석을 보여 줍니다" />
              <HourlyBarChart class="mt-card" :hours="hourlyStats" :selected-hour="selectedHour" @select="toggleHour" />

              <div v-if="selectedHourData" class="mt-card rounded-lg border border-line bg-canvas/40 p-4">
                <p class="flex items-baseline gap-3">
                  <span class="text-xl font-semibold tabular-nums text-fg">{{ selectedHourData.time }}</span>
                  <span class="text-base tabular-nums text-fg-muted">점유 {{ selectedHourData.occupied }}/{{ selectedHourData.total }}석</span>
                </p>
                <div v-if="selectedHourData.seats?.length" class="mt-3 flex flex-wrap gap-2">
                  <span
                    v-for="sid in selectedHourData.seats"
                    :key="sid"
                    class="rounded-md border border-state-occupied/40 bg-state-occupied/10 px-2.5 py-1 text-sm tabular-nums text-state-occupied"
                  >{{ sid }}번</span>
                </div>
                <p v-else class="mt-2 text-sm text-fg-muted">이 시간에 점유된 좌석이 없습니다.</p>
              </div>
            </UiCard>

            <UiCard>
              <SectionHeader :title="rankingTitle" :description="`하루 종일 10분마다 확인한 점유 시간을 좌석별로 누적했습니다 · 상위 ${Math.min(8, seatRows.length)}석`" />
              <SeatRankBars class="mt-card" :rows="seatRows" :max-items="8" />
              <p v-if="selectedDay?.isToday" class="mt-card text-sm text-fg-muted">{{ rangeDescription }}이라 하루 전체 기록보다 적을 수 있습니다.</p>
            </UiCard>
          </div>
        </template>
      </section>
    </div>

    <!-- 시간표 설정 모달 -->
    <Teleport to="body">
      <ScheduleModal
        v-if="scheduleOpen && classroom"
        :classroom="classroom"
        @close="onScheduleClose"
      />
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { useClassroomStore } from '@/stores/classroomStore.js'
import ScheduleModal from '@/components/modals/ScheduleModal.vue'
import HourlyBarChart from '@/components/charts/HourlyBarChart.vue'
import SeatRankBars from '@/components/charts/SeatRankBars.vue'
import UiCard from '@/components/ui/UiCard.vue'
import MetricStat from '@/components/ui/MetricStat.vue'
import SectionHeader from '@/components/ui/SectionHeader.vue'
import ClassroomSeatMap from '@/components/monitoring/ClassroomSeatMap.vue'
import SeatDetailPanel from '@/components/monitoring/SeatDetailPanel.vue'
import SnapshotTimeline from '@/components/monitoring/SnapshotTimeline.vue'
import ErrorNotice from '@/components/ui/ErrorNotice.vue'
import { useSnapshotTimeline } from '@/composables/useSnapshotTimeline'
import { useDailyStats } from '@/composables/useDailyStats'
import api from '@/api'

const route = useRoute()
const cStore = useClassroomStore()
const classroom = computed(() => cStore.current)
const scheduleOpen = ref(false)

function onScheduleClose() {
  scheduleOpen.value = false
  fetchStats()
}

const WEEKDAY_LABELS = ['월', '화', '수', '목', '금', '토', '일']

function pad(n) { return String(n).padStart(2, '0') }
function toDateStr(d) { return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}` }
function isSameDate(a, b) { return toDateStr(a) === toDateStr(b) }

const today = new Date()

// 이번 주(월~일) 날짜 목록. 오늘 이후 날짜는 아직 기록이 없으므로 비활성화.
const weekDays = computed(() => {
  const dow = (today.getDay() + 6) % 7 // 월=0 ... 일=6
  const monday = new Date(today)
  monday.setDate(today.getDate() - dow)
  monday.setHours(0, 0, 0, 0)

  return WEEKDAY_LABELS.map((label, i) => {
    const d = new Date(monday)
    d.setDate(monday.getDate() + i)
    return {
      label,
      dateStr: toDateStr(d),
      shortDate: `${d.getMonth() + 1}/${d.getDate()}`,
      isToday: isSameDate(d, today),
      isFuture: d > today && !isSameDate(d, today),
    }
  })
})

const selectedDateStr = ref(toDateStr(today))

// 하루치 통계. 요일 탭을 빠르게 바꿀 때 늦게 온 응답이 최신 응답을 덮지 않고, 조회에 실패하면 이전 날짜
// 통계를 비운다(composables/useDailyStats.js, 단위 테스트 있음).
const { seatStats, periodMinutes, hourlyStats, loading, error: statsError, load: loadStats } = useDailyStats({
  fetchDaily: (date) => api.get(`/analysis/${route.params.id}/occupancy-stats-daily`, { params: { date } }).then((r) => r.data),
  fetchHourly: (date) => api.get(`/analysis/${route.params.id}/occupancy-hourly`, { params: { date } }).then((r) => r.data),
  dateStr: selectedDateStr,
})
const selectedHour = ref(null)

function toggleHour(hour) {
  selectedHour.value = selectedHour.value === hour ? null : hour
}

const selectedHourData = computed(() => hourlyStats.value.find(h => h.hour === selectedHour.value) ?? null)

// 선택된 시간대가 없으면 점유율이 가장 높은 시간대를 대신 보여준다
const peakHourData = computed(() => {
  const scheduled = hourlyStats.value.filter(h => h.scheduled && h.occupied !== null)
  if (!scheduled.length) return null
  return scheduled.reduce((max, h) => (h.occupied > (max?.occupied ?? -1) ? h : max), null)
})

const displayHourData = computed(() => selectedHourData.value ?? peakHourData.value)

async function fetchStats() {
  selectedHour.value = null
  await loadStats()
}

// 관리자가 설정해 놓은 전체 좌석 번호(숫자 오름차순)
const realSeatIds = computed(() => {
  const ids = new Set()
  for (const cam of classroom.value?.cameras ?? []) {
    for (const sid of cam.seat_ids ?? []) ids.add(sid)
  }
  return [...ids].sort((a, b) => Number(a) - Number(b))
})

const allSeatIds = realSeatIds

// ── 배치도 + 스냅샷 타임라인 ─────────────────────────────────────────────────
const classroomId = computed(() => Number(route.params.id))

// 맵 에디터가 저장한 배치도를 읽기만 한다(저장 형식/저장 요청 없음)
const mapData = ref(null)
const mapLoading = ref(true)

async function loadMap() {
  mapLoading.value = true
  try {
    const { data } = await api.get(`/classrooms/${classroomId.value}/map-data`)
    mapData.value = data?.objects?.length ? data : null
  } catch {
    mapData.value = null // 404: 배치도 미등록
  } finally {
    mapLoading.value = false
  }
}

const { slots, index, current, isLatest, seatStates, hasRecord, playing, intervalMin, load: loadTimeline, scrub, togglePlay, start: startTimeline, stop: stopTimeline } =
  useSnapshotTimeline({ classroomId, dateStr: selectedDateStr, seatIds: realSeatIds })

const selectedSeat = ref(null)
const selectSeat = (id) => { selectedSeat.value = selectedSeat.value === id ? null : id }
const selectedCamera = computed(() => classroom.value?.cameras.find((c) => (c.seat_ids ?? []).includes(selectedSeat.value)) ?? null)

// 마운트 중 await가 끝나기 전에 화면을 떠나면 onUnmounted(stopTimeline)이 먼저 실행된다. 그 뒤에 startTimeline()이
// 호출되면 1초 타이머가 정리되지 않고 남으므로, 떠난 뒤에는 시작하지 않는다.
let unmounted = false
onMounted(async () => {
  await cStore.fetchOne(classroomId.value)
  if (unmounted) return
  await Promise.all([fetchStats(), loadMap(), loadTimeline()])
  if (unmounted) return
  startTimeline()
})
onUnmounted(() => {
  unmounted = true
  stopTimeline()
})

watch(selectedDateStr, fetchStats)

const hasAnyData = computed(() => Object.keys(seatStats.value).length > 0)

function formatMinutes(min) {
  if (min <= 0) return '0분'
  const h = Math.floor(min / 60)
  const m = min % 60
  return h ? `${h}시간 ${m}분` : `${m}분`
}

// 오래 점유한 좌석 순으로 정렬 (막대는 최댓값을 100%로 맞춘 상대 비율). 점유 기록이 없으면 번호순.
const seatRows = computed(() => {
  const maxMinutes = Math.max(1, ...allSeatIds.value.map(sid => seatStats.value[sid]?.occupied_minutes ?? 0))
  const rows = allSeatIds.value.map(seatId => {
    const s = seatStats.value[seatId]
    const occupiedMinutes = s?.occupied_minutes ?? 0
    const barPct = Math.round((occupiedMinutes / maxMinutes) * 100)
    return { seatId, occupiedMinutes, barPct, timeText: formatMinutes(occupiedMinutes) }
  })
  return rows.sort((a, b) => b.occupiedMinutes - a.occupiedMinutes || Number(a.seatId) - Number(b.seatId))
})

const topSeat = computed(() => seatRows.value[0] ?? null)
const hasTopSeat = computed(() => topSeat.value != null && topSeat.value.occupiedMinutes > 0)

const selectedDay = computed(() => weekDays.value.find(d => d.dateStr === selectedDateStr.value))

const selectedDayLabel = computed(() => {
  const d = selectedDay.value
  if (!d) return ''
  return `${d.shortDate} (${d.label})`
})

const rangeDescription = computed(() => {
  const d = selectedDay.value
  if (!d) return ''
  return d.isToday ? `0:00 ~ 지금까지 (${formatMinutes(periodMinutes.value)})` : '하루 전체 기준'
})

const rankingTitle = computed(() => {
  const d = selectedDay.value
  if (!d) return '가장 오래 사용된 좌석'
  return d.isToday ? '오늘 가장 오래 사용된 좌석' : `${d.shortDate}(${d.label}) 가장 오래 사용된 좌석`
})
</script>
