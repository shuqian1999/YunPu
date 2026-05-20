<template>
  <div class="settings-container">
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
    
    <el-card class="settings-card">
      <template #header>
        <span class="card-title">数据管理</span>
      </template>
      
      <div class="data-actions">
        <el-button type="primary" @click="handleExportData">
          <el-icon><Download /></el-icon>
          导出数据
        </el-button>
        <el-button @click="handleImportData">
          <el-icon><Upload /></el-icon>
          导入数据
        </el-button>
      </div>
    </el-card>
    
    <el-dialog v-model="dataDialogVisible" title="数据导入/导出" width="600px">
      <el-tabs v-model="dataDialogTab">
        <el-tab-pane label="导出数据" name="export">
          <div class="export-options">
            <el-radio-group v-model="exportFormat">
              <el-radio label="json">JSON 格式</el-radio>
              <el-radio label="csv">CSV 格式</el-radio>
            </el-radio-group>
          </div>
          
          <el-alert
            title="导出说明"
            type="info"
            :closable="false"
            show-icon
          >
            <ul>
              <li>JSON 格式：包含所有数据，适合完整备份</li>
              <li>CSV 格式：仅包含人物数据，适合Excel编辑</li>
            </ul>
          </el-alert>
        </el-tab-pane>
        
        <el-tab-pane label="导入数据" name="import">
          <el-upload
            drag
            :auto-upload="false"
            :on-change="handleFileChange"
            accept=".json"
            class="upload-area"
          >
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">
              拖拽文件到此处或 <em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                仅支持 JSON 格式文件
              </div>
            </template>
          </el-upload>
          
          <el-alert
            title="导入说明"
            type="warning"
            :closable="false"
            show-icon
          >
            <ul>
              <li>导入数据将添加到现有数据中</li>
              <li>建议先导出备份再导入</li>
            </ul>
          </el-alert>
        </el-tab-pane>
      </el-tabs>
      
      <template #footer>
        <el-button @click="dataDialogVisible = false">取消</el-button>
        <el-button
          v-if="dataDialogTab === 'export'"
          type="primary"
          :loading="exporting"
          @click="handleExport"
        >
          导出
        </el-button>
        <el-button
          v-if="dataDialogTab === 'import'"
          type="primary"
          :loading="importing"
          @click="handleImport"
        >
          导入
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Download, Upload, UploadFilled } from '@element-plus/icons-vue'
import { changePassword, getSystemSettings } from '@/api/settings'
import { exportDataJson, exportDataCsv, importDataJson } from '@/api/data'

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
  old_password: [
    { required: true, message: '请输入原密码', trigger: 'blur' }
  ],
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
const exportFormat = ref('json')
const exporting = ref(false)
const importing = ref(false)
const selectedFile = ref(null)

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

const handleExportData = () => {
  dataDialogVisible.value = true
}

const handleImportData = () => {
  dataDialogVisible.value = true
  dataDialogTab.value = 'import'
}

const handleFileChange = (file) => {
  selectedFile.value = file.raw
}

const handleExport = async () => {
  exporting.value = true
  try {
    let blob, filename
    if (exportFormat.value === 'json') {
      blob = await exportDataJson()
      filename = 'yunpu_data.json'
    } else {
      blob = await exportDataCsv()
      filename = 'yunpu_persons.csv'
    }
    
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    ElMessage.success('导出成功')
    dataDialogVisible.value = false
  } catch (error) {
    ElMessage.error('导出失败')
  } finally {
    exporting.value = false
  }
}

const handleImport = async () => {
  if (!selectedFile.value) {
    ElMessage.warning('请选择要导入的文件')
    return
  }
  
  importing.value = true
  try {
    const result = await importDataJson(selectedFile.value)
    ElMessage.success(result.message)
    dataDialogVisible.value = false
    loadSystemSettings()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '导入失败')
  } finally {
    importing.value = false
    selectedFile.value = null
  }
}

onMounted(() => {
  loadSystemSettings()
})
</script>

<style scoped lang="scss">
.settings-container {
  padding: 24px;
  max-width: 1000px;
  margin: 0 auto;
}

.settings-card {
  margin-bottom: 16px;
}

.card-title {
  font-size: 18px;
  font-weight: 500;
  color: #303133;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.stat-item {
  text-align: center;
  padding: 24px;
  background: var(--bg-color, #F5F7FA);
  border-radius: 8px;
}

.stat-value {
  font-size: 32px;
  font-weight: 600;
  color: #409EFF;
  line-height: 1.2;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 8px;
}

.data-actions {
  display: flex;
  gap: 12px;
}

.export-options {
  margin-bottom: 16px;
}

.upload-area {
  margin-bottom: 16px;
}
</style>
