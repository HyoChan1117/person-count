<template>
  <div class="ds-root flex h-full flex-col overflow-hidden p-section">
    <div class="mx-auto flex w-full max-w-[1680px] flex-1 flex-col gap-gutter overflow-hidden">
    <header class="flex shrink-0 items-end justify-between gap-gutter">
      <div>
        <router-link to="/face" class="text-sm text-fg-muted transition-colors hover:text-fg">← 얼굴 인식</router-link>
        <h1 class="mt-1 text-3xl font-bold tracking-tight text-fg">모니터링</h1>
        <p class="mt-1 text-fg-muted">{{ place?.name }} 순찰 중 감지된 인물</p>
      </div>
    </header>

    <!-- 2xl(1536px) 미만에서는 좌측 패널을 줄여 감지 기록 행에 이름이 들어갈 폭을 남긴다 -->
    <!-- 불러오기에 실패하면 "등록된 장소 없음"처럼 보이는 빈 패널 대신 오류와 재시도만 보여준다 -->
    <ErrorNotice v-if="loadError" class="shrink-0" title="모니터링 정보를 불러오지 못했습니다" :message="loadError" @retry="load" />

    <div v-else class="grid min-h-0 flex-1 grid-cols-[minmax(0,24rem)_minmax(0,1fr)] gap-gutter 2xl:grid-cols-[minmax(0,34rem)_minmax(0,1fr)]">
      <!-- 좌: 순찰 라이브 + 자리별 결과 -->
      <div class="flex min-h-0 flex-col gap-gutter overflow-y-auto pr-1">
        <PatrolLivePanel
          :place="place"
          :status="status"
          :phase="phase"
          :estimated="estimated"
          :pass-through="passThrough"
          :next-zone="nextZone"
          :busy="busy"
          v-model:record-all="recordAll"
          @toggle="toggle"
        />

        <UiCard v-if="seatLogs.length" class="flex flex-col gap-gutter">
          <SectionHeader title="자리별 결과" :description="`검증 ${counts.verified}명 · 미검증 ${counts.unverified}명 · 빈자리 ${counts.empty}개`">
            <template #actions>
              <select v-model="logIndex" name="seat-log" aria-label="순찰 회차" class="rounded-lg border border-line bg-card px-3 py-2 text-sm text-fg focus-visible:outline focus-visible:outline-2 focus-visible:outline-fg-muted">
                <option v-for="(s, i) in seatLogs" :key="i" :value="i">{{ s.ts.replace('T', ' ').slice(0, 16) }}{{ i === 0 ? ' (최근)' : '' }}</option>
              </select>
            </template>
          </SectionHeader>
          <div class="flex flex-wrap gap-2">
            <div
              v-for="s in sortedSeats"
              :key="s.num"
              class="w-16 rounded-lg border px-1.5 py-1.5 text-center"
              :class="seatClass(s)"
              :title="s.empty ? '비어있음' : `${s.name ?? '미등록 인물'} · 유사도 ${s.score} · ${s.zone}`"
            >
              <div class="text-sm font-semibold tabular-nums">{{ s.num }}</div>
              <div class="truncate text-xs">{{ s.empty ? '빈자리' : (s.name ?? '미등록') }}</div>
            </div>
          </div>
        </UiCard>
      </div>

      <!-- 우: 감지 로그 -->
      <UiCard class="flex min-h-0 flex-col gap-gutter">
        <SectionHeader title="감지 기록" description="썸네일은 기본 블러 처리되며, 클릭하면 공개됩니다.">
          <template #actions>
            <button v-if="detections.length" type="button" class="text-sm text-fg-muted transition-colors hover:text-state-alert" @click="clearAll">전체 삭제</button>
          </template>
        </SectionHeader>
        <DetectionFilters
          v-model:period="period"
          v-model:zone="zone"
          v-model:registration="registration"
          :zones="zones"
          :count="filtered.length"
          :total="detections.length"
          :is-filtered="isFiltered"
          @reset="reset"
        />
        <p v-if="loading" class="flex-1 py-12 text-center text-fg-muted">불러오는 중...</p>
        <DetectionFeed v-else :items="filtered" :empty="!detections.length" @zoom="zoomed = $event" @remove="removeOne" />
      </UiCard>
    </div>

    <!-- 사진 크게 보기 (블러를 이미 해제한 뒤에만 열린다) -->
    <div v-if="zoomed" class="fixed inset-0 z-50 flex items-center justify-center bg-canvas/85 p-section" role="dialog" aria-label="감지 사진" @click="zoomed = null" @keydown.esc="zoomed = null">
      <img :src="`/api/face/detections/${zoomed.id}/photo`" class="max-h-full max-w-full rounded-card" alt="감지 사진 크게 보기" />
    </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import api from '@/api'
import UiCard from '@/components/ui/UiCard.vue'
import SectionHeader from '@/components/ui/SectionHeader.vue'
import PatrolLivePanel from '@/components/face/PatrolLivePanel.vue'
import DetectionFilters from '@/components/face/DetectionFilters.vue'
import DetectionFeed from '@/components/face/DetectionFeed.vue'
import ErrorNotice from '@/components/ui/ErrorNotice.vue'
import { usePatrolPhase } from '@/composables/usePatrolPhase'
import { useDetectionFilters } from '@/composables/useDetectionFilters'

const route = useRoute()
const placeId = route.params.id

const place = ref(null)
const detections = ref([])
const status = ref({ running: false, zone: null, zone_index: 0, total_zones: 0, detections: 0, completed: false, error: null })
const loading = ref(true)
const busy = ref(false)
const zoomed = ref(null)
const recordAll = ref(false) // 개발 확인용: 허가된 인원까지 촬영
const seatLogs = ref([]) // 순찰 1회분 자리별 결과 (최신순)
const logIndex = ref(0)

const zoneList = computed(() => place.value?.zones ?? [])
const { phase, estimated, nextZone, passThrough } = usePatrolPhase(status, zoneList)
const { period, zone, registration, zones, filtered, isFiltered, reset } = useDetectionFilters(detections)

const currentLog = computed(() => seatLogs.value[logIndex.value] ?? null)

// 자리 번호 순으로 정렬해서 보여준다 ('30' 같은 문자열 키라 숫자로 비교)
const sortedSeats = computed(() => {
  if (!currentLog.value) return []
  return Object.entries(currentLog.value.seats)
    .sort(([a], [b]) => (Number(a) || 0) - (Number(b) || 0))
    .map(([num, v]) => ({ num, empty: v === null, ...(v ?? {}) }))
})

const counts = computed(() => ({
  verified: sortedSeats.value.filter((s) => !s.empty && s.verified).length,
  unverified: sortedSeats.value.filter((s) => !s.empty && !s.verified).length,
  empty: sortedSeats.value.filter((s) => s.empty).length,
}))

// 경고색은 미등록 인물에만 쓴다. 등록됐지만 미허가인 사람은 중립 톤.
function seatClass(s) {
  if (s.empty) return 'border-line text-fg-muted'
  if (s.verified) return 'border-state-occupied/60 bg-state-occupied/10 text-fg'
  if (s.name == null) return 'border-state-alert/60 bg-state-alert/10 text-state-alert'
  return 'border-line text-fg'
}

async function fetchAll() {
  const [placeRes, detectionRes, statusRes, seatLogRes] = await Promise.all([
    api.get(`/face/places/${placeId}`),
    api.get(`/face/places/${placeId}/detections`),
    api.get(`/face/places/${placeId}/patrol/status`),
    api.get(`/face/places/${placeId}/seat-logs`),
  ])
  place.value = placeRes.data
  detections.value = detectionRes.data.detections
  status.value = statusRes.data
  seatLogs.value = seatLogRes.data.snapshots
  logIndex.value = 0
  if (status.value.running) recordAll.value = !!status.value.record_all
  loading.value = false
}

// 순찰 중에만 1초마다 진행 상황과 새 기록을 갱신한다
let timer = null
let polling = false
async function poll() {
  if (polling || !status.value.running) return
  polling = true
  try {
    const { data } = await api.get(`/face/places/${placeId}/patrol/status`)
    const wasCount = status.value.detections
    const wasSeatsLogged = status.value.seats_logged ?? 0
    const wasRunning = status.value.running
    status.value = data
    if (wasRunning && !data.running) await fetchAll() // 순찰 완료 -> 자리 결과 갱신
    else if ((data.seats_logged ?? 0) !== wasSeatsLogged) {
      const res = await api.get(`/face/places/${placeId}/seat-logs`, { params: { limit: 50 } })
      seatLogs.value = res.data.snapshots
      logIndex.value = 0
    }
    else if (data.detections !== wasCount) {
      const res = await api.get(`/face/places/${placeId}/detections`)
      detections.value = res.data.detections
    }
  } catch { /* 일시적 실패는 다음 주기에 다시 시도 */ } finally {
    polling = false
  }
}

watch(() => status.value.running, (running) => {
  clearInterval(timer)
  timer = running ? setInterval(poll, 1000) : null
}, { immediate: true })

async function toggle() {
  busy.value = true
  try {
    if (status.value.running) {
      await api.post(`/face/places/${placeId}/patrol/stop`)
    } else {
      await api.post(`/face/places/${placeId}/patrol/start`, { record_all: recordAll.value })
    }
    await fetchAll()
  } catch (e) {
    alert(e.response?.data?.detail ?? e.message)
  } finally {
    busy.value = false
  }
}

async function removeOne(detection) {
  await api.delete(`/face/detections/${detection.id}`)
  detections.value = detections.value.filter((d) => d.id !== detection.id)
}

async function clearAll() {
  if (!confirm('이 장소의 감지 기록을 모두 삭제하시겠습니까?')) return
  await api.delete(`/face/places/${placeId}/detections`)
  detections.value = []
}

// 첫 로딩. 실패해도 loading을 반드시 끄고 오류를 보여준다(순찰 시작/종료·폴링에서 쓰는 fetchAll은 호출부가 처리한다)
const loadError = ref('')
async function load() {
  loading.value = true
  loadError.value = ''
  try {
    await fetchAll()
  } catch (e) {
    loadError.value = e.response?.data?.detail ?? e.message
  } finally {
    loading.value = false
  }
}

onMounted(load)
onUnmounted(() => clearInterval(timer))
</script>
