"""为已存在的 reminders 表添加新字段（与 Event 对齐）"""
import sqlite3
import os
import sys

# 添加项目根目录到 path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def get_db_path():
    """从配置中读取数据库路径"""
    try:
        from app.core.config import settings
        db_url = settings.DATABASE_URL
        if db_url.startswith("sqlite:///"):
            return db_url.replace("sqlite:///", "")
    except Exception:
        pass
    return "./yunpu.db"


def column_exists(cursor, table_name, column_name):
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns


def migrate():
    db_path = get_db_path()
    if not os.path.exists(db_path):
        print(f"数据库文件 {db_path} 不存在，跳过迁移（启动时自动建表）")
        return

    print(f"正在迁移数据库: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    new_columns = [
        ("event_type_id", "INTEGER", "FOREIGN KEY(event_types.id)"),
        ("description", "TEXT", None),
        ("location", "VARCHAR(200)", None),
        ("priority", "VARCHAR(20)", "DEFAULT 'normal'"),
        ("remind_advance_days", "INTEGER", "DEFAULT 0"),
    ]

    for col_name, col_type, col_constraint in new_columns:
        if column_exists(cursor, "reminders", col_name):
            print(f"  - 列 {col_name} 已存在，跳过")
            continue
        constraint = f" {col_constraint}" if col_constraint else ""
        sql = f"ALTER TABLE reminders ADD COLUMN {col_name} {col_type}{constraint}"
        print(f"  + 添加列: {col_name} ({col_type})")
        try:
            cursor.execute(sql)
        except Exception as e:
            print(f"    错误: {e}")

    conn.commit()
    conn.close()
    print("迁移完成")


if __name__ == "__main__":
    migrate()
