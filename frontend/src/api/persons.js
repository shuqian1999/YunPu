import request from '../utils/request'

export const getPersons = (params = {}) => {
  return request.get('/persons', { params })
}

export const getPerson = (id) => {
  return request.get(`/persons/${id}`)
}

export const createPerson = (data) => {
  return request.post('/persons', data)
}

export const updatePerson = (id, data) => {
  return request.put(`/persons/${id}`, data)
}

export const deletePerson = (id) => {
  return request.delete(`/persons/${id}`)
}

export const getPersonEvents = (id) => {
  return request.get(`/persons/${id}/events`)
}

export const getPersonReminders = (id) => {
  return request.get(`/persons/${id}/reminders`)
}

export const getPersonRelations = (id) => {
  return request.get(`/persons/${id}/relations`)
}