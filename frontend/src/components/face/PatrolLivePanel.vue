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
  recordAll: { type: Boolean, default: false },
})
const emit = defineEmits(['toggle', 'update:recordAll'])

const stateText = computed(() => (props.status.running ? '순찰 중' : props.status.completed ? '순찰 완료' : '대기'))
const zoneText = computed(() => zoneLabel(props.status, props.place?.zones))
const nextText = computed(() => {
  if (!props.status.running) return '–'
  return props.nextZone ? props.nextZone.name : '종료 (마지막 구역)'
})
</script>
