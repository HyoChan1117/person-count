export const ZONE_UNSPECIFIED = '구역 미지정'

// 순찰이 끝나면 실서버는 status.zone을 null로 돌려준다(patrol.py의 finally). 순찰 중이거나 끝난 경우에는
// 구역 이름이 항상 있어야 하므로, zone이 비어 있으면 마지막 진행 번호(zone_index)로 이름을 찾고
// 그래도 없으면 기본 문구를 쓴다. 한 번도 순찰하지 않은 대기 상태는 null(표시 안 함)을 돌려준다.
export function zoneLabel(status, zones) {
  if (!status?.running && !status?.completed) return null
  if (status.zone) return status.zone
  return zones?.[(status.zone_index ?? 0) - 1]?.name ?? ZONE_UNSPECIFIED
}
