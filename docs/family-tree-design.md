# 家谱树可视化详细设计

## 1. 概述

### 1.1 设计目标

家谱树可视化组件负责：
- 将家族关系数据以树形结构展示
- 支持交互式操作（缩放、平移、节点点击）
- 提供直观的亲属关系展示
- 支持快捷添加亲属关系

### 1.2 技术选型

| 技术 | 选型 | 理由 |
|------|------|------|
| 可视化库 | Vue Flow | Vue生态原生支持，拖拽交互开箱即用 |
| 布局算法 | 自定义层级布局 | 家族树结构特殊，需要定制布局 |
| 样式框架 | Element Plus | 与项目现有技术栈一致 |

---

## 2. 架构设计

### 2.1 组件结构

```
FamilyTree.vue (主组件)
├── VueFlow (可视化容器)
│   ├── Background (背景网格)
│   ├── Controls (控制按钮)
│   └── Custom Node (自定义节点)
├── NodeDetailPanel (节点详情面板)
├── AddRelationDialog (添加关系弹窗)
└── QuickAddDialog (快速添加弹窗)
```

### 2.2 数据流

```
┌──────────────────┐     ┌─────────────────┐     ┌──────────────────┐
│  API Layer       │────▶│  Store/State    │────▶│  VueFlow         │
│  (getFamilyTree) │     │  (localNodes)   │     │  (nodes/edges)   │
└──────────────────┘     └─────────────────┘     └──────────────────┘
       ▲                                                     │
       │                                                     │
       └─────────────────────────────────────────────────────┘
                              │
                     ┌────────┴────────┐
                     ▼                 ▼
              addFamilyRelation   calculateLayout
```

---

## 3. 布局算法设计

### 3.1 数据结构

```typescript
interface FamilyTreeNode {
  id: string;
  personId: number;
  name: string;
  gender: 'male' | 'female' | 'unknown';
  birthDate?: string;
  deathDate?: string;
  isMe: boolean;
  position: { x: number; y: number };
}

interface FamilyTreeEdge {
  id: string;
  source: string;
  target: string;
  relationNature: 'qin' | 'ji' | 'yi';
}
```

### 3.2 层级布局算法

```typescript
function calculateLayout(nodes: FamilyTreeNode[], edges: FamilyTreeEdge[]): FamilyTreeNode[] {
  // 1. 构建父子关系映射
  const parentMap = new Map<string, string[]>();
  const childMap = new Map<string, string[]>();
  
  edges.forEach(edge => {
    if (!parentMap.has(edge.source)) parentMap.set(edge.source, []);
    if (!childMap.has(edge.target)) childMap.set(edge.target, []);
    parentMap.get(edge.source)!.push(edge.target);
    childMap.get(edge.target)!.push(edge.source);
  });
  
  // 2. 确定层级（以"我"为中心）
  const levelMap = new Map<string, number>();
  const meNode = nodes.find(n => n.isMe);
  
  if (meNode) {
    levelMap.set(meNode.id, 0);
    assignLevels(meNode.id, 0, parentMap, childMap, levelMap);
  } else {
    // 如果没有"我"节点，以第一个节点为根
    const rootNode = nodes[0];
    if (rootNode) {
      levelMap.set(rootNode.id, 0);
      assignLevels(rootNode.id, 0, parentMap, childMap, levelMap);
    }
  }
  
  // 3. 计算每层节点位置
  const levels: Map<number, string[]> = new Map();
  levelMap.forEach((level, nodeId) => {
    if (!levels.has(level)) levels.set(level, []);
    levels.get(level)!.push(nodeId);
  });
  
  // 4. 计算坐标
  const NODE_WIDTH = 180;
  const NODE_HEIGHT = 120;
  const VERTICAL_SPACING = 100;
  const HORIZONTAL_SPACING = 60;
  
  const positionedNodes = nodes.map(node => {
    const level = levelMap.get(node.id) || 0;
    const levelNodes = levels.get(level) || [];
    const index = levelNodes.indexOf(node.id);
    const totalWidth = levelNodes.length * NODE_WIDTH + (levelNodes.length - 1) * HORIZONTAL_SPACING;
    const startX = Math.max(200, window.innerWidth / 2 - totalWidth / 2);
    
    return {
      ...node,
      position: {
        x: startX + index * (NODE_WIDTH + HORIZONTAL_SPACING),
        y: 150 + level * (NODE_HEIGHT + VERTICAL_SPACING)
      }
    };
  });
  
  return positionedNodes;
}

function assignLevels(
  nodeId: string,
  currentLevel: number,
  parentMap: Map<string, string[]>,
  childMap: Map<string, string[]>,
  levelMap: Map<string, number>
): void {
  // 向下遍历子节点
  const children = parentMap.get(nodeId) || [];
  children.forEach(childId => {
    if (!levelMap.has(childId) || levelMap.get(childId)! > currentLevel + 1) {
      levelMap.set(childId, currentLevel + 1);
      assignLevels(childId, currentLevel + 1, parentMap, childMap, levelMap);
    }
  });
  
  // 向上遍历父节点
  const parents = childMap.get(nodeId) || [];
  parents.forEach(parentId => {
    if (!levelMap.has(parentId) || levelMap.get(parentId)! < currentLevel - 1) {
      levelMap.set(parentId, currentLevel - 1);
      assignLevels(parentId, currentLevel - 1, parentMap, childMap, levelMap);
    }
  });
}
```

---

## 4. 组件设计

### 4.1 主组件 FamilyTree.vue

```vue
<template>
  <div class="family-tree-page">
    <!-- 页面头部 -->
    <el-page-header @back="goBack">
      <template #content>
        <span class="page-title">家族树</span>
      </template>
      <template #extra>
        <el-button @click="refreshTree" type="primary" size="small">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
        <el-button @click="addRelation" type="success" size="small">
          <el-icon><Plus /></el-icon>
          添加关系
        </el-button>
      </template>
    </el-page-header>

    <!-- 可视化容器 -->
    <div class="tree-container">
      <VueFlow
        :nodes="localNodes"
        :edges="localEdges"
        :default-zoom="1"
        :min-zoom="0.2"
        :max-zoom="3"
        class="vue-flow-container"
        @node-click="onNodeClick"
        @node-mouse-enter="onNodeMouseEnter"
        @node-mouse-leave="onNodeMouseLeave"
      >
        <Background pattern-color="#aaa" :gap="16" />
        <Controls />
        
        <!-- 自定义节点模板 -->
        <template #node-person="props">
          <div 
            class="family-node"
            :class="{ 
              'is-me': props.data.isMe, 
              'is-deceased': props.data.deathDate,
              'is-hovered': hoveredNode === props.id
            }"
          >
            <div class="node-avatar">
              <span :class="{ 'female': props.data.gender === 'female' }">
                {{ getInitials(props.data.name) }}
              </span>
              <div v-if="props.data.deathDate" class="deceased-badge">逝</div>
            </div>
            <div class="node-name">{{ props.data.name }}</div>
            <div class="node-date">{{ formatDateRange(props.data.birthDate, props.data.deathDate) }}</div>
            
            <!-- 悬停提示 -->
            <div v-if="hoveredNode === props.id" class="relation-tooltip">
              {{ getRelationToMe(props.data.personId) }}
            </div>
            
            <!-- 快捷操作按钮 -->
            <div v-if="hoveredNode === props.id" class="quick-actions">
              <div 
                class="action-btn add-parent"
                @click.stop="quickAddRelation(props.id, 'parent')"
                title="添加父母"
              >
                <el-icon><Plus /></el-icon>
              </div>
              <div 
                class="action-btn add-child"
                @click.stop="quickAddRelation(props.id, 'child')"
                title="添加子女"
              >
                <el-icon><Plus /></el-icon>
              </div>
            </div>
          </div>
        </template>
      </VueFlow>
    </div>
  </div>
</template>
```

### 4.2 节点详情面板

```vue
<template>
  <div v-if="selectedNode" class="node-detail-panel">
    <div class="panel-header">
      <h3>{{ selectedNode.data.name }}</h3>
      <el-button @click="selectedNode = null" size="small">
        <el-icon><Close /></el-icon>
      </el-button>
    </div>
    <div class="panel-content">
      <div class="detail-row">
        <span class="label">性别</span>
        <span class="value">{{ selectedNode.data.gender === 'female' ? '女' : '男' }}</span>
      </div>
      <div class="detail-row">
        <span class="label">出生</span>
        <span class="value">{{ formatDate(selectedNode.data.birthDate) }}</span>
      </div>
      <div class="detail-row">
        <span class="label">逝世</span>
        <span class="value">{{ selectedNode.data.deathDate ? formatDate(selectedNode.data.deathDate) : '-' }}</span>
      </div>
      <div class="detail-actions">
        <el-button @click="editPerson(selectedNode.data.personId)" type="primary" size="small">
          编辑详情
        </el-button>
      </div>
    </div>
  </div>
</template>
```

### 4.3 添加关系弹窗

```vue
<template>
  <el-dialog title="添加家庭关系" v-model="showAddRelation">
    <el-form :model="relationForm" label-width="80px">
      <el-form-item label="父/母亲">
        <el-select v-model="relationForm.parent_person_id" placeholder="选择父/母亲">
          <el-option 
            v-for="p in availablePersons" 
            :key="p.id" 
            :label="p.name" 
            :value="p.id"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="关系类型">
        <el-select v-model="relationForm.parent_type">
          <el-option label="父亲" value="father" />
          <el-option label="母亲" value="mother" />
        </el-select>
      </el-form-item>
      <el-form-item label="子/女儿">
        <el-select v-model="relationForm.child_person_id" placeholder="选择子/女儿">
          <el-option 
            v-for="p in availablePersons" 
            :key="p.id" 
            :label="p.name" 
            :value="p.id"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="关系性质">
        <el-select v-model="relationForm.relation_nature">
          <el-option label="亲生" value="qin" />
          <el-option label="继亲" value="ji" />
          <el-option label="义亲" value="yi" />
        </el-select>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="showAddRelation = false">取消</el-button>
      <el-button @click="submitRelation" type="primary">确认添加</el-button>
    </template>
  </el-dialog>
</template>
```

---

## 5. API 接口设计

### 5.1 获取家族树数据

```python
# app/api/v1/family.py
@router.get("/tree")
async def get_family_tree(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取家族树数据（节点和边）
    
    Returns:
        {
            "nodes": [{
                "id": int,
                "person_id": int,
                "name": str,
                "gender": str,
                "birth_date": str,
                "death_date": str,
                "is_me": bool
            }],
            "edges": [{
                "id": int,
                "source": int,
                "target": int,
                "relation_nature": str
            }]
        }
    """
    # 获取所有家族成员
    family_members = db.query(FamilyMember).filter(
        FamilyMember.user_id == current_user.id
    ).all()
    
    # 获取所有关系
    relations = db.query(FamilyRelation).filter(
        FamilyRelation.user_id == current_user.id
    ).all()
    
    # 获取用户信息（用于确定"我"）
    user_person = db.query(Person).filter(
        Person.user_id == current_user.id
    ).first()
    
    nodes = []
    edges = []
    
    member_id_map = {}
    
    for member in family_members:
        person = db.query(Person).filter(Person.id == member.person_id).first()
        if person:
            member_id_map[member.id] = person.id
            nodes.append({
                "id": member.id,
                "person_id": person.id,
                "name": person.nickname or (person.last_name + person.first_name),
                "gender": person.gender,
                "birth_date": person.birth_date,
                "death_date": person.death_date,
                "is_me": person.id == user_person.id if user_person else False
            })
    
    for relation in relations:
        edges.append({
            "id": relation.id,
            "source": relation.parent_person_id,
            "target": relation.child_person_id,
            "relation_nature": relation.relation_nature
        })
    
    return {"nodes": nodes, "edges": edges}
```

### 5.2 添加家族关系

```python
@router.post("/relation")
async def add_family_relation(
    parent_person_id: int,
    child_person_id: int,
    parent_type: str = "father",
    relation_nature: str = "qin",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    添加家族关系
    
    Args:
        parent_person_id: 父/母亲ID
        child_person_id: 子/女儿ID
        parent_type: father/mother
        relation_nature: qin/ji/yi
    """
    # 检查关系是否已存在
    existing = db.query(FamilyRelation).filter(
        FamilyRelation.user_id == current_user.id,
        FamilyRelation.parent_person_id == parent_person_id,
        FamilyRelation.child_person_id == child_person_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="关系已存在")
    
    # 创建关系
    relation = FamilyRelation(
        user_id=current_user.id,
        parent_person_id=parent_person_id,
        child_person_id=child_person_id,
        parent_type=parent_type,
        relation_nature=relation_nature
    )
    
    db.add(relation)
    db.commit()
    
    # 失效缓存
    invalidate_relation_cache(db, current_user.id)
    
    return {"message": "添加成功"}
```

---

## 6. 样式设计

### 6.1 节点样式

```scss
.family-node {
  width: 160px;
  padding: 12px;
  background: white;
  border: 2px solid #d9d9d9;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  
  &:hover {
    border-color: #409EFF;
    transform: translateY(-2px);
    box-shadow: 0 4px 16px rgba(64, 158, 255, 0.2);
  }
  
  &.is-me {
    border-color: #409EFF;
    background: #E6F7FF;
  }
  
  &.is-deceased {
    opacity: 0.7;
  }
}

.node-avatar {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background: #E6F7FF;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  margin-bottom: 8px;
  
  span {
    font-size: 20px;
    font-weight: bold;
    color: #409EFF;
    
    &.female {
      color: #FF6B6B;
    }
  }
}

.deceased-badge {
  position: absolute;
  bottom: -2px;
  right: -2px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #666;
  color: white;
  font-size: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}
```

### 6.2 连线样式

```scss
.vue-flow__edge-path {
  stroke-width: 2;
  
  // 亲生关系：实线
  &.relation-qin {
    stroke: #409EFF;
    stroke-dasharray: none;
  }
  
  // 继亲/义亲：虚线
  &.relation-ji,
  &.relation-yi {
    stroke: #999;
    stroke-dasharray: 8, 4;
  }
}
```

---

## 7. 交互设计

### 7.1 鼠标交互

| 操作 | 效果 |
|------|------|
| **点击节点** | 显示详情面板 |
| **悬停节点** | 显示亲属关系提示 + 快捷操作按钮 |
| **滚轮** | 缩放画布 |
| **拖拽空白区域** | 平移画布 |
| **拖拽节点** | 移动节点位置 |

### 7.2 快捷操作按钮

```
节点悬停时显示：
    ┌──────────┐
    │   +      │  上方按钮：添加父母
    └──────────┘
         ▼
    ┌──────────┐
    │  节点    │
    │  内容    │
    └──────────┘
         ▼
    ┌──────────┐
    │   +      │  下方按钮：添加子女
    └──────────┘
```

---

## 8. 性能优化

### 8.1 虚拟滚动

对于大型家族树，考虑使用虚拟滚动技术：

```typescript
// 仅渲染可视区域内的节点
function getVisibleNodes(nodes: FamilyTreeNode[], viewport: Viewport): FamilyTreeNode[] {
  return nodes.filter(node => {
    return (
      node.position.x >= viewport.left &&
      node.position.x <= viewport.right &&
      node.position.y >= viewport.top &&
      node.position.y <= viewport.bottom
    );
  });
}
```

### 8.2 缓存布局结果

```typescript
const layoutCache = new Map<string, FamilyTreeNode[]>();

function getLayout(nodes: FamilyTreeNode[], edges: FamilyTreeEdge[]): FamilyTreeNode[] {
  const cacheKey = JSON.stringify({ nodes, edges });
  
  if (layoutCache.has(cacheKey)) {
    return layoutCache.get(cacheKey)!;
  }
  
  const result = calculateLayout(nodes, edges);
  layoutCache.set(cacheKey, result);
  
  return result;
}
```

---

## 9. 扩展性设计

### 9.1 支持的扩展功能

| 功能 | 描述 |
|------|------|
| **颜色主题** | 支持多种配色方案 |
| **导出功能** | 支持导出为图片/PDF |
| **打印功能** | 支持打印家谱树 |
| **共享功能** | 支持生成分享链接 |
| **搜索功能** | 支持搜索家族成员 |

### 9.2 国际化支持

```typescript
const i18n = {
  zh: {
    father: '父亲',
    mother: '母亲',
    son: '儿子',
    daughter: '女儿',
    brother: '兄弟',
    sister: '姐妹'
  },
  en: {
    father: 'Father',
    mother: 'Mother',
    son: 'Son',
    daughter: 'Daughter',
    brother: 'Brother',
    sister: 'Sister'
  }
};
```

---

## 10. 兼容性考虑

| 平台 | 支持情况 | 备注 |
|------|----------|------|
| Chrome | ✅ 完全支持 | 推荐浏览器 |
| Firefox | ✅ 完全支持 | |
| Safari | ✅ 完全支持 | |
| Edge | ✅ 完全支持 | |
| 移动端 | ⚠️ 有限支持 | 触摸交互需要优化 |

---

## 11. 安全考虑

### 11.1 数据权限

```python
# 确保用户只能访问自己的数据
def get_family_tree(current_user: User, db: Session):
    return db.query(FamilyMember).filter(
        FamilyMember.user_id == current_user.id
    ).all()
```

### 11.2 输入验证

```python
# 验证关系数据
def validate_relation(parent_id: int, child_id: int):
    if parent_id == child_id:
        raise HTTPException(status_code=400, detail="不能建立自己与自己的关系")
    
    if parent_id <= 0 or child_id <= 0:
        raise HTTPException(status_code=400, detail="无效的人物ID")
```