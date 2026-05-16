<template>
  <div class="family-tree-page">
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
            
            <div v-if="hoveredNode === props.id" class="relation-tooltip">
              {{ getRelationToMe(props.data.personId) }}
            </div>
            
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

    <el-dialog 
      :title="quickRelationDialog.title" 
      v-model="quickRelationDialog.show"
    >
      <el-form :model="quickRelationForm" label-width="80px">
        <el-form-item :label="quickRelationDialog.label">
          <el-select v-model="quickRelationForm.target_person_id" placeholder="选择人物">
            <el-option 
              v-for="p in availablePersons" 
              :key="p.id" 
              :label="p.name" 
              :value="p.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="关系类型">
          <el-select v-model="quickRelationForm.parent_type">
            <el-option 
              v-for="option in quickRelationDialog.options" 
              :key="option.value" 
              :label="option.label" 
              :value="option.value"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="quickRelationDialog.show = false">取消</el-button>
        <el-button @click="submitQuickRelation" type="primary">确认添加</el-button>
      </template>
    </el-dialog>

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
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { VueFlow } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import { Refresh, Plus, Close } from '@element-plus/icons-vue'
import { getFamilyTree, addFamilyRelation } from '@/api/family'
import { getPersons } from '@/api/persons'

const router = useRouter()

const localNodes = ref([])
const localEdges = ref([])
const hoveredNode = ref(null)
const selectedNode = ref(null)
const showAddRelation = ref(false)
const availablePersons = ref([])
const relationsToMe = ref([])

const relationForm = ref({
  parent_person_id: null,
  parent_type: 'father',
  child_person_id: null,
  relation_nature: 'qin'
})

const quickRelationDialog = ref({
  show: false,
  title: '',
  label: '',
  options: [],
  sourceNodeId: null,
  relationType: '',
  sourcePersonId: null
})

const quickRelationForm = ref({
  target_person_id: null,
  parent_type: ''
})

const getInitials = (name) => {
  if (!name) return '?'
  return name.charAt(0)
}

const formatDate = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN')
}

const formatDateRange = (birth, death) => {
  const birthYear = birth ? new Date(birth).getFullYear() : '?'
  const deathYear = death ? new Date(death).getFullYear() : ''
  return death ? `${birthYear}-${deathYear}` : `${birthYear}-`
}

const getRelationToMe = (personId) => {
  const relation = relationsToMe.value.find(r => r.person_id === personId)
  if (relation) {
    return relation.relation_name
  }
  return '未知关系'
}

const refreshTree = async () => {
  await loadTree()
}

const goBack = () => {
  router.back()
}

const calculateLayout = (nodeList, edgeList) => {
  if (nodeList.length === 0) return nodeList

  const levelMap = {}
  const meNode = nodeList.find(n => n.data.isMe)
  
  if (meNode) {
    levelMap[meNode.id] = { level: 0, pos: 0 }
  }
  
  const visited = new Set()
  const queue = meNode ? [meNode] : nodeList.slice(0, 1)
  
  while (queue.length > 0) {
    const current = queue.shift()
    if (visited.has(current.id)) continue
    visited.add(current.id)
    
    const currentLevel = levelMap[current.id]?.level || 0
    
    const children = edgeList
      .filter(e => e.source === current.id)
      .map(e => nodeList.find(n => n.id === e.target))
      .filter(Boolean)
    
    const parents = edgeList
      .filter(e => e.target === current.id)
      .map(e => nodeList.find(n => n.id === e.source))
      .filter(Boolean)
    
    children.forEach((child, index) => {
      if (!levelMap[child.id]) {
        levelMap[child.id] = { 
          level: currentLevel + 1, 
          pos: index - (children.length - 1) / 2 
        }
      }
      queue.push(child)
    })
    
    parents.forEach((parent, index) => {
      if (!levelMap[parent.id]) {
        levelMap[parent.id] = { 
          level: currentLevel - 1, 
          pos: index - (parents.length - 1) / 2 
        }
      }
      queue.push(parent)
    })
  }
  
  const levels = {}
  Object.keys(levelMap).forEach(id => {
    const level = levelMap[id].level
    if (!levels[level]) levels[level] = []
    levels[level].push({ id, pos: levelMap[id].pos })
  })
  
  const levelNumbers = Object.keys(levels).map(Number).sort((a, b) => a - b)
  const NODE_WIDTH = 180
  const NODE_HEIGHT = 120
  const VERTICAL_SPACING = 100
  const HORIZONTAL_SPACING = 60
  
  return nodeList.map(node => {
    const level = levelMap[node.id]?.level || 0
    const levelNodes = levels[level] || []
    const index = levelNodes.findIndex(n => n.id === node.id)
    const totalWidth = levelNodes.length * NODE_WIDTH + (levelNodes.length - 1) * HORIZONTAL_SPACING
    const startX = Math.max(200, window.innerWidth / 2 - totalWidth / 2)
    
    return {
      ...node,
      position: {
        x: startX + index * (NODE_WIDTH + HORIZONTAL_SPACING),
        y: 150 + level * (NODE_HEIGHT + VERTICAL_SPACING)
      }
    }
  })
}

const loadTree = async () => {
  try {
    const [treeRes, personsRes] = await Promise.all([
      getFamilyTree(),
      getPersons()
    ])
    
    const newEdges = treeRes.edges.map(edge => ({
      id: String(edge.id),
      source: String(edge.source),
      target: String(edge.target),
      animated: true,
      style: {
        stroke: edge.relation_nature === 'qin' ? '#409EFF' : '#999',
        strokeDasharray: edge.relation_nature === 'qin' ? 'none' : '8,4'
      }
    }))
    
    const initialNodes = treeRes.nodes.map(node => ({
      id: String(node.id),
      type: 'person',
      data: {
        name: node.name,
        gender: node.gender,
        birthDate: node.birth_date,
        deathDate: node.death_date,
        personId: node.person_id,
        isMe: node.is_me
      },
      position: { x: 0, y: 0 }
    }))
    
    const positionedNodes = calculateLayout(initialNodes, newEdges)
    
    availablePersons.value = personsRes.map(p => ({
      id: p.id,
      name: p.nickname || (p.last_name + p.first_name)
    }))
    
    localEdges.value = newEdges
    localNodes.value = positionedNodes
  } catch (error) {
    console.error('加载家族树失败:', error)
  }
}

const onNodeClick = (event) => {
  selectedNode.value = event.node
}

const onNodeMouseEnter = (event) => {
  hoveredNode.value = event.node.id
}

const onNodeMouseLeave = () => {
  hoveredNode.value = null
}

const editPerson = (personId) => {
  router.push(`/persons/${personId}`)
}

const addRelation = () => {
  showAddRelation.value = true
}

const submitRelation = async () => {
  if (!relationForm.value.parent_person_id || !relationForm.value.child_person_id) {
    return
  }
  
  try {
    await addFamilyRelation(
      relationForm.value.parent_person_id,
      relationForm.value.child_person_id,
      relationForm.value.parent_type,
      relationForm.value.relation_nature
    )
    
    showAddRelation.value = false
    await loadTree()
    
    relationForm.value = {
      parent_person_id: null,
      parent_type: 'father',
      child_person_id: null,
      relation_nature: 'qin'
    }
  } catch (error) {
    console.error('添加关系失败:', error)
  }
}

const quickAddRelation = (nodeId, relationType) => {
  const node = localNodes.value.find(n => n.id === nodeId)
  if (!node) return
  
  quickRelationDialog.value = {
    show: true,
    title: relationType === 'parent' ? '添加父母' : '添加子女',
    label: relationType === 'parent' ? '选择父母' : '选择子女',
    options: relationType === 'parent' 
      ? [{ label: '父亲', value: 'father' }, { label: '母亲', value: 'mother' }]
      : [{ label: '儿子', value: 'father' }, { label: '女儿', value: 'mother' }],
    sourceNodeId: nodeId,
    relationType: relationType,
    sourcePersonId: node.data.personId
  }
  
  quickRelationForm.value = {
    target_person_id: null,
    parent_type: relationType === 'parent' ? 'father' : 'father'
  }
}

const submitQuickRelation = async () => {
  if (!quickRelationForm.value.target_person_id) return
  
  const dialog = quickRelationDialog.value
  
  try {
    if (dialog.relationType === 'parent') {
      await addFamilyRelation(
        quickRelationForm.value.target_person_id,
        dialog.sourcePersonId,
        quickRelationForm.value.parent_type,
        'qin'
      )
    } else {
      await addFamilyRelation(
        dialog.sourcePersonId,
        quickRelationForm.value.target_person_id,
        quickRelationForm.value.parent_type,
        'qin'
      )
    }
    
    quickRelationDialog.value.show = false
    await loadTree()
  } catch (error) {
    console.error('添加关系失败:', error)
  }
}

onMounted(() => {
  loadTree()
})
</script>

<style scoped>
.family-tree-page {
  min-height: 100vh;
  background: #f5f7fa;
}

.page-title {
  font-size: 24px;
  font-weight: bold;
}

.tree-container {
  padding: 20px;
  height: calc(100vh - 120px);
}

.vue-flow-container {
  width: 100%;
  height: 100%;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

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
}

.family-node:hover {
  border-color: #409EFF;
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(64, 158, 255, 0.2);
}

.family-node.is-me {
  border-color: #409EFF;
  background: #E6F7FF;
}

.family-node.is-deceased {
  opacity: 0.7;
}

.family-node.is-hovered {
  border-color: #409EFF;
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
}

.node-avatar span {
  font-size: 20px;
  font-weight: bold;
  color: #409EFF;
}

.node-avatar span.female {
  color: #FF6B6B;
}

.node-avatar.female {
  background: #FFE4E1;
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

.node-name {
  font-size: 14px;
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
}

.node-date {
  font-size: 11px;
  color: #999;
}

.relation-tooltip {
  position: absolute;
  top: -36px;
  left: 50%;
  transform: translateX(-50%);
  background: #333;
  color: white;
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 12px;
  white-space: nowrap;
  z-index: 100;
}

.relation-tooltip::after {
  content: '';
  position: absolute;
  bottom: -6px;
  left: 50%;
  transform: translateX(-50%);
  border-left: 6px solid transparent;
  border-right: 6px solid transparent;
  border-top: 6px solid #333;
}

.quick-actions {
  position: absolute;
  top: -40px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 8px;
}

.action-btn {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
  color: white;
  font-size: 14px;
}

.action-btn:hover {
  transform: scale(1.1);
}

.add-parent {
  background: #409EFF;
}

.add-child {
  background: #67C23A;
}

.node-detail-panel {
  position: fixed;
  right: 20px;
  top: 100px;
  width: 280px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  z-index: 1000;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid #eee;
}

.panel-header h3 {
  margin: 0;
  font-size: 16px;
}

.panel-content {
  padding: 16px;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid #f5f5f5;
}

.detail-row:last-of-type {
  border-bottom: none;
}

.detail-row .label {
  color: #999;
  font-size: 13px;
}

.detail-row .value {
  color: #333;
  font-size: 13px;
  font-weight: 500;
}

.detail-actions {
  margin-top: 16px;
  display: flex;
  gap: 8px;
}

.detail-actions .el-button {
  flex: 1;
}
</style>

<style>
.vue-flow__edge-path {
  stroke-width: 2;
}
</style>