from typing import List, Optional

from app.models.tag import Tag, PersonTag


# 自动配色调色板
TAG_COLOR_PALETTE = [
    "#409EFF", "#67C23A", "#E6A23C", "#F56C6C", "#9B59B6",
    "#1ABC9C", "#36CFC9", "#FF85C0", "#5C7BD9", "#FF9F40",
]


def auto_color(name: str) -> str:
    """根据标签名稳定地分配一个颜色。"""
    if not name:
        return TAG_COLOR_PALETTE[0]
    total = sum(ord(ch) for ch in name)
    return TAG_COLOR_PALETTE[total % len(TAG_COLOR_PALETTE)]


def normalize_names(names: Optional[List[str]]) -> List[str]:
    """去空白、去重并保持原有顺序。"""
    if not names:
        return []
    result = []
    seen = set()
    for raw in names:
        if not raw:
            continue
        name = raw.strip()
        if name and name not in seen:
            seen.add(name)
            result.append(name)
    return result


def sync_person_tags(db, person, names: Optional[List[str]]) -> None:
    """
    按标签名称数组重建人物的标签关联。
    不存在的标签自动创建并赋予颜色；传空数组清空全部标签。
    """
    clean_names = normalize_names(names)

    tags = []
    for name in clean_names:
        tag = db.query(Tag).filter(Tag.name == name).first()
        if not tag:
            tag = Tag(name=name, color=auto_color(name))
            db.add(tag)
            db.flush()
        tags.append(tag)

    # 清空旧关联后重建
    db.query(PersonTag).filter(PersonTag.person_id == person.id).delete(
        synchronize_session=False
    )
    for tag in tags:
        db.add(PersonTag(person_id=person.id, tag_id=tag.id))
    db.flush()
