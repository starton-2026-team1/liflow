import { useEffect, useState } from 'react'
import { getCurrentUser, login, logout, signUp, updateCurrentUser } from './api/auth'
import AuthLandingPage from './features/auth/pages/AuthLandingPage'
import LoginPage from './features/auth/pages/LoginPage'
import SignUpPage from './features/auth/pages/SignUpPage'
import MainPage from './features/main/pages/MainPage'

function App() {
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

export default App
