<template>
  <!-- 1920x1080에서 카드가 교실 카드 한 행(217px)에 묶여 있어 위아래 여백만 20px로 준다(기본 24px).
       남는 높이는 블록 사이로 고르게 나눠 갖는다 — 높이가 달라져도 구성은 그대로다. -->
  <UiCard :padded="false" class="flex h-full flex-col justify-between gap-1.5 px-card py-5">
    <SectionHeader title="순찰 상태" :description="place ? place.name : '등록된 장소 없음'">
      <template #actions>
        <!-- 카드 높이는 교실 카드 한 행에 맞춰져 있어 여유가 없다. 조작은 제목 줄 오른쪽에 둔다.
             스위치 색은 상태색 4종(좌석·경고 전용)을 쓰지 않고 중립 토큰만 쓴다. -->
        <!-- 이 선택은 아래 '최근 감지 로그'까지 함께 바꾼다(전체를 고르면 순찰 중인 장소를 보여 준다) -->
        <select
          v-if="places.length"
          :value="selectedId ?? ''"
          aria-label="교실 선택"
          class="rounded-lg border border-line bg-card px-2 py-1.5 text-sm text-fg focus-visible:outline focus-visible:outline-2 focus-visible:outline-fg-muted"
          @change="emit('select', $event.target.value === '' ? null : Number($event.target.value))"
        >
          <option value="">전체</option>
          <option v-for="p in places" :key="p.id" :value="p.id">{{ p.name }}</option>
        </select>

        <template v-if="place">
          <span class="text-sm text-fg-muted">자동 순찰</span>
          <button
            type="button"
            role="switch"
            :aria-checked="autoPatrol"
            aria-label="자동 순찰"
            :disabled="busy"
            :title="autoPatrol ? '10분마다 자동으로 한 바퀴 돕니다' : '자동 순찰 꺼짐 · 수동으로만 순찰합니다'"
            class="relative h-6 w-11 shrink-0 rounded-full border transition-colors disabled:cursor-not-allowed disabled:opacity-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-fg-muted"
            :class="autoPatrol ? 'border-fg bg-fg' : 'border-line bg-line/50'"
            @click="emit('toggle-auto')"
          >
            <span
              class="absolute top-1/2 h-4 w-4 -translate-y-1/2 rounded-full transition-all"
              :class="autoPatrol ? 'left-[1.375rem] bg-canvas' : 'left-1 bg-fg-muted'"
            />
          </button>
          <button
            type="button"
            :disabled="busy || !place.hasCamera"
            :title="place.hasCamera ? '' : '카메라 설정에서 IP를 먼저 입력해주세요'"
            class="rounded-lg px-3 py-1.5 text-sm font-semibold transition-colors disabled:cursor-not-allowed disabled:opacity-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-fg-muted"
            :class="running ? 'border border-line text-fg hover:border-fg-muted/60' : 'bg-fg text-canvas hover:opacity-90'"
            @click="emit(running ? 'stop' : 'start')"
          >{{ running ? '순찰 중지' : status.completed ? '다시 순찰' : '순찰 시작' }}</button>
        </template>
      </template>
    </SectionHeader>

    <!-- 화면 높이와 상관없이 늘 같은 것만 보여 준다(자리에 따라 나타났다 사라지지 않게) -->
    <template v-if="place">
      <!-- 구역 정보 한 덩어리: 현재 구역·진행 단계와 그 진행을 나타내는 점 줄은 붙여 둔다 -->
      <div class="space-y-1.5">
      <div class="grid grid-cols-2 gap-gutter">
        <div>
          <p class="text-label text-fg-muted">현재 구역</p>
          <p class="mt-0.5 truncate text-xl font-semibold text-fg">{{ current || '–' }}</p>
        </div>
        <div>
          <p class="text-label text-fg-muted">진행 단계</p>
          <p class="mt-0.5 text-xl font-semibold tabular-nums text-fg">
            {{ status.zone_index }}<span class="text-fg-muted"> / {{ total }}</span>
          </p>
        </div>
      </div>

      <ol class="flex items-center gap-1.5" aria-label="구역 진행 단계">
        <li v-for="(z, i) in place.zones" :key="z.id" class="h-1 flex-1 rounded-full" :class="dotClass(i)" :title="z.name" />
      </ol>
      </div>

      <!-- 순찰 단계: 순찰 중이면 지금 단계가 켜지고, 아니면 네 칸 모두 회색 -->
      <div>
        <p class="text-label text-fg-muted">
          단계
          <span v-if="!running" class="ml-2 font-normal">순찰을 시작하면 여기에 표시됩니다</span>
        </p>
        <ol class="mt-1.5 grid grid-cols-4 gap-2" aria-label="순찰 단계">
          <li
            v-for="step in PHASE_STEPS"
            :key="step.key"
            class="rounded-lg border py-0.5 text-center text-sm font-medium transition-colors"
            :class="running && phase === step.key ? 'border-fg bg-fg/10 text-fg' : 'border-line text-fg-muted'"
            :aria-current="running && phase === step.key ? 'step' : undefined"
          >{{ step.label }}</li>
        </ol>
      </div>
    </template>
  </UiCard>
</template>

<script setup>
import { computed } from 'vue'
import UiCard from '@/components/ui/UiCard.vue'
import SectionHeader from '@/components/ui/SectionHeader.vue'
import { zoneLabel } from '@/utils/patrolZone'
import { usePatrolPhase, PHASE_STEPS } from '@/composables/usePatrolPhase'

const props = defineProps({
  place: { type: Object, default: null }, // { name, zones[{id,name}], status, autoPatrol }
  busy: { type: Boolean, default: false },
  places: { type: Array, default: () => [] },      // 고를 수 있는 장소 목록
  selectedId: { type: Number, default: null },     // null이면 전체
})
const emit = defineEmits(['start', 'stop', 'toggle-auto', 'select'])

const status = computed(() => props.place?.status ?? {})
const running = computed(() => !!status.value.running)
const autoPatrol = computed(() => props.place?.autoPatrol ?? true)
const total = computed(() => status.value.total_zones || props.place?.zones.length || 0)
const current = computed(() => zoneLabel(status.value, props.place?.zones))

// 단계(이동/대기/촬영/분석)는 모니터링 화면과 같은 방식으로 얻는다.
// 서버 응답에 phase가 있으면 그 값을, 없으면 구역이 바뀐 뒤 경과 시간으로 추정한다.
const { phase } = usePatrolPhase(status, computed(() => props.place?.zones ?? []))

// 완료/지나온 구역은 밝게, 현재 구역은 가장 밝게, 남은 구역은 경계선 색
function dotClass(i) {
  const idx = i + 1
  if (status.value.completed) return 'bg-fg-muted'
  if (!running.value) return 'bg-line'
  if (idx < status.value.zone_index) return 'bg-fg-muted'
  if (idx === status.value.zone_index) return 'bg-fg'
  return 'bg-line'
}
</script>
