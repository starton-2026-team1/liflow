import { useEffect, useState } from 'react'
import { Check, CheckCircle2, LoaderCircle, Wifi } from 'lucide-react'
import StepFormLayout from '../../../components/common/StepFormLayout'
import UnderlinedInput from '../../../components/common/UnderlinedInput'
import '../../auth/styles/login.css'
import '../styles/sensorRegistration.css'

const steps = [
  { field: 'serialNumber', question: '센서 고유번호를 입력해 주세요.' },
  { field: 'connection', question: '센서 연결을 확인할게요.' },
  { field: 'personId', question: '누구의 센서인가요?' },
  { field: 'name', question: '센서 이름을 정해 주세요.' },
  { field: 'type', question: '어떤 유형의 센서인가요?' },
  { field: 'targetObject', question: '어떤 물체를 감지하나요?' },
  { field: 'location', question: '센서를 어디에 설치했나요?' },
]

const initialForm = { serialNumber: '', personId: '', name: '', type: 'ultrasonic', targetObject: '', location: '' }

function SensorRegistrationPage({ initialSensor, people, onBack, onRegister }) {
  const [form, setForm] = useState(() => initialSensor
    ? { ...initialForm, ...initialSensor }
    : { ...initialForm, personId: people[0]?.id || '' })
  const [step, setStep] = useState(0)
  const [error, setError] = useState('')
  const [connectionStatus, setConnectionStatus] = useState(initialSensor ? 'success' : 'idle')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const current = steps[step]

  useEffect(() => {
    if (connectionStatus !== 'testing') return undefined
    const timer = window.setTimeout(() => setConnectionStatus('success'), 1200)
    return () => window.clearTimeout(timer)
  }, [connectionStatus])

  const update = (value) => {
    setForm((values) => ({ ...values, [current.field]: value }))
    setError('')
  }

  const handleBack = () => step > 0 ? setStep((value) => value - 1) : onBack?.()

  const handleSubmit = async (event) => {
    event.preventDefault()
    if (current.field === 'connection') {
      if (connectionStatus === 'success') setStep((value) => value + 1)
      return
    }
    if (!String(form[current.field] ?? '').trim()) {
      setError('필수 정보를 입력해 주세요.')
      return
    }
    if (step === steps.length - 1) {
      setIsSubmitting(true)
      try {
        await onRegister?.({ ...form, status: 'normal' })
      } catch (submitError) {
        setError(submitError.message || `센서를 ${initialSensor ? '수정' : '등록'}하지 못했어요.`)
      } finally {
        setIsSubmitting(false)
      }
    } else setStep((value) => value + 1)
  }

  const renderInput = () => {
    if (current.field === 'connection') {
      return (
        <div className={`step-connection step-connection--${connectionStatus}`}>
          {connectionStatus === 'testing' ? <LoaderCircle className="connection-test__spinner" aria-hidden="true" /> : connectionStatus === 'success' ? <CheckCircle2 aria-hidden="true" /> : <Wifi aria-hidden="true" />}
          <strong>{connectionStatus === 'testing' ? '연결 확인 중' : connectionStatus === 'success' ? '연결 정상' : '테스트 준비 완료'}</strong>
          <p>{connectionStatus === 'success' ? '센서가 정상적으로 연결됐어요.' : '센서 전원을 켠 후 테스트해 주세요.'}</p>
          {connectionStatus === 'idle' && <button type="button" onClick={() => setConnectionStatus('testing')}>연결 테스트</button>}
        </div>
      )
    }
    if (current.field === 'personId') {
      return <div className="step-choice-list">{people.map((person) => <button className={form.personId === person.id ? 'selected' : ''} type="button" key={person.id} onClick={() => update(person.id)}>{person.name}{form.personId === person.id && <Check aria-hidden="true" />}</button>)}</div>
    }
    if (current.field === 'type') {
      return <div className="step-choice-list"><button className="selected" type="button" aria-pressed="true">초음파 센서<Check aria-hidden="true" /></button></div>
    }
    const placeholders = { serialNumber: '센서 고유번호', name: '예: 거실 센서', targetObject: '예: 냉장고, 현관문', location: '예: 주방, 현관' }
    return <UnderlinedInput id={`sensor-${current.field}`} value={form[current.field]} placeholder={placeholders[current.field]} autoFocus error={error} onChange={(event) => update(current.field === 'serialNumber' ? event.target.value.toUpperCase() : event.target.value)} action={form[current.field].trim() ? <Check className="input-check" aria-label="입력 완료" /> : null} />
  }

  return (
    <StepFormLayout ariaLabel={`센서 정보 ${initialSensor ? '수정' : '등록'}`} currentStep={step} totalSteps={steps.length} onBack={handleBack} onSubmit={handleSubmit} actionLabel={isSubmitting ? `${initialSensor ? '수정' : '등록'} 중...` : step === steps.length - 1 ? `${initialSensor ? '수정' : '등록'}하기` : '다음'} actionDisabled={isSubmitting || (current.field === 'connection' && connectionStatus !== 'success')}>
      <h1 className="step-form-question">{current.question}</h1>
      {current.field === 'serialNumber' && <p className="step-form-description">센서 뒷면에 적힌 번호를 확인해 주세요.</p>}
      {renderInput()}
      {error && ['connection', 'personId', 'type'].includes(current.field) && <p className="step-form-server-error" role="alert">{error}</p>}
    </StepFormLayout>
  )
}

export default SensorRegistrationPage
