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
    """配偶关系类型（仅正式婚姻；男女朋友归社会关系类型「男朋友/女朋友」）"""
    HUSBAND = 0     # 丈夫
    WIFE = 1        # 妻子
    CONCUBINE = 2   # 姨太太/妾


class SpouseRelationNature(IntEnum):
    """配偶关系性质"""
    CURRENT = 0  # 现任
    EX = 1      # 前任


# ---------------------------------------------------------------------------
# 共享展示常量（family_service / relationship_service / API 统一引用，勿各自复制）
# ---------------------------------------------------------------------------

# 家庭关系性质：单字标签
NATURE_LABELS = {
    RelationNature.BIOLOGICAL: "亲",
    RelationNature.STEP: "继",
    RelationNature.ADOPTIVE: "养",
    RelationNature.SWORN: "义",
    RelationNature.FOSTER: "干",
}

# 亲子四角色的完整称谓（value -> 称谓）
FAMILY_ROLE_LABELS = {
    FamilyRelationType.FATHER: "父亲",
    FamilyRelationType.MOTHER: "母亲",
    FamilyRelationType.SON: "儿子",
    FamilyRelationType.DAUGHTER: "女儿",
}

# 配偶角色的完整称谓（value -> 称谓，与枚举值对应）
SPOUSE_ROLE_LABELS = {
    SpouseRelationType.HUSBAND: "丈夫",
    SpouseRelationType.WIFE: "妻子",
    SpouseRelationType.CONCUBINE: "姨太太",
}
