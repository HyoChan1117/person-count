// 홈 대시보드의 교실 상태 판정. 카드 배지와 상단 힌트가 같은 기준을 쓰도록 한곳에 모은다.
//   unknown  : 조회 오류, 좌석 0개, 판정 가능한 좌석이 없음 (비어 있다고 말할 수 없다)
//   occupied : 판정된 좌석 중 점유가 있음
//   empty    : 판정된 좌석이 전부 비어 있음
// 입력은 homeDashboardStore의 교실 객체 { total, occupied, judgeable, unknown, error }.
export function roomStatus(room) {
  if (!room || room.error) return 'unknown'
  if (!(room.total > 0) || !(room.judgeable > 0)) return 'unknown'
  return room.occupied > 0 ? 'occupied' : 'empty'
}

export function countRoomStatuses(rooms) {
  const counts = { occupied: 0, empty: 0, unknown: 0 }
  for (const room of rooms) counts[roomStatus(room)] += 1
  return counts
}

// "사용 중 교실" 카드 아래 힌트. 판정 불가 교실은 비어 있음에 섞지 않고 따로 적는다.
export function describeRoomCounts({ occupied, empty, unknown }) {
  if (occupied + empty + unknown === 0) return ''
  const parts = []
  if (empty > 0) parts.push(`${empty}개 교실 비어 있음`)
  if (unknown > 0) parts.push(`판정 불가 ${unknown}개`)
  return parts.length ? parts.join(' · ') : '모든 교실 사용 중'
}
