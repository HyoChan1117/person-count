import { ref } from 'vue'

// 하루치 좌석 통계(누적 + 정각별)를 불러온다. 화면이 날짜를 바꿔 가며 부르므로 두 가지를 보장한다.
//  - 요청 순서 가드: 더 최근에 시작한 요청이 있으면 이전 요청의 결과(성공/실패 모두)는 버린다.
//  - 실패하면 이전 날짜 데이터를 비우고 오류를 남긴다(새 날짜 라벨에 옛 통계가 남지 않게).
// 실제 API 호출은 fetchDaily(date)/fetchHourly(date)로 주입받는다(응답 body를 그대로 돌려주는 함수).
export function useDailyStats({ fetchDaily, fetchHourly, dateStr }) {
  const seatStats = ref({})
  const periodMinutes = ref(0)
  const hourlyStats = ref([])
  const loading = ref(false)
  const error = ref('')
  let latest = 0

  function clear() {
    seatStats.value = {}
    periodMinutes.value = 0
    hourlyStats.value = []
  }

  async function load() {
    const mine = ++latest
    const date = dateStr.value
    loading.value = true
    error.value = ''
    try {
      const [daily, hourly] = await Promise.all([fetchDaily(date), fetchHourly(date)])
      if (mine !== latest) return
      seatStats.value = daily?.seats ?? {}
      periodMinutes.value = daily?.period_minutes ?? 0
      hourlyStats.value = hourly?.hours ?? []
    } catch (e) {
      if (mine !== latest) return
      clear()
      error.value = e?.response?.data?.detail ?? e?.message ?? '알 수 없는 오류'
    } finally {
      if (mine === latest) loading.value = false
    }
  }

  return { seatStats, periodMinutes, hourlyStats, loading, error, load }
}
