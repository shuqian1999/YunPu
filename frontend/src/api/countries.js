import request from '@/utils/request'

export const getCountries = () => {
  return request.get('/countries')
}