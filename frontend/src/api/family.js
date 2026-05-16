import request from '../utils/request'

export const getFamilyTree = () => {
  return request({
    url: '/family/tree',
    method: 'get'
  })
}

export const getCalculatedRelations = () => {
  return request({
    url: '/family/relations',
    method: 'get'
  })
}

export const recalculateRelations = () => {
  return request({
    url: '/family/recalculate',
    method: 'post'
  })
}

export const addFamilyMember = (personId) => {
  return request({
    url: '/family/member',
    method: 'post',
    params: { person_id: personId }
  })
}

export const addFamilyRelation = (parentPersonId, childPersonId, parentType, relationNature) => {
  return request({
    url: '/family/relation',
    method: 'post',
    params: {
      parent_person_id: parentPersonId,
      child_person_id: childPersonId,
      parent_type: parentType,
      relation_nature: relationNature
    }
  })
}