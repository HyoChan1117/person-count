<template>
  <div class="h-full overflow-y-auto bg-neutral-50 p-6 lg:p-8">
    <div class="max-w-5xl mx-auto">

      <!-- 헤더 -->
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
        <div>
          <router-link to="/face" class="inline-flex items-center gap-1 text-xs text-neutral-400 hover:text-neutral-600 transition mb-2">
            ← 얼굴 인식
          </router-link>
          <h1 class="text-2xl font-bold text-neutral-900 tracking-tight">모니터링</h1>
          <p class="text-sm text-neutral-500 mt-0.5">{{ place?.name }} 순찰 중 감지된 미허가 인물</p>
        </div>

        <div class="flex items-center gap-3 shrink-0">
          <label class="flex items-center gap-1.5 text-xs text-neutral-500 cursor-pointer select-none"
            :class="{ 'opacity-50 cursor-not-allowed': status.running }">
            <input type="checkbox" v-model="recordAll" :disabled="status.running" class="accent-violet-600" />
            허가 인원도 촬영
          </label>
          <button
            @click="toggle"
            :disabled="busy"
            class="inline-flex items-center gap-2 text-sm font-medium px-4 py-2 rounded-lg transition w-fit disabled:opacity-50"
            :class="status.running ? 'bg-red-600 text-white hover:bg-red-700' : 'bg-violet-600 text-white hover:bg-violet-700'"
          >
            <span class="w-1.5 h-1.5 rounded-full" :class="status.running ? 'bg-white animate-pulse' : 'bg-white/60'" />
            {{ status.running ? '순찰 중지' : status.completed ? '다시 순찰' : '순찰 시작' }}
          </button>
        </div>
      </div>

      <!-- 순찰 상태 -->
      <div class="bg-white border rounded-2xl shadow-sm p-5 mb-6"
        :class="status.running ? 'border-violet-200' : 'border-neutral-200'">
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div>
            <div class="text-[11px] text-neutral-400 mb-1">상태</div>
            <div class="text-sm font-semibold"
              :class="status.running ? 'text-violet-600' : status.completed ? 'text-emerald-600' : 'text-neutral-500'">
              {{ status.running ? '순찰 중' : status.completed ? '순찰 완료' : '대기' }}
            </div>
          </div>
          <div>
            <div class="text-[11px] text-neutral-400 mb-1">현재 구역</div>
            <div class="text-sm font-semibold text-neutral-700">{{ status.zone ?? '–' }}</div>
          </div>
          <div>
            <div class="text-[11px] text-neutral-400 mb-1">진행</div>
            <div class="text-sm font-semibold text-neutral-700 tabular-nums">
              {{ status.zone_index }} / {{ status.total_zones || place?.zones?.length || 0 }} 구역
            </div>
          </div>
          <div>
            <div class="text-[11px] text-neutral-400 mb-1">이번 순찰 감지</div>
            <div class="text-sm font-semibold text-neutral-700 tabular-nums">{{ status.detections }}건</div>
          </div>
        </div>

        <!-- 진행 막대 -->
        <div v-if="status.total_zones" class="mt-4 w-full h-1.5 bg-neutral-100 rounded-full overflow-hidden">
          <div
            class="h-full rounded-full transition-all duration-500"
            :class="status.completed ? 'bg-emerald-500' : 'bg-violet-500'"
            :style="{ width: `${Math.round(status.zone_index / status.total_zones * 100)}%` }"
          />
        </div>

        <p v-if="status.error" class="mt-4 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700">
          순찰이 중단되었습니다 — {{ status.error }}
        </p>
        <p v-else-if="status.completed" class="mt-4 text-[11px] text-emerald-600">
          한 바퀴를 모두 돌았습니다. 카메라는 마지막 구역({{ status.zone }})에 멈춰 있습니다.
        </p>
        <p v-else-if="!status.running" class="mt-4 text-[11px] text-neutral-400">
          등록된 구역 {{ place?.zones?.length ?? 0 }}개를 순서대로 한 바퀴 돌며, {{ recordAll ? '얼굴이 보이면 허가 여부와 상관없이' : '허가되지 않은 얼굴이 보이면' }} 사진을 남깁니다.
          마지막 구역에서 순찰이 끝납니다.
        </p>
      </div>

      <!-- 자리별 결과 -->
      <div v-if="seatLogs.length" class="bg-white border border-neutral-200 rounded-2xl shadow-sm p-5 mb-6">
        <div class="flex items-center justify-between gap-3 mb-4 flex-wrap">
          <div>
            <h2 class="text-sm font-semibold text-neutral-800">자리별 결과</h2>
            <p class="text-[11px] text-neutral-400 mt-0.5">
              검증 {{ counts.verified }}명 · 미검증 {{ counts.unverified }}명 · 빈자리 {{ counts.empty }}개
            </p>
          </div>
          <select v-model="logIndex" class="text-xs border border-neutral-200 rounded-lg px-2.5 py-1.5 focus:outline-none focus:ring-2 focus:ring-violet-400">
            <option v-for="(s, i) in seatLogs" :key="i" :value="i">
              {{ s.ts.replace('T', ' ') }}{{ i === 0 ? ' (최근)' : '' }}
            </option>
          </select>
        </div>

        <div class="flex flex-wrap gap-1.5">
          <div
            v-for="s in sortedSeats"
            :key="s.num"
            class="w-16 rounded-lg border px-1.5 py-1.5 text-center"
            :class="s.empty ? 'border-neutral-200 bg-neutral-50'
              : s.verified ? 'border-emerald-200 bg-emerald-50'
              : 'border-red-200 bg-red-50'"
            :title="s.empty ? '비어있음' : `${s.name ?? '미등록 인물'} · 유사도 ${s.score} · ${s.zone}`"
          >
            <div class="text-sm font-bold tabular-nums"
              :class="s.empty ? 'text-neutral-300' : s.verified ? 'text-emerald-700' : 'text-red-600'"
            >{{ s.num }}</div>
            <div class="text-[10px] truncate"
              :class="s.empty ? 'text-neutral-300' : s.verified ? 'text-emerald-600' : 'text-red-500'"
            >{{ s.empty ? '빈자리' : (s.name ?? '미등록') }}</div>
          </div>
        </div>
      </div>

      <!-- 감지 기록 -->
      <div class="flex items-center justify-between mb-3">
        <h2 class="text-sm font-semibold text-neutral-800">감지 기록 {{ detections.length ? `(${detections.length}건)` : '' }}</h2>
        <button
          v-if="detections.length"
          @click="clearAll"
          class="text-xs text-neutral-400 hover:text-red-500 transition"
        >전체 삭제</button>
      </div>

      <div v-if="loading" class="text-center py-12 text-neutral-400">불러오는 중...</div>

      <div v-else-if="!detections.length" class="bg-white border border-neutral-200 rounded-2xl shadow-sm">
        <div class="flex flex-col items-center justify-center py-20 text-neutral-400 gap-3 text-center px-6">
          <div class="w-14 h-14 rounded-2xl bg-neutral-100 flex items-center justify-center text-2xl">🗂</div>
          <p class="text-sm">아직 감지 기록이 없습니다.</p>
          <p class="text-xs max-w-sm">
            순찰을 시작하면 미허가 인물이 촬영된 사진이 여기에 쌓입니다.
            <router-link :to="`/face/${placeId}/zones`" class="text-violet-600 hover:underline">구역 등록</router-link>과
            <router-link to="/face/people" class="text-violet-600 hover:underline">인물 등록</router-link>을 먼저 확인해주세요.
          </p>
        </div>
      </div>

      <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <div
          v-for="d in detections"
          :key="d.id"
          class="bg-white border border-neutral-200 rounded-2xl shadow-sm overflow-hidden group"
        >
          <img
            :src="`/api/face/detections/${d.id}/photo`"
            class="w-full aspect-video object-cover bg-neutral-900 cursor-pointer"
            @click="zoomed = d"
          />
          <div class="p-4">
            <div class="flex items-start justify-between gap-2 mb-1.5">
              <span class="text-sm font-semibold" :class="d.authorized || d.name ? 'text-neutral-800' : 'text-red-600'">
                {{ d.name ?? '미등록 인물' }}
              </span>
              <div class="flex items-center gap-1.5 shrink-0">
                <span class="text-[11px] font-medium px-2 py-0.5 rounded-full"
                  :class="d.authorized ? 'bg-emerald-50 text-emerald-700' : 'bg-red-50 text-red-600'">
                  {{ d.authorized ? '허가됨' : d.name ? '미허가' : '미등록' }}
                </span>
                <button
                  @click="removeOne(d)"
                  title="기록 삭제"
                  class="text-neutral-300 hover:text-red-400 opacity-0 group-hover:opacity-100 transition text-xs"
                >✕</button>
              </div>
            </div>
            <div class="text-[11px] text-neutral-400 tabular-nums">
              {{ d.zone_name }} · {{ d.ts?.replace('T', ' ') }}
              <span v-if="d.score"> · 유사도 {{ d.score.toFixed(2) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 사진 크게 보기 -->
    <div v-if="zoomed" class="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-6" @click="zoomed = null">
      <img :src="`/api/face/detections/${zoomed.id}/photo`" class="max-w-full max-h-full rounded-xl" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import api from '@/api'

const route = useRoute()
const placeId = route.params.id

const place = ref(null)
const detections = ref([])
const status = ref({ running: false, zone: null, zone_index: 0, total_zones: 0, detections: 0, completed: false, error: null })
const loading = ref(true)
const busy = ref(false)
const zoomed = ref(null)
const recordAll = ref(false)   // 개발 확인용: 허가된 인원까지 촬영
const seatLogs = ref([])       // 순찰 1회분 자리별 결과 (최신순)
const logIndex = ref(0)

const currentLog = computed(() => seatLogs.value[logIndex.value] ?? null)

// 자리 번호 순으로 정렬해서 보여준다 ('30' 같은 문자열 키라 숫자로 비교)
const sortedSeats = computed(() => {
  if (!currentLog.value) return []
  return Object.entries(currentLog.value.seats)
    .sort(([a], [b]) => (Number(a) || 0) - (Number(b) || 0))
    .map(([num, v]) => ({ num, empty: v === null, ...(v ?? {}) }))
})

const counts = computed(() => ({
  verified: sortedSeats.value.filter(s => !s.empty && s.verified).length,
  unverified: sortedSeats.value.filter(s => !s.empty && !s.verified).length,
  empty: sortedSeats.value.filter(s => s.empty).length,
}))
let timer = null

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

// 순찰 중에는 진행 상황과 새 기록을 주기적으로 갱신한다
async function poll() {
  if (!status.value.running) return   // 순찰이 끝났으면 더 물어볼 필요가 없다
  try {
    const { data } = await api.get(`/face/places/${placeId}/patrol/status`)
    const wasCount = status.value.detections
    const wasRunning = status.value.running
    status.value = data
    if (wasRunning && !data.running) await fetchAll()   // 순찰 완료 -> 자리 결과 갱신
    if (data.detections !== wasCount) {
      const res = await api.get(`/face/places/${placeId}/detections`)
      detections.value = res.data.detections
    }
  } catch { /* 일시적 실패는 다음 주기에 다시 시도 */ }
}

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
  detections.value = detections.value.filter(d => d.id !== detection.id)
}

async function clearAll() {
  if (!confirm('이 장소의 감지 기록을 모두 삭제하시겠습니까?')) return
  await api.delete(`/face/places/${placeId}/detections`)
  detections.value = []
}

onMounted(async () => {
  await fetchAll()
  timer = setInterval(poll, 3000)
})

onUnmounted(() => clearInterval(timer))
</script>
