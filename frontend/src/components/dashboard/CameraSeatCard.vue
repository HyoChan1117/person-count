<template>
  <UiCard>
    <div class="flex items-center justify-between gap-2">
      <h3 class="min-w-0 truncate text-base font-medium text-fg" :title="cam.name">{{ cam.name }}</h3>
      <span class="shrink-0 rounded-full border border-line px-2.5 py-0.5 text-sm font-semibold tabular-nums text-fg">{{ cam.occupied_count }}/{{ cam.total }}석</span>
    </div>

    <!-- 조회 실패는 상태색이 아닌 중립 안내로 알린다 -->
    <p v-if="cam.error" class="mt-3 text-sm text-fg-muted">{{ errorText }}</p>

    <div v-else-if="cam.occupied?.length" class="mt-3 flex flex-wrap gap-1.5">
      <span
        v-for="s in cam.occupied"
        :key="'occ-' + s"
        class="rounded-md border border-state-occupied/40 bg-state-occupied/10 px-2 py-0.5 text-sm font-medium tabular-nums text-state-occupied"
      >{{ s }}</span>
    </div>
  </UiCard>
</template>

<script setup>
import { computed } from 'vue'
import UiCard from '@/components/ui/UiCard.vue'

// 카메라 한 대의 분석 결과(점유 좌석 번호 / 빈 좌석 번호).
const props = defineProps({
  cam: { type: Object, required: true }, // { name, total, occupied_count, occupied[], empty[], error? }
  // 캡처 실패한 카메라를 "판정 불가"로 보여 줄지(YOLO 분석). false면 개수 배지를 그대로 두고 오류 문구만 붙인다(YOLO+LLM).
  unknownOnError: { type: Boolean, default: false },
})

const errorText = computed(() =>
  props.unknownOnError ? `캡처 실패로 ${props.cam.total}석을 판정하지 못했습니다. (${props.cam.error})` : props.cam.error,
)
</script>
