import { useState } from 'react'
import { Check } from 'lucide-react'
import StepFormLayout from '../../../components/common/StepFormLayout'
import UnderlinedInput from '../../../components/common/UnderlinedInput'
import ConfirmDialog from '../../../components/common/ConfirmDialog'
import '../../auth/styles/login.css'
import '../styles/personRegistration.css'

const steps = [
  { field: 'name', question: '대상자를 어떻게 부를까요?', description: '실명 대신 별칭을 입력해도 괜찮아요.' },
  { field: 'ageGroup', question: '대상자의 연령대를 알려주세요.', description: '선택 정보이며 건너뛸 수 있어요.' },
  { field: 'phone', question: '대상자의 연락처를 입력해 주세요.', description: '선택 정보이며 긴급 연락이 필요할 때 사용해요.' },
  { field: 'livingSpace', question: '주로 생활하는 공간은 어디인가요?', description: '상세 주소가 아닌 센서를 사용할 공간만 입력해 주세요.' },
  { field: 'healthNotes', question: '건강이나 거동에 참고할 사항이 있나요?', description: '민감정보이며 입력하지 않아도 서비스를 이용할 수 있어요.' },
]

const ageGroups = ['60대 이하', '70대', '80대', '90대 이상']
const initialForm = { name: '', ageGroup: '', phone: '', livingSpace: '', healthNotes: '' }

function PersonRegistrationPage({ initialPerson, onBack, onDelete, onRegister }) {
  const [form, setForm] = useState(() => initialPerson
    ? { ...initialForm, ...initialPerson }
    : initialForm)
  const [step, setStep] = useState(0)
  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)
  const current = steps[step]

  const update = (field, value) => {
    setForm((values) => ({ ...values, [field]: value }))
    setError('')
  }

  const handleBack = () => step > 0 ? setStep((value) => value - 1) : onBack?.()

  const handleSubmit = async (event) => {
    event.preventDefault()
    const value = form[current.field]?.trim()

    if (['name', 'livingSpace'].includes(current.field) && !value) {
      setError('필수 정보를 입력해 주세요.')
      return
    }
    if (current.field === 'phone' && value && form.phone.length !== 13) {
      setError('연락처를 정확히 입력하거나 건너뛰어 주세요.')
      return
    }
    if (step === steps.length - 1) {
      setIsSubmitting(true)
      try {
        await onRegister?.(form)
      } catch (submitError) {
        setError(submitError.message || `대상자 정보를 ${initialPerson ? '수정' : '등록'}하지 못했어요.`)
      } finally {
        setIsSubmitting(false)
      }
    } else setStep((valueStep) => valueStep + 1)
  }

  const phoneChange = (event) => {
    const digits = event.target.value.replace(/\D/g, '').slice(0, 11)
    const value = digits.length <= 3 ? digits : digits.length <= 7
      ? `${digits.slice(0, 3)}-${digits.slice(3)}`
      : `${digits.slice(0, 3)}-${digits.slice(3, 7)}-${digits.slice(7)}`
    update('phone', value)
  }

  const renderInput = () => {
    if (current.field === 'ageGroup') {
      return <div className="person-step-choices">{ageGroups.map((age) => <button className={form.ageGroup === age ? 'selected' : ''} type="button" key={age} onClick={() => update('ageGroup', age)}>{age}{form.ageGroup === age && <Check aria-hidden="true" />}</button>)}</div>
    }
    if (current.field === 'phone') {
      return <UnderlinedInput id="person-phone" type="tel" inputMode="numeric" value={form.phone} placeholder="010-0000-0000" error={error} onChange={phoneChange} action={form.phone.length === 13 ? <Check className="input-check" aria-label="입력 완료" /> : null} />
    }
    if (current.field === 'healthNotes') {
      return <div className="step-notes-input"><textarea value={form.healthNotes} maxLength={300} autoFocus placeholder="예: 보행 보조기 사용, 복용 중인 약" onChange={(event) => update('healthNotes', event.target.value)} /><span>{form.healthNotes.length}/300</span></div>
    }
    const placeholders = { name: '이름 또는 별칭', livingSpace: '예: 집, 요양원, 침실' }
    return <UnderlinedInput id={`person-${current.field}`} value={form[current.field]} placeholder={placeholders[current.field]} autoFocus error={error} onChange={(event) => update(current.field, event.target.value)} action={form[current.field].trim() ? <Check className="input-check" aria-label="입력 완료" /> : null} />
  }

  const isOptionalStep = ['ageGroup', 'phone', 'healthNotes'].includes(current.field)

  const handleDelete = async () => {
    setIsDeleting(true)
    try {
      await onDelete?.()
    } catch (deleteError) {
      setError(deleteError.message || '대상자를 삭제하지 못했어요.')
      setShowDeleteConfirm(false)
    } finally {
      setIsDeleting(false)
    }
  }

  return (
    <>
      <StepFormLayout ariaLabel={`대상자 정보 ${initialPerson ? '수정 및 삭제' : '등록'}`} currentStep={step} totalSteps={steps.length} onBack={handleBack} onSubmit={handleSubmit} actionDisabled={isSubmitting || isDeleting} actionLabel={isSubmitting ? `${initialPerson ? '수정' : '등록'} 중...` : step === steps.length - 1 ? `${initialPerson ? '수정' : '등록'}하기` : isOptionalStep && !form[current.field] ? '건너뛰기' : '다음'} secondaryActionLabel={initialPerson && step === 0 ? '대상자 삭제' : undefined} secondaryActionDisabled={isSubmitting || isDeleting} onSecondaryAction={() => setShowDeleteConfirm(true)}>
        <h1 className="step-form-question">{current.question}</h1>
        <p className="step-form-description">{current.description}</p>
        {renderInput()}
        {error && ['ageGroup', 'healthNotes'].includes(current.field) && <p className="step-form-server-error" role="alert">{error}</p>}
      </StepFormLayout>
      {showDeleteConfirm && (
        <ConfirmDialog
          title={`${initialPerson.name} 대상자를 삭제할까요?`}
          description={<>연결된 센서와 기록도 함께 삭제되며,<br />삭제한 정보는 복구할 수 없어요.</>}
          confirmLabel="삭제"
          isConfirming={isDeleting}
          onCancel={() => setShowDeleteConfirm(false)}
          onConfirm={handleDelete}
        />
      )}
    </>
  )
}

export default PersonRegistrationPage
