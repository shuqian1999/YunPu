<template>
  <div class="family-tree-page">
    <el-page-header @back="goBack">
      <template #content>
        <span class="page-title">家族树</span>
      </template>
    </el-page-header>

    <div class="view-tabs">
      <el-radio-group v-model="viewMode" size="default">
        <el-radio-button value="tree">树状图</el-radio-button>
        <el-radio-button value="graph">关系图谱</el-radio-button>
      </el-radio-group>

      <div class="view-actions">
        <template v-if="viewMode === 'tree'">
          <el-button @click="refreshTree" type="primary" size="small">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
          <el-button @click="handleRecalculateRelations" type="warning" size="small">
            <el-icon><Edit /></el-icon>
            重新计算关系
          </el-button>
          <el-button @click="addAllPersons" type="info" size="small">
            <el-icon><Document /></el-icon>
            导入所有人物
          </el-button>
          <el-button @click="addRelation" type="success" size="small">
            <el-icon><Plus /></el-icon>
            添加关系
          </el-button>
        </template>
      </div>
    </div>

    <!-- 树状图视图 -->
    <div v-show="viewMode === 'tree'" ref="treeContainer" class="tree-container"></div>

    <!-- 关系图谱视图 -->
    <RelationGraph v-show="viewMode === 'graph'" />

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

    <div v-if="selectedPerson" class="person-detail-panel">
      <div class="panel-header">
        <h3>{{ selectedPerson.last_name }}</h3>
        <el-button @click="selectedPerson = null" size="small">
          <el-icon><Close /></el-icon>
        </el-button>
      </div>
      <div class="panel-content">
        <div class="detail-row">
          <span class="label">性别</span>
          <span class="value">{{ getGenderLabel(selectedPerson.gender) }}</span>
        </div>
        <div class="detail-row">
          <span class="label">出生</span>
          <span class="value">{{ formatDate(selectedPerson.birth_date) }}</span>
        </div>
        <div class="detail-row">
          <span class="label">逝世</span>
          <span class="value">{{ selectedPerson.death_date ? formatDate(selectedPerson.death_date) : '-' }}</span>
        </div>
        <div class="detail-actions">
          <el-button @click="editPerson(selectedPerson.id)" type="primary" size="small">
            编辑详情
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import * as d3 from 'd3'
import { Refresh, Plus, Close, Edit, Document } from '@element-plus/icons-vue'
import { getFamilyTree, addFamilyRelation, getRelationsToMe, recalculateRelations, addFamilyMember } from '@/api/family'
import { getPersons } from '@/api/persons'
import { ElMessage } from 'element-plus'
import RelationGraph from '@/components/RelationGraph.vue'

const router = useRouter()

const treeContainer = ref(null)
const viewMode = ref('tree')
const selectedPerson = ref(null)
const showAddRelation = ref(false)
const availablePersons = ref([])
const relationsToMe = ref([])
let svg = null
let gRoot = null

const relationForm = ref({
  parent_person_id: null,
  parent_type: 'father',
  child_person_id: null,
  relation_nature: 'qin'
})

const CARD_WIDTH = 180
const CARD_HEIGHT = 70
const H_GAP = 40
const V_GAP = 100

const GENDER_MAP = { 1: 'male', 2: 'female', male: 'male', female: 'female' }

const getGenderLabel = (gender) => {
  if (gender === 'male' || gender === 1) return '男'
  if (gender === 'female' || gender === 2) return '女'
  return '-'
}

const formatDate = (dateString) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleDateString('zh-CN')
}

const refreshTree = async () => {
  await loadTree()
}

const handleRecalculateRelations = async () => {
  try {
    await recalculateRelations()
    ElMessage.success('关系重新计算成功')
    await loadTree()
  } catch (error) {
    console.error('重新计算关系失败:', error)
    ElMessage.error('重新计算关系失败')
  }
}

const addAllPersons = async () => {
  try {
    const personsRes = await getPersons()
    const treeRes = await getFamilyTree()
    const existingMemberIds = new Set(treeRes.nodes.map(n => n.person_id))
    for (const person of personsRes) {
      if (!existingMemberIds.has(person.id)) {
        await addFamilyMember(person.id)
      }
    }
    await handleRecalculateRelations()
    ElMessage.success('导入人物并重新计算关系成功')
    await loadTree()
  } catch (error) {
    console.error('导入人物失败:', error)
    ElMessage.error('导入人物失败')
  }
}

const goBack = () => {
  router.back()
}

const buildHierarchy = (nodes, edges) => {
  if (!nodes || nodes.length === 0) return null

  const nodeIdToPersonId = {}
  const personMap = {}
  nodes.forEach(node => {
    if (!node || !node.person_id || !node.id) return
    const nodeId = String(node.id)
    const pid = String(node.person_id)
    nodeIdToPersonId[nodeId] = pid
    personMap[pid] = {
      id: node.person_id,
      first_name: '',
      last_name: node.name || '未知',
      birth_date: node.birth_date || null,
      death_date: node.death_date || null,
      gender: GENDER_MAP[node.gender] || 'male'
    }
  })

  console.log('nodeIdToPersonId:', nodeIdToPersonId)
  console.log('personMap:', personMap)

  const childrenByParent = {}

  if (edges && Array.isArray(edges)) {
    edges.forEach(edge => {
      if (!edge || !edge.source || !edge.target) return
      const sourceNodeId = String(edge.source)
      const targetNodeId = String(edge.target)
      const sourcePersonId = nodeIdToPersonId[sourceNodeId]
      const targetPersonId = nodeIdToPersonId[targetNodeId]
      if (!sourcePersonId || !targetPersonId) return

      if (edge.parent_type === 'spouse') return

      if (!childrenByParent[sourcePersonId]) childrenByParent[sourcePersonId] = []
      if (!childrenByParent[sourcePersonId].includes(targetPersonId)) {
        childrenByParent[sourcePersonId].push(targetPersonId)
      }
    })
  }

  console.log('childrenByParent:', childrenByParent)

  const childSet = {}
  Object.keys(childrenByParent).forEach(parentPid => {
    childrenByParent[parentPid].forEach(childPid => {
      childSet[childPid] = true
    })
  })

  const rootPids = Object.keys(personMap).filter(pid => !childSet[pid])
  console.log('rootPids:', rootPids)
  if (rootPids.length === 0) rootPids.push(Object.keys(personMap)[0])

  const processed = {}
  const convertNode = (pid) => {
    if (processed[pid]) return null
    processed[pid] = true
    const person = personMap[pid]
    if (!person) return null
    const children = (childrenByParent[pid] || [])
      .map(convertNode)
      .filter(Boolean)
    return { data: person, children: children.length > 0 ? children : undefined }
  }

  return convertNode(rootPids[0])
}

const initSvg = () => {
  if (!treeContainer.value) return
  const container = treeContainer.value
  const rect = container.getBoundingClientRect()
  const width = rect.width || 800
  const height = rect.height || 600

  if (svg) svg.remove()

  svg = d3.select(container)
    .append('svg')
    .attr('width', '100%')
    .attr('height', '100%')
    .attr('viewBox', `0 0 ${width} ${height}`)
    .style('cursor', 'grab')

  const zoom = d3.zoom()
    .scaleExtent([0.3, 3])
    .on('zoom', (event) => {
      gRoot.attr('transform', event.transform)
    })

  svg.call(zoom)
  gRoot = svg.append('g')
}

const renderTree = (rootNode) => {
  if (!svg || !gRoot || !rootNode) return

  gRoot.selectAll('*').remove()

  const root = d3.hierarchy(rootNode)
  const treeLayout = d3.tree().nodeSize([CARD_WIDTH + H_GAP, CARD_HEIGHT + V_GAP])
  treeLayout(root)

  const descendants = root.descendants()
  console.log('Tree descendants:', descendants)

  const container = treeContainer.value
  if (!container) return
  const width = container.clientWidth
  const height = container.clientHeight

  const minX = d3.min(descendants, d => d.x) || 0
  const maxX = d3.max(descendants, d => d.x) || width
  const treeWidth = maxX - minX + CARD_WIDTH + H_GAP
  const offsetX = Math.max((width - treeWidth) / 2 - minX + CARD_WIDTH / 2, 50)
  const offsetY = 50

  const links = root.links()
  gRoot.selectAll('.link')
    .data(links)
    .enter().append('path')
    .attr('fill', 'none')
    .attr('stroke', '#ccc')
    .attr('stroke-width', 2)
    .attr('d', d => {
      const x1 = d.source.x + offsetX
      const y1 = d.source.y + offsetY + CARD_HEIGHT / 2
      const x2 = d.target.x + offsetX
      const y2 = d.target.y + offsetY - CARD_HEIGHT / 2
      const midY = (y1 + y2) / 2
      return `M${x1},${y1} L${x1},${midY} L${x2},${midY} L${x2},${y2}`
    })

  const nodes = gRoot.selectAll('.node')
    .data(descendants)
    .enter().append('g')
    .attr('class', 'node')
    .attr('transform', d => `translate(${d.x + offsetX - CARD_WIDTH / 2},${d.y + offsetY - CARD_HEIGHT / 2})`)
    .style('cursor', 'pointer')

  const isFemale = d => d.data.gender === 'female'

  nodes.append('rect')
    .attr('width', CARD_WIDTH)
    .attr('height', CARD_HEIGHT)
    .attr('rx', 8)
    .attr('ry', 8)
    .attr('fill', d => isFemale(d) ? '#FFF0F5' : '#F0F8FF')
    .attr('stroke', d => isFemale(d) ? '#FFB6C1' : '#87CEEB')
    .attr('stroke-width', 2)

  nodes.append('circle')
    .attr('cx', CARD_WIDTH / 2)
    .attr('cy', 28)
    .attr('r', 18)
    .attr('fill', d => isFemale(d) ? '#FFE4E1' : '#E6F7FF')
    .attr('stroke', d => isFemale(d) ? '#FF6B6B' : '#409EFF')
    .attr('stroke-width', 2)

  nodes.append('text')
    .attr('x', CARD_WIDTH / 2)
    .attr('y', 33)
    .attr('text-anchor', 'middle')
    .attr('font-size', 14)
    .attr('font-weight', 'bold')
    .attr('fill', d => isFemale(d) ? '#FF6B6B' : '#409EFF')
    .text(d => (d.data.last_name || '?').charAt(0))

  nodes.append('text')
    .attr('x', CARD_WIDTH / 2)
    .attr('y', 55)
    .attr('text-anchor', 'middle')
    .attr('font-size', 12)
    .attr('font-weight', '600')
    .attr('fill', '#333')
    .text(d => d.data.last_name || '')

  nodes.filter(d => d.data.death_date)
    .append('g')
    .attr('transform', `translate(${CARD_WIDTH - 12}, 12)`)
    .each(function () {
      d3.select(this).append('circle').attr('r', 10).attr('fill', '#666')
      d3.select(this).append('text')
        .attr('y', 4)
        .attr('text-anchor', 'middle')
        .attr('font-size', 9)
        .attr('fill', 'white')
        .text('逝')
    })

  nodes.on('click', (event, d) => {
    event.stopPropagation()
    selectedPerson.value = d.data
  })

  svg.on('click', () => {
    selectedPerson.value = null
  })
}

const loadTree = async () => {
  try {
    const [treeRes, personsRes, relationsRes] = await Promise.all([
      getFamilyTree(),
      getPersons(),
      getRelationsToMe()
    ])

    console.log('Nodes:', treeRes.nodes)
    console.log('Edges:', treeRes.edges)

    availablePersons.value = personsRes.map(p => ({
      id: p.id,
      name: p.nickname || (p.last_name + p.first_name)
    }))
    relationsToMe.value = relationsRes

    const rootNode = buildHierarchy(treeRes.nodes, treeRes.edges)
    if (!rootNode) {
      console.warn('No valid data to render family tree')
      return
    }
    initSvg()
    renderTree(rootNode)
  } catch (error) {
    console.error('加载家族树失败:', error)
  }
}

const editPerson = (personId) => {
  router.push(`/persons/${personId}`)
}

const addRelation = () => {
  showAddRelation.value = true
}

const submitRelation = async () => {
  if (!relationForm.value.parent_person_id || !relationForm.value.child_person_id) return
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

onUnmounted(() => {
  if (svg) svg.remove()
})
</script>

<style scoped>
.family-tree-page {
  min-height: 100vh;
  background: var(--bg-color, #f5f7fa);
}
.page-title {
  font-size: 24px;
  font-weight: bold;
}
.view-tabs {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding: 12px 16px;
  background: var(--el-bg-color, white);
  border-radius: 8px;
}
.view-actions {
  display: flex;
  gap: 8px;
}
.tree-container {
  padding: 20px;
  height: calc(100vh - 120px);
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}
.tree-container svg {
  display: block;
  width: 100%;
  height: 100%;
}
.person-detail-panel {
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
.detail-row:last-child {
  border-bottom: none;
}
.detail-row .label {
  color: #999;
  font-size: 14px;
}
.detail-row .value {
  color: #333;
  font-size: 14px;
  font-weight: 500;
}
.detail-actions {
  margin-top: 16px;
  text-align: center;
}
</style>