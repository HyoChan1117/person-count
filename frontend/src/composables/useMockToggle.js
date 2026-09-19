import { ref } from 'vue'

// 카메라/PTZ 없이도 화면을 미리 볼 수 있는 "목데이터 모드"의 공통 토글 로직.
// 실제 목데이터 내용은 화면마다 다르므로 onEnable/onDisable 콜백으로 받는다.
export function useMockToggle(onEnable, onDisable) {
  const mockActive = ref(false)

  function toggleMock() {
    mockActive.value = !mockActive.value
    if (mockActive.value) onEnable?.()
    else onDisable?.()
  }

  return { mockActive, toggleMock }
}
