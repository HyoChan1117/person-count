// 데모 모드 전용 Vite 미들웨어(dev/preview).
// axios 어댑터가 가로채지 못하는 요청을 처리한다: <img src> 사진/라이브, 로그인, fetch() 쓰기 요청.
// 화면 코드는 건드리지 않는다. 실제 얼굴 사진은 반환하지 않고 실루엣 SVG만 돌려준다.
import { loadEnv } from 'vite'

// style.css의 디자인 토큰과 같은 값(빌드 도구 파일이라 CSS 변수를 못 읽는다)
const C = {
  canvas: '#0B1220', card: '#111A2B', line: '#1F2A3F', fg: '#E6EDF7', muted: '#8FA0BA',
}

function silhouette(label, sub = '') {
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300" width="400" height="300">
  <rect width="400" height="300" fill="${C.canvas}"/>
  <rect x="0" y="0" width="400" height="300" fill="${C.card}" opacity="0.6"/>
  <circle cx="200" cy="112" r="46" fill="${C.muted}" opacity="0.55"/>
  <path d="M96 300c0-64 46-104 104-104s104 40 104 104z" fill="${C.muted}" opacity="0.55"/>
  <text x="20" y="34" font-family="Inter, Pretendard, sans-serif" font-size="18" font-weight="600" fill="${C.fg}">${label}</text>
  <text x="20" y="58" font-family="Inter, Pretendard, sans-serif" font-size="14" fill="${C.muted}">${sub}</text>
</svg>`
}

function placeholder(label, sub = '') {
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" width="1280" height="720">
  <rect width="1280" height="720" fill="${C.canvas}"/>
  <rect x="40" y="70" width="1200" height="610" fill="${C.card}"/>
  <g stroke="${C.line}" stroke-width="1">${Array.from({ length: 16 }, (_, i) => `<line x1="${40 + i * 80}" y1="70" x2="${40 + i * 80}" y2="680"/>`).join('')}${Array.from({ length: 8 }, (_, i) => `<line x1="40" y1="${70 + i * 80}" x2="1240" y2="${70 + i * 80}"/>`).join('')}</g>
  <text x="44" y="44" font-family="Inter, Pretendard, sans-serif" font-size="22" font-weight="600" fill="${C.fg}">${label}</text>
  <text x="44" y="710" font-family="Inter, Pretendard, sans-serif" font-size="16" fill="${C.muted}">${sub}</text>
</svg>`
}

function sendSvg(res, svg) {
  res.statusCode = 200
  res.setHeader('Content-Type', 'image/svg+xml; charset=utf-8')
  res.setHeader('Cache-Control', 'no-store')
  res.end(svg)
}

function sendJson(res, data, status = 200) {
  res.statusCode = status
  res.setHeader('Content-Type', 'application/json; charset=utf-8')
  res.end(JSON.stringify(data))
}

function createHandler() {
  return (req, res, next) => {
    const url = (req.url || '').split('?')[0]
    const method = (req.method || 'GET').toUpperCase()

    if (method === 'POST' && url === '/auth/admin/login') return sendJson(res, { token: 'demo-token' })
    if (!url.startsWith('/api/')) return next()

    if (method === 'GET') {
      const m = url.match(/^\/api\/face\/(detections|people)\/(\d+)\/photo$/)
      if (m) return sendSvg(res, silhouette(m[1] === 'people' ? `등록 인물 #${m[2]}` : `감지 #${m[2]}`, '데모 실루엣'))
      if (/^\/api\/analysis\/\d+\/live\/[^/]+$/.test(url)) return sendSvg(res, placeholder('DEMO LIVE', '데모 모드 정지 화면'))
      if (/^\/api\/face\/places\/\d+\/ptz\/(preview|snapshot)$/.test(url)) return sendSvg(res, placeholder('DEMO PTZ', '데모 모드 정지 화면'))
      return sendJson(res, { detail: `데모 모드에서 지원하지 않는 요청: GET ${url}` }, 404)
    }

    // axios는 어댑터가 처리하므로, 여기까지 오는 쓰기 요청은 fetch()(맵 에디터 자동 저장 등)뿐이다.
    return sendJson(res, { success: true })
  }
}

export default function demoPlugin() {
  let enabled = false
  return {
    name: 'demo-mode-middleware',
    config(_, { mode }) {
      enabled = loadEnv(mode, process.cwd(), 'VITE_').VITE_DEMO_MODE === 'true'
    },
    configureServer(server) {
      if (enabled) server.middlewares.use(createHandler())
    },
    configurePreviewServer(server) {
      if (enabled) server.middlewares.use(createHandler())
    },
  }
}
