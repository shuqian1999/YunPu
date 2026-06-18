<template>
  <el-card class="settings-card">
    <template #header>
      <div class="card-header-flex">
        <span class="card-title">发送日志</span>
        <el-button text type="danger" size="small" @click="handleClearLogs">清空日志</el-button>
      </div>
    </template>

    <el-table :data="emailLogs" stripe>
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag v-if="row.status === 'success'" type="success" size="small">成功</el-tag>
          <el-tag v-else type="danger" size="small">失败</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="subject" label="主题" min-width="200" show-overflow-tooltip />
      <el-table-column prop="receivers" label="接收方" min-width="180" show-overflow-tooltip />
      <el-table-column prop="related_count" label="数量" width="80" align="center" />
      <el-table-column label="时间" width="180">
        <template #default="{ row }">
          {{ formatDateTime(row.created_at) }}
        </template>
      </el-table-column>
      <template #empty>
        <el-empty description="暂无日志" />
      </template>
    </el-table>
  </el-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { listEmailLogs, clearEmailLogs } from '@/api/email'

const emailLogs = ref([])

const formatDateTime = (str) => {
  if (!str) return '-'
  return new Date(str).toLocaleString('zh-CN', { hour12: false })
}

const loadLogs = async () => {
  try {
    emailLogs.value = await listEmailLogs(50)
  } catch (e) {
    console.error('加载日志失败:', e)
  }
}

const handleClearLogs = async () => {
  try {
    await ElMessageBox.confirm('确定要清空所有发送日志吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await clearEmailLogs()
    ElMessage.success('已清空')
    await loadLogs()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('清空失败')
    }
  }
}

onMounted(() => {
  loadLogs()
})
</script>

<style scoped>
.settings-card {
  margin-bottom: 20px;
  background: var(--card-bg, #ffffff);
  border: 1px solid var(--border-color, #dcdfe6);
  border-radius: 12px;
}

.card-title {
  font-size: 18px;
  font-weight: 500;
  color: var(--text-primary, #303133);
}

.card-header-flex {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}
</style>
