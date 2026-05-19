import request from '../utils/request'

export const getEventTypes = () => {
  return request.get('/event-types')
}