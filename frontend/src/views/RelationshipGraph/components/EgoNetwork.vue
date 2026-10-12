<template>
  <div class="ego-wrapper" v-loading="loading">
    <div class="ego-toolbar">
      <el-button :icon="Back" size="small" @click="$emit('back')">返回全局图</el-button>
      <el-button
        v-if="data?.center"
        type="primary"
        size="small"
        :icon="User"
        @click="$emit('view-detail', data.center.id)"
      >
        查看「{{ data.center.name }}」资料
      </el-button>

      <div class="ego-legend">
        <span v-for="c in visibleCategories" :key="c.key" class="legend-item">
          <i class="dot" :style="{ background: c.color }" />{{ c.label }}
          <em>{{ counts[c.key] || 0 }}</em>
        </span>
      </div>
    </div>

    <div class="ego-canvas">
      <el-empty
        v-if="!loading && (!data || !data.center)"
        class="ego-empty"
        description="未找到该人物"
      />
      <el-empty
        v-else-if="!loading && data && data.nodes.length === 0"
        class="ego-empty"
        description="还没有维护任何直接关系"
      />

      <svg
        v-else-if="data"
        class="ego-svg"
        viewBox="-500 -500 1000 1000"
        preserveAspectRatio="xMidYMid meet"
      >
        <!-- 参考环 -->
        <circle r="300" class="ring ring-inner" />
        <circle :r="layout.radius" class="ring" />

        <!-- 分类扇区底色与标题 -->
        <g v-for="sector in layout.sectors" :key="sector.key">
          <path
            :d="sectorArc(sector)"
            :stroke="sector.color"
            class="sector-arc"
          />
          <g :transform="polar(sector.midAngle, layout.radius + 92)">
            <rect
              x="-58" y="-15" width="116" height="30" rx="15"
              :fill="sector.color" class="sector-label-bg"
            />
            <text
              y="1" text-anchor="middle" dominant-baseline="middle"
              class="sector-label-text"
            >
              {{ sector.label }} {{ sector.count }}
              <tspan v-if="hasMore[sector.key]" class="sector-more">+</tspan>
            </text>
          </g>
        </g>

        <!-- 关系线 -->
        <g class="edges">
          <line
            v-for="edge in layout.edges"
            :key="edge.id"
            :x1="0" :y1="0"
            :x2="edge.x2" :y2="edge.y2"
            :stroke="edge.color"
            :stroke-dasharray="edge.dashed ? '6 5' : undefined"
            class="edge-line"
          />
          <g v-for="edge in layout.edges" :key="edge.id + '-label'">
            <rect
              :x="edge.lx - edgeLabelWidth(edge.label) / 2"
              :y="edge.ly - 11"
              :width="edgeLabelWidth(edge.label)"
              height="22" rx="11"
              class="edge-label-bg"
            />
            <text
              :x="edge.lx" :y="edge.ly"
              text-anchor="middle" dominant-baseline="middle"
              class="edge-label"
            >{{ edge.label }}</text>
          </g>
        </g>

        <!-- 外圈人物 -->
        <g
          v-for="(node, idx) in layout.nodes"
          :key="node.id"
          :transform="`translate(${node.x},${node.y})`"
          class="ego-node-slot"
          @click="$emit('recenter', node.id)"
        >
          <g
            class="ego-node"
            :style="{ animationDelay: `${Math.min(idx * 25, 500)}ms` }"
          >
            <circle
              r="30"
              :fill="node.death_date ? '#a8abb2' : node.color"
              :stroke="node.color"
              class="node-circle"
            />
            <text y="1" text-anchor="middle" dominant-baseline="middle" class="node-initial">
              {{ node.name.charAt(0) }}
            </text>
            <text y="56" text-anchor="middle" class="node-name">
              {{ node.name.length > 5 ? node.name.slice(0, 5) + '…' : node.name }}
            </text>
            <text v-if="node.death_date" y="74" text-anchor="middle" class="node-dead">已故</text>
          </g>
        </g>

        <!-- 中心人物 -->
        <g
          class="ego-center"
          @click="$emit('view-detail', data.center.id)"
        >
          <circle
            r="48"
            :fill="data.center.death_date ? '#909399' : centerColor"
            :stroke="data.center.is_me ? '#e6a23c' : '#ffffff'"
            :stroke-width="data.center.is_me ? 5 : 3"
            class="center-circle"
          />
          <text y="2" text-anchor="middle" dominant-baseline="middle" class="center-initial">
            {{ data.center.name.charAt(0) }}
          </text>
          <text y="78" text-anchor="middle" class="center-name">
            {{ data.center.name }}
          </text>
          <text y="100" text-anchor="middle" class="center-hint">点击查看资料</text>
        </g>
      </svg>

      <div class="ego-tip" v-if="data && data.nodes.length">
        点击外圈人物可切换关系中心
      </div>
    </div>
  </div>
)
</template>

<script setup>
import { computed } from 'vue'
import { Back, User } from '@element-plus/icons-vue'
import { avatarColor } from '@/utils/avatar'

const props = defineProps({
  data: { type: Object, default: null },
  loading: { type: Boolean, default: false }
})
defineEmits(['back', 'recenter', 'view-detail'])

const CATEGORIES = [
  { key: 'parent', label: '长辈', color: '#409eff' },
  { key: 'spouse', label: '伴侣', color: '#f56c6c' },
  { key: 'social', label: '社会', color: '#fa8c16' },
  { key: 'child', label: '晚辈', color: '#67c23a' },
  { key: 'group', label: '同分组', color: '#13c2c2' },
  { key: 'tag', label: '同标签', color: '#722ed1' }
]

const colorOf = (key) => (CATEGORIES.find((c) => c.key === key) || {}).color || '#909399'

const counts = computed(() => props.data?.counts || {})
const hasMore = computed(() => props.data?.has_more || {})

const visibleCategories = computed(() =>
  CATEGORIES.filter((c) => (counts.value[c.key] || 0) > 0)
)

const centerColor = computed(() =>
  props.data?.center ? avatarColor(props.data.center.name) : '#409eff'
)

const polar = (angleRad, r) => ({
  x: Math.cos(angleRad) * r,
  y: Math.sin(angleRad) * r
})

const edgeLabelWidth = (label) => Math.max(44, (label || '').length * 13 + 18)

const layout = computed(() => {
  const empty = { nodes: [], edges: [], sectors: [] }
  if (!props.data || !props.data.nodes.length) return empty

  const total = props.data.nodes.length
  const cats = CATEGORIES.map((c) => ({
    ...c,
    count: props.data.nodes.filter((n) => n.category === c.key).length
  })).filter((c) => c.count > 0)

  // 每个节点分配的角度槽（弧度），分类间留空隙
  const gapDeg = 16
  const slotDeg = Math.max(14, (360 - cats.length * gapDeg) / total)
  const slot = (slotDeg * Math.PI) / 180
  const gap = (gapDeg * Math.PI) / 180

  // 半径随人数增大，保证标签不挤
  const radius = Math.max(280, Math.min(430, total * 12 + 200))

  // 从长辈开始顺时针排列，并让长辈扇区居中于正上方(-90°)
  let cursor = (-90 * Math.PI) / 180 - (cats[0].count * slot) / 2

  const positioned = []
  const sectors = []

  cats.forEach((cat) => {
    const sectorStart = cursor
    const list = props.data.nodes.filter((n) => n.category === cat.key)
    list.forEach((node, i) => {
      const angle = sectorStart + i * slot + slot / 2
      const p = polar(angle, radius)
      positioned.push({
        ...node,
        color: node.death_date ? '#a8abb2' : colorOf(cat.key),
        angle,
        x: p.x,
        y: p.y
      })
    })
    const sectorEnd = sectorStart + list.length * slot
    sectors.push({
      key: cat.key,
      label: cat.label,
      color: cat.color,
      count: cat.count,
      start: sectorStart,
      end: sectorEnd,
      midAngle: (sectorStart + sectorEnd) / 2
    })
    cursor = sectorEnd + gap
  })

  const byId = new Map(positioned.map((n) => [n.id, n]))
  const edges = (props.data.edges || []).map((e) => {
    const node = byId.get(e.target)
    if (!node) return null
    const color = colorOf(e.edge_type)
    const lx = node.x * 0.52
    const ly = node.y * 0.52
    return {
      ...e,
      x2: node.x * 0.88,
      y2: node.y * 0.88,
      lx,
      ly,
      color,
      label: (e.label || '').split(' / ')[0]
    }
  }).filter(Boolean)

  return { nodes: positioned, edges, sectors, radius }
})

// 扇区底色弧线路径
const sectorArc = (sector) => {
  const r = layout.value.radius + 26
  const p1 = polar(sector.start, r)
  const p2 = polar(sector.end, r)
  const large = sector.end - sector.start > Math.PI ? 1 : 0
  return `M ${p1.x} ${p1.y} A ${r} ${r} 0 ${large} 1 ${p2.x} ${p2.y}`
}
</script>

<style scoped>
.ego-wrapper {
  background: var(--card-bg, #ffffff);
  border: 1px solid var(--border-color, #dcdfe6);
  border-radius: var(--radius-lg, 12px);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.ego-toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  border-bottom: 1px solid var(--border-lighter, #ebeef5);
  background: var(--bg-color-light, #fafbfc);
  flex-wrap: wrap;
}

.ego-legend {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-left: auto;
  font-size: 12px;
  color: var(--text-secondary, #909399);
}

.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.legend-item em {
  font-style: normal;
  font-weight: 600;
  color: var(--text-regular, #606266);
}

.legend-item .dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.ego-canvas {
  position: relative;
  flex: 1;
  min-height: 520px;
  height: calc(100vh - 218px);
}

.ego-svg {
  width: 100%;
  height: 100%;
}

.ring {
  fill: none;
  stroke: var(--border-lighter, #ebeef5);
  stroke-width: 1;
  stroke-dasharray: 3 6;
}

.ring-inner {
  stroke-dasharray: 2 8;
  opacity: 0.7;
}

.sector-arc {
  fill: none;
  stroke-width: 3;
  stroke-linecap: round;
  opacity: 0.35;
}

.sector-label-text {
  fill: #ffffff;
  font-size: 14px;
  font-weight: 600;
}

.sector-more {
  font-size: 12px;
}

.edge-line {
  stroke-width: 1.5;
  opacity: 0.55;
}

.edge-label-bg {
  fill: var(--card-bg, #ffffff);
  stroke: var(--border-lighter, #ebeef5);
  stroke-width: 1;
  opacity: 0.92;
}

.edge-label {
  font-size: 12px;
  fill: var(--text-secondary, #909399);
}

.ego-node-slot {
  cursor: pointer;
}

.ego-node {
  animation: ego-pop 0.45s ease both;
  transform-box: fill-box;
  transform-origin: center;
}

.node-circle {
  stroke-width: 3;
  opacity: 0.95;
  transition: opacity 0.15s ease;
}

.ego-node:hover .node-circle {
  opacity: 1;
  filter: brightness(1.06);
}

.node-initial {
  fill: #ffffff;
  font-size: 24px;
  font-weight: 600;
  pointer-events: none;
}

.node-name {
  font-size: 14px;
  font-weight: 500;
  fill: var(--text-primary, #303133);
  pointer-events: none;
}

.node-dead {
  font-size: 11px;
  fill: #909399;
  pointer-events: none;
}

.ego-center {
  cursor: pointer;
  animation: ego-pop 0.5s ease both;
}

.center-circle {
  filter: drop-shadow(0 4px 12px rgba(0, 0, 0, 0.18));
  transition: transform 0.15s ease;
  transform-box: fill-box;
  transform-origin: center;
}

.ego-center:hover .center-circle {
  transform: scale(1.06);
}

.center-initial {
  fill: #ffffff;
  font-size: 34px;
  font-weight: 700;
  pointer-events: none;
}

.center-name {
  font-size: 18px;
  font-weight: 700;
  fill: var(--text-primary, #303133);
  pointer-events: none;
}

.center-hint {
  font-size: 12px;
  fill: var(--text-placeholder, #b6b8bd);
  pointer-events: none;
}

.ego-empty {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.ego-tip {
  position: absolute;
  left: 50%;
  bottom: 14px;
  transform: translateX(-50%);
  font-size: 12px;
  color: var(--text-placeholder, #b6b8bd);
  pointer-events: none;
}

@keyframes ego-pop {
  from { opacity: 0; transform: scale(0.4); }
  to { opacity: 1; }
}

@media (max-width: 768px) {
  .ego-legend { display: none; }
}
</style>
