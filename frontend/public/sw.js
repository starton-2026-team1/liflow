self.addEventListener('push', (event) => {
  let payload = {}
  try {
    payload = event.data?.json() || {}
  } catch {
    payload = { body: event.data?.text() }
  }

  event.waitUntil(self.registration.showNotification(payload.title || '살핌이 알림', {
    body: payload.body || '보호 대상자의 상태를 확인해 주세요.',
    icon: '/favicon.svg',
    badge: '/favicon.svg',
    tag: payload.tag || 'starton-alert',
    renotify: true,
    data: { url: payload.url || '/', alert: payload.data || null },
  }))
})

self.addEventListener('notificationclick', (event) => {
  event.notification.close()
  const targetUrl = new URL(event.notification.data?.url || '/', self.location.origin).href
  event.waitUntil((async () => {
    const windows = await self.clients.matchAll({ type: 'window', includeUncontrolled: true })
    const existing = windows.find((client) => client.url.startsWith(self.location.origin))
    if (existing) {
      await existing.focus()
      if ('navigate' in existing) await existing.navigate(targetUrl)
      return
    }
    await self.clients.openWindow(targetUrl)
  })())
})
