import request from '../utils/request'

export const getUserSettings = () => {
  return request({
    url: '/settings/user',
    method: 'get'
  })
}

export const updateUserSettings = (settings) => {
  return request({
    url: '/settings/user',
    method: 'put',
    data: settings
  })
}

export const changePassword = (oldPassword, newPassword) => {
  return request({
    url: '/settings/change-password',
    method: 'post',
    params: {
      old_password: oldPassword,
      new_password: newPassword
    }
  })
}

export const getSystemSettings = () => {
  return request({
    url: '/settings/system',
    method: 'get'
  })
}