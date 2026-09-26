import test from 'node:test'
import assert from 'node:assert/strict'
import { describeError } from './errorMessage.js'

const http = (status, detail) => ({ response: { status, data: detail === undefined ? {} : { detail } }, message: `Request failed with status code ${status}` })

test('서버가 한국어 detail을 주면 그대로 쓴다', () => {
  assert.equal(describeError(http(404, '선택한 교실을 찾을 수 없습니다')), '선택한 교실을 찾을 수 없습니다')
})

test('detail 앞뒤 공백은 지운다', () => {
  assert.equal(describeError(http(400, '  이름이 비어 있습니다  ')), '이름이 비어 있습니다')
})

test('한글이 없는 영문 detail(FastAPI 기본 문구)은 믿지 않고 상태 코드 문장을 쓴다', () => {
  assert.equal(describeError(http(404, 'Not Found')), '요청한 항목을 찾을 수 없습니다')
  assert.equal(describeError(http(405, 'Method Not Allowed')), '오류가 발생했습니다 (405)')
  assert.equal(describeError(http(500, 'Internal Server Error')), '서버에서 오류가 발생했습니다')
})

test('영문이 섞여도 한글 메시지면 그대로 쓴다', () => {
  assert.equal(describeError(http(500, '분석 실패: CUDA out of memory')), '분석 실패: CUDA out of memory')
})

test('FastAPI 입력값 검증 오류(배열)는 한 문장으로 줄인다', () => {
  assert.equal(describeError(http(422, [{ msg: 'field required', loc: ['body', 'name'] }])), '입력값이 올바르지 않습니다')
})

test('영문 원문(Request failed with status code 500)은 보여 주지 않는다', () => {
  const msg = describeError(http(500))
  assert.equal(msg, '서버에서 오류가 발생했습니다')
  assert.ok(!msg.includes('Request failed'))
})

test('응답이 없으면(서버가 꺼졌거나 네트워크 오류) 연결 실패로 안내한다', () => {
  assert.equal(describeError({ message: 'Network Error', code: 'ERR_NETWORK' }), '서버에 연결하지 못했습니다')
})

test('시간 초과는 따로 안내한다', () => {
  assert.equal(describeError({ code: 'ECONNABORTED', message: 'timeout of 10000ms exceeded' }), '응답 시간이 초과되었습니다')
})

test('상태 코드별 문장', () => {
  assert.equal(describeError(http(401)), '로그인이 필요합니다')
  assert.equal(describeError(http(403)), '권한이 없습니다')
  assert.equal(describeError(http(404)), '요청한 항목을 찾을 수 없습니다')
  assert.equal(describeError(http(400)), '요청이 올바르지 않습니다')
  assert.equal(describeError(http(503)), '서버에서 오류가 발생했습니다')
})

test('그 밖의 상태 코드는 코드를 붙여 안내한다', () => {
  assert.equal(describeError(http(418)), '오류가 발생했습니다 (418)')
})

test('오류 객체가 비어 있어도 죽지 않는다', () => {
  assert.equal(describeError(null), '서버에 연결하지 못했습니다')
  assert.equal(describeError(undefined), '서버에 연결하지 못했습니다')
  assert.equal(describeError({}), '서버에 연결하지 못했습니다')
})
