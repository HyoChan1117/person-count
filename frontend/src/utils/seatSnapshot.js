// 스냅샷 슬롯 하나를 화면용 좌석 상태로 바꾸는 순수 함수(브라우저/API 의존 없음, 단위 테스트 대상).
//
// "기록 없음"(그 시각 스냅샷 자체가 없음)과 "판정 불가"(스냅샷은 있는데 그 좌석을 판정하지 못함)는
// 다른 상황이다. 좌석 상태는 둘 다 'unknown'으로 채우되, 화면이 구분해 보여 줄 수 있게
// 기록 유무는 hasSnapshotRecord로 따로 알려 준다.

// seats: { 좌석ID: 'occupied' | 'empty' } | null
export function seatStatesFor(seats, seatIds) {
  const states = {}
  for (const id of seatIds) states[id] = seats ? (seats[id] ?? 'unknown') : 'unknown'
  return states
}

// slot: { seats } | null. 슬롯이 없거나 seats가 null이면 그 시각 기록이 없는 것이다.
export function hasSnapshotRecord(slot) {
  return slot != null && slot.seats != null
}
