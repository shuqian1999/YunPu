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
      <div class="tree-toolbar">
        <el-button-group>
          <el-button @click="zoomIn" size="small">
            <el-icon><ZoomIn /></el-icon>
          </el-button>
          <el-button @click="zoomOut" size="small">
            <el-icon><ZoomOut /></el-icon>
          </el-button>
          <el-button @click="resetZoom" size="small">
            <el-icon><Refresh /></el-icon>
          </el-button>
        </el-button-group>
        <span class="zoom-info">缩放: {{ Math.round(scale * 100) }}%</span>
      </div>

      <div 
        class="tree-canvas"
        @wheel="handleWheel"
        @mousedown="handleMouseDown"
        @mousemove="handleMouseMove"
        @mouseup="handleMouseUp"
        @mouseleave="handleMouseUp"
      >
        <svg 
          :viewBox="viewBox"
          class="tree-svg"
          :style="{ transform: `scale(${scale})` }"
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
            <marker
              id="arrowhead-dashed"
              markerWidth="10"
              markerHeight="7"
              refX="9"
              refY="3.5"
              orient="auto"
            >
              <polygon points="0 0, 10 3.5, 0 7" fill="#999" />
            </marker>
            <pattern id="dashed" patternUnits="userSpaceOnUse" width="8" height="1">
              <line x1="0" y1="0" x2="4" y2="0" stroke="#999" stroke-width="2" />
            </pattern>
          </defs>

          <g v-for="edge in edges" :key="edge.id">
            <line
              :x1="getNodePosition(edge.source).x"
              :y1="getNodePosition(edge.source).y"
              :x2="getNodePosition(edge.target).x"
              :y2="getNodePosition(edge.target).y - 60"
              :stroke="edge.relation_nature === 'qin' ? '#409EFF' : '#999'"
              :stroke-dasharray="edge.relation_nature === 'qin' ? 'none' : '8,4'"
              stroke-width="2"
              :marker-end="`url(#arrowhead${edge.relation_nature === 'qin' ? '' : '-dashed'})`"
            />
          </g>

          <g 
            v-for="node in nodes" 
            :key="node.id"
            class="tree-node"
            :class="{ 'is-me': node.is_me, 'is-deceased': node.death_date }"
            @click="selectNode(node)"
          >
            <rect
              :x="getNodePosition(node.id).x - 80"
              :y="getNodePosition(node.id).y - 50"
              width="160"
              height="100"
              rx="8"
              :fill="node.is_me ? '#E6F7FF' : '#fff'"
              :stroke="node.is_me ? '#409EFF' : '#d9d9d9'"
              stroke-width="2"
            />
            
            <circle
              :cx="getNodePosition(node.id).x"
              :cy="getNodePosition(node.id).y - 20"
              r="25"
              :fill="node.gender === 'female' ? '#FFE4E1' : '#E6F7FF'"
              :stroke="node.gender === 'female' ? '#FF6B6B' : '#409EFF'"
              stroke-width="2"
            />
            
            <text
              :x="getNodePosition(node.id).x"
              :y="getNodePosition(node.id).y - 20"
              text-anchor="middle"
              dominant-baseline="middle"
              font-size="16"
              :fill="node.gender === 'female' ? '#FF6B6B' : '#409EFF'"
            >
              {{ getInitials(node.name) }}
            </text>
            
            <text
              :x="getNodePosition(node.id).x"
              :y="getNodePosition(node.id).y + 15"
              text-anchor="middle"
              font-size="14"
              font-weight="500"
              fill="#333"
            >
              {{ node.name }}
            </text>
            
            <text
              :x="getNodePosition(node.id).x"
              :y="getNodePosition(node.id).y + 35"
              text-anchor="middle"
              font-size="11"
              fill="#999"
            >
              {{ formatDateRange(node.birth_date, node.death_date) }}
            </text>
            
            <g v-if="node.death_date">
              <circle
                :cx="getNodePosition(node.id).x + 55"
                :cy="getNodePosition(node.id).y - 40"
                r="10"
                fill="#666"
              />
              <text
                :x="getNodePosition(node.id).x + 55"
                :y="getNodePosition(node.id).y - 37"
                text-anchor="middle"
                font-size="8"
                fill="#fff"
              >
                逝
              </text>
            </g>
          </g>
        </svg>
      </div>

      <div v-if="selectedNode" class="node-detail-panel">
        <div class="panel-header">
          <h3>{{ selectedNode.name }}</h3>
          <el-button @click="selectedNode = null" size="small">
            <el-icon><Close /></el-icon>
          </el-button>
        </div>
        <div class="panel-content">
          <div class="detail-row">
            <span class="label">性别</span>
            <span class="value">{{ selectedNode.gender === 'female' ? '女' : '男' }}</span>
          </div>
          <div class="detail-row">
            <span class="label">出生</span>
            <span class="value">{{ formatDate(selectedNode.birth_date) }}</span>
          </div>
          <div class="detail-row">
            <span class="label">逝世</span>
            <span class="value">{{ selectedNode.death_date ? formatDate(selectedNode.death_date) : '-' }}</span>
          </div>
          <div class="detail-actions">
            <el-button @click="editPerson(selectedNode.person_id)" type="primary" size="small">
              编辑详情
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <el-dialog title="添加家庭关系" :visible="showAddRelation" @close="showAddRelation = false">
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
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { Refresh, Plus, ZoomIn, ZoomOut, Close } from '@element-plus/icons-vue'
import { getFamilyTree, addFamilyRelation } from '@/api/family'
import { getPersons } from '@/api/persons'

const router = useRouter()

const nodes = ref([])
const edges = ref([])
const scale = ref(1)
const translateX = ref(0)
const translateY = ref(0)
const isDragging = ref(false)
const dragStart = ref({ x: 0, y: 0 })
const selectedNode = ref(null)
const showAddRelation = ref(false)
const availablePersons = ref([])

const relationForm = ref({
  parent_person_id: null,
  parent_type: 'father',
  child_person_id: null,
  relation_nature: 'qin'
})

const viewBox = computed(() => {
  const padding = 200
  const maxX = Math.max(...nodes.value.map(n => getNodePosition(n.id).x), 0) + padding
  const maxY = Math.max(...nodes.value.map(n => getNodePosition(n.id).y), 0) + padding
  return `0 0 ${maxX} ${maxY}`
})

const nodePositions = ref({})

const calculatePositions = () => {
  if (nodes.value.length === 0) return
  
  const levelMap = {}
  const meNode = nodes.value.find(n => n.is_me)
  
  if (meNode) {
    levelMap[meNode.id] = { level: 0, pos: 0 }
  }
  
  const visited = new Set()
  const queue = meNode ? [meNode] : nodes.value.slice(0, 1)
  
  while (queue.length > 0) {
    const current = queue.shift()
    if (visited.has(current.id)) continue
    visited.add(current.id)
    
    const currentLevel = levelMap[current.id]?.level || 0
    
    const children = edges.value
      .filter(e => e.source === current.id)
      .map(e => nodes.value.find(n => n.id === e.target))
      .filter(Boolean)
    
    const parents = edges.value
      .filter(e => e.target === current.id)
      .map(e => nodes.value.find(n => n.id === e.source))
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
  
  const nodePositionsTemp = {}
  let minLevel = Infinity
  let minPos = Infinity
  
  Object.keys(levelMap).forEach(id => {
    minLevel = Math.min(minLevel, levelMap[id].level)
    minPos = Math.min(minPos, levelMap[id].pos)
  })
  
  Object.keys(levelMap).forEach(id => {
    const x = (levelMap[id].level - minLevel + 2) * 200 + 100
    const y = (levelMap[id].pos - minPos + 3) * 150 + 150
    nodePositionsTemp[id] = { x, y }
  })
  
  nodes.value.forEach(node => {
    if (!nodePositionsTemp[node.id]) {
      nodePositionsTemp[node.id] = { 
        x: 100 + Object.keys(nodePositionsTemp).length * 180, 
        y: 200 
      }
    }
  })
  
  nodePositions.value = nodePositionsTemp
}

const getNodePosition = (nodeId) => {
  return nodePositions.value[nodeId] || { x: 100, y: 100 }
}

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

const refreshTree = async () => {
  await loadTree()
}

const goBack = () => {
  router.back()
}

const loadTree = async () => {
  try {
    const [treeRes, personsRes] = await Promise.all([
      getFamilyTree(),
      getPersons()
    ])
    
    nodes.value = treeRes.data.nodes
    edges.value = treeRes.data.edges
    
    availablePersons.value = personsRes.data.map(p => ({
      id: p.id,
      name: p.nickname || (p.last_name + p.first_name)
    }))
    
    calculatePositions()
  } catch (error) {
    console.error('加载家族树失败:', error)
  }
}

const zoomIn = () => {
  scale.value = Math.min(scale.value + 0.2, 3)
}

const zoomOut = () => {
  scale.value = Math.max(scale.value - 0.2, 0.3)
}

const resetZoom = () => {
  scale.value = 1
}

const handleWheel = (e) => {
  e.preventDefault()
  if (e.deltaY < 0) {
    zoomIn()
  } else {
    zoomOut()
  }
}

const handleMouseDown = (e) => {
  isDragging.value = true
  dragStart.value = { x: e.clientX - translateX.value, y: e.clientY - translateY.value }
}

const handleMouseMove = (e) => {
  if (isDragging.value) {
    translateX.value = e.clientX - dragStart.value.x
    translateY.value = e.clientY - dragStart.value.y
  }
}

const handleMouseUp = () => {
  isDragging.value = false
}

const selectNode = (node) => {
  selectedNode.value = node
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
  display: flex;
  gap: 20px;
}

.tree-toolbar {
  position: absolute;
  top: 20px;
  left: 20px;
  z-index: 10;
  display: flex;
  align-items: center;
  gap: 12px;
  background: white;
  padding: 8px 12px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.zoom-info {
  font-size: 12px;
  color: #666;
}

.tree-canvas {
  flex: 1;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  overflow: hidden;
  position: relative;
  height: calc(100vh - 180px);
}

.tree-svg {
  width: 100%;
  height: 100%;
}

.tree-node {
  cursor: pointer;
  transition: opacity 0.3s;
}

.tree-node:hover {
  opacity: 0.8;
}

.tree-node.is-me rect {
  stroke: #409EFF;
  stroke-width: 3;
}

.tree-node.is-deceased rect {
  fill: #f5f5f5;
}

.node-detail-panel {
  width: 300px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  display: flex;
  flex-direction: column;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
}

.panel-header h3 {
  margin: 0;
  font-size: 16px;
}

.panel-content {
  padding: 16px 20px;
  flex: 1;
}

.detail-row {
  display: flex;
  margin-bottom: 12px;
}

.detail-row:last-child {
  margin-bottom: 0;
}

.detail-row .label {
  width: 60px;
  color: #999;
  font-size: 13px;
}

.detail-row .value {
  flex: 1;
  font-size: 13px;
}

.detail-actions {
  margin-top: 20px;
}

.empty-tree {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #999;
}
</style>