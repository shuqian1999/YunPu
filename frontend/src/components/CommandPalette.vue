<template>
  <Teleport to="body">
    <Transition name="cmdk-fade">
      <div v-if="visible" class="cmdk-overlay" @click.self="close">
        <div class="cmdk-panel" role="dialog" aria-modal="true" aria-label="命令面板">
          <div class="cmdk-input-wrap">
            <el-icon class="cmdk-search-icon"><Search /></el-icon>
            <input
              ref="inputRef"
              v-model="query"
              type="text"
              class="cmdk-input"
              placeholder="搜索人物，或输入「新建 / 仪表盘 / 设置」…"
              @keydown="onKeydown"
              @compositionstart="isComposing = true"
              @compositionend="isComposing = false"
            />
            <kbd class="cmdk-kbd">ESC</kbd>
          </div>

          <div class="cmdk-body" v-loading="searching">
            <!-- 人物结果 -->
            <div v-if="persons.length" class="cmdk-group">
              <div class="cmdk-group-title">人物</div>
              <div
                v-for="(person, i) in persons"
                :key="`p-${person.id}`"
                class="cmdk-item"
                :class="{ active: activeIndex === personIndexStart + i }"
                @mouseenter="activeIndex = personIndexStart + i"
                @click="execute(flatItems[personIndexStart + i])"
              >
                <PersonAvatar :name="displayName(person)" :src="person.avatar_url" :size="32" />
                <div class="cmdk-item-main">
                  <span class="cmdk-item-title">
                    {{ displayName(person) }}
                    <em v-if="person.death_date" class="cmdk-deceased">已故</em>
                  </span>
                  <span class="cmdk-item-sub">{{ personSub(person) }}</span>
                </div>
                <el-icon class="cmdk-item-icon"><User /></el-icon>
              </div>
            </div>

            <!-- 动作 / 导航 -->
            <div v-if="filteredActions.length" class="cmdk-group">
              <div class="cmdk-group-title">
                {{ query.trim() ? '操作' : '快速导航 / 操作' }}
              </div>
              <div
                v-for="(action, i) in filteredActions"
                :key="action.id"
                class="cmdk-item"
                :class="{ active: activeIndex === actionIndexStart + i }"
                @mouseenter="activeIndex = actionIndexStart + i"
                @click="execute(flatItems[actionIndexStart + i])"
              >
                <span class="cmdk-action-icon">
                  <el-icon><component :is="action.icon" /></el-icon>
                </span>
                <div class="cmdk-item-main">
                  <span class="cmdk-item-title">{{ action.title }}</span>
                  <span v-if="action.hint" class="cmdk-item-sub">{{ action.hint }}</span>
                </div>
                <span v-if="action.path" class="cmdk-path">{{ action.path }}</span>
              </div>
            </div>

            <!-- 无结果 -->
            <div
              v-if="!searching && !persons.length && !filteredActions.length"
              class="cmdk-empty"
            >
              <el-icon><Search /></el-icon>
              <span>没有找到与「{{ query }}」相关的人物或操作</span>
            </div>
          </div>

          <div class="cmdk-footer">
            <span><kbd>↑</kbd><kbd>↓</kbd> 选择</span>
            <span><kbd>↵</kbd> 打开</span>
            <span><kbd>⌘/Ctrl</kbd> + <kbd>K</kbd> 唤起</span>
          </div>
        </div>
      </div>
    </Transition>

    <!-- 新建人物表单 -->
    <PersonForm
      v-model:visible="formVisible"
      :person-id="null"
      @success="onPersonCreated"
    />
  </Teleport>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import {
  Search, User, Plus, Odometer, Share, Connection, CollectionTag, Setting
} from '@element-plus/icons-vue'
import { searchPersons } from '@/api/search'
import PersonAvatar from './PersonAvatar.vue'
import PersonForm from './PersonForm.vue'

const router = useRouter()

const visible = ref(false)
const query = ref('')
const persons = ref([])
const searching = ref(false)
const activeIndex = ref(0)
const isComposing = ref(false)
const inputRef = ref(null)
const formVisible = ref(false)

let searchTimer = null

const navActions = [
  { id: 'nav-dashboard', title: '仪表盘', icon: Odometer, path: '/dashboard', keywords: 'dashboard home 首页 概览' },
  { id: 'nav-persons', title: '人物管理', icon: User, path: '/persons', keywords: 'person people 联系人 人物列表' },
  { id: 'nav-family', title: '家族关系', icon: Share, path: '/family', keywords: 'family 家谱 图谱 亲属' },
  { id: 'nav-relationships', title: '关系图谱', icon: Connection, path: '/relationships', keywords: 'graph 3d 关系网 链接图 ego 人物网络' },
  { id: 'nav-groups', title: '分组管理', icon: CollectionTag, path: '/groups', keywords: 'group tag 分组 标签' },
  { id: 'nav-settings', title: '设置', icon: Setting, path: '/settings', keywords: 'setting config 配置 偏好' }
]

const specialActions = [
  { id: 'action-new-person', title: '新建人物', icon: Plus, action: 'new-person', hint: '添加一位新联系人', keywords: 'new create add 新建 添加 创建 联系人' }
]

const filteredActions = computed(() => {
  const all = [...specialActions, ...navActions]
  const q = query.value.trim().toLowerCase()
  if (!q) return all
  return all.filter(
    (a) =>
      a.title.toLowerCase().includes(q) ||
      (a.keywords || '').toLowerCase().includes(q)
  )
})

// 扁平化可选项，用于键盘导航索引
const flatItems = computed(() => [
  ...persons.value.map((p) => ({ kind: 'person', ...p })),
  ...filteredActions.value.map((a) => ({ kind: 'action', ...a }))
])

const personIndexStart = 0
const actionIndexStart = computed(() => persons.value.length)

const displayName = (person) => {
  const full = `${person.last_name || ''}${person.first_name || ''}`.trim()
  return full || person.nickname || '未命名'
}

const personSub = (person) => {
  const parts = []
  if (person.nickname) parts.push(person.nickname)
  if (person.company) parts.push(person.company)
  else if (person.occupation) parts.push(person.occupation)
  return parts.join(' · ') || '查看人物详情'
}

const runSearch = async () => {
  const q = query.value.trim()
  if (!q) {
    persons.value = []
    searching.value = false
    activeIndex.value = 0
    return
  }
  searching.value = true
  try {
    const res = await searchPersons(q)
    persons.value = Array.isArray(res) ? res.slice(0, 8) : []
  } catch (err) {
    console.error('命令面板搜索失败', err)
    persons.value = []
  } finally {
    searching.value = false
    activeIndex.value = 0
  }
}

const onQueryInput = () => {
  activeIndex.value = 0
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(runSearch, 220)
}

const execute = (item) => {
  if (!item) return
  close()
  if (item.kind === 'person') {
    router.push(`/persons/${item.id}`)
  } else if (item.action === 'new-person') {
    nextTick(() => { formVisible.value = true })
  } else if (item.path) {
    router.push(item.path)
  }
}

const onPersonCreated = () => {
  formVisible.value = false
  router.push('/persons')
}

const onKeydown = (e) => {
  const total = flatItems.value.length
  if (e.key === 'ArrowDown') {
    e.preventDefault()
    if (total) activeIndex.value = (activeIndex.value + 1) % total
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    if (total) activeIndex.value = (activeIndex.value - 1 + total) % total
  } else if (e.key === 'Enter') {
    if (isComposing.value) return
    e.preventDefault()
    execute(flatItems.value[activeIndex.value])
  } else if (e.key === 'Escape') {
    e.preventDefault()
    close()
  }
}

const reset = () => {
  query.value = ''
  persons.value = []
  activeIndex.value = 0
  searching.value = false
  if (searchTimer) clearTimeout(searchTimer)
}

const open = () => {
  reset()
  visible.value = true
  document.body.style.overflow = 'hidden'
  nextTick(() => inputRef.value?.focus())
}

const close = () => {
  visible.value = false
  document.body.style.overflow = ''
}

const onGlobalKeydown = (e) => {
  if ((e.metaKey || e.ctrlKey) && (e.key === 'k' || e.key === 'K')) {
    e.preventDefault()
    visible.value ? close() : open()
  }
}

// 输入变化触发防抖搜索
watch(query, onQueryInput)

onMounted(() => {
  window.addEventListener('keydown', onGlobalKeydown)
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', onGlobalKeydown)
  if (searchTimer) clearTimeout(searchTimer)
  document.body.style.overflow = ''
})

defineExpose({ open, close })
</script>

<style scoped lang="scss">
.cmdk-overlay {
  position: fixed;
  inset: 0;
  z-index: var(--z-modal, 2200);
  background: rgba(0, 0, 0, 0.35);
  backdrop-filter: blur(2px);
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding: 14vh 16px 16px;
}

.cmdk-panel {
  width: 100%;
  max-width: 620px;
  background: var(--card-bg, #ffffff);
  border: 1px solid var(--border-color, #dcdfe6);
  border-radius: 14px;
  box-shadow: 0 18px 48px rgba(0, 0, 0, 0.22);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.cmdk-input-wrap {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 16px;
  border-bottom: 1px solid var(--border-lighter, #ebeef5);
}

.cmdk-search-icon {
  font-size: 18px;
  color: var(--text-secondary, #909399);
}

.cmdk-input {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  font-size: 15px;
  color: var(--text-primary, #303133);
}

.cmdk-input::placeholder {
  color: var(--text-placeholder, #b6b8bd);
}

.cmdk-kbd {
  font-family: inherit;
  font-size: 11px;
  color: var(--text-secondary, #909399);
  background: var(--bg-color, #f5f7fa);
  border: 1px solid var(--border-color, #dcdfe6);
  border-radius: 5px;
  padding: 1px 6px;
}

.cmdk-body {
  max-height: 48vh;
  overflow-y: auto;
  padding: 8px;
  min-height: 120px;
  position: relative;
}

.cmdk-group {
  margin-bottom: 6px;
}

.cmdk-group-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary, #909399);
  padding: 8px 10px 4px;
}

.cmdk-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 10px;
  border-radius: 8px;
  cursor: pointer;
}

.cmdk-item.active {
  background: var(--primary-color-light-9, #ecf5ff);
}

.cmdk-item-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.cmdk-item-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary, #303133);
  display: flex;
  align-items: center;
  gap: 6px;
}

.cmdk-deceased {
  font-style: normal;
  font-size: 11px;
  color: #909399;
  background: var(--bg-color, #f5f7fa);
  border-radius: 4px;
  padding: 0 5px;
}

.cmdk-item-sub {
  font-size: 12px;
  color: var(--text-secondary, #909399);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.cmdk-item-icon {
  color: var(--text-placeholder, #b6b8bd);
  font-size: 16px;
}

.cmdk-action-icon {
  width: 32px;
  height: 32px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  color: var(--primary-color, #409eff);
  background: var(--primary-color-light-9, #ecf5ff);
  font-size: 16px;
}

.cmdk-path {
  font-size: 12px;
  color: var(--text-placeholder, #b6b8bd);
  font-family: ui-monospace, monospace;
}

.cmdk-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 36px 0;
  color: var(--text-secondary, #909399);
  font-size: 13px;
}

.cmdk-footer {
  display: flex;
  align-items: center;
  gap: 18px;
  padding: 10px 16px;
  border-top: 1px solid var(--border-lighter, #ebeef5);
  background: var(--bg-color-light, #fafbfc);
  font-size: 12px;
  color: var(--text-secondary, #909399);
}

.cmdk-footer kbd {
  font-family: inherit;
  font-size: 11px;
  background: var(--card-bg, #fff);
  border: 1px solid var(--border-color, #dcdfe6);
  border-radius: 4px;
  padding: 0 5px;
  margin: 0 2px;
}

.cmdk-fade-enter-active,
.cmdk-fade-leave-active {
  transition: opacity 0.16s ease;

  .cmdk-panel {
    transition: transform 0.16s ease, opacity 0.16s ease;
  }
}

.cmdk-fade-enter-from,
.cmdk-fade-leave-to {
  opacity: 0;

  .cmdk-panel {
    transform: translateY(-10px) scale(0.99);
    opacity: 0;
  }
}
</style>
