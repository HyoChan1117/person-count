<template>
  <div class="h-full overflow-y-auto bg-neutral-50 p-6">
    <div class="max-w-3xl mx-auto">
      <router-link to="/classrooms" class="text-xs text-neutral-400 hover:text-neutral-600">← 목록</router-link>

      <div class="mt-2 mb-4 flex items-start justify-between gap-4">
        <div>
          <h1 class="text-xl font-bold text-neutral-800">좌석별 누적 점유 시간</h1>
          <p class="text-xs text-neutral-400 mt-1">{{ classroom?.name }}</p>
        </div>
        <button
          v-if="classroom"
          @click="scheduleOpen = true"
          class="text-xs bg-white border border-neutral-200 text-neutral-600 px-3 py-1.5 rounded-lg hover:bg-neutral-50 transition shrink-0"
        >📅 시간표 설정</button>
      </div>

      <!-- 요일 선택 (매주 월요일 00시에 기록이 초기화되므로 이번 주 요일 단위로 조회) -->
      <div class="grid grid-cols-7 gap-1.5 mb-5">
        <button
          v-for="day in weekDays"
          :key="day.dateStr"
          :disabled="day.isFuture"
          @click="selectedDateStr = day.dateStr"
          class="rounded-lg py-2 text-center transition"
          :class="[
            day.isFuture
              ? 'bg-neutral-50 text-neutral-300 cursor-not-allowed'
              : selectedDateStr === day.dateStr
                ? 'bg-blue-600 text-white shadow-sm'
                : 'bg-white text-neutral-600 border border-neutral-200 hover:border-blue-300 hover:text-blue-600',
          ]"
        >
          <div class="text-sm font-semibold">{{ day.label }}</div>
          <div class="text-[10px] mt-0.5" :class="day.isFuture ? 'text-neutral-300' : selectedDateStr === day.dateStr ? 'text-blue-100' : 'text-neutral-400'">
            {{ day.shortDate }}
          </div>
        </button>
      </div>

      <div v-if="loading" class="text-center py-20 text-neutral-400 text-sm">불러오는 중...</div>

      <div v-else-if="!hasAnyData" class="text-center py-20 text-neutral-400 text-sm">
        {{ selectedDayLabel }}에 저장된 점유 기록이 없습니다.<br>
        <span class="text-xs">10분마다 자동으로 좌석 점유 상태가 기록됩니다.</span>
      </div>

      <template v-else>
        <!-- 정각 기준 시간별 점유 좌석 수 -->
        <p class="text-xs text-neutral-400 mb-2">수업 시간인 09:00 ~ 21:00 사이, 교실별로 설정한 시간표에 따라 정각 기준으로 확인합니다.</p>
        <div class="flex flex-wrap gap-2 mb-2">
          <button
            v-for="h in hourlyStats"
            :key="h.hour"
            :disabled="!h.scheduled || h.occupied === null"
            @click="toggleHour(h.hour)"
            class="w-[74px] bg-white rounded-xl border py-2.5 text-center transition"
            :class="[
              !h.scheduled ? 'border-neutral-100 bg-neutral-50 cursor-not-allowed' : h.occupied === null ? 'border-neutral-200 cursor-not-allowed' : 'border-neutral-200 hover:border-blue-300',
              selectedHour === h.hour ? '!border-blue-500 ring-1 ring-blue-500' : '',
            ]"
          >
            <div
              class="w-5 h-5 mx-auto rounded-full flex items-center justify-center text-[11px] font-bold mb-1"
              :class="h.scheduled && h.occupied !== null ? 'bg-emerald-500 text-white' : 'bg-neutral-100 text-neutral-300'"
            >{{ h.scheduled && h.occupied !== null ? '✓' : '·' }}</div>
            <div class="text-xs font-semibold" :class="h.scheduled && h.occupied !== null ? 'text-neutral-700' : 'text-neutral-300'">{{ h.time }}</div>
            <div class="text-[10px] mt-0.5" :class="h.scheduled && h.occupied !== null ? 'text-neutral-400' : 'text-neutral-300'">
              {{ !h.scheduled ? '수업 없음' : h.occupied !== null ? `점유 ${h.occupied}석` : '대기중' }}
            </div>
          </button>
        </div>

        <!-- 선택한 정각의 점유 좌석 상세 -->
        <div v-if="selectedHourData" class="bg-blue-50/60 border border-blue-100 rounded-xl px-4 py-3 mb-6 text-sm">
          <div class="flex items-center gap-2 mb-2">
            <span class="font-semibold text-blue-700">{{ selectedHourData.time }}</span>
            <span class="text-xs text-neutral-500">점유 {{ selectedHourData.occupied }}석 / {{ selectedHourData.total }}석</span>
          </div>
          <div v-if="selectedHourData.seats?.length" class="flex flex-wrap gap-1.5">
            <span
              v-for="sid in selectedHourData.seats"
              :key="sid"
              class="text-xs px-2 py-0.5 rounded-full bg-red-100 text-red-700 font-medium"
            >{{ sid }}번</span>
          </div>
          <div v-else class="text-xs text-neutral-400">이 시간에 점유된 좌석이 없습니다.</div>
        </div>

        <!-- 가장 오래 점유한 좌석 순위 -->
        <h2 class="text-sm font-bold text-neutral-700 mb-1">{{ rankingTitle }}</h2>
        <p class="text-xs text-neutral-400 mb-2">하루 종일 10분마다 점유 여부를 확인해 좌석마다 누적한 시간입니다.</p>
        <div class="bg-white rounded-xl border border-neutral-200 p-4">
          <div
            v-for="(row, i) in seatRows"
            :key="row.seatId"
            class="flex items-center gap-3 py-1.5"
          >
            <span
              class="text-xs font-bold w-10 h-7 shrink-0 rounded-lg border flex items-center justify-center"
              :class="isTopRow(i, row) ? 'border-red-300 text-red-600 bg-red-50' : 'border-neutral-200 text-neutral-400 bg-neutral-50'"
            >{{ row.seatId }}</span>
            <div
              class="flex-1 h-3 rounded-full overflow-hidden bg-neutral-100"
              :class="isTopRow(i, row) && barsFilled ? 'gauge-glow' : ''"
              :title="`${row.seatId}번 · 점유 ${row.timeText} / ${rangeDescription}`"
            >
              <div
                class="h-full rounded-full duration-700 ease-out"
                :class="isTopRow(i, row) ? 'bg-red-400' : 'bg-red-100'"
                :style="{ width: (barsFilled ? row.barPct : 0) + '%', transitionProperty: 'width', transitionDelay: (i * 50) + 'ms' }"
              />
            </div>
            <span
              class="text-xs w-16 text-right shrink-0 tabular-nums"
              :class="isTopRow(i, row) ? 'text-neutral-700 font-semibold' : 'text-neutral-400'"
            >{{ row.timeText }}</span>
          </div>
        </div>
      </template>
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
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { useClassroomStore } from '@/stores/classroomStore.js'
import ScheduleModal from '@/components/modals/ScheduleModal.vue'
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

const loading = ref(false)
const seatStats = ref({})
const periodMinutes = ref(0)
const hourlyStats = ref([])
const selectedHour = ref(null)
const barsFilled = ref(false)

function toggleHour(hour) {
  selectedHour.value = selectedHour.value === hour ? null : hour
}

const selectedHourData = computed(() => hourlyStats.value.find(h => h.hour === selectedHour.value) ?? null)

async function fetchStats() {
  loading.value = true
  selectedHour.value = null
  barsFilled.value = false
  try {
    const [dailyRes, hourlyRes] = await Promise.all([
      api.get(`/analysis/${route.params.id}/occupancy-stats-daily`, { params: { date: selectedDateStr.value } }),
      api.get(`/analysis/${route.params.id}/occupancy-hourly`, { params: { date: selectedDateStr.value } }),
    ])
    seatStats.value = dailyRes.data.seats ?? {}
    periodMinutes.value = dailyRes.data.period_minutes ?? 0
    hourlyStats.value = hourlyRes.data.hours ?? []
  } catch (e) {
    alert('점유 기록 조회 실패: ' + (e.response?.data?.detail ?? e.message))
  } finally {
    loading.value = false
    // 막대를 0%로 먼저 그린 뒤 다음 프레임에 목표 길이로 전환해 게이지가 차오르는 것처럼 보이게 함
    await nextTick()
    requestAnimationFrame(() => { barsFilled.value = true })
  }
}

onMounted(async () => {
  await cStore.fetchOne(Number(route.params.id))
  await fetchStats()
})

watch(selectedDateStr, fetchStats)

// 관리자가 설정해 놓은 전체 좌석 번호(숫자 오름차순)
const allSeatIds = computed(() => {
  const ids = new Set()
  for (const cam of classroom.value?.cameras ?? []) {
    for (const sid of cam.seat_ids ?? []) ids.add(sid)
  }
  return [...ids].sort((a, b) => Number(a) - Number(b))
})

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

// 가장 오래 사용된 좌석(1위)만 강조 표시
function isTopRow(index, row) {
  return index === 0 && row.occupiedMinutes > 0
}

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

<style scoped>
/* 1위 좌석 게이지가 다 채워진 뒤 잠깐 반짝이며 시선을 끄는 효과 */
.gauge-glow {
  animation: gauge-glow 1.1s ease-out 0.7s 1;
}

@keyframes gauge-glow {
  0% { box-shadow: 0 0 0 0 rgba(248, 113, 113, 0.6); }
  60% { box-shadow: 0 0 8px 3px rgba(248, 113, 113, 0.35); }
  100% { box-shadow: 0 0 0 0 rgba(248, 113, 113, 0); }
}
</style>
