<template>
  <div class="relation-graph-container">
    <div class="graph-header">
      <h3 class="graph-title">关系图谱</h3>
      <div class="graph-actions">
        <el-button text type="primary" @click="handleZoomIn">
          <el-icon><Plus /></el-icon>
        </el-button>
        <el-button text type="primary" @click="handleZoomOut">
          <el-icon><Minus /></el-icon>
        </el-button>
        <el-button text type="primary" @click="handleReset">
          <el-icon><Refresh /></el-icon>
        </el-button>
      </div>
    </div>

    <el-card class="graph-card">
      <div v-loading="loading" class="graph-canvas" ref="graphContainer">
        <svg
          ref="svgRef"
          :width="canvasWidth"
          :height="canvasHeight"
          :viewBox="`0 0 ${canvasWidth} ${canvasHeight}`"
          @mousedown="handleMouseDown"
          @mousemove="handleMouseMove"
          @mouseup="handleMouseUp"
          @wheel="handleWheel"
          class="graph-svg"
        >
          <g :transform="`translate(${panX}, ${panY}) scale(${zoom})`">
            <!-- 绘制连线 -->
            <g class="edges">
              <line
                v-for="edge in edges"
                :key="edge.id"
                :x1="getNodeX(edge.source)"
                :y1="getNodeY(edge.source)"
                :x2="getNodeX(edge.target)"
                :y2="getNodeY(edge.target)"
                :stroke="edge.is_blood ? '#409EFF' : '#909399'"
                :stroke-width="2"
                :stroke-dasharray="edge.is_blood ? 'none' : '5,5'"
                class="edge-line"
              />
              <!-- 关系标签 -->
              <text
                v-for="edge in edges"
                :key="`label-${edge.id}`"
                :x="(getNodeX(edge.source) + getNodeX(edge.target)) / 2"
                :y="(getNodeY(edge.source) + getNodeY(edge.target)) / 2 - 8"
                text-anchor="middle"
                font-size="12"
                fill="#606266"
              >
                {{ edge.relation_name }}
              </text>
            </g>

            <!-- 绘制节点 -->
            <g class="nodes">
              <g
                v-for="node in nodes"
                :key="node.id"
                :transform="`translate(${getNodeX(node.id)}, ${getNodeY(node.id)})`"
                class="node-group"
                @click="handleNodeClick(node)"
                @mouseenter="hoveredNode = node.id"
                @mouseleave="hoveredNode = null"
              >
                <!-- 头像背景 -->
                <circle
                  :r="nodeRadius"
                  :fill="node.is_me ? '#E1F3FF' : (node.is_blood ? '#FFE1E1' : '#F5F7FA')"
                  :stroke="node.is_me ? '#409EFF' : (hoveredNode === node.id ? '#409EFF' : '#E4E7ED')"
                  :stroke-width="node.is_me ? 3 : (hoveredNode === node.id ? 2 : 1)"
                />
                <!-- 头像首字母 -->
                <text
                  y="5"
                  text-anchor="middle"
                  font-size="20"
                  font-weight="500"
                  fill="#303133"
                >
                  {{ getInitial(node.name) }}
                </text>
                <!-- 节点名称 -->
                <text
                  :y="nodeRadius + 16"
                  text-anchor="middle"
                  font-size="12"
                  fill="var(--text-regular, #606266)"
                >
                  {{ truncateName(node.name) }}
                </text>
                <!-- 关系名称 -->
                <text
                  v-if="node.relation_name && !node.is_me"
                  :y="nodeRadius + 30"
                  text-anchor="middle"
                  font-size="10"
                  fill="var(--text-secondary, #909399)"
                >
                  {{ node.relation_name }}
                </text>
              </g>
            </g>
          </g>
        </svg>
      </div>

      <div v-if="!loading && nodes.length === 0" class="empty-graph">
        <el-empty description="暂无关系数据" />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Plus, Minus, Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { getRelationsToMe } from '@/api/family'

const router = useRouter()
const loading = ref(false)
const nodes = ref([])
const edges = ref([])
const hoveredNode = ref(null)

// 画布配置
const canvasWidth = 800
const canvasHeight = 600
const nodeRadius = 36
const levelHeight = 120
const nodeSpacing = 120

// 缩放和平移
const zoom = ref(1)
const panX = ref(0)
const panY = ref(0)
const isDragging = ref(false)
const lastMousePos = ref({ x: 0, y: 0 })

const graphContainer = ref(null)
const svgRef = ref(null)

const loadGraph = async () => {
  loading.value = true
  try {
    const relations = await getRelationsToMe()

    if (!relations || relations.length === 0) {
      nodes.value = []
      edges.value = []
      return
    }

    // 获取"我"的信息（作为中心节点）
    const meNode = {
      id: 1,
      name: '我',
      relation_name: '',
      relation_level: 0,
      is_blood: true,
      is_me: true
    }

    const nodeMap = new Map()
    nodeMap.set(1, meNode)

    const edgeList = []

    for (const relation of relations) {
      nodeMap.set(relation.person_id, {
        id: relation.person_id,
        name: relation.name || '未知',
        relation_name: relation.relation_name || '',
        relation_level: 1,
        is_blood: relation.relation_nature === 0,
        is_me: false
      })

      edgeList.push({
        id: `1-${relation.person_id}`,
        source: 1,
        target: relation.person_id,
        relation_name: relation.relation_name || '',
        is_blood: relation.relation_nature === 0
      })
    }

    nodes.value = Array.from(nodeMap.values())
    edges.value = edgeList

    // 自动居中
    centerGraph()
  } catch (error) {
    console.error('加载关系图谱失败:', error)
    ElMessage.error('加载关系图谱失败')
  } finally {
    loading.value = false
  }
}

const getNodeX = (nodeId) => {
  const node = nodes.value.find(n => n.id === nodeId)
  if (!node) return 0

  // 按层级分组
  const levelNodes = nodes.value.filter(n => n.relation_level === node.relation_level)
  const index = levelNodes.findIndex(n => n.id === nodeId)

  // 计算该层级的总宽度
  const levelWidth = Math.max(levelNodes.length * nodeSpacing, canvasWidth)
  const startX = (canvasWidth - levelWidth) / 2 + nodeSpacing / 2

  return startX + index * nodeSpacing
}

const getNodeY = (nodeId) => {
  const node = nodes.value.find(n => n.id === nodeId)
  if (!node) return 0

  return 60 + node.relation_level * levelHeight
}

const getInitial = (name) => {
  return name.charAt(0).toUpperCase()
}

const truncateName = (name) => {
  if (name.length > 6) {
    return name.substring(0, 6) + '...'
  }
  return name
}

const centerGraph = () => {
  panX.value = 0
  panY.value = 0
  zoom.value = 1
}

const handleZoomIn = () => {
  zoom.value = Math.min(zoom.value + 0.1, 2)
}

const handleZoomOut = () => {
  zoom.value = Math.max(zoom.value - 0.1, 0.5)
}

const handleReset = () => {
  centerGraph()
}

const handleWheel = (e) => {
  if (e.deltaY < 0) {
    handleZoomIn()
  } else {
    handleZoomOut()
  }
  e.preventDefault()
}

const handleMouseDown = (e) => {
  isDragging.value = true
  lastMousePos.value = { x: e.clientX, y: e.clientY }
}

const handleMouseMove = (e) => {
  if (!isDragging.value) return

  const dx = e.clientX - lastMousePos.value.x
  const dy = e.clientY - lastMousePos.value.y

  panX.value += dx
  panY.value += dy

  lastMousePos.value = { x: e.clientX, y: e.clientY }
}

const handleMouseUp = () => {
  isDragging.value = false
}

const handleNodeClick = (node) => {
  router.push(`/persons/${node.id}`)
}

onMounted(() => {
  loadGraph()
})
</script>

<style scoped lang="scss">
.relation-graph-container {
  padding: 16px;
}

.graph-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.graph-title {
  font-size: 16px;
  font-weight: 500;
  color: var(--text-primary, #303133);
  margin: 0;
}

.graph-actions {
  display: flex;
  gap: 4px;
}

.graph-card {
  min-height: 400px;
}

.graph-canvas {
  width: 100%;
  height: 400px;
  overflow: hidden;
  background: var(--bg-color-light, #fafafa);
  border-radius: 4px;
}

.graph-svg {
  cursor: grab;

  &:active {
    cursor: grabbing;
  }
}

.node-group {
  cursor: pointer;
  transition: all 0.3s;

  &:hover {
    circle {
      stroke-width: 2;
    }
  }
}

.edge-line {
  pointer-events: none;
}

.empty-graph {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}
</style>