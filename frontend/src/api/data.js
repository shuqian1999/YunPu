import request from '../utils/request'

export const exportDataJson = () => {
  return request({
    url: '/data/export/json',
    method: 'get',
    responseType: 'blob'
  })
}

export const exportDataCsv = () => {
  return request({
    url: '/data/export/csv',
    method: 'get',
    responseType: 'blob'
  })
}

export const importDataJson = (file) => {
  const formData = new FormData()
  formData.append('file', file)
  return request({
    url: '/data/import/json',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}