<template>
  <el-card class="reminders-card">
    <template #header>
      <div class="card-header">
        <span class="card-title">提醒事项</span>
        <el-button @click="openReminderDialog()" type="primary" size="small">
          <el-icon><Plus /></el-icon>
          添加提醒
        </el-button>
      </div>
    </template>
    <div v-if="reminders.length === 0" class="empty">暂无提醒事项</div>
    <div v-else class="reminder-list">
      <div
        v-for="reminder in reminders"
        :key="reminder.id"
        class="reminder-item"
      >
        <div class="reminder-title-row">
          <span class="reminder-title">{{ reminder.title }}</span>
          <el-tag
            v-if="reminder.event_type"
            size="small"
            effect="dark"
            :style="{
              backgroundColor: reminder.event_type_color,
              borderColor: reminder.event_type_color,
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
          <el-switch
            v-model="reminder.enabled"
            size="small"
            @change="handleToggleReminder(reminder)"
          />
        </div>
        <div class="reminder-row">
          <div class="reminder-meta">
            <span class="reminder-date">
              <el-icon><Calendar /></el-icon>
              {{ formatDate(reminder.display_date || reminder.remind_date) }}
            </span>
            <span v-if="reminder.location" class="reminder-location">
              <el-icon><MapLocation /></el-icon>
              {{ reminder.location }}
            </span>
          </div>
          <div class="reminder-actions">
            <el-button @click="openReminderDialog(reminder)" text type="primary" size="small">
              <el-icon><Edit /></el-icon>
            </el-button>
            <el-button @click="handleDeleteReminder(reminder.id)" text type="danger" size="small">
              <el-icon><Delete /></el-icon>
            </el-button>
          </div>
        </div>
        <p v-if="reminder.description" class="reminder-description">{{ reminder.description }}</p>
      </div>
    </div>

    <el-dialog :title="reminderDialogTitle" v-model="showReminderDialog" width="500px">
      <el-form :model="reminderForm" label-width="80px">
        <el-form-item label="标题" required>
          <el-input v-model="reminderForm.title" placeholder="请输入提醒标题" />
        </el-form-item>
        <el-form-item label="日期" required>
          <el-date-picker
            v-model="reminderForm.remind_date"
            type="date"
            placeholder="选择提醒日期"
            value-format="YYYY-MM-DD"
            format="YYYY年M月D日"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="农历">
          <el-switch
            v-model="reminderForm.is_lunar"
            active-text="是"
            inactive-text="否"
            inline-prompt
          />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="reminderForm.event_type_id" placeholder="选择提醒类型" clearable style="width: 100%">
            <el-option
              v-for="type in eventTypes"
              :key="type.id"
              :label="type.name"
              :value="type.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="重复">
          <el-select v-model="reminderForm.repeat_type" style="width: 100%">
            <el-option label="不重复" value="once" />
            <el-option label="每年" value="yearly" />
            <el-option label="每月" value="monthly" />
            <el-option label="每周" value="weekly" />
          </el-select>
        </el-form-item>
        <el-form-item label="提前提醒">
          <el-input-number v-model="reminderForm.remind_advance_days" :min="0" :max="30" />
          <span class="form-hint">天（0 = 当天）</span>
        </el-form-item>
        <el-form-item label="事件转换">
          <el-switch v-model="reminderForm.trans_event" />
          <span class="form-hint">开启后，到期会自动生成对应事件（字段对应，无需重复录入）</span>
        </el-form-item>
        <el-form-item label="地点">
          <el-input v-model="reminderForm.location" placeholder="请输入地点" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="reminderForm.description" type="textarea" :rows="3" placeholder="请输入描述" />
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="reminderForm.enabled" active-text="是" inactive-text="否" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showReminderDialog = false">取消</el-button>
        <el-button @click="submitReminder" type="primary" :loading="reminderSaving">保存</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { ref, reactive, inject, computed, onMounted } from 'vue'
import { Plus, Edit, Delete, MapLocation, Calendar } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getPersonReminders } from '@/api/persons'
import { createReminder, updateReminder, deleteReminder } from '@/api/reminders'

const props = defineProps({
  personId: { type: Number, required: true }
})

const shared = inject('personShared', null)
const eventTypes = computed(() => shared?.eventTypes?.value || [])

const reminders = ref([])
const showReminderDialog = ref(false)
const reminderDialogTitle = ref('添加提醒')
const reminderForm = reactive({
  id: null,
  title: '',
  remind_date: '',
  is_lunar: false,
  event_type_id: null,
  repeat_type: 'once',
  enabled: true,
  location: '',
  description: '',
  remind_advance_days: 0,
  trans_event: false
})
const reminderSaving = ref(false)

const formatDate = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

const repeatTypeLabel = (type) => {
  const map = { once: '不重复', yearly: '每年', monthly: '每月', weekly: '每周' }
  return map[type] || ''
}

const loadReminders = async () => {
  try {
    reminders.value = await getPersonReminders(props.personId)
  } catch (error) {
    console.error('获取提醒失败:', error)
    reminders.value = []
  }
}

const openReminderDialog = (reminder = null) => {
  if (reminder) {
    reminderDialogTitle.value = '编辑提醒'
    reminderForm.id = reminder.id
    reminderForm.title = reminder.title
    reminderForm.remind_date = reminder.remind_date
    reminderForm.is_lunar = reminder.is_lunar
    reminderForm.event_type_id = reminder.event_type_id
    reminderForm.repeat_type = reminder.repeat_type || 'once'
    reminderForm.enabled = reminder.enabled
    reminderForm.location = reminder.location || ''
    reminderForm.description = reminder.description || ''
    reminderForm.remind_advance_days = reminder.remind_advance_days || 0
    reminderForm.trans_event = reminder.trans_event || false
  } else {
    reminderDialogTitle.value = '添加提醒'
    reminderForm.id = null
    reminderForm.title = ''
    reminderForm.remind_date = ''
    reminderForm.is_lunar = false
    reminderForm.event_type_id = null
    reminderForm.repeat_type = 'once'
    reminderForm.enabled = true
    reminderForm.location = ''
    reminderForm.description = ''
    reminderForm.remind_advance_days = 0
    reminderForm.trans_event = false
  }
  showReminderDialog.value = true
}

const submitReminder = async () => {
  if (!reminderForm.title || !reminderForm.remind_date) {
    ElMessage.warning('请填写标题和日期')
    return
  }

  reminderSaving.value = true
  try {
    const data = {
      person_id: props.personId,
      title: reminderForm.title,
      remind_date: reminderForm.remind_date,
      is_lunar: reminderForm.is_lunar,
      event_type_id: reminderForm.event_type_id,
      repeat_type: reminderForm.repeat_type,
      enabled: reminderForm.enabled,
      location: reminderForm.location || null,
      description: reminderForm.description || null,
      remind_advance_days: reminderForm.remind_advance_days,
      trans_event: reminderForm.trans_event
    }

    if (reminderForm.id) {
      await updateReminder(reminderForm.id, data)
      ElMessage.success('提醒更新成功')
    } else {
      await createReminder(data)
      ElMessage.success('提醒添加成功')
    }

    showReminderDialog.value = false
    await loadReminders()
  } catch (error) {
    console.error('保存提醒失败:', error)
    ElMessage.error('保存提醒失败')
  } finally {
    reminderSaving.value = false
  }
}

const handleDeleteReminder = async (reminderId) => {
  try {
    await ElMessageBox.confirm('确定要删除这个提醒吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    await deleteReminder(reminderId)
    ElMessage.success('提醒删除成功')
    await loadReminders()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除提醒失败:', error)
      ElMessage.error('删除提醒失败')
    }
  }
}

const handleToggleReminder = async (reminder) => {
  try {
    await updateReminder(reminder.id, {
      person_id: props.personId,
      title: reminder.title,
      remind_date: reminder.remind_date,
      is_lunar: reminder.is_lunar,
      event_type_id: reminder.event_type_id,
      repeat_type: reminder.repeat_type,
      enabled: reminder.enabled,
      location: reminder.location,
      description: reminder.description,
      remind_advance_days: reminder.remind_advance_days,
      trans_event: reminder.trans_event
    })
  } catch (error) {
    console.error('更新提醒状态失败:', error)
    ElMessage.error('更新提醒状态失败')
    reminder.enabled = !reminder.enabled
  }
}

onMounted(() => {
  loadReminders()
})
</script>

<style scoped>
.reminders-card {
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
  padding: 12px;
  background: var(--bg-color-light, #f8f9fa);
  border-radius: 8px;
  text-align: center;
}

.reminder-list {
  margin-top: 16px;
}

.reminder-item {
  padding: 12px 14px;
  border-bottom: 1px solid var(--border-lighter, #ebeef5);
  transition: background 0.2s ease;
}

.reminder-item:last-child {
  border-bottom: none;
}

.reminder-item:hover {
  background: var(--bg-color-light, #f8f9fa);
}

.reminder-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.reminder-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary, #303133);
  flex: 1;
}

.reminder-type-tag {
  font-size: 11px;
  flex-shrink: 0;
}

.reminder-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 4px;
  gap: 8px;
}

.reminder-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  flex-wrap: wrap;
  font-size: 13px;
  color: var(--text-secondary, #909399);
}

.reminder-date,
.reminder-location {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.reminder-actions {
  display: flex;
  gap: 2px;
  flex-shrink: 0;
}

.reminder-description {
  margin: 6px 0 0 0;
  padding: 8px 10px;
  background: var(--bg-color-light, #f7f8fa);
  border-radius: 6px;
  font-size: 13px;
  color: var(--text-regular, #606266);
  line-height: 1.6;
}

.form-hint {
  margin-left: 8px;
  color: var(--text-secondary, #909399);
  font-size: 12px;
}
</style>
