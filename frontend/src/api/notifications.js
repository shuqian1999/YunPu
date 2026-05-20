import request from '../utils/request'

export const getNotifications = (skip = 0, limit = 50) => {
  return request({
    url: '/notifications',
    method: 'get',
    params: { skip, limit }
  })
}

export const getUnreadCount = () => {
  return request({
    url: '/notifications/unread-count',
    method: 'get'
  })
}

export const markAsRead = (notificationId) => {
  return request({
    url: `/notifications/${notificationId}/read`,
    method: 'put'
  })
}

export const markAllAsRead = () => {
  return request({
    url: '/notifications/read-all',
    method: 'put'
  })
}

export const deleteNotification = (notificationId) => {
  return request({
    url: `/notifications/${notificationId}`,
    method: 'delete'
  })
}
