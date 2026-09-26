// 요청 오류(axios 오류 객체)를 화면에 보여 줄 짧은 한국어 문장으로 바꾸는 순수 함수(브라우저/API 의존 없음, 단위 테스트 대상).
//
// 서버가 준 detail 중 백엔드가 직접 쓴 한국어 메시지는 그대로 쓰고, 없으면 상태 코드로 문장을 만든다.
// "Request failed with status code 500"이나 FastAPI 기본 문구("Not Found", "Method Not Allowed")처럼
// 한글이 없는 영문 detail은 관람객 화면에 보여 주지 않는다.
const HAS_HANGUL = /[가-힣]/

export function describeError(err) {
  const detail = err?.response?.data?.detail
  if (typeof detail === 'string' && HAS_HANGUL.test(detail)) return detail.trim()
  // FastAPI 입력값 검증 오류는 [{ msg, loc, ... }] 배열로 온다
  if (Array.isArray(detail) && detail.length) return '입력값이 올바르지 않습니다'

  if (err?.code === 'ECONNABORTED' || /timeout/i.test(err?.message ?? '')) return '응답 시간이 초과되었습니다'
  if (!err?.response) return '서버에 연결하지 못했습니다'

  const status = err.response.status
  if (status === 401) return '로그인이 필요합니다'
  if (status === 403) return '권한이 없습니다'
  if (status === 404) return '요청한 항목을 찾을 수 없습니다'
  if (status === 400 || status === 422) return '요청이 올바르지 않습니다'
  if (status >= 500) return '서버에서 오류가 발생했습니다'
  return `오류가 발생했습니다 (${status})`
}
