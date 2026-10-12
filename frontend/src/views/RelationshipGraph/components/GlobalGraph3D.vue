<template>
  <div class="graph3d-wrapper">
    <div class="graph3d-toolbar">
      <el-tooltip content="重置视角" placement="bottom">
        <el-button :icon="Aim" circle size="small" @click="resetView" />
      </el-tooltip>
      <el-tooltip content="重新布局" placement="bottom">
        <el-button :icon="Refresh" circle size="small" @click="reheat" />
      </el-tooltip>
      <el-tooltip content="切换自动旋转" placement="bottom">
        <el-button
          :icon="RefreshRight"
          circle size="small"
          :type="autoRotate ? 'primary' : ''"
          @click="toggleRotate"
        />
      </el-tooltip>

      <div class="graph3d-legend">
        <span class="legend-item"><i class="dot" style="background:#8a94a6" />亲子</span>
        <span class="legend-item"><i class="dot" style="background:#b6bac2" />非亲生</span>
        <span class="legend-item"><i class="dot" style="background:#f56c6c" />伴侣</span>
        <span class="legend-item"><i class="dot" style="background:#fa8c16" />社会</span>
        <span class="legend-item"><i class="dot" style="background:#13c2c2" />同分组</span>
        <span class="legend-item"><i class="dot" style="background:#722ed1" />同标签</span>
      </div>

      <div class="graph3d-stats" v-if="data">
        {{ data.stats.node_count }} 人 · {{ data.stats.edge_count }} 条关系
        <el-tooltip
          v-if="data.stats.truncated"
          content="同组/同标签关系过多，已截断显示；可通过筛选减少关系类型"
          placement="bottom"
        >
          <el-tag type="warning" size="small">已截断</el-tag>
        </el-tooltip>
      </div>
    </div>

    <div ref="containerRef" class="graph3d-canvas" v-loading="loading">
      <el-empty
        v-if="!loading && (!data || data.nodes.length === 0)"
        class="graph3d-empty"
        description="当前筛选下没有人物，试试放宽筛选条件"
      />
      <div class="graph3d-hint" v-if="data && data.nodes.length">
        拖拽旋转 · 滚轮缩放 · WASD/方向键上下左右平移 · 拖动节点调整布局 · 点击人物查看关系网络
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, shallowRef, watch, onMounted, onBeforeUnmount } from 'vue'
import { Aim, Refresh, RefreshRight } from '@element-plus/icons-vue'
import { avatarColor } from '@/utils/avatar'

const props = defineProps({
  data: { type: Object, default: null },
  loading: { type: Boolean, default: false }
})
const emit = defineEmits(['select'])

const containerRef = ref(null)
const graphRef = shallowRef(null)
let THREERef = null
let spriteMap = new Map()      // nodeId -> THREE.Sprite
let adjacency = new Map()      // nodeId -> Set<nodeId>
let autoRotate = ref(false)
let resizeObserver = null
let themeObserver = null
let highlightNodes = new Set()

// 键盘平移视角：WASD / 方向键，相对当前相机朝向
const MOVE_KEYS = ['KeyW', 'KeyS', 'KeyA', 'KeyD', 'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight']
const moveKeys = new Set()
let moveRafId = null
let lastMoveTs = 0

const readTheme = () => {
  const s = getComputedStyle(document.documentElement)
  const v = (name, fallback) => (s.getPropertyValue(name).trim() || fallback)
  return {
    text: v('--text-primary', '#303133'),
    primary: v('--primary-color', '#409eff')
  }
}

/** 用 Canvas 绘制「头像首字 + 姓名」精灵贴图 */
const buildSprite = (node, theme) => {
  const deceased = !!node.death_date
  const isMe = !!node.is_me
  const fontSize = 34
  const name = node.name.length > 5 ? `${node.name.slice(0, 5)}…` : node.name

  const measure = document.createElement('canvas').getContext('2d')
  measure.font = `500 ${fontSize}px sans-serif`
  const textW = Math.ceil(measure.measureText(name).width)
  const w = Math.max(180, textW + 60)
  const h = 190
  const dpr = Math.min(window.devicePixelRatio || 1, 2)

  const canvas = document.createElement('canvas')
  canvas.width = w * dpr
  canvas.height = h * dpr
  const ctx = canvas.getContext('2d')
  ctx.scale(dpr, dpr)

  // 头像圆
  const cx = w / 2
  const cy = 52
  const r = 36
  ctx.beginPath()
  ctx.arc(cx, cy, r, 0, Math.PI * 2)
  ctx.fillStyle = deceased ? '#a8abb2' : avatarColor(node.name)
  ctx.fill()
  if (isMe) {
    ctx.lineWidth = 4
    ctx.strokeStyle = theme.primary
    ctx.stroke()
  }

  // 首字
  ctx.fillStyle = '#ffffff'
  ctx.font = '600 30px sans-serif'
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'
  ctx.fillText((node.name || '?').charAt(0), cx, cy + 1)

  // 姓名
  ctx.fillStyle = deceased ? '#909399' : theme.text
  ctx.font = `500 ${fontSize}px sans-serif`
  ctx.fillText(name, cx, 128)

  // 已故标记
  if (deceased) {
    ctx.font = '500 22px sans-serif'
    ctx.fillStyle = '#909399'
    ctx.fillText('已故', cx, 166)
  }

  const texture = new THREERef.CanvasTexture(canvas)
  texture.minFilter = THREERef.LinearFilter
  const material = new THREERef.SpriteMaterial({
    map: texture,
    transparent: true,
    depthWrite: false
  })
  const sprite = new THREERef.Sprite(material)
  const scale = 15 + (node.importance || 1) * 1.6 + Math.min(node.degree || 0, 12) * 0.35
  sprite.scale.set(scale * (w / h), scale, 1)
  return sprite
}

const buildAdjacency = (edges) => {
  adjacency = new Map()
  edges.forEach((e) => {
    const a = e.source
    const b = e.target
    if (!adjacency.has(a)) adjacency.set(a, new Set())
    if (!adjacency.has(b)) adjacency.set(b, new Set())
    adjacency.get(a).add(b)
    adjacency.get(b).add(a)
  })
}

const renderGraph = async () => {
  const container = containerRef.value
  if (!container || !props.data || !props.data.nodes || !props.data.nodes.length) return

  if (graphRef.value) {
    graphRef.value._destructor?.()
    graphRef.value = null
    spriteMap = new Map()
  }

  const [{ default: ForceGraph3D }, THREE] = await Promise.all([
    import('3d-force-graph'),
    import('three')
  ])
  THREERef = THREE
  const theme = readTheme()

  const nodes = props.data.nodes.map((n) => ({ ...n }))
  const links = props.data.edges.map((e) => ({ ...e }))
  buildAdjacency(links)

  const graph = new ForceGraph3D(container, {
    controlType: 'orbit',
    backgroundColor: 'rgba(0,0,0,0)',
    showNavInfo: false,
    nodeRelSize: 6,
    linkDirectionalArrowResolution: 8
  })
    .graphData({ nodes, links })
    .backgroundColor('rgba(0,0,0,0)')
    .nodeThreeObject((node) => {
      const sprite = buildSprite(node, theme)
      spriteMap.set(node.id, sprite)
      return sprite
    })
    .nodeLabel((node) => `
      <div style="padding:4px 8px;background:rgba(20,22,28,.85);color:#fff;border-radius:6px;font-size:12px;white-space:nowrap">
        ${node.name}${node.death_date ? '（已故）' : ''}
        <div style="color:#a8abb2;font-size:11px;margin-top:2px">
          直接关系 ${node.degree || 0} · 重要度 ${node.importance || 1}
        </div>
      </div>
    `)
    .linkColor((l) => l.color || '#8a94a6')
    .linkOpacity(0.55)
    .linkWidth((l) => {
      if (l.edge_type === 'spouse') return 1.4
      if (l.edge_type === 'social') return l.width || 0.8
      return 0.8
    })
    // 注意：3d-force-graph 1.73.x / three-forcegraph 不支持 linkLineDash 等虚线 API，
    // 调用不存在的方法会中断链式初始化（onNodeClick/键盘平移会全部失效）；
    // 过期关系改由标签「前」前缀与边色区分
    .linkLabel((l) => (l.label ? `<span style="font-size:11px;color:#606266">${l.label}</span>` : ''))
    .linkDirectionalArrowLength((l) =>
      l.edge_type === 'family' || (l.edge_type === 'social' && l.directed) ? 4 : 0
    )
    .linkDirectionalArrowRelPos(0.85)
    .onNodeClick((node) => emit('select', node.id))
    .onNodeHover((node) => {
      container.style.cursor = node ? 'pointer' : ''
      highlightNodes = new Set()
      if (node) {
        highlightNodes.add(node.id)
        ;(adjacency.get(node.id) || []).forEach((id) => highlightNodes.add(id))
      }
      // 只高亮人物节点：本人与直接关系保持不透明，其余淡出；连线不变
      spriteMap.forEach((sprite, id) => {
        sprite.material.opacity = !node || highlightNodes.has(id) ? 1 : 0.15
      })
    })

  // 力参数：
  // - 亲子/伴侣：短而强的弹簧，让核心家庭聚成紧密团块
  // - 同组/同标签：长而弱的弹簧，只做松散桥接，避免大量跨色线缠在一起
  const linkForce = graph.d3Force('link')
  linkForce
    .distance((l) => {
      if (l.edge_type === 'spouse') return 22
      if (l.edge_type === 'family') return 34
      if (l.edge_type === 'social') return 48
      if (l.edge_type === 'group') return 70
      return 90 // tag
    })
    .strength((l) => {
      if (l.edge_type === 'spouse') return 0.9
      if (l.edge_type === 'family') return 0.7
      if (l.edge_type === 'social') return 0.3
      if (l.edge_type === 'group') return 0.12
      return 0.06 // tag
    })
  graph.d3Force('charge').strength(-170)
  graph.d3VelocityDecay(0.32)

  graphRef.value = graph

  setTimeout(() => graph.zoomToFit(400, 60), 350)
}

const resetView = () => graphRef.value?.zoomToFit(500, 60)
const reheat = () => {
  graphRef.value?.d3ReheatSimulation()
  setTimeout(() => graphRef.value?.zoomToFit(400, 60), 500)
}
const toggleRotate = () => {
  autoRotate.value = !autoRotate.value
  const controls = graphRef.value?.controls?.()
  if (controls) controls.autoRotate = autoRotate.value
  if (controls) controls.autoRotateSpeed = 1.2
}

/** 按住按键时按帧积分平移，保证持续移动的手感 */
const moveStep = (ts) => {
  const graph = graphRef.value
  const camera = graph?.camera?.()
  const controls = graph?.controls?.()
  if (!THREERef || !camera || moveKeys.size === 0) {
    moveRafId = null
    return
  }

  const dt = Math.min((ts - lastMoveTs) / 1000, 0.05)
  lastMoveTs = ts

  const forward = new THREERef.Vector3()
  camera.getWorldDirection(forward)
  // 右手系：right = forward × up，保证 D=右、A=左
  const right = new THREERef.Vector3().crossVectors(forward, camera.up).normalize()
  // 屏幕平面内的正上方：right × forward，保证 W/S 是上下平移而非沿视线缩放
  const screenUp = new THREERef.Vector3().crossVectors(right, forward).normalize()

  const delta = new THREERef.Vector3()
  if (moveKeys.has('KeyW') || moveKeys.has('ArrowUp')) delta.add(screenUp)
  if (moveKeys.has('KeyS') || moveKeys.has('ArrowDown')) delta.sub(screenUp)
  if (moveKeys.has('KeyD') || moveKeys.has('ArrowRight')) delta.add(right)
  if (moveKeys.has('KeyA') || moveKeys.has('ArrowLeft')) delta.sub(right)

  if (delta.lengthSq() > 0) {
    // 平移速度与当前轨道视距成正比：缩放越远移动越快；约 0.6 倍视距/秒
    const dist = controls ? camera.position.distanceTo(controls.target) : 300
    delta.normalize().multiplyScalar(dist * 0.6 * dt)
    // 相机与轨道目标一起平移，之后拖拽仍围绕新的目标点旋转
    camera.position.add(delta)
    if (controls) {
      controls.target.add(delta)
      controls.update()
    }
  }
  moveRafId = requestAnimationFrame(moveStep)
}

const ensureMoveLoop = () => {
  if (moveRafId === null) {
    lastMoveTs = performance.now()
    moveRafId = requestAnimationFrame(moveStep)
  }
}

const isEditableTarget = () => {
  const el = document.activeElement
  if (!el || !el.tagName) return false
  return el.tagName === 'INPUT' || el.tagName === 'TEXTAREA' || el.isContentEditable
}

const onKeyDown = (e) => {
  if (e.ctrlKey || e.metaKey || e.altKey || isEditableTarget()) return
  if (!MOVE_KEYS.includes(e.code)) return
  e.preventDefault()
  moveKeys.add(e.code)
  // 手动平移时关闭自动旋转，避免互相打架
  if (autoRotate.value) {
    autoRotate.value = false
    const controls = graphRef.value?.controls?.()
    if (controls) controls.autoRotate = false
  }
  ensureMoveLoop()
}

const onKeyUp = (e) => {
  if (MOVE_KEYS.includes(e.code)) moveKeys.delete(e.code)
}

const clearMoveKeys = () => moveKeys.clear()

watch(() => props.data, renderGraph, { deep: false })

onMounted(() => {
  renderGraph()
  resizeObserver = new ResizeObserver(() => {
    const g = graphRef.value
    if (g && containerRef.value) {
      g.width(containerRef.value.clientWidth)
      g.height(containerRef.value.clientHeight)
      g.refresh()
    }
  })
  resizeObserver.observe(containerRef.value)

  themeObserver = new MutationObserver(() => renderGraph())
  themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] })

  window.addEventListener('keydown', onKeyDown)
  window.addEventListener('keyup', onKeyUp)
  window.addEventListener('blur', clearMoveKeys)
})

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
  themeObserver?.disconnect()
  window.removeEventListener('keydown', onKeyDown)
  window.removeEventListener('keyup', onKeyUp)
  window.removeEventListener('blur', clearMoveKeys)
  if (moveRafId !== null) cancelAnimationFrame(moveRafId)
  spriteMap.forEach((s) => {
    s.material.map?.dispose()
    s.material.dispose()
  })
  spriteMap = new Map()
  graphRef.value?._destructor?.()
  graphRef.value = null
})
</script>

<style scoped>
.graph3d-wrapper {
  background: var(--card-bg, #ffffff);
  border: 1px solid var(--border-color, #dcdfe6);
  border-radius: var(--radius-lg, 12px);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.graph3d-toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  border-bottom: 1px solid var(--border-lighter, #ebeef5);
  background: var(--bg-color-light, #fafbfc);
}

.graph3d-legend {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-left: 12px;
  font-size: 12px;
  color: var(--text-secondary, #909399);
}

.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.legend-item .dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}

.graph3d-stats {
  margin-left: auto;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--text-secondary, #909399);
}

.graph3d-canvas {
  position: relative;
  flex: 1;
  min-height: 520px;
  height: calc(100vh - 218px);
  background:
    radial-gradient(circle at 50% 40%, rgba(64, 158, 255, 0.06), transparent 60%),
    var(--bg-color, #f5f7fa);
}

:global(.dark) .graph3d-canvas {
  background:
    radial-gradient(circle at 50% 40%, rgba(64, 158, 255, 0.12), transparent 60%),
    #14161c;
}

.graph3d-empty {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.graph3d-hint {
  position: absolute;
  left: 16px;
  bottom: 12px;
  font-size: 12px;
  color: var(--text-placeholder, #b6b8bd);
  pointer-events: none;
  user-select: none;
}

@media (max-width: 768px) {
  .graph3d-legend { display: none; }
}
</style>
