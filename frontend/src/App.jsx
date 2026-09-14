import { useEffect, useState } from 'react'
import { getCurrentUser, login, logout, signUp, updateCurrentUser } from './api/auth'
import AuthLandingPage from './features/auth/pages/AuthLandingPage'
import LoginPage from './features/auth/pages/LoginPage'
import SignUpPage from './features/auth/pages/SignUpPage'
import MainPage from './features/main/pages/MainPage'
import HomeDashboard from './features/main/components/HomeDashboard'

const previewPerson = {
  id: 'preview-person',
  name: '김영희',
  phone: '010-0000-0000',
  livingSpace: '서울특별시 마포구',
}

const previewSensors = [
  { id: 'preview-door', personId: previewPerson.id, name: '현관 센서', location: '현관', targetObject: '현관문', status: 'normal' },
  { id: 'preview-bedroom', personId: previewPerson.id, name: '침실 센서', location: '침실', targetObject: '침대', status: 'normal' },
]

const minutesAgo = (minutes) => new Date(Date.now() - minutes * 60_000).toISOString()

function AnomalyCardsPreview() {
  const previewEvents = [
    { id: 'preview-event', personId: previewPerson.id, sensorId: 'preview-door', detectedAt: minutesAgo(35), detectedValue: '문 열림' },
  ]
  const previewAlerts = [
    {
      id: 'preview-inactivity', personId: previewPerson.id, sensorId: 'preview-bedroom', cause: 'INACTIVITY',
      title: '장시간 움직임 없음', description: '평소보다 35분간 움직임이 없어요.',
      evidence: '마지막 감지 35분 전', occurredAt: minutesAgo(1),
    },
    {
      id: 'preview-repeat', personId: previewPerson.id, sensorId: 'preview-door', cause: 'REPEATED_ACTIVITY',
      title: '평소와 다른 반복 행동', description: '짧은 시간 동안 같은 위치의 움직임이 반복됐어요.',
      evidence: '10분 동안 현관 센서 7회 감지', occurredAt: minutesAgo(5),
    },
    {
      id: 'preview-night', personId: previewPerson.id, sensorId: 'preview-bedroom', cause: 'UNUSUAL_HOUR',
      title: '늦은 시간 활동 감지', description: '평소 활동이 드문 시간에 움직임이 감지됐어요.',
      evidence: '오전 2:18 침실 센서 감지', occurredAt: minutesAgo(10),
    },
  ]

  return (
    <main className="main-page">
      <section className="main-panel" aria-label="이상 징후 카드 디자인 미리보기">
        <div className="main-content">
          <HomeDashboard
            alerts={previewAlerts}
            events={previewEvents}
            isConfirmingSafety={false}
            onConfirmSafety={() => {}}
            onOpenPerson={() => {}}
            onOpenWelfare={() => {}}
            person={previewPerson}
            sensors={previewSensors}
          />
        </div>
      </section>
    </main>
  )
}

function AuthenticatedApp() {
  const [page, setPage] = useState('loading')
  const [user, setUser] = useState(null)

  useEffect(() => {
    getCurrentUser()
      .then((currentUser) => {
        setUser(currentUser)
        setPage(currentUser ? 'main' : 'landing')
      })
      .catch(() => setPage('landing'))
  }, [])

  const handleAuthentication = async (action, credentials) => {
    const authenticatedUser = await action(credentials)
    setUser(authenticatedUser)
    setPage('main')
  }

  if (page === 'loading') return null

  if (page === 'login') {
    return (
      <LoginPage
        onBack={() => setPage('landing')}
        onLogin={(credentials) => handleAuthentication(login, credentials)}
      />
    )
  }

  if (page === 'signup') {
    return (
      <SignUpPage
        onBack={() => setPage('landing')}
        onSignUp={(credentials) => handleAuthentication(signUp, credentials)}
      />
    )
  }

  if (page === 'main') {
    return (
      <MainPage
        user={user}
        onUserUpdate={async (account) => {
          const updatedUser = await updateCurrentUser(account)
          setUser(updatedUser)
          return updatedUser
        }}
        onLogout={async () => {
          await logout()
          setUser(null)
          setPage('landing')
        }}
      />
    )
  }

  return (
    <AuthLandingPage
      onEmailLogin={() => setPage('login')}
      onSignUp={() => setPage('signup')}
    />
  )
}

function App() {
  const isAnomalyPreview = new URLSearchParams(window.location.search).get('preview') === 'anomalies'
  return isAnomalyPreview ? <AnomalyCardsPreview /> : <AuthenticatedApp />
}

export default App
