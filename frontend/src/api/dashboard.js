import request from '../utils/request'

export const getDashboardStats = () => {
  return request.get('/dashboard/stats')
}

export const getDashboardEvents = (params = {}) => {
  return request.get('/dashboard/events', { params })
}

export const getDashboardReminders = (params = {}) => {
  return request.get('/dashboard/reminders', { params })
}