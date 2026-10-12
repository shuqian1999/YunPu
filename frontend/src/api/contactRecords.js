import request from '../utils/request'

export const getContactRecords = (params = {}) => {
  return request.get('/contact-records', { params })
}

export const createContactRecord = (data) => {
  return request.post('/contact-records', data)
}

export const updateContactRecord = (id, data) => {
  return request.put(`/contact-records/${id}`, data)
}

export const deleteContactRecord = (id) => {
  return request.delete(`/contact-records/${id}`)
}
