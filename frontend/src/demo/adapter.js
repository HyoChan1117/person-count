// VITE_DEMO_MODE=true일 때 api.js의 axios 인스턴스가 실제 네트워크 대신 이 어댑터를 쓴다.
// 화면 쪽 API 호출 코드는 그대로이고, 응답 형태만 백엔드와 같게 맞춘다.
import { AxiosError } from 'axios'
import * as S from './state'
import { renderFrame } from './frame'

const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

function respond(config, data, status = 200) {
  return { data, status, statusText: 'OK', headers: {}, config, request: {} }
}

function fail(config, status, detail) {
  const response = { data: { detail }, status, statusText: detail, headers: {}, config, request: {} }
  return new AxiosError(`Request failed with status code ${status}`, status >= 500 ? 'ERR_BAD_RESPONSE' : 'ERR_BAD_REQUEST', config, {}, response)
}

const ok = { ok: true }
const success = { success: true }

function parseBody(config) {
  const d = config.data
  if (d == null) return {}
  if (typeof FormData !== 'undefined' && d instanceof FormData) return d
  if (typeof d === 'string') { try { return JSON.parse(d) } catch { return {} } }
  return d
}

const notFound = (what) => { const e = new Error(what); e.status = 404; return e }
const need = (v, what = 'Not found') => { if (v == null) throw notFound(what); return v }
const today = () => S.localDateStr()

// [method, 경로 정규식, (match, ctx) => 응답 데이터]
const ROUTES = [
  // 교실 / 배치도
  ['get', /^\/classrooms\/?$/, () => S.listClassrooms()],
  ['post', /^\/classrooms\/?$/, (m, c) => S.createClassroom(c.body)],
  ['get', /^\/classrooms\/(\d+)$/, (m) => need(S.getClassroom(m[1]), 'Classroom not found')],
  ['put', /^\/classrooms\/(\d+)$/, (m, c) => need(S.updateClassroom(m[1], c.body), 'Classroom not found')],
  ['delete', /^\/classrooms\/(\d+)$/, (m) => { S.removeClassroom(m[1]); return success }],
  ['get', /^\/classrooms\/(\d+)\/map-data$/, (m) => need(S.getMap(m[1]), 'Map not found')],
  ['put', /^\/classrooms\/(\d+)\/map-data$/, (m, c) => { S.setMap(m[1], c.body); return success }],

  // 분석
  ['get', /^\/analysis\/(\d+)\/seat-occupancy$/, (m) => need(S.seatOccupancy(m[1]), 'Classroom not found')],
  ['get', /^\/analysis\/(\d+)\/yolo-llm-count$/, (m) => need(S.yoloLlmCount(m[1]), 'Classroom not found')],
  ['get', /^\/analysis\/(\d+)\/occupancy-hourly$/, (m, c) => need(S.hourlyFor(m[1], c.params.date || today()), 'Classroom not found')],
  ['get', /^\/analysis\/(\d+)\/occupancy-stats-daily$/, (m, c) => need(S.statsDailyFor(m[1], c.params.date || today()), 'Classroom not found')],
  // 실서버에는 없는 10분 단위 스냅샷 엔드포인트(프런트가 404면 60분 단위로 폴백한다)
  ['get', /^\/analysis\/(\d+)\/occupancy-snapshots$/, (m, c) => need(S.snapshotsFor(m[1], c.params.date || today()), 'Classroom not found')],
  ['get', /^\/analysis\/(\d+)\/frame\/([^/]+)$/, (m, c) => {
    const image = need(renderFrame(m[1], m[2], c.params.t), 'Camera not found')
    return { image, ...S.FRAME_SIZE }
  }],
  ['get', /^\/analysis\/(\d+)\/prewarm$/, () => ({ ok: true, cameras: 2, model: 'demo' })],
  ['get', /^\/analysis\/(\d+)\/bg-status\/[^/]+$/, () => ({ has_reference: false })],
  ['get', /^\/analysis\/(\d+)\/bg-detect\/[^/]+$/, () => ({ occupied: false, change_ratio: 0.004 })],
  ['post', /^\/analysis\/(\d+)\/seat-lines\/([^/]+)$/, (m, c) => {
    const room = need(S.getClassroom(m[1]), 'Classroom not found')
    const cameras = room.cameras.map((cam) => (cam.camera_id === m[2] ? { ...cam, seat_lines: c.body.seat_lines || {} } : cam))
    S.updateClassroom(m[1], { cameras })
    return success
  }],
  ['post', /^\/analysis\/(\d+)\/(map-image|seat-counts|bg-reference|bg-reference-upload)(\/[^/]+)?$/, () => ({ ...success, image: null })],

  // 프롬프트
  ['get', /^\/prompts\/?$/, () => S.getPrompts()],
  ['put', /^\/prompts\/?$/, (m, c) => S.setPrompts(c.body)],

  // 얼굴 인식: 장소 / PTZ / 구역
  ['get', /^\/face\/places\/?$/, () => ({ places: S.listPlaces() })],
  ['post', /^\/face\/places\/?$/, (m, c) => S.createPlace(c.body)],
  ['get', /^\/face\/places\/(\d+)$/, (m) => need(S.getPlace(m[1]), 'Place not found')],
  ['put', /^\/face\/places\/(\d+)$/, (m, c) => need(S.updatePlace(m[1], c.body), 'Place not found')],
  ['delete', /^\/face\/places\/(\d+)$/, (m) => { S.removePlace(m[1]); return ok }],
  ['get', /^\/face\/places\/(\d+)\/camera\/test$/, (m) => ({ ok: true, model: 'DS-2DE4425IW-DE (데모)', firmware: 'V5.7.0', position: S.getPtz(m[1]) })],
  ['get', /^\/face\/places\/(\d+)\/ptz\/position$/, (m) => S.getPtz(m[1])],
  ['post', /^\/face\/places\/(\d+)\/ptz\/move$/, (m, c) => { S.movePtz(m[1], c.body); return ok }],
  ['post', /^\/face\/places\/(\d+)\/ptz\/stop$/, () => ok],
  ['post', /^\/face\/places\/(\d+)\/zones$/, (m, c) => need(S.addZone(m[1], c.body.name), 'Place not found')],
  ['put', /^\/face\/places\/(\d+)\/zones\/order$/, (m, c) => { S.reorderZones(m[1], c.body.zone_ids || []); return ok }],
  ['delete', /^\/face\/places\/(\d+)\/zones\/(\d+)$/, (m) => { S.removeZone(m[1], m[2]); return ok }],
  ['post', /^\/face\/places\/(\d+)\/zones\/(\d+)\/goto$/, (m) => { S.gotoZone(m[1], m[2]); return ok }],
  ['post', /^\/face\/places\/(\d+)\/zones\/(\d+)\/test$/, (m) => need(S.testZone(m[1], m[2]), 'Zone not found')],

  // 얼굴 인식: 순찰 / 감지 / 로그
  ['get', /^\/face\/places\/(\d+)\/patrol\/status$/, (m) => S.patrolStatus(m[1])],
  ['post', /^\/face\/places\/(\d+)\/patrol\/start$/, (m, c) => need(S.patrolStart(m[1], c.body.record_all), 'Place not found')],
  ['post', /^\/face\/places\/(\d+)\/patrol\/stop$/, (m) => { S.patrolStop(m[1]); return ok }],
  ['get', /^\/face\/places\/(\d+)\/detections$/, (m) => ({ detections: S.listDetections(m[1]) })],
  ['delete', /^\/face\/places\/(\d+)\/detections$/, (m) => ({ removed: S.clearDetections(m[1]) })],
  ['delete', /^\/face\/detections\/(\d+)$/, (m) => { S.removeDetection(m[1]); return ok }],
  ['get', /^\/face\/places\/(\d+)\/seat-logs$/, (m, c) => ({ snapshots: S.listSeatLogs(m[1], Number(c.params.limit) || 50) })],

  // 얼굴 인식: 인물
  ['get', /^\/face\/people\/?$/, () => ({ people: S.listPeople() })],
  ['post', /^\/face\/people\/?$/, (m, c) => {
    const form = c.body
    const name = typeof form?.get === 'function' ? String(form.get('name') || '') : ''
    const count = typeof form?.getAll === 'function' ? form.getAll('images').length : 1
    S.addPerson(name || '등록자', count)
    return { found: count, total: count }
  }],
  ['put', /^\/face\/people\/(\d+)\/authorized$/, (m, c) => need(S.setPersonAuthorized(m[1], c.body.authorized), 'Person not found')],
  ['delete', /^\/face\/people\/(\d+)$/, (m) => { S.removePerson(m[1]); return ok }],
  ['post', /^\/face\/recognize$/, () => S.recognizeDemo()],
]

export async function demoAdapter(config) {
  await sleep(60 + Math.random() * 120)
  const method = (config.method || 'get').toLowerCase()
  const path = (config.url || '').split('?')[0]
  const ctx = { config, body: parseBody(config), params: config.params || {} }

  for (const [m, re, handler] of ROUTES) {
    if (m !== method) continue
    const match = path.match(re)
    if (!match) continue
    try {
      return respond(config, handler(match, ctx))
    } catch (e) {
      throw fail(config, e.status || 500, e.message)
    }
  }
  throw fail(config, 404, `데모 모드에서 지원하지 않는 요청: ${method.toUpperCase()} ${path}`)
}
