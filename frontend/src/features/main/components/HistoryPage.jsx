import { useMemo, useState } from 'react'
import { ChevronDown } from 'lucide-react'
import { createHistoryAnalysis } from '../utils/historyAnalysis'
import '../styles/history.css'

const getSensorLabel = (sensor, event) => sensor?.name || `센서 ${event.sensorId}`

const getEventTitle = (sensor, event) => {
  const value = event.detectedValue?.trim()
  if (value && !/^\d+(\.\d+)?$/.test(value)) return value
  return `${sensor?.targetObject || sensor?.name || '센서'} 움직임 감지`
}

const deduplicateEventsByMinute = (events) => {
  const seenMinutes = new Set()

  return events.filter((event) => {
    if (!event.date) return true

    const minute = Math.floor(event.date.getTime() / 60000)
    if (seenMinutes.has(minute)) return false

    seenMinutes.add(minute)
    return true
  })
}

function PersonSelector({ people, personId, onChange }) {
  if (people.length <= 1) return <span className="history-person-name">{people[0]?.name || '대상자'} 님</span>

  return (
    <label className="history-person-selector">
      <span className="visually-hidden">대상자 선택</span>
      <select value={personId} onChange={(event) => onChange(Number(event.target.value))}>
        {people.map((person) => <option key={person.id} value={person.id}>{person.name} 님</option>)}
      </select>
      <ChevronDown aria-hidden="true" />
    </label>
  )
}

function ActivityChart({ counts, dayLabels, maxCount }) {
  return (
    <div className="activity-chart" role="img" aria-label={`최근 7일 활동량: ${counts.join(', ')}`}>
      <div className="activity-chart__grid" aria-hidden="true">
        <span /><span /><span /><span />
      </div>
      <div className="activity-chart__bars">
        {counts.map((count, index) => (
          <div className="activity-chart__column" key={`${dayLabels[index]}-${count}`}>
            <div className="activity-chart__track">
              <span style={{ height: `${Math.max(count ? 12 : 2, (count / maxCount) * 100)}%` }} />
            </div>
            <small>{dayLabels[index]}</small>
          </div>
        ))}
      </div>
    </div>
  )
}

function EventRows({ events, sensors, limit, showEmpty = true }) {
  const visibleEvents = typeof limit === 'number' ? events.slice(0, limit) : events

  if (visibleEvents.length === 0) {
    return showEmpty ? <p className="history-empty-copy">아직 센서 기록이 없어요.</p> : null
  }

  return (
    <div className="history-event-list">
      {visibleEvents.map((event) => {
        const sensor = sensors.find(({ id }) => id === event.sensorId)
        return (
          <article className="history-event-row" key={event.id}>
            <time dateTime={event.detectedAt}>{event.date ? new Intl.DateTimeFormat('ko-KR', { hour: '2-digit', minute: '2-digit', hour12: false }).format(event.date) : '--:--'}</time>
            <div>
              <strong>{getEventTitle(sensor, event)}</strong>
              <span>{sensor?.location || getSensorLabel(sensor, event)}</span>
            </div>
          </article>
        )
      })}
    </div>
  )
}

export default function HistoryPage({ events, initialTab = 'analysis', people, sensors }) {
  const [activeTab, setActiveTab] = useState(initialTab)
  const [personId, setPersonId] = useState(people[0]?.id || '')
  const [sensorFilter, setSensorFilter] = useState('all')
  const selectedPerson = people.find(({ id }) => id === personId) || people[0]
  const analysis = useMemo(
    () => createHistoryAnalysis(selectedPerson, sensors, events),
    [selectedPerson, sensors, events],
  )
  const recentEvents = useMemo(
    () => deduplicateEventsByMinute(analysis.recentEvents),
    [analysis.recentEvents],
  )
  const filteredEvents = useMemo(() => deduplicateEventsByMinute(
    sensorFilter === 'all'
      ? analysis.recentEvents
      : analysis.recentEvents.filter(({ sensorId }) => sensorId === sensorFilter),
  ), [analysis.recentEvents, sensorFilter])

  return (
    <div className="history-view">
      <header className="history-header">
        <h1>기록</h1>
        <PersonSelector people={people} personId={selectedPerson?.id || ''} onChange={setPersonId} />
      </header>

      <div className="history-tabs" role="tablist" aria-label="기록 보기">
        <button type="button" role="tab" aria-selected={activeTab === 'records'} onClick={() => setActiveTab('records')}>센서 기록</button>
        <button type="button" role="tab" aria-selected={activeTab === 'analysis'} onClick={() => setActiveTab('analysis')}>생활 분석</button>
      </div>

      {activeTab === 'analysis' ? (
        <div className="history-analysis" role="tabpanel">
          <div className="history-period">
            <span>최근 7일 <ChevronDown aria-hidden="true" /></span>
            <time>{analysis.periodLabel}</time>
          </div>

          <section className="analysis-section">
            <div className="analysis-section__heading">
              <h2>활동량 변화</h2>
              <span>{analysis.changeText}</span>
            </div>
            <ActivityChart counts={analysis.counts} dayLabels={analysis.dayLabels} maxCount={analysis.maxCount} />
          </section>

          <section className="analysis-section">
            <h2>핵심 지표</h2>
            <div className="history-metrics">
              <div><span>평균 첫 활동</span><strong>{analysis.averageFirstActivity}</strong></div>
              <div><span>장시간 미감지</span><strong>{analysis.inactivityCount}회</strong></div>
            </div>
          </section>

          <section className="analysis-section">
            <h2>AI 요약</h2>
            <div className="history-ai-summary">
              {analysis.summary.match(/[^.?!]+[.?!]?/g)?.map((sentence) => (
                <p key={sentence}>{sentence.trim()}</p>
              ))}
            </div>
          </section>

          <section className="analysis-section analysis-section--recent">
            <div className="analysis-section__heading">
              <h2>최근 기록</h2>
              <button type="button" onClick={() => setActiveTab('records')}>전체보기</button>
            </div>
            <EventRows events={recentEvents} sensors={sensors} limit={2} />
          </section>
        </div>
      ) : (
        <div className="history-records" role="tabpanel">
          <div className="history-filter-list" aria-label="센서 필터">
            <button type="button" className={sensorFilter === 'all' ? 'is-active' : ''} onClick={() => setSensorFilter('all')}>전체</button>
            {analysis.linkedSensors.map((sensor) => (
              <button type="button" className={sensorFilter === sensor.id ? 'is-active' : ''} key={sensor.id} onClick={() => setSensorFilter(sensor.id)}>{sensor.name}</button>
            ))}
          </div>
          <p className="history-record-count">센서 활동 {filteredEvents.length}건</p>
          <EventRows events={filteredEvents} sensors={sensors} showEmpty={false} />
        </div>
      )}
    </div>
  )
}
