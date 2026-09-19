import test from 'node:test'
import assert from 'node:assert/strict'
import { ref } from 'vue'
import { useDailyStats } from './useDailyStats.js'

function deferred() {
  let resolve, reject
  const promise = new Promise((res, rej) => { resolve = res; reject = rej })
  return { promise, resolve, reject }
}

const daily = (seats, minutes = 60) => ({ date: 'x', period_minutes: minutes, seats })
const hourly = (hours) => ({ date: 'x', hours })
const tick = () => new Promise((r) => setImmediate(r))

// 날짜별로 응답을 직접 풀어 줄 수 있는 가짜 API
function makeApi() {
  const calls = []
  const api = {
    fetchDaily: (date) => { const d = deferred(); calls.push({ kind: 'daily', date, d }); return d.promise },
    fetchHourly: (date) => { const d = deferred(); calls.push({ kind: 'hourly', date, d }); return d.promise },
  }
  const forDate = (date) => ({
    daily: calls.find((c) => c.kind === 'daily' && c.date === date),
    hourly: calls.find((c) => c.kind === 'hourly' && c.date === date),
  })
  return { api, forDate, calls }
}

test('성공하면 통계를 채우고 loading을 끈다', async () => {
  const date = ref('2026-09-14')
  const { api, forDate } = makeApi()
  const s = useDailyStats({ ...api, dateStr: date })
  const p = s.load()
  assert.equal(s.loading.value, true)
  const c = forDate('2026-09-14')
  c.daily.d.resolve(daily({ 1: { occupied_minutes: 30 } }, 120))
  c.hourly.d.resolve(hourly([{ hour: 9 }]))
  await p
  assert.deepEqual(s.seatStats.value, { 1: { occupied_minutes: 30 } })
  assert.equal(s.periodMinutes.value, 120)
  assert.deepEqual(s.hourlyStats.value, [{ hour: 9 }])
  assert.equal(s.loading.value, false)
  assert.equal(s.error.value, '')
})

test('실패하면 이전 날짜 통계를 비우고 오류를 남긴다', async () => {
  const date = ref('2026-09-14')
  const { api, forDate } = makeApi()
  const s = useDailyStats({ ...api, dateStr: date })

  let p = s.load()
  let c = forDate('2026-09-14')
  c.daily.d.resolve(daily({ 1: { occupied_minutes: 30 } }))
  c.hourly.d.resolve(hourly([{ hour: 9 }]))
  await p
  assert.equal(Object.keys(s.seatStats.value).length, 1)

  date.value = '2026-09-15'
  p = s.load()
  c = forDate('2026-09-15')
  c.daily.d.reject(Object.assign(new Error('boom'), { response: { data: { detail: '서버 오류' } } }))
  c.hourly.d.resolve(hourly([]))
  await p

  assert.deepEqual(s.seatStats.value, {})
  assert.deepEqual(s.hourlyStats.value, [])
  assert.equal(s.periodMinutes.value, 0)
  assert.equal(s.error.value, '서버 오류')
  assert.equal(s.loading.value, false)
})

test('서버 detail이 없으면 예외 message를 오류로 쓴다', async () => {
  const date = ref('d')
  const { api, forDate } = makeApi()
  const s = useDailyStats({ ...api, dateStr: date })
  const p = s.load()
  const c = forDate('d')
  c.daily.d.reject(new Error('Network Error'))
  c.hourly.d.reject(new Error('Network Error'))
  await p
  assert.equal(s.error.value, 'Network Error')
})

test('실패 뒤 다시 성공하면 오류가 지워지고 데이터가 채워진다', async () => {
  const date = ref('d')
  const { api, calls } = makeApi()
  const s = useDailyStats({ ...api, dateStr: date })

  let p = s.load()
  calls[0].d.reject(new Error('down')); calls[1].d.reject(new Error('down'))
  await p
  assert.equal(s.error.value, 'down')

  p = s.load()
  calls[2].d.resolve(daily({ 7: { occupied_minutes: 10 } }))
  calls[3].d.resolve(hourly([{ hour: 10 }]))
  await p
  assert.equal(s.error.value, '')
  assert.deepEqual(s.seatStats.value, { 7: { occupied_minutes: 10 } })
})

test('늦게 도착한 이전 요청의 응답은 최신 응답을 덮어쓰지 못한다', async () => {
  const date = ref('2026-09-14')
  const { api, forDate } = makeApi()
  const s = useDailyStats({ ...api, dateStr: date })

  const pOld = s.load()                 // 9/14 요청 (느림)
  date.value = '2026-09-15'
  const pNew = s.load()                 // 9/15 요청 (빠름)

  const newer = forDate('2026-09-15')
  newer.daily.d.resolve(daily({ 2: { occupied_minutes: 99 } }))
  newer.hourly.d.resolve(hourly([{ hour: 11 }]))
  await pNew

  const older = forDate('2026-09-14')
  older.daily.d.resolve(daily({ 1: { occupied_minutes: 1 } }))
  older.hourly.d.resolve(hourly([{ hour: 9 }]))
  await pOld

  assert.deepEqual(s.seatStats.value, { 2: { occupied_minutes: 99 } })
  assert.deepEqual(s.hourlyStats.value, [{ hour: 11 }])
  assert.equal(s.loading.value, false)
})

test('늦게 도착한 이전 요청의 실패도 최신 결과를 망가뜨리지 않는다', async () => {
  const date = ref('2026-09-14')
  const { api, forDate } = makeApi()
  const s = useDailyStats({ ...api, dateStr: date })

  const pOld = s.load()
  date.value = '2026-09-15'
  const pNew = s.load()

  const newer = forDate('2026-09-15')
  newer.daily.d.resolve(daily({ 2: { occupied_minutes: 5 } }))
  newer.hourly.d.resolve(hourly([{ hour: 12 }]))
  await pNew

  const older = forDate('2026-09-14')
  older.daily.d.reject(new Error('late failure'))
  older.hourly.d.resolve(hourly([]))
  await pOld

  assert.deepEqual(s.seatStats.value, { 2: { occupied_minutes: 5 } })
  assert.equal(s.error.value, '')
})

test('요청이 겹치는 동안 loading은 최신 요청이 끝날 때까지 유지된다', async () => {
  const date = ref('2026-09-14')
  const { api, forDate } = makeApi()
  const s = useDailyStats({ ...api, dateStr: date })

  const pOld = s.load()
  date.value = '2026-09-15'
  const pNew = s.load()

  const older = forDate('2026-09-14')
  older.daily.d.resolve(daily({})); older.hourly.d.resolve(hourly([]))
  await pOld
  assert.equal(s.loading.value, true, '이전 요청이 끝나도 최신 요청이 남아 있으면 로딩 중')

  const newer = forDate('2026-09-15')
  newer.daily.d.resolve(daily({})); newer.hourly.d.resolve(hourly([]))
  await pNew
  assert.equal(s.loading.value, false)
})

test('응답에 seats/hours/period_minutes가 없어도 빈 값으로 처리한다', async () => {
  const date = ref('d')
  const { api, calls } = makeApi()
  const s = useDailyStats({ ...api, dateStr: date })
  const p = s.load()
  calls[0].d.resolve({}); calls[1].d.resolve({})
  await p
  assert.deepEqual(s.seatStats.value, {})
  assert.deepEqual(s.hourlyStats.value, [])
  assert.equal(s.periodMinutes.value, 0)
  assert.equal(s.error.value, '')
})

test('load는 호출 시점의 날짜로 요청한다', async () => {
  const date = ref('2026-09-14')
  const { api, calls } = makeApi()
  const s = useDailyStats({ ...api, dateStr: date })
  s.load()
  date.value = '2026-09-16'
  s.load()
  await tick()
  assert.deepEqual(calls.map((c) => c.date), ['2026-09-14', '2026-09-14', '2026-09-16', '2026-09-16'])
})
