import { startTicker, stopTicker } from './state'

export const isDemoMode = import.meta.env.VITE_DEMO_MODE === 'true'

// main.js에서 앱을 만들기 전에 호출한다. 데모 모드가 아니면 아무것도 하지 않는다.
export function setupDemo() {
  if (!isDemoMode) return
  // 전시용이라 로그인 화면을 건너뛴다(authStore는 localStorage 토큰 유무만 본다)
  if (!localStorage.getItem('admin_token')) localStorage.setItem('admin_token', 'demo-token')
  startTicker()
  if (import.meta.hot) import.meta.hot.dispose(stopTicker)
}
