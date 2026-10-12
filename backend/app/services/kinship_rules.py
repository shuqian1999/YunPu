# -*- coding: utf-8 -*-
"""
亲属称谓规则表引擎（阶段1）

设计：
- 路径由原子步组成：U=上溯父母一代，D=下行子女一代，M=婚姻/伴侣
- 每条规则 = 路径模式（U/D/M 元组）+ 解析函数，RULES 按声明顺序匹配
- 解析函数只负责"这条路径该叫什么"，代差/血亲由引擎统一计算
- 未命中且以 M 开头的姻亲路径，回退为组合称谓"{妻子/前妻/...}的{自配偶视角称谓}"，
  其余未命中回退"远亲"（代差与血亲仍准确）
- 路径首步为前任婚姻时，对多跳姻亲结果统一前缀"前"
"""
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple

from app.models.enums.relation_enums import (
    FamilyRelationType, RelationNature,
    SpouseRelationType, SpouseRelationNature,
    SPOUSE_ROLE_LABELS,
)

U = "u"
D = "d"
M = "m"

MALE = 1
FEMALE = 2

# 一跳父母称谓（nature -> (男=父亲角色, 女=母亲角色)）
PARENT_TITLES: Dict[int, Tuple[str, str]] = {
    RelationNature.BIOLOGICAL: ("父亲", "母亲"),
    RelationNature.STEP: ("继父", "继母"),
    RelationNature.ADOPTIVE: ("养父", "养母"),
    RelationNature.SWORN: ("义父", "义母"),
    RelationNature.FOSTER: ("干爹", "干妈"),
}
# 一跳子女称谓（nature -> (男, 女)）
CHILD_TITLES: Dict[int, Tuple[str, str]] = {
    RelationNature.BIOLOGICAL: ("儿子", "女儿"),
    RelationNature.STEP: ("继子", "继女"),
    RelationNature.ADOPTIVE: ("养子", "养女"),
    RelationNature.SWORN: ("义子", "义女"),
    RelationNature.FOSTER: ("干儿子", "干女儿"),
}

_FATHER = FamilyRelationType.FATHER
_MOTHER = FamilyRelationType.MOTHER


def spouse_title(role: int, nature: int) -> str:
    """配偶一跳称谓（含前任特称）"""
    if nature == SpouseRelationNature.EX:
        ex_titles = {
            SpouseRelationType.HUSBAND: "前夫",
            SpouseRelationType.WIFE: "前妻",
        }
        return ex_titles.get(role, "前" + SPOUSE_ROLE_LABELS.get(role, "配偶"))
    return SPOUSE_ROLE_LABELS.get(role, "配偶")


@dataclass
class KinshipContext:
    steps: List[tuple]
    ego_id: int
    persons: dict
    parents_of: dict
    children_of: dict
    spouses_of: dict

    # ---- 基础派生 ----
    @property
    def kinds(self) -> tuple:
        return tuple(s[0] for s in self.steps)

    @property
    def target(self) -> int:
        return self.steps[-1][3]

    @property
    def level(self) -> int:
        return self.kinds.count(U) - self.kinds.count(D)

    @property
    def is_blood(self) -> bool:
        return M not in self.kinds and all(
            s[1] == RelationNature.BIOLOGICAL for s in self.steps
        )

    @property
    def lead_ex(self) -> bool:
        """路径首步是否经由前任配偶"""
        return bool(self.steps) and self.steps[0][0] == M \
            and self.steps[0][1] == SpouseRelationNature.EX

    # ---- 人物信息 ----
    def gender(self, pid) -> Optional[int]:
        p = self.persons.get(pid)
        if p and p.gender in (MALE, FEMALE):
            return p.gender
        return None

    def birth(self, pid):
        p = self.persons.get(pid)
        return p.birth_date if p else None

    def older(self, pid_a, pid_b) -> Optional[bool]:
        """pid_a 比 pid_b 年长 -> True；日期缺失 -> None"""
        da, db_ = self.birth(pid_a), self.birth(pid_b)
        if da and db_ and da != db_:
            return da < db_
        return None

    def gidx(self, pid) -> int:
        """性别转称谓下标：男 0 / 女 1"""
        return 0 if self.gender(pid) == MALE else 1

    # ---- 直接关系查询（供 U+M / D+M / M+D / D+U 消歧）----
    def direct_parent(self, child_id, parent_id):
        return next(
            (item for item in self.parents_of.get(child_id, []) if item[0] == parent_id),
            None,
        )

    def direct_child(self, parent_id, child_id):
        return next(
            (item for item in self.children_of.get(parent_id, []) if item[0] == child_id),
            None,
        )

    def direct_spouse(self, holder_id, other_id):
        # 邻接项：(other, role, nature, start, end, row_id)；现任优先
        cands = [
            item for item in self.spouses_of.get(holder_id, []) if item[0] == other_id
        ]
        if not cands:
            return None
        cands.sort(key=lambda it: (it[2], it[3] is None, it[3]))
        return cands[0]


# ----------------------------------------------------------------------
# 规则函数（每个返回称谓或 None）
# ----------------------------------------------------------------------

def _r_one_parent(ctx: KinshipContext):
    _, nature, role, _ = ctx.steps[0]
    return PARENT_TITLES.get(nature, PARENT_TITLES[0])[
        0 if role == _FATHER else 1
    ]


def _r_one_child(ctx: KinshipContext):
    _, nature, _, _ = ctx.steps[0]
    return CHILD_TITLES.get(nature, CHILD_TITLES[0])[ctx.gidx(ctx.target)]


def _r_one_spouse(ctx: KinshipContext):
    _, nature, role, _ = ctx.steps[0]
    return spouse_title(role, nature)


def _r_grandparent(ctx: KinshipContext):
    # 祖父母 / 外祖父母：按第一跳父系/母系
    if ctx.steps[0][2] == _FATHER:
        return ("祖父", "祖母")[ctx.gidx(ctx.target)]
    return ("外祖父", "外祖母")[ctx.gidx(ctx.target)]


def _r_sibling(ctx: KinshipContext):
    return ("兄弟", "姐妹")[ctx.gidx(ctx.target)]


def _r_grandchild(ctx: KinshipContext):
    # 第一个孩子是女儿 -> 外孙系
    first_child = ctx.steps[0][3]
    if ctx.gender(first_child) == FEMALE:
        return ("外孙", "外孙女")[ctx.gidx(ctx.target)]
    return ("孙子", "孙女")[ctx.gidx(ctx.target)]


def _r_spouse_parent(ctx: KinshipContext):
    # M + U：配偶的父母，按 ego 性别分岳父母/公婆
    ego_gender = ctx.gender(ctx.ego_id)
    if ego_gender == MALE:
        return ("岳父", "岳母")[ctx.gidx(ctx.target)]
    if ego_gender == FEMALE:
        return ("公公", "婆婆")[ctx.gidx(ctx.target)]
    return ("公公/岳父", "婆婆/岳母")[ctx.gidx(ctx.target)]


def _r_parent_spouse(ctx: KinshipContext):
    # U + M：父母的配偶；若本就是直接父/母则用直接称谓，否则继父母
    dp = ctx.direct_parent(ctx.ego_id, ctx.target)
    if dp:
        _, p_nature, p_role = dp
        return PARENT_TITLES.get(p_nature, PARENT_TITLES[0])[
            0 if p_role == _FATHER else 1
        ]
    return ("继父", "继母")[ctx.gidx(ctx.target)]


def _r_child_spouse(ctx: KinshipContext):
    # D + M：子女的配偶
    child = ctx.steps[0][3]
    cg, tg = ctx.gender(child), ctx.gender(ctx.target)
    if cg == MALE and tg == FEMALE:
        return "儿媳"
    if cg == FEMALE and tg == MALE:
        return "女婿"
    return "子女的配偶"


def _r_spouse_child(ctx: KinshipContext):
    # M + D：配偶的子女；同时是本人子女则直接用子女称谓，否则继子女
    dc = ctx.direct_child(ctx.ego_id, ctx.target)
    if dc:
        _, c_nature, _ = dc
        return CHILD_TITLES.get(c_nature, CHILD_TITLES[0])[ctx.gidx(ctx.target)]
    return ("继子", "继女")[ctx.gidx(ctx.target)]


def _r_child_other_parent(ctx: KinshipContext):
    # D + U：子女的另一方父母，一般即本人配偶
    ds = ctx.direct_spouse(ctx.ego_id, ctx.target)
    if ds:
        return spouse_title(ds[1], ds[2])
    return None


def _r_great_grandparent(ctx: KinshipContext):
    return ("曾祖父", "曾祖母")[0 if ctx.steps[2][2] == _FATHER else 1]


def _r_great_grandchild(ctx: KinshipContext):
    return ("曾孙", "曾孙女")[ctx.gidx(ctx.target)]


def _r_uncle_aunt(ctx: KinshipContext):
    # U + U + D：叔伯姑舅姨
    parent_side = ctx.steps[0][2]
    middle = ctx.steps[2][3]
    if parent_side == _FATHER:
        if ctx.gender(middle) == MALE:
            order = ctx.older(middle, ctx.steps[0][3])
            if order is True:
                return "伯伯"
            if order is False:
                return "叔叔"
            return "叔叔/伯伯"
        return "姑姑"
    if ctx.gender(middle) == MALE:
        return "舅舅"
    return "姨"


def _r_nephew(ctx: KinshipContext):
    # U + D + D：兄弟的孩子=侄，姐妹的孩子=甥
    sibling = ctx.steps[1][3]
    if ctx.gender(sibling) == MALE:
        return ("侄子", "侄女")[ctx.gidx(ctx.target)]
    if ctx.gender(sibling) == FEMALE:
        return ("外甥", "外甥女")[ctx.gidx(ctx.target)]
    return None


def _r_step_grandparent_via_parent(ctx: KinshipContext):
    # U + M + U：经继/另一方父母上溯的祖父母
    if ctx.steps[0][2] == _FATHER:
        return ("外祖父", "外祖母")[0 if ctx.steps[2][2] == _FATHER else 1]
    return ("祖父", "祖母")[0 if ctx.steps[2][2] == _FATHER else 1]


def _r_grandparent_spouse(ctx: KinshipContext):
    # U + U + M：祖父母的配偶
    if ctx.steps[0][2] == _FATHER:
        return ("祖父", "祖母")[ctx.gidx(ctx.target)]
    return ("外祖父", "外祖母")[ctx.gidx(ctx.target)]


def _r_spouse_sibling(ctx: KinshipContext):
    # M + U + D：配偶的兄弟姐妹（大舅子/小姨子等）
    spouse = ctx.steps[0][3]
    order = ctx.older(ctx.target, spouse)
    if ctx.gender(ctx.target) == MALE:
        if order is True:
            return "大舅子"
        if order is False:
            return "小舅子"
        return "配偶的兄弟"
    if order is True:
        return "大姨子"
    if order is False:
        return "小姨子"
    return "配偶的姐妹"


def _r_sibling_spouse(ctx: KinshipContext):
    # U + D + M：兄弟姐妹的配偶（嫂子/姐夫等）
    sibling = ctx.steps[1][3]
    sg, tg = ctx.gender(sibling), ctx.gender(ctx.target)
    order = ctx.older(sibling, ctx.ego_id)
    if sg == MALE and tg == FEMALE:
        if order is True:
            return "嫂子"
        if order is False:
            return "弟媳"
        return "兄弟的配偶"
    if sg == FEMALE and tg == MALE:
        if order is True:
            return "姐夫"
        if order is False:
            return "妹夫"
        return "姐妹的配偶"
    return None


def _r_cousin(ctx: KinshipContext):
    # U + U + D + D：堂/表兄弟姐妹
    parent_side = ctx.steps[0][2]
    middle = ctx.steps[2][3]
    is_tang = parent_side == _FATHER and ctx.gender(middle) == MALE
    head = "堂" if is_tang else "表"
    return head + _cousin_tail(ctx, ctx.target)


def _cousin_tail(ctx: KinshipContext, target_id) -> str:
    order = ctx.older(target_id, ctx.ego_id)
    if ctx.gender(target_id) == MALE:
        return "兄" if order is True else ("弟" if order is False else "兄弟")
    return "姐" if order is True else ("妹" if order is False else "姐妹")


# ---- 阶段1 新增：更深姻亲 ----

def _r_uncle_aunt_spouse(ctx: KinshipContext):
    # U + U + D + M：叔伯姑舅姨的配偶
    parent_side = ctx.steps[0][2]
    middle = ctx.steps[2][3]
    if parent_side == _FATHER:
        if ctx.gender(middle) == MALE:
            order = ctx.older(middle, ctx.steps[0][3])
            if order is True:
                return "伯母"
            if order is False:
                return "婶母"
            return "伯母/婶母"
        return "姑父"
    if ctx.gender(middle) == MALE:
        return "舅母"
    return "姨父"


def _r_nephew_spouse(ctx: KinshipContext):
    # U + D + D + M：侄/甥的配偶
    sibling = ctx.steps[1][3]
    if ctx.gender(sibling) == MALE:
        return ("侄女婿", "侄媳妇")[ctx.gidx(ctx.target)]
    if ctx.gender(sibling) == FEMALE:
        return ("外甥女婿", "外甥媳妇")[ctx.gidx(ctx.target)]
    return None


def _r_grandchild_spouse(ctx: KinshipContext):
    # D + D + M：孙辈的配偶（按第一个孩子是否女儿分外孙系）
    first_child = ctx.steps[0][3]
    wai = ctx.gender(first_child) == FEMALE
    head = "外孙" if wai else "孙"
    return (head + "女婿", head + "媳妇")[ctx.gidx(ctx.target)]


def _r_spouse_grandparent(ctx: KinshipContext):
    # M + U + U：配偶的祖父母（男称岳祖父/岳祖母；女随组合称谓回退）
    if ctx.gender(ctx.ego_id) == MALE:
        return ("岳祖父", "岳祖母")[ctx.gidx(ctx.target)]
    return None


def _r_spouse_uncle_aunt(ctx: KinshipContext):
    # M + U + U + D：配偶的叔伯姑舅姨（男性 ego；女性 ego 走组合称谓）
    if ctx.gender(ctx.ego_id) != MALE:
        return None
    spouse_parent = ctx.steps[1][3]
    side = ctx.steps[1][2]  # 配偶的父亲/母亲
    middle = ctx.steps[3][3]
    if side == _FATHER:
        if ctx.gender(middle) == MALE:
            order = ctx.older(middle, spouse_parent)
            if order is True:
                return "岳伯"
            if order is False:
                return "岳叔"
            return "岳伯/岳叔"
        return "岳姑"
    if ctx.gender(middle) == MALE:
        return "岳舅"
    return "岳姨"


def _r_spouse_nephew(ctx: KinshipContext):
    # M + U + D + D：配偶的侄甥（男称内侄/内甥，女随夫家称侄/甥）
    sibling = ctx.steps[2][3]
    if ctx.gender(ctx.ego_id) == MALE:
        if ctx.gender(sibling) == MALE:
            return ("内侄", "内侄女")[ctx.gidx(ctx.target)]
        if ctx.gender(sibling) == FEMALE:
            return ("内甥", "内甥女")[ctx.gidx(ctx.target)]
        return None
    if ctx.gender(sibling) == MALE:
        return ("侄子", "侄女")[ctx.gidx(ctx.target)]
    if ctx.gender(sibling) == FEMALE:
        return ("外甥", "外甥女")[ctx.gidx(ctx.target)]
    return None


def _r_cosibling_in_law(ctx: KinshipContext):
    # M + U + D + M：连襟（妻姐妹之夫，男）/ 妯娌（夫兄弟之妻，女）
    if ctx.gender(ctx.ego_id) == MALE and ctx.gender(ctx.target) == MALE:
        return "连襟"
    if ctx.gender(ctx.ego_id) == FEMALE and ctx.gender(ctx.target) == FEMALE:
        return "妯娌"
    return None


def _r_parent_in_law_peer(ctx: KinshipContext):
    # D + M + U：亲家公/亲家母（子女配偶的父母）
    g = ctx.gender(ctx.target)
    if g == MALE:
        return "亲家公"
    if g == FEMALE:
        return "亲家母"
    return "亲家"


def _r_cousin_spouse(ctx: KinshipContext):
    # U + U + D + D + M：堂/表兄弟姐妹的配偶
    parent_side = ctx.steps[0][2]
    middle = ctx.steps[2][3]
    cousin = ctx.steps[3][3]
    is_tang = parent_side == _FATHER and ctx.gender(middle) == MALE
    head = "堂" if is_tang else "表"
    order = ctx.older(cousin, ctx.ego_id)
    older_ = order is True
    unknown = order is None
    if ctx.gender(cousin) == MALE and ctx.gender(ctx.target) == FEMALE:
        tail = "嫂" if older_ else ("弟妹" if not unknown else "兄弟之妻")
        return head + tail
    if ctx.gender(cousin) == FEMALE and ctx.gender(ctx.target) == MALE:
        tail = "姐夫" if older_ else ("妹夫" if not unknown else "姐妹之夫")
        return head + tail
    return None


# 规则表：模式精确匹配，按声明顺序求值
Rule = Tuple[tuple, Callable[[KinshipContext], Optional[str]], str]

RULES: List[Rule] = [
    # 一跳
    ((U,), _r_one_parent, "父母"),
    ((D,), _r_one_child, "子女"),
    ((M,), _r_one_spouse, "配偶"),
    # 两跳
    ((U, U), _r_grandparent, "祖父母"),
    ((U, D), _r_sibling, "兄弟姐妹"),
    ((D, D), _r_grandchild, "孙辈"),
    ((M, U), _r_spouse_parent, "配偶父母"),
    ((U, M), _r_parent_spouse, "父母配偶"),
    ((D, M), _r_child_spouse, "子女配偶"),
    ((M, D), _r_spouse_child, "配偶子女"),
    ((D, U), _r_child_other_parent, "子女另一方父母"),
    # 三跳
    ((U, U, U), _r_great_grandparent, "曾祖辈"),
    ((D, D, D), _r_great_grandchild, "曾孙辈"),
    ((U, U, D), _r_uncle_aunt, "叔伯姑舅姨"),
    ((U, D, D), _r_nephew, "侄甥"),
    ((U, M, U), _r_step_grandparent_via_parent, "继亲祖父母"),
    ((U, U, M), _r_grandparent_spouse, "祖父母配偶"),
    ((M, U, D), _r_spouse_sibling, "配偶兄弟姐妹"),
    ((U, D, M), _r_sibling_spouse, "兄弟姐妹配偶"),
    ((D, D, M), _r_grandchild_spouse, "孙辈配偶"),
    ((M, U, U), _r_spouse_grandparent, "配偶祖父母"),
    ((D, M, U), _r_parent_in_law_peer, "亲家"),
    # 四跳
    ((U, U, D, D), _r_cousin, "堂表兄弟姐妹"),
    ((U, U, D, M), _r_uncle_aunt_spouse, "叔伯姑舅姨配偶"),
    ((U, D, D, M), _r_nephew_spouse, "侄甥配偶"),
    ((M, U, U, D), _r_spouse_uncle_aunt, "配偶叔伯姑舅姨"),
    ((M, U, D, D), _r_spouse_nephew, "配偶侄甥"),
    ((M, U, D, M), _r_cosibling_in_law, "连襟妯娌"),
    # 五跳
    ((U, U, D, D, M), _r_cousin_spouse, "堂表兄弟姐妹配偶"),
]

_RULE_BY_PATTERN: Dict[tuple, Rule] = {r[0]: r for r in RULES}


def _composite_in_law(ctx: KinshipContext) -> Optional[str]:
    """以 M 开头但无专门规则：自配偶视角组合称谓，如 妻子的祖父 / 前妻的姑姑"""
    if ctx.kinds[0] != M:
        return None
    anchor = ctx.steps[0][3]
    _, nature, role, _ = ctx.steps[0]
    sub = resolve_kinship(ctx.steps[1:], anchor,
                          (ctx.persons, ctx.parents_of, ctx.children_of, ctx.spouses_of))
    sub_name = sub["relation_name"]
    if sub_name == "远亲":
        return None
    return f"{spouse_title(role, nature)}的{sub_name}"


def resolve_kinship(steps: List[tuple], ego_id: int, graph) -> Dict:
    """规则表引擎入口。graph=(persons, parents_of, children_of, spouses_of)"""
    persons, parents_of, children_of, spouses_of = graph
    ctx = KinshipContext(
        steps=steps, ego_id=ego_id, persons=persons,
        parents_of=parents_of, children_of=children_of, spouses_of=spouses_of,
    )

    title = None
    rule = _RULE_BY_PATTERN.get(ctx.kinds)
    if rule:
        title = rule[1](ctx)

    if title is None:
        title = _composite_in_law(ctx)

    if title is None:
        title = "远亲"

    # 经由前任配偶的多跳姻亲：前岳父 / 前大舅子 等（一跳"前妻/前夫"本身已含"前"）
    if ctx.lead_ex and len(ctx.steps) > 1 and not title.startswith("前"):
        title = "前" + title

    return {
        "relation_name": title,
        "level": ctx.level,
        "is_blood": ctx.is_blood,
    }
