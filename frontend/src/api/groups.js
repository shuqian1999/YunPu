import request from '../utils/request'

export const getGroups = () => {
  return request({
    url: '/groups',
    method: 'get'
  })
}

export const createGroup = (group) => {
  return request({
    url: '/groups',
    method: 'post',
    data: group
  })
}

export const updateGroup = (groupId, group) => {
  return request({
    url: `/groups/${groupId}`,
    method: 'put',
    data: group
  })
}

export const deleteGroup = (groupId) => {
  return request({
    url: `/groups/${groupId}`,
    method: 'delete'
  })
}

export const addPersonToGroup = (groupId, personId) => {
  return request({
    url: `/groups/${groupId}/members/${personId}`,
    method: 'post'
  })
}

export const removePersonFromGroup = (groupId, personId) => {
  return request({
    url: `/groups/${groupId}/members/${personId}`,
    method: 'delete'
  })
}