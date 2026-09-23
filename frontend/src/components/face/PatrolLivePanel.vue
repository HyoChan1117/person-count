<template>
  <UiCard class="flex flex-col gap-card">
    <SectionHeader title="순찰 라이브" :description="place ? place.name : '등록된 장소 없음'">
      <template #actions>
        <span class="rounded-full border border-line px-3 py-1 text-sm font-medium" :class="status.running ? 'text-fg' : 'text-fg-muted'">{{ stateText }}</span>
      </template>
    </SectionHeader>

    <template v-if="place">
      <div class="flex items-center gap-4">
        <button
          type="button"
          class="rounded-lg px-5 py-2.5 text-sm font-semibold transition-colors disabled:opacity-50"
          :class="status.running ? 'border border-line text-fg hover:border-fg-muted/60' : 'bg-fg text-canvas hover:bg-fg/90'"
          :disabled="busy"
          @click="emit('toggle')"
        >{{ status.running ? '순찰 중지' : status.completed ? '다시 순찰' : '순찰 시작' }}</button>
        <label class="flex cursor-pointer select-none items-center gap-2 text-sm text-fg-muted" :class="{ 'cursor-not-allowed opacity-50': status.running }">
          <input :checked="recordAll" name="record-all" type="checkbox" class="accent-fg" :disabled="status.running" @change="emit('update:recordAll', $event.target.checked)" />
          허가 인원도 촬영
        </label>
      </div>

      <!-- 10분 주기 정기 순찰 on/off. 꺼도 위의 '순찰 시작'으로 직접 돌릴 수 있다.
           상태색 4가지는 좌석/경고 전용이라 여기서는 중립 토큰(fg/line)만 쓴다. -->
      <div class="flex items-center justify-between gap-gutter border-t border-line pt-4">
        <div class="min-w-0">
          <p class="text-label text-fg">자동 순찰</p>
          <p class="mt-0.5 text-sm text-fg-muted">
            {{ autoPatrol ? '10분마다 한 바퀴씩 자동으로 돕니다' : '꺼짐 · 수동으로만 순찰합니다' }}
          </p>
        </div>
        <button
          type="button"
          role="switch"
          :aria-checked="autoPatrol"
          aria-label="자동 순찰"
          :disabled="busy"
          class="relative h-7 w-12 shrink-0 rounded-full border transition-colors disabled:cursor-not-allowed disabled:opacity-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-fg-muted"
          :class="autoPatrol ? 'border-fg bg-fg' : 'border-line bg-line/50'"
          @click="emit('toggle-auto')"
        >
          <span
            class="absolute top-1/2 h-5 w-5 -translate-y-1/2 rounded-full transition-all"
            :class="autoPatrol ? 'left-[1.375rem] bg-canvas' : 'left-1 bg-fg-muted'"
          />
        </button>
      </div>

      <div class="grid grid-cols-2 gap-gutter">
        <div>
          <p class="text-label text-fg-muted">현재 구역</p>
          <p class="mt-1 truncate text-2xl font-semibold text-fg">{{ status.running ? zoneText : '–' }}</p>
        </div>
        <div>
          <p class="text-label text-fg-muted">다음 구역</p>
          <p class="mt-1 truncate text-2xl font-semibold text-fg-muted">{{ nextText }}</p>
        </div>
      </div>

      <PatrolStepper :zones="place.zones" :current="status.zone_index" :running="status.running" :completed="status.completed" />

      <div>
        <div class="mb-2 flex items-center justify-between">
          <p class="text-label text-fg-muted">단계</p>
          <p v-if="status.running && estimated" class="text-xs text-fg-muted" title="서버가 단계를 알려주지 않아 구역이 바뀐 뒤 경과 시간으로 추정한 값입니다">경과 시간 기준 추정</p>
        </div>
        <ol class="grid grid-cols-4 gap-2" aria-label="순찰 단계">
          <li
            v-for="s in PHASE_STEPS"
            :key="s.key"
            class="rounded-lg border py-2 text-center text-sm font-medium transition-colors"
            :class="phase === s.key ? 'border-fg bg-fg/10 text-fg' : 'border-line text-fg-muted'"
            :aria-current="phase === s.key ? 'step' : undefined"
          >{{ s.label }}</li>
        </ol>
        <p v-if="status.running && passThrough" class="mt-2 text-xs text-fg-muted">자리 영역이 없는 구역이라 인식 없이 지나갑니다.</p>
      </div>

      <div class="flex items-baseline justify-between border-t border-line pt-4">
        <span class="text-label text-fg-muted">이번 순찰 감지</span>
        <span class="text-2xl font-semibold tabular-nums text-fg">{{ status.detections }}<span class="text-base text-fg-muted"> 건</span></span>
      </div>

      <p v-if="status.error" class="rounded-lg border border-line px-3 py-2 text-sm text-fg">순찰이 중단되었습니다 — {{ status.error }}</p>
      <p v-else-if="returning" class="text-sm text-fg-muted">순찰을 중지했습니다. 카메라를 초기 위치로 되돌리는 중...</p>
      <p v-else-if="returnedZone && !status.running" class="text-sm text-fg-muted">순찰을 중지하고 카메라를 초기 위치로 되돌렸습니다 — {{ returnedZone }}</p>
      <p v-else-if="status.completed && !status.running" class="text-sm text-fg-muted">한 바퀴를 모두 돌았습니다. 카메라는 마지막 구역({{ zoneText }})에 멈춰 있습니다.</p>
    </template>
  </UiCard>
</template>

<script setup>
import { computed } from 'vue'
import UiCard from '@/components/ui/UiCard.vue'
import SectionHeader from '@/components/ui/SectionHeader.vue'
import PatrolStepper from './PatrolStepper.vue'
import { PHASE_STEPS } from '@/composables/usePatrolPhase'
import { zoneLabel } from '@/utils/patrolZone'

const props = defineProps({
  place: { type: Object, default: null }, // { name, zones[{id,name,rois}] }
  status: { type: Object, required: true },
  phase: { type: String, default: null },
  estimated: { type: Boolean, default: false },
  passThrough: { type: Boolean, default: false },
  nextZone: { type: Object, default: null },
  busy: { type: Boolean, default: false },
  // 중지 후 초기 고정 구역으로 되돌리는 중 / 되돌린 구역 이름
  returning: { type: Boolean, default: false },
  returnedZone: { type: String, default: '' },
  // 10분 주기 정기 순찰 대상인지 (장소별 설정)
  autoPatrol: { type: Boolean, default: true },
  recordAll: { type: Boolean, default: false },
})
const emit = defineEmits(['toggle', 'toggle-auto', 'update:recordAll'])

const stateText = computed(() => (props.status.running ? '순찰 중' : props.status.completed ? '순찰 완료' : '대기'))
const zoneText = computed(() => zoneLabel(props.status, props.place?.zones))
const nextText = computed(() => {
  if (!props.status.running) return '–'
  return props.nextZone ? props.nextZone.name : '종료 (마지막 구역)'
})
</script>
