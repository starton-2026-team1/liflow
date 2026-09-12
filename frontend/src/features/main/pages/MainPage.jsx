import { useEffect, useState } from 'react'
import {
  Activity,
  Check,
  ChevronDown,
  ChevronRight,
  FileClock,
  Home,
  Info,
  LogOut,
  MoreVertical,
  Plus,
  Radio,
  Settings,
  UsersRound,
  X,
} from 'lucide-react'
import { createPerson, deletePerson, getPeople, updatePerson, updatePersonMonitoringStatus } from '../../../api/people'
import { connectSensorEventStream } from '../../../api/realtimeEvents'
import { getSensorEvents } from '../../../api/sensorEvents'
import { connectSensor, createSensor, deleteSensor, disconnectSensor, getSensors, updateSensor } from '../../../api/sensors'
import mascot from '../../../assets/mascot.png'
import personProfileMascot from '../../../assets/mascot-profile.png'
import emptyMascot from '../../../assets/mascot/empty.png'
import NoticeToast from '../../../components/common/NoticeToast'
import ConfirmDialog from '../../../components/common/ConfirmDialog'
import DetailActionButtons from '../../../components/common/DetailActionButtons'
import BackButton from '../../../components/common/BackButton'
import StepFormLayout from '../../../components/common/StepFormLayout'
import UnderlinedInput from '../../../components/common/UnderlinedInput'
import PersonRegistrationPage from '../../people/pages/PersonRegistrationPage'
import SensorRegistrationPage from '../../sensor/pages/SensorRegistrationPage'
import HomeDashboard from '../components/HomeDashboard'
import HistoryPage from '../components/HistoryPage'
import '../styles/main.css'

const navigationItems = [
  { id: 'home', label: '홈', icon: Home },
  { id: 'people', label: '대상자', icon: UsersRound },
  { id: 'sensor', label: '센서', icon: Activity },
  { id: 'history', label: '기록', icon: FileClock },
  { id: 'profile', label: '설정', icon: Settings },
]

const profileSections = [
  { title: '계정', items: ['내 정보 수정'] },
  { title: '환경설정', items: ['알림 설정', '접근성 설정', '테마 설정'] },
  { title: '기기 및 안전', items: ['안심태그(NFC)'] },
  { title: '지원', items: ['도움말', '이용약관 및 개인정보 처리방침'] },
]

const mergeSensorEvents = (...eventGroups) => {
  const eventsById = new Map()
  eventGroups.flat().forEach((event) => eventsById.set(event.id, event))
  return [...eventsById.values()].sort(
    (left, right) => new Date(right.detectedAt) - new Date(left.detectedAt),
  )
}

function EmptyState({ actionLabel, description, onAction, title }) {
  return (
    <div className="empty-state">
      <div className="empty-state__image-wrap">
        <img src={emptyMascot} alt="기다리고 있는 캐릭터" />
      </div>
      <h2>{title}</h2>
      {description && <p>{description}</p>}
      {actionLabel && (
        <button className="primary-action" type="button" onClick={onAction}>
          <Plus aria-hidden="true" />
          {actionLabel}
        </button>
      )}
    </div>
  )
}

function HomePage({ hasSensor, onAddPerson, onConnectSensor, onStartRecording, person }) {
  const hasPerson = Boolean(person)

  return (
    <div className="home-view">
      <header className="page-header home-view__header">
        <p>안녕하세요!</p>
        <h1>
          {hasSensor ? `${person.name}님의 오늘을` : hasPerson ? `${person.name}님의 모니터링을` : '안심 모니터링을'}
          <br />
          {hasSensor ? '확인해 볼까요?' : hasPerson ? '준비해 볼까요?' : '시작해 볼까요?'}
        </h1>
      </header>

      <section className="onboarding-card" aria-labelledby="onboarding-title">
        <div className="onboarding-card__illustration">
          <img src={mascot} alt="손을 흔드는 살핌이 캐릭터" />
        </div>
        <h2 id="onboarding-title">
          {hasSensor ? '모니터링 준비가 완료됐어요' : hasPerson ? '이제 센서를 연결해 주세요' : '먼저 대상자를 등록해 주세요'}
        </h2>
        <p className="onboarding-card__description">
          {hasSensor
            ? '센서 기록과 이상 징후를 확인할 수 있어요.'
            : hasPerson
            ? '생활공간에 센서를 연결하면 모니터링을 시작할 수 있어요.'
            : '가족을 등록한 다음 센서를 연결할 수 있어요.'}
        </p>

        <ol className="onboarding-progress" aria-label="모니터링 시작 단계">
          <li className={`onboarding-progress__item${hasPerson ? ' onboarding-progress__item--complete' : ' onboarding-progress__item--active'}`}>
            <span>1</span>
            <strong>대상자 등록</strong>
          </li>
          <li className={`onboarding-progress__line${hasPerson ? ' onboarding-progress__line--complete' : ''}`} aria-hidden="true" />
          <li className={`onboarding-progress__item${hasSensor ? ' onboarding-progress__item--complete' : hasPerson ? ' onboarding-progress__item--active' : ''}`}>
            <span>2</span>
            <strong>센서 연결</strong>
          </li>
          <li className={`onboarding-progress__line${hasSensor ? ' onboarding-progress__line--complete' : ''}`} aria-hidden="true" />
          <li className={`onboarding-progress__item${hasSensor ? ' onboarding-progress__item--active' : ''}`}>
            <span>3</span>
            <strong>준비 완료</strong>
          </li>
        </ol>

        <button
          className="primary-action primary-action--wide"
          type="button"
          onClick={hasSensor ? onStartRecording : hasPerson ? onConnectSensor : onAddPerson}
        >
          {hasSensor ? '기록 시작하기' : hasPerson ? '센서 연결하기' : '대상자 등록하기'}
          <ChevronRight aria-hidden="true" />
        </button>
      </section>
    </div>
  )
}

function ProfilePage({ onLogout, onThemeChange, onUserUpdate, theme, user }) {
  const [showThemeDialog, setShowThemeDialog] = useState(false)
  const [isEditing, setIsEditing] = useState(false)
  const [editMode, setEditMode] = useState('menu')
  const [email, setEmail] = useState(user?.email || '')
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [error, setError] = useState('')
  const [isSaving, setIsSaving] = useState(false)
  const themeOptions = [
    { id: 'inverted', label: '반전', description: '회색 배경 · 흰색 카드' },
    { id: 'classic', label: '기본', description: '흰색 배경 · 회색 카드' },
  ]

  const resetForm = () => {
    setEmail(user?.email || '')
    setCurrentPassword('')
    setNewPassword('')
    setError('')
    setEditMode('menu')
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')

    const normalizedEmail = email.trim()
    if (editMode === 'email' && !normalizedEmail) {
      setError('바꿀 이메일을 입력해 주세요.')
      return
    }

    const emailChanged = editMode === 'email' && normalizedEmail !== user?.email
    if (!currentPassword) {
      setError('현재 비밀번호를 입력해 주세요.')
      return
    }
    if (newPassword && newPassword.length < 8) {
      setError('새 비밀번호는 8자 이상 입력해 주세요.')
      return
    }
    if (editMode === 'email' && !emailChanged) {
      setError('변경할 이메일을 입력해 주세요.')
      return
    }
    if (editMode === 'password' && !newPassword) {
      setError('새 비밀번호를 입력해 주세요.')
      return
    }

    setIsSaving(true)
    try {
      await onUserUpdate({
        current_password: currentPassword,
        ...(emailChanged ? { email: normalizedEmail } : {}),
        ...(newPassword ? { new_password: newPassword } : {}),
      })
      setCurrentPassword('')
      setNewPassword('')
      setEditMode('menu')
      setIsEditing(false)
    } catch (requestError) {
      setError(requestError.message || '내 정보를 수정하지 못했어요.')
    } finally {
      setIsSaving(false)
    }
  }

  if (isEditing) {
    if (editMode === 'menu') {
      return (
        <div className="profile-edit-menu">
          <header className="profile-edit-menu__header">
            <BackButton onClick={() => { resetForm(); setIsEditing(false) }} />
          </header>

          <section className="settings-section profile-edit-menu__section" aria-labelledby="profile-edit-menu-title">
            <h2 id="profile-edit-menu-title">계정 정보</h2>
            <div className="settings-list">
              <button type="button" onClick={() => { setEditMode('email'); setError('') }}>
                <span className="settings-list__label">이메일 변경</span>
                <ChevronRight aria-hidden="true" />
              </button>
              <button type="button" onClick={() => { setEditMode('password'); setError('') }}>
                <span className="settings-list__label">비밀번호 변경</span>
                <ChevronRight aria-hidden="true" />
              </button>
            </div>
          </section>
        </div>
      )
    }

    return (
      <div className="profile-edit-flow">
        <StepFormLayout
          ariaLabel="내 정보 수정"
          currentStep={0}
          totalSteps={1}
          onBack={() => {
            setCurrentPassword('')
            setNewPassword('')
            setError('')
            setEditMode('menu')
          }}
          onSubmit={handleSubmit}
          actionDisabled={isSaving}
          actionLabel={isSaving ? '저장 중...' : '변경사항 저장'}
        >
          {editMode === 'email' ? (
            <>
              <p className="profile-edit-flow__eyebrow">이메일 변경</p>
              <h1 className="step-form-question">바꿀 이메일을<br />입력해 주세요.</h1>
              <p className="step-form-description">안전한 정보 변경을 위해 현재 비밀번호도 입력해 주세요.</p>
              <div className="profile-edit-flow__passwords">
                <UnderlinedInput
                  id="profile-email"
                  type="email"
                  value={email}
                  placeholder="바꿀 이메일"
                  autoComplete="email"
                  autoFocus
                  onChange={(event) => { setEmail(event.target.value); setError('') }}
                  action={email.trim() ? <Check className="input-check" aria-label="입력 완료" /> : null}
                />
                <UnderlinedInput
                  id="profile-email-current-password"
                  type="password"
                  value={currentPassword}
                  placeholder="현재 비밀번호"
                  autoComplete="current-password"
                  onChange={(event) => { setCurrentPassword(event.target.value); setError('') }}
                />
              </div>
              {error && <p className="step-form-server-error" role="alert">{error}</p>}
            </>
          ) : (
            <>
              <p className="profile-edit-flow__eyebrow">비밀번호 변경</p>
              <h1 className="step-form-question">새 비밀번호를<br />설정해 주세요.</h1>
              <p className="step-form-description">안전한 정보 변경을 위해 현재 비밀번호가 필요해요.</p>
              <div className="profile-edit-flow__passwords">
                <UnderlinedInput
                  id="profile-current-password"
                  type="password"
                  value={currentPassword}
                  placeholder="현재 비밀번호"
                  autoComplete="current-password"
                  autoFocus
                  onChange={(event) => { setCurrentPassword(event.target.value); setError('') }}
                />
                <UnderlinedInput
                  id="profile-new-password"
                  type="password"
                  value={newPassword}
                  placeholder="새 비밀번호 (8자 이상)"
                  autoComplete="new-password"
                  minLength="8"
                  onChange={(event) => { setNewPassword(event.target.value); setError('') }}
                />
              </div>
              {error && <p className="step-form-server-error" role="alert">{error}</p>}
            </>
          )}
        </StepFormLayout>
      </div>
    )
  }

  return (
    <div className="profile-view">
      <header className="page-header">
        <h1>설정</h1>
      </header>

      <button className="profile-card" type="button" onClick={() => setIsEditing(true)} aria-label="내 정보 수정">
        <div className="profile-card__avatar"><img src={mascot} alt="" /></div>
        <div><strong>사용자</strong><span>{user?.email || '계정 정보를 확인해 주세요'}</span></div>
        <ChevronRight aria-hidden="true" />
      </button>

      <div className="settings-sections">
        {profileSections.map(({ title, items }) => (
          <section className="settings-section" aria-labelledby={`settings-${title}`} key={title}>
            <h2 id={`settings-${title}`}>{title}</h2>
            <div className="settings-list">
              {items.map((label) => (
                <button
                  key={label}
                  type="button"
                  onClick={() => {
                    if (label === '테마 설정') setShowThemeDialog(true)
                    if (label === '내 정보 수정') setIsEditing(true)
                  }}
                >
                  <span className="settings-list__label">
                    {label}
                  </span>
                  <ChevronRight aria-hidden="true" />
                </button>
              ))}
            </div>
          </section>
        ))}
      </div>

      <button className="logout-button" type="button" onClick={onLogout}>
        <LogOut aria-hidden="true" />
        로그아웃
      </button>
      <p className="app-version"><Info aria-hidden="true" /> 앱 버전 1.0.0</p>
      {showThemeDialog && (
        <div className="theme-dialog-backdrop" role="presentation" onMouseDown={() => setShowThemeDialog(false)}>
          <section className="theme-dialog" role="dialog" aria-modal="true" aria-labelledby="theme-dialog-title" onMouseDown={(event) => event.stopPropagation()}>
            <h2 id="theme-dialog-title">테마 설정</h2>
            <div className="theme-dialog__options">
              {themeOptions.map((option) => (
                <button className={theme === option.id ? 'is-selected' : ''} type="button" key={option.id} onClick={() => { onThemeChange(option.id); setShowThemeDialog(false) }}>
                  <span><strong>{option.label}</strong><small>{option.description}</small></span>
                  {theme === option.id && <Check aria-label="선택됨" />}
                </button>
              ))}
            </div>
            <button className="theme-dialog__cancel" type="button" onClick={() => setShowThemeDialog(false)}>취소</button>
          </section>
        </div>
      )}
    </div>
  )
}

function PersonCard({ defaultExpanded, isUpdating, onConnectSensor, onEdit, onStopMonitoring, person, sensorCount }) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded)

  return (
    <article className={`person-accordion${isExpanded ? ' person-accordion--expanded' : ''}`}>
      <button
        className="person-summary"
        type="button"
        aria-expanded={isExpanded}
        onClick={() => setIsExpanded((expanded) => !expanded)}
      >
        <span className="person-summary__avatar">
          <img src={personProfileMascot} alt="" />
        </span>
        <span className="person-summary__identity">
          <strong>{person.name}</strong>
          <small>{person.ageGroup || '-'} · {person.livingSpace}</small>
        </span>
        <ChevronDown className="person-summary__chevron" aria-hidden="true" />
      </button>

      {isExpanded && (
        <>
          <div className="person-accordion__content">
            <section className="person-detail-section" aria-label={`${person.name} 기본 정보`}>
              <h3>기본 정보</h3>
              <dl className="person-details">
                <div><dt>연령대</dt><dd>{person.ageGroup || '-'}</dd></div>
                <div><dt>연락처</dt><dd>{person.phone || '-'}</dd></div>
                <div><dt>생활공간</dt><dd>{person.livingSpace}</dd></div>
              </dl>
            </section>

            {person.healthNotes?.trim() && (
              <section className="person-notes-section" aria-label={`${person.name} 건강 및 거동 참고사항`}>
                <h3>건강·거동 참고사항</h3>
                <p>{person.healthNotes}</p>
              </section>
            )}

            <button className="person-sensor-link" type="button" onClick={onConnectSensor}>
              <span>연결된 센서</span>
              <strong>{sensorCount > 0 ? `${sensorCount}개` : '연결하기'}</strong>
              <ChevronRight aria-hidden="true" />
            </button>
          </div>
          <DetailActionButtons
            primaryLabel="정보수정/삭제"
            onPrimary={onEdit}
            secondaryLabel={isUpdating ? '중지 중...' : '모니터링 중지'}
            onSecondary={onStopMonitoring}
            secondaryDisabled={isUpdating || person.monitoringStatus !== 'ACTIVE'}
          />
        </>
      )}
    </article>
  )
}

function PeoplePage({ people, onConnectSensor, onEditPerson, onStopMonitoring, sensors, updatingPersonId }) {
  const [showLimitNotice, setShowLimitNotice] = useState(false)

  useEffect(() => {
    if (!showLimitNotice) return undefined
    const timer = window.setTimeout(() => setShowLimitNotice(false), 2400)
    return () => window.clearTimeout(timer)
  }, [showLimitNotice])

  return (
    <div className="people-view">
      <header className="page-header people-view__header">
        <h1>대상자</h1>
        <button type="button" aria-label="대상자 추가" onClick={() => setShowLimitNotice(true)}>
          <Plus aria-hidden="true" />
        </button>
      </header>

      <div className="people-list">
        {people.map((person, index) => (
          <PersonCard
            key={person.id}
            person={person}
            defaultExpanded={index === 0}
            onConnectSensor={onConnectSensor}
            onEdit={() => onEditPerson(person)}
            onStopMonitoring={() => onStopMonitoring(person)}
            isUpdating={updatingPersonId === person.id}
            sensorCount={sensors.filter(({ personId }) => personId === person.id).length}
          />
        ))}
      </div>
      {showLimitNotice && <NoticeToast>현재 대상자는 1명만 등록할 수 있어요.</NoticeToast>}
    </div>
  )
}

const sensorStatusLabels = {
  normal: '정상',
  connecting: '연결 중',
  unstable: '연결 불안정',
  disconnected: '끊김',
}

const sensorStatusGuide = [
  { status: 'normal', label: '정상' },
  { status: 'connecting', label: '연결 중' },
  { status: 'unstable', label: '연결 불안정' },
  { status: 'disconnected', label: '끊김' },
]

function SensorStatusIcon({ status, showLabel = false }) {
  const resolvedStatus = sensorStatusLabels[status] ? status : 'disconnected'
  const label = sensorStatusLabels[resolvedStatus]
  const StatusIcon = resolvedStatus === 'disconnected' ? X : Radio

  return (
    <span
      className={`sensor-status-icon sensor-status-icon--${resolvedStatus}${showLabel ? ' sensor-status-icon--labeled' : ''}`}
      aria-label={showLabel ? undefined : label}
    >
      <StatusIcon aria-hidden="true" />
      {showLabel && <span>{label}</span>}
    </span>
  )
}

function SensorPage({ onAddSensor, onDeleteSensor, onEditSensor, onToggleConnection, people, sensors, updatingConnectionSensorId }) {
  const [openMenuId, setOpenMenuId] = useState(null)

  const closeMenu = (event) => {
    if (!event.currentTarget.contains(event.relatedTarget)) setOpenMenuId(null)
  }

  return (
    <div className="sensors-view">
      <header className="page-header sensors-view__header">
        <div>
          <h1>센서</h1>
          <p>연결된 센서 {sensors.length}개</p>
        </div>
        <button type="button" aria-label="센서 추가" onClick={onAddSensor}>
          <Plus aria-hidden="true" />
        </button>
      </header>

      <div className="sensor-list">
        {sensors.map((sensor) => {
          const person = people.find(({ id }) => id === sensor.personId)
          return (
            <article className="sensor-card" key={sensor.id}>
              <div className="sensor-card__icon">
                <SensorStatusIcon status={sensor.status} />
              </div>
              <div className="sensor-card__heading">
                <h2>{sensor.name}</h2>
                <p>{person?.name} · {sensor.location} · {sensor.targetObject}</p>
              </div>
              <div className="sensor-card__actions" onBlur={closeMenu}>
                <button
                  className="sensor-card__menu-button"
                  type="button"
                  aria-label={`${sensor.name} 관리 메뉴`}
                  aria-haspopup="menu"
                  aria-expanded={openMenuId === sensor.id}
                  onClick={() => setOpenMenuId((id) => id === sensor.id ? null : sensor.id)}
                >
                  <MoreVertical aria-hidden="true" />
                </button>
                {openMenuId === sensor.id && (
                  <div className="sensor-card__menu" role="menu">
                    <button
                      type="button"
                      role="menuitem"
                      onClick={() => {
                        setOpenMenuId(null)
                        onEditSensor(sensor)
                      }}
                    >센서 수정</button>
                    <button
                      type="button"
                      role="menuitem"
                      disabled={updatingConnectionSensorId === sensor.id}
                      onClick={() => {
                        setOpenMenuId(null)
                        onToggleConnection(sensor)
                      }}
                    >{updatingConnectionSensorId === sensor.id
                      ? sensor.status === 'disconnected' ? '연결 중...' : '연결 해제 중...'
                      : sensor.status === 'disconnected' ? '다시 연결' : '연결 해제'}</button>
                    <button
                      className="sensor-card__menu-danger"
                      type="button"
                      role="menuitem"
                      onClick={() => {
                        setOpenMenuId(null)
                        onDeleteSensor(sensor)
                      }}
                    >센서 삭제</button>
                  </div>
                )}
              </div>
            </article>
          )
        })}
      </div>
      <section className="sensor-status-guide" aria-labelledby="sensor-status-guide-title">
        <h2 id="sensor-status-guide-title">센서 연결 상태</h2>
        <div>
          {sensorStatusGuide.map(({ status }) => (
            <SensorStatusIcon status={status} showLabel key={status} />
          ))}
        </div>
      </section>
    </div>
  )
}

function MainPage({ onLogout, onUserUpdate, user }) {
  const [theme, setTheme] = useState(() => window.localStorage.getItem('app-theme') || 'inverted')
  const [activePage, setActivePage] = useState('home')
  const [historyInitialTab, setHistoryInitialTab] = useState('analysis')
  const [isRegisteringPerson, setIsRegisteringPerson] = useState(false)
  const [isRegisteringSensor, setIsRegisteringSensor] = useState(false)
  const [editingPerson, setEditingPerson] = useState(null)
  const [editingSensor, setEditingSensor] = useState(null)
  const [updatingPersonId, setUpdatingPersonId] = useState(null)
  const [registeredPeople, setRegisteredPeople] = useState([])
  const [registeredSensors, setRegisteredSensors] = useState([])
  const [sensorEvents, setSensorEvents] = useState([])
  const [sensorToDelete, setSensorToDelete] = useState(null)
  const [isDeletingSensor, setIsDeletingSensor] = useState(false)
  const [updatingConnectionSensorId, setUpdatingConnectionSensorId] = useState(null)
  const [personToStopMonitoring, setPersonToStopMonitoring] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [apiError, setApiError] = useState('')
  const activeItem = navigationItems.find(({ id }) => id === activePage)
  const primaryPerson = registeredPeople[0]
  const hasLinkedSensor = Boolean(primaryPerson) && registeredSensors.some(
    ({ personId }) => personId === primaryPerson.id,
  )
  const isRecordingStarted = primaryPerson?.monitoringStatus === 'ACTIVE'

  useEffect(() => {
    let isActive = true

    Promise.all([getPeople(), getSensors(), getSensorEvents()])
      .then(([people, sensors, events]) => {
        if (!isActive) return
        setRegisteredPeople(people)
        setRegisteredSensors(sensors)
        setSensorEvents((currentEvents) => mergeSensorEvents(events, currentEvents))
      })
      .catch((error) => {
        if (isActive) setApiError(error.message || '데이터를 불러오지 못했어요.')
      })
      .finally(() => {
        if (isActive) setIsLoading(false)
      })

    return () => { isActive = false }
  }, [])

  useEffect(() => connectSensorEventStream({
    onEvent: (event) => {
      setSensorEvents((events) => mergeSensorEvents(event, events))
    },
    onFatalError: (error) => {
      setApiError(error.message || '실시간 연결을 시작하지 못했어요.')
    },
  }), [])

  useEffect(() => {
    document.documentElement.dataset.appTheme = theme
    window.localStorage.setItem('app-theme', theme)
  }, [theme])

  useEffect(() => {
    if (!apiError) return undefined
    const timer = window.setTimeout(() => setApiError(''), 3000)
    return () => window.clearTimeout(timer)
  }, [apiError])

  const startRecording = async () => {
    try {
      const updatedPerson = await updatePersonMonitoringStatus(primaryPerson.id, 'ACTIVE')
      setRegisteredPeople((people) => people.map((person) => (
        person.id === updatedPerson.id ? updatedPerson : person
      )))
    } catch (error) {
      setApiError(error.message || '모니터링을 시작하지 못했어요.')
    }
  }

  const stopMonitoring = async (person) => {
    setUpdatingPersonId(person.id)
    try {
      const updatedPerson = await updatePersonMonitoringStatus(person.id, 'PAUSED')
      setRegisteredPeople((people) => people.map((item) => (
        item.id === updatedPerson.id ? updatedPerson : item
      )))
    } catch (error) {
      setApiError(error.message || '모니터링을 중지하지 못했어요.')
    } finally {
      setUpdatingPersonId(null)
      setPersonToStopMonitoring(null)
    }
  }

  const confirmSensorDeletion = async () => {
    if (!sensorToDelete) return
    setIsDeletingSensor(true)
    try {
      await deleteSensor(sensorToDelete.id)
      setRegisteredSensors((sensors) => sensors.filter(({ id }) => id !== sensorToDelete.id))
      setSensorToDelete(null)
    } catch (error) {
      setApiError(error.message || '센서를 삭제하지 못했어요.')
    } finally {
      setIsDeletingSensor(false)
    }
  }

  const toggleSensorConnection = async (sensor) => {
    setUpdatingConnectionSensorId(sensor.id)
    try {
      const updated = sensor.status === 'disconnected'
        ? await connectSensor(sensor.id)
        : await disconnectSensor(sensor.id)
      setRegisteredSensors((sensors) => sensors.map((item) => (
        item.id === updated.id ? updated : item
      )))
    } catch (error) {
      setApiError(error.message || `센서를 ${sensor.status === 'disconnected' ? '다시 연결' : '연결 해제'}하지 못했어요.`)
    } finally {
      setUpdatingConnectionSensorId(null)
    }
  }

  const renderPage = () => {
    if (isLoading) {
      return <EmptyState title="정보를 불러오고 있어요" description="잠시만 기다려 주세요." />
    }

    if (activePage === 'home') {
      if (isRecordingStarted) {
        return (
          <HomeDashboard
            person={primaryPerson}
            sensors={registeredSensors}
            events={sensorEvents}
            onOpenPerson={() => setActivePage('people')}
          />
        )
      }

      return (
        <HomePage
          person={primaryPerson}
          hasSensor={hasLinkedSensor}
          onAddPerson={() => setIsRegisteringPerson(true)}
          onConnectSensor={() => setActivePage('sensor')}
          onStartRecording={startRecording}
        />
      )
    }

    if (activePage === 'people') {
      if (registeredPeople.length > 0) {
        return (
          <PeoplePage
            people={registeredPeople}
            sensors={registeredSensors}
            onConnectSensor={() => setActivePage('sensor')}
            onEditPerson={setEditingPerson}
            onStopMonitoring={setPersonToStopMonitoring}
            updatingPersonId={updatingPersonId}
          />
        )
      }

      return (
        <EmptyState
          title="등록된 대상자가 없어요"
          description="돌봄이 필요한 가족을 등록해 주세요."
          actionLabel="대상자 등록하기"
          onAction={() => setIsRegisteringPerson(true)}
        />
      )
    }

    if (activePage === 'sensor') {
      if (registeredSensors.length > 0) {
        return (
          <SensorPage
            sensors={registeredSensors}
            people={registeredPeople}
            onAddSensor={() => setIsRegisteringSensor(true)}
            onDeleteSensor={setSensorToDelete}
            onEditSensor={setEditingSensor}
            onToggleConnection={toggleSensorConnection}
            updatingConnectionSensorId={updatingConnectionSensorId}
          />
        )
      }

      if (registeredPeople.length > 0) {
        return (
          <EmptyState
            title="연결된 센서가 없어요"
            description={`${registeredPeople[0].name}님의 생활공간에 센서를 연결해 주세요.`}
            actionLabel="센서 연결하기"
            onAction={() => setIsRegisteringSensor(true)}
          />
        )
      }

      return (
        <EmptyState
          title="먼저 대상자를 등록해 주세요"
          description="대상자를 등록한 다음 센서를 연결할 수 있어요."
          actionLabel="대상자 등록하기"
          onAction={() => setActivePage('people')}
        />
      )
    }

    if (activePage === 'history') {
      if (registeredPeople.length === 0) {
        return (
          <EmptyState
            title="등록된 대상자가 없어요"
            description="먼저 대상자를 등록해주세요."
            actionLabel="대상자 등록하기"
            onAction={() => setIsRegisteringPerson(true)}
          />
        )
      }

      return <HistoryPage events={sensorEvents} initialTab={historyInitialTab} people={registeredPeople} sensors={registeredSensors} />
    }

    return (
      <ProfilePage
        theme={theme}
        user={user}
        onLogout={onLogout}
        onThemeChange={setTheme}
        onUserUpdate={onUserUpdate}
      />
    )
  }

  if (isRegisteringPerson) {
    return (
      <PersonRegistrationPage
        onBack={() => setIsRegisteringPerson(false)}
        onRegister={async (person) => {
          const created = await createPerson(person)
          setRegisteredPeople((people) => [...people, created])
          setActivePage('people')
          setIsRegisteringPerson(false)
        }}
      />
    )
  }


  if (editingPerson) {
    return (
      <PersonRegistrationPage
        initialPerson={editingPerson}
        onBack={() => setEditingPerson(null)}
        onDelete={async () => {
          await deletePerson(editingPerson.id)
          setRegisteredPeople((people) => people.filter(({ id }) => id !== editingPerson.id))
          setRegisteredSensors((sensors) => sensors.filter(({ personId }) => personId !== editingPerson.id))
          setSensorEvents((events) => events.filter(({ personId }) => personId !== editingPerson.id))
          setEditingPerson(null)
          setActivePage('people')
        }}
        onRegister={async (person) => {
          const updated = await updatePerson(editingPerson.id, person)
          setRegisteredPeople((people) => people.map((item) => (
            item.id === updated.id ? updated : item
          )))
          setEditingPerson(null)
        }}
      />
    )
  }

  if (isRegisteringSensor) {
    return (
      <SensorRegistrationPage
        people={registeredPeople}
        onBack={() => setIsRegisteringSensor(false)}
        onRegister={async (sensor) => {
          const created = await createSensor(sensor)
          setRegisteredSensors((sensors) => [...sensors, created])
          setActivePage('sensor')
          setIsRegisteringSensor(false)
        }}
      />
    )
  }

  if (editingSensor) {
    return (
      <SensorRegistrationPage
        initialSensor={editingSensor}
        people={registeredPeople}
        onBack={() => setEditingSensor(null)}
        onRegister={async (sensor) => {
          const updated = await updateSensor(editingSensor.id, sensor)
          setRegisteredSensors((sensors) => sensors.map((item) => (
            item.id === updated.id ? updated : item
          )))
          setEditingSensor(null)
        }}
      />
    )
  }

  return (
    <main className="main-page">
      <section className="main-panel" aria-label={activeItem?.label}>
        <div className="main-content" role="region" aria-label={`${activeItem?.label} 페이지`}>
          {renderPage()}
        </div>

        <nav className="bottom-navigation" aria-label="주요 메뉴">
          {navigationItems.map(({ id, label, icon: Icon }) => {
            const isActive = id === activePage
            const className = 'bottom-navigation__item'
              + (isActive ? ' bottom-navigation__item--active' : '')

            return (
              <button
                key={id}
                className={className}
                type="button"
                aria-current={isActive ? 'page' : undefined}
            onClick={() => {
              if (id === 'history') setHistoryInitialTab('analysis')
              setActivePage(id)
            }}
              >
                <Icon aria-hidden="true" />
                <span>{label}</span>
              </button>
            )
          })}
        </nav>
        {sensorToDelete && (
          <ConfirmDialog
            title="센서를 삭제할까요?"
            confirmLabel="삭제하기"
            isConfirming={isDeletingSensor}
            onCancel={() => setSensorToDelete(null)}
            onConfirm={confirmSensorDeletion}
          />
        )}
        {personToStopMonitoring && (
          <ConfirmDialog
            title="모니터링을 중지할까요?"
            confirmLabel="중지"
            confirmingLabel="중지 중..."
            isConfirming={updatingPersonId === personToStopMonitoring.id}
            onCancel={() => setPersonToStopMonitoring(null)}
            onConfirm={() => stopMonitoring(personToStopMonitoring)}
          />
        )}
        {apiError && <NoticeToast>{apiError}</NoticeToast>}
      </section>
    </main>
  )
}

export default MainPage
