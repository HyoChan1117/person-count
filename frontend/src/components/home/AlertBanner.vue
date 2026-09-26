<template>
  <!-- 새 미등록 인물이 감지되면 홈 맨 위에서 바로 알린다. 얼굴 사진은 넣지 않는다(사진은 감지 로그에서 클릭해야 공개). -->
  <div
    role="alert"
    class="flex flex-wrap items-center gap-x-gutter gap-y-2 rounded-card border border-l-4 border-state-alert/40 border-l-state-alert bg-state-alert/10 px-card py-3"
  >
    <span class="h-2.5 w-2.5 shrink-0 rounded-full bg-state-alert" aria-hidden="true" />
    <p class="shrink-0 text-xl font-bold text-state-alert">미등록 인물 감지 {{ alerts.length }}건</p>
    <!-- 좁아지면 이 문구가 다음 줄로 내려가 전체 폭을 쓴다(min-w) -->
    <p class="min-w-[14rem] flex-1 truncate text-lg text-fg">
      {{ latest.placeName }} · {{ latest.zone_name }} · {{ timeOf(latest.ts) }}
      <span v-if="alerts.length > 1" class="text-fg-muted">외 {{ alerts.length - 1 }}건</span>
    </p>
    <!-- 경과 시간은 30초마다 바뀌므로 스크린리더가 매번 읽지 않게 숨긴다 -->
    <span class="shrink-0 text-base tabular-nums text-fg-muted" aria-hidden="true">{{ ageText(latest.ts) }}</span>
    <router-link
      :to="`/face/${latest.placeId}/monitoring`"
      class="shrink-0 rounded-md px-2 py-0.5 text-base text-fg underline underline-offset-4 transition-colors hover:text-fg-muted focus-visible:outline focus-visible:outline-2 focus-visible:outline-fg-muted"
    >감지 기록 보기</router-link>
    <button
      type="button"
      class="shrink-0 rounded-lg border border-line bg-card px-4 py-2 text-base font-semibold text-fg transition-colors hover:border-fg-muted/60 focus-visible:outline focus-visible:outline-2 focus-visible:outline-fg-muted"
      @click="emit('ack')"
    >확인</button>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

// 최신순으로 정렬된 미확인 미등록 인물 감지 목록 [{ key, ts, placeId, placeName, zone_name }]
const props = defineProps({
  alerts: { type: Array, required: true },
})
const emit = defineEmits(['ack'])

const latest = computed(() => props.alerts[0])

const now = ref(Date.now())
let timer = null
onMounted(() => { timer = setInterval(() => { now.value = Date.now() }, 30000) })
onBeforeUnmount(() => clearInterval(timer))

const timeOf = (ts) => (ts || '').slice(11, 16)

function ageText(ts) {
  const min = Math.floor((now.value - new Date(ts).getTime()) / 60000)
  if (min < 1) return '방금 전'
  if (min < 60) return `${min}분 전`
  return `${Math.floor(min / 60)}시간 전`
}
</script>
