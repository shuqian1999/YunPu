import request from '../utils/request'

export const searchPersons = (query, filters = {}) => {
  return request({
    url: '/search/persons',
    method: 'get',
    params: {
      query,
      ...filters
    }
  })
}