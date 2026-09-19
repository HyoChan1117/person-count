import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

// 전시·영상 촬영이 기준이라 저장된 선택이 없으면 OS 설정과 무관하게 다크로 시작한다.
// index.html의 인라인 스크립트도 같은 규칙으로 페인트 전에 클래스를 붙인다.
function getInitial() {
  try {
    const saved = localStorage.getItem('theme')
    if (saved === 'dark' || saved === 'light') return saved
  } catch {
    // 저장소를 못 읽는 환경(시크릿 모드 등)에서는 기본값을 쓴다
  }
  return 'dark'
}

export const useThemeStore = defineStore('theme', () => {
  const mode = ref(getInitial())

  function apply() {
    document.documentElement.classList.toggle('dark', mode.value === 'dark')
  }

  function setMode(next) {
    if (next === 'dark' || next === 'light') mode.value = next
  }

  function toggle() {
    mode.value = mode.value === 'dark' ? 'light' : 'dark'
  }

  watch(mode, (v) => {
    try {
      localStorage.setItem('theme', v)
    } catch {
      // 저장 실패는 무시(화면 동작에는 영향 없음)
    }
    apply()
  }, { immediate: true })

  return { mode, setMode, toggle }
})
