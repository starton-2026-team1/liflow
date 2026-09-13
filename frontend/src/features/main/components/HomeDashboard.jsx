import { useEffect, useState } from 'react'
import { ChevronRight, Phone, Radio, ShieldCheck, X } from 'lucide-react'
import personProfileMascot from '../../../assets/mascot-profile.png'
import alertMascot from '../../../assets/mascot/alert.png'
import disconnectedMascot from '../../../assets/mascot/disconnected.png'
import profileMascot from '../../../assets/mascot/normal.png'
import { createHomeDashboard } from '../utils/homeDashboard'
import '../styles/homeDashboard.css'

const sensorStatusLabels = {
  normal: '정상',
  connecting: '연결 중',
  unstable: '연결 불안정',
  disconnected: '끊김',
}

function HomeSensorStatusIcon({ status }) {
  const resolvedStatus = sensorStatusLabels[status] ? status : 'disconnected'
  const StatusIcon = resolvedStatus === 'disconnected' ? X : Radio

  return (
    <span
      className={`home-sensor-status-icon home-sensor-status-icon--${resolvedStatus}`}
      aria-label={`센서 상태: ${sensorStatusLabels[resolvedStatus]}`}
    >
      <StatusIcon aria-hidden="true" />
    </span>
  )
}

function DashboardHeader({ person, warning }) {
  return (
    <header className={`page-header home-dashboard__header${warning ? ' home-dashboard__header--warning' : ''}`}>
      <p>{warning ? '살핌이가 이상 징후를 발견했어요' : '안녕하세요!'}</p>
      <h1>{warning ? '확인이 필요한 상황이 있어요' : <>{person.name}님의 하루를<br />확인해 보세요</>}</h1>
    </header>
  )
}

function PersonOverview({ model, onOpenPerson }) {
  return (
    <button className="home-dashboard__person" type="button" onClick={onOpenPerson}>
      <span className="home-dashboard__avatar"><img src={personProfileMascot} alt="" /></span>
      <span className="home-dashboard__person-text">
        <strong>{model.person.name} 님</strong>
        <small>모니터링 중 · 센서 {model.sensors.length}개</small>
      </span>
      <ChevronRight aria-hidden="true" />
    </button>
  )
}

function NormalStatus({ model }) {
  return (
    <section className="home-status-card home-status-card--normal" aria-labelledby="home-status-title">
      <div>
        <span>현재 상태</span>
        <h2 id="home-status-title">평소와 비슷해요</h2>
        <p>{model.latestEvent ? `최근 움직임이 ${model.latestElapsed}에 감지됐어요.` : '센서가 정상적으로 연결되어 있어요.'}</p>
      </div>
      <img className="home-status-card__mascot" src={profileMascot} alt="정상 상태인 살핌이" />
    </section>
  )
}

function ActivitySummary({ model }) {
  const activity = model.events.length >= 10 ? '활발' : model.events.length >= 3 ? '보통' : '조용'

  return (
    <>
      <section className="home-dashboard__section" aria-labelledby="today-activity-title">
        <h2 id="today-activity-title">오늘 활동</h2>
        <div className="home-activity-grid">
          <article><strong>{activity}</strong><span>활동량</span></article>
          <article><strong>{model.latestElapsed}</strong><span>마지막 감지</span></article>
          <article><strong>{model.events.length}회</strong><span>오늘 감지</span></article>
        </div>
      </section>

      <section className="home-recent-card" aria-labelledby="recent-record-title">
        <div className="home-recent-card__icon">
          <HomeSensorStatusIcon status={model.latestSensor?.status} />
        </div>
        <div>
          <h2 id="recent-record-title">최근 기록</h2>
          {model.latestEvent ? (
            <><strong>{model.latestTime} {model.latestSensor?.location || '생활공간'} 움직임 감지</strong><span>{model.latestSensor?.name} · {model.latestEvent.detectedValue}</span></>
          ) : <strong>아직 감지 기록이 없어요</strong>}
        </div>
      </section>
    </>
  )
}

function WarningStatus({ model }) {
  const isSensorDisconnected = model.warning.sensor?.status === 'disconnected'
  const callTarget = () => {
    if (model.person.phone) window.location.href = `tel:${model.person.phone}`
  }

  return (
    <>
      <section className="home-status-card home-status-card--warning" aria-labelledby="home-warning-title">
        <div>
          <h2 id="home-warning-title">{model.warning.title}</h2>
          <p>{model.warning.description}<br />{model.warning.connectionMessage}</p>
        </div>
        <img
          className="home-status-card__mascot"
          src={isSensorDisconnected ? disconnectedMascot : alertMascot}
          alt={isSensorDisconnected ? '센서 연결 끊김을 알리는 살핌이' : '주의 상황을 알리는 살핌이'}
        />
      </section>

      <div className="home-warning-actions">
        <button className="primary-action" type="button" onClick={callTarget} disabled={!model.person.phone}>
          <Phone aria-hidden="true" />대상자에게 전화하기
        </button>
        <button className="home-safety-confirm-action" type="button">
          <ShieldCheck aria-hidden="true" />안전을 확인했어요
        </button>
      </div>

      <section className="home-dashboard__section home-evidence" aria-labelledby="situation-evidence-title">
        <h2 id="situation-evidence-title">상황 근거</h2>
        <article>
          <div className="home-evidence__icon">
            <HomeSensorStatusIcon status={model.warning.sensor?.status} />
          </div>
          <div>
            <strong>{model.warning.sensor?.name || '움직임 센서'}</strong>
            <dl>
              <div><dt>마지막 감지</dt><dd>{model.latestTime}</dd></div>
              <div><dt>감지 내용</dt><dd>{model.warning.evidence}</dd></div>
            </dl>
            <small>AI 판단 신뢰도 높음</small>
          </div>
        </article>
      </section>
    </>
  )
}

export default function HomeDashboard({ events, onOpenPerson, person, sensors }) {
  const [now, setNow] = useState(() => new Date())

  useEffect(() => {
    const updateCurrentTime = () => setNow(new Date())
    const timer = window.setInterval(updateCurrentTime, 30_000)
    window.addEventListener('focus', updateCurrentTime)
    document.addEventListener('visibilitychange', updateCurrentTime)

    return () => {
      window.clearInterval(timer)
      window.removeEventListener('focus', updateCurrentTime)
      document.removeEventListener('visibilitychange', updateCurrentTime)
    }
  }, [])

  const dashboard = createHomeDashboard(person, sensors, events, now)
  const previewStatus = import.meta.env.DEV
    ? new URLSearchParams(window.location.search).get('preview')
    : null
  const previewWarning = {
    sensor: dashboard.latestSensor || dashboard.sensors[0],
    title: '장시간 움직임 없음',
    description: '평소보다 35분간 움직임이 없어요.',
    connectionMessage: '센서 연결 상태는 정상입니다.',
    evidence: dashboard.latestEvent?.detectedValue || '평소 대비 활동량 -42%',
  }
  const model = previewStatus === 'warning'
    ? { ...dashboard, isWarning: true, warning: dashboard.warning || previewWarning }
    : previewStatus === 'normal'
      ? { ...dashboard, isWarning: false, warning: null }
      : dashboard

  return (
    <div className="home-dashboard">
      <DashboardHeader person={person} warning={model.isWarning} />
      <PersonOverview model={model} onOpenPerson={onOpenPerson} />
      {model.isWarning
        ? <WarningStatus model={model} />
        : <NormalStatus model={model} />}
      <ActivitySummary model={model} />
    </div>
  )
}
