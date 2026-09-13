import { apiRequest } from './client'

export const toSensorEvent = (event) => ({
  id: event.id,
  personId: event.person_id,
  sensorId: event.sensor_id,
  detectedAt: event.detected_at,
  detectedValue: event.detected_value,
  sensorStatus: event.sensor_status,
  receivedAt: event.received_at,
})

export async function getSensorEvents(personId) {
  const query = personId ? `?person_id=${personId}` : ''
  const events = await apiRequest(`/sensor-events${query}`)
  return events.map(toSensorEvent)
}
