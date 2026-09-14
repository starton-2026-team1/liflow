import { useEffect, useRef, useState } from 'react'
import { ChevronRight, Phone, Radio, ShieldCheck, X } from 'lucide-react'
import personProfileMascot from '../../../assets/mascot-profile.png'
import alertMascot from '../../../assets/mascot/alert.png'
import disconnectedMascot from '../../../assets/mascot/disconnected.png'
import profileMascot from '../../../assets/mascot/normal.png'
import { createHomeDashboard } from '../utils/homeDashboard'
import { WelfareBenefitsCard } from './WelfareBenefits'
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
      <p>{warning ? '리피가 이상 징후를 발견했어요' : '안녕하세요!'}</p>
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
      <img className="home-status-card__mascot" src={profileMascot} alt="정상 상태인 리피" />
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

function WarningStatus({ isConfirmingSafety, model, onConfirmSafety }) {
  const [warningIndex, setWarningIndex] = useState(0)
  const swipeStartX = useRef(null)
  const activeWarningIndex = Math.min(warningIndex, model.warnings.length - 1)
  const warning = model.warnings[activeWarningIndex] || model.warning
  const isSensorDisconnected = warning.sensor?.status === 'disconnected'
  const selectAdjacentWarning = (direction) => {
    setWarningIndex((activeWarningIndex + direction + model.warnings.length) % model.warnings.length)
  }
  const handleSwipeEnd = (clientX) => {
    if (swipeStartX.current === null || model.warnings.length < 2) return
    const distance = clientX - swipeStartX.current
    swipeStartX.current = null
    if (Math.abs(distance) < 45) return
    selectAdjacentWarning(distance < 0 ? 1 : -1)
  }
  const callTarget = () => {
    if (model.person.phone) window.location.href = `tel:${model.person.phone}`
  }

  return (
    <>
      <section
        className="home-status-card home-status-card--warning"
        aria-labelledby="home-warning-title"
        onPointerDown={(event) => {
          if (event.pointerType === 'mouse' && event.button !== 0) return
          swipeStartX.current = event.clientX
          event.currentTarget.setPointerCapture(event.pointerId)
        }}
        onPointerUp={(event) => handleSwipeEnd(event.clientX)}
        onPointerCancel={() => { swipeStartX.current = null }}
      >
        <div>
          <h2 id="home-warning-title">{warning.title}</h2>
          <p>{warning.description}<br />{warning.connectionMessage}</p>
        </div>
        <img
          className="home-status-card__mascot"
          src={isSensorDisconnected ? disconnectedMascot : alertMascot}
          alt={isSensorDisconnected ? '센서 연결 끊김을 알리는 리피' : '주의 상황을 알리는 리피'}
        />
      </section>

      {model.warnings.length > 1 && (
        <div className="home-warning-pagination" aria-label="이상 징후 카드 선택">
          {model.warnings.map((item, index) => (
            <button
              key={item.alert.id}
              type="button"
              className={index === activeWarningIndex ? 'is-active' : ''}
              aria-label={`${index + 1}번째 이상 징후 보기`}
              aria-current={index === activeWarningIndex ? 'true' : undefined}
              onClick={() => setWarningIndex(index)}
            />
          ))}
        </div>
      )}

      <div className="home-warning-actions">
        <button className="primary-action" type="button" onClick={callTarget} disabled={!model.person.phone}>
          <Phone aria-hidden="true" />대상자에게 전화하기
        </button>
        <button
          className="home-safety-confirm-action"
          type="button"
          onClick={() => onConfirmSafety(warning.alert)}
          disabled={isConfirmingSafety}
        >
          <ShieldCheck aria-hidden="true" />{isConfirmingSafety ? '확인 처리 중...' : '안전을 확인했어요'}
        </button>
      </div>

      <section className="home-dashboard__section home-evidence" aria-labelledby="situation-evidence-title">
        <h2 id="situation-evidence-title">상황 근거</h2>
        <article>
          <div className="home-evidence__icon">
            <HomeSensorStatusIcon status={warning.sensor?.status} />
          </div>
          <div>
            <strong>{warning.sensor?.name || '움직임 센서'}</strong>
            <dl>
              <div><dt>마지막 감지</dt><dd>{model.latestTime}</dd></div>
              <div><dt>감지 내용</dt><dd>{warning.evidence}</dd></div>
            </dl>
            <small>AI 판단 신뢰도 높음</small>
          </div>
        </article>
      </section>
    </>
  )
}

export default function HomeDashboard({ alerts, events, isConfirmingSafety, onConfirmSafety, onOpenPerson, onOpenWelfare, person, sensors }) {
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

  const dashboard = createHomeDashboard(person, sensors, events, alerts, now)
  const previewStatus = import.meta.env.DEV
    ? new URLSearchParams(window.location.search).get('preview')
    : null
  const previewWarning = {
    alert: { id: 'preview' },
    sensor: dashboard.latestSensor || dashboard.sensors[0],
    title: '장시간 움직임 없음',
    description: '평소보다 35분간 움직임이 없어요.',
    connectionMessage: '센서 연결 상태는 정상입니다.',
    evidence: dashboard.latestEvent?.detectedValue || '평소 대비 활동량 -42%',
  }
  const previewAnomalies = [
    previewWarning,
    {
      alert: { id: 'preview-repeat', cause: 'REPEATED_ACTIVITY' },
      sensor: dashboard.latestSensor || dashboard.sensors[0],
      title: '평소와 다른 반복 행동',
      description: '짧은 시간 동안 같은 위치의 움직임이 반복됐어요.',
      connectionMessage: '센서 연결 상태는 정상입니다.',
      evidence: '10분 동안 현관 센서 7회 감지',
    },
    {
      alert: { id: 'preview-night', cause: 'UNUSUAL_HOUR' },
      sensor: dashboard.latestSensor || dashboard.sensors[0],
      title: '늦은 시간 활동 감지',
      description: '평소 활동이 드문 시간에 움직임이 감지됐어요.',
      connectionMessage: '센서 연결 상태는 정상입니다.',
      evidence: '오전 2:18 침실 센서 감지',
    },
  ]
  const model = previewStatus === 'warning'
    ? { ...dashboard, isWarning: true, warning: dashboard.warning || previewWarning, warnings: dashboard.warnings.length ? dashboard.warnings : [previewWarning] }
    : previewStatus === 'anomalies'
      ? { ...dashboard, isWarning: true, warning: dashboard.warning || previewWarning, warnings: dashboard.warnings.length ? dashboard.warnings : previewAnomalies }
    : previewStatus === 'normal'
      ? { ...dashboard, isWarning: false, warning: null }
      : dashboard

  return (
    <div className="home-dashboard">
      <DashboardHeader person={person} warning={model.isWarning} />
      <PersonOverview model={model} onOpenPerson={onOpenPerson} />
      {model.isWarning
        ? <WarningStatus isConfirmingSafety={isConfirmingSafety} model={model} onConfirmSafety={onConfirmSafety} />
        : <NormalStatus model={model} />}
      <ActivitySummary model={model} />
      <WelfareBenefitsCard person={person} onClick={onOpenWelfare} />
    </div>
  )
}
