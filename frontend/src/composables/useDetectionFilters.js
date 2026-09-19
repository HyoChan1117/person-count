import { ref, computed } from 'vue'

export const PERIODS = [
  { key: 'hour', label: '최근 1시간' },
  { key: 'today', label: '오늘' },
  { key: 'all', label: '전체' },
]

export const REGISTRATIONS = [
  { key: 'all', label: '전체' },
  { key: 'registered', label: '등록' },
  { key: 'unregistered', label: '미등록' },
]

// 감지 기록의 zone_name은 자리가 있으면 "구역명 · 자리번호" 형태다. 구역 필터는 앞부분으로 묶는다.
export function zoneOf(zoneName) {
  return (zoneName ?? '').split(' · ')[0]
}

const localDate = (d) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`

export function filterDetections(items, { period = 'all', zone = '', registration = 'all' } = {}, nowMs = Date.now()) {
  const today = localDate(new Date(nowMs))
  return items.filter((d) => {
    if (period === 'hour' && nowMs - new Date(d.ts).getTime() > 3600 * 1000) return false
    if (period === 'today' && !(d.ts ?? '').startsWith(today)) return false
    if (zone && zoneOf(d.zone_name) !== zone) return false
    if (registration === 'registered' && d.name == null) return false
    if (registration === 'unregistered' && d.name != null) return false
    return true
  })
}

export function useDetectionFilters(items) {
  const period = ref('all')
  const zone = ref('')
  const registration = ref('all')

  const zones = computed(() => [...new Set(items.value.map((d) => zoneOf(d.zone_name)).filter(Boolean))])
  const filtered = computed(() => filterDetections(items.value, { period: period.value, zone: zone.value, registration: registration.value }))
  const isFiltered = computed(() => period.value !== 'all' || zone.value !== '' || registration.value !== 'all')

  function reset() {
    period.value = 'all'
    zone.value = ''
    registration.value = 'all'
  }

  return { period, zone, registration, zones, filtered, isFiltered, reset }
}
