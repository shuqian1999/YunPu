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

    <!-- 添加关系对话框 -->
    <el-dialog title="添加关系" v-model="showAddRelation">
      <el-form :model="relationForm" label-width="80px">
        <el-form-item label="关系类型">
          <el-radio-group v-model="relationForm.relationType">
            <el-radio label="family">家庭关系</el-radio>
            <el-radio label="spouse">配偶关系</el-radio>
          </el-radio-group>
        </el-form-item>

        <template v-if="relationForm.relationType === 'family'">
          <el-form-item label="人物A">
            <el-select v-model="relationForm.person_a_id" placeholder="选择人物">
              <el-option 
                v-for="p in availablePersons" 
                :key="p.id" 
                :label="p.name" 
                :value="p.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="关系">
            <el-select v-model="relationForm.relation">
              <el-option label="父亲" :value="0" />
              <el-option label="母亲" :value="1" />
              <el-option label="儿子" :value="2" />
              <el-option label="女儿" :value="3" />
            </el-select>
          </el-form-item>
          <el-form-item label="人物B">
            <el-select v-model="relationForm.person_b_id" placeholder="选择人物">
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
              <el-option label="亲（血亲）" :value="0" />
              <el-option label="继（继亲）" :value="1" />
              <el-option label="养（收养）" :value="2" />
              <el-option label="义（结义）" :value="3" />
              <el-option label="干（干亲）" :value="4" />
            </el-select>
          </el-form-item>
        </template>

        <template v-else>
          <el-form-item label="人物A">
            <el-select v-model="relationForm.person_a_id" placeholder="选择人物">
              <el-option 
                v-for="p in availablePersons" 
                :key="p.id" 
                :label="p.name" 
                :value="p.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="关系">
            <el-select v-model="relationForm.relation">
              <el-option label="丈夫" :value="0" />
              <el-option label="妻子" :value="1" />
              <el-option label="姨太太" :value="2" />
              <el-option label="男朋友" :value="3" />
              <el-option label="女朋友" :value="4" />
            </el-select>
          </el-form-item>
          <el-form-item label="人物B">
            <el-select v-model="relationForm.person_b_id" placeholder="选择人物">
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
              <el-option label="现任" :value="0" />
              <el-option label="前任" :value="1" />
            </el-select>
          </el-form-item>
        </template>
      </el-form>
      <template #footer>
        <el-button @click="showAddRelation = false">取消</el-button>
        <el-button @click="submitRelation" type="primary">确认添加</el-button>
      </template>
    </el-dialog>

    <div v-if="selectedPerson" class="person-detail-panel">
      <div class="panel-header">
        <h3>{{ selectedPerson.name || selectedPerson.last_name }}</h3>
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
        <div v-if="selectedPerson.relation_to_me" class="detail-row">
          <span class="label">与我的关系</span>
          <span class="value">{{ selectedPerson.relation_to_me.relation_name }}</span>
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
import { Refresh, Plus, Close } from '@element-plus/icons-vue'
import { getFamilyTree, createFamilyRelation, createSpouseRelation, getRelationsToMe, getRelationBetween } from '@/api/family'
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
  relationType: 'family',
  person_a_id: null,
  person_b_id: null,
  relation: 0,
  relation_nature: 0
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

const goBack = () => {
  router.back()
}

const buildHierarchy = (nodes, edges) => {
  if (!nodes || nodes.length === 0) return null

  const personMap = {}
  nodes.forEach(node => {
    if (!node || !node.id) return
    personMap[String(node.id)] = {
      id: node.id,
      first_name: '',
      last_name: node.name || '未知',
      birth_date: node.birth_date || null,
      death_date: node.death_date || null,
      gender: GENDER_MAP[node.gender] || 'male',
      is_me: node.is_me || false,
      name: node.name || '未知'
    }
  })

  const childrenByParent = {}

  if (edges && Array.isArray(edges)) {
    edges.forEach(edge => {
      if (!edge || !edge.source || !edge.target) return
      
      // 跳过配偶关系边
      if (edge.is_spouse) return
      
      const sourceId = String(edge.source)
      const targetId = String(edge.target)
      
      // 关系类型：0=父, 1=母, 2=子, 3=女
      // 父子关系：source是父辈，target是子辈
      // 0=父, 1=母 表示 source 是 target 的父亲/母亲
      if (!childrenByParent[sourceId]) childrenByParent[sourceId] = []
      if (!childrenByParent[sourceId].includes(targetId)) {
        childrenByParent[sourceId].push(targetId)
      }
    })
  }

  const childSet = {}
  Object.keys(childrenByParent).forEach(parentId => {
    childrenByParent[parentId].forEach(childId => {
      childSet[childId] = true
    })
  })

  // 找到根节点（没有父节点的人）
  let rootIds = Object.keys(personMap).filter(id => !childSet[id])
  if (rootIds.length === 0) rootIds = [Object.keys(personMap)[0]]

  const processed = {}
  const convertNode = (id) => {
    if (processed[id]) return null
    processed[id] = true
    const person = personMap[id]
    if (!person) return null
    const children = (childrenByParent[id] || [])
      .map(convertNode)
      .filter(Boolean)
    return { data: person, children: children.length > 0 ? children : undefined }
  }

  return convertNode(rootIds[0])
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

  // 绘制卡片背景
  nodes.append('rect')
    .attr('width', CARD_WIDTH)
    .attr('height', CARD_HEIGHT)
    .attr('rx', 8)
    .attr('ry', 8)
    .attr('fill', d => isFemale(d) ? '#FFF0F5' : '#F0F8FF')
    .attr('stroke', d => isFemale(d) ? '#FFB6C1' : '#87CEEB')
    .attr('stroke-width', 2)

  // 绘制头像圆圈
  nodes.append('circle')
    .attr('cx', CARD_WIDTH / 2)
    .attr('cy', 28)
    .attr('r', 18)
    .attr('fill', d => isFemale(d) ? '#FFE4E1' : '#E6F7FF')
    .attr('stroke', d => isFemale(d) ? '#FF6B6B' : '#409EFF')
    .attr('stroke-width', 2)

  // 绘制姓氏首字
  nodes.append('text')
    .attr('x', CARD_WIDTH / 2)
    .attr('y', 33)
    .attr('text-anchor', 'middle')
    .attr('font-size', 14)
    .attr('font-weight', 'bold')
    .attr('fill', d => isFemale(d) ? '#FF6B6B' : '#409EFF')
    .text(d => (d.data.last_name || '?').charAt(0))

  // 绘制姓名
  nodes.append('text')
    .attr('x', CARD_WIDTH / 2)
    .attr('y', 55)
    .attr('text-anchor', 'middle')
    .attr('font-size', 12)
    .attr('font-weight', '600')
    .attr('fill', '#333')
    .text(d => d.data.last_name || '')

  // 标记已故人士
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

  // 标记"我"
  nodes.filter(d => d.data.is_me)
    .append('g')
    .attr('transform', `translate(12, 12)`)
    .each(function () {
      d3.select(this).append('circle').attr('r', 10).attr('fill', '#67C23A')
      d3.select(this).append('text')
        .attr('y', 4)
        .attr('text-anchor', 'middle')
        .attr('font-size', 9)
        .attr('fill', 'white')
        .text('我')
    })

  // 点击事件
  nodes.on('click', async (event, d) => {
    event.stopPropagation()
    // 获取与"我"的关系
    let relationToMe = null
    if (d.data && d.data.id) {
      relationToMe = await getRelationBetween(d.data.id, 1).catch(() => null)
    }
    selectedPerson.value = {
      ...d.data,
      relation_to_me: relationToMe
    }
  })

  svg.on('click', () => {
    selectedPerson.value = null
  })
}

const loadTree = async () => {
  try {
    const [treeRes, personsRes] = await Promise.all([
      getFamilyTree(),
      getPersons()
    ])

    availablePersons.value = personsRes.map(p => ({
      id: p.id,
      name: p.nickname || (p.last_name + (p.first_name || ''))
    }))

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
  if (!relationForm.value.person_a_id || !relationForm.value.person_b_id) {
    ElMessage.warning('请选择两个人物')
    return
  }
  
  if (relationForm.value.person_a_id === relationForm.value.person_b_id) {
    ElMessage.warning('不能与自己建立关系')
    return
  }

  try {
    if (relationForm.value.relationType === 'family') {
      await createFamilyRelation(
        relationForm.value.person_a_id,
        relationForm.value.person_b_id,
        relationForm.value.relation,
        relationForm.value.relation_nature
      )
    } else {
      await createSpouseRelation(
        relationForm.value.person_a_id,
        relationForm.value.person_b_id,
        relationForm.value.relation,
        relationForm.value.relation_nature
      )
    }
    showAddRelation.value = false
    ElMessage.success('关系添加成功')
    await loadTree()
    
    // 重置表单
    relationForm.value = {
      relationType: 'family',
      person_a_id: null,
      person_b_id: null,
      relation: 0,
      relation_nature: 0
    }
  } catch (error) {
    console.error('添加关系失败:', error)
    ElMessage.error('添加关系失败')
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
