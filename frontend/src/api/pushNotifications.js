import { apiRequest } from './client'
import { Capacitor } from '@capacitor/core'
import { PushNotifications } from '@capacitor/push-notifications'

const decodeVapidKey = (value) => {
  const padding = '='.repeat((4 - (value.length % 4)) % 4)
  const base64 = (value + padding).replace(/-/g, '+').replace(/_/g, '/')
  return Uint8Array.from(window.atob(base64), (character) => character.charCodeAt(0))
}

export const pushNotificationsSupported = () => (
  Capacitor.isNativePlatform()
  || ('serviceWorker' in navigator && 'PushManager' in window && 'Notification' in window)
)

const enableNativePushNotifications = async () => {
  await PushNotifications.createChannel({
    id: 'liflow_alerts',
    name: 'liflow 안전 알림',
    description: '이상행동 및 장시간 움직임 없음 알림',
    importance: 5,
    visibility: 1,
    vibration: true,
  })

  let permission = await PushNotifications.checkPermissions()
  if (permission.receive === 'prompt') {
    permission = await PushNotifications.requestPermissions()
  }
  if (permission.receive !== 'granted') {
    throw new Error('앱 알림 권한이 필요해요.')
  }

  return new Promise((resolve, reject) => {
    let settled = false
    const finish = (callback, value) => {
      if (settled) return
      settled = true
      callback(value)
    }

    PushNotifications.addListener('registration', async ({ value: token }) => {
      try {
        await apiRequest('/fcm-device-tokens', {
          method: 'POST',
          body: JSON.stringify({ token, platform: 'android' }),
        })
        finish(resolve, true)
      } catch (error) {
        finish(reject, error)
      }
    })
    PushNotifications.addListener('registrationError', (error) => {
      finish(reject, new Error(error?.error || '푸시 알림 등록에 실패했어요.'))
    })
    PushNotifications.register()
  })
}

export async function enablePushNotifications() {
  if (Capacitor.isNativePlatform()) {
    return enableNativePushNotifications()
  }
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
  if (Capacitor.isNativePlatform()) return null
  if (!pushNotificationsSupported()) return null
  return navigator.serviceWorker.register('/sw.js')
}
