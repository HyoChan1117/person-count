<template>
  <div class="ds-root h-full overflow-y-auto p-section">
    <div class="mx-auto max-w-[1680px]">
      <header class="mb-section flex items-end justify-between gap-section">
        <div class="min-w-0">
          <h1 class="text-3xl font-bold tracking-tight text-fg">얼굴 인식</h1>
          <p class="mt-1 text-lg text-fg-muted">감시 장소를 등록하고 PTZ 카메라와 순찰 구역을 관리합니다</p>
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
          <button type="button" :class="BTN_MAIN" @click="showForm = true">+ 새 교실 추가</button>
        </div>
      </header>

      <div
        v-if="actionMeta"
        role="status"
        class="mb-section flex items-center justify-between gap-gutter rounded-card border border-l-2 border-line border-l-fg bg-card px-card py-gutter"
      >
        <p class="text-lg text-fg"><strong class="font-semibold">{{ actionMeta.label }}</strong>을 진행할 장소를 선택하세요.</p>
        <router-link to="/face" class="shrink-0 text-base text-fg-muted underline underline-offset-4 transition-colors hover:text-fg">선택 취소</router-link>
      </div>

      <p v-if="loading" class="py-20 text-center text-base text-fg-muted">불러오는 중...</p>

      <ErrorNotice
        v-else-if="loadError"
        title="감시 장소를 불러오지 못했습니다"
        :message="loadError"
        @retry="retryPlaces"
      />

      <div v-else-if="!places.length" class="flex flex-col items-center justify-center gap-3 py-24 text-center">
        <span class="flex h-14 w-14 items-center justify-center rounded-card border border-line bg-card text-fg-muted">
          <NavIcon name="face" :size="28" />
        </span>
        <p class="text-lg font-semibold text-fg">등록된 감시 장소가 없습니다</p>
        <p class="text-sm text-fg-muted">장소를 추가한 뒤 카메라와 순찰 구역을 설정하세요.</p>
      </div>

      <p v-else-if="filteredPlaces.length === 0" class="py-16 text-center text-base text-fg-muted">"{{ search }}"에 해당하는 교실이 없습니다.</p>

      <div v-else class="grid grid-cols-1 gap-gutter sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4">
        <UiCard
          v-for="p in filteredPlaces"
          :key="p.id"
          interactive
          class="group flex min-h-[13rem] flex-col"
          :class="actionMeta ? 'cursor-pointer hover:!border-fg' : ''"
          :role="actionMeta ? 'button' : undefined"
          :tabindex="actionMeta ? 0 : undefined"
          @click="actionMeta && selectPlace(p)"
          @keydown.enter.self.prevent="actionMeta && selectPlace(p)"
        >
          <div class="flex items-start justify-between gap-2">
            <h2 class="min-w-0 truncate text-xl font-semibold text-fg" :title="p.name">{{ p.name }}</h2>
            <span class="rounded-full border border-line px-2.5 py-0.5 text-xs text-fg-muted">PTZ</span>
          </div>

          <dl class="mt-card grid grid-cols-2 gap-gutter">
            <div>
              <dt class="text-sm text-fg-muted">등록 인물</dt>
              <dd class="mt-1 text-3xl font-bold tabular-nums text-fg">{{ peopleCount }}<span class="ml-1 text-base font-normal text-fg-muted">명</span></dd>
            </div>
            <div>
              <dt class="text-sm text-fg-muted">순찰 구역</dt>
              <dd class="mt-1 text-3xl font-bold tabular-nums text-fg">{{ p.zones?.length ?? 0 }}<span class="ml-1 text-base font-normal text-fg-muted">개</span></dd>
            </div>
          </dl>

          <div class="flex-1" />

          <div v-if="!actionMeta" class="mt-card space-y-2 border-t border-line pt-card">
            <div class="flex gap-2">
              <router-link :to="`/face/${p.id}/monitoring`" :class="BTN_MAIN_LINK" @click.stop>모니터링</router-link>
              <router-link :to="`/face/${p.id}/zones`" :class="BTN_SUB_LINK" @click.stop>구역 등록</router-link>
            </div>
            <div class="flex gap-2">
              <router-link :to="`/face/${p.id}/camera`" :class="BTN_SUB_LINK" @click.stop>카메라 설정</router-link>
              <router-link to="/face/people" :class="BTN_SUB_LINK" @click.stop>인물 등록</router-link>
            </div>
          </div>
          <p v-else class="mt-card border-t border-line pt-card text-sm text-fg-muted">클릭하면 {{ actionMeta.label }} 화면으로 이동합니다.</p>
        </UiCard>
      </div>
    </div>

    <div
      v-if="showForm"
      class="fixed inset-0 z-50 flex items-center justify-center bg-canvas/80"
      @click.self="showForm = false"
      @keydown.esc="showForm = false"
    >
      <div role="dialog" aria-modal="true" aria-labelledby="new-place-title" class="ds-text w-96 rounded-card border border-line bg-card p-card">
        <h2 id="new-place-title" class="mb-4 text-xl font-semibold text-fg">새 교실 추가</h2>
        <form @submit.prevent="createPlace">
          <label class="mb-1 block text-sm text-fg-muted">교실 선택</label>
          <select v-model="form.classroomId" :class="[INPUT, 'mb-3 w-full']">
            <option v-for="c in classrooms" :key="c.id" :value="c.id">{{ c.name }}</option>
            <option :value="null">직접 입력</option>
          </select>

          <template v-if="form.classroomId === null">
            <label class="mb-1 block text-sm text-fg-muted">장소 이름</label>
            <input v-model="form.name" required :class="[INPUT, 'mb-3 w-full']" placeholder="예: 창조관 301호" />
          </template>

          <p class="mb-4 text-xs text-fg-muted">추가한 뒤 카메라 설정에서 IP와 계정을 입력해주세요.</p>
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
import api from '@/api'
import { FACE_ACTIONS } from '@/constants/navActions'
import UiCard from '@/components/ui/UiCard.vue'
import ErrorNotice from '@/components/ui/ErrorNotice.vue'
import NavIcon from '@/components/ui/NavIcon.vue'

const FOCUS = 'focus-visible:outline focus-visible:outline-2 focus-visible:outline-fg-muted'
const INPUT = `rounded-lg border border-line bg-canvas px-3 py-2.5 text-sm text-fg placeholder:text-fg-muted focus:outline-none focus-visible:border-fg-muted ${FOCUS}`
const BTN_MAIN = `shrink-0 rounded-lg bg-fg px-4 py-2.5 text-sm font-semibold text-canvas transition-opacity hover:opacity-90 ${FOCUS}`
const BTN_MAIN_FULL = `flex-1 rounded-lg bg-fg px-4 py-2.5 text-sm font-semibold text-canvas transition-opacity hover:opacity-90 ${FOCUS}`
const BTN_MAIN_LINK = `flex-1 rounded-lg bg-fg py-2.5 text-center text-sm font-semibold text-canvas transition-opacity hover:opacity-90 ${FOCUS}`
const BTN_SUB = `flex-1 rounded-lg border border-line px-4 py-2.5 text-sm font-medium text-fg-muted transition-colors hover:border-fg-muted/60 hover:text-fg ${FOCUS}`
const BTN_SUB_LINK = `flex-1 rounded-lg border border-line py-2.5 text-center text-sm font-medium text-fg-muted transition-colors hover:border-fg-muted/60 hover:text-fg ${FOCUS}`

const route = useRoute()
const router = useRouter()
const places = ref([])
const classrooms = ref([])
const peopleCount = ref(0)
const loading = ref(true)
const showForm = ref(false)
const form = ref({ name: '', classroomId: null })
const loadError = ref('')
const search = ref('')

const ACTIONS = Object.fromEntries(FACE_ACTIONS.map(a => [a.action, a]))
const actionMeta = computed(() => ACTIONS[route.query.action] ?? null)
const filteredPlaces = computed(() => {
  const q = search.value.trim().toLowerCase()
  if (!q) return places.value
  return places.value.filter((p) => p.name.toLowerCase().includes(q))
})

function selectPlace(p) {
  if (!actionMeta.value) return
  router.push(actionMeta.value.path(p.id))
}

async function fetchPlaces() {
  loadError.value = ''
  try {
    const [placeRes, classroomRes, peopleRes] = await Promise.all([
      api.get('/face/places'),
      api.get('/classrooms/'),
      api.get('/face/people'),
    ])
    places.value = placeRes.data.places
    classrooms.value = classroomRes.data
    peopleCount.value = peopleRes.data.people?.length ?? 0
    if (form.value.classroomId === null && classrooms.value.length) {
      form.value.classroomId = classrooms.value[0].id
    }
  } catch (e) {
    loadError.value = e.response?.data?.detail ?? e.message
  } finally {
    loading.value = false
  }
}

function retryPlaces() {
  loading.value = true
  fetchPlaces()
}

async function createPlace() {
  await api.post('/face/places', {
    name: form.value.classroomId === null ? form.value.name : null,
    classroom_id: form.value.classroomId,
  })
  showForm.value = false
  form.value = { name: '', classroomId: classrooms.value[0]?.id ?? null }
  await fetchPlaces()
}

onMounted(fetchPlaces)
</script>
