<template>
  <el-card class="page-card events-card">
    <template #header>
      <div class="card-header">
        <span class="card-title">事件时间轴</span>
        <div class="card-actions">
          <el-button
            :type="showFilterPanel ? 'primary' : 'default'"
            size="small"
            @click="$emit('toggle-filter')"
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
            @click="$emit('clear-filters')"
          >
            清空
          </el-button>
        </div>
      </div>
    </template>

    <transition name="filter">
      <div v-show="showFilterPanel" class="filter-panel">
        <el-input
          :model-value="searchKeyword"
          @update:model-value="$emit('update:searchKeyword', $event)"
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
          :model-value="dateRange"
          @update:model-value="$emit('update:dateRange', $event)"
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
          :model-value="selectedTypes"
          @update:model-value="$emit('update:selectedTypes', $event)"
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
              <span class="type-color-dot" :style="{ backgroundColor: type.color }"></span>
              <span>{{ type.name }}</span>
              <span class="type-count">{{ type.count }}</span>
            </span>
          </el-option>
        </el-select>

        <el-select
          :model-value="selectedPersons"
          @update:model-value="$emit('update:selectedPersons', $event)"
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

    <el-timeline v-if="events.length > 0" class="events-timeline">
      <el-timeline-item
        v-for="event in events"
        :key="event.id"
        placement="top"
        :timestamp="formatDate(event.display_date || event.event_date)"
        :color="event.event_type_color || '#c0c4cc'"
      >
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
              class="event-type-tag"
            >
              {{ event.event_type }}
            </el-tag>
            <el-tag
              v-if="event.person_name"
              size="small"
              type="info"
              effect="plain"
              class="event-person-tag"
            >
              <el-icon><User /></el-icon>
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
</template>

<script setup>
import { Filter, Search, Location, User } from '@element-plus/icons-vue'

defineProps({
  events: { type: Array, required: true },
  showFilterPanel: { type: Boolean, default: false },
  searchKeyword: { type: String, default: '' },
  dateRange: { type: Array, default: () => [] },
  selectedTypes: { type: Array, default: () => [] },
  selectedPersons: { type: Array, default: () => [] },
  availableTypes: { type: Array, default: () => [] },
  availablePersons: { type: Array, default: () => [] },
  activeFilterCount: { type: Number, default: 0 }
})

defineEmits([
  'toggle-filter',
  'clear-filters',
  'update:searchKeyword',
  'update:dateRange',
  'update:selectedTypes',
  'update:selectedPersons'
])

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  })
}
</script>

<style scoped>
.events-card {
  grid-column: span 2;
}

.events-card :deep(.el-card) {
  background: var(--card-bg, #ffffff);
  border-color: var(--border-color, #dcdfe6);
  border-radius: 12px;
}

.events-card :deep(.el-card__body) {
  padding: 20px;
  background: var(--card-bg, #ffffff);
}

.events-card :deep(.el-card__header) {
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
  margin-bottom: 16px;
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
  padding: 4px 0;
}

.events-timeline :deep(.el-timeline-item__wrapper) {
  padding-left: 16px;
  top: -6px;
}

.events-timeline :deep(.el-timeline-item__timestamp) {
  color: var(--text-primary, #303133);
  font-weight: 500;
  font-size: 13px;
}

.events-timeline :deep(.el-timeline-item__node) {
  z-index: 2;
}

.event-item {
  padding: 12px 16px;
  background: var(--bg-color-page, #f7f8fa);
  border-radius: 8px;
  border-left: 3px solid var(--border-lighter, #EBEEF5);
  transition: all 0.2s ease;
}

.event-item:hover {
  background: var(--bg-color-hover, #eef0f3);
}

.event-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
  flex-wrap: wrap;
}

.event-title {
  font-size: 15px;
  font-weight: 500;
  color: var(--text-primary, #303133);
}

.event-type-tag {
  font-size: 11px;
  flex-shrink: 0;
}

.event-person-tag {
  font-size: 11px;
  flex-shrink: 0;
}

.event-person-tag .el-icon {
  margin-right: 2px;
  font-size: 11px;
}

.event-description {
  font-size: 13px;
  color: var(--text-regular, #606266);
  line-height: 1.6;
  margin-top: 4px;
}

.event-location {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--text-secondary, #909399);
  margin-top: 4px;
}
</style>

<style lang="scss">
/* 深色模式 */
.events-card {
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
