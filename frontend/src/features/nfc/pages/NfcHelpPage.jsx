import { useCallback, useEffect, useRef, useState } from 'react'
import { getNfcHelpStatus, revealNfcContact, sendNfcHelp } from '../../../api/nfcTags'
import NfcalamPage from './NfcalamPage'
import NfcGuardianContactPage from './NfcGuardianContactPage'
import '../styles/nfcHelp.css'

function NfcHelpPage({ token }) {
  const [event, setEvent] = useState(null)
  const [status, setStatus] = useState(null)
  const [contact, setContact] = useState(null)
  const [confirmationAccepted, setConfirmationAccepted] = useState(false)
  const [error, setError] = useState('')
  const notificationRequestRef = useRef(null)

  const ensureHelpEvent = useCallback(() => {
    if (!notificationRequestRef.current) {
      const storageKey = `liflow:nfc-help:${token}`
      try {
        const cachedEvent = JSON.parse(window.localStorage.getItem(storageKey))
        const cacheExpiresAt = new Date(cachedEvent?.contact_available_at).getTime() + 60 * 60_000
        if (cachedEvent?.event_id && cachedEvent?.finder_token && Date.now() < cacheExpiresAt) {
          notificationRequestRef.current = Promise.resolve(cachedEvent)
        }
      } catch {
        window.localStorage.removeItem(storageKey)
      }
      if (!notificationRequestRef.current) {
        notificationRequestRef.current = sendNfcHelp(token).then((createdEvent) => {
          window.localStorage.setItem(storageKey, JSON.stringify(createdEvent))
          return createdEvent
        })
      }
      notificationRequestRef.current.then(setEvent)
    }
    return notificationRequestRef.current
  }, [token])

  useEffect(() => {
    ensureHelpEvent().catch((e) => setError(e.message))
  }, [ensureHelpEvent])

  useEffect(() => {
    if (!event) return undefined
    const check = () => getNfcHelpStatus(event.event_id, event.finder_token)
      .then(setStatus)
      .catch((e) => setError(e.message))
    check()
    const timer = window.setInterval(check, 5000)
    return () => window.clearInterval(timer)
  }, [event])

  useEffect(() => {
    if (!confirmationAccepted || !status?.contact_available || !event || contact) return
    revealNfcContact(event.event_id, event.finder_token)
      .then(setContact)
      .catch((e) => setError(e.message))
  }, [confirmationAccepted, contact, event, status?.contact_available])

  if (contact) {
    return <NfcGuardianContactPage guardianPhone={contact.guardian_phone} />
  }

  return (
    <NfcalamPage
      onConfirm={() => setConfirmationAccepted(true)}
      waiting={confirmationAccepted}
      error={error}
    />
  )
}

export default NfcHelpPage
