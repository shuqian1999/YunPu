# 家谱树可视化详细设计

## 1. 概述

### 1.1 设计目标

家谱树可视化组件负责：
- 将家族关系数据以宝塔式树形结构展示
- 支持初始化流程（首次进入为空状态）
- 提供直观的亲属关系展示（实线表示亲生，虚线表示非亲生）
- 支持快捷添加亲属关系
- 节点不可拖动，保证布局规整

### 1.2 技术选型

| 技术 | 选型 | 理由 |
|------|------|------|
| 可视化库 | Vue Flow | Vue生态原生支持，布局控制灵活 |
| 布局算法 | 自定义宝塔式层级布局 | 家族树结构特殊，需要定制布局，节点不可拖动 |
| 样式框架 | Element Plus | 与项目现有技术栈一致 |

---

## 2. 架构设计

### 2.1 组件结构

```
FamilyTree.vue (主组件)
├── InitialState (初始化状态)
│   ├── EmptyHint (空状态提示)
│   └── InitButton (初始化按钮)
├── VueFlow (可视化容器)
│   ├── Background (背景网格)
│   ├── Controls (控制按钮 - 仅缩放平移)
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
              addFamilyRelation   calculatePagodaLayout
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
  isSpousalLine: boolean; // 是否为配偶连线
}
```

### 3.2 宝塔式布局算法

```typescript
function calculatePagodaLayout(nodes: FamilyTreeNode[], edges: FamilyTreeEdge[]): { nodes: FamilyTreeNode[], edges: FamilyTreeEdge[] } {
  // 1. 构建父子关系映射
  const parentMap = new Map<string, string[]>();
  const childMap = new Map<string, string[]>();
  const spouseMap = new Map<string, string[]>();
  
  edges.forEach(edge => {
    if (edge.isSpousalLine) {
      if (!spouseMap.has(edge.source)) spouseMap.set(edge.source, []);
      if (!spouseMap.has(edge.target)) spouseMap.set(edge.target, []);
      spouseMap.get(edge.source)!.push(edge.target);
      spouseMap.get(edge.target)!.push(edge.source);
    } else {
      if (!parentMap.has(edge.source)) parentMap.set(edge.source, []);
      if (!childMap.has(edge.target)) childMap.set(edge.target, []);
      parentMap.get(edge.source)!.push(edge.target);
      childMap.get(edge.target)!.push(edge.source);
    }
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
  
  // 3. 计算每层节点位置（考虑配偶）
  const levels: Map<number, { nodes: string[], spouses: Map<string, string[]> }> = new Map();
  
  levelMap.forEach((level, nodeId) => {
    if (!levels.has(level)) {
      levels.set(level, { nodes: [], spouses: new Map() });
    }
    levels.get(level)!.nodes.push(nodeId);
    
    // 记录配偶关系
    const spouses = spouseMap.get(nodeId) || [];
    spouses.forEach(spouseId => {
      if (!levels.get(level)!.spouses.has(nodeId)) {
        levels.get(level)!.spouses.set(nodeId, []);
      }
      levels.get(level)!.spouses.get(nodeId)!.push(spouseId);
    });
  });
  
  // 4. 计算坐标（宝塔式布局）
  const NODE_WIDTH = 160;
  const NODE_HEIGHT = 100;
  const VERTICAL_SPACING = 120;
  const HORIZONTAL_SPACING = 80;
  const SPOUSE_GAP = 40; // 配偶之间的间距
  
  const positionedNodes: FamilyTreeNode[] = [];
  const newEdges: FamilyTreeEdge[] = [];
  
  levels.forEach((levelData, level) => {
    const allNodes = expandWithSpouses(levelData.nodes, levelData.spouses);
    const totalWidth = allNodes.length * NODE_WIDTH + (allNodes.length - 1) * HORIZONTAL_SPACING;
    const startX = Math.max(200, window.innerWidth / 2 - totalWidth / 2);
    
    const nodePositionMap = new Map<string, { x: number; y: number }>();
    
    allNodes.forEach((nodeId, index) => {
      const x = startX + index * (NODE_WIDTH + HORIZONTAL_SPACING);
      const y = 150 + level * (NODE_HEIGHT + VERTICAL_SPACING);
      
      nodePositionMap.set(nodeId, { x, y });
      
      const originalNode = nodes.find(n => n.id === nodeId);
      if (originalNode) {
        positionedNodes.push({
          ...originalNode,
          position: { x, y }
        });
      }
    });
    
    // 生成配偶连线（从两人底部延伸出水平线，中间汇合后向下延伸）
    levelData.spouses.forEach((spouses, nodeId) => {
      spouses.forEach(spouseId => {
        if (nodePositionMap.has(nodeId) && nodePositionMap.has(spouseId)) {
          const nodePos = nodePositionMap.get(nodeId)!;
          const spousePos = nodePositionMap.get(spouseId)!;
          
          // 计算配偶中点
          const midX = (nodePos.x + spousePos.x) / 2;
          const nodeBottomY = nodePos.y + NODE_HEIGHT / 2;
          
          // 垂直线向下延伸的起点（在配偶连线下方）
          const verticalStartY = nodeBottomY + 20;
          
          // 第一条边：从配偶1底部向右延伸到中点
          newEdges.push({
            id: `spouse-left-${nodeId}-${spouseId}`,
            source: nodeId,
            target: `spouse-mid-${nodeId}-${spouseId}`,
            relationNature: 'qin',
            isSpousalLine: true,
            startPoint: { x: nodePos.x + NODE_WIDTH / 2, y: nodeBottomY },
            endPoint: { x: midX, y: nodeBottomY }
          });
          
          // 第二条边：从配偶2底部向左延伸到中点
          newEdges.push({
            id: `spouse-right-${nodeId}-${spouseId}`,
            source: spouseId,
            target: `spouse-mid-${nodeId}-${spouseId}`,
            relationNature: 'qin',
            isSpousalLine: true,
            startPoint: { x: spousePos.x + NODE_WIDTH / 2, y: nodeBottomY },
            endPoint: { x: midX, y: nodeBottomY }
          });
        }
      });
    });
    
    // 生成子女连线（从配偶连线中点向下延伸，90度弯折）
    if (level > 0) {
      const parentLevel = levels.get(level - 1);
      if (parentLevel) {
        const parentNodes = expandWithSpouses(parentLevel.nodes, parentLevel.spouses);
        const parentPosMap = new Map<string, { x: number; y: number }>();
        
        // 获取上层节点位置
        positionedNodes.forEach(node => {
          if (levelMap.get(node.id) === level - 1) {
            parentPosMap.set(node.id, node.position);
          }
        });
        
        // 计算子女与父母的连接
        const childGroups = groupChildrenByParents(levelData.nodes, childMap, spouseMap);
        
        childGroups.forEach((children, parentIds) => {
          const parentPositions = parentIds.map(id => parentPosMap.get(id)).filter(Boolean);
          if (parentPositions.length === 0) return;
          
          // 计算父母连线中点
          const midX = parentPositions.reduce((sum, p) => sum + p!.x, 0) / parentPositions.length;
          const parentBottomY = parentPositions[0]!.y + NODE_HEIGHT / 2;
          
          // 计算子女位置范围
          const childPositions = children.map(c => nodePositionMap.get(c)).filter(Boolean);
          if (childPositions.length === 0) return;
          
          const childMidX = childPositions.reduce((sum, c) => sum + c!.x, 0) / childPositions.length;
          const childTopY = childPositions[0]!.y - NODE_HEIGHT / 2;
          
          // 创建垂直线段（从父母中点向下）
          const verticalLineId = `vertical-${parentIds.join('-')}`;
          newEdges.push({
            id: verticalLineId,
            source: parentIds[0], // 使用第一个父母节点作为source
            target: children[0],  // 使用第一个子女节点作为target
            relationNature: 'qin',
            isSpousalLine: false
          });
        });
      }
    }
  });
  
  return { nodes: positionedNodes, edges: newEdges };
}

function expandWithSpouses(nodes: string[], spouses: Map<string, string[]>): string[] {
  const result: string[] = [];
  const processed = new Set<string>();
  
  nodes.forEach(nodeId => {
    if (processed.has(nodeId)) return;
    
    result.push(nodeId);
    processed.add(nodeId);
    
    const spouseList = spouses.get(nodeId) || [];
    spouseList.forEach(spouseId => {
      if (!processed.has(spouseId)) {
        result.push(spouseId);
        processed.add(spouseId);
      }
    });
  });
  
  return result;
}

function groupChildrenByParents(children: string[], childMap: Map<string, string[]>, spouseMap: Map<string, string[]>): Map<string[], string[]> {
  const groups = new Map<string, string[]>();
  
  children.forEach(childId => {
    const parents = childMap.get(childId) || [];
    if (parents.length === 0) return;
    
    // 获取所有相关父母（包括配偶）
    const allParents = new Set<string>();
    parents.forEach(parentId => {
      allParents.add(parentId);
      const spouses = spouseMap.get(parentId) || [];
      spouses.forEach(s => allParents.add(s));
    });
    
    const key = Array.from(allParents).sort().join('-');
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key)!.push(childId);
  });
  
  // 转换为以父母数组为key的Map
  const result = new Map<string[], string[]>();
  groups.forEach((childrenList, key) => {
    result.set(key.split('-'), childrenList);
  });
  
  return result;
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

    <!-- 初始化状态 -->
    <div v-if="!treeInitialized" class="empty-state">
      <div class="empty-icon">
        <el-icon><Tree /></el-icon>
      </div>
      <h3>家族树为空</h3>
      <p>点击下方按钮初始化家族树</p>
      <el-button @click="initializeTree" type="primary">
        <el-icon><Plus /></el-icon>
        初始化家族树
      </el-button>
    </div>

    <!-- 可视化容器 -->
    <div v-else class="tree-container">
      <VueFlow
        :nodes="localNodes"
        :edges="localEdges"
        :default-zoom="1"
        :min-zoom="0.2"
        :max-zoom="3"
        :nodes-draggable="false"  <!-- 节点不可拖动 -->
        :edges-updatable="false"  <!-- 连线不可修改 -->
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

### 4.2 初始化状态组件

```vue
<template>
  <div class="empty-state">
    <div class="empty-icon">
      <el-icon><Tree /></el-icon>
    </div>
    <h3>家族树为空</h3>
    <p>点击下方按钮根据现有人物关系初始化家族树</p>
    <el-button @click="initializeTree" type="primary">
      <el-icon><Plus /></el-icon>
      初始化家族树
    </el-button>
  </div>
</template>
```

### 4.3 节点详情面板

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

### 4.4 添加关系弹窗

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
                "relation_nature": str,
                "is_spousal": bool
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
            "source": relation.parent_id,
            "target": relation.child_id,
            "relation_nature": relation.relation_nature,
            "is_spousal": False
        })
    
    # 检测配偶关系
    spouse_relations = detect_spousal_relations(relations, family_members)
    edges.extend(spouse_relations)
    
    return {"nodes": nodes, "edges": edges}

def detect_spousal_relations(relations: list, members: list) -> list:
    """
    检测配偶关系（共同拥有子女的成员）
    """
    child_parents = {}
    
    for relation in relations:
        child_id = relation.child_id
        if child_id not in child_parents:
            child_parents[child_id] = set()
        child_parents[child_id].add(relation.parent_id)
    
    spouse_pairs = set()
    
    for child_id, parents in child_parents.items():
        if len(parents) >= 2:
            parent_list = list(parents)
            for i in range(len(parent_list)):
                for j in range(i + 1, len(parent_list)):
                    pair = tuple(sorted([parent_list[i], parent_list[j]]))
                    spouse_pairs.add(pair)
    
    result = []
    for pair in spouse_pairs:
        result.append({
            "id": f"spouse-{pair[0]}-{pair[1]}",
            "source": pair[0],
            "target": pair[1],
            "relation_nature": "qin",
            "is_spousal": True
        })
    
    return result
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
        FamilyRelation.parent_id == parent_person_id,
        FamilyRelation.child_id == child_person_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="关系已存在")
    
    # 创建关系
    relation = FamilyRelation(
        user_id=current_user.id,
        parent_id=parent_person_id,
        child_id=child_person_id,
        parent_type=parent_type,
        relation_nature=relation_nature
    )
    
    db.add(relation)
    db.commit()
    
    return {"message": "添加成功"}
```

---

## 6. 样式设计

### 6.1 空状态样式

```scss
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 400px;
  text-align: center;
  
  .empty-icon {
    width: 80px;
    height: 80px;
    border-radius: 50%;
    background: #E6F7FF;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 20px;
    
    :deep(.el-icon) {
      font-size: 40px;
      color: #409EFF;
    }
  }
  
  h3 {
    font-size: 20px;
    color: #303133;
    margin-bottom: 8px;
  }
  
  p {
    font-size: 14px;
    color: #909399;
    margin-bottom: 24px;
  }
}
```

### 6.2 节点样式

```scss
.family-node {
  width: 140px;
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
  user-select: none;
  
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
  width: 45px;
  height: 45px;
  border-radius: 50%;
  background: #E6F7FF;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  margin-bottom: 8px;
  
  span {
    font-size: 18px;
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
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #666;
  color: white;
  font-size: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.node-name {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.node-date {
  font-size: 12px;
  color: #909399;
}
```

### 6.3 连线样式

```scss
.vue-flow__edge-path {
  stroke-width: 2;
  
  // 配偶连线：水平实线
  &.spousal-line {
    stroke: #409EFF;
    stroke-dasharray: none;
  }
  
  // 亲生关系：实线
  &.relation-qin {
    stroke: #409EFF;
    stroke-dasharray: none;
  }
  
  // 继亲：虚线
  &.relation-ji {
    stroke: #999;
    stroke-dasharray: 8, 4;
  }
  
  // 义亲：点状虚线
  &.relation-yi {
    stroke: #999;
    stroke-dasharray: 2, 6;
  }
}

// 连线交叉处理
.vue-flow__edge {
  &.cross-over {
    z-index: 10;
    
    .vue-flow__edge-path {
      stroke: #FF6B6B;
      stroke-width: 3;
    }
    
    &::before {
      content: '';
      position: absolute;
      width: 12px;
      height: 12px;
      background: white;
      border: 2px solid #FF6B6B;
      border-radius: 50%;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      z-index: 11;
    }
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
| **拖拽节点** | 无效果（节点不可拖动） |

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

## 8. 布局规范

### 8.1 宝塔式布局规则

```
          爷爷         奶奶
          ┗━━━━┳━━━━┛
                   │
          爸爸         妈妈
          ┗━━━━┳━━━━┛
                   │
           我        配偶
           ┗━━┳━━┛
               │
       ┌──────┴──────┐
       ▼             ▼
     儿子           女儿
```

### 8.2 连线规范

| 连线类型 | 样式 | 说明 |
|----------|------|------|
| 配偶连线 | 底部水平线汇合 | 从两人底部延伸水平线到中点汇合 |
| 亲子连线 | 垂直实线（向下延伸分叉） | 从配偶汇合点向下延伸，分叉连接到子女 |
| 亲生关系 | 实线 | `relation_nature = qin` |
| 继亲关系 | 虚线（8,4） | `relation_nature = ji` |
| 义亲关系 | 点状虚线（2,6） | `relation_nature = yi` |

### 8.3 连线交叉处理

对于二婚等复杂情况导致的连线交叉：

```
        父亲 ───────── 母亲
              │
              │  (实线)
              ▼
            子女
              │
              │  (虚线 - 继亲)
              ▼
        继母/继父 ────── 新配偶
```

交叉点处理：
- 检测连线交叉位置
- 在交叉点添加标记（红色圆点）
- 上层连线在交叉点处略微抬高

---

## 9. 性能优化

### 9.1 缓存布局结果

```typescript
const layoutCache = new Map<string, { nodes: FamilyTreeNode[], edges: FamilyTreeEdge[] }>();

function getLayout(nodes: FamilyTreeNode[], edges: FamilyTreeEdge[]): { nodes: FamilyTreeNode[], edges: FamilyTreeEdge[] } {
  const cacheKey = JSON.stringify({ nodes, edges });
  
  if (layoutCache.has(cacheKey)) {
    return layoutCache.get(cacheKey)!;
  }
  
  const result = calculatePagodaLayout(nodes, edges);
  layoutCache.set(cacheKey, result);
  
  return result;
}
```

---

## 10. 安全考虑

### 10.1 数据权限

```python
def get_family_tree(current_user: User, db: Session):
    return db.query(FamilyMember).filter(
        FamilyMember.user_id == current_user.id
    ).all()
```

### 10.2 输入验证

```python
def validate_relation(parent_id: int, child_id: int):
    if parent_id == child_id:
        raise HTTPException(status_code=400, detail="不能建立自己与自己的关系")
    
    if parent_id <= 0 or child_id <= 0:
        raise HTTPException(status_code=400, detail="无效的人物ID")
```