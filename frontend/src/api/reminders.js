import request from '../utils/request'

export const getReminders = (params = {}) => {
  return request.get('/reminders', { params })
}

export const getReminder = (id) => {
  return request.get(`/reminders/${id}`)
}

export const createReminder = (data) => {
  return request.post('/reminders', data)
}

export const updateReminder = (id, data) => {
  return request.put(`/reminders/${id}`, data)
}

export const deleteReminder = (id) => {
  return request.delete(`/reminders/${id}`)
}