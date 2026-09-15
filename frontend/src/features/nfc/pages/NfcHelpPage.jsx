import { useEffect, useRef, useState } from 'react'
import { getNfcHelp, getNfcHelpStatus, revealNfcContact, sendNfcHelp } from '../../../api/nfcTags'
import NfcalamPage from './NfcalamPage'
import NfcGuardianContactPage from './NfcGuardianContactPage'
import '../styles/nfcHelp.css'

function NfcHelpPage({ token }) {
  const [tag, setTag] = useState(null)
  const [event, setEvent] = useState(null)
  const [status, setStatus] = useState(null)
  const [contact, setContact] = useState(null)
  const [showSentConfirmation, setShowSentConfirmation] = useState(true)
  const [error, setError] = useState('')
  const notificationStartedRef = useRef(false)
  const contactRevealStartedRef = useRef(false)

  useEffect(() => { getNfcHelp(token).then(setTag).catch((e) => setError(e.message)) }, [token])
  useEffect(() => {
    if (notificationStartedRef.current) return
    notificationStartedRef.current = true
    sendNfcHelp(token)
      .then(setEvent)
      .catch((e) => {
        setError(e.message)
        setShowSentConfirmation(false)
      })
  }, [token])
  useEffect(() => {
    if (!event) return undefined
    const check = () => getNfcHelpStatus(event.event_id, event.finder_token).then(setStatus).catch(() => {})
    check()
    const timer = window.setInterval(check, 10000)
    return () => window.clearInterval(timer)
  }, [event])
  useEffect(() => {
    if (!event || !status?.contact_available || contactRevealStartedRef.current) return
    contactRevealStartedRef.current = true
    revealNfcContact(event.event_id, event.finder_token)
      .then(setContact)
      .catch((e) => {
        contactRevealStartedRef.current = false
        setError(e.message)
      })
  }, [event, status?.contact_available])

  const notify = async () => {
    setError('')
    setShowSentConfirmation(true)
    try {
      setEvent(await sendNfcHelp(token))
    } catch (e) {
      setError(e.message)
      setShowSentConfirmation(false)
    }
  }
  if (showSentConfirmation) {
    return <NfcalamPage onConfirm={() => setShowSentConfirmation(false)} />
  }

  if (contact) {
    return <NfcGuardianContactPage guardianPhone={contact.guardian_phone} />
  }

  return <main className="nfc-help-page"><section className="nfc-help-card">
    <span className="nfc-help-badge">liflow 안심태그</span>
    <h1>{tag?.tag_name || '안심태그 확인 중'}</h1>
    <p>개인정보 보호를 위해 대상자 정보는 공개하지 않습니다.</p>
    {!event && error && <button type="button" onClick={notify} disabled={!tag}>알림 다시 보내기</button>}
    {event && !status?.acknowledged && <><strong>보호자에게 알림을 보냈습니다.</strong><p>보호자의 확인을 기다리고 있어요.</p></>}
    {status?.acknowledged && <strong>보호자가 확인했습니다. 도와주셔서 감사합니다.</strong>}
    {status?.contact_available && !contact && <strong>보호자 연락처를 불러오고 있어요.</strong>}
    {contact && <a className="nfc-help-phone" href={`tel:${contact.guardian_phone}`}>보호자에게 전화하기<br />{contact.guardian_phone}</a>}
    {error && <p className="nfc-help-error">{error}</p>}
  </section></main>
}

export default NfcHelpPage
