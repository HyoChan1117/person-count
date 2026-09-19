<template>
  <div class="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-6" @click.self="$emit('close')">
    <div class="bg-white dark:bg-neutral-900 rounded-2xl shadow-xl w-full max-w-4xl max-h-full overflow-y-auto">

      <!-- 헤더 -->
      <div class="px-6 py-4 border-b border-neutral-100 dark:border-neutral-800 flex items-center justify-between gap-4">
        <div>
          <h2 class="font-bold text-neutral-800 dark:text-neutral-100">{{ zone.name }} · 자리 영역(ROI) 설정</h2>
          <p class="text-xs text-neutral-500 dark:text-neutral-400 mt-0.5">앞쪽 선 2클릭, 뒤쪽 선 2클릭으로 자리를 감싸세요. 그 안에서 인식된 얼굴만 기록됩니다.</p>
        </div>
        <button @click="$emit('close')" class="text-neutral-400 dark:text-neutral-600 hover:text-neutral-600 dark:hover:text-neutral-300 shrink-0">✕</button>
      </div>

      <div class="p-6">
        <div v-if="error" class="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {{ error }}
        </div>

        <div v-else-if="!snapshotUrl" class="flex flex-col items-center justify-center py-20 text-neutral-400 dark:text-neutral-600 gap-3 text-sm">
          <div class="w-9 h-9 rounded-full border-2 border-neutral-200 dark:border-neutral-800 border-t-violet-500 animate-spin" />
          카메라를 구역으로 옮기는 중...
        </div>

        <template v-else>
          <!-- 진행 안내 -->
          <div class="mb-2 flex items-center gap-3 flex-wrap text-xs">
            <span class="font-semibold text-neutral-700 dark:text-neutral-300">자리 그리기</span>
            <span v-if="draft.length < 2" class="text-orange-600">① 앞쪽 선: 시작점 → 끝점 클릭</span>
            <span v-else-if="draft.length < 4" class="text-emerald-600">② 뒤쪽 선: 시작점 → 끝점 클릭 (4번째에 자동 완성)</span>
            <button v-if="draft.length" @click="draft.pop()" class="text-neutral-400 dark:text-neutral-600 hover:text-neutral-700 dark:hover:text-neutral-200 underline">되돌리기</button>
          </div>

          <!-- 그리기 영역 -->
          <div
            ref="stageRef"
            class="relative select-none rounded-xl overflow-hidden bg-neutral-900 cursor-crosshair"
            @click="onStageClick"
          >
            <img
              :src="snapshotUrl"
              class="w-full block pointer-events-none"
              @load="imageReady = true"
              @error="error = '카메라 화면을 가져오지 못했습니다. 카메라 연결을 확인해주세요.'"
            />

            <!-- 화면이 뜨기 전까지 안내 (이미지는 미리 붙여둬야 load 이벤트가 온다) -->
            <div v-if="!imageReady" class="absolute inset-0 flex flex-col items-center justify-center gap-3 text-sm text-neutral-300 dark:text-neutral-700">
              <div class="w-9 h-9 rounded-full border-2 border-neutral-600 border-t-violet-400 animate-spin" />
              화면을 가져오는 중...
            </div>

            <!-- 저장된 자리 영역과 그리는 중인 점/선 -->
            <svg viewBox="0 0 1 1" preserveAspectRatio="none" class="absolute inset-0 w-full h-full pointer-events-none">
              <polygon
                v-for="(r, i) in rois"
                :key="i"
                :points="hullPoints(r.points)"
                fill="rgba(139,92,246,0.25)"
                stroke="#a78bfa"
                stroke-width="0.004"
              />
              <!-- 앞선(주황) / 뒷선(초록) -->
              <line v-if="draft.length >= 2" :x1="draft[0][0]" :y1="draft[0][1]" :x2="draft[1][0]" :y2="draft[1][1]"
                stroke="#fb923c" stroke-width="0.005" />
              <line v-if="draft.length === 4" :x1="draft[2][0]" :y1="draft[2][1]" :x2="draft[3][0]" :y2="draft[3][1]"
                stroke="#34d399" stroke-width="0.005" />
              <circle v-for="(p, i) in draft" :key="'p'+i" :cx="p[0]" :cy="p[1]" r="0.006"
                :fill="i < 2 ? '#fb923c' : '#34d399'" />
            </svg>

            <!-- 자리 이름표 -->
            <span
              v-for="(r, i) in rois"
              :key="'label'+i"
              class="absolute text-[11px] bg-violet-600 text-white px-1.5 py-0.5 rounded whitespace-nowrap -translate-y-full"
              :style="labelStyle(r.points)"
            >{{ r.name }}</span>
          </div>

          <!-- 목록 -->
          <div class="mt-4">
            <div class="flex items-center justify-between mb-2">
              <span class="text-sm font-semibold text-neutral-800 dark:text-neutral-100">자리 {{ rois.length }}개</span>
              <button v-if="rois.length" @click="rois = []; draft = []" class="text-xs text-neutral-400 dark:text-neutral-600 hover:text-red-500 transition">모두 지우기</button>
            </div>

            <div v-if="!rois.length" class="text-xs text-neutral-400 dark:text-neutral-600 py-3">
              아직 지정한 자리가 없습니다. 화면을 클릭해 선을 그어보세요.
            </div>

            <div v-else class="grid grid-cols-1 sm:grid-cols-2 gap-2">
              <div v-for="(r, i) in rois" :key="i" class="flex items-center gap-2 rounded-lg border border-neutral-200 dark:border-neutral-800 px-3 py-2">
                <span class="w-5 h-5 rounded bg-violet-100 text-violet-700 text-[11px] flex items-center justify-center shrink-0">{{ i + 1 }}</span>
                <input v-model="r.name" class="flex-1 min-w-0 text-sm border-0 focus:outline-none" />
                <button @click="rois.splice(i, 1)" class="text-neutral-300 dark:text-neutral-700 hover:text-red-400 text-xs shrink-0">✕</button>
              </div>
            </div>
          </div>
        </template>
      </div>

      <!-- 하단 -->
      <div class="px-6 py-4 border-t border-neutral-100 dark:border-neutral-800 flex items-center justify-between gap-3">
        <p class="text-[11px] text-neutral-400 dark:text-neutral-600">
          구역의 팬·틸트·줌을 바꾸면 이 영역들은 화면과 어긋나므로 다시 지정해야 합니다.
        </p>
        <div class="flex gap-2 shrink-0">
          <button @click="$emit('close')" class="bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300 text-sm px-4 py-2 rounded-lg hover:bg-neutral-200 dark:hover:bg-neutral-700 transition">취소</button>
          <button @click="save" :disabled="saving || !imageReady" class="bg-violet-600 text-white text-sm px-4 py-2 rounded-lg hover:bg-violet-700 transition disabled:opacity-50">
            {{ saving ? '저장 중...' : '저장' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/api'

const props = defineProps({ placeId: [String, Number], zone: Object })
const emit = defineEmits(['close', 'saved'])

const imageReady = ref(false)   // 스냅샷 <img>가 실제로 표시됐는지
const saving = ref(false)
const error = ref('')
const snapshotUrl = ref('')
const stageRef = ref(null)
const rois = ref([])
const draft = ref([])          // 그리는 중인 점들 (앞선 2점 + 뒷선 2점)

// 점 4개를 볼록 다각형 순서로 정렬해 그린다. 백엔드 판정도 convexHull을 쓰므로 동일하다.
function hullPoints(points) {
  const cx = points.reduce((a, p) => a + p[0], 0) / points.length
  const cy = points.reduce((a, p) => a + p[1], 0) / points.length
  return [...points]
    .sort((a, b) => Math.atan2(a[1] - cy, a[0] - cx) - Math.atan2(b[1] - cy, b[0] - cx))
    .map(p => `${p[0]},${p[1]}`)
    .join(' ')
}

function labelStyle(points) {
  const x = Math.min(...points.map(p => p[0]))
  const y = Math.min(...points.map(p => p[1]))
  return { left: `${x * 100}%`, top: `${y * 100}%` }
}

// 화면 좌표 -> 0~1 비율 (해상도가 달라도 유지되도록)
function onStageClick(e) {
  if (!imageReady.value) return
  const rect = stageRef.value.getBoundingClientRect()
  const x = Math.min(1, Math.max(0, (e.clientX - rect.left) / rect.width))
  const y = Math.min(1, Math.max(0, (e.clientY - rect.top) / rect.height))
  draft.value.push([Number(x.toFixed(4)), Number(y.toFixed(4))])

  // 4점이 모이면 한 자리로 확정
  if (draft.value.length === 4) {
    rois.value.push({ name: `${rois.value.length + 1}번 자리`, points: draft.value })
    draft.value = []
  }
}

async function load() {
  try {
    // 그리는 화면과 순찰이 찍는 화면이 같아야 하므로 먼저 그 구역으로 이동시킨다
    await api.post(`/face/places/${props.placeId}/zones/${props.zone.id}/goto`)
    await new Promise(r => setTimeout(r, 2500))   // 이동·안정화 대기
    snapshotUrl.value = `/api/face/places/${props.placeId}/ptz/snapshot?t=${Date.now()}`
    rois.value = (props.zone.rois ?? []).map(r => ({ name: r.name, points: r.points.map(p => [...p]) }))
  } catch (e) {
    error.value = e.response?.data?.detail ?? e.message
  }
}

async function save() {
  saving.value = true
  try {
    await api.put(`/face/places/${props.placeId}/zones/${props.zone.id}/rois`, {
      rois: rois.value.map(r => ({ name: r.name, points: r.points })),
    })
    emit('saved')
    emit('close')
  } catch (e) {
    error.value = e.response?.data?.detail ?? e.message
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>
