# -*- coding: utf-8 -*-
"""
亲属称谓规则表引擎金标准测试（阶段1）

不依赖数据库：用 SimpleNamespace 构造内存图 (persons, parents_of,
children_of, spouses_of)，直接驱动 resolve_kinship 与
FamilyService._choose_relation。

运行方式（cwd=backend）：
    python -m pytest tests/test_kinship_rules.py
或：
    python tests/test_kinship_rules.py
"""
import os
import sys
from collections import defaultdict
from datetime import date
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.enums.relation_enums import (  # noqa: E402
    FamilyRelationType as F,
    SpouseRelationType as S,
    SpouseRelationNature as EXN,
)
from app.services import kinship_rules as kr  # noqa: E402
from app.services.family_service import FamilyService  # noqa: E402

U, D, M = kr.U, kr.D, kr.M
BIO = 0

# ----------------------------------------------------------------------
# 构造人物（1..99 全部存在，未列出的性别默认为女）
# ----------------------------------------------------------------------
MALE_IDS = {
    1, 2, 4, 6, 8, 9, 11, 13, 15, 17, 22, 24, 25, 26, 29, 31, 34, 35, 37,
    42, 44, 47, 48, 50, 53, 54, 56, 58, 60, 61, 62, 67, 69, 71, 72, 75,
    77, 78, 79, 80, 82, 85, 88, 89, 91, 92, 93, 97, 98,
}
BIRTHS = {
    1: date(1990, 1, 1), 2: date(1960, 1, 1), 3: date(1962, 1, 1),
    8: date(1958, 1, 1), 9: date(1965, 1, 1), 10: date(1963, 1, 1),
    11: date(1961, 1, 1), 12: date(1964, 1, 1), 13: date(1988, 1, 1),
    14: date(1992, 1, 1), 19: date(1991, 1, 1), 31: date(1988, 1, 1),
    32: date(1995, 1, 1), 35: date(1985, 1, 1), 37: date(1995, 1, 1),
    38: date(1995, 1, 1), 61: date(1955, 1, 1), 62: date(1965, 1, 1),
    85: date(1995, 1, 1), 87: date(1988, 1, 1),
}

PEOPLE = {
    i: SimpleNamespace(
        id=i,
        gender=1 if i in MALE_IDS else 2,
        birth_date=BIRTHS.get(i),
    )
    for i in range(1, 100)
}

# ----------------------------------------------------------------------
# 亲子边（parent, nature, 父母角色），children_of 由其派生
# ----------------------------------------------------------------------
PARENTS: dict = {
    1: [(2, BIO, F.FATHER), (3, BIO, F.MOTHER)],
    2: [(4, BIO, F.FATHER), (5, BIO, F.MOTHER)],
    3: [(6, BIO, F.FATHER), (7, BIO, F.MOTHER)],
    8: [(4, BIO, F.FATHER), (5, BIO, F.MOTHER)],
    9: [(4, BIO, F.FATHER), (5, BIO, F.MOTHER)],
    10: [(4, BIO, F.FATHER), (5, BIO, F.MOTHER)],
    11: [(6, BIO, F.FATHER), (7, BIO, F.MOTHER)],
    12: [(6, BIO, F.FATHER), (7, BIO, F.MOTHER)],
    61: [(6, BIO, F.FATHER), (7, BIO, F.MOTHER)],
    62: [(6, BIO, F.FATHER), (7, BIO, F.MOTHER)],
    63: [(6, BIO, F.FATHER), (7, BIO, F.MOTHER)],
    13: [(2, BIO, F.FATHER), (3, BIO, F.MOTHER)],
    14: [(2, BIO, F.FATHER), (3, BIO, F.MOTHER)],
    15: [(1, BIO, F.FATHER), (19, BIO, F.MOTHER)],
    16: [(1, BIO, F.FATHER), (19, BIO, F.MOTHER)],
    17: [(15, BIO, F.FATHER), (23, BIO, F.MOTHER)],
    52: [(15, BIO, F.FATHER), (23, BIO, F.MOTHER)],
    28: [(17, BIO, F.FATHER)],
    18: [(16, BIO, F.MOTHER), (24, BIO, F.FATHER)],
    54: [(16, BIO, F.MOTHER), (24, BIO, F.FATHER)],
    25: [(19, BIO, F.MOTHER), (97, BIO, F.FATHER)],
    35: [(8, BIO, F.FATHER), (40, BIO, F.MOTHER)],
    85: [(8, BIO, F.FATHER), (40, BIO, F.MOTHER)],
    19: [(11, BIO, F.FATHER), (43, BIO, F.MOTHER)],
    31: [(11, BIO, F.FATHER), (43, BIO, F.MOTHER)],
    32: [(11, BIO, F.FATHER), (43, BIO, F.MOTHER)],
    37: [(11, BIO, F.FATHER), (43, BIO, F.MOTHER)],
    38: [(11, BIO, F.FATHER), (43, BIO, F.MOTHER)],
    71: [(11, BIO, F.FATHER), (43, BIO, F.MOTHER)],
    74: [(11, BIO, F.FATHER), (43, BIO, F.MOTHER)],
    87: [(11, BIO, F.FATHER), (43, BIO, F.MOTHER)],
    29: [(13, BIO, F.FATHER), (33, BIO, F.MOTHER)],
    46: [(13, BIO, F.FATHER), (33, BIO, F.MOTHER)],
    30: [(14, BIO, F.MOTHER), (34, BIO, F.FATHER)],
    48: [(14, BIO, F.MOTHER), (34, BIO, F.FATHER)],
    72: [(71, BIO, F.FATHER)],
    73: [(71, BIO, F.FATHER)],
    75: [(74, BIO, F.MOTHER), (79, BIO, F.FATHER)],
    76: [(74, BIO, F.MOTHER), (79, BIO, F.FATHER)],
    43: [(67, BIO, F.FATHER), (68, BIO, F.MOTHER)],
    69: [(67, BIO, F.FATHER), (68, BIO, F.MOTHER)],
    70: [(67, BIO, F.FATHER), (68, BIO, F.MOTHER)],
    58: [(98, BIO, F.FATHER), (59, BIO, F.MOTHER)],
    77: [(98, BIO, F.FATHER), (59, BIO, F.MOTHER)],
    80: [(98, BIO, F.FATHER), (59, BIO, F.MOTHER)],
    78: [(77, BIO, F.FATHER)],
    56: [(82, BIO, F.FATHER), (83, BIO, F.MOTHER)],
    6: [(92, BIO, F.FATHER), (99, BIO, F.MOTHER)],
    90: [(91, BIO, F.FATHER), (96, BIO, F.MOTHER)],
}

PARENTS_OF = defaultdict(list)
CHILDREN_OF = defaultdict(list)
for child, plist in PARENTS.items():
    for pid, nature, role in plist:
        PARENTS_OF[child].append((pid, nature, role))
        CHILDREN_OF[pid].append((child, nature, role))


def sp(other, role, nature=0, start=None, end=None, row=0):
    return (other, role, nature, start, end, row)


SPOUSES_OF = defaultdict(list)
SPOUSES_OF[1].extend([
    sp(19, S.WIFE, 0, row=1),
    sp(90, S.WIFE, EXN.EX, row=3),
])
SPOUSES_OF[19].append(sp(1, S.HUSBAND, 0, row=2))
SPOUSES_OF[90].append(sp(1, S.HUSBAND, EXN.EX, row=4))
SPOUSES_OF[3].append(sp(22, S.HUSBAND, 0))
SPOUSES_OF[15].append(sp(23, S.WIFE, 0))
SPOUSES_OF[16].append(sp(24, S.HUSBAND, 0))
SPOUSES_OF[57].append(sp(58, S.HUSBAND, 0))
SPOUSES_OF[58].append(sp(57, S.WIFE, 0))

GRAPH = (PEOPLE, PARENTS_OF, CHILDREN_OF, SPOUSES_OF)


def name(steps, ego=1):
    return kr.resolve_kinship(steps, ego, GRAPH)["relation_name"]


# ----------------------------------------------------------------------
# 金标准用例（steps, 期望称谓）—— 含阶段0 的全部平移用例
# ----------------------------------------------------------------------
CASES = [
    # 一跳
    ([(U, BIO, F.FATHER, 2)], "父亲"),
    ([(U, BIO, F.MOTHER, 3)], "母亲"),
    ([(U, 1, F.FATHER, 2)], "继父"),
    ([(U, 2, F.MOTHER, 3)], "养母"),
    ([(U, 4, F.FATHER, 2)], "干爹"),
    ([(D, BIO, F.FATHER, 15)], "儿子"),
    ([(D, BIO, F.MOTHER, 16)], "女儿"),
    ([(D, 1, F.FATHER, 15)], "继子"),
    ([(M, 0, S.WIFE, 19)], "妻子"),
    ([(M, EXN.EX, S.WIFE, 90)], "前妻"),
    # 两跳：祖辈/兄弟姐妹/孙辈
    ([(U, 0, F.FATHER, 2), (U, 0, F.FATHER, 4)], "祖父"),
    ([(U, 0, F.FATHER, 2), (U, 0, F.MOTHER, 5)], "祖母"),
    ([(U, 0, F.MOTHER, 3), (U, 0, F.FATHER, 6)], "外祖父"),
    ([(U, 0, F.MOTHER, 3), (U, 0, F.MOTHER, 7)], "外祖母"),
    ([(U, 0, F.FATHER, 2), (D, 0, F.FATHER, 13)], "兄弟"),
    ([(U, 0, F.FATHER, 2), (D, 0, F.MOTHER, 14)], "姐妹"),
    ([(D, 0, F.FATHER, 15), (D, 0, F.FATHER, 17)], "孙子"),
    ([(D, 0, F.MOTHER, 16), (D, 0, F.FATHER, 54)], "外孙"),
    ([(D, 0, F.MOTHER, 16), (D, 0, F.MOTHER, 18)], "外孙女"),
    # 两跳：姻亲
    ([(M, 0, S.WIFE, 19), (U, 0, F.FATHER, 11)], "岳父"),
    ([(M, 0, S.WIFE, 19), (U, 0, F.MOTHER, 43)], "岳母"),
    ([(U, 0, F.MOTHER, 3), (M, 0, S.HUSBAND, 22)], "继父"),
    ([(U, 0, F.FATHER, 2), (M, 0, S.WIFE, 3)], "母亲"),
    ([(D, 0, F.FATHER, 15), (M, 0, S.WIFE, 23)], "儿媳"),
    ([(D, 0, F.MOTHER, 16), (M, 0, S.HUSBAND, 24)], "女婿"),
    ([(M, 0, S.WIFE, 19), (D, 0, F.MOTHER, 25)], "继子"),
    ([(M, 0, S.WIFE, 19), (D, 0, F.FATHER, 15)], "儿子"),
    ([(D, 0, F.FATHER, 15), (U, 0, F.MOTHER, 19)], "妻子"),
    # 三跳
    ([(U, 0, F.FATHER, 2), (U, 0, F.FATHER, 4), (U, 0, F.FATHER, 26)], "曾祖父"),
    ([(D, 0, F.FATHER, 15), (D, 0, F.FATHER, 17), (D, 0, F.MOTHER, 28)], "曾孙女"),
    ([(U, 0, F.FATHER, 2), (U, 0, F.FATHER, 4), (D, 0, F.FATHER, 8)], "伯伯"),
    ([(U, 0, F.FATHER, 2), (U, 0, F.FATHER, 4), (D, 0, F.FATHER, 9)], "叔叔"),
    ([(U, 0, F.FATHER, 2), (U, 0, F.FATHER, 4), (D, 0, F.MOTHER, 10)], "姑姑"),
    ([(U, 0, F.MOTHER, 3), (U, 0, F.MOTHER, 7), (D, 0, F.FATHER, 11)], "舅舅"),
    ([(U, 0, F.MOTHER, 3), (U, 0, F.MOTHER, 7), (D, 0, F.MOTHER, 12)], "姨"),
    ([(U, 0, F.FATHER, 2), (D, 0, F.FATHER, 13), (D, 0, F.FATHER, 29)], "侄子"),
    ([(U, 0, F.FATHER, 2), (D, 0, F.MOTHER, 14), (D, 0, F.MOTHER, 30)], "外甥女"),
    ([(U, 0, F.FATHER, 2), (M, 0, S.WIFE, 93), (U, 0, F.MOTHER, 94)], "外祖母"),
    ([(U, 0, F.FATHER, 2), (U, 0, F.FATHER, 4), (M, 0, S.HUSBAND, 95)], "祖母"),
    ([(M, 0, S.WIFE, 19), (U, 0, F.FATHER, 11), (D, 0, F.FATHER, 31)], "大舅子"),
    ([(M, 0, S.WIFE, 19), (U, 0, F.FATHER, 11), (D, 0, F.MOTHER, 32)], "小姨子"),
    ([(U, 0, F.FATHER, 2), (D, 0, F.FATHER, 13), (M, 0, S.WIFE, 33)], "嫂子"),
    ([(U, 0, F.FATHER, 2), (D, 0, F.MOTHER, 14), (M, 0, S.HUSBAND, 34)], "妹夫"),
    # 三跳：孙辈配偶 / 配偶祖辈 / 亲家
    ([(D, 0, F.FATHER, 15), (D, 0, F.FATHER, 17), (M, 0, S.WIFE, 51)], "孙媳妇"),
    ([(D, 0, F.FATHER, 15), (D, 0, F.MOTHER, 52), (M, 0, S.HUSBAND, 53)], "孙女婿"),
    ([(D, 0, F.MOTHER, 16), (D, 0, F.FATHER, 54), (M, 0, S.WIFE, 55)], "外孙媳妇"),
    ([(D, 0, F.MOTHER, 16), (D, 0, F.MOTHER, 18), (M, 0, S.HUSBAND, 56)], "外孙女婿"),
    ([(M, 0, S.WIFE, 19), (U, 0, F.FATHER, 11), (U, 0, F.FATHER, 6)], "岳祖父"),
    ([(M, 0, S.WIFE, 19), (U, 0, F.FATHER, 11), (U, 0, F.MOTHER, 7)], "岳祖母"),
    ([(D, 0, F.MOTHER, 16), (M, 0, S.HUSBAND, 56), (U, 0, F.FATHER, 82)], "亲家公"),
    ([(D, 0, F.MOTHER, 16), (M, 0, S.HUSBAND, 56), (U, 0, F.MOTHER, 83)], "亲家母"),
    # 四跳：堂表
    ([(U, 0, F.FATHER, 2), (U, 0, F.FATHER, 4), (D, 0, F.FATHER, 8), (D, 0, F.FATHER, 35)], "堂兄"),
    ([(U, 0, F.FATHER, 2), (U, 0, F.FATHER, 4), (D, 0, F.FATHER, 8), (D, 0, F.FATHER, 85)], "堂弟"),
    ([(U, 0, F.MOTHER, 3), (U, 0, F.MOTHER, 7), (D, 0, F.FATHER, 11), (D, 0, F.FATHER, 37)], "表弟"),
    ([(U, 0, F.MOTHER, 3), (U, 0, F.MOTHER, 7), (D, 0, F.FATHER, 11), (D, 0, F.MOTHER, 38)], "表妹"),
    # 四跳：叔伯姑舅姨的配偶
    ([(U, 0, F.FATHER, 2), (U, 0, F.FATHER, 4), (D, 0, F.FATHER, 8), (M, 0, S.WIFE, 40)], "伯母"),
    ([(U, 0, F.FATHER, 2), (U, 0, F.FATHER, 4), (D, 0, F.FATHER, 9), (M, 0, S.WIFE, 41)], "婶母"),
    ([(U, 0, F.FATHER, 2), (U, 0, F.FATHER, 4), (D, 0, F.MOTHER, 10), (M, 0, S.HUSBAND, 42)], "姑父"),
    ([(U, 0, F.MOTHER, 3), (U, 0, F.MOTHER, 7), (D, 0, F.FATHER, 11), (M, 0, S.WIFE, 43)], "舅母"),
    ([(U, 0, F.MOTHER, 3), (U, 0, F.MOTHER, 7), (D, 0, F.MOTHER, 12), (M, 0, S.HUSBAND, 44)], "姨父"),
    # 四跳：侄甥配偶
    ([(U, 0, F.FATHER, 2), (D, 0, F.FATHER, 13), (D, 0, F.FATHER, 29), (M, 0, S.WIFE, 45)], "侄媳妇"),
    ([(U, 0, F.FATHER, 2), (D, 0, F.FATHER, 13), (D, 0, F.MOTHER, 46), (M, 0, S.HUSBAND, 47)], "侄女婿"),
    ([(U, 0, F.FATHER, 2), (D, 0, F.MOTHER, 14), (D, 0, F.FATHER, 48), (M, 0, S.WIFE, 49)], "外甥媳妇"),
    ([(U, 0, F.FATHER, 2), (D, 0, F.MOTHER, 14), (D, 0, F.MOTHER, 30), (M, 0, S.HUSBAND, 50)], "外甥女婿"),
    # 四跳：配偶的叔伯姑舅姨
    ([(M, 0, S.WIFE, 19), (U, 0, F.FATHER, 11), (U, 0, F.FATHER, 6), (D, 0, F.FATHER, 61)], "岳伯"),
    ([(M, 0, S.WIFE, 19), (U, 0, F.FATHER, 11), (U, 0, F.FATHER, 6), (D, 0, F.FATHER, 62)], "岳叔"),
    ([(M, 0, S.WIFE, 19), (U, 0, F.FATHER, 11), (U, 0, F.FATHER, 6), (D, 0, F.MOTHER, 63)], "岳姑"),
    ([(M, 0, S.WIFE, 19), (U, 0, F.MOTHER, 43), (U, 0, F.MOTHER, 68), (D, 0, F.FATHER, 69)], "岳舅"),
    # 四跳：配偶的侄甥
    ([(M, 0, S.WIFE, 19), (U, 0, F.FATHER, 11), (D, 0, F.FATHER, 71), (D, 0, F.FATHER, 72)], "内侄"),
    ([(M, 0, S.WIFE, 19), (U, 0, F.FATHER, 11), (D, 0, F.FATHER, 71), (D, 0, F.MOTHER, 73)], "内侄女"),
    ([(M, 0, S.WIFE, 19), (U, 0, F.FATHER, 11), (D, 0, F.MOTHER, 74), (D, 0, F.FATHER, 75)], "内甥"),
    ([(M, 0, S.WIFE, 19), (U, 0, F.FATHER, 11), (D, 0, F.MOTHER, 74), (D, 0, F.MOTHER, 76)], "内甥女"),
    # 四跳：连襟/妯娌（女 ego）
    ([(M, 0, S.WIFE, 19), (U, 0, F.FATHER, 11), (D, 0, F.MOTHER, 74), (M, 0, S.HUSBAND, 79)], "连襟"),
    ([(M, 0, S.HUSBAND, 58), (U, 0, F.MOTHER, 59), (D, 0, F.FATHER, 80), (M, 0, S.WIFE, 81)], "妯娌", 57),
    # 女 ego：丈夫的侄子随夫家称
    ([(M, 0, S.HUSBAND, 58), (U, 0, F.MOTHER, 59), (D, 0, F.FATHER, 77), (D, 0, F.FATHER, 78)], "侄子", 57),
    # 五跳：堂表兄弟姐妹的配偶
    ([(U, 0, F.FATHER, 2), (U, 0, F.FATHER, 4), (D, 0, F.FATHER, 8), (D, 0, F.FATHER, 35), (M, 0, S.WIFE, 84)], "堂嫂"),
    ([(U, 0, F.FATHER, 2), (U, 0, F.FATHER, 4), (D, 0, F.FATHER, 8), (D, 0, F.FATHER, 85), (M, 0, S.WIFE, 86)], "堂弟妹"),
    ([(U, 0, F.MOTHER, 3), (U, 0, F.MOTHER, 7), (D, 0, F.FATHER, 11), (D, 0, F.MOTHER, 87), (M, 0, S.HUSBAND, 88)], "表姐夫"),
    ([(U, 0, F.MOTHER, 3), (U, 0, F.MOTHER, 7), (D, 0, F.FATHER, 11), (D, 0, F.MOTHER, 38), (M, 0, S.HUSBAND, 89)], "表妹夫"),
    # 前任姻亲前缀 / 组合称谓
    ([(M, EXN.EX, S.WIFE, 90), (U, 0, F.FATHER, 91)], "前岳父"),
    ([(M, 0, S.WIFE, 19), (U, 0, F.FATHER, 11), (U, 0, F.FATHER, 6), (U, 0, F.FATHER, 92)], "妻子的曾祖父"),
    ([(M, EXN.EX, S.WIFE, 90), (U, 0, F.FATHER, 91), (U, 0, F.FATHER, 60), (U, 0, F.FATHER, 92)], "前妻的曾祖父"),
    ([(M, 0, S.HUSBAND, 58), (U, 0, F.FATHER, 98), (U, 0, F.FATHER, 60)], "丈夫的祖父", 57),
]

# ----------------------------------------------------------------------
# level / is_blood 代表断言
# #
# ----------------------------------------------------------------------
LEVEL_BLOOD_CASES = [
    ([(M, 0, S.WIFE, 19)], 0, False),
    ([(M, 0, S.WIFE, 19), (U, 0, F.FATHER, 11)], 1, False),
    ([(U, 0, F.FATHER, 2), (D, 0, F.MOTHER, 14), (M, 0, S.HUSBAND, 34)], 0, False),
    ([(U, 0, F.FATHER, 2), (D, 0, F.FATHER, 13), (D, 0, F.FATHER, 29), (M, 0, S.WIFE, 45)], -1, False),
    ([(U, 0, F.MOTHER, 3), (U, 0, F.MOTHER, 7), (D, 0, F.FATHER, 11), (D, 0, F.FATHER, 37)], 0, True),
    ([(D, 0, F.MOTHER, 16), (M, 0, S.HUSBAND, 56), (U, 0, F.FATHER, 82)], 0, False),
    ([(U, 0, F.FATHER, 2), (U, 0, F.FATHER, 4), (U, 0, F.FATHER, 26)], 3, True),
    ([(D, 1, F.FATHER, 15)], -1, False),
]


def test_all_kinship_titles():
    failures = []
    for case in CASES:
        steps, expected = case[0], case[1]
        ego = case[2] if len(case) > 2 else 1
        got = name(steps, ego)
        if got != expected:
            failures.append(f"expect={expected:<6} got={got:<6} steps={steps}")
    assert not failures, "\n".join(failures)


def test_level_and_blood():
    failures = []
    for steps, exp_level, exp_blood in LEVEL_BLOOD_CASES:
        info = kr.resolve_kinship(steps, 1, GRAPH)
        if info["level"] != exp_level or info["is_blood"] != exp_blood:
            failures.append(
                f"{steps}: expect level={exp_level} blood={exp_blood}, "
                f"got level={info['level']} blood={info['is_blood']}"
            )
    assert not failures, "\n".join(failures)


def test_multi_identity_wife_and_cousin():
    """妻子同时是表妹：主称谓=妻子（一跳），备用称谓含表妹（血亲路径）"""
    persons = {i: PEOPLE[i] for i in (1, 3, 7, 11, 19)}
    p_of = defaultdict(list)
    c_of = defaultdict(list)
    # 1 -> 母3 -> 外祖母7 -> 舅舅11 -> 女19
    p_of[3] = [(7, BIO, F.MOTHER)]
    c_of[7] = [(11, BIO, F.MOTHER)]
    p_of[11] = [(7, BIO, F.MOTHER)]
    c_of[11] = [(19, BIO, F.FATHER)]
    p_of[19] = [(11, BIO, F.FATHER)]
    s_of = defaultdict(list)
    s_of[1] = [sp(19, S.WIFE, 0, row=1)]
    s_of[19] = [sp(1, S.HUSBAND, 0, row=2)]
    mini = (persons, p_of, c_of, s_of)

    svc = FamilyService.__new__(FamilyService)
    candidates = [
        [(M, 0, S.WIFE, 19)],
        [(U, BIO, F.MOTHER, 3), (U, BIO, F.MOTHER, 7),
         (D, BIO, F.MOTHER, 11), (D, BIO, F.FATHER, 19)],
    ]
    result = svc._choose_relation(candidates, 1, mini)
    assert result["relation_name"] == "妻子", result
    assert "表妹" in result["alt_relation_names"], result
    assert result["is_blood"] is False  # 主称谓是配偶，非血亲


def test_enumerate_finds_both_paths():
    """端到端枚举：内存图中 1 -> 19 同时存在婚姻路径与表亲路径"""
    svc = FamilyService.__new__(FamilyService)
    paths = svc._enumerate_paths(1, 19, GRAPH)
    kind_sets = {tuple(s[0] for s in p) for p in paths}
    assert (M,) in kind_sets
    assert (U, U, D, D) in kind_sets


if __name__ == "__main__":
    test_all_kinship_titles()
    test_level_and_blood()
    test_multi_identity_wife_and_cousin()
    test_enumerate_finds_both_paths()
    print(f"ALL GOLDEN CASES PASSED: {len(CASES)} title cases + "
          f"{len(LEVEL_BLOOD_CASES)} level/blood + multi-identity")
