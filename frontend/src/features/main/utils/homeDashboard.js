const warningStatuses = new Set(['WARNING', 'ALERT', 'ANOMALY'])
const inactivityLimitMinutes = 30

const toDate = (value) => {
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? null : date
}

const formatTime = (date) => new Intl.DateTimeFormat('ko-KR', {
  hour: '2-digit',
  minute: '2-digit',
  hour12: false,
}).format(date)

const formatElapsed = (date, now) => {
  const elapsedMilliseconds = now.getTime() - date.getTime()
  const isFuture = elapsedMilliseconds < -60_000
  const minutes = Math.floor(Math.abs(elapsedMilliseconds) / 60000)
  if (minutes < 1) return '방금 전'
  const suffix = isFuture ? '후' : '전'
  if (minutes < 60) return `${minutes}분 ${suffix}`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}시간 ${suffix}`
  return `${Math.floor(hours / 24)}일 ${suffix}`
}

const isToday = (date, now) => date
  && date.getTime() <= now.getTime()
  && date.getFullYear() === now.getFullYear()
  && date.getMonth() === now.getMonth()
  && date.getDate() === now.getDate()

export function createHomeDashboard(person, sensors, events, now = new Date()) {
  const linkedSensors = sensors.filter(({ personId }) => personId === person.id)
  const linkedSensorIds = new Set(linkedSensors.map(({ id }) => id))
  const linkedEvents = events
    .filter((event) => event.personId === person.id || linkedSensorIds.has(event.sensorId))
    .sort((a, b) => (toDate(b.detectedAt)?.getTime() || 0) - (toDate(a.detectedAt)?.getTime() || 0))
  const todayEvents = linkedEvents.filter((event) => isToday(toDate(event.detectedAt), now))
  const latestEvent = linkedEvents[0]
  const latestDate = toDate(latestEvent?.detectedAt)
  const latestSensor = linkedSensors.find(({ id }) => id === latestEvent?.sensorId) || linkedSensors[0]
  const disconnectedSensor = linkedSensors.find(({ status }) => status === 'disconnected')
  const warningStatus = warningStatuses.has(latestEvent?.sensorStatus?.toUpperCase())
  const inactiveMinutes = latestDate ? Math.max(0, Math.floor((now.getTime() - latestDate.getTime()) / 60000)) : 0
  const inactiveTooLong = Boolean(latestDate) && inactiveMinutes >= inactivityLimitMinutes
  const isWarning = Boolean(disconnectedSensor || warningStatus || inactiveTooLong)

  return {
    person,
    sensors: linkedSensors,
    events: todayEvents,
    latestEvent,
    latestSensor,
    latestTime: latestDate ? formatTime(latestDate) : '--:--',
    latestElapsed: latestDate ? formatElapsed(latestDate, now) : '기록 없음',
    isWarning,
    warning: isWarning ? {
      sensor: disconnectedSensor || latestSensor,
      title: disconnectedSensor ? '센서 연결 상태 확인' : '장시간 움직임 없음',
      description: disconnectedSensor
        ? `${disconnectedSensor.name}의 연결이 끊겼어요.`
        : `평소보다 ${inactiveMinutes}분간 움직임이 없어요.`,
      connectionMessage: disconnectedSensor ? '센서 연결 상태를 확인해 주세요.' : '센서 연결 상태는 정상입니다.',
      evidence: latestEvent?.detectedValue || '최근 감지 기록 없음',
    } : null,
  }
}
