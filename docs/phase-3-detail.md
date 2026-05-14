# 阶段三：人物详情与家谱可视化

## 阶段概述

**周期**：2-3周  
**目标**：实现人物详情页、家谱页和谱系可视化功能

---

## 任务分解

### 3.1 人物详情页开发

#### 后端 API

##### 人物详情接口
```python
# app/api/persons.py（续）
@router.get("/{person_id}/events", response_model=List[EventResponse])
async def get_person_events(
    person_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    events = db.query(Event).filter(
        Event.person_id == person_id,
        Event.user_id == current_user.id
    ).order_by(Event.event_date.desc()).all()
    return events

@router.get("/{person_id}/reminders", response_model=List[ReminderResponse])
async def get_person_reminders(
    person_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    reminders = db.query(Reminder).filter(
        Reminder.person_id == person_id,
        Reminder.user_id == current_user.id,
        Reminder.enabled == True
    ).order_by(Reminder.remind_date.asc()).all()
    return reminders

@router.get("/{person_id}/relations")
async def get_person_relations(
    person_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from app.models.family_member import FamilyMember
    from app.models.family_relation import FamilyRelation
    
    family_member = db.query(FamilyMember).filter(
        FamilyMember.person_id == person_id,
        FamilyMember.user_id == current_user.id
    ).first()
    
    if not family_member:
        return {"parents": [], "children": []}
    
    parents = db.query(FamilyRelation).filter(
        FamilyRelation.child_id == family_member.id
    ).all()
    
    children = db.query(FamilyRelation).filter(
        FamilyRelation.parent_id == family_member.id
    ).all()
    
    return {
        "parents": [
            {
                "id": parent.parent_id,
                "parent_type": parent.parent_type,
                "relation_nature": parent.relation_nature
            }
            for parent in parents
        ],
        "children": [
            {
                "id": child.child_id,
                "parent_type": child.parent_type,
                "relation_nature": child.relation_nature
            }
            for child in children
        ]
    }
```

#### 前端人物详情页

##### PersonDetail.vue
```vue
<template>
  <div class="person-detail-container">
    <div class="detail-layout">
      <div class="left-panel">
        <el-card class="reminders-card">
          <template #header>
            <div class="card-header">
              <span class="card-title">日期提醒</span>
              <el-button text type="primary" @click="handleAddReminder">
                <el-icon><Plus /></el-icon>
                添加
              </el-button>
            </div>
          </template>
          
          <div v-loading="remindersLoading" class="reminders-list">
            <div
              v-for="reminder in reminders"
              :key="reminder.id"
              class="reminder-item"
            >
              <div class="reminder-date">
                {{ formatDate(reminder.remind_date) }}
                <el-tag v-if="reminder.is_lunar" size="small" type="warning">农历</el-tag>
              </div>
              <div class="reminder-title">{{ reminder.title }}</div>
            </div>
            
            <el-empty
              v-if="!remindersLoading && reminders.length === 0"
              description="暂无提醒"
              :image-size="80"
            />
          </div>
        </el-card>
        
        <el-card class="events-card">
          <template #header>
            <div class="card-header">
              <span class="card-title">事件时间轴</span>
              <el-button text type="primary" @click="handleAddEvent">
                <el-icon><Plus /></el-icon>
                添加
              </el-button>
            </div>
          </template>
          
          <el-timeline v-loading="eventsLoading" class="events-timeline">
            <el-timeline-item
              v-for="event in events"
              :key="event.id"
              :timestamp="formatDate(event.event_date)"
              placement="top"
              :color="event.event_type_color"
            >
              <div class="event-item">
                <div class="event-title">{{ event.title }}</div>
                <div v-if="event.description" class="event-description">
                  {{ event.description }}
                </div>
                <div v-if="event.location" class="event-location">
                  <el-icon><Location /></el-icon>
                  {{ event.location }}
                </div>
              </div>
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </div>
      
      <div class="right-panel">
        <el-card class="person-info-card">
          <div class="person-header">
            <el-avatar :size="100" :src="person.avatar_url">
              {{ person.nickname || person.first_name }}
            </el-avatar>
            <div class="person-name">
              {{ person.first_name }}{{ person.last_name }}
            </div>
            <div v-if="person.nickname" class="person-nickname">
              {{ person.nickname }}
            </div>
            <el-tag v-if="person.is_me" type="primary" size="large">我</el-tag>
          </div>
          
          <el-divider />
          
          <div class="person-details">
            <div v-if="person.birth_date" class="detail-item">
              <span class="detail-label">出生日期</span>
              <span class="detail-value">{{ formatDate(person.birth_date) }}</span>
            </div>
            
            <div v-if="person.death_date" class="detail-item">
              <span class="detail-label">逝世日期</span>
              <span class="detail-value">{{ formatDate(person.death_date) }}</span>
            </div>
            
            <div v-if="person.gender" class="detail-item">
              <span class="detail-label">性别</span>
              <span class="detail-value">{{ getGenderText(person.gender) }}</span>
            </div>
            
            <div v-if="person.country" class="detail-item">
              <span class="detail-label">国家</span>
              <span class="detail-value">{{ person.country }}</span>
            </div>
            
            <div v-if="person.hometown" class="detail-item">
              <span class="detail-label">故乡</span>
              <span class="detail-value">{{ person.hometown }}</span>
            </div>
            
            <div v-if="person.residence" class="detail-item">
              <span class="detail-label">现居地</span>
              <span class="detail-value">{{ person.residence }}</span>
            </div>
          </div>
          
          <el-divider />
          
          <div class="person-relations">
            <div class="relation-section">
              <div class="relation-title">父母</div>
              <div class="relation-list">
                <div
                  v-for="parent in relations.parents"
                  :key="parent.id"
                  class="relation-item"
                >
                  <el-tag :type="parent.relation_nature === 'qin' ? 'primary' : 'info'">
                    {{ getParentTypeText(parent.parent_type) }}
                  </el-tag>
                </div>
                <el-empty
                  v-if="relations.parents.length === 0"
                  description="暂无父母"
                  :image-size="60"
                />
              </div>
            </div>
            
            <div class="relation-section">
              <div class="relation-title">子女</div>
              <div class="relation-list">
                <div
                  v-for="child in relations.children"
                  :key="child.id"
                  class="relation-item"
                >
                  <el-tag :type="child.relation_nature === 'qin' ? 'primary' : 'info'">
                    {{ getChildTypeText(child.parent_type) }}
                  </el-tag>
                </div>
                <el-empty
                  v-if="relations.children.length === 0"
                  description="暂无子女"
                  :image-size="60"
                />
              </div>
            </div>
          </div>
          
          <div class="person-actions">
            <el-button type="primary" @click="handleEdit">
              <el-icon><Edit /></el-icon>
              编辑
            </el-button>
            <el-button type="danger" @click="handleDelete">
              <el-icon><Delete /></el-icon>
              删除
            </el-button>
          </div>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getPerson, deletePerson } from '@/api/persons'
import { getPersonEvents } from '@/api/events'
import { getPersonReminders } from '@/api/reminders'
import { getPersonRelations } from '@/api/relations'
import { formatDate } from '@/utils/date'

const route = useRoute()
const router = useRouter()
const personId = route.params.id

const person = ref({})
const events = ref([])
const reminders = ref([])
const relations = ref({ parents: [], children: [] })
const eventsLoading = ref(false)
const remindersLoading = ref(false)

const loadPerson = async () => {
  try {
    person.value = await getPerson(personId)
  } catch (error) {
    ElMessage.error('加载人物信息失败')
    router.push('/persons')
  }
}

const loadEvents = async () => {
  eventsLoading.value = true
  try {
    events.value = await getPersonEvents(personId)
  } catch (error) {
    ElMessage.error('加载事件失败')
  } finally {
    eventsLoading.value = false
  }
}

const loadReminders = async () => {
  remindersLoading.value = true
  try {
    reminders.value = await getPersonReminders(personId)
  } catch (error) {
    ElMessage.error('加载提醒失败')
  } finally {
    remindersLoading.value = false
  }
}

const loadRelations = async () => {
  try {
    relations.value = await getPersonRelations(personId)
  } catch (error) {
    ElMessage.error('加载关系失败')
  }
}

const getGenderText = (gender) => {
  const map = { 0: '未知', 1: '男', 2: '女' }
  return map[gender] || '未知'
}

const getParentTypeText = (type) => {
  const map = { father: '父亲', mother: '母亲' }
  return map[type] || type
}

const getChildTypeText = (type) => {
  const map = { father: '儿子', mother: '女儿' }
  return map[type] || type
}

const handleEdit = () => {
  router.push(`/persons/${personId}/edit`)
}

const handleDelete = async () => {
  try {
    await ElMessageBox.confirm('确定要删除这个人物吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await deletePerson(personId)
    ElMessage.success('删除成功')
    router.push('/persons')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const handleAddEvent = () => {
  router.push(`/events/create?person_id=${personId}`)
}

const handleAddReminder = () => {
  router.push(`/reminders/create?person_id=${personId}`)
}

onMounted(() => {
  loadPerson()
  loadEvents()
  loadReminders()
  loadRelations()
})
</script>

<style scoped lang="scss">
.person-detail-container {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
}

.detail-layout {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 16px;
}

.left-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.right-panel {
  position: sticky;
  top: 24px;
  height: fit-content;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-size: 18px;
  font-weight: 500;
  color: #303133;
}

.reminders-list {
  max-height: 400px;
  overflow-y: auto;
}

.reminder-item {
  padding: 12px 0;
  border-bottom: 1px solid #E4E7ED;
  
  &:last-child {
    border-bottom: none;
  }
}

.reminder-date {
  font-size: 14px;
  color: #409EFF;
  font-weight: 500;
  margin-bottom: 4px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.reminder-title {
  font-size: 14px;
  color: #303133;
}

.events-timeline {
  padding: 8px 0;
}

.event-item {
  padding: 8px 0;
}

.event-title {
  font-size: 16px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 4px;
}

.event-description {
  font-size: 14px;
  color: #606266;
  margin-bottom: 4px;
  line-height: 1.6;
}

.event-location {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: #909399;
}

.person-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 16px;
}

.person-name {
  font-size: 24px;
  font-weight: 500;
  color: #303133;
  margin-top: 12px;
  margin-bottom: 4px;
}

.person-nickname {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}

.person-details {
  margin-bottom: 16px;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid #F5F7FA;
  
  &:last-child {
    border-bottom: none;
  }
}

.detail-label {
  font-size: 14px;
  color: #909399;
}

.detail-value {
  font-size: 14px;
  color: #303133;
  font-weight: 500;
}

.person-relations {
  margin-bottom: 16px;
}

.relation-section {
  margin-bottom: 16px;
  
  &:last-child {
    margin-bottom: 0;
  }
}

.relation-title {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 8px;
}

.relation-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.relation-item {
  cursor: pointer;
}

.person-actions {
  display: flex;
  gap: 8px;
  
  .el-button {
    flex: 1;
  }
}
</style>
```

---

### 3.2 家谱页基础框架

#### 后端 API

##### 家谱数据接口
```python
# app/api/family.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.family_member import FamilyMember
from app.models.family_relation import FamilyRelation
from app.models.person import Person
from app.models.family_calculated_relation import FamilyCalculatedRelation
from app.utils.security import get_current_user
from app.models.user import User

router = APIRouter(prefix="/family", tags=["家谱"])

@router.get("/tree")
async def get_family_tree(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    family_members = db.query(FamilyMember).filter(
        FamilyMember.user_id == current_user.id
    ).all()
    
    relations = db.query(FamilyRelation).filter(
        FamilyRelation.user_id == current_user.id
    ).all()
    
    nodes = []
    edges = []
    
    for member in family_members:
        person = db.query(Person).filter(Person.id == member.person_id).first()
        if person:
            nodes.append({
                "id": member.id,
                "name": person.nickname or f"{person.first_name}{person.last_name}",
                "gender": person.gender,
                "birth_date": person.birth_date.isoformat() if person.birth_date else None,
                "death_date": person.death_date.isoformat() if person.death_date else None,
                "avatar_url": person.avatar_url,
                "is_me": person.is_me
            })
    
    for relation in relations:
        edges.append({
            "id": relation.id,
            "source": relation.parent_id,
            "target": relation.child_id,
            "parent_type": relation.parent_type,
            "relation_nature": relation.relation_nature
        })
    
    return {
        "nodes": nodes,
        "edges": edges
    }

@router.get("/relations")
async def get_calculated_relations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    relations = db.query(FamilyCalculatedRelation).filter(
        FamilyCalculatedRelation.user_id == current_user.id
    ).all()
    
    return [
        {
            "person_id": relation.person_id,
            "relation_name": relation.relation_name,
            "relation_level": relation.relation_level,
            "is_blood": relation.is_blood
        }
        for relation in relations
    ]

@router.post("/recalculate")
async def recalculate_relations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from app.services.family_service import FamilyService
    
    service = FamilyService(db)
    service.recalculate_all_relations(current_user.id)
    
    return {"message": "关系重新计算成功"}
```

#### 前端家谱页

##### FamilyTree.vue
```vue
<template>
  <div class="family-tree-container">
    <div class="tree-header">
      <h2 class="page-title">家谱</h2>
      <div class="tree-actions">
        <el-button @click="handleZoomIn">
          <el-icon><ZoomIn /></el-icon>
        </el-button>
        <el-button @click="handleZoomOut">
          <el-icon><ZoomOut /></el-icon>
        </el-button>
        <el-button @click="handleReset">
          <el-icon><Refresh /></el-icon>
        </el-button>
        <el-button type="primary" @click="handleRecalculate">
          <el-icon><Refresh /></el-icon>
          重新计算
        </el-button>
      </div>
    </div>
    
    <el-card class="tree-card">
      <div v-loading="loading" class="tree-canvas" ref="treeCanvas">
        <svg
          :width="canvasWidth"
          :height="canvasHeight"
          :viewBox="`0 0 ${canvasWidth} ${canvasHeight}`"
        >
          <defs>
            <marker
              id="arrowhead"
              markerWidth="10"
              markerHeight="7"
              refX="9"
              refY="3.5"
              orient="auto"
            >
              <polygon points="0 0, 10 3.5, 0 7" fill="#409EFF" />
            </marker>
          </defs>
          
          <g :transform="`translate(${panX}, ${panY}) scale(${zoom})`">
            <line
              v-for="edge in edges"
              :key="edge.id"
              :x1="getNodeX(edge.source)"
              :y1="getNodeY(edge.source)"
              :x2="getNodeX(edge.target)"
              :y2="getNodeY(edge.target)"
              :stroke="edge.relation_nature === 'qin' ? '#409EFF' : '#909399'"
              :stroke-width="2"
              :stroke-dasharray="edge.relation_nature === 'qin' ? 'none' : '5,5'"
              marker-end="url(#arrowhead)"
            />
            
            <g
              v-for="node in nodes"
              :key="node.id"
              :transform="`translate(${getNodeX(node.id)}, ${getNodeY(node.id)})`"
              class="node-group"
              @click="handleNodeClick(node)"
            >
              <circle
                :r="30"
                :fill="node.gender === 1 ? '#E1F3FF' : '#FFE1E1'"
                :stroke="node.is_me ? '#409EFF' : '#E4E7ED'"
                :stroke-width="node.is_me ? 3 : 1"
              />
              
              <text
                x="0"
                y="5"
                text-anchor="middle"
                font-size="12"
                fill="#303133"
              >
                {{ node.name }}
              </text>
              
              <circle
                v-if="node.death_date"
                cx="20"
                cy="-20"
                r="4"
                fill="#C0C4CC"
                class="death-marker"
              />
            </g>
          </g>
        </svg>
      </div>
    </el-card>
    
    <el-dialog v-model="relationDialogVisible" title="人物关系" width="500px">
      <div v-if="selectedNode" class="relation-info">
        <div class="info-item">
          <span class="info-label">姓名：</span>
          <span class="info-value">{{ selectedNode.name }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">性别：</span>
          <span class="info-value">{{ getGenderText(selectedNode.gender) }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">出生日期：</span>
          <span class="info-value">{{ formatDate(selectedNode.birth_date) }}</span>
        </div>
        <div v-if="selectedNode.death_date" class="info-item">
          <span class="info-label">逝世日期：</span>
          <span class="info-value">{{ formatDate(selectedNode.death_date) }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">关系：</span>
          <span class="info-value">{{ getRelationName(selectedNode.id) }}</span>
        </div>
      </div>
      
      <template #footer>
        <el-button @click="relationDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="handleViewPerson">查看详情</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getFamilyTree, recalculateRelations } from '@/api/family'
import { getCalculatedRelations } from '@/api/relations'
import { formatDate } from '@/utils/date'

const router = useRouter()
const loading = ref(false)
const nodes = ref([])
const edges = ref([])
const relations = ref([])
const zoom = ref(1)
const panX = ref(0)
const panY = ref(0)
const canvasWidth = ref(1200)
const canvasHeight = ref(800)
const treeCanvas = ref(null)
const selectedNode = ref(null)
const relationDialogVisible = ref(false)

const nodePositions = computed(() => {
  const positions = {}
  const levelMap = {}
  
  nodes.value.forEach(node => {
    const level = getRelationLevel(node.id)
    if (!levelMap[level]) {
      levelMap[level] = []
    }
    levelMap[level].push(node)
  })
  
  Object.keys(levelMap).forEach((level, index) => {
    const levelNodes = levelMap[level]
    const levelY = 100 + index * 150
    const levelWidth = levelNodes.length * 120
    const startX = (canvasWidth.value - levelWidth) / 2 + 60
    
    levelNodes.forEach((node, nodeIndex) => {
      positions[node.id] = {
        x: startX + nodeIndex * 120,
        y: levelY
      }
    })
  })
  
  return positions
})

const loadFamilyTree = async () => {
  loading.value = true
  try {
    const data = await getFamilyTree()
    nodes.value = data.nodes
    edges.value = data.edges
    relations.value = await getCalculatedRelations()
  } catch (error) {
    ElMessage.error('加载家谱失败')
  } finally {
    loading.value = false
  }
}

const getNodeX = (nodeId) => {
  return nodePositions.value[nodeId]?.x || 0
}

const getNodeY = (nodeId) => {
  return nodePositions.value[nodeId]?.y || 0
}

const getRelationLevel = (nodeId) => {
  const relation = relations.value.find(r => r.person_id === nodeId)
  return relation?.relation_level || 0
}

const getRelationName = (nodeId) => {
  const relation = relations.value.find(r => r.person_id === nodeId)
  return relation?.relation_name || '未知'
}

const getGenderText = (gender) => {
  const map = { 0: '未知', 1: '男', 2: '女' }
  return map[gender] || '未知'
}

const handleZoomIn = () => {
  zoom.value = Math.min(zoom.value * 1.2, 3)
}

const handleZoomOut = () => {
  zoom.value = Math.max(zoom.value / 1.2, 0.3)
}

const handleReset = () => {
  zoom.value = 1
  panX.value = 0
  panY.value = 0
}

const handleRecalculate = async () => {
  try {
    await recalculateRelations()
    ElMessage.success('关系重新计算成功')
    loadFamilyTree()
  } catch (error) {
    ElMessage.error('重新计算失败')
  }
}

const handleNodeClick = (node) => {
  selectedNode.value = node
  relationDialogVisible.value = true
}

const handleViewPerson = () => {
  relationDialogVisible.value = false
  router.push(`/persons/${selectedNode.value.person_id}`)
}

onMounted(() => {
  loadFamilyTree()
})
</script>

<style scoped lang="scss">
.family-tree-container {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
}

.tree-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-title {
  font-size: 24px;
  font-weight: 500;
  color: #303133;
}

.tree-actions {
  display: flex;
  gap: 8px;
}

.tree-card {
  height: calc(100vh - 150px);
}

.tree-canvas {
  width: 100%;
  height: 100%;
  overflow: auto;
  background: #FFFFFF;
}

.node-group {
  cursor: pointer;
  transition: all 0.3s;
  
  &:hover {
    circle:first-child {
      stroke: #409EFF;
      stroke-width: 2;
    }
  }
}

.death-marker {
  &:hover {
    fill: #909399;
  }
}

.relation-info {
  padding: 16px 0;
}

.info-item {
  display: flex;
  padding: 8px 0;
  border-bottom: 1px solid #F5F7FA;
  
  &:last-child {
    border-bottom: none;
  }
}

.info-label {
  width: 100px;
  font-size: 14px;
  color: #909399;
}

.info-value {
  flex: 1;
  font-size: 14px;
  color: #303133;
  font-weight: 500;
}
</style>
```

---

### 3.3 关系计算服务

#### 后端服务
```python
# app/services/family_service.py
from sqlalchemy.orm import Session
from app.models.family_member import FamilyMember
from app.models.family_relation import FamilyRelation
from app.models.family_calculated_relation import FamilyCalculatedRelation
from app.models.person import Person
from typing import Dict, List, Optional

class FamilyService:
    def __init__(self, db: Session):
        self.db = db
    
    def recalculate_all_relations(self, user_id: int):
        me_person = self.db.query(Person).filter(
            Person.user_id == user_id,
            Person.is_me == True
        ).first()
        
        if not me_person:
            return
        
        me_member = self.db.query(FamilyMember).filter(
            FamilyMember.person_id == me_person.id
        ).first()
        
        if not me_member:
            return
        
        self.db.query(FamilyCalculatedRelation).filter(
            FamilyCalculatedRelation.user_id == user_id
        ).delete()
        
        all_members = self.db.query(FamilyMember).filter(
            FamilyMember.user_id == user_id
        ).all()
        
        for member in all_members:
            if member.id == me_member.id:
                continue
            
            relation = self._calculate_relation(me_member, member)
            if relation:
                calculated_relation = FamilyCalculatedRelation(
                    user_id=user_id,
                    person_id=member.person_id,
                    relation_name=relation['name'],
                    relation_level=relation['level'],
                    relation_path=relation['path'],
                    is_blood=relation['is_blood']
                )
                self.db.add(calculated_relation)
        
        self.db.commit()
    
    def _calculate_relation(self, from_member: FamilyMember, to_member: FamilyMember) -> Optional[Dict]:
        path = self._find_path(from_member, to_member)
        if not path:
            return None
        
        return self._path_to_relation(path)
    
    def _find_path(self, from_member: FamilyMember, to_member: FamilyMember) -> Optional[List]:
        from collections import deque
        
        queue = deque([(from_member, [])])
        visited = {from_member.id}
        
        while queue:
            current, path = queue.popleft()
            
            if current.id == to_member.id:
                return path
            
            parents = self.db.query(FamilyRelation).filter(
                FamilyRelation.child_id == current.id
            ).all()
            
            for parent in parents:
                if parent.parent_id not in visited:
                    visited.add(parent.parent_id)
                    queue.append((parent.parent, path + [parent]))
            
            children = self.db.query(FamilyRelation).filter(
                FamilyRelation.parent_id == current.id
            ).all()
            
            for child in children:
                if child.child_id not in visited:
                    visited.add(child.child_id)
                    queue.append((child.child, path + [child]))
        
        return None
    
    def _path_to_relation(self, path: List[FamilyRelation]) -> Dict:
        if not path:
            return {'name': '我', 'level': 0, 'path': '', 'is_blood': True}
        
        level = 0
        is_blood = all(r.relation_nature == 'qin' for r in path)
        
        if len(path) == 1:
            relation = path[0]
            if relation.parent_type == 'father':
                return {'name': '父亲', 'level': 1, 'path': 'father', 'is_blood': is_blood}
            else:
                return {'name': '母亲', 'level': 1, 'path': 'mother', 'is_blood': is_blood}
        
        return {
            'name': self._generate_relation_name(path),
            'level': level,
            'path': '->'.join([r.parent_type for r in path]),
            'is_blood': is_blood
        }
    
    def _generate_relation_name(self, path: List[FamilyRelation]) -> str:
        return '未知关系'
```

---

## 验收标准

### 功能验收
- [ ] 人物详情页显示完整信息
- [ ] 事件时间轴按人物筛选显示
- [ ] 日期提醒按人物筛选显示
- [ ] 父母/子女关系显示正确
- [ ] 家谱可视化展示所有人物
- [ ] 亲生关系用实线，非亲生用虚线
- [ ] 已故人物显示灰色标记
- [ ] 关系计算功能正常
- [ ] 缩放、平移功能正常

### UI/UX 验收
- [ ] 人物详情页布局合理
- [ ] 时间轴视觉效果流畅
- [ ] 家谱连线清晰
- [ ] 悬停效果友好
- [ ] 响应式布局适配

### 性能要求
- [ ] 人物详情加载时间 < 500ms
- [ ] 家谱渲染时间 < 1s
- [ ] 关系计算时间 < 2s

---

## 注意事项

1. **家谱布局**：使用层次化布局算法，避免节点重叠
2. **关系计算**：使用 BFS 算法查找最短路径
3. **性能优化**：大量人物时使用虚拟滚动
4. **缓存策略**：计算结果缓存，减少重复计算
5. **错误处理**：循环关系检测，避免无限循环

---

## 下一步

完成阶段三后，可以进入阶段四开发设置页和扩展功能。