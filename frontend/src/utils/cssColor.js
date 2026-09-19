// canvas처럼 Tailwind 클래스를 쓸 수 없는 곳에서 디자인 토큰 색을 읽는다.
// style.css의 `--color-*` RGB 채널을 그대로 가져오므로 hex를 코드에 두지 않는다.
// 사용: cssColor('state-occupied') / cssColor('card', 0.6)
export function cssColor(name, alpha = 1) {
  const raw = getComputedStyle(document.documentElement).getPropertyValue(`--color-${name}`).trim()
  return alpha >= 1 ? `rgb(${raw})` : `rgb(${raw} / ${alpha})`
}
