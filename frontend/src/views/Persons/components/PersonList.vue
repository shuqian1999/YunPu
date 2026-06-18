<template>
  <el-card class="page-card list-card" shadow="never">
    <el-table
      :data="persons"
      stripe
      style="width: 100%"
      row-class-name="person-row"
      :empty-text="loading ? '' : '暂无人物'"
      @row-click="(row) => $emit('view', row.id)"
    >
      <el-table-column type="index" label="#" width="60" align="center" />

      <el-table-column label="姓名" min-width="150">
        <template #default="{ row }">
          <div class="list-name-cell">
            <el-avatar :size="32" :src="row.avatar_url">
              {{ row.first_name || row.nickname || '?' }}
            </el-avatar>
            <div class="list-name-text">
              <span class="list-name">{{ row.last_name }}{{ row.first_name }}</span>
              <span v-if="row.nickname" class="list-nickname">（{{ row.nickname }}）</span>
              <el-tag v-if="row.is_me" type="primary" size="small" class="list-me-tag">我</el-tag>
            </div>
          </div>
        </template>
      </el-table-column>

      <el-table-column label="性别" width="80" align="center">
        <template #default="{ row }">
          <el-tag v-if="row.gender === 1" type="success" size="small">男</el-tag>
          <el-tag v-else-if="row.gender === 2" type="danger" size="small">女</el-tag>
          <span v-else class="muted">—</span>
        </template>
      </el-table-column>

      <el-table-column label="年龄" width="160" align="center">
        <template #default="{ row }">
          <span v-if="getPersonAgeText(row)" class="age-text">{{ getPersonAgeText(row) }}</span>
          <span v-else class="muted">—</span>
        </template>
      </el-table-column>

      <el-table-column label="生日" width="160">
        <template #default="{ row }">
          <span v-if="row.birth_date" class="date-text">{{ formatBirthday(row.birth_date) }}</span>
          <span v-else class="muted">—</span>
          <el-tag v-if="row.is_lunar_birth" size="small" type="warning" class="lunar-tag">农历</el-tag>
        </template>
      </el-table-column>

      <el-table-column label="忌日" width="160">
        <template #default="{ row }">
          <span v-if="row.death_date" class="date-text">{{ formatBirthday(row.death_date) }}</span>
          <span v-else class="muted">—</span>
          <el-tag v-if="row.is_lunar_death" size="small" type="warning" class="lunar-tag">农历</el-tag>
        </template>
      </el-table-column>

      <el-table-column label="位置" min-width="180">
        <template #default="{ row }">
          <span class="location-cell">
            <span v-if="getCountryFlag(row.country)" class="location-flag">{{ getCountryFlag(row.country) }}</span>
            <span v-if="getCountryName(row.country)">{{ getCountryName(row.country) }}</span>
            <span v-if="getCountryName(row.country) && row.residence" class="location-sep">·</span>
            <el-icon v-if="row.residence" class="location-icon"><Location /></el-icon>
            <span v-if="row.residence">{{ row.residence }}</span>
            <span v-if="!getCountryName(row.country) && !row.residence" class="muted">—</span>
          </span>
        </template>
      </el-table-column>

      <el-table-column label="家乡" min-width="140">
        <template #default="{ row }">
          <span v-if="row.hometown && row.hometown !== row.residence">
            <el-icon><HomeFilled /></el-icon>
            {{ row.hometown }}
          </span>
          <span v-else class="muted">—</span>
        </template>
      </el-table-column>

      <el-table-column label="操作" width="100" align="center" fixed="right">
        <template #default="{ row }">
          <el-button
            v-if="!row.is_me"
            type="danger"
            text
            size="small"
            @click.stop="$emit('delete', row.id)"
          >
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </el-card>
</template>

<script setup>
import { Location, HomeFilled } from '@element-plus/icons-vue'

defineProps({
  persons: { type: Array, required: true },
  loading: { type: Boolean, default: false },
  getCountryName: { type: Function, required: true },
  getCountryFlag: { type: Function, required: true },
  getPersonAgeText: { type: Function, required: true },
  formatBirthday: { type: Function, required: true }
})

defineEmits(['view', 'delete'])
</script>

<style scoped>
.list-card {
  margin-bottom: 16px;
}

.list-card :deep(.el-card__body) {
  padding: 0;
}

:deep(.person-row) {
  cursor: pointer;
}

:deep(.person-row):hover {
  background-color: var(--bg-color-light, #F5F7FA) !important;
}

.list-name-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}

.list-name-text {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.list-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary, #303133);
}

.list-nickname {
  font-size: 12px;
  color: var(--text-secondary, #909399);
}

.list-me-tag {
  font-size: 10px;
  height: 18px;
  padding: 0 6px;
  line-height: 18px;
}

.age-text {
  color: var(--el-color-primary, #409eff);
  font-weight: 500;
  font-size: 13px;
}

.date-text {
  font-weight: 500;
  color: var(--text-primary, #303133);
}

.muted {
  color: var(--text-secondary, #c0c4cc);
}

.location-cell {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: var(--text-regular, #606266);
}

.lunar-tag {
  margin-left: 4px;
  font-size: 10px;
  height: 16px;
  padding: 0 4px;
  line-height: 16px;
}

.location-flag {
  font-size: 14px;
  line-height: 1;
}

.location-icon {
  font-size: 12px;
  color: var(--text-secondary, #909399);
}

.location-sep {
  color: var(--text-secondary, #c0c4cc);
  margin: 0 2px;
}
</style>
