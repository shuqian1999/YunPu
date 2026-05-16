# 关系计算引擎详细设计

## 1. 概述

### 1.1 设计目标

关系计算引擎是家谱系统的核心组件，负责：
- 根据家族关系数据计算任意两人之间的亲属关系
- 支持复杂的亲属关系类型（直系、旁系、姻亲、继亲、义亲等）
- 提供高效的关系查询和路径分析能力
- 支持中文亲属称谓的自动生成

### 1.2 术语定义

| 术语 | 定义 |
|------|------|
| **直系亲属** | 父母、子女、祖父母、孙子女等直接血缘关系 |
| **旁系亲属** | 兄弟姐妹、叔伯姑舅、堂表兄弟姐妹等 |
| **姻亲关系** | 配偶、岳父母、公婆、连襟、妯娌等 |
| **继亲关系** | 继父、继母、继子女等 |
| **义亲关系** | 义父、义母、义子、义女等 |
| **亲属等级** | 表示亲属关系的远近程度（1=父母/子女，2=祖父母/孙子女等） |

---

## 2. 数据模型设计

### 2.1 核心实体

#### 2.1.1 FamilyRelation（家庭关系表）

```python
# app/models/family_relation.py
class FamilyRelation(Base):
    __tablename__ = "family_relations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    parent_person_id = Column(Integer, ForeignKey("persons.id"), nullable=False)
    child_person_id = Column(Integer, ForeignKey("persons.id"), nullable=False)
    
    parent_type = Column(Enum("father", "mother"), nullable=False)  # 父亲/母亲
    relation_nature = Column(Enum("qin", "ji", "yi"), nullable=False)  # 亲生/继亲/义亲
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

#### 2.1.2 FamilyCalculatedRelation（计算关系缓存表）

```python
# app/models/family_calculated_relation.py
class FamilyCalculatedRelation(Base):
    __tablename__ = "family_calculated_relations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    source_person_id = Column(Integer, ForeignKey("persons.id"), nullable=False)
    target_person_id = Column(Integer, ForeignKey("persons.id"), nullable=False)
    
    relation_name = Column(String(50), nullable=False)  # 亲属称谓
    relation_type = Column(Enum("direct", "collateral", "marriage"))  # 关系类型
    relation_degree = Column(Integer)  # 亲属等级
    shortest_path = Column(Text)  # JSON格式的最短路径
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

---

## 3. 关系计算算法

### 3.1 数据结构

```python
# 关系图节点
class RelationNode:
    def __init__(self, person_id: int, gender: str):
        self.person_id = person_id
        self.gender = gender  # 'male', 'female', 'unknown'
        self.fathers = []     # 父节点ID列表
        self.mothers = []     # 母节点ID列表
        self.spouses = []     # 配偶节点ID列表
        self.children = []    # 子节点ID列表
```

### 3.2 最短路径算法（BFS）

```python
from collections import deque
from typing import List, Tuple, Optional, Dict

def find_shortest_path(
    graph: Dict[int, RelationNode],
    source_id: int,
    target_id: int
) -> Optional[List[Tuple[int, str]]]:
    """
    查找两人之间的最短亲属路径
    
    Args:
        graph: 关系图
        source_id: 起始人物ID
        target_id: 目标人物ID
    
    Returns:
        路径列表，每个元素为 (person_id, relation_type)
        relation_type: 'father', 'mother', 'son', 'daughter', 'spouse'
    """
    if source_id == target_id:
        return []
    
    visited = {source_id}
    queue = deque([(source_id, [])])
    
    while queue:
        current_id, path = queue.popleft()
        current_node = graph.get(current_id)
        
        if not current_node:
            continue
        
        # 遍历父节点
        for father_id in current_node.fathers:
            if father_id == target_id:
                return path + [(father_id, 'father')]
            if father_id not in visited:
                visited.add(father_id)
                queue.append((father_id, path + [(father_id, 'father')]))
        
        for mother_id in current_node.mothers:
            if mother_id == target_id:
                return path + [(mother_id, 'mother')]
            if mother_id not in visited:
                visited.add(mother_id)
                queue.append((mother_id, path + [(mother_id, 'mother')]))
        
        # 遍历子节点
        for child_id in current_node.children:
            child_node = graph.get(child_id)
            relation_type = 'son' if child_node and child_node.gender == 'male' else 'daughter'
            if child_id == target_id:
                return path + [(child_id, relation_type)]
            if child_id not in visited:
                visited.add(child_id)
                queue.append((child_id, path + [(child_id, relation_type)]))
        
        # 遍历配偶
        for spouse_id in current_node.spouses:
            if spouse_id == target_id:
                return path + [(spouse_id, 'spouse')]
            if spouse_id not in visited:
                visited.add(spouse_id)
                queue.append((spouse_id, path + [(spouse_id, 'spouse')]))
    
    return None
```

### 3.3 关系称谓计算

```python
def calculate_relation(
    graph: Dict[int, RelationNode],
    source_id: int,
    target_id: int,
    source_gender: str = 'unknown'
) -> dict:
    """
    计算两人之间的亲属关系
    
    Returns:
        {
            'relation_name': str,      # 亲属称谓（如：父亲、堂兄、岳母）
            'relation_type': str,      # direct/collateral/marriage
            'degree': int,             # 亲属等级
            'path': list               # 路径详情
        }
    """
    path = find_shortest_path(graph, source_id, target_id)
    
    if not path:
        return {
            'relation_name': '未知',
            'relation_type': 'unknown',
            'degree': 0,
            'path': []
        }
    
    return interpret_path(path, source_gender)
```

### 3.4 路径解释算法

```python
def interpret_path(path: List[Tuple[int, str]], source_gender: str) -> dict:
    """
    根据路径解释亲属关系称谓
    
    路径模式分析：
    - 直接路径：父子/母子 -> 直系亲属
    - 兄弟路径：父子+子 -> 兄弟姐妹
    - 堂表路径：父子+子+父子 -> 堂兄弟姐妹
    - 姻亲路径：配偶+父子 -> 岳父母/公婆
    """
    relations = [rel for _, rel in path]
    
    # 直接父子关系
    if len(relations) == 1:
        rel = relations[0]
        if rel == 'father':
            return {'relation_name': '父亲', 'relation_type': 'direct', 'degree': 1}
        elif rel == 'mother':
            return {'relation_name': '母亲', 'relation_type': 'direct', 'degree': 1}
        elif rel in ('son', 'daughter'):
            return {
                'relation_name': '儿子' if rel == 'son' else '女儿',
                'relation_type': 'direct',
                'degree': 1
            }
        elif rel == 'spouse':
            return {'relation_name': '配偶', 'relation_type': 'marriage', 'degree': 1}
    
    # 祖父母/孙子女
    if len(relations) == 2:
        if relations == ['father', 'father']:
            return {'relation_name': '祖父', 'relation_type': 'direct', 'degree': 2}
        if relations == ['father', 'mother']:
            return {'relation_name': '祖母', 'relation_type': 'direct', 'degree': 2}
        if relations == ['mother', 'father']:
            return {'relation_name': '外祖父', 'relation_type': 'direct', 'degree': 2}
        if relations == ['mother', 'mother']:
            return {'relation_name': '外祖母', 'relation_type': 'direct', 'degree': 2}
        if relations[0] in ('son', 'daughter') and relations[1] in ('son', 'daughter'):
            child_type = '孙子' if relations[1] == 'son' else '孙女'
            return {'relation_name': child_type, 'relation_type': 'direct', 'degree': 2}
    
    # 兄弟姐妹
    if len(relations) >= 2:
        # 模式：父亲/母亲 -> 儿子/女儿
        if relations[0] in ('father', 'mother') and relations[-1] in ('son', 'daughter'):
            # 检查中间是否有配偶
            has_spouse = 'spouse' in relations[1:-1]
            
            if has_spouse:
                # 继兄弟姐妹
                if relations[-1] == 'son':
                    return {'relation_name': '继兄' if source_gender == 'male' else '继姐', 
                            'relation_type': 'collateral', 'degree': 1}
                else:
                    return {'relation_name': '继弟' if source_gender == 'male' else '继妹', 
                            'relation_type': 'collateral', 'degree': 1}
            else:
                # 亲兄弟姐妹
                if relations[-1] == 'son':
                    return {'relation_name': '哥哥' if source_gender == 'male' else '姐姐', 
                            'relation_type': 'collateral', 'degree': 1}
                else:
                    return {'relation_name': '弟弟' if source_gender == 'male' else '妹妹', 
                            'relation_type': 'collateral', 'degree': 1}
    
    # 堂表兄弟姐妹（三代旁系）
    if len(relations) >= 4:
        # 模式：父->子->父->子
        if (relations[0] in ('father', 'mother') and 
            relations[1] in ('son', 'daughter') and
            relations[2] in ('father', 'mother') and
            relations[3] in ('son', 'daughter')):
            
            # 判断堂/表
            is_paternal = relations[0] == 'father' and relations[2] == 'father'
            
            if is_paternal:
                prefix = '堂'
            else:
                prefix = '表'
            
            if relations[-1] == 'son':
                return {'relation_name': f'{prefix}兄' if source_gender == 'male' else f'{prefix}姐', 
                        'relation_type': 'collateral', 'degree': 2}
            else:
                return {'relation_name': f'{prefix}弟' if source_gender == 'male' else f'{prefix}妹', 
                        'relation_type': 'collateral', 'degree': 2}
    
    # 默认处理
    return {
        'relation_name': f'{len(relations)}代亲属',
        'relation_type': 'collateral',
        'degree': len(relations)
    }
```

---

## 4. API 接口设计

### 4.1 计算两人关系

```python
# app/api/v1/family.py
@router.get("/relation/calculate")
async def calculate_relation_api(
    source_person_id: int,
    target_person_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    计算两人之间的亲属关系
    
    Args:
        source_person_id: 起始人物ID
        target_person_id: 目标人物ID
    
    Returns:
        {
            "relation_name": "父亲",
            "relation_type": "direct",
            "degree": 1,
            "path": [...]
        }
    """
    # 构建关系图
    graph = build_relation_graph(current_user.id, db)
    
    source_person = db.query(Person).filter(Person.id == source_person_id).first()
    source_gender = source_person.gender if source_person else 'unknown'
    
    result = calculate_relation(graph, source_person_id, target_person_id, source_gender)
    return result
```

### 4.2 获取某人的所有亲属

```python
@router.get("/person/{person_id}/all-relations")
async def get_person_all_relations(
    person_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取某人的所有亲属关系列表
    
    Returns:
        [{
            "person_id": int,
            "name": str,
            "relation_name": str,
            "relation_type": str,
            "degree": int
        }, ...]
    """
    graph = build_relation_graph(current_user.id, db)
    
    person = db.query(Person).filter(Person.id == person_id).first()
    source_gender = person.gender if person else 'unknown'
    
    results = []
    for target_id in graph:
        if target_id == person_id:
            continue
        
        relation = calculate_relation(graph, person_id, target_id, source_gender)
        target_person = db.query(Person).filter(Person.id == target_id).first()
        
        results.append({
            "person_id": target_id,
            "name": target_person.nickname or (target_person.last_name + target_person.first_name),
            **relation
        })
    
    return sorted(results, key=lambda x: x['degree'])
```

---

## 5. 性能优化策略

### 5.1 缓存机制

```python
def get_cached_relation(
    db: Session,
    user_id: int,
    source_id: int,
    target_id: int
) -> Optional[dict]:
    """从缓存获取计算结果"""
    cached = db.query(FamilyCalculatedRelation).filter(
        FamilyCalculatedRelation.user_id == user_id,
        FamilyCalculatedRelation.source_person_id == source_id,
        FamilyCalculatedRelation.target_person_id == target_id
    ).first()
    
    if cached:
        return {
            'relation_name': cached.relation_name,
            'relation_type': cached.relation_type,
            'degree': cached.relation_degree,
            'path': json.loads(cached.shortest_path) if cached.shortest_path else []
        }
    return None

def cache_relation(
    db: Session,
    user_id: int,
    source_id: int,
    target_id: int,
    result: dict
):
    """缓存计算结果"""
    cached = FamilyCalculatedRelation(
        user_id=user_id,
        source_person_id=source_id,
        target_person_id=target_id,
        relation_name=result['relation_name'],
        relation_type=result['relation_type'],
        relation_degree=result['degree'],
        shortest_path=json.dumps(result.get('path', []))
    )
    db.add(cached)
    db.commit()
```

### 5.2 图缓存策略

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def build_relation_graph(user_id: int) -> Dict[int, RelationNode]:
    """构建并缓存关系图"""
    # 实际实现中需要从数据库读取
    pass
```

---

## 6. 边缘情况处理

| 场景 | 处理方式 |
|------|----------|
| **自己与自己** | 返回空关系 |
| **无血缘关系** | 返回"未知关系" |
| **单亲家庭** | 允许只有父亲或母亲 |
| **同性婚姻** | 支持配偶关系，子女通过父母双方关联 |
| **多重婚姻** | 支持多个配偶关系 |
| **收养关系** | 通过relation_nature字段区分 |

---

## 7. 数据同步机制

```python
def invalidate_relation_cache(
    db: Session,
    user_id: int,
    person_id: Optional[int] = None
):
    """
    当家族关系发生变化时，失效相关缓存
    
    Args:
        person_id: 如果指定，只失效与该人相关的缓存；否则失效全部
    """
    query = db.query(FamilyCalculatedRelation).filter(
        FamilyCalculatedRelation.user_id == user_id
    )
    
    if person_id:
        query = query.filter(
            or_(
                FamilyCalculatedRelation.source_person_id == person_id,
                FamilyCalculatedRelation.target_person_id == person_id
            )
        )
    
    query.delete()
    db.commit()
```

---

## 8. 扩展计划

### 8.1 未来功能

1. **亲属关系预测**：根据现有关系推断可能的缺失关系
2. **DNA匹配集成**：结合基因检测数据验证亲属关系
3. **多语言支持**：支持英文、粤语等多种语言的亲属称谓
4. **关系统计分析**：提供家族关系网络分析报告