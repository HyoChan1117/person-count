import { ref } from 'vue'

// 화면을 막지 않는 알림. 브라우저 기본 alert()는 확인을 누를 때까지 화면 전체를 멈추고 앱 톤과도 다르다.
// 알림 목록은 앱 전체에서 하나만 두고(모듈 전역), ToastHost.vue가 그려 준다.
const MAX_VISIBLE = 3
const DURATION_MS = { success: 4000, info: 5000, error: 9000 }

const toasts = ref([]) // [{ id, type: 'success' | 'info' | 'error', title, detail, action: { label, onClick } | null }]
const timers = new Map()
let seq = 0

function clearTimer(id) {
  clearTimeout(timers.get(id))
  timers.delete(id)
}

function dismiss(id) {
  clearTimer(id)
  toasts.value = toasts.value.filter((t) => t.id !== id)
}

function schedule(id, duration) {
  clearTimer(id)
  timers.set(id, setTimeout(() => dismiss(id), duration))
}

function push(type, title, { detail = '', action = null, duration = DURATION_MS[type] } = {}) {
  // 같은 내용이 이미 떠 있으면 새로 쌓지 않고 그것의 표시 시간만 늘린다(연속 실패로 화면이 알림으로 뒤덮이지 않게)
  const same = toasts.value.find((t) => t.type === type && t.title === title && t.detail === detail)
  if (same) {
    schedule(same.id, duration)
    return same.id
  }

  const id = ++seq
  const next = [...toasts.value, { id, type, title, detail, action }]
  // 넘치면 가장 오래된 것부터 밀어낸다
  for (const old of next.slice(0, Math.max(0, next.length - MAX_VISIBLE))) clearTimer(old.id)
  toasts.value = next.slice(-MAX_VISIBLE)
  schedule(id, duration)
  return id
}

export function useToast() {
  return {
    toasts,
    dismiss,
    success: (title, opts) => push('success', title, opts),
    info: (title, opts) => push('info', title, opts),
    error: (title, opts) => push('error', title, opts),
  }
}
