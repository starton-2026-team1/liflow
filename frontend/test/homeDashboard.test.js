import test from 'node:test'
import assert from 'node:assert/strict'

import { createHomeDashboard } from '../src/features/main/utils/homeDashboard.js'

const now = new Date('2026-09-14T12:00:00+09:00')
const sensor = { id: 10, personId: 1, name: '거실센서', location: '거실', status: 'normal' }

const build = (detectedAt, person = {}) => createHomeDashboard(
  { id: 1, inactivityThresholdMinutes: 30, ...person },
  [sensor],
  [{ id: 100, personId: 1, sensorId: 10, detectedAt, detectedValue: '움직임', sensorStatus: 'CONNECTED' }],
  [],
  now,
)

test('3일 동안 움직임이 없으면 정상 상태가 아닌 경고 상태다', () => {
  const dashboard = build('2026-09-11T12:00:00+09:00')

  assert.equal(dashboard.isWarning, true)
  assert.equal(dashboard.warning.title, '장시간 움직임 없음')
  assert.match(dashboard.warning.description, /3일 전/)
})

test('대상자별 미감지 기준을 사용한다', () => {
  const eventAt = '2026-09-14T11:15:00+09:00'

  assert.equal(build(eventAt, { inactivityThresholdMinutes: 60 }).isWarning, false)
  assert.equal(build(eventAt, { inactivityThresholdMinutes: 30 }).isWarning, true)
})

test('오늘 감지 횟수와 전체 기록의 마지막 감지를 구분한다', () => {
  const dashboard = build('2026-09-11T12:00:00+09:00')

  assert.equal(dashboard.events.length, 0)
  assert.equal(dashboard.latestElapsed, '3일 전')
})
