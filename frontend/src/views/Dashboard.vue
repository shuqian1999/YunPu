<template>
  <div class="dashboard-container">
    <div class="stats-row">
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
    </div>
    
    <div class="content-row">
      <el-card class="events-card">
        <template #header>
          <div class="card-header">
            <span class="card-title">事件时间轴</span>
          </div>
        </template>
        
        <el-timeline v-if="events.length > 0" class="events-timeline">
          <el-timeline-item
            v-for="event in events"
            :key="event.id"
            :timestamp="formatDate(event.event_date)"
            placement="top"
            :color="event.event_type_color"
          >
            <div class="event-item">
              <div class="event-header">
                <span class="event-title">{{ event.title }}</span>
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
        <el-empty v-else description="暂无事件" />
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
              {{ formatDate(reminder.remind_date) }}
              <el-tag v-if="reminder.is_lunar" size="small" type="warning">农历</el-tag>
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
import { ref, onMounted } from 'vue'
import { User, Document, Bell, Location } from '@element-plus/icons-vue'
import { getDashboardStats, getDashboardEvents, getDashboardReminders } from '@/api/dashboard'

const stats = ref({
  person_count: 0,
  event_count: 0,
  reminder_count: 0
})
const events = ref([])
const reminders = ref([])

const formatDate = (dateStr) => {
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  })
}

const loadDashboard = async () => {
  try {
    stats.value = await getDashboardStats()
    events.value = await getDashboardEvents({ limit: 10 })
    reminders.value = await getDashboardReminders({ days: 30 })
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
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  :deep(.el-card__body) {
    padding: 24px;
  }
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  
  &.person-icon {
    background: #E1F3FF;
    color: #409EFF;
  }
  
  &.event-icon {
    background: #E1F3FF;
    color: #409EFF;
  }
  
  &.reminder-icon {
    background: #E1F3FF;
    color: #409EFF;
  }
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 32px;
  font-weight: 600;
  color: #303133;
  line-height: 1.2;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}

.content-row {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-size: 18px;
  font-weight: 500;
  color: #303133;
}

.events-timeline {
  padding: 8px 0;
}

.event-item {
  padding: 8px 0;
}

.event-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.event-title {
  font-size: 16px;
  font-weight: 500;
  color: #303133;
}

.event-description {
  font-size: 14px;
  color: #606266;
  margin-bottom: 4px;
  line-height: 1.6;
}

.event-location {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: #909399;
}

.reminders-list {
  max-height: 500px;
  overflow-y: auto;
}

.reminder-item {
  padding: 12px 0;
  border-bottom: 1px solid #E4E7ED;
  
  &:last-child {
    border-bottom: none;
  }
}

.reminder-date {
  font-size: 14px;
  color: #409EFF;
  font-weight: 500;
  margin-bottom: 4px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.reminder-content {
  padding-left: 12px;
}

.reminder-title {
  font-size: 14px;
  color: #303133;
  margin-bottom: 2px;
}

.reminder-person {
  font-size: 12px;
  color: #909399;
}
</style>