import { apiRequest } from './client'

const toPerson = (person) => ({
  id: person.id,
  name: person.name,
  ageGroup: person.age_group || '',
  phone: person.phone || '',
  livingSpace: person.living_space,
  healthNotes: person.health_notes || '',
  monitoringStatus: person.monitoring_status,
})

export async function getPeople() {
  const people = await apiRequest('/people')
  return people.map(toPerson)
}

export async function createPerson(person) {
  const created = await apiRequest('/people', {
    method: 'POST',
    body: JSON.stringify({
      name: person.name,
      age_group: person.ageGroup || null,
      phone: person.phone || null,
      living_space: person.livingSpace,
      health_notes: person.healthNotes || null,
      monitoring_status: 'PAUSED',
    }),
  })
  return toPerson(created)
}

export async function updatePersonMonitoringStatus(personId, monitoringStatus) {
  const updated = await apiRequest(`/people/${personId}`, {
    method: 'PATCH',
    body: JSON.stringify({ monitoring_status: monitoringStatus }),
  })
  return toPerson(updated)
}

export async function updatePerson(personId, person) {
  const updated = await apiRequest(`/people/${personId}`, {
    method: 'PATCH',
    body: JSON.stringify({
      name: person.name,
      age_group: person.ageGroup || null,
      phone: person.phone || null,
      living_space: person.livingSpace,
      health_notes: person.healthNotes || null,
    }),
  })
  return toPerson(updated)
}

export async function deletePerson(personId) {
  await apiRequest(`/people/${personId}`, { method: 'DELETE' })
}
