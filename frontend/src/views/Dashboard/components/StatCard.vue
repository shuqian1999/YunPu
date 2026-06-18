<template>
  <el-card class="page-card stat-card">
    <div class="stat-content">
      <div class="stat-icon" :class="iconClass">
        <el-icon><component :is="icon" /></el-icon>
      </div>
      <div class="stat-info">
        <div class="stat-value">{{ value }}</div>
        <div class="stat-label">{{ label }}</div>
      </div>
    </div>
  </el-card>
</template>

<script setup>
defineProps({
  value: { type: [Number, String], required: true },
  label: { type: String, required: true },
  icon: { type: [Object, Function], required: true },
  iconClass: { type: String, default: 'person-icon' }
})
</script>

<style scoped>
.stat-card {
  display: flex;
  align-items: stretch;
}

.stat-card :deep(.el-card) {
  background: var(--card-bg, #ffffff);
  border-color: var(--border-color, #dcdfe6);
  border-radius: 12px;
}

.stat-card :deep(.el-card__body) {
  padding: 24px;
  width: 100%;
  background: var(--card-bg, #ffffff);
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
}

.stat-icon.person-icon {
  background: rgba(64, 158, 255, 0.1);
  color: var(--primary-color, #409EFF);
}

.stat-icon.event-icon {
  background: rgba(64, 158, 255, 0.1);
  color: var(--primary-color, #409EFF);
}

.stat-icon.reminder-icon {
  background: rgba(64, 158, 255, 0.1);
  color: #409EFF;
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
</style>
