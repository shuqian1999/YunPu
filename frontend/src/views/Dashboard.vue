<template>
  <div class="dashboard-container">
    <div class="dashboard-grid">
      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon person-icon">
            <el-icon><User /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.person_count }}</div>
            <div class="stat-label">人物总数</div>
          </div>
        </div>
      </el-card>

      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon event-icon">
            <el-icon><Document /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.event_count }}</div>
            <div class="stat-label">事件总数</div>
          </div>
        </div>
      </el-card>

      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon reminder-icon">
            <el-icon><Bell /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.reminder_count }}</div>
            <div class="stat-label">提醒总数</div>
          </div>
        </div>
      </el-card>

      <el-card class="events-card">
        <template #header>
          <div class="card-header">
            <span class="card-title">事件时间轴</span>
            <div class="card-actions">
              <el-button
                :type="showFilterPanel ? 'primary' : 'default'"
                size="small"
                @click="showFilterPanel = !showFilterPanel"
              >
                <el-icon><Filter /></el-icon>
                筛选
                <el-badge
                  v-if="activeFilterCount > 0"
                  :value="activeFilterCount"
                  class="filter-badge"
                />
              </el-button>
              <el-button
                v-if="activeFilterCount > 0"
                size="small"
                text
                @click="clearFilters"
              >
                清空
              </el-button>
            </div>
          </div>
        </template>

        <transition name="filter">
          <div v-show="showFilterPanel" class="filter-panel">
            <el-input
              v-model="searchKeyword"
              placeholder="搜索标题或描述"
              clearable
              size="small"
              class="filter-item filter-search"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>

            <el-date-picker
              v-model="dateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              value-format="YYYY-MM-DD"
              size="small"
              class="filter-item filter-date"
              unlink-panels
            />

            <el-select
              v-model="selectedTypes"
              multiple
              collapse-tags
              collapse-tags-tooltip
              clearable
              placeholder="全部类型"
              size="small"
              class="filter-item filter-type"
            >
              <el-option
                v-for="type in availableTypes"
                :key="type.name"
                :label="type.name"
                :value="type.name"
              >
                <span class="type-option">
                  <span
                    class="type-color-dot"
                    :style="{ backgroundColor: type.color }"
                  ></span>
                  <span>{{ type.name }}</span>
                  <span class="type-count">{{ type.count }}</span>
                </span>
              </el-option>
            </el-select>

            <el-select
              v-model="selectedPersons"
              multiple
              collapse-tags
              collapse-tags-tooltip
              clearable
              filterable
              placeholder="全部人物"
              size="small"
              class="filter-item filter-person"
            >
              <el-option
                v-for="person in availablePersons"
                :key="person.id"
                :label="person.name"
                :value="person.id"
              >
                <span class="type-option">
                  <span>{{ person.name }}</span>
                  <span class="type-count">{{ person.count }}</span>
                </span>
              </el-option>
            </el-select>
          </div>
        </transition>

        <el-timeline v-if="eventGroups.length > 0" class="events-timeline">
          <el-timeline-item
            v-for="event in eventGroups"
            :key="event.id"
            placement="top"
            :color="event.event_type_color"
            :hollow="event.showDate"
          >
            <div
              v-if="event.showDate"
              class="event-date-badge"
              :style="{ borderColor: event.event_type_color, color: event.event_type_color }"
            >
              {{ formatDate(event.dateKey) }}
            </div>
            <div class="event-item">
              <div class="event-header">
                <span class="event-title">{{ event.title }}</span>
                <el-tag
                  v-if="event.event_type"
                  size="small"
                  effect="dark"
                  :style="{
                    backgroundColor: event.event_type_color,
                    borderColor: event.event_type_color,
                    color: '#fff'
                  }"
                >
                  {{ event.event_type }}
                </el-tag>
                <el-tag
                  v-if="event.person_name"
                  size="small"
                  type="info"
                >
                  {{ event.person_name }}
                </el-tag>
              </div>
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
        <el-empty
          v-else
          :description="activeFilterCount > 0 ? '没有符合筛选条件的事件' : '暂无事件'"
        />
      </el-card>

      <el-card class="reminders-card">
        <template #header>
          <div class="card-header">
            <span class="card-title">最近30天提醒</span>
          </div>
        </template>

        <div v-if="reminders.length > 0" class="reminders-list">
          <div
            v-for="reminder in reminders"
            :key="reminder.id"
            class="reminder-item"
          >
            <div class="reminder-date">
              {{ formatDate(reminder.display_date || reminder.remind_date) }}
            </div>
            <div class="reminder-content">
              <div class="reminder-title">{{ reminder.title }}</div>
              <div v-if="reminder.person_name" class="reminder-person">
                {{ reminder.person_name }}
              </div>
            </div>
          </div>
        </div>
        <el-empty v-else description="暂无提醒" />
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { User, Document, Bell, Location, Filter, Search } from '@element-plus/icons-vue'
import { getDashboardStats, getDashboardEvents, getDashboardReminders } from '@/api/dashboard'

const stats = ref({
  person_count: 0,
  event_count: 0,
  reminder_count: 0
})
const events = ref([])
const reminders = ref([])

// 筛选条件
const showFilterPanel = ref(false)
const searchKeyword = ref('')
const dateRange = ref([])
const selectedTypes = ref([])
const selectedPersons = ref([])

const formatDate = (dateStr) => {
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  })
}

// 从事件中提取所有类型及数量
const availableTypes = computed(() => {
  const typeMap = new Map()
  for (const event of events.value) {
    const name = event.event_type || '其他'
    const color = event.event_type_color || '#c0c4cc'
    if (!typeMap.has(name)) {
      typeMap.set(name, { name, color, count: 0 })
    }
    typeMap.get(name).count++
  }
  return Array.from(typeMap.values()).sort((a, b) => b.count - a.count)
})

// 从事件中提取所有人物及数量
const availablePersons = computed(() => {
  const personMap = new Map()
  for (const event of events.value) {
    if (event.person_id && event.person_name) {
      if (!personMap.has(event.person_id)) {
        personMap.set(event.person_id, {
          id: event.person_id,
          name: event.person_name,
          count: 0
        })
      }
      personMap.get(event.person_id).count++
    }
  }
  return Array.from(personMap.values()).sort((a, b) => b.count - a.count)
})

// 活跃的筛选条件数量（用于角标）
const activeFilterCount = computed(() => {
  let count = 0
  if (searchKeyword.value.trim()) count++
  if (dateRange.value && dateRange.value.length === 2) count++
  if (selectedTypes.value.length > 0) count++
  if (selectedPersons.value.length > 0) count++
  return count
})

// 清空所有筛选
const clearFilters = () => {
  searchKeyword.value = ''
  dateRange.value = []
  selectedTypes.value = []
  selectedPersons.value = []
}

// 综合筛选 + 按同一天合并日期
const eventGroups = computed(() => {
  const keyword = searchKeyword.value.trim().toLowerCase()
  const [startDate, endDate] = dateRange.value || []

  const filtered = events.value.filter(event => {
    // 关键词搜索
    if (keyword) {
      const title = (event.title || '').toLowerCase()
      const desc = (event.description || '').toLowerCase()
      if (!title.includes(keyword) && !desc.includes(keyword)) {
        return false
      }
    }

    // 日期范围（基于 display_date，即转换后的公历日期）
    if (startDate && endDate) {
      const eventDate = event.display_date || event.event_date
      if (eventDate < startDate || eventDate > endDate) {
        return false
      }
    }

    // 类型筛选
    if (selectedTypes.value.length > 0) {
      const type = event.event_type || '其他'
      if (!selectedTypes.value.includes(type)) {
        return false
      }
    }

    // 人物筛选
    if (selectedPersons.value.length > 0) {
      if (!event.person_id || !selectedPersons.value.includes(event.person_id)) {
        return false
      }
    }

    return true
  })

  const seenDates = new Set()
  return filtered.map(event => {
    const dateKey = event.display_date || event.event_date
    const showDate = !seenDates.has(dateKey)
    seenDates.add(dateKey)
    return { ...event, dateKey, showDate }
  })
})

const loadDashboard = async () => {
  try {
    stats.value = await getDashboardStats()
    events.value = await getDashboardEvents({ limit: 10 })
    reminders.value = await getDashboardReminders({ days: 30 })
    // 数据变化时重置筛选
    clearFilters()
  } catch (error) {
    console.error('加载仪表盘失败:', error)
  }
}

onMounted(() => {
  loadDashboard()
})
</script>

<style scoped lang="scss">
.dashboard-container {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
  box-sizing: border-box;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.stat-card {
  display: flex;
  align-items: stretch;

  :deep(.el-card) {
    background: var(--card-bg, #ffffff);
    border-color: var(--border-color, #dcdfe6);
  }

  :deep(.el-card__body) {
    padding: 24px;
    width: 100%;
    background: var(--card-bg, #ffffff);
  }
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
  height: 100%;
}

.stat-icon {
  flex-shrink: 0;
  width: 56px;
  height: 56px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;

  &.person-icon {
    background: rgba(64, 158, 255, 0.1);
    color: var(--primary-color, #409EFF);
  }

  &.event-icon {
    background: rgba(64, 158, 255, 0.1);
    color: var(--primary-color, #409EFF);
  }

  &.reminder-icon {
    background: rgba(64, 158, 255, 0.1);
    color: #409EFF;
  }
}

.stat-info {
  flex: 1;
  min-width: 0;
}

.stat-value {
  font-size: 32px;
  font-weight: 600;
  color: var(--text-primary, #303133);
  line-height: 1.2;
}

.stat-label {
  font-size: 14px;
  color: var(--text-secondary, #909399);
  margin-top: 4px;
}

.events-card {
  grid-column: span 2;

  :deep(.el-card) {
    background: var(--card-bg, #ffffff);
    border-color: var(--border-color, #dcdfe6);
  }

  :deep(.el-card__body) {
    padding: 20px;
    background: var(--card-bg, #ffffff);
  }

  :deep(.el-card__header) {
    padding: 16px 20px;
    border-bottom: 1px solid var(--border-lighter, #EBEEF5);
    background: var(--card-bg, #ffffff);
  }
}

.reminders-card {
  :deep(.el-card) {
    background: var(--card-bg, #ffffff);
    border-color: var(--border-color, #dcdfe6);
  }

  :deep(.el-card__body) {
    padding: 20px;
    background: var(--card-bg, #ffffff);
  }

  :deep(.el-card__header) {
    padding: 16px 20px;
    border-bottom: 1px solid var(--border-lighter, #EBEEF5);
    background: var(--card-bg, #ffffff);
  }
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.card-title {
  font-size: 18px;
  font-weight: 500;
  color: var(--text-primary, #303133);
}

.card-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}

.filter-badge {
  margin-left: 4px;
}

.filter-panel {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr 1fr;
  gap: 12px;
  padding: 16px;
  margin-bottom: 8px;
  background: var(--bg-color-page, #f7f8fa);
  border-radius: 8px;
  border: 1px solid var(--border-lighter, #EBEEF5);
}

.filter-item {
  width: 100%;
}

.filter-search :deep(.el-input__wrapper) {
  background: var(--card-bg, #ffffff);
}

.filter-enter-active,
.filter-leave-active {
  transition: all 0.25s ease;
  overflow: hidden;
}

.filter-enter-from,
.filter-leave-to {
  opacity: 0;
  max-height: 0;
  padding-top: 0;
  padding-bottom: 0;
  margin-bottom: 0;
}

.filter-enter-to,
.filter-leave-from {
  opacity: 1;
  max-height: 200px;
}

.type-option {
  display: flex;
  align-items: center;
  gap: 8px;
}

.type-color-dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.type-count {
  margin-left: auto;
  color: var(--text-secondary, #909399);
  font-size: 12px;
}

@media (max-width: 900px) {
  .filter-panel {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 600px) {
  .filter-panel {
    grid-template-columns: 1fr;
  }
}

.events-timeline {
  padding: 8px 0;

  :deep(.el-timeline-item) {
    padding-bottom: 20px;

    &:last-child {
      padding-bottom: 0;
    }
  }

  :deep(.el-timeline-item__node) {
    z-index: 2;
  }
}

.event-date-badge {
  display: inline-flex;
  align-items: center;
  padding: 6px 14px;
  margin-bottom: 12px;
  font-size: 15px;
  font-weight: 600;
  border: 2px solid;
  border-radius: 16px;
  background: var(--card-bg, #ffffff);
  letter-spacing: 0.5px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06);
}

.event-item {
  padding: 14px 16px;
  margin-bottom: 4px;
  background: var(--bg-color-page, #f7f8fa);
  border-radius: 8px;
  border-left: 3px solid var(--border-lighter, #EBEEF5);
  transition: all 0.2s ease;

  &:hover {
    background: var(--bg-color-hover, #eef0f3);
  }
}

.event-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}

.event-title {
  font-size: 16px;
  font-weight: 500;
  color: var(--text-primary, #303133);
}

.event-description {
  font-size: 14px;
  color: var(--text-regular, #606266);
  margin-bottom: 4px;
  line-height: 1.6;
  padding-left: 24px;
}

.event-location {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: var(--text-secondary, #909399);
  padding-left: 24px;
}

.reminders-list {
  max-height: 480px;
  overflow-y: auto;
}

.reminder-item {
  padding: 16px 0;
  border-bottom: 1px solid var(--border-lighter, #EBEEF5);

  &:last-child {
    border-bottom: none;
  }
}

.reminder-date {
  font-size: 14px;
  color: var(--primary-color, #409EFF);
  font-weight: 500;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.reminder-content {
  padding-left: 12px;
}

.reminder-title {
  font-size: 14px;
  color: var(--text-primary, #303133);
  margin-bottom: 4px;
}

.reminder-person {
  font-size: 12px;
  color: var(--text-secondary, #909399);
}
</style>

<!-- 深色模式覆盖样式 -->
<style lang="scss">
.dashboard-container {
  .stat-card, .events-card, .reminders-card {
    .el-card {
      background: var(--card-bg) !important;
      border-color: var(--border-color) !important;
      color: var(--text-primary) !important;
    }

    .el-card__body {
      background: var(--card-bg) !important;
      color: var(--text-primary) !important;
    }

    .el-card__header {
      background: var(--card-bg) !important;
      border-bottom-color: var(--border-color) !important;
      color: var(--text-primary) !important;
    }
  }
}
</style>