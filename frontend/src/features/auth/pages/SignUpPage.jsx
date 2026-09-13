import { useState } from 'react'
import { Check, Eye, EyeOff } from 'lucide-react'
import BackButton from '../../../components/common/BackButton'
import UnderlinedInput from '../../../components/common/UnderlinedInput'
import { getEmailError, isValidEmail, shouldAutoConfirmEmail } from '../utils/emailValidation'
import '../styles/login.css'
import '../styles/signup.css'

const MIN_PASSWORD_LENGTH = 8

function SignUpPage({ onBack, onSignUp }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [passwordConfirm, setPasswordConfirm] = useState('')
  const [emailConfirmed, setEmailConfirmed] = useState(false)
  const [passwordVisible, setPasswordVisible] = useState(false)
  const [emailError, setEmailError] = useState('')
  const [passwordError, setPasswordError] = useState('')
  const [confirmError, setConfirmError] = useState('')
  const [signUpError, setSignUpError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const confirmEmail = () => {
    const validationError = getEmailError(email)

    if (validationError) {
      setEmailError(validationError)
      return
    }

    setEmailError('')
    setEmailConfirmed(true)
  }

  const handleEmailChange = (event) => {
    const nextEmail = event.target.value
    setEmail(nextEmail)
    setEmailError('')

    if (shouldAutoConfirmEmail(nextEmail)) {
      setEmailConfirmed(true)
    }
  }

  const handlePasswordChange = (event) => {
    const nextPassword = event.target.value
    setPassword(nextPassword)
    setPasswordError('')

    if (passwordConfirm) {
      setConfirmError(nextPassword === passwordConfirm ? '' : '비밀번호가 일치하지 않아요.')
    }
  }

  const handlePasswordConfirmChange = (event) => {
    const nextPasswordConfirm = event.target.value
    setPasswordConfirm(nextPasswordConfirm)
    setConfirmError(nextPasswordConfirm === password ? '' : '비밀번호가 일치하지 않아요.')
  }

  const handleSubmit = async (event) => {
    event.preventDefault()

    if (!emailConfirmed) {
      confirmEmail()
      return
    }

    const nextEmailError = getEmailError(email)
    const nextPasswordError = password.length < MIN_PASSWORD_LENGTH
      ? `비밀번호는 ${MIN_PASSWORD_LENGTH}자 이상 입력해 주세요.`
      : ''
    const nextConfirmError = password !== passwordConfirm ? '비밀번호가 일치하지 않아요.' : ''

    setEmailError(nextEmailError)
    setPasswordError(nextPasswordError)
    setConfirmError(nextConfirmError)

    if (!nextEmailError && !nextPasswordError && !nextConfirmError && onSignUp) {
      setIsSubmitting(true)
      setSignUpError('')
      try {
        await onSignUp({ email, password })
      } catch (error) {
        setSignUpError(error.message || '회원가입하지 못했어요.')
      } finally {
        setIsSubmitting(false)
      }
    }
  }

  const handleBack = () => {
    if (emailConfirmed) {
      setEmailConfirmed(false)
      setPassword('')
      setPasswordConfirm('')
      setPasswordError('')
      setConfirmError('')
      setPasswordVisible(false)
      return
    }

    onBack?.()
  }

  const canSubmit = password.length >= MIN_PASSWORD_LENGTH
    && passwordConfirm === password
    && !emailError

  return (
    <main className="login-page signup-page">
      <section className="login-panel" aria-label="회원가입">
        <BackButton onClick={handleBack} />

        <form className="login-form signup-form" onSubmit={handleSubmit} noValidate>
          {!emailConfirmed ? (
            <UnderlinedInput
              id="signup-email"
              type="email"
              value={email}
              placeholder="이메일"
              autoComplete="email"
              autoFocus
              aria-invalid={Boolean(emailError)}
              aria-describedby={emailError ? 'signup-email-error' : undefined}
              error={emailError}
              onChange={handleEmailChange}
              action={isValidEmail(email) ? <Check className="input-check" aria-label="입력 완료" /> : null}
            />
          ) : (
            <div className="signup-fields">
              <UnderlinedInput
                id="signup-password"
                type={passwordVisible ? 'text' : 'password'}
                value={password}
                placeholder="비밀번호 (8자 이상)"
                autoComplete="new-password"
                autoFocus
                aria-invalid={Boolean(passwordError)}
                error={passwordError}
                onChange={handlePasswordChange}
                action={(
                  <button
                    className="visibility-button"
                    type="button"
                    aria-label={passwordVisible ? '비밀번호 숨기기' : '비밀번호 보기'}
                    onClick={() => setPasswordVisible((visible) => !visible)}
                  >
                    {passwordVisible ? <EyeOff aria-hidden="true" /> : <Eye aria-hidden="true" />}
                  </button>
                )}
              />

              <UnderlinedInput
                id="signup-password-confirm"
                type={passwordVisible ? 'text' : 'password'}
                value={passwordConfirm}
                placeholder="비밀번호 확인"
                autoComplete="new-password"
                aria-invalid={Boolean(confirmError)}
                error={confirmError}
                onChange={handlePasswordConfirmChange}
                action={passwordConfirm && !confirmError ? <Check className="input-check" aria-label="입력 완료" /> : null}
              />

              <div className={`confirmed-email${emailError ? ' confirmed-email--error' : ''}`}>
                <input
                  id="signup-confirmed-email"
                  type="email"
                  value={email}
                  aria-label="이메일 수정"
                  autoComplete="email"
                  onChange={(event) => {
                    setEmail(event.target.value)
                    setEmailError(getEmailError(event.target.value))
                  }}
                />
                {!emailError && <Check className="input-check" aria-hidden="true" />}
              </div>
              {emailError && <p className="confirmed-email-error">{emailError}</p>}
              {signUpError && <p className="confirmed-email-error" role="alert">{signUpError}</p>}
            </div>
          )}

          <button
            className="login-button"
            type="submit"
            disabled={isSubmitting || (emailConfirmed ? !canSubmit : !isValidEmail(email))}
          >
            {isSubmitting ? '가입 중...' : emailConfirmed ? '가입하기' : '다음'}
          </button>
        </form>
      </section>
    </main>
  )
}

export default SignUpPage
