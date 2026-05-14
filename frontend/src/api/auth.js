import request from '../utils/request'

export const login = (credentials) => {
  return request.post('/auth/login', credentials, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
  })
}
