// 하루치 좌석 통계를 화면용 값으로 바꾸는 순수 함수(API/브라우저 의존 없음).
// 모니터링 화면과 홈 요약 모달이 같은 기준으로 "최다 점유 좌석 / 최고 점유 시간대"를 말하도록 한곳에 모은다.

export function formatMinutes(min) {
  if (!(min > 0)) return '0분'
  const h = Math.floor(min / 60)
  const m = min % 60
  return h ? `${h}시간 ${m}분` : `${m}분`
}

// seatStats: { 좌석ID: { occupied_minutes } }. 막대는 1위를 100%로 맞춘 상대 비율이다.
// 오래 점유한 순 → 같으면 좌석 번호순.
export function buildSeatRows(seatIds, seatStats) {
  const minutesOf = (id) => seatStats?.[id]?.occupied_minutes ?? 0
  const max = Math.max(1, ...seatIds.map(minutesOf))
  return seatIds
    .map((seatId) => {
      const occupiedMinutes = minutesOf(seatId)
      return {
        seatId,
        occupiedMinutes,
        barPct: Math.round((occupiedMinutes / max) * 100),
        timeText: formatMinutes(occupiedMinutes),
      }
    })
    .sort((a, b) => b.occupiedMinutes - a.occupiedMinutes || Number(a.seatId) - Number(b.seatId))
}

// 수업이 있고 기록이 남은 시간대 중 점유 좌석이 가장 많았던 시각. 없으면 null.
export function peakHour(hours) {
  const scheduled = (hours ?? []).filter((h) => h.scheduled && h.occupied !== null)
  if (!scheduled.length) return null
  return scheduled.reduce((max, h) => (h.occupied > (max?.occupied ?? -1) ? h : max), null)
}

// 오늘 날짜를 API가 쓰는 'YYYY-MM-DD'(로컬 기준)로.
export function todayDateStr(now = new Date()) {
  const pad = (n) => String(n).padStart(2, '0')
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`
}
