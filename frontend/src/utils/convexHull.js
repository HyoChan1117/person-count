// 점 집합의 볼록 껍질을 돌아가는 순서로 돌려준다(Andrew monotone chain).
// 백엔드는 좌석선 4점을 순서와 상관없이 볼록 껍질로 판정에 쓴다(_is_in_seat_band).
// 그릴 때도 같은 기준으로 정렬해야 점 순서가 제각각인 저장 데이터가 꼬인(나비넥타이) 도형으로 보이지 않는다.
export function convexHull(points) {
  const pts = points
    .map(([x, y]) => [Number(x), Number(y)])
    .filter(([x, y]) => Number.isFinite(x) && Number.isFinite(y))
    .sort((a, b) => a[0] - b[0] || a[1] - b[1])
  if (pts.length < 3) return pts

  const cross = (o, a, b) => (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
  const build = (list) => {
    const out = []
    for (const p of list) {
      while (out.length >= 2 && cross(out[out.length - 2], out[out.length - 1], p) <= 0) out.pop()
      out.push(p)
    }
    out.pop()
    return out
  }
  return [...build(pts), ...build([...pts].reverse())]
}
