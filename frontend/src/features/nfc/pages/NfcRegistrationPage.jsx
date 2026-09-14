import { useEffect, useRef, useState } from 'react'
import { Check, CheckCircle2, LoaderCircle, Nfc } from 'lucide-react'
import StepFormLayout from '../../../components/common/StepFormLayout'
import UnderlinedInput from '../../../components/common/UnderlinedInput'
import '../styles/nfcRegistration.css'

const steps = [
  { field: 'tag', question: '안심태그를 휴대폰에 가까이 대 주세요.' },
  { field: 'personId', question: '누구의 안심태그인가요?' },
  { field: 'name', question: '안심태그 이름을 정해 주세요.' },
  { field: 'guardianName', question: '보호자 이름을 입력해 주세요.' },
  { field: 'guardianPhone', question: '보호자 전화번호를 입력해 주세요.' },
  { field: 'write', question: '입력한 정보를 태그에 저장할게요.' },
]

const isWebNfcSupported = typeof window !== 'undefined' && 'NDEFReader' in window

function NfcRegistrationPage({ people, onBack, onRegister }) {
  const [form, setForm] = useState({ personId: people[0]?.id || '', name: '', guardianName: '', guardianPhone: '', tagSerial: '' })
  const [step, setStep] = useState(0)
  const [scanStatus, setScanStatus] = useState('idle')
  const [scanError, setScanError] = useState('')
  const [writeStatus, setWriteStatus] = useState('idle')
  const [writeError, setWriteError] = useState('')
  const [error, setError] = useState('')
  const current = steps[step]
  const abortControllerRef = useRef(null)

  useEffect(() => {
    return () => abortControllerRef.current?.abort()
  }, [])

  const update = (field, value) => {
    setForm((values) => ({ ...values, [field]: value }))
    setError('')
  }

  const startScan = async () => {
    setScanError('')
    if (!isWebNfcSupported) {
      setScanError('이 기기 또는 브라우저는 NFC 태그 스캔을 지원하지 않아요. Android Chrome에서 시도해 주세요.')
      return
    }
    setScanStatus('scanning')
    try {
      const controller = new AbortController()
      abortControllerRef.current = controller
      const reader = new window.NDEFReader()
      await reader.scan({ signal: controller.signal })
      reader.onreading = (event) => {
        update('tagSerial', event.serialNumber || '')
        setScanStatus('success')
      }
      reader.onreadingerror = () => {
        setScanError('태그를 읽지 못했어요. 다시 시도해 주세요.')
        setScanStatus('idle')
      }
    } catch (err) {
      setScanError(err?.name === 'NotAllowedError' ? 'NFC 사용 권한이 필요해요.' : '태그 스캔을 시작하지 못했어요.')
      setScanStatus('idle')
    }
  }

  const writeTag = async () => {
    setWriteError('')
    if (!isWebNfcSupported) {
      setWriteError('이 기기 또는 브라우저는 NFC 태그 쓰기를 지원하지 않아요. Android Chrome에서 시도해 주세요.')
      return
    }
    setWriteStatus('writing')
    try {
      const reader = new window.NDEFReader()
      await reader.write({
        records: [
          {
            recordType: 'text',
            data: [
              `안심태그: ${form.name}`,
              `보호자: ${form.guardianName}`,
              `연락처: ${form.guardianPhone}`,
            ].join('\n'),
          },
        ],
      })
      setWriteStatus('success')
    } catch (err) {
      setWriteError(err?.name === 'NotAllowedError' ? 'NFC 사용 권한이 필요해요.' : '태그에 저장하지 못했어요. 태그를 다시 대고 시도해 주세요.')
      setWriteStatus('idle')
    }
  }

  const handleBack = () => {
    if (step > 0) setStep((value) => value - 1)
    else onBack?.()
  }

  const handleSubmit = (event) => {
    event.preventDefault()
    if (current.field === 'tag') {
      if (scanStatus === 'success') setStep((value) => value + 1)
      return
    }
    if (current.field === 'write') {
      if (writeStatus === 'success') onRegister?.(form)
      return
    }
    if (!String(form[current.field] || '').trim()) {
      setError('필수 정보를 입력해 주세요.')
      return
    }
    if (step === steps.length - 1) onRegister?.(form)
    else setStep((value) => value + 1)
  }

  const renderContent = () => {
    if (current.field === 'tag') {
      return (
        <div className={`nfc-scan-card nfc-scan-card--${scanStatus}`}>
          {scanStatus === 'scanning' ? <LoaderCircle className="nfc-scan-card__spinner" aria-hidden="true" /> : scanStatus === 'success' ? <CheckCircle2 aria-hidden="true" /> : <Nfc aria-hidden="true" />}
          <strong>{scanStatus === 'scanning' ? '태그를 찾고 있어요' : scanStatus === 'success' ? '안심태그를 인식했어요' : '스캔할 준비가 됐어요'}</strong>
          <p>{scanStatus === 'success' ? '이제 태그를 사용할 사람과 이름을 설정해 주세요.' : '휴대폰 뒷면의 NFC 인식 영역에 태그를 가까이 대 주세요.'}</p>
          {scanStatus === 'idle' && <button type="button" onClick={startScan}>태그 스캔하기</button>}
          {scanError && <p className="step-form-server-error" role="alert">{scanError}</p>}
        </div>
      )
    }
    if (current.field === 'write') {
      return (
        <div className={`nfc-scan-card nfc-scan-card--${writeStatus}`}>
          {writeStatus === 'writing' ? <LoaderCircle className="nfc-scan-card__spinner" aria-hidden="true" /> : writeStatus === 'success' ? <CheckCircle2 aria-hidden="true" /> : <Nfc aria-hidden="true" />}
          <strong>{writeStatus === 'writing' ? '태그에 저장하고 있어요' : writeStatus === 'success' ? '태그에 저장했어요' : '태그를 다시 대 주세요'}</strong>
          <p>{writeStatus === 'success' ? '등록하기를 눌러 마무리해 주세요.' : '처음에 스캔했던 안심태그를 휴대폰 뒷면에 가까이 대 주세요.'}</p>
          {writeStatus === 'idle' && <button type="button" onClick={writeTag}>태그에 저장하기</button>}
          {writeError && <p className="step-form-server-error" role="alert">{writeError}</p>}
        </div>
      )
    }
    if (current.field === 'personId') {
      if (people.length === 0) {
        return (
          <div className="nfc-empty-people">
            <strong>등록된 대상자가 없어요</strong>
            <p>대상자를 먼저 등록한 뒤 안심태그를 연결할 수 있어요.</p>
          </div>
        )
      }
      return (
        <div className="nfc-choice-list">
          {people.map((person) => (
            <button className={form.personId === person.id ? 'selected' : ''} type="button" key={person.id} onClick={() => update('personId', person.id)}>
              {person.name}
              {form.personId === person.id && <Check aria-hidden="true" />}
            </button>
          ))}
        </div>
      )
    }
    const inputSettings = {
      name: { placeholder: '예: 00의 안심태그', type: 'text' },
      guardianName: { placeholder: '보호자 이름', type: 'text' },
      guardianPhone: { placeholder: '010-0000-0000', type: 'tel' },
    }
    const settings = inputSettings[current.field]
    const value = form[current.field]
    return <UnderlinedInput id={`nfc-${current.field}`} type={settings.type} value={value} placeholder={settings.placeholder} autoFocus error={error} inputMode={current.field === 'guardianPhone' ? 'tel' : undefined} onChange={(event) => update(current.field, current.field === 'guardianPhone' ? event.target.value.replace(/[^0-9-]/g, '') : event.target.value)} action={value.trim() ? <Check className="input-check" aria-label="입력 완료" /> : null} />
  }

  return (
    <StepFormLayout ariaLabel="안심태그 등록" currentStep={step} totalSteps={steps.length} onBack={handleBack} onSubmit={handleSubmit} actionLabel={step === steps.length - 1 ? '등록하기' : '다음'} actionDisabled={(current.field === 'tag' && scanStatus !== 'success') || (current.field === 'write' && writeStatus !== 'success') || (current.field === 'personId' && people.length === 0)}>
      <p className="nfc-registration__eyebrow">안심태그(NFC) 등록</p>
      <h1 className="step-form-question">{current.question}</h1>
      {renderContent()}
      {error && current.field === 'personId' && <p className="step-form-server-error" role="alert">{error}</p>}
    </StepFormLayout>
  )
}

export default NfcRegistrationPage
