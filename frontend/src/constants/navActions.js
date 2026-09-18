// 좌석 확인 / 얼굴 인식 사이드바 메뉴와 목록 화면의 "선택 모드"가 공유하는
// 단일 소스. 여기서만 액션을 추가/수정하면 Sidebar.vue의 서브메뉴와
// ClassroomListView.vue / FacePlaceListView.vue의 선택 모드가 함께 바뀐다.

export const SEAT_ACTIONS = [
  { action: 'setup', icon: '📷', label: '카메라 설정', adminOnly: true, path: (id) => `/classrooms/${id}/setup` },
  { action: 'dashboard', icon: '📊', label: '대시보드', adminOnly: false, path: (id) => `/dashboard/${id}` },
  { action: 'monitoring', icon: '🖥️', label: '모니터링', adminOnly: false, path: (id) => `/monitoring/${id}` },
  { action: 'map', icon: '🗺️', label: '맵 에디터', adminOnly: true, path: (id) => `/classrooms/${id}/map` },
]

export const FACE_ACTIONS = [
  { action: 'camera', icon: '📷', label: '카메라 설정', path: (id) => `/face/${id}/camera` },
  { action: 'zones', icon: '🗺️', label: '구역 등록', path: (id) => `/face/${id}/zones` },
  { action: 'monitoring', icon: '🖥️', label: '모니터링', path: (id) => `/face/${id}/monitoring` },
]
