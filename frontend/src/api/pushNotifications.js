import { apiRequest } from './client'

const decodeVapidKey = (value) => {
  const padding = '='.repeat((4 - (value.length % 4)) % 4)
  const base64 = (value + padding).replace(/-/g, '+').replace(/_/g, '/')
  return Uint8Array.from(window.atob(base64), (character) => character.charCodeAt(0))
}

export const pushNotificationsSupported = () => (
  'serviceWorker' in navigator && 'PushManager' in window && 'Notification' in window
)

export async function enablePushNotifications() {
  if (!pushNotificationsSupported()) {
    throw new Error('이 기기에서는 웹 푸시 알림을 지원하지 않아요.')
  }

  const configuration = await apiRequest('/push-subscriptions/configuration')
  if (!configuration.enabled || !configuration.public_key) {
    throw new Error('서버의 푸시 알림 키가 아직 설정되지 않았어요.')
  }

  const permission = await Notification.requestPermission()
  if (permission !== 'granted') {
    throw new Error('브라우저 알림 권한이 필요해요.')
  }

  const registration = await navigator.serviceWorker.register('/sw.js')
  const existing = await registration.pushManager.getSubscription()
  const subscription = existing || await registration.pushManager.subscribe({
    userVisibleOnly: true,
    applicationServerKey: decodeVapidKey(configuration.public_key),
  })

  await apiRequest('/push-subscriptions', {
    method: 'POST',
    body: JSON.stringify(subscription.toJSON()),
  })
  return true
}

export async function registerNotificationWorker() {
  if (!pushNotificationsSupported()) return null
  return navigator.serviceWorker.register('/sw.js')
}
