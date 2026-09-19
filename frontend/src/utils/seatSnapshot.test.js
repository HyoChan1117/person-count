import { test } from 'node:test'
import assert from 'node:assert/strict'
import { seatStatesFor, hasSnapshotRecord } from './seatSnapshot.js'

test('seatStatesFor: 기록이 있으면 좌석별 상태를 그대로 쓴다', () => {
  const states = seatStatesFor({ 1: 'occupied', 2: 'empty' }, ['1', '2'])
  assert.deepEqual(states, { 1: 'occupied', 2: 'empty' })
})

test('seatStatesFor: 스냅샷에 빠진 좌석은 판정 불가', () => {
  const states = seatStatesFor({ 1: 'occupied' }, ['1', '2'])
  assert.deepEqual(states, { 1: 'occupied', 2: 'unknown' })
})

test('seatStatesFor: 스냅샷 자체가 없으면 모든 좌석이 판정 불가 값으로 채워진다', () => {
  assert.deepEqual(seatStatesFor(null, ['1', '2']), { 1: 'unknown', 2: 'unknown' })
})

test('seatStatesFor: 좌석이 없으면 빈 객체', () => {
  assert.deepEqual(seatStatesFor({ 1: 'occupied' }, []), {})
})

test('hasSnapshotRecord: 슬롯이 없거나 seats가 null이면 기록 없음', () => {
  assert.equal(hasSnapshotRecord(null), false)
  assert.equal(hasSnapshotRecord(undefined), false)
  assert.equal(hasSnapshotRecord({ seats: null }), false)
})

test('hasSnapshotRecord: seats가 있으면(비어 있어도) 기록 있음', () => {
  assert.equal(hasSnapshotRecord({ seats: { 1: 'empty' } }), true)
  assert.equal(hasSnapshotRecord({ seats: {} }), true)
})
