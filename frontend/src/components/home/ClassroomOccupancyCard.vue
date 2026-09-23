<template>
  <!-- 가로로 긴 행 카드: 왼쪽에서 오른쪽으로 [교실] → [점유율] → [배치도] 순으로 읽힌다.
       누르면 화면을 옮기지 않고 홈 위에 요약 모달을 띄운다(부모가 연다). -->
  <UiCard interactive :padded="false" class="relative flex h-full items-center gap-card px-card py-4">
    <!-- 카드 전체를 덮는 버튼: 누르면 요약 모달이 열린다(글자·배치도는 이 버튼 아래에 깔린다) -->
    <button
      type="button"
      class="absolute inset-0 rounded-card focus-visible:outline focus-visible:outline-2 focus-visible:outline-fg-muted"
      :aria-label="`${room.name} 요약 보기`"
      @click="emit('open', $event.currentTarget)"
    />

    <div class="flex w-56 shrink-0 flex-col items-start gap-2">
      <h3 class="w-full truncate text-xl font-semibold text-fg" :title="room.name">{{ room.name }}</h3>
      <StatusBadge :status="badge.status" :label="badge.label" size="lg" />
    </div>

    <div class="min-w-0 flex-1">
      <div class="flex items-baseline gap-1">
        <span class="text-metric-sm tabular-nums" :class="pct > 0 ? 'text-state-occupied' : 'text-fg-muted'">{{ pct ?? '–' }}</span>
        <span v-if="pct != null" class="text-xl text-fg-muted">%</span>
      </div>
      <p class="mt-1 text-sm text-fg-muted tabular-nums">
        {{ room.occupied }} / {{ room.judgeable }}석
        <span v-if="room.unknown" class="text-state-unknown"> · 판정 불가 {{ room.unknown }}</span>
      </p>
    </div>

    <!-- 배치도의 책상 배치만 가져와 좌석 상태색으로 칠한다(클릭은 카드 전체 버튼에 맡긴다).
         카드 높이를 다 쓰지 않고 한 겹 줄여 카드 안에서 숨 쉴 여백을 남긴다 -->
    <div v-if="room.map" class="flex h-3/4 shrink-0 items-center">
      <SeatLayoutMini :map="room.map" :seat-states="seatStates" />
    </div>
    <SeatMiniBar v-else-if="room.seats.length" :seats="room.seats" class="w-48 shrink-0" />
    <div
      v-else
      class="flex h-full w-48 shrink-0 items-center justify-center rounded-lg border border-dashed border-line text-xs text-fg-muted"
    >배치도 미등록</div>

    <!-- 이 교실만 지금 다시 판정한다. 덮개 버튼 위로 올려야 눌린다. -->
    <button
      type="button"
      class="relative z-10 shrink-0 rounded-lg border border-line px-4 py-2.5 text-sm font-medium text-fg-muted transition-colors hover:border-fg-muted/60 hover:text-fg disabled:cursor-not-allowed disabled:opacity-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-fg-muted"
      :disabled="analyzing || !room.total"
      :title="room.total ? '이 교실의 좌석을 지금 다시 판정합니다' : '카메라와 좌석을 먼저 설정해주세요'"
      @click="emit('analyze')"
    >{{ analyzing ? '분석 중...' : '분석' }}</button>
  </UiCard>
</template>

<script setup>
import { computed } from 'vue'
import UiCard from '@/components/ui/UiCard.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import SeatLayoutMini from './SeatLayoutMini.vue'
import SeatMiniBar from './SeatMiniBar.vue'
import { roomStatus } from '@/utils/roomStatus'

const props = defineProps({
  room: { type: Object, required: true }, // { id, name, total, occupied, judgeable, unknown, seats[], map, error }
  analyzing: { type: Boolean, default: false },
})

const emit = defineEmits(['open', 'analyze'])

// 점유율 = 점유 ÷ 판정 가능 좌석. 판정 가능한 좌석이 없으면 null("–")
const pct = computed(() => (props.room.judgeable ? Math.round((props.room.occupied / props.room.judgeable) * 100) : null))

// 배치도는 좌석을 label로 찾으므로 { 좌석ID: 상태 } 형태로 바꿔 넘긴다
const seatStates = computed(() => Object.fromEntries(props.room.seats.map((s) => [s.id, s.state])))

// 오류·좌석 0개·판정 가능한 좌석 없음은 "비어 있음"이 아니라 "판정 불가"다(utils/roomStatus.js)
const BADGES = {
  unknown: { status: 'unknown', label: '판정 불가' },
  occupied: { status: 'occupied', label: '사용 중' },
  empty: { status: 'empty', label: '비어 있음' },
}
const badge = computed(() => BADGES[roomStatus(props.room)])
</script>
