<template>
  <div class="ds-root h-full overflow-y-auto p-section">
    <div class="mx-auto max-w-[1680px]">

      <!-- 헤더 -->
      <header class="mb-section flex items-end justify-between gap-section">
        <div class="min-w-0">
          <h1 class="text-3xl font-bold tracking-tight text-fg">좌석 확인</h1>
          <p class="mt-1 text-lg text-fg-muted">교실별 대시보드와 모니터링을 열고, 카메라와 좌석 배치를 관리합니다</p>
        </div>

        <div class="flex shrink-0 items-center gap-gutter">
          <label class="relative block">
            <span class="sr-only">교실 이름 검색</span>
            <NavIcon name="search" :size="18" class="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-fg-muted" />
            <input
              v-model="search"
              type="text"
              placeholder="교실 이름으로 검색"
              :class="[INPUT, 'w-64 pl-10']"
            />
          </label>
          <button v-if="auth.isAdmin" type="button" :class="BTN_MAIN" @click="showForm = true">+ 새 교실 추가</button>
        </div>
      </header>

      <!-- 교실 선택 모드 배너 (사이드바 하위 메뉴에서 넘어온 경우) -->
      <div
        v-if="actionMeta"
        role="status"
        class="mb-section flex items-center justify-between gap-gutter rounded-card border border-l-2 border-line border-l-fg bg-card px-card py-gutter"
      >
        <p class="text-lg text-fg"><strong class="font-semibold">{{ actionMeta.label }}</strong>을(를) 진행할 교실을 선택하세요.</p>
        <router-link to="/classrooms" class="shrink-0 text-base text-fg-muted underline underline-offset-4 transition-colors hover:text-fg">선택 취소</router-link>
      </div>

      <p v-if="store.loading" class="py-20 text-center text-base text-fg-muted">불러오는 중...</p>

      <!-- 조회 실패를 "등록된 교실 없음"으로 보이지 않게 따로 안내한다 -->
      <ErrorNotice
        v-else-if="store.error && store.classrooms.length === 0"
        title="교실 목록을 불러오지 못했습니다"
        :message="store.error"
        @retry="reload"
      />

      <div v-else-if="store.classrooms.length === 0" class="flex flex-col items-center justify-center gap-3 py-24 text-center">
        <span class="flex h-14 w-14 items-center justify-center rounded-card border border-line bg-card text-fg-muted">
          <NavIcon name="seats" :size="28" />
        </span>
        <p class="text-lg font-semibold text-fg">등록된 교실이 없습니다</p>
        <p class="text-sm text-fg-muted">새 교실을 추가해 보세요.</p>
      </div>

      <p v-else-if="filteredClassrooms.length === 0" class="py-16 text-center text-base text-fg-muted">"{{ search }}"에 해당하는 교실이 없습니다.</p>

      <div v-else class="grid grid-cols-1 gap-gutter sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4">
        <UiCard
          v-for="c in filteredClassrooms"
          :key="c.id"
          interactive
          class="group flex min-h-[13rem] flex-col"
          :class="actionMeta ? 'cursor-pointer hover:!border-fg' : ''"
          :role="actionMeta ? 'button' : undefined"
          :tabindex="actionMeta ? 0 : undefined"
          @click="actionMeta && selectClassroom(c)"
          @keydown.enter.self.prevent="actionMeta && selectClassroom(c)"
        >
          <div class="flex items-start justify-between gap-2">
            <h2 class="min-w-0 truncate text-xl font-semibold text-fg" :title="c.name">{{ c.name }}</h2>
            <button
              v-if="auth.isAdmin"
              type="button"
              :class="[LINK_QUIET, 'opacity-0 group-hover:opacity-100 focus-visible:opacity-100']"
              @click.stop="deleteClassroom(c.id)"
            >삭제</button>
          </div>

          <dl class="mt-6 grid grid-cols-2 gap-gutter">
            <div>
              <dt class="text-sm text-fg-muted">CCTV</dt>
              <dd class="mt-1 text-3xl font-bold tabular-nums text-fg">{{ c.cameras.length }}<span class="ml-1 text-base font-normal text-fg-muted">대</span></dd>
            </div>
            <div>
              <dt class="text-sm text-fg-muted">좌석 설정</dt>
              <dd class="mt-1 text-3xl font-bold tabular-nums text-fg">{{ seatLineCount(c) }}<span class="ml-1 text-base font-normal text-fg-muted">대</span></dd>
            </div>
          </dl>

          <!-- 액션: 보기(모니터링·대시보드)를 먼저, 관리자 설정은 아래 -->
          <div v-if="!actionMeta" class="mt-card space-y-2 border-t border-line pt-card">
            <div class="flex gap-2">
              <router-link :to="`/monitoring/${c.id}`" :class="BTN_MAIN_LINK" @click.stop>모니터링</router-link>
              <router-link :to="`/dashboard/${c.id}`" :class="BTN_SUB_LINK" @click.stop>대시보드</router-link>
            </div>
            <div v-if="auth.isAdmin" class="flex gap-2">
              <router-link :to="`/classrooms/${c.id}/setup`" :class="BTN_SUB_LINK" @click.stop>카메라 설정</router-link>
              <router-link :to="`/classrooms/${c.id}/map`" :class="BTN_SUB_LINK" @click.stop>맵 에디터</router-link>
            </div>
          </div>
          <p v-else class="mt-card border-t border-line pt-card text-sm text-fg-muted">클릭하면 {{ actionMeta.label }}(으)로 이동합니다</p>
        </UiCard>
      </div>
    </div>

    <!-- 새 교실 추가 모달 -->
    <div
      v-if="showForm"
      class="fixed inset-0 z-50 flex items-center justify-center bg-canvas/80"
      @click.self="showForm = false"
      @keydown.esc="showForm = false"
    >
      <div role="dialog" aria-modal="true" aria-labelledby="new-classroom-title" class="ds-text w-96 rounded-card border border-line bg-card p-card">
        <h2 id="new-classroom-title" class="mb-4 text-xl font-semibold text-fg">새 교실 추가</h2>
        <form @submit.prevent="createClassroom">
          <label for="new-classroom-name" class="mb-1 block text-sm text-fg-muted">교실 이름</label>
          <input id="new-classroom-name" v-model="form.name" required autofocus :class="[INPUT, 'mb-4 w-full']" placeholder="예: 101호" />
          <div class="flex gap-2">
            <button type="button" :class="BTN_SUB" @click="showForm = false">취소</button>
            <button type="submit" :class="BTN_MAIN_FULL">추가</button>
          </div>
        </form>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useClassroomStore } from '@/stores/classroomStore.js'
import { useAuthStore } from '@/stores/authStore'
import { SEAT_ACTIONS } from '@/constants/navActions'
import UiCard from '@/components/ui/UiCard.vue'
import ErrorNotice from '@/components/ui/ErrorNotice.vue'
import NavIcon from '@/components/ui/NavIcon.vue'

// 클래스는 Tailwind가 스캔할 수 있도록 전부 리터럴로 적는다.
const FOCUS = 'focus-visible:outline focus-visible:outline-2 focus-visible:outline-fg-muted'
const INPUT = `rounded-lg border border-line bg-canvas px-3 py-2.5 text-sm text-fg placeholder:text-fg-muted focus:outline-none focus-visible:border-fg-muted ${FOCUS}`
const BTN_MAIN = `shrink-0 rounded-lg bg-fg px-4 py-2.5 text-sm font-semibold text-canvas transition-opacity hover:opacity-90 ${FOCUS}`
const BTN_MAIN_FULL = `flex-1 rounded-lg bg-fg px-4 py-2.5 text-sm font-semibold text-canvas transition-opacity hover:opacity-90 ${FOCUS}`
const BTN_MAIN_LINK = `flex-1 rounded-lg bg-fg py-2.5 text-center text-sm font-semibold text-canvas transition-opacity hover:opacity-90 ${FOCUS}`
const BTN_SUB = `flex-1 rounded-lg border border-line px-4 py-2.5 text-sm font-medium text-fg-muted transition-colors hover:border-fg-muted/60 hover:text-fg ${FOCUS}`
const BTN_SUB_LINK = `flex-1 rounded-lg border border-line py-2.5 text-center text-sm font-medium text-fg-muted transition-colors hover:border-fg-muted/60 hover:text-fg ${FOCUS}`
const LINK_QUIET = `shrink-0 rounded-md px-2 py-0.5 text-sm text-fg-muted transition-colors hover:text-fg ${FOCUS}`

const auth = useAuthStore()
const store = useClassroomStore()
const route = useRoute()
const router = useRouter()
const showForm = ref(false)
const form = ref({ name: '' })
const search = ref('')

const ACTIONS = Object.fromEntries(SEAT_ACTIONS.map(a => [a.action, a]))
const actionMeta = computed(() => ACTIONS[route.query.action] ?? null)

function selectClassroom(c) {
  if (!actionMeta.value) return
  if (actionMeta.value.adminOnly && !auth.isAdmin) {
    alert('관리자만 이용할 수 있습니다.')
    return
  }
  router.push(actionMeta.value.path(c.id))
}

// 다른 화면에서 남은 오류가 이 화면에 비치지 않도록 비운 뒤 조회한다
function reload() {
  store.error = null
  store.fetchAll()
}

onMounted(reload)

const filteredClassrooms = computed(() => {
  const q = search.value.trim().toLowerCase()
  if (!q) return store.classrooms
  return store.classrooms.filter(c => c.name.toLowerCase().includes(q))
})

function seatLineCount(classroom) {
  return classroom.cameras.filter(c => Object.keys(c.seat_lines ?? {}).length > 0).length
}

async function createClassroom() {
  await store.createClassroom({ name: form.value.name })
  showForm.value = false
  form.value = { name: '' }
}

async function deleteClassroom(id) {
  if (!confirm('이 교실을 삭제하시겠습니까?')) return
  await store.deleteClassroom(id)
}
</script>
