<template>
  <Teleport to="body">
    <div v-if="visible" class="onboarding">
      <!-- 四块遮罩，在目标周围挖出聚光灯区域 -->
      <template v-if="rect">
        <div class="ob-mask" :style="maskStyle.top" />
        <div class="ob-mask" :style="maskStyle.bottom" />
        <div class="ob-mask" :style="maskStyle.left" />
        <div class="ob-mask" :style="maskStyle.right" />
        <div class="ob-spotlight" :style="spotStyle" />
      </template>
      <div v-else class="ob-mask ob-mask-full" />

      <!-- 引导卡片 -->
      <div class="ob-card" :class="{ 'ob-card-center': !rect }" :style="cardStyle">
        <div class="ob-step-no">{{ stepIndex }} / {{ steps.length }}</div>
        <h3 class="ob-title">{{ current.title }}</h3>
        <p class="ob-desc">{{ current.desc }}</p>
        <div class="ob-footer">
          <div class="ob-dots">
            <span
              v-for="(s, i) in steps"
              :key="i"
              class="ob-dot"
              :class="{ active: i === stepIndex - 1 }"
            />
          </div>
          <div class="ob-actions">
            <el-button text size="small" @click="skip">跳过引导</el-button>
            <el-button
              v-if="stepIndex > 1"
              size="small"
              @click="prev"
            >上一步</el-button>
            <el-button type="primary" size="small" @click="next">
              {{ stepIndex === steps.length ? '开始使用' : '下一步' }}
            </el-button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, nextTick, onBeforeUnmount } from 'vue'

const props = defineProps({
  isMobile: { type: Boolean, default: false }
})

const STORAGE_KEY = 'yunpu_onboarding_seen_v1'
const PAD = 6 // 聚光灯与目标的间距

const visible = ref(false)
const stepIndex = ref(1) // 1..steps.length；带 target 的步骤序号
const rect = ref(null)

const desktopSteps = [
  {
    target: null,
    title: '欢迎使用云谱 👋',
    desc: '花 30 秒了解核心功能，让云谱从"记事本"变成你的关系管家。'
  },
  {
    target: '[data-guide="search"]',
    placement: 'bottom',
    title: '全局搜索 / 跳转',
    desc: '点击搜索框，或随时按下 Ctrl + K（Mac 为 ⌘ + K），快速找人、跳转到任意页面。'
  },
  {
    target: '[data-guide="nav"]',
    placement: 'right',
    title: '左侧导航',
    desc: '仪表盘、人物管理、家族关系、关系图谱、分组管理都在这里；侧边栏还可以一键收起。'
  },
  {
    target: '[data-guide="nav-graph"]',
    placement: 'right',
    title: '关系图谱（新）',
    desc: '3D 全局关系网络，支持按亲子/伴侣/分组/标签筛选；点击任意人物，查看以 TA 为中心的人际圈。'
  },
  {
    target: null,
    title: '准备就绪！',
    desc: '建议先到「人物管理」添加第一位人物。想再看一遍引导？点头像菜单里的「新手引导」即可。'
  }
]

const mobileSteps = [
  {
    target: null,
    title: '欢迎使用云谱 👋',
    desc: '花 30 秒了解核心功能，让云谱成为你随身携带的关系管家。'
  },
  {
    target: '[data-guide="search"]',
    placement: 'bottom',
    title: '全局搜索 / 跳转',
    desc: '点右上角搜索图标，可快速搜索人物、跳转到任意页面。'
  },
  {
    target: '[data-guide="tabbar"]',
    placement: 'top',
    title: '底部导航',
    desc: '首页、人物、关系、分组、我的，五个标签一键切换。'
  },
  {
    target: '[data-guide="tab-graph"]',
    placement: 'top',
    title: '关系图谱（新）',
    desc: '3D 全局关系网络；点「关系」进入，还能点任意人物查看以 TA 为中心的人际圈。'
  },
  {
    target: null,
    title: '准备就绪！',
    desc: '建议先到「人物」添加第一位人物。想再看一遍？点头像菜单里的「新手引导」。'
  }
]

const steps = computed(() => (props.isMobile ? mobileSteps : desktopSteps))
const current = computed(() => steps.value[stepIndex.value - 1])

const spotStyle = computed(() => {
  if (!rect.value) return {}
  const r = rect.value
  return {
    top: `${r.top - PAD}px`,
    left: `${r.left - PAD}px`,
    width: `${r.width + PAD * 2}px`,
    height: `${r.height + PAD * 2}px`
  }
})

const maskStyle = computed(() => {
  const r = rect.value
  const w = window.innerWidth
  const h = window.innerHeight
  if (!r) return { top: {}, bottom: {}, left: {}, right: {} }
  const top = r.top - PAD
  const left = r.left - PAD
  const right = left + r.width + PAD * 2
  const bottom = top + r.height + PAD * 2
  return {
    top: { top: 0, left: 0, right: 0, height: `${Math.max(top, 0)}px` },
    bottom: { top: `${bottom}px`, left: 0, right: 0, bottom: 0 },
    left: { top: `${top}px`, left: 0, width: `${Math.max(left, 0)}px`, height: `${r.height + PAD * 2}px` },
    right: { top: `${top}px`, left: `${right}px`, right: 0, height: `${r.height + PAD * 2}px` }
  }
})

const cardStyle = computed(() => {
  if (!rect.value || !current.value.target) return {}
  const r = rect.value
  const cw = 320
  const ch = 200
  const margin = 12
  const vw = window.innerWidth
  const vh = window.innerHeight

  let top = 0
  let left = 0
  switch (current.value.placement) {
    case 'bottom':
      top = r.bottom + PAD + 12
      left = r.left
      break
    case 'right':
      top = r.top
      left = r.right + PAD + 12
      break
    case 'top':
      top = r.top - PAD - 12 - ch
      left = r.left + r.width / 2 - cw / 2
      break
    case 'left':
      top = r.top
      left = r.left - PAD - 12 - cw
      break
  }
  // 视口兜底
  left = Math.min(Math.max(left, margin), vw - cw - margin)
  if (top < margin) top = r.bottom + PAD + 12
  if (top + ch > vh - margin) top = Math.max(margin, vh - ch - margin)
  return { top: `${top}px`, left: `${left}px`, width: `${cw}px` }
})

const measure = () => {
  const sel = current.value?.target
  if (!sel) {
    rect.value = null
    return
  }
  const el = document.querySelector(sel)
  if (!el) {
    rect.value = null
    return
  }
  rect.value = el.getBoundingClientRect()
}

const go = async (n) => {
  stepIndex.value = n
  await nextTick()
  measure()
}

const next = () => {
  if (stepIndex.value >= steps.value.length) {
    finish()
  } else {
    go(stepIndex.value + 1)
  }
}

const prev = () => go(stepIndex.value - 1)

const finish = () => {
  visible.value = false
  rect.value = null
  try { localStorage.setItem(STORAGE_KEY, '1') } catch { /* ignore */ }
  teardownListeners()
}

const skip = () => finish()

const start = () => {
  visible.value = true
  setupListeners()
  go(1)
}

const autoStart = () => {
  let seen = false
  try { seen = localStorage.getItem(STORAGE_KEY) === '1' } catch { /* ignore */ }
  if (!seen) start()
}

const onKeydown = (e) => {
  if (!visible.value) return
  if (e.key === 'Escape') skip()
  if (e.key === 'ArrowRight') next()
  if (e.key === 'ArrowLeft' && stepIndex.value > 1) prev()
}

const onReposition = () => { if (visible.value) measure() }

function setupListeners() {
  window.addEventListener('resize', onReposition)
  window.addEventListener('scroll', onReposition, true)
  window.addEventListener('keydown', onKeydown)
}

function teardownListeners() {
  window.removeEventListener('resize', onReposition)
  window.removeEventListener('scroll', onReposition, true)
  window.removeEventListener('keydown', onKeydown)
}

onBeforeUnmount(teardownListeners)

defineExpose({ start, autoStart })
</script>

<style scoped>
.onboarding {
  position: fixed;
  inset: 0;
  z-index: 3000;
  pointer-events: none;
}

.ob-mask {
  position: fixed;
  background: rgba(0, 0, 0, 0.55);
  transition: all 0.25s ease;
  /* 遮罩拦截所有点击/触摸，引导期间不能操作被引导界面 */
  pointer-events: auto;
}

.ob-mask-full {
  inset: 0;
}

.ob-spotlight {
  position: fixed;
  border-radius: 10px;
  box-shadow: 0 0 0 2px var(--el-color-primary, #409eff), 0 0 24px rgba(64, 158, 255, 0.45);
  transition: all 0.25s ease;
  /* 高亮区域本身也拦截点击（透明层），引导期间整页只有引导卡片可交互 */
  pointer-events: auto;
  background: transparent;
  animation: ob-pulse 2s ease-in-out infinite;
}

@keyframes ob-pulse {
  0%, 100% { box-shadow: 0 0 0 2px var(--el-color-primary, #409eff), 0 0 18px rgba(64, 158, 255, 0.35); }
  50% { box-shadow: 0 0 0 2px var(--el-color-primary, #409eff), 0 0 32px rgba(64, 158, 255, 0.65); }
}

.ob-card {
  position: fixed;
  width: 320px;
  background: var(--card-bg, #fff);
  color: var(--text-primary, #303133);
  border-radius: 14px;
  padding: 20px 20px 14px;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.22);
  pointer-events: auto;
  transition: top 0.25s ease, left 0.25s ease;
}

.ob-card-center {
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}

.ob-step-no {
  font-size: 12px;
  color: var(--text-secondary, #909399);
  margin-bottom: 6px;
}

.ob-title {
  margin: 0 0 8px;
  font-size: 17px;
  font-weight: 600;
}

.ob-desc {
  margin: 0 0 18px;
  font-size: 13.5px;
  line-height: 1.7;
  color: var(--text-regular, #606266);
}

.ob-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.ob-dots {
  display: flex;
  gap: 5px;
}

.ob-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--border-color, #dcdfe6);
  transition: all 0.2s;
}

.ob-dot.active {
  width: 16px;
  border-radius: 3px;
  background: var(--el-color-primary, #409eff);
}

.ob-actions {
  display: flex;
  align-items: center;
  gap: 6px;
}
</style>
