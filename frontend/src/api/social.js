import request from '../utils/request'

// ---------------------------------------------------------------------------
// 社会关系类型
// ---------------------------------------------------------------------------

export const getSocialTypes = () => {
  return request({ url: '/social/types', method: 'get' })
}

// payload: { name, directed, reverse_name?, color? }
export const createSocialType = (payload) => {
  return request({ url: '/social/types', method: 'post', data: payload })
}

export const updateSocialType = (typeId, payload) => {
  return request({ url: `/social/types/${typeId}`, method: 'put', data: payload })
}

export const deleteSocialType = (typeId) => {
  return request({ url: `/social/types/${typeId}`, method: 'delete' })
}

// ---------------------------------------------------------------------------
// 社会关系实例
// payload: {
//   person_a_id, person_b_id, type_id,
//   closeness?, start_date?(YYYY-MM-DD), end_date?, introducer_id?
// }
// ---------------------------------------------------------------------------

export const listSocialRelations = (personId) => {
  return request({
    url: '/social/relations',
    method: 'get',
    params: { person_id: personId }
  })
}

export const createSocialRelation = (payload) => {
  return request({ url: '/social/relations', method: 'post', data: payload })
}

export const updateSocialRelation = (relationId, payload) => {
  return request({
    url: `/social/relations/${relationId}`,
    method: 'put',
    data: payload
  })
}

export const deleteSocialRelation = (relationId) => {
  return request({ url: `/social/relations/${relationId}`, method: 'delete' })
}
