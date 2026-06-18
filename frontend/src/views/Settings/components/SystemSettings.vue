<template>
  <div>
    <!-- 数据统计 -->
    <el-card class="settings-card">
      <template #header>
        <span class="card-title">数据统计</span>
      </template>

      <div class="stats-grid">
        <div class="stat-item">
          <div class="stat-value">{{ systemStats.person_count }}</div>
          <div class="stat-label">人物总数</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">{{ systemStats.event_count }}</div>
          <div class="stat-label">事件总数</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">{{ systemStats.reminder_count }}</div>
          <div class="stat-label">提醒总数</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">{{ systemStats.database_size }}</div>
          <div class="stat-label">数据库大小</div>
        </div>
      </div>
    </el-card>

    <!-- 修改密码 -->
    <el-card class="settings-card">
      <template #header>
        <span class="card-title">修改密码</span>
      </template>

      <el-form
        ref="passwordFormRef"
        :model="passwordForm"
        :rules="passwordRules"
        label-width="120px"
      >
        <el-form-item label="原密码" prop="old_password">
          <el-input
            v-model="passwordForm.old_password"
            type="password"
            show-password
            placeholder="请输入原密码"
          />
        </el-form-item>

        <el-form-item label="新密码" prop="new_password">
          <el-input
            v-model="passwordForm.new_password"
            type="password"
            show-password
            placeholder="请输入新密码"
          />
        </el-form-item>

        <el-form-item label="确认密码" prop="confirm_password">
          <el-input
            v-model="passwordForm.confirm_password"
            type="password"
            show-password
            placeholder="请再次输入新密码"
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="changingPassword" @click="handleChangePassword">
            修改密码
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 数据管理 -->
    <el-card class="settings-card">
      <template #header>
        <span class="card-title">数据管理</span>
      </template>

      <div class="data-actions">
        <el-button type="primary" @click="openDataDialog('export')">
          <el-icon><Download /></el-icon>
          导出数据
        </el-button>
        <el-button @click="openDataDialog('import')">
          <el-icon><Upload /></el-icon>
          导入数据
        </el-button>
      </div>
    </el-card>

    <DataDialog
      v-model:visible="dataDialogVisible"
      :default-tab="dataDialogTab"
      @completed="onDataCompleted"
    />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Download, Upload } from '@element-plus/icons-vue'
import { changePassword, getSystemSettings } from '@/api/settings'
import DataDialog from './DataDialog.vue'

const changingPassword = ref(false)
const passwordFormRef = ref(null)
const passwordForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: ''
})
const systemStats = ref({
  person_count: 0,
  event_count: 0,
  reminder_count: 0,
  database_size: '0 MB'
})
const passwordRules = {
  old_password: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 8, message: '密码长度不能少于8位', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== passwordForm.new_password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

const dataDialogVisible = ref(false)
const dataDialogTab = ref('export')

const openDataDialog = (tab) => {
  dataDialogTab.value = tab
  dataDialogVisible.value = true
}

const onDataCompleted = () => {
  loadSystemSettings()
}

const loadSystemSettings = async () => {
  try {
    systemStats.value = await getSystemSettings()
  } catch (error) {
    ElMessage.error('加载系统设置失败')
  }
}

const handleChangePassword = async () => {
  const valid = await passwordFormRef.value.validate()
  if (!valid) return
  changingPassword.value = true
  try {
    await changePassword(passwordForm.old_password, passwordForm.new_password)
    ElMessage.success('密码修改成功')
    passwordFormRef.value.resetFields()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '密码修改失败')
  } finally {
    changingPassword.value = false
  }
}

onMounted(() => {
  loadSystemSettings()
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

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.stat-item {
  text-align: center;
  padding: 24px;
  background: var(--bg-color-light, #F5F7FA);
  border-radius: 8px;
}

.stat-value {
  font-size: 32px;
  font-weight: 600;
  color: var(--primary-color, #409EFF);
  line-height: 1.2;
}

.stat-label {
  font-size: 14px;
  color: var(--text-secondary, #909399);
  margin-top: 8px;
}

.data-actions {
  display: flex;
  gap: 12px;
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
