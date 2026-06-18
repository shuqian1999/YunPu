import request from '../utils/request'

// 获取与"我"的所有关系
export const getRelationsToMe = () => {
  return request({
    url: '/family/relations/to-me',
    method: 'get'
  })
}

// 按代差分组获取所有与"我"相关的人物
export const getRelationsGrouped = () => {
  return request({
    url: '/family/relations/grouped',
    method: 'get'
  })
}

// 创建家庭关系（父母子女）
export const createFamilyRelation = (personAId, personBId, relation, relationNature = 0) => {
  return request({
    url: '/family/relation/family',
    method: 'post',
    params: {
      person_a_id: personAId,
      person_b_id: personBId,
      relation: relation,
      relation_nature: relationNature
    }
  })
}

// 创建配偶关系
export const createSpouseRelation = (personAId, personBId, relation, relationNature = 0) => {
  return request({
    url: '/family/relation/spouse',
    method: 'post',
    params: {
      person_a_id: personAId,
      person_b_id: personBId,
      relation: relation,
      relation_nature: relationNature
    }
  })
}

// 删除家庭关系
export const deleteFamilyRelation = (personAId, personBId) => {
  return request({
    url: '/family/relation/family',
    method: 'delete',
    params: {
      person_a_id: personAId,
      person_b_id: personBId
    }
  })
}

// 删除配偶关系
export const deleteSpouseRelation = (personAId, personBId) => {
  return request({
    url: '/family/relation/spouse',
    method: 'delete',
    params: {
      person_a_id: personAId,
      person_b_id: personBId
    }
  })
}

// 获取关系枚举值
export const getRelationEnums = () => {
  return request({
    url: '/family/enums',
    method: 'get'
  })
}

// 获取关系性质标签
export const getRelationNatureLabel = (nature) => {
  // 家庭关系性质
  const familyNatureLabels = {
    0: '亲',
    1: '继',
    2: '养',
    3: '义',
    4: '干'
  }
  return familyNatureLabels[nature] || '亲'
}
