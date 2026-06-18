<template>
  <div class="group-card-wrap">
    <el-card class="page-card group-card" shadow="never">
      <div class="group-header">
        <div class="group-info">
          <el-tag :color="group.color" effect="dark" class="group-color-tag">
            {{ group.name }}
          </el-tag>
          <span v-if="group.description" class="group-description">
            {{ group.description }}
          </span>
        </div>
        <div class="group-actions">
          <el-button type="primary" text size="small" @click="$emit('edit', group)">
            <el-icon><Edit /></el-icon>
          </el-button>
          <el-button type="danger" text size="small" @click="$emit('delete', group.id)">
            <el-icon><Delete /></el-icon>
          </el-button>
        </div>
      </div>

      <div class="group-members">
        <div class="members-header">
          <span class="members-title">成员列表</span>
          <el-button type="primary" link size="small" @click="$emit('add-member', group.id)">
            <el-icon><Plus /></el-icon>
            添加成员
          </el-button>
        </div>

        <div v-if="members.length > 0" class="members-list">
          <el-tag
            v-for="member in members"
            :key="member.id"
            closable
            class="member-tag"
            @close="$emit('remove-member', group.id, member.person_id)"
          >
            {{ member.person_name }}
          </el-tag>
        </div>
        <el-empty v-else description="暂无成员" :image-size="60" />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { Edit, Delete, Plus } from '@element-plus/icons-vue'

defineProps({
  group: { type: Object, required: true },
  members: { type: Array, default: () => [] }
})

defineEmits(['edit', 'delete', 'add-member', 'remove-member'])
</script>

<style scoped>
.group-card {
  margin-bottom: 0;
  border-radius: 12px;
}

.group-card :deep(.el-card__body) {
  padding: 20px;
}

.group-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-lighter, #EBEEF5);
}

.group-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.group-color-tag {
  font-size: 14px;
  padding: 6px 12px;
}

.group-description {
  color: var(--text-secondary, #909399);
  font-size: 14px;
}

.group-actions {
  display: flex;
  gap: 8px;
}

.members-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.members-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-regular, #606266);
}

.members-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.member-tag {
  margin-right: 0;
}
</style>
