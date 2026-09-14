import test from 'node:test'
import assert from 'node:assert/strict'

import { createHomeDashboard } from '../src/features/main/utils/homeDashboard.js'

const now = new Date('2026-09-14T12:00:00+09:00')
const sensor = { id: 10, personId: 1, name: '거실센서', location: '거실', status: 'normal' }

const build = (detectedAt, person = {}, alerts = []) => createHomeDashboard(
  { id: 1, inactivityThresholdMinutes: 30, ...person },
  [sensor],
  [{ id: 100, personId: 1, sensorId: 10, detectedAt, detectedValue: '움직임', sensorStatus: 'CONNECTED' }],
  alerts,
  now,
)

test('서버에서 생성된 미확인 알림을 경고 상태로 표시한다', () => {
  const alert = {
    id: 200,
    personId: 1,
    sensorId: 10,
    title: '장시간 움직임 없음',
    description: '3일 전부터 움직임이 감지되지 않았어요.',
    occurredAt: '2026-09-14T11:30:00+09:00',
  }
  const dashboard = build('2026-09-11T12:00:00+09:00', {}, [alert])

  assert.equal(dashboard.isWarning, true)
  assert.equal(dashboard.warning.title, '장시간 움직임 없음')
  assert.match(dashboard.warning.description, /3일 전/)
})

test('안전을 확인한 알림은 경고 상태에서 제외한다', () => {
  const confirmedAlert = {
    id: 201,
    personId: 1,
    sensorId: 10,
    title: '장시간 움직임 없음',
    description: '움직임이 감지되지 않았어요.',
    occurredAt: '2026-09-14T11:30:00+09:00',
    safetyConfirmedAt: '2026-09-14T11:45:00+09:00',
  }

  assert.equal(build('2026-09-14T11:15:00+09:00', {}, [confirmedAlert]).isWarning, false)
})

test('오늘 감지 횟수와 전체 기록의 마지막 감지를 구분한다', () => {
  const dashboard = build('2026-09-11T12:00:00+09:00')

  assert.equal(dashboard.events.length, 0)
  assert.equal(dashboard.latestElapsed, '3일 전')
})
