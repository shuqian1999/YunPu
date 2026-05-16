import request from '../utils/request'

export const getEvents = (params = {}) => {
  return request.get('/events', { params })
}

export const getEvent = (id) => {
  return request.get(`/events/${id}`)
}

export const createEvent = (data) => {
  return request.post('/events', data)
}

export const updateEvent = (id, data) => {
  return request.put(`/events/${id}`, data)
}

export const deleteEvent = (id) => {
  return request.delete(`/events/${id}`)
}