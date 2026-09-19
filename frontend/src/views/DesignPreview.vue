<template>
  <div class="ds-root h-full overflow-y-auto p-section">
    <div class="mx-auto flex max-w-[1500px] flex-col gap-section">
      <SectionHeader title="디자인 토대 미리보기" description="개발 모드 전용 (/__ds). 토큰, 타이포, 공용 컴포넌트를 한 화면에서 확인합니다." />

      <UiCard>
        <SectionHeader title="색 토큰" description="컴포넌트에서는 hex 대신 이 이름만 사용합니다." class="mb-card" />
        <div class="grid grid-cols-5 gap-gutter">
          <div v-for="s in surfaces" :key="s.name" class="flex flex-col gap-2">
            <div class="h-16 rounded-lg border border-line" :class="s.cls" />
            <span class="text-label text-fg">{{ s.name }}</span>
            <span class="text-sm text-fg-muted">{{ s.hint }}</span>
          </div>
        </div>
        <div class="mt-card grid grid-cols-4 gap-gutter">
          <div v-for="s in states" :key="s.name" class="flex flex-col gap-2">
            <div class="h-16 rounded-lg" :class="s.cls" />
            <span class="text-label text-fg">{{ s.name }}</span>
            <span class="text-sm text-fg-muted">{{ s.hint }}</span>
          </div>
        </div>
      </UiCard>

      <div class="grid grid-cols-2 gap-section">
        <UiCard>
          <SectionHeader title="타이포그래피" description="한글 Pretendard · 영문/숫자 Inter · 숫자 tabular-nums" class="mb-card" />
          <div class="flex flex-col gap-4">
            <div class="text-metric-lg text-fg">72%</div>
            <div class="text-metric text-fg">1,234</div>
            <div class="text-metric-sm text-fg">08:45:12</div>
            <div class="text-label text-fg-muted">라벨 Label · 좌석 점유율 Occupancy 0123456789</div>
            <p class="text-fg">가나다라마바사 · The quick brown fox jumps over the lazy dog</p>
          </div>
        </UiCard>

        <UiCard>
          <SectionHeader title="상태 뱃지" description="상태색은 4가지 고정, 다른 용도 금지" class="mb-card" />
          <div class="flex flex-wrap items-center gap-3">
            <StatusBadge status="occupied" />
            <StatusBadge status="empty" />
            <StatusBadge status="unknown" />
            <StatusBadge status="alert" />
          </div>
          <div class="mt-4 flex flex-wrap items-center gap-3">
            <StatusBadge status="occupied" size="lg" />
            <StatusBadge status="empty" size="lg" />
            <StatusBadge status="unknown" size="lg" />
            <StatusBadge status="alert" size="lg" label="경고 3건" />
          </div>
          <div class="mt-card flex items-center gap-4">
            <FaceAvatar name="김OO" :size="48" />
            <FaceAvatar name="이OO" :size="48" />
            <FaceAvatar :size="48" />
            <FaceAvatar name="감지" src="/api/face/detections/1/photo" :size="64" />
            <span class="text-sm text-fg-muted">← 마지막은 기본 블러(클릭 시 공개, 15초 뒤 재블러)</span>
          </div>
        </UiCard>
      </div>

      <UiCard>
        <SectionHeader title="핵심 지표" description="1920×1080에서 멀리서도 읽히는 큰 숫자" class="mb-card">
          <template #actions>
            <span class="rounded-lg border border-line px-3 py-1.5 text-sm text-fg-muted">액션 슬롯</span>
          </template>
        </SectionHeader>
        <div class="grid grid-cols-3 gap-section">
          <MetricStat label="전체 점유율" value="63" unit="%" hint="152 / 240석" size="lg" tone="occupied" />
          <MetricStat label="사용 중 교실" value="7" unit="/ 8" hint="1개 교실 비어 있음" size="lg" />
          <MetricStat label="미확인 경고" value="3" unit="건" hint="미등록 인물 감지" size="lg" tone="alert" />
        </div>
      </UiCard>
    </div>
  </div>
</template>

<script setup>
import UiCard from '@/components/ui/UiCard.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import MetricStat from '@/components/ui/MetricStat.vue'
import SectionHeader from '@/components/ui/SectionHeader.vue'
import FaceAvatar from '@/components/ui/FaceAvatar.vue'

// 클래스는 Tailwind가 스캔할 수 있게 전부 리터럴로 적는다
const surfaces = [
  { name: 'canvas', hint: '배경', cls: 'bg-canvas' },
  { name: 'card', hint: '카드', cls: 'bg-card' },
  { name: 'line', hint: '경계선', cls: 'bg-line' },
  { name: 'fg', hint: '텍스트', cls: 'bg-fg' },
  { name: 'fg-muted', hint: '보조 텍스트', cls: 'bg-fg-muted' },
]
const states = [
  { name: 'state-occupied', hint: '점유', cls: 'bg-state-occupied' },
  { name: 'state-empty', hint: '빈 좌석', cls: 'bg-state-empty' },
  { name: 'state-unknown', hint: '판정 불가', cls: 'bg-state-unknown' },
  { name: 'state-alert', hint: '경고 (미등록 인물)', cls: 'bg-state-alert' },
]
</script>
