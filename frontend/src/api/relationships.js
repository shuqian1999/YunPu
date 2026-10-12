import request from '../utils/request'

/**
 * 全局关系图
 * @param {Object} params
 * @param {string[]} params.types 边类型 family/spouse/social/group/tag
 * @param {number} [params.importanceMin] 最低人物重要度（节点级 1-5）
 * @param {boolean} [params.aliveOnly] 仅在世
 * @param {string} [params.keyword] 姓名关键词
 */
export const getRelationshipGraph = (params = {}) => {
  const { types = ['family', 'spouse', 'social', 'group'], importanceMin, aliveOnly, keyword } = params
  return request({
    url: '/relationships/graph',
    method: 'get',
    params: {
      types: types.join(','),
      importance_min: importanceMin || 0,
      alive_only: aliveOnly ? true : undefined,
      keyword: keyword || undefined
    }
  })
}

// 以某人为中心的一级关系网络
export const getEgoNetwork = (personId) => {
  return request({
    url: `/relationships/ego/${personId}`,
    method: 'get'
  })
}
