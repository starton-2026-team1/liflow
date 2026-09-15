import { useCallback, useEffect, useRef, useState } from 'react'
import { revealNfcContact, sendNfcHelp } from '../../../api/nfcTags'
import NfcalamPage from './NfcalamPage'
import NfcGuardianContactPage from './NfcGuardianContactPage'
import '../styles/nfcHelp.css'

function NfcHelpPage({ token }) {
  const [event, setEvent] = useState(null)
  const [contact, setContact] = useState(null)
  const [showSentConfirmation, setShowSentConfirmation] = useState(true)
  const [error, setError] = useState('')
  const notificationRequestRef = useRef(null)

  const ensureHelpEvent = useCallback(() => {
    if (!notificationRequestRef.current) {
      notificationRequestRef.current = sendNfcHelp(token).then((createdEvent) => {
        setEvent(createdEvent)
        return createdEvent
      })
    }
    return notificationRequestRef.current
  }, [token])

  useEffect(() => {
    ensureHelpEvent().catch((e) => setError(e.message))
  }, [ensureHelpEvent])

  const confirmContact = async () => {
    setError('')
    try {
      const activeEvent = event || await ensureHelpEvent()
      const nextContact = contact || await revealNfcContact(activeEvent.event_id, activeEvent.finder_token)
      setContact(nextContact)
      setShowSentConfirmation(false)
    } catch (e) {
      setError(e.message)
    }
  }
  if (showSentConfirmation) {
    return <NfcalamPage onConfirm={confirmContact} error={error} />
  }

  if (contact) {
    return <NfcGuardianContactPage guardianPhone={contact.guardian_phone} />
  }

  return <NfcalamPage onConfirm={confirmContact} error={error} />
}

export default NfcHelpPage
