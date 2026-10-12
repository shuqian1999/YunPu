<template>
  <el-card class="contacts-card">
    <template #header>
      <div class="card-header">
        <span class="card-title">交往记录</span>
        <el-button @click="openDialog()" type="primary" size="small">
          <el-icon><Plus /></el-icon>
          记录一次联系
        </el-button>
      </div>
    </template>

    <div v-if="records.length === 0" class="empty">
      暂无交往记录，记录一次见面或通话，让关系不断线
    </div>

    <el-timeline v-else class="record-list">
      <el-timeline-item
        v-for="record in records"
        :key="record.id"
        placement="top"
        :timestamp="formatDate(record.contact_date)"
        :color="typeMeta(record.contact_type).color"
      >
        <div class="record-item">
          <div class="record-header">
            <el-tag
              size="small"
              effect="dark"
              :style="{
                backgroundColor: typeMeta(record.contact_type).color,
                borderColor: typeMeta(record.contact_type).color,
                color: '#fff'
              }"
            >
              {{ typeMeta(record.contact_type).label }}
            </el-tag>
            <div class="record-actions">
              <el-button @click="openDialog(record)" text type="primary" size="small">
                <el-icon><Edit /></el-icon>
              </el-button>
              <el-button @click="handleDelete(record.id)" text type="danger" size="small">
                <el-icon><Delete /></el-icon>
              </el-button>
            </div>
          </div>
          <p v-if="record.content" class="record-content">{{ record.content }}</p>
        </div>
      </el-timeline-item>
    </el-timeline>

    <el-dialog :title="dialogTitle" v-model="showDialog" width="500px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="日期" required>
          <el-date-picker
            v-model="form.contact_date"
            type="date"
            placeholder="选择联系日期"
            value-format="YYYY-MM-DD"
            format="YYYY年M月D日"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="方式" required>
          <el-select v-model="form.contact_type" placeholder="选择互动方式" style="width: 100%">
            <el-option
              v-for="item in contactTypeOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="内容">
          <el-input
            v-model="form.content"
            type="textarea"
            :rows="4"
            placeholder="记录这次联系的内容，例如：约了周末一起吃饭"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button @click="submit" type="primary" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { Plus, Edit, Delete } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getContactRecords,
  createContactRecord,
  updateContactRecord,
  deleteContactRecord
} from '@/api/contactRecords'

const props = defineProps({
  personId: { type: Number, required: true }
})
const emit = defineEmits(['refresh'])

const CONTACT_TYPES = {
  meet: { label: '见面', color: '#409eff' },
  dinner: { label: '聚餐', color: '#e6a23c' },
  phone: { label: '电话', color: '#67c23a' },
  wechat: { label: '微信', color: '#1abc9c' },
  email: { label: '邮件', color: '#9b59b6' },
  gift: { label: '礼物', color: '#f56c6c' },
  other: { label: '其他', color: '#909399' }
}

const contactTypeOptions = Object.entries(CONTACT_TYPES).map(([value, meta]) => ({
  value,
  label: meta.label
}))

const typeMeta = (type) => CONTACT_TYPES[type] || CONTACT_TYPES.other

const records = ref([])
const showDialog = ref(false)
const dialogTitle = ref('记录一次联系')
const saving = ref(false)
const form = reactive({
  id: null,
  contact_date: '',
  contact_type: 'meet',
  content: ''
})

const todayStr = () => {
  const d = new Date()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${d.getFullYear()}-${m}-${day}`
}

const formatDate = (dateString) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  })
}

const loadRecords = async () => {
  try {
    records.value = await getContactRecords({ person_id: props.personId, limit: 100 })
  } catch (error) {
    console.error('获取交往记录失败:', error)
    records.value = []
  }
}

const openDialog = (record = null) => {
  if (record) {
    dialogTitle.value = '编辑交往记录'
    form.id = record.id
    form.contact_date = record.contact_date
    form.contact_type = record.contact_type
    form.content = record.content || ''
  } else {
    dialogTitle.value = '记录一次联系'
    form.id = null
    form.contact_date = todayStr()
    form.contact_type = 'meet'
    form.content = ''
  }
  showDialog.value = true
}

const submit = async () => {
  if (!form.contact_date) {
    ElMessage.warning('请选择联系日期')
    return
  }

  saving.value = true
  try {
    const data = {
      person_id: props.personId,
      contact_date: form.contact_date,
      contact_type: form.contact_type,
      content: form.content || null
    }

    if (form.id) {
      await updateContactRecord(form.id, data)
      ElMessage.success('交往记录已更新')
    } else {
      await createContactRecord(data)
      ElMessage.success('交往记录已添加')
    }

    showDialog.value = false
    await loadRecords()
    // 通知父组件刷新人物信息（更新最近联系时间）
    emit('refresh')
  } catch (error) {
    console.error('保存交往记录失败:', error)
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

const handleDelete = async (recordId) => {
  try {
    await ElMessageBox.confirm('确定要删除这条交往记录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    await deleteContactRecord(recordId)
    ElMessage.success('删除成功')
    await loadRecords()
    emit('refresh')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除交往记录失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

onMounted(() => {
  loadRecords()
})
</script>

<style scoped>
.contacts-card {
  background: var(--card-bg, white);
  border: 1px solid var(--border-color, #dcdfe6);
  border-radius: 12px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary, #303133);
}

.empty {
  color: var(--text-secondary, #999);
  font-size: 13px;
  padding: 16px 12px;
  background: var(--bg-color-light, #f8f9fa);
  border-radius: 8px;
  text-align: center;
}

.record-list {
  padding: 4px 0;
}

.record-list :deep(.el-timeline-item__wrapper) {
  padding-left: 16px;
  top: -6px;
}

.record-list :deep(.el-timeline-item__timestamp) {
  color: var(--text-primary, #303133);
  font-weight: 500;
  font-size: 13px;
}

.record-item {
  padding: 12px 16px;
  background: var(--bg-color-page, #f7f8fa);
  border-radius: 8px;
  border-left: 3px solid var(--border-lighter, #ebeef5);
  transition: all 0.2s ease;
}

.record-item:hover {
  background: var(--bg-color-hover, #eef0f3);
}

.record-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}

.record-actions {
  display: flex;
  gap: 2px;
  margin-left: auto;
}

.record-content {
  margin: 8px 0 0;
  color: var(--text-regular, #606266);
  font-size: 13px;
  line-height: 1.6;
  white-space: pre-wrap;
}
</style>
