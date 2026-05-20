import request from '../utils/request'

// 获取家族树
export const getFamilyTree = () => {
  return request({
    url: '/family/tree',
    method: 'get'
  })
}

// 获取与"我"的所有关系
export const getRelationsToMe = () => {
  return request({
    url: '/family/relations/to-me',
    method: 'get'
  })
}

// 计算两人之间的关系
export const getRelationBetween = (personAId, personBId) => {
  return request({
    url: '/family/relations/between',
    method: 'get',
    params: {
      person_a_id: personAId,
      person_b_id: personBId
    }
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

// 关系类型常量
export const RelationTypes = {
  // 家庭关系类型
  FAMILY: {
    FATHER: 0,  // 父
    MOTHER: 1,  // 母
    SON: 2,     // 子
    DAUGHTER: 3 // 女
  },
  // 关系性质
  NATURE: {
    BIOLOGICAL: 0, // 亲
    STEP: 1,       // 继
    ADOPTIVE: 2,   // 养
    SWORN: 3,      // 义
    FOSTER: 4      // 干
  },
  // 配偶关系类型
  SPOUSE: {
    HUSBAND: 0,    // 丈夫
    WIFE: 1,       // 妻子
    CONCUBINE: 2,  // 姨太太/妾
    BOYFRIEND: 3,  // 男朋友
    GIRLFRIEND: 4  // 女朋友
  },
  // 配偶关系性质
  SPOUSE_NATURE: {
    CURRENT: 0, // 现任
    EX: 1      // 前任
  }
}

// 获取关系类型标签
export const getRelationTypeLabel = (type, isSpouse = false) => {
  if (isSpouse) {
    const spouseLabels = {
      0: '丈夫',
      1: '妻子',
      2: '姨太太',
      3: '男朋友',
      4: '女朋友'
    }
    return spouseLabels[type] || '未知'
  } else {
    const familyLabels = {
      0: '父',
      1: '母',
      2: '子',
      3: '女'
    }
    return familyLabels[type] || '未知'
  }
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
