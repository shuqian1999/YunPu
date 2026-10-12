<template>
  <div class="page-container-wide">
    <div class="page-header">
      <div class="page-header-left">
        <h2 class="page-title">仪表盘</h2>
        <span class="page-subtitle">最近事件和提醒一览</span>
      </div>
    </div>

    <PageSkeleton v-if="initialLoading" variant="dashboard" />

    <template v-else>
      <TodayFocus />

      <div class="dashboard-grid">
        <StatCard
          :value="stats.person_count"
          label="人物总数"
          :icon="User"
          icon-class="person-icon"
        />
        <StatCard
          :value="stats.event_count"
          label="事件总数"
          :icon="Document"
          icon-class="event-icon"
        />
        <StatCard
          :value="stats.reminder_count"
          label="提醒总数"
          :icon="Bell"
          icon-class="reminder-icon"
        />

        <EventsTimeline
          :events="filteredEvents"
          :show-filter-panel="showFilterPanel"
          :search-keyword="searchKeyword"
          :date-range="dateRange"
          :selected-types="selectedTypes"
          :selected-persons="selectedPersons"
          :available-types="availableTypes"
          :available-persons="availablePersons"
          :active-filter-count="activeFilterCount"
          @toggle-filter="showFilterPanel = !showFilterPanel"
          @clear-filters="clearFilters"
          @update:search-keyword="searchKeyword = $event"
          @update:date-range="dateRange = $event"
          @update:selected-types="selectedTypes = $event"
          @update:selected-persons="selectedPersons = $event"
        />

        <RemindersList :reminders="reminders" />
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { User, Document, Bell } from '@element-plus/icons-vue'
import { getDashboardStats, getDashboardEvents, getDashboardReminders } from '@/api/dashboard'
import StatCard from './components/StatCard.vue'
import TodayFocus from './components/TodayFocus.vue'
import EventsTimeline from './components/EventsTimeline.vue'
import RemindersList from './components/RemindersList.vue'
import PageSkeleton from '@/components/PageSkeleton.vue'

const initialLoading = ref(true)

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

const activeFilterCount = computed(() => {
  let count = 0
  if (searchKeyword.value.trim()) count++
  if (dateRange.value && dateRange.value.length === 2) count++
  if (selectedTypes.value.length > 0) count++
  if (selectedPersons.value.length > 0) count++
  return count
})

const clearFilters = () => {
  searchKeyword.value = ''
  dateRange.value = []
  selectedTypes.value = []
  selectedPersons.value = []
}

// 综合筛选（日期展示交给时间轴组件 timestamp 自行对齐）
const filteredEvents = computed(() => {
  const keyword = searchKeyword.value.trim().toLowerCase()
  const [startDate, endDate] = dateRange.value || []

  return events.value.filter(event => {
    if (keyword) {
      const title = (event.title || '').toLowerCase()
      const desc = (event.description || '').toLowerCase()
      if (!title.includes(keyword) && !desc.includes(keyword)) {
        return false
      }
    }

    if (startDate && endDate) {
      const eventDate = event.display_date || event.event_date
      if (eventDate < startDate || eventDate > endDate) {
        return false
      }
    }

    if (selectedTypes.value.length > 0) {
      const type = event.event_type || '其他'
      if (!selectedTypes.value.includes(type)) {
        return false
      }
    }

    if (selectedPersons.value.length > 0) {
      if (!event.person_id || !selectedPersons.value.includes(event.person_id)) {
        return false
      }
    }

    return true
  })
})

const loadDashboard = async () => {
  try {
    stats.value = await getDashboardStats()
    events.value = await getDashboardEvents({ limit: 10 })
    reminders.value = await getDashboardReminders({ days: 30 })
    clearFilters()
  } catch (error) {
    console.error('加载仪表盘失败:', error)
  } finally {
    initialLoading.value = false
  }
}

onMounted(() => {
  loadDashboard()
})
</script>

<style scoped>
.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

@media (max-width: 768px) {
  .dashboard-grid {
    grid-template-columns: 1fr;
    gap: 12px;
  }
  .dashboard-grid > * {
    grid-column: auto !important;
    grid-row: auto !important;
  }
}
</style>

<style lang="scss">
/* 深色模式：统计卡 */
.dashboard-grid {
  .stat-card {
    .el-card {
      background: var(--card-bg) !important;
      border-color: var(--border-color) !important;
      color: var(--text-primary) !important;
    }
    .el-card__body {
      background: var(--card-bg) !important;
      color: var(--text-primary) !important;
    }
  }
}
</style>
