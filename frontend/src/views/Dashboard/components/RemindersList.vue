<template>
  <el-card class="page-card reminders-card">
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
        <div class="reminder-top-row">
          <el-tag
            v-if="reminder.event_type"
            size="small"
            effect="dark"
            :style="{
              backgroundColor: reminder.event_type_color || '#c0c4cc',
              borderColor: reminder.event_type_color || '#c0c4cc',
              color: '#fff'
            }"
            class="reminder-type-tag"
          >
            {{ reminder.event_type }}
          </el-tag>
          <el-tag
            v-if="reminder.repeat_type && reminder.repeat_type !== 'once'"
            size="small"
            type="info"
            effect="plain"
          >
            {{ repeatTypeLabel(reminder.repeat_type) }}
          </el-tag>
          <el-tag v-if="reminder.is_lunar" size="small" type="warning">农历</el-tag>
          <div class="reminder-date">
            <el-icon><Calendar /></el-icon>
            {{ formatDate(reminder.display_date || reminder.remind_date) }}
          </div>
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
</template>

<script setup>
import { Calendar } from '@element-plus/icons-vue'

defineProps({
  reminders: { type: Array, required: true }
})

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  })
}

const repeatTypeLabel = (type) => {
  const map = { once: '不重复', yearly: '每年', monthly: '每月', weekly: '每周' }
  return map[type] || ''
}
</script>

<style scoped>
.reminders-card :deep(.el-card) {
  background: var(--card-bg, #ffffff);
  border-color: var(--border-color, #dcdfe6);
  border-radius: 12px;
}

.reminders-card :deep(.el-card__body) {
  padding: 20px;
  background: var(--card-bg, #ffffff);
}

.reminders-card :deep(.el-card__header) {
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-lighter, #EBEEF5);
  background: var(--card-bg, #ffffff);
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

.reminders-list {
  max-height: 480px;
  overflow-y: auto;
}

.reminder-item {
  padding: 16px 0;
  border-bottom: 1px solid var(--border-lighter, #EBEEF5);
}

.reminder-item:last-child {
  border-bottom: none;
}

.reminder-top-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 8px;
}

.reminder-type-tag {
  font-size: 11px;
  flex-shrink: 0;
}

.reminder-date {
  margin-left: auto;
  font-size: 13px;
  color: var(--primary-color, #409EFF);
  font-weight: 500;
  display: inline-flex;
  align-items: center;
  gap: 4px;
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

<style lang="scss">
/* 深色模式覆盖 */
.reminders-card {
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
</style>
