// 데모 모드용 메모리 데이터. 백엔드 응답 형태(routers/analysis.py, face.py)를 그대로 따른다.
// 값은 시드 기반이라 새로고침해도 같은 교실/과거 스냅샷이 나오고, 현재 값만 티커가 조금씩 바꾼다.
// 얼굴 사진은 만들지 않는다(사진 URL은 vite 데모 플러그인이 실루엣 SVG로 응답).

// ── 유틸 ────────────────────────────────────────────────────────────────────
const pad = (n) => String(n).padStart(2, '0')
export const localDateStr = (d = new Date()) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
export const localIso = (d = new Date()) =>
  `${localDateStr(d)}T${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`

function hash(str) {
  let h = 2166136261
  for (let i = 0; i < str.length; i++) { h ^= str.charCodeAt(i); h = Math.imul(h, 16777619) }
  return h >>> 0
}
function seeded(...keys) {
  let a = hash(keys.join('|'))
  a = (a + 0x6d2b79f5) | 0
  let t = Math.imul(a ^ (a >>> 15), 1 | a)
  t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
  return ((t ^ (t >>> 14)) >>> 0) / 4294967296
}
const pick = (arr) => arr[Math.floor(Math.random() * arr.length)]
const clone = (v) => JSON.parse(JSON.stringify(v))

// ── 스냅샷 슬롯 (09:00 ~ 21:00, 10분 간격 = 73칸) ────────────────────────────
export const SLOT_MIN = 10
export const FIRST_MIN = 9 * 60
export const LAST_MIN = 21 * 60
export const SLOT_COUNT = (LAST_MIN - FIRST_MIN) / SLOT_MIN + 1
export const slotTime = (slot) => {
  const m = FIRST_MIN + slot * SLOT_MIN
  return `${pad(Math.floor(m / 60))}:${pad(m % 60)}`
}

// 전시장이 수업 시간이 아닐 때 열어도 그림이 비지 않도록, 수업 시간 밖이면 오후 3시 40분쯤을 "지금"으로 본다.
export function demoNowSlot() {
  const now = new Date()
  const m = now.getHours() * 60 + now.getMinutes()
  if (m < FIRST_MIN || m > LAST_MIN) return 40
  return Math.min(SLOT_COUNT - 1, Math.round((m - FIRST_MIN) / SLOT_MIN))
}

function maxSlotFor(date) {
  const today = localDateStr()
  if (date > today) return -1
  if (date === today) return demoNowSlot()
  return SLOT_COUNT - 1
}

// ── 교실 8개 ────────────────────────────────────────────────────────────────
const ROOM_DEFS = [
  { id: 1, name: '창조관 301호', seats: 24 },
  { id: 2, name: '창조관 302호', seats: 20 },
  { id: 3, name: '창조관 303호', seats: 18 },
  { id: 4, name: '창조관 304호', seats: 16 },
  { id: 5, name: '창조관 401호', seats: 24 },
  { id: 6, name: '창조관 402호', seats: 20 },
  { id: 7, name: '창조관 403호', seats: 12 },
  { id: 8, name: '창조관 404호', seats: 16 },
]

const SCHEDULE = {
  mon: [9, 10, 11, 13, 14, 15, 16, 17], tue: [9, 10, 11, 13, 14, 15, 16, 17],
  wed: [9, 10, 11, 13, 14, 15, 16, 17], thu: [9, 10, 11, 13, 14, 15, 16, 17],
  fri: [9, 10, 11, 13, 14, 15, 16, 17], sat: [], sun: [],
}

const FRAME_W = 1280
const FRAME_H = 720

function buildRoom(def) {
  const n = def.seats
  const cols = n >= 18 ? 6 : 4
  const rows = Math.ceil(n / cols)
  const seatIds = Array.from({ length: n }, (_, i) => String(i + 1))
  const half = Math.ceil(n / 2)
  const colGap = (900 - 140) / cols
  const rowGap = (600 - 230) / rows

  const objects = [
    { id: 1, type: 'cctv', x: 30, y: 30, w: 90, h: 60, label: 'CCTV 1' },
    { id: 2, type: 'cctv', x: 780, y: 30, w: 90, h: 60, label: 'CCTV 2' },
  ]
  const deskRect = {}
  seatIds.forEach((sid, i) => {
    const c = i % cols
    const r = Math.floor(i / cols)
    const x = Math.round(70 + c * colGap + (colGap - 90) / 2)
    const y = Math.round(150 + r * rowGap)
    deskRect[sid] = { x, y, w: 90, h: 50 }
    objects.push({ id: 10 + i, type: 'desk', x, y, w: 90, h: 50, label: sid, cctvIds: [i < half ? 1 : 2] })
    objects.push({ id: 200 + i, type: 'chair', x: x + 25, y: y + 54, w: 40, h: 24 })
  })

  const sx = FRAME_W / 900
  const sy = FRAME_H / 600
  const cameras = [1, 2].map((k) => {
    const ids = k === 1 ? seatIds.slice(0, half) : seatIds.slice(half)
    const seat_lines = {}
    ids.forEach((sid) => {
      const d = deskRect[sid]
      const fx = d.x * sx, fy = d.y * sy, fw = d.w * sx, fh = d.h * sy
      seat_lines[sid] = [
        [Math.round(fx), Math.round(fy + fh)], [Math.round(fx + fw), Math.round(fy + fh)],
        [Math.round(fx + 10), Math.round(fy)], [Math.round(fx + fw - 10), Math.round(fy)],
      ]
    })
    return {
      camera_id: `R${def.id}C${k}`, name: `CCTV ${k}`, ip_address: `192.168.${def.id}.${100 + k}`,
      rtsp_url: 'rtsp://demo/stream', roi_polygon: [], view_group: null,
      seat_count: ids.length, seat_ids: ids, seat_lines,
    }
  })

  const now = localIso()
  return {
    classroom: {
      id: def.id, name: def.name, cameras, prompt: null,
      yolo_model: 'yolov8x', conf_threshold: null, yolo_llm_model: 'claude-sonnet-5',
      yolo_llm_conf_threshold: null, yolo_llm_yolo_model: 'yolo26x-pose',
      schedule: clone(SCHEDULE), created_at: now, updated_at: now,
    },
    map: { mapW: 900, mapH: 600, objects },
    seatIds,
  }
}

let rooms = ROOM_DEFS.map(buildRoom)
const roomOf = (id) => rooms.find((r) => r.classroom.id === Number(id))

// ── 스냅샷 생성 (시드 기반, 새로고침해도 동일) ────────────────────────────────
function occupancyCurve(hourFloat) {
  const peak = Math.exp(-((hourFloat - 13.5) ** 2) / (2 * 2.6 ** 2))
  const base = 0.12 + 0.8 * peak
  return hourFloat >= 18 ? base * 0.35 : base
}

function snapshotSeats(room, date, slot) {
  const hourFloat = (FIRST_MIN + slot * SLOT_MIN) / 60
  const roomFactor = 0.65 + 0.35 * seeded('room', room.classroom.id)
  const dayFactor = 0.75 + 0.25 * seeded('day', date)
  const p = occupancyCurve(hourFloat) * roomFactor * dayFactor
  const seats = {}
  room.seatIds.forEach((sid) => {
    if (seeded(room.classroom.id, sid, date, slot, 'unknown') < 0.012) return // 판정 불가: 스냅샷에 없음
    const bias = 0.6 + 0.8 * seeded('bias', room.classroom.id, sid)
    const persist = seeded(room.classroom.id, sid, date, Math.floor(slot / 2), 'state')
    seats[sid] = persist < p * bias ? 'occupied' : 'empty'
  })
  return seats
}

// ── 현재 점유 상태 (티커가 조금씩 바꾼다) ─────────────────────────────────────
const live = new Map() // roomId -> { occupied:Set, unknown:Set }

function initLive(room) {
  const seats = snapshotSeats(room, localDateStr(), demoNowSlot())
  const occupied = new Set()
  const unknown = new Set()
  room.seatIds.forEach((sid) => {
    if (!(sid in seats)) unknown.add(sid)
    else if (seats[sid] === 'occupied') occupied.add(sid)
  })
  live.set(room.classroom.id, { occupied, unknown })
}
rooms.forEach(initLive)

function liveSeats(room) {
  const st = live.get(room.classroom.id)
  const seats = {}
  room.seatIds.forEach((sid) => {
    if (st.unknown.has(sid)) return
    seats[sid] = st.occupied.has(sid) ? 'occupied' : 'empty'
  })
  return seats
}

function seatsAt(room, date, slot) {
  if (date === localDateStr() && slot === demoNowSlot()) return liveSeats(room)
  return snapshotSeats(room, date, slot)
}

// 화면이 "마지막 수집 시각 / 다음 수집까지"를 계산할 수 있도록 티커 상태를 노출한다.
export const tickInfo = { last: Date.now(), intervalMs: 10000 }

export function tickOccupancy() {
  tickInfo.last = Date.now()
  rooms.forEach((room) => {
    const st = live.get(room.classroom.id)
    const flips = 1 + Math.floor(Math.random() * 2)
    for (let i = 0; i < flips; i++) {
      const sid = pick(room.seatIds)
      if (st.unknown.has(sid)) { st.unknown.delete(sid); continue }
      if (st.occupied.has(sid)) st.occupied.delete(sid)
      else st.occupied.add(sid)
    }
    // 가끔 한 좌석이 잠깐 판정 불가가 된다(카메라 프레임 실패 흉내)
    if (Math.random() < 0.12 && st.unknown.size < 2) st.unknown.add(pick(room.seatIds))
    // 너무 비거나 꽉 차지 않게 범위 유지
    const ratio = st.occupied.size / room.seatIds.length
    if (ratio > 0.92) st.occupied.delete(pick([...st.occupied]))
    if (ratio < 0.08) st.occupied.add(pick(room.seatIds))
  })
}

// ── 교실 / 배치도 ───────────────────────────────────────────────────────────
export const listClassrooms = () => clone(rooms.map((r) => r.classroom))
export const getClassroom = (id) => (roomOf(id) ? clone(roomOf(id).classroom) : null)
export const getMap = (id) => (roomOf(id) ? clone(roomOf(id).map) : null)
export function setMap(id, data) { const r = roomOf(id); if (r) r.map = clone(data) }

export function createClassroom(body) {
  const id = Math.max(0, ...rooms.map((r) => r.classroom.id)) + 1
  const room = buildRoom({ id, name: body?.name || `교실 ${id}`, seats: 12 })
  rooms.push(room)
  initLive(room)
  return clone(room.classroom)
}
export function updateClassroom(id, patch) {
  const r = roomOf(id)
  if (!r) return null
  Object.entries(patch || {}).forEach(([k, v]) => { if (v !== undefined && v !== null) r.classroom[k] = clone(v) })
  r.classroom.updated_at = localIso()
  return clone(r.classroom)
}
export function removeClassroom(id) { rooms = rooms.filter((r) => r.classroom.id !== Number(id)) }

// ── 좌석 점유 분석 ──────────────────────────────────────────────────────────
function cameraResults(room) {
  const st = live.get(room.classroom.id)
  return room.classroom.cameras.map((cam) => {
    const occupied = cam.seat_ids.filter((s) => st.occupied.has(s) && !st.unknown.has(s))
    const empty = cam.seat_ids.filter((s) => !st.occupied.has(s) && !st.unknown.has(s))
    return {
      camera_id: cam.camera_id, name: cam.name, occupied, empty,
      total: cam.seat_ids.length, occupied_count: occupied.length,
    }
  })
}

export function seatOccupancy(id) {
  const room = roomOf(id)
  if (!room) return null
  const cameras = cameraResults(room)
  const total_occupied = cameras.reduce((a, c) => a + c.occupied_count, 0)
  const total_seats = cameras.reduce((a, c) => a + c.total, 0)
  const total_empty = cameras.reduce((a, c) => a + c.empty.length, 0)
  return { cameras, total_seats, total_occupied, total_empty }
}

export function yoloLlmCount(id) {
  const base = seatOccupancy(id)
  if (!base) return null
  const activities = ['공부', '휴대폰', '노트북', '대화']
  const cameras = base.cameras.map((c) => ({
    ...c, yolo_count: c.occupied_count,
    llm_response: c.occupied.map((s) => `${s} - ${pick(activities)}`).join('\n'),
  }))
  return { cameras, total_yolo_count: base.total_occupied, total_seats: base.total_seats, total_occupied: base.total_occupied }
}

// ── 스냅샷 / 시간대별 / 일별 통계 ──────────────────────────────────────────────
const numSort = (a, b) => Number(a) - Number(b)

export function snapshotsFor(id, date) {
  const room = roomOf(id)
  if (!room) return null
  const max = maxSlotFor(date)
  const snapshots = []
  for (let s = 0; s <= max; s++) {
    const m = FIRST_MIN + s * SLOT_MIN
    snapshots.push({ ts: `${date}T${pad(Math.floor(m / 60))}:${pad(m % 60)}:00`, seats: seatsAt(room, date, s) })
  }
  return { date, interval_minutes: SLOT_MIN, snapshots }
}

export function hourlyFor(id, date) {
  const room = roomOf(id)
  if (!room) return null
  const max = maxSlotFor(date)
  const day = new Date(`${date}T00:00:00`)
  const key = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'][(day.getDay() + 6) % 7]
  const scheduled = room.classroom.schedule?.[key] ? new Set(room.classroom.schedule[key]) : null
  const hours = []
  for (let h = 9; h <= 21; h++) {
    const slot = (h - 9) * 6
    const isScheduled = scheduled === null ? true : scheduled.has(h)
    const entry = { hour: h, time: `${pad(h)}:00`, scheduled: isScheduled, occupied: null, total: null, seats: null }
    if (isScheduled && slot <= max) {
      const seats = seatsAt(room, date, slot)
      const occ = Object.keys(seats).filter((s) => seats[s] === 'occupied').sort(numSort)
      entry.occupied = occ.length
      entry.total = Object.keys(seats).length
      entry.seats = occ
    }
    hours.push(entry)
  }
  return { date, hours }
}

export function statsDailyFor(id, date) {
  const room = roomOf(id)
  if (!room) return null
  const max = maxSlotFor(date)
  const seats = {}
  for (let s = 0; s <= max; s++) {
    const snap = seatsAt(room, date, s)
    Object.entries(snap).forEach(([sid, state]) => {
      const e = (seats[sid] ||= { occupied: 0, empty: 0, total: 0 })
      e.total += 1
      e[state] += 1
    })
  }
  Object.values(seats).forEach((e) => {
    e.occupied_pct = e.total ? Math.round((e.occupied / e.total) * 100) : 0
    e.occupied_minutes = e.occupied * SLOT_MIN
  })
  return { date, period_minutes: Math.max(0, (max + 1) * SLOT_MIN), seats }
}

// 프레임 렌더링용: 지정 시각(ts)의 좌석 상태. ts가 없으면 현재 상태.
export function seatStateAt(id, ts) {
  const room = roomOf(id)
  if (!room) return null
  if (!ts) return { room, seats: liveSeats(room), label: '현재' }
  const [date, time = '00:00'] = ts.split('T')
  const [hh, mm] = time.split(':').map(Number)
  const slot = Math.max(0, Math.min(SLOT_COUNT - 1, Math.round((hh * 60 + mm - FIRST_MIN) / SLOT_MIN)))
  return { room, seats: seatsAt(room, date, slot), label: `${date} ${slotTime(slot)}` }
}

// ── 얼굴 인식: 장소 / 구역 / 인물 ─────────────────────────────────────────────
const PEOPLE_SEED = [
  { name: '김OO', authorized: true, samples: 4 },
  { name: '이OO', authorized: true, samples: 3 },
  { name: '박OO', authorized: true, samples: 3 },
  { name: '최OO', authorized: false, samples: 2 },
  { name: '정OO', authorized: true, samples: 5 },
]
let personSeq = 1
let people = PEOPLE_SEED.map((p) => ({ id: personSeq++, ...p, enrolled_at: localIso(new Date(Date.now() - personSeq * 86400000)) }))

const defaultCamera = () => ({
  ip: '192.168.0.50', username: 'admin', password: '', channel_code: '101',
  control_channel: 1, http_port: 80, rtsp_port: 554,
})

let zoneSeq = 100
const makeZone = (name, pan, tilt, zoom, seats) => ({
  id: zoneSeq++, name, pan, tilt, zoom,
  rois: seats.map((s) => ({ name: String(s), points: [[0.2, 0.3], [0.4, 0.3], [0.4, 0.5], [0.2, 0.5]] })),
})

let places = [
  {
    id: 1, name: '창조관 301호', classroom_id: 1, camera: defaultCamera(),
    zones: [
      makeZone('앞줄 좌측', 300, 100, 20, [1, 2, 7, 8]),
      makeZone('앞줄 우측', 1200, 100, 20, [5, 6, 11, 12]),
      makeZone('뒷줄 중앙', 700, 250, 15, [15, 16, 21, 22]),
      makeZone('대기 위치', 700, 150, 10, []),
    ],
  },
  {
    id: 2, name: '창조관 401호', classroom_id: 5, camera: defaultCamera(),
    zones: [
      makeZone('앞줄', 500, 90, 18, [1, 2, 3, 4]),
      makeZone('중간줄', 900, 160, 16, [9, 10, 11, 12]),
      makeZone('뒷줄', 700, 260, 14, [19, 20, 21, 22]),
    ],
  },
]
let placeSeq = 3
const placeOf = (id) => places.find((p) => p.id === Number(id))
const ptz = new Map(places.map((p) => [p.id, { pan: 700, tilt: 150, zoom: 20 }]))

export const listPlaces = () => clone(places)
export const getPlace = (id) => (placeOf(id) ? clone(placeOf(id)) : null)
export function createPlace(body) {
  const cls = body?.classroom_id ? roomOf(body.classroom_id) : null
  const place = {
    id: placeSeq++, name: cls?.classroom.name || body?.name || `장소 ${placeSeq}`,
    classroom_id: cls ? cls.classroom.id : null, camera: { ...defaultCamera(), ip: '' }, zones: [],
  }
  places.push(place)
  ptz.set(place.id, { pan: 700, tilt: 150, zoom: 20 })
  ensurePatrol(place)
  return clone(place)
}
export function updatePlace(id, patch) {
  const p = placeOf(id)
  if (!p) return null
  if (patch?.name) p.name = patch.name
  if (patch?.camera) p.camera = { ...p.camera, ...patch.camera }
  if (patch?.clear_classroom) p.classroom_id = null
  else if (patch?.classroom_id) p.classroom_id = patch.classroom_id
  return clone(p)
}
export function removePlace(id) { places = places.filter((p) => p.id !== Number(id)); patrols.delete(Number(id)) }

export const getPtz = (id) => ({ ...(ptz.get(Number(id)) || { pan: 0, tilt: 0, zoom: 10 }) })
export function movePtz(id, d) {
  const cur = ptz.get(Number(id))
  if (!cur) return
  cur.pan += d.pan || 0
  cur.tilt += d.tilt || 0
  cur.zoom = Math.max(10, cur.zoom + (d.zoom || 0))
}
export function addZone(id, name) {
  const p = placeOf(id)
  const cur = ptz.get(Number(id))
  if (!p || !cur) return null
  const z = { id: zoneSeq++, name, pan: cur.pan, tilt: cur.tilt, zoom: cur.zoom, rois: [] }
  p.zones.push(z)
  return clone(z)
}
export function removeZone(id, zoneId) { const p = placeOf(id); if (p) p.zones = p.zones.filter((z) => z.id !== Number(zoneId)) }
export function reorderZones(id, ids) {
  const p = placeOf(id)
  if (!p) return
  p.zones = ids.map((zid) => p.zones.find((z) => z.id === Number(zid))).filter(Boolean)
}
export function gotoZone(id, zoneId) {
  const p = placeOf(id)
  const z = p?.zones.find((x) => x.id === Number(zoneId))
  if (z) ptz.set(Number(id), { pan: z.pan, tilt: z.tilt, zoom: z.zoom })
}
export function testZone(id, zoneId) {
  const p = placeOf(id)
  const z = p?.zones.find((x) => x.id === Number(zoneId))
  if (!z) return null
  const seats = {}
  z.rois.forEach((r) => {
    const roll = Math.random()
    seats[r.name] = roll < 0.35 ? null
      : { verified: roll > 0.65, authorized: roll > 0.65, name: roll > 0.65 ? pick(PEOPLE_SEED).name : null, score: Number((0.2 + Math.random() * 0.6).toFixed(2)) }
  })
  return { zone: z.name, detected: Object.values(seats).filter(Boolean).length, outside_roi: 0, seats }
}

export const listPeople = () => clone(people)
export function addPerson(name, samples) {
  const p = { id: personSeq++, name, samples, enrolled_at: localIso(), authorized: true }
  people.unshift(p)
  return clone(p)
}
export function setPersonAuthorized(id, authorized) {
  const p = people.find((x) => x.id === Number(id))
  if (p) p.authorized = !!authorized
  return p ? { authorized: p.authorized } : null
}
export function removePerson(id) { people = people.filter((p) => p.id !== Number(id)) }
export function recognizeDemo() {
  if (Math.random() < 0.3) return { faces: [], threshold: 0.45 }
  const person = pick(people)
  return { faces: [{ name: person.name, authorized: person.authorized, score: Number((0.5 + Math.random() * 0.35).toFixed(2)) }], threshold: 0.45 }
}

// ── 순찰 상태 순환 / 감지 로그 / 자리별 로그 ──────────────────────────────────
const PHASES = ['move', 'settle', 'shoot', 'analyze']
const patrols = new Map() // placeId -> { frames, pointer, detectionsThisRun, recordAll, seatsLogged }
const detections = new Map() // placeId -> [ ... ] (최신순)
const seatLogs = new Map() // placeId -> [ ... ] (최신순)
let detectionSeq = 1

function framesFor(place) {
  const n = place.zones.length
  const frames = []
  const idle = { running: false, zone: null, zone_index: 0, total_zones: n, completed: false, phase: null }
  for (let i = 0; i < 4; i++) frames.push({ ...idle })
  place.zones.forEach((z, idx) => {
    const base = { running: true, zone: z.name, zone_index: idx + 1, total_zones: n, completed: false }
    if (!z.rois.length) frames.push({ ...base, phase: 'move' })
    else PHASES.forEach((phase) => frames.push({ ...base, phase }))
  })
  const last = place.zones[n - 1]
  for (let i = 0; i < 4; i++) frames.push({ running: false, zone: last?.name ?? null, zone_index: n, total_zones: n, completed: true, phase: null })
  return frames
}

function ensurePatrol(place, offset = 0) {
  patrols.set(place.id, { frames: framesFor(place), pointer: offset, detectionsThisRun: 0, recordAll: false, seatsLogged: 0 })
  if (!detections.has(place.id)) detections.set(place.id, [])
  if (!seatLogs.has(place.id)) seatLogs.set(place.id, [])
}

function buildSeatLog(place) {
  const seats = {}
  place.zones.forEach((z) => z.rois.forEach((r) => {
    const roll = Math.random()
    seats[r.name] = roll < 0.3 ? null
      : { verified: roll > 0.6, name: roll > 0.6 ? pick(PEOPLE_SEED).name : null, score: Number((0.3 + Math.random() * 0.5).toFixed(3)), zone: z.name }
  }))
  return { ts: localIso(), seats }
}

function recordDetection(place, zone, recordAll, tsDate = new Date()) {
  const roi = zone.rois.length ? pick(zone.rois) : null
  const known = Math.random() < 0.4
  const person = known ? pick(people) : null
  if (person?.authorized && !recordAll) return false
  const item = {
    id: detectionSeq++, place_id: place.id,
    zone_name: roi ? `${zone.name} · ${roi.name}` : zone.name,
    name: person ? person.name : null,
    score: Number((known ? 0.5 + Math.random() * 0.35 : 0.12 + Math.random() * 0.28).toFixed(3)),
    authorized: person ? person.authorized : null,
    ts: localIso(tsDate),
  }
  const list = detections.get(place.id)
  list.unshift(item)
  if (list.length > 60) list.length = 60
  return true
}

export function tickPatrol() {
  places.forEach((place) => {
    const st = patrols.get(place.id)
    if (!st) return
    const prev = st.frames[st.pointer]
    st.pointer = (st.pointer + 1) % st.frames.length
    const f = st.frames[st.pointer]
    if (f.running && f.zone_index === 1 && f.phase === 'move') st.detectionsThisRun = 0
    if (f.running && f.phase === 'analyze' && Math.random() < 0.6) {
      const zone = place.zones[f.zone_index - 1]
      if (zone && recordDetection(place, zone, st.recordAll)) st.detectionsThisRun += 1
    }
    if (f.completed && !prev.completed) {
      const log = buildSeatLog(place)
      seatLogs.get(place.id).unshift(log)
      st.seatsLogged = Object.keys(log.seats).length
    }
  })
}

export function patrolStatus(id) {
  const st = patrols.get(Number(id))
  if (!st) return { running: false, zone: null, zone_index: 0, total_zones: 0, detections: 0, completed: false, record_all: false, seats_logged: 0, error: null, phase: null }
  const f = st.frames[st.pointer]
  return { ...f, detections: st.detectionsThisRun, record_all: st.recordAll, seats_logged: st.seatsLogged, error: null }
}
export function patrolStart(id, recordAll) {
  const st = patrols.get(Number(id))
  if (!st) return null
  st.recordAll = !!recordAll
  st.pointer = 4 // 첫 구역 이동 단계로 바로 시작
  st.detectionsThisRun = 0
  return patrolStatus(id)
}
export function patrolStop(id) {
  const st = patrols.get(Number(id))
  if (st) st.pointer = 0
}
export const listDetections = (id) => clone(detections.get(Number(id)) || [])
export function removeDetection(detectionId) {
  detections.forEach((list, pid) => detections.set(pid, list.filter((d) => d.id !== Number(detectionId))))
}
export function clearDetections(id) {
  const n = (detections.get(Number(id)) || []).length
  detections.set(Number(id), [])
  return n
}
export const listSeatLogs = (id, limit = 50) => clone((seatLogs.get(Number(id)) || []).slice(0, limit))

// 초기 시드: 과거 감지 기록과 자리별 로그
places.forEach((p, i) => {
  ensurePatrol(p, i * 9)
  const withRois = p.zones.filter((x) => x.rois.length)
  for (let k = 14; k >= 1; k--) {
    recordDetection(p, withRois[k % withRois.length], true, new Date(Date.now() - k * 23 * 60000))
  }
  seatLogs.get(p.id).push(buildSeatLog(p), buildSeatLog(p))
})

// ── 프롬프트 ─────────────────────────────────────────────────────────────────
let promptConfig = { system_prompt: '', default_user_prompt: '' }
export const getPrompts = () => clone(promptConfig)
export function setPrompts(patch) { promptConfig = { ...promptConfig, ...(patch || {}) }; return clone(promptConfig) }

export const FRAME_SIZE = { width: FRAME_W, height: FRAME_H }

// ── 티커 ─────────────────────────────────────────────────────────────────────
let occTimer = null
let patrolTimer = null
export function startTicker() {
  if (occTimer) return
  occTimer = setInterval(tickOccupancy, 10000) // 10초마다 점유 좌석이 조금씩 바뀐다
  patrolTimer = setInterval(tickPatrol, 2500) // 순찰은 구역당 4단계 × 2.5초 = 10초
}
export function stopTicker() {
  clearInterval(occTimer)
  clearInterval(patrolTimer)
  occTimer = null
  patrolTimer = null
}
