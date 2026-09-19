import test from 'node:test'
import assert from 'node:assert/strict'
import { roomStatus, countRoomStatuses, describeRoomCounts } from './roomStatus.js'

const room = (over = {}) => ({ total: 10, occupied: 0, judgeable: 10, unknown: 0, error: false, ...over })

test('점유 좌석이 있으면 occupied', () => {
  assert.equal(roomStatus(room({ occupied: 3 })), 'occupied')
})

test('판정된 좌석이 전부 비어 있으면 empty', () => {
  assert.equal(roomStatus(room({ occupied: 0, judgeable: 10 })), 'empty')
})

test('조회 오류 교실은 unknown (비어 있음이 아니다)', () => {
  assert.equal(roomStatus(room({ error: true, judgeable: 0, unknown: 10 })), 'unknown')
})

test('오류 플래그가 있으면 값이 남아 있어도 unknown', () => {
  assert.equal(roomStatus(room({ error: true, occupied: 2, judgeable: 8 })), 'unknown')
})

test('좌석이 0개인 교실은 unknown', () => {
  assert.equal(roomStatus(room({ total: 0, judgeable: 0, unknown: 0 })), 'unknown')
})

test('좌석은 있지만 판정 가능한 좌석이 0이면 unknown', () => {
  assert.equal(roomStatus(room({ total: 10, judgeable: 0, unknown: 10 })), 'unknown')
})

test('일부만 판정 불가여도 판정된 좌석이 있으면 그 결과를 따른다', () => {
  assert.equal(roomStatus(room({ occupied: 0, judgeable: 8, unknown: 2 })), 'empty')
  assert.equal(roomStatus(room({ occupied: 1, judgeable: 8, unknown: 2 })), 'occupied')
})

test('값이 빠진 교실 객체도 unknown으로 처리한다', () => {
  assert.equal(roomStatus(null), 'unknown')
  assert.equal(roomStatus(undefined), 'unknown')
  assert.equal(roomStatus({}), 'unknown')
})

test('countRoomStatuses는 세 상태를 모두 센다', () => {
  const counts = countRoomStatuses([
    room({ occupied: 2 }),
    room({ occupied: 0 }),
    room({ error: true, judgeable: 0, unknown: 10 }),
    room({ total: 0, judgeable: 0 }),
    room({ occupied: 5 }),
  ])
  assert.deepEqual(counts, { occupied: 2, empty: 1, unknown: 2 })
})

test('countRoomStatuses는 빈 목록에서 0을 돌려준다', () => {
  assert.deepEqual(countRoomStatuses([]), { occupied: 0, empty: 0, unknown: 0 })
})

test('describeRoomCounts: 판정 불가 교실을 비어 있음에 섞지 않는다', () => {
  assert.equal(describeRoomCounts({ occupied: 2, empty: 1, unknown: 2 }), '1개 교실 비어 있음 · 판정 불가 2개')
})

test('describeRoomCounts: 비어 있음만 있을 때', () => {
  assert.equal(describeRoomCounts({ occupied: 3, empty: 2, unknown: 0 }), '2개 교실 비어 있음')
})

test('describeRoomCounts: 판정 불가만 있을 때', () => {
  assert.equal(describeRoomCounts({ occupied: 1, empty: 0, unknown: 1 }), '판정 불가 1개')
})

test('describeRoomCounts: 모두 사용 중일 때만 "모든 교실 사용 중"', () => {
  assert.equal(describeRoomCounts({ occupied: 4, empty: 0, unknown: 0 }), '모든 교실 사용 중')
})

test('describeRoomCounts: 교실이 없으면 빈 문구', () => {
  assert.equal(describeRoomCounts({ occupied: 0, empty: 0, unknown: 0 }), '')
})
