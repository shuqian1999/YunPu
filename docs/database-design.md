# 云谱 - 数据库设计文档

## 数据库概览

基于功能需求分析，设计以下数据库表结构：

| 表名 | 说明 | 核心用途 |
|------|------|----------|
| `users` | 用户表 | 存储系统登录用户（仅用于身份验证） |
| `persons` | 人物表 | 存储人物基本信息 |
| `person_groups` | 人物群组表 | 人物分类管理 |
| `person_group_members` | 人物-群组关联 | 多对多关系 |
| `events` | 事件表 | 个人/人物事件时间轴 |
| `event_types` | 事件类型表 | 用户自定义事件类型 |
| `reminders` | 提醒表 | 日期提醒（生日、纪念日等） |
| `notifications` | 通知表 | 站内通知记录 |
| `family_members` | 家族成员表 | 家谱成员信息 |
| `family_relations` | 家族关系表 | 成员关系定义（父母→子女） |
| `family_calculated_relations` | 计算关系表 | 存储相对于"我"的计算关系 |

---

## 表结构详细设计

### 1. users（用户表）

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | 用户ID |
| `username` | VARCHAR(50) | UNIQUE NOT NULL | 用户名（仅用于登录） |
| `password_hash` | VARCHAR(255) | NOT NULL | 密码哈希 |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| `updated_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 更新时间 |

**说明**：该表仅用于身份验证，与系统内容无关。

---

### 2. persons（人物表）

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | 人物ID |
| `user_id` | INTEGER | FOREIGN KEY REFERENCES users(id) | 所属用户 |
| `first_name` | VARCHAR(50) | | 姓 |
| `last_name` | VARCHAR(50) | | 名 |
| `nickname` | VARCHAR(50) | | 昵称 |
| `gender` | TINYINT | | 性别（0:未知, 1:男, 2:女） |
| `birth_date` | DATE | | 出生日期 |
| `death_date` | DATE | | 逝世日期（NULL表示在世） |
| `country` | VARCHAR(50) | | 国家 |
| `hometown` | VARCHAR(100) | | 故乡 |
| `residence` | VARCHAR(100) | | 现居地 |
| `custom_fields` | JSON | | 自定义字段（JSON格式） |
| `is_me` | BOOLEAN | DEFAULT FALSE | 是否为使用者本人 |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| `updated_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 更新时间 |
| `last_contact_at` | TIMESTAMP | | 最后记录时间 |

**custom_fields 格式示例**：
```json
{
  "手机号": {
    "工作": "123****",
    "私人": "135****"
  },
  "邮箱": {
    "QQ邮箱": "asdaf@qq.com"
  }
}
```

---

### 3. person_groups（人物群组表）

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | 群组ID |
| `user_id` | INTEGER | FOREIGN KEY REFERENCES users(id) | 所属用户 |
| `name` | VARCHAR(50) | NOT NULL | 群组名称 |
| `color` | VARCHAR(7) | DEFAULT '#1890ff' | 群组颜色 |
| `description` | VARCHAR(255) | | 群组描述 |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

---

### 4. person_group_members（人物-群组关联表）

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `person_id` | INTEGER | FOREIGN KEY REFERENCES persons(id) | 人物ID |
| `group_id` | INTEGER | FOREIGN KEY REFERENCES person_groups(id) | 群组ID |

**复合主键**：`(person_id, group_id)`

---

### 5. events（事件表）

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | 事件ID |
| `user_id` | INTEGER | FOREIGN KEY REFERENCES users(id) | 所属用户 |
| `person_id` | INTEGER | FOREIGN KEY REFERENCES persons(id) | 关联人物（NULL表示用户事件） |
| `title` | VARCHAR(200) | NOT NULL | 事件标题 |
| `description` | TEXT | | 事件描述 |
| `event_date` | DATE | NOT NULL | 事件日期 |
| `location` | VARCHAR(200) | | 事件地点 |
| `event_type_id` | INTEGER | FOREIGN KEY REFERENCES event_types(id) | 事件类型ID |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

**索引**：`(user_id, person_id, event_date)`

---

### 6. event_types（事件类型表）

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | 类型ID |
| `user_id` | INTEGER | FOREIGN KEY REFERENCES users(id) | 所属用户 |
| `name` | VARCHAR(50) | NOT NULL | 类型名称 |
| `color` | VARCHAR(7) | DEFAULT '#1890ff' | 类型颜色 |
| `icon` | VARCHAR(50) | | 类型图标 |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

**内置默认类型**：工作经历、教育经历、个人经历、感情经历

---

### 7. reminders（提醒表）

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | 提醒ID |
| `user_id` | INTEGER | FOREIGN KEY REFERENCES users(id) | 所属用户 |
| `person_id` | INTEGER | FOREIGN KEY REFERENCES persons(id) | 关联人物（NULL表示个人提醒） |
| `title` | VARCHAR(200) | NOT NULL | 提醒标题 |
| `remind_date` | DATE | NOT NULL | 提醒日期 |
| `is_lunar` | BOOLEAN | DEFAULT FALSE | 是否农历 |
| `repeat_type` | VARCHAR(10) | DEFAULT 'once' | 重复类型（once/yearly/monthly/weekly） |
| `notify_before_days` | INTEGER | DEFAULT 0 | 提前N天提醒 |
| `enabled` | BOOLEAN | DEFAULT TRUE | 是否启用 |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| `updated_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 更新时间 |

**索引**：`(user_id, remind_date)`

---

### 8. notifications（通知表）

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | 通知ID |
| `user_id` | INTEGER | FOREIGN KEY REFERENCES users(id) | 所属用户 |
| `type` | VARCHAR(20) | NOT NULL | 通知类型（reminder/event） |
| `title` | VARCHAR(200) | NOT NULL | 通知标题 |
| `content` | TEXT | | 通知内容 |
| `related_id` | INTEGER | | 关联ID（提醒ID/事件ID） |
| `is_read` | BOOLEAN | DEFAULT FALSE | 是否已读 |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

**索引**：`(user_id, is_read, created_at)`

---

### 9. family_members（家族成员表）

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | 成员ID |
| `user_id` | INTEGER | FOREIGN KEY REFERENCES users(id) | 所属用户 |
| `person_id` | INTEGER | FOREIGN KEY REFERENCES persons(id) | 关联人物 |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

**说明**：家族成员与人物是一对一关系，确保数据一致性。

---

### 10. family_relations（家族关系表）

**设计原则**：只记录**直系血缘关系（父母→子女）**，其他关系通过算法计算得出。

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | 关系ID |
| `user_id` | INTEGER | FOREIGN KEY REFERENCES users(id) | 所属用户 |
| `parent_id` | INTEGER | FOREIGN KEY REFERENCES family_members(id) | 父/母ID |
| `child_id` | INTEGER | FOREIGN KEY REFERENCES family_members(id) | 子/女ID |
| `parent_type` | VARCHAR(10) | NOT NULL | 父母类型（father/mother） |
| `relation_nature` | VARCHAR(10) | DEFAULT 'qin' | 关系性质（qin/gan/yi/yang/ji） |

**索引**：`(parent_id, child_id)`

---

### 11. family_calculated_relations（计算关系表）

**设计原则**：存储所有人物相对于"我"（is_me=true）的计算关系，避免重复计算。

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | 关系ID |
| `user_id` | INTEGER | FOREIGN KEY REFERENCES users(id) | 所属用户 |
| `person_id` | INTEGER | FOREIGN KEY REFERENCES persons(id) | 人物ID |
| `relation_name` | VARCHAR(50) | NOT NULL | 关系名称（如：父亲、祖父、哥哥） |
| `relation_level` | INTEGER | NOT NULL | 关系层级（1=父母, 2=祖父母, -1=子女等） |
| `relation_path` | TEXT | | 关系路径（用于验证） |
| `is_blood` | BOOLEAN | DEFAULT TRUE | 是否血缘关系 |
| `updated_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 更新时间 |

**索引**：`(user_id, person_id)`

---

## ER 关系图

```
users 1 -- * persons
users 1 -- * person_groups
users 1 -- * events
users 1 -- * event_types
users 1 -- * reminders
users 1 -- * notifications
users 1 -- * family_members
users 1 -- * family_relations
users 1 -- * family_calculated_relations

persons 1 -- * person_group_members
person_groups 1 -- * person_group_members

persons 1 -- * events
persons 1 -- * reminders
persons 1 -- 1 family_members

events 1 -- 1 event_types

family_members 1 -- * family_relations (as parent)
family_members 1 -- * family_relations (as child)
```

---

## 数据字典

### relation_nature 枚举值

| 值 | 说明 | 连线样式 |
|----|------|----------|
| `qin` | 亲生 | 实线 |
| `gan` | 干亲 | 虚线 |
| `yi` | 义亲 | 虚线 |
| `yang` | 收养 | 虚线 |
| `ji` | 继亲 | 虚线 |

### repeat_type 枚举值

| 值 | 说明 |
|----|------|
| `once` | 单次 |
| `yearly` | 每年 |
| `monthly` | 每月 |
| `weekly` | 每周 |

### notification_type 枚举值

| 值 | 说明 |
|----|------|
| `reminder` | 提醒通知 |
| `event` | 事件通知 |

---

## 索引优化建议

1. **users**：`username` 添加唯一索引
2. **persons**：`user_id`、`is_me` 添加索引，`first_name`、`last_name` 添加全文索引
3. **events**：`(user_id, person_id, event_date)` 复合索引
4. **reminders**：`(user_id, remind_date)` 复合索引
5. **family_relations**：`(parent_id, child_id)` 复合索引
6. **family_calculated_relations**：`(user_id, person_id)` 复合索引
7. **notifications**：`(user_id, is_read, created_at)` 复合索引

---

## 数据库配置

使用 SQLAlchemy ORM 实现，支持多数据库切换：

```python
# .env 配置示例
DATABASE_URL=sqlite:///./yunpu.db
# 扩展支持：
# DATABASE_URL=postgresql://user:pass@localhost/yunpu
# DATABASE_URL=mysql+pymysql://user:pass@localhost/yunpu
```

---

## 初始化流程

1. 创建用户（用户名/密码，仅用于登录）
2. 创建人物（`is_me=true`，昵称="我"）
3. 创建默认事件类型（工作经历、教育经历、个人经历、感情经历）