import request from '../utils/request'

// ============= 配置 =============
export const getEmailConfig = () => {
  return request({
    url: '/email/config',
    method: 'get'
  })
}

export const updateEmailConfig = (data) => {
  return request({
    url: '/email/config',
    method: 'put',
    data
  })
}

export const testEmailConnection = () => {
  return request({
    url: '/email/test-connection',
    method: 'post'
  })
}

export const testEmailSend = (receiver) => {
  return request({
    url: '/email/test-send',
    method: 'post',
    data: { receiver }
  })
}

export const sendEmailNow = (params) => {
  return request({
    url: '/email/send-now',
    method: 'post',
    data: params
  })
}

// ============= 模板 =============
export const listEmailTemplates = () => {
  return request({
    url: '/email/templates',
    method: 'get'
  })
}

export const getEmailTemplate = (id) => {
  return request({
    url: `/email/templates/${id}`,
    method: 'get'
  })
}

export const createEmailTemplate = (data) => {
  return request({
    url: '/email/templates',
    method: 'post',
    data
  })
}

export const updateEmailTemplate = (id, data) => {
  return request({
    url: `/email/templates/${id}`,
    method: 'put',
    data
  })
}

export const deleteEmailTemplate = (id) => {
  return request({
    url: `/email/templates/${id}`,
    method: 'delete'
  })
}

export const previewEmailTemplate = (id, sampleType = 'event') => {
  return request({
    url: `/email/templates/${id}/preview`,
    method: 'post',
    data: { sample_type: sampleType }
  })
}

// ============= 日志 =============
export const listEmailLogs = (limit = 50) => {
  return request({
    url: '/email/logs',
    method: 'get',
    params: { limit }
  })
}

export const clearEmailLogs = () => {
  return request({
    url: '/email/logs',
    method: 'delete'
  })
}
