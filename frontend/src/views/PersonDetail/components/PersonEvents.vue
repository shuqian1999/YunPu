<template>
  <el-card class="events-card">
    <template #header>
      <div class="card-header">
        <span class="card-title">事件记录</span>
        <el-button @click="openEventDialog()" type="primary" size="small">
          <el-icon><Plus /></el-icon>
          添加事件
        </el-button>
      </div>
    </template>
    <div v-if="events.length === 0" class="empty">暂无事件记录</div>
    <el-timeline v-else class="event-list">
      <el-timeline-item
        v-for="event in events"
        :key="event.id"
        placement="top"
        :timestamp="formatTimelineDate(event.display_date || event.event_date)"
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
                backgroundColor: event.event_type_color || '#c0c4cc',
                borderColor: event.event_type_color || '#c0c4cc',
                color: '#fff'
              }"
              class="event-type-tag"
            >
              {{ event.event_type || '其他' }}
            </el-tag>
            <div class="event-actions">
              <el-button @click="openEventDialog(event)" text type="primary" size="small">
                <el-icon><Edit /></el-icon>
              </el-button>
              <el-button @click="handleDeleteEvent(event.id)" text type="danger" size="small">
                <el-icon><Delete /></el-icon>
              </el-button>
            </div>
          </div>
          <p v-if="event.description" class="event-description">{{ event.description }}</p>
          <div v-if="event.location" class="event-location">
            <el-icon><MapLocation /></el-icon>
            <span>{{ event.location }}</span>
          </div>
        </div>
      </el-timeline-item>
    </el-timeline>

    <el-dialog :title="eventDialogTitle" v-model="showEventDialog" width="500px">
      <el-form :model="eventForm" label-width="80px">
        <el-form-item label="标题" required>
          <el-input v-model="eventForm.title" placeholder="请输入事件标题" />
        </el-form-item>
        <el-form-item label="日期" required>
          <el-date-picker
            v-model="eventForm.event_date"
            type="date"
            placeholder="选择事件日期"
            value-format="YYYY-MM-DD"
            format="YYYY年M月D日"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="农历">
          <el-switch
            v-model="eventForm.is_lunar"
            active-text="是"
            inactive-text="否"
            inline-prompt
          />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="eventForm.event_type_id" placeholder="选择事件类型" clearable style="width: 100%">
            <el-option
              v-for="type in eventTypes"
              :key="type.id"
              :label="type.name"
              :value="type.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="eventForm.description" type="textarea" :rows="3" placeholder="请输入事件描述" />
        </el-form-item>
        <el-form-item label="地点">
          <el-input v-model="eventForm.location" placeholder="请输入事件地点" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEventDialog = false">取消</el-button>
        <el-button @click="submitEvent" type="primary" :loading="eventSaving">保存</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { ref, reactive, inject, computed, onMounted } from 'vue'
import { Plus, Edit, Delete, MapLocation } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getPersonEvents } from '@/api/persons'
import { createEvent, updateEvent, deleteEvent } from '@/api/events'

const props = defineProps({
  personId: { type: Number, required: true }
})

const shared = inject('personShared', null)
const eventTypes = computed(() => shared?.eventTypes?.value || [])

const events = ref([])
const showEventDialog = ref(false)
const eventDialogTitle = ref('添加事件')
const eventForm = reactive({
  id: null,
  title: '',
  event_date: '',
  event_type_id: null,
  is_lunar: false,
  description: '',
  location: ''
})
const eventSaving = ref(false)

const formatTimelineDate = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  })
}

const loadEvents = async () => {
  try {
    events.value = await getPersonEvents(props.personId)
  } catch (error) {
    console.error('获取事件失败:', error)
    events.value = []
  }
}

const openEventDialog = (event = null) => {
  if (event) {
    eventDialogTitle.value = '编辑事件'
    eventForm.id = event.id
    eventForm.title = event.title
    eventForm.event_date = event.event_date
    eventForm.event_type_id = event.event_type_id
    eventForm.is_lunar = event.is_lunar || false
    eventForm.description = event.description || ''
    eventForm.location = event.location || ''
  } else {
    eventDialogTitle.value = '添加事件'
    eventForm.id = null
    eventForm.title = ''
    eventForm.event_date = ''
    eventForm.event_type_id = null
    eventForm.is_lunar = false
    eventForm.description = ''
    eventForm.location = ''
  }
  showEventDialog.value = true
}

const submitEvent = async () => {
  if (!eventForm.title || !eventForm.event_date) {
    ElMessage.warning('请填写标题和日期')
    return
  }

  eventSaving.value = true
  try {
    const data = {
      person_id: props.personId,
      title: eventForm.title,
      event_date: eventForm.event_date,
      event_type_id: eventForm.event_type_id,
      is_lunar: eventForm.is_lunar,
      description: eventForm.description || null,
      location: eventForm.location || null
    }

    if (eventForm.id) {
      await updateEvent(eventForm.id, data)
      ElMessage.success('事件更新成功')
    } else {
      await createEvent(data)
      ElMessage.success('事件添加成功')
    }

    showEventDialog.value = false
    await loadEvents()
  } catch (error) {
    console.error('保存事件失败:', error)
    ElMessage.error('保存事件失败')
  } finally {
    eventSaving.value = false
  }
}

const handleDeleteEvent = async (eventId) => {
  try {
    await ElMessageBox.confirm('确定要删除这个事件吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    await deleteEvent(eventId)
    ElMessage.success('事件删除成功')
    await loadEvents()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除事件失败:', error)
      ElMessage.error('删除事件失败')
    }
  }
}

onMounted(() => {
  loadEvents()
})
</script>

<style scoped>
.events-card {
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

.event-list {
  padding: 4px 0;
}

.event-list :deep(.el-timeline-item__wrapper) {
  padding-left: 16px;
  top: -6px;
}

.event-list :deep(.el-timeline-item__timestamp) {
  color: var(--text-primary, #303133);
  font-weight: 500;
  font-size: 13px;
}

.event-list :deep(.el-timeline-item__node) {
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
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
  flex-wrap: wrap;
}

.event-title {
  font-weight: 500;
  font-size: 15px;
  color: var(--text-primary, #303133);
}

.event-type-tag {
  font-size: 11px;
  flex-shrink: 0;
}

.event-actions {
  display: flex;
  gap: 2px;
  margin-left: auto;
}

.event-description {
  margin: 4px 0 0;
  color: var(--text-regular, #606266);
  font-size: 13px;
  line-height: 1.6;
}

.event-location {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 4px;
  font-size: 12px;
  color: var(--text-secondary, #909399);
}
</style>
