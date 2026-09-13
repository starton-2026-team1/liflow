const DAY_MS = 24 * 60 * 60 * 1000
const INACTIVITY_MS = 4 * 60 * 60 * 1000

const toDate = (value) => {
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? null : date
}

const startOfDay = (date) => new Date(date.getFullYear(), date.getMonth(), date.getDate())

const formatTime = (date) => new Intl.DateTimeFormat('ko-KR', {
  hour: '2-digit',
  minute: '2-digit',
  hour12: false,
}).format(date)

const formatShortDate = (date) => `${date.getMonth() + 1}.${date.getDate()}`

const formatWeekday = (date) => new Intl.DateTimeFormat('ko-KR', {
  weekday: 'short',
}).format(date).replace('요일', '')

const getDayEvents = (events, day) => events.filter(({ date }) => (
  date >= day && date < new Date(day.getTime() + DAY_MS)
))

const getInactivityCount = (events) => events.reduce((count, event, index) => {
  if (index === 0) return count
  const previous = events[index - 1]
  const isSameDay = startOfDay(previous.date).getTime() === startOfDay(event.date).getTime()
  const isDaytime = previous.date.getHours() >= 6 && event.date.getHours() <= 22
  return count + (isSameDay && isDaytime && event.date - previous.date >= INACTIVITY_MS ? 1 : 0)
}, 0)

const getAverageFirstActivity = (events, days) => {
  const firstActivities = days
    .map((day) => getDayEvents(events, day)[0]?.date)
    .filter(Boolean)

  if (firstActivities.length === 0) return '--:--'
  const averageMinutes = Math.round(firstActivities.reduce((total, date) => (
    total + date.getHours() * 60 + date.getMinutes()
  ), 0) / firstActivities.length)
  const hour = String(Math.floor(averageMinutes / 60)).padStart(2, '0')
  const minute = String(averageMinutes % 60).padStart(2, '0')
  return `${hour}:${minute}`
}

export function createHistoryAnalysis(person, sensors, events, now = new Date()) {
  const linkedSensors = sensors.filter(({ personId }) => person?.id && personId === person.id)
  const linkedSensorIds = new Set(linkedSensors.map(({ id }) => id))
  const personEvents = events
    .map((event) => ({ ...event, date: toDate(event.detectedAt) }))
    .filter((event) => event.date && (
      !person || event.personId === person.id || linkedSensorIds.has(event.sensorId)
    ))
    .sort((a, b) => a.date - b.date)

  const today = startOfDay(now)
  const periodEnd = new Date(today.getTime() - DAY_MS)
  const days = Array.from({ length: 7 }, (_, index) => (
    new Date(periodEnd.getTime() - (6 - index) * DAY_MS)
  ))
  const previousDays = days.map((day) => new Date(day.getTime() - 7 * DAY_MS))
  const counts = days.map((day) => getDayEvents(personEvents, day).length)
  const previousCounts = previousDays.map((day) => getDayEvents(personEvents, day).length)
  const currentTotal = counts.reduce((total, count) => total + count, 0)
  const previousTotal = previousCounts.reduce((total, count) => total + count, 0)
  const changeRate = previousTotal > 0
    ? Math.round(((currentTotal - previousTotal) / previousTotal) * 100)
    : null
  const periodEvents = personEvents.filter(({ date }) => date >= days[0] && date < today)
  const recentEvents = [...personEvents].sort((a, b) => b.date - a.date)

  const changeText = changeRate === null
    ? '비교할 지난주 기록이 없어요'
    : changeRate === 0
      ? '지난주와 활동량이 같아요'
      : `지난주보다 ${Math.abs(changeRate)}% ${changeRate > 0 ? '증가' : '감소'}`
  const summary = currentTotal === 0
    ? '이번 주에는 아직 분석할 활동 기록이 없어요. 센서 기록이 쌓이면 생활 패턴을 알려드릴게요.'
    : changeRate === null
      ? '이번 주 활동 기록을 분석하고 있어요. 데이터가 더 쌓이면 평소 생활 패턴과 비교해드릴게요.'
      : `주간 활동량이 지난주보다 ${changeRate >= 0 ? '늘었어요' : '줄었어요'}. 장시간 미감지는 ${getInactivityCount(periodEvents)}회 확인됐어요.`

  return {
    linkedSensors,
    recentEvents,
    counts,
    dayLabels: days.map(formatWeekday),
    maxCount: Math.max(...counts, 1),
    currentTotal,
    changeText,
    averageFirstActivity: getAverageFirstActivity(personEvents, days),
    inactivityCount: getInactivityCount(periodEvents),
    periodLabel: `${formatShortDate(days[0])} — ${formatShortDate(periodEnd)}`,
    summary,
    formatTime,
  }
}
