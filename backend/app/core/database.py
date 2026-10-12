from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

from app.core.config import settings

DATABASE_URL = settings.database_url

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from app.models import user, person
    Base.metadata.create_all(bind=engine)


# 轻量级迁移：为已存在的表补充新增列（create_all 不会修改已有表结构）
# 仅做"新增可空列"这种安全操作，幂等执行
_EXTRA_COLUMNS = {
    "persons": {
        "phone": "VARCHAR(50)",
        "email": "VARCHAR(100)",
        "wechat": "VARCHAR(50)",
        "address": "VARCHAR(200)",
        "company": "VARCHAR(100)",
        "occupation": "VARCHAR(100)",
        "website": "VARCHAR(200)",
        "last_contact_at": "DATETIME",
        "importance": "INTEGER DEFAULT 3",
        "is_favorite": "BOOLEAN DEFAULT 0",
    },
    # 阶段1：配偶多段时间线
    "spouse_relations": {
        "start_date": "DATE",
        "end_date": "DATE",
    },
}

# family 表单向化后仍保持 (父母, 子女) 成对唯一
_EXTRA_UNIQUE_INDEXES = [
    ("uq_family_relations_pair", "family_relations", "person_a_id, person_b_id"),
]

# 阶段1 结构性迁移前的一次性备份文件名后缀
_PHASE1_BACKUP_SUFFIX = ".pre_phase1.bak"


def _backup_database_once(logger):
    """结构迁移前用 sqlite3 backup API 做一次一致性快照（已存在则不覆盖）"""
    if "sqlite" not in DATABASE_URL:
        return
    db_path = engine.url.database
    if not db_path or not os.path.exists(db_path):
        return
    bak_path = db_path + _PHASE1_BACKUP_SUFFIX
    if os.path.exists(bak_path):
        return
    import sqlite3
    src = sqlite3.connect(db_path)
    dst = sqlite3.connect(bak_path)
    try:
        src.backup(dst)
        logger.warning("已创建阶段1 迁移前数据库备份：%s", bak_path)
    finally:
        dst.close()
        src.close()


def _migrate_family_to_unidirectional(conn, logger):
    """
    family_relations 由双行冗余迁移为单行 parent->child：
    - SON/DAUGHTER 行若存在对应的 FATHER/MOTHER 正向行：直接删除
    - 无正向行的"孤儿反向行"：翻转为 (原person_b 父母 -> 原person_a 子女)，
      父母角色按父母性别决定（未知默认父亲）
    幂等：迁移后表中不再有 relation IN (2,3) 的行，重跑为 no-op
    """
    reverse_rows = conn.execute(
        text("SELECT id, person_a_id, person_b_id, relation, relation_nature "
             "FROM family_relations WHERE relation IN (2, 3)")
    ).fetchall()
    if not reverse_rows:
        return

    _backup_database_once(logger)

    parent_rows = conn.execute(
        text("SELECT person_a_id, person_b_id FROM family_relations WHERE relation IN (0, 1)")
    ).fetchall()
    parent_pairs = {(r[0], r[1]) for r in parent_rows}

    orphans = []  # (parent_id, child_id, relation_nature)
    for _id, a_id, b_id, relation, nature in reverse_rows:
        # (a, b, SON/DAUGHTER)：a 是子女，b 是父母；正向边应为 (b, a, FATHER/MOTHER)
        if (b_id, a_id) in parent_pairs:
            continue
        orphans.append((b_id, a_id, nature))

    conn.execute(text("DELETE FROM family_relations WHERE relation IN (2, 3)"))

    # 父母角色依据父母性别（persons.gender: 1 男 2 女，未知按父亲）
    for parent_id, child_id, nature in orphans:
        gender = conn.execute(
            text("SELECT gender FROM persons WHERE id = :pid"), {"pid": parent_id}
        ).scalar()
        role = 1 if gender == 2 else 0
        conn.execute(
            text(
                "INSERT INTO family_relations "
                "(person_a_id, person_b_id, relation, relation_nature) "
                "VALUES (:a, :b, :r, :n)"
            ),
            {"a": parent_id, "b": child_id, "r": role, "n": nature},
        )
    logger.warning(
        "家庭关系单向化迁移完成：清理冗余行 %s 条，翻转孤儿行 %s 条",
        len(reverse_rows), len(orphans),
    )


def _migrate_spouse_segment_indexes(conn, inspector, logger):
    """
    配偶表改为多段时间线：
    - 摘除旧的全对唯一索引 uq_spouse_relations_pair
    - 新建部分唯一索引：仅现任段（relation_nature=0）每方向成对唯一
    """
    existing = {idx["name"] for idx in inspector.get_indexes("spouse_relations")}

    if "uq_spouse_relations_pair" in existing:
        _backup_database_once(logger)
        conn.execute(text("DROP INDEX uq_spouse_relations_pair"))
        existing.discard("uq_spouse_relations_pair")
        logger.warning("已摘除旧配偶全对唯一索引 uq_spouse_relations_pair")

    if "uq_spouse_current_pair" not in existing:
        dup = conn.execute(
            text(
                "SELECT COUNT(*) FROM ("
                "SELECT 1 FROM spouse_relations WHERE relation_nature = 0 "
                "GROUP BY person_a_id, person_b_id HAVING COUNT(*) > 1)"
            )
        ).scalar()
        if dup:
            logger.warning(
                "跳过创建现任配偶唯一索引：存在 %s 组重复现任段，请先清理", dup
            )
            return
        conn.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_spouse_current_pair "
                "ON spouse_relations (person_a_id, person_b_id) "
                "WHERE relation_nature = 0"
            )
        )


# 阶段2：社会关系预设类型（name 唯一；按 name 判存，幂等 seed）
_PRESET_SOCIAL_TYPES = [
    ("朋友", None, 0, "#fa8c16"),
    ("同事", None, 0, "#13c2c2"),
    ("同学", None, 0, "#52c41a"),
    ("战友", None, 0, "#722ed1"),
    ("邻居", None, 0, "#eb2f96"),
    ("客户", None, 0, "#faad14"),
    ("合伙人", None, 0, "#1890ff"),
    ("老师", "学生", 1, "#f5222d"),
    # 恋人属社会关系（未组建正式家庭）：无向，兼容异性/同性恋爱关系
    ("恋人", None, 0, "#ff6b81"),
]


def _seed_preset_social_types(conn, logger):
    """新表由 create_all 创建后，幂等写入预设社会关系类型。"""
    from sqlalchemy import inspect as sa_inspect
    if "social_relation_types" not in set(
        sa_inspect(conn).get_table_names()
    ):
        return
    existing = {
        r[0] for r in conn.execute(
            text("SELECT name FROM social_relation_types")
        ).fetchall()
    }
    inserted = 0
    for name, reverse_name, directed, color in _PRESET_SOCIAL_TYPES:
        if name in existing:
            continue
        conn.execute(
            text(
                "INSERT INTO social_relation_types "
                "(name, reverse_name, directed, color, is_preset, created_at) "
                "VALUES (:name, :reverse_name, :directed, :color, 1, CURRENT_TIMESTAMP)"
            ),
            {
                "name": name,
                "reverse_name": reverse_name,
                "directed": directed,
                "color": color,
            },
        )
        inserted += 1
    if inserted:
        logger.warning("已写入预设社会关系类型 %s 个", inserted)


def _ensure_lover_type(conn):
    """返回无向预设社会关系类型「恋人」的 id（不存在则创建）。"""
    lover_type_id = conn.execute(
        text("SELECT id FROM social_relation_types WHERE name = '恋人'")
    ).scalar()
    if lover_type_id is None:
        conn.execute(
            text(
                "INSERT INTO social_relation_types "
                "(name, reverse_name, directed, color, is_preset, created_at) "
                "VALUES ('恋人', NULL, 0, '#ff6b81', 1, CURRENT_TIMESTAMP)"
            )
        )
        lover_type_id = conn.execute(text("SELECT last_insert_rowid()")).scalar()
    return lover_type_id


def _migrate_lovers_to_social(conn, logger):
    """
    男女朋友从配偶表迁移到社会关系（无向预设类型「恋人」）：
    - relation=3/4 双行冗余折叠为一条无向边，存储归一化为 a < b
    - start_date/end_date 原样携带（分手段 end_date 非空，社会边自动显示「前恋人」）
    幂等：spouse_relations 中不再有 relation IN (3,4) 的行，重跑为 no-op
    """
    from sqlalchemy import inspect as sa_inspect

    tables = set(sa_inspect(conn).get_table_names())
    if "spouse_relations" not in tables:
        return
    if "social_relations" not in tables or "social_relation_types" not in tables:
        logger.warning("跳过恋人关系迁移：社会关系表尚未创建")
        return
    rows = conn.execute(
        text(
            "SELECT person_a_id, person_b_id, relation, start_date, end_date "
            "FROM spouse_relations WHERE relation IN (3, 4)"
        )
    ).fetchall()
    if not rows:
        return

    _backup_database_once(logger)

    lover_type_id = _ensure_lover_type(conn)

    # 折叠双行冗余；无向边归一化为 (小id, 大id, 开始, 结束)
    targets = set()
    for a_id, b_id, relation, sdate, edate in rows:
        targets[(min(a_id, b_id), max(a_id, b_id), sdate, edate)]

    existing = {
        (r[0], r[1], r[2], r[3])
        for r in conn.execute(
            text(
                "SELECT person_a_id, person_b_id, start_date, end_date "
                "FROM social_relations WHERE type_id = :tid"
            ),
            {"tid": lover_type_id},
        ).fetchall()
    }

    inserted = 0
    for a_id, b_id, sdate, edate in targets:
        if (a_id, b_id, sdate, edate) in existing:
            continue
        conn.execute(
            text(
                "INSERT INTO social_relations "
                "(person_a_id, person_b_id, type_id, closeness, "
                " start_date, end_date, introducer_id, created_at) "
                "VALUES (:a, :b, :tid, NULL, :s, :e, NULL, CURRENT_TIMESTAMP)"
            ),
            {"a": a_id, "b": b_id, "tid": lover_type_id, "s": sdate, "e": edate},
        )
        inserted += 1

    conn.execute(text("DELETE FROM spouse_relations WHERE relation IN (3, 4)"))
    logger.warning(
        "恋人关系迁移完成：转换 %s 条恋人关系（清理配偶冗余行 %s 条）",
        inserted, len(rows),
    )


def _migrate_directed_lover_type(conn, logger):
    """
    把过渡版本的有向预设「男朋友/女朋友」合并为无向「恋人」：
    - 旧类型的边归一化（a<b）后搬到「恋人」，按段指纹去重
    - 删除旧边与旧类型
    幂等：旧类型不存在即为 no-op
    """
    from sqlalchemy import inspect as sa_inspect

    if "social_relation_types" not in set(sa_inspect(conn).get_table_names()):
        return
    old = conn.execute(
        text("SELECT id FROM social_relation_types WHERE name = '男朋友'")
    ).fetchone()
    if old is None:
        return
    old_type_id = old[0]

    old_rows = conn.execute(
        text(
            "SELECT person_a_id, person_b_id, start_date, end_date "
            "FROM social_relations WHERE type_id = :tid"
        ),
        {"tid": old_type_id},
    ).fetchall()
    if not old_rows:
        conn.execute(
            text("DELETE FROM social_relation_types WHERE id = :tid"),
            {"tid": old_type_id},
        )
        logger.warning("已移除过渡版有向类型「男朋友/女朋友」（无关系数据）")
        return

    _backup_database_once(logger)
    lover_type_id = _ensure_lover_type(conn)

    targets = {
        (min(a, b), max(a, b), s, e) for a, b, s, e in old_rows
    }
    existing = {
        (r[0], r[1], r[2], r[3])
        for r in conn.execute(
            text(
                "SELECT person_a_id, person_b_id, start_date, end_date "
                "FROM social_relations WHERE type_id = :tid"
            ),
            {"tid": lover_type_id},
        ).fetchall()
    }
    inserted = 0
    for a_id, b_id, sdate, edate in targets - existing:
        conn.execute(
            text(
                "INSERT INTO social_relations "
                "(person_a_id, person_b_id, type_id, closeness, "
                " start_date, end_date, introducer_id, created_at) "
                "VALUES (:a, :b, :tid, NULL, :s, :e, NULL, CURRENT_TIMESTAMP)"
            ),
            {"a": a_id, "b": b_id, "tid": lover_type_id, "s": sdate, "e": edate},
        )
        inserted += 1

    conn.execute(
        text("DELETE FROM social_relations WHERE type_id = :tid"),
        {"tid": old_type_id},
    )
    conn.execute(
        text("DELETE FROM social_relation_types WHERE id = :tid"),
        {"tid": old_type_id},
    )
    logger.warning(
        "有向「男朋友/女朋友」已合并为无向「恋人」：转换 %s 条（旧关系 %s 条）",
        inserted, len(old_rows),
    )


def run_lightweight_migrations():
    """检查并补充缺失的列/索引，适用于 SQLite 等无需独立迁移工具的自托管场景。"""
    from sqlalchemy import inspect, text
    import logging

    logger = logging.getLogger("uvicorn")
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    with engine.begin() as conn:
        for table_name, columns in _EXTRA_COLUMNS.items():
            if table_name not in existing_tables:
                continue
            present = {col["name"] for col in inspector.get_columns(table_name)}
            for column_name, column_type in columns.items():
                if column_name not in present:
                    conn.execute(
                        text(
                            f'ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}'
                        )
                    )

        for index_name, table_name, columns in _EXTRA_UNIQUE_INDEXES:
            if table_name not in existing_tables:
                continue
            existing_indexes = {idx["name"] for idx in inspector.get_indexes(table_name)}
            if index_name in existing_indexes:
                continue
            # 存量脏数据（重复对）会导致建索引失败：检测到重复则跳过并告警
            col_a, col_b = [c.strip() for c in columns.split(",")]
            dup_count = conn.execute(
                text(
                    f"SELECT COUNT(*) FROM ("
                    f"SELECT 1 FROM {table_name} "
                    f"GROUP BY {col_a}, {col_b} HAVING COUNT(*) > 1)"
                )
            ).scalar()
            if dup_count:
                logger.warning(
                    "跳过创建唯一索引 %s：表 %s 存在 %s 组重复关系，请先清理",
                    index_name, table_name, dup_count
                )
                continue
            conn.execute(
                text(
                    f"CREATE UNIQUE INDEX {index_name} ON {table_name} ({columns})"
                )
            )

        # 阶段1 结构性迁移
        if "family_relations" in existing_tables:
            _migrate_family_to_unidirectional(conn, logger)
        if "spouse_relations" in existing_tables:
            _migrate_spouse_segment_indexes(conn, inspector, logger)

        # 阶段2：社会关系预设类型 seed（create_all 之后执行）
        _seed_preset_social_types(conn, logger)
        # 男女朋友从配偶表迁移到社会关系（依赖预设类型先 seed）
        _migrate_lovers_to_social(conn, logger)
        # 过渡版有向「男朋友/女朋友」合并为无向「恋人」
        _migrate_directed_lover_type(conn, logger)
