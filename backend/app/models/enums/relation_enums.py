from enum import IntEnum


class FamilyRelationType(IntEnum):
    """家庭关系类型"""
    FATHER = 0  # 父
    MOTHER = 1  # 母
    SON = 2     # 子
    DAUGHTER = 3  # 女


class RelationNature(IntEnum):
    """关系性质"""
    BIOLOGICAL = 0  # 亲（血亲）
    STEP = 1        # 继（继亲）
    ADOPTIVE = 2    # 养（收养）
    SWORN = 3       # 义（结义）
    FOSTER = 4      # 干（干亲/寄养）


class SpouseRelationType(IntEnum):
    """配偶关系类型"""
    HUSBAND = 0     # 丈夫
    WIFE = 1        # 妻子
    CONCUBINE = 2   # 姨太太/妾
    BOYFRIEND = 3   # 男朋友
    GIRLFRIEND = 4  # 女朋友


class SpouseRelationNature(IntEnum):
    """配偶关系性质"""
    CURRENT = 0  # 现任
    EX = 1      # 前任
