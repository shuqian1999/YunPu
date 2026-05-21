<template>
  <div class="person-detail">
    <el-page-header @back="goBack">
      <template #content>
        <span class="person-name">{{ personInfo.nickname || (personInfo.last_name + personInfo.first_name) }}</span>
        <el-tag v-if="personInfo.is_me" type="primary" size="small">我</el-tag>
        <el-tag v-if="personInfo.gender === 2" type="success" size="small">女</el-tag>
        <el-tag v-else-if="personInfo.gender === 1" type="warning" size="small">男</el-tag>
      </template>
      <template #extra>
        <template v-if="!isEditing">
          <el-button @click="startEdit" type="primary" size="small">
            <el-icon><Edit /></el-icon>
            编辑
          </el-button>
        </template>
        <template v-else>
          <el-button @click="cancelEdit" size="small">取消</el-button>
          <el-button @click="saveEdit" type="primary" size="small" :loading="saving">保存</el-button>
        </template>
      </template>
    </el-page-header>

    <div class="detail-content">
      <div class="info-section">
        <div class="avatar-wrapper">
          <div class="avatar-container" @click="isEditing && !uploading && triggerUpload">
            <img
              v-if="personInfo.avatar_url"
              :src="personInfo.avatar_url"
              class="avatar"
              alt="头像"
            />
            <div v-else class="avatar-placeholder">
              <el-icon :size="48" class="avatar-icon">
                <User />
              </el-icon>
            </div>
            <div v-if="personInfo.death_date" class="deceased-marker">
              <span>逝</span>
            </div>
            <div v-if="isEditing" class="avatar-overlay">
              <el-icon v-if="!uploading" :size="32">
                <Camera />
              </el-icon>
              <el-icon v-else class="loading-icon" :size="32">
                <Loading />
              </el-icon>
            </div>
          </div>
          <div v-if="isEditing" class="avatar-actions">
            <el-button @click="triggerUpload" type="primary" size="small">
              <el-icon><Camera /></el-icon>
              上传头像
            </el-button>
            <el-button v-if="personInfo.avatar_url" @click="handleDeleteAvatar" type="danger" size="small">
              删除头像
            </el-button>
          </div>
        </div>
        <input
          ref="fileInputRef"
          type="file"
          accept="image/*"
          style="display: none"
          @change="handleAvatarUpload"
        />

        <div class="basic-info">
          <div class="info-row">
            <span class="label">称呼</span>
            <span v-if="!isEditing" class="value">{{ personInfo.nickname || '-' }}</span>
            <el-input v-else v-model="editForm.nickname" class="edit-input" placeholder="请输入称呼" />
          </div>
          <div class="info-row">
            <span class="label">姓名</span>
            <span v-if="!isEditing" class="value">{{ personInfo.last_name }}{{ personInfo.first_name || '-' }}</span>
            <el-input v-else v-model="editForm.name" class="edit-input" placeholder="请输入姓名" />
          </div>
          <div class="info-row">
            <span class="label">性别</span>
            <span v-if="!isEditing" class="value">{{ personInfo.gender === 1 ? '男' : personInfo.gender === 2 ? '女' : '-' }}</span>
            <el-radio-group v-else v-model="editForm.gender">
              <el-radio :value="1">男</el-radio>
              <el-radio :value="2">女</el-radio>
            </el-radio-group>
          </div>
          <div class="info-row">
            <span class="label">出生日期</span>
            <span v-if="!isEditing" class="value">{{ formatDate(personInfo.birth_date) }}</span>
            <el-date-picker v-else v-model="editForm.birth_date" type="date" placeholder="选择出生日期" value-format="YYYY-MM-DD" class="edit-input" />
          </div>
          <div class="info-row">
            <span class="label">是否已故</span>
            <span v-if="!isEditing" class="value">{{ personInfo.death_date ? '是' : '否' }}</span>
            <el-switch v-else v-model="editForm.is_deceased" active-text="是" inactive-text="否" />
          </div>
          <div class="info-row">
            <span class="label">逝世日期</span>
            <span v-if="!isEditing" class="value">{{ personInfo.death_date ? formatDate(personInfo.death_date) : '-' }}</span>
            <el-date-picker v-else v-model="editForm.death_date" type="date" placeholder="选择逝世日期" value-format="YYYY-MM-DD" class="edit-input" :disabled="!editForm.is_deceased" />
          </div>
          <div class="info-row">
            <span class="label">国家</span>
            <span v-if="!isEditing" class="value">{{ getCountryName(personInfo.country) }}</span>
            <el-select v-else v-model="editForm.country" class="edit-input" placeholder="选择国家" filterable clearable style="width: 200px">
              <el-option v-for="(info, code) in countries" :key="code" :label="info.name" :value="code" />
            </el-select>
          </div>
          <div class="info-row">
            <span class="label">家乡</span>
            <span v-if="!isEditing" class="value">{{ personInfo.hometown || '-' }}</span>
            <el-input v-else v-model="editForm.hometown" class="edit-input" placeholder="请输入家乡" />
          </div>
          <div class="info-row">
            <span class="label">现居地</span>
            <span v-if="!isEditing" class="value">{{ personInfo.residence || '-' }}</span>
            <el-input v-else v-model="editForm.residence" class="edit-input" placeholder="请输入现居地" />
          </div>
          <div class="info-row">
            <span class="label">备注</span>
            <span v-if="!isEditing" class="value">{{ personInfo.custom_fields?.notes || '-' }}</span>
            <el-input v-else v-model="editForm.notes" class="edit-textarea" type="textarea" placeholder="请输入备注" :rows="3" />
          </div>
          <div class="info-row">
            <span class="label">自定义字段</span>
            <div v-if="!isEditing" class="value custom-fields-view">
              <div v-if="customFieldsList.length === 0">暂无自定义字段</div>
              <div v-for="(field, index) in customFieldsList" :key="index" class="custom-field-item">
                <span class="field-name">{{ field.name }}:</span>
                <span class="field-value">{{ field.value }}</span>
              </div>
            </div>
            <div v-else class="custom-fields-edit">
              <div v-for="(field, index) in editForm.customFields" :key="index" class="custom-field-row">
                <el-input v-model="field.name" placeholder="字段名称" class="custom-field-name" />
                <el-input v-model="field.value" placeholder="字段值" class="custom-field-value" />
                <el-button v-if="editForm.customFields.length > 1" @click="removeCustomField(index)" text type="danger" size="small">删除</el-button>
              </div>
              <el-button @click="addCustomField" text type="primary" size="small">+ 添加字段</el-button>
            </div>
          </div>
        </div>
      </div>

      <div class="groups-section">
        <div class="section-header">
          <h3 class="section-title">所属分组</h3>
          <el-button @click="showEditGroups = true" type="primary" size="small">
            <el-icon><Edit /></el-icon>
            编辑分组
          </el-button>
        </div>
        <div class="groups-content">
          <div v-if="personGroups.length === 0" class="empty">暂无分组</div>
          <div v-else class="groups-list">
            <el-tag
              v-for="group in personGroups"
              :key="group.id"
              :color="group.color"
              effect="dark"
              class="group-tag"
            >
              {{ group.name }}
            </el-tag>
          </div>
        </div>
      </div>

      <div class="relations-section">
        <div class="section-header">
          <h3 class="section-title">家庭关系</h3>
          <el-button @click="showEditRelation = true" type="primary" size="small">
            <el-icon><Edit /></el-icon>
            编辑关系
          </el-button>
        </div>
        <div class="relations-content">
          <div v-if="relations.length === 0" class="empty">暂无关系信息</div>
          <div v-else class="relation-list">
            <div
              v-for="rel in relations"
              :key="rel.person_id"
              class="relation-item clickable"
              @click="navigateToPerson(rel.person_id)"
            >
              <div class="relation-main">
                <span class="nature-tag" :class="{ secondary: rel.relation_nature > 0 }">
                  {{ rel.relation_nature > 0 ? getRelationNatureLabel(rel.relation_nature) : '亲' }}
                </span>
                <span class="relation-type">{{ rel.relation_name }}</span>
                <span class="relation-name">{{ rel.name }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="events-reminders-grid">
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
          <div v-else class="event-list">
            <el-timeline>
              <el-timeline-item
                v-for="event in events"
                :key="event.id"
                :timestamp="formatDate(event.event_date)"
                placement="top"
              >
                <el-card class="event-card" :shadow="false">
                  <div class="event-header">
                    <span class="event-title">{{ event.title }}</span>
                    <el-tag
                      :color="event.event_type_color"
                      size="small"
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
                  <p class="event-description">{{ event.description }}</p>
                  <div v-if="event.location" class="event-location">
                    <el-icon><MapLocation /></el-icon>
                    <span>{{ event.location }}</span>
                  </div>
                </el-card>
              </el-timeline-item>
            </el-timeline>
          </div>
        </el-card>

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
                <el-tag v-if="reminder.is_lunar" type="info" size="small">农历</el-tag>
                <el-switch
                  v-model="reminder.enabled"
                  size="small"
                  @change="handleToggleReminder(reminder)"
                />
              </div>
              <div class="reminder-row">
                <span class="reminder-date">{{ formatDate(reminder.remind_date) }}</span>
                <div class="reminder-actions">
                  <el-button @click="openReminderDialog(reminder)" text type="primary" size="small">
                    <el-icon><Edit /></el-icon>
                  </el-button>
                  <el-button @click="handleDeleteReminder(reminder.id)" text type="danger" size="small">
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </div>
    </div>

    <el-dialog title="编辑分组" v-model="showEditGroups" width="500px">
      <el-checkbox-group v-model="selectedGroups" v-loading="groupsLoading">
        <div v-if="allGroups.length === 0" class="empty">暂无可用分组，请先创建分组</div>
        <el-checkbox
          v-for="group in allGroups"
          :key="group.id"
          :label="group.id"
          class="group-checkbox"
        >
          <el-tag :color="group.color" size="small" effect="dark">
            {{ group.name }}
          </el-tag>
          <span v-if="group.description" class="group-desc">{{ group.description }}</span>
        </el-checkbox>
      </el-checkbox-group>
      <template #footer>
        <el-button @click="showEditGroups = false">取消</el-button>
        <el-button type="primary" @click="handleSaveGroups">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog title="编辑家族关系" v-model="showEditRelation" width="600px">
      <div class="relation-edit-section">
        <h4>添加关系</h4>
        <el-form :model="relationForm" label-width="80px">
          <el-form-item label="关系类型">
            <el-radio-group v-model="relationForm.relationType">
              <el-radio label="family">家庭关系</el-radio>
              <el-radio label="spouse">配偶关系</el-radio>
            </el-radio-group>
          </el-form-item>

          <template v-if="relationForm.relationType === 'family'">
            <el-form-item label="选择人物">
              <el-select v-model="relationForm.person_b_id" placeholder="选择人物" filterable>
                <el-option
                  v-for="p in availablePersons"
                  :key="p.id"
                  :label="p.name"
                  :value="p.id"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="关系">
              <el-select v-model="relationForm.relation">
                <el-option label="父亲" :value="0" />
                <el-option label="母亲" :value="1" />
                <el-option label="儿子" :value="2" />
                <el-option label="女儿" :value="3" />
              </el-select>
            </el-form-item>
            <el-form-item label="关系性质">
              <el-select v-model="relationForm.relation_nature">
                <el-option label="亲（血亲）" :value="0" />
                <el-option label="继（继亲）" :value="1" />
                <el-option label="养（收养）" :value="2" />
                <el-option label="义（结义）" :value="3" />
                <el-option label="干（干亲）" :value="4" />
              </el-select>
            </el-form-item>
          </template>

          <template v-else>
            <el-form-item label="选择人物">
              <el-select v-model="relationForm.person_b_id" placeholder="选择人物" filterable>
                <el-option
                  v-for="p in availablePersons"
                  :key="p.id"
                  :label="p.name"
                  :value="p.id"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="关系">
              <el-select v-model="relationForm.relation">
                <el-option label="丈夫" :value="0" />
                <el-option label="妻子" :value="1" />
                <el-option label="姨太太" :value="2" />
                <el-option label="男朋友" :value="3" />
                <el-option label="女朋友" :value="4" />
              </el-select>
            </el-form-item>
            <el-form-item label="关系性质">
              <el-select v-model="relationForm.relation_nature">
                <el-option label="现任" :value="0" />
                <el-option label="前任" :value="1" />
              </el-select>
            </el-form-item>
          </template>

          <el-form-item>
            <div class="relation-preview">
              <strong>{{ getPersonDetailRelationPreview() }}</strong>
            </div>
          </el-form-item>

          <el-form-item>
            <el-button type="primary" @click="handleAddRelation">添加关系</el-button>
          </el-form-item>
        </el-form>
      </div>

      <div class="relation-edit-section">
        <h4>现有关系</h4>
        <div v-if="relations.length === 0" class="empty">暂无关系</div>
        <div v-else class="existing-relations">
          <div
            v-for="rel in relations"
            :key="rel.person_id + '-' + rel.relation_type"
            class="existing-relation-item"
          >
            <div class="relation-info">
              <span class="relation-name">{{ rel.name }}</span>
              <span class="relation-type">{{ rel.relation_name }}</span>
              <span v-if="rel.relation_nature > 0" class="nature-tag secondary">
                {{ getRelationNatureLabel(rel.relation_nature) }}
              </span>
            </div>
            <el-button
              @click="handleDeleteRelation(rel)"
              text
              type="danger"
              size="small"
            >
              删除
            </el-button>
          </div>
        </div>
      </div>

      <template #footer>
        <el-button @click="showEditRelation = false">关闭</el-button>
      </template>
    </el-dialog>

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
            style="width: 100%"
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
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="农历">
          <el-switch v-model="reminderForm.is_lunar" active-text="是" inactive-text="否" />
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

  </div>
</template>

<script setup>
import { ref, onMounted, reactive, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { User, MapLocation, Edit, Camera, Loading, Plus, Delete } from '@element-plus/icons-vue'
import { getPerson, getPersonEvents, getPersonReminders, getPersonRelations } from '@/api/persons'
import { getGroups, addPersonToGroup, removePersonFromGroup, getPersonGroups } from '@/api/groups'
import { createEvent, updateEvent, deleteEvent } from '@/api/events'
import { createReminder, updateReminder, deleteReminder } from '@/api/reminders'
import { createFamilyRelation, createSpouseRelation, deleteFamilyRelation, deleteSpouseRelation, getRelationNatureLabel } from '@/api/family'
import { getEventTypes } from '@/api/event_types'
import { getCountries } from '@/api/countries'
import { getPersons } from '@/api/persons'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()
const route = useRoute()
const personId = parseInt(route.params.id)

const personInfo = ref({})
const events = ref([])
const reminders = ref([])
const relations = ref([])
const activeTab = ref('events')
const countries = ref([])
const availablePersons = ref([])
const showEditRelation = ref(false)

// 分组管理
const showEditGroups = ref(false)
const allGroups = ref([])
const personGroups = ref([])
const selectedGroups = ref([])
const groupsLoading = ref(false)

const showEventDialog = ref(false)
const eventDialogTitle = ref('添加事件')
const eventForm = reactive({
  id: null,
  title: '',
  event_date: '',
  event_type_id: null,
  description: '',
  location: ''
})
const eventSaving = ref(false)

const showReminderDialog = ref(false)
const reminderDialogTitle = ref('添加提醒')
const reminderForm = reactive({
  id: null,
  title: '',
  remind_date: '',
  is_lunar: false,
  enabled: true
})
const reminderSaving = ref(false)

const eventTypes = ref([])

const isEditing = ref(false)
const saving = ref(false)
const uploading = ref(false)
const fileInputRef = ref(null)

const relationForm = reactive({
  relationType: 'family',
  person_b_id: null,
  relation: 0,
  relation_nature: 0
})

const editForm = reactive({
  nickname: '',
  name: '',
  gender: null,
  birth_date: '',
  is_deceased: false,
  death_date: '',
  country: '',
  hometown: '',
  residence: '',
  notes: '',
  customFields: []
})

const formatDate = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

const getCountryName = (countryCode) => {
  if (!countryCode) return '-'
  const country = countries.value[countryCode]
  return country ? country.name : countryCode
}

const customFieldsList = computed(() => {
  const fields = []
  const customData = personInfo.value.custom_fields || {}
  for (const key in customData) {
    if (key !== 'notes') {
      fields.push({ name: key, value: customData[key] })
    }
  }
  return fields
})

const navigateToPerson = (id) => {
  router.push(`/persons/${id}`)
}

const goBack = () => {
  router.back()
}

const startEdit = () => {
  const p = personInfo.value
  editForm.nickname = p.nickname || ''
  editForm.name = p.last_name ? p.last_name + p.first_name : ''
  editForm.gender = p.gender || null
  editForm.birth_date = p.birth_date || ''
  editForm.is_deceased = !!p.death_date
  editForm.death_date = p.death_date || ''
  editForm.country = p.country || ''
  editForm.hometown = p.hometown || ''
  editForm.residence = p.residence || ''
  editForm.notes = p.custom_fields?.notes || ''
  
  const customFieldsData = p.custom_fields || {}
  const fields = []
  for (const key in customFieldsData) {
    if (key !== 'notes') {
      fields.push({ name: key, value: customFieldsData[key] })
    }
  }
  editForm.customFields = fields.length > 0 ? fields : [{ name: '', value: '' }]
  isEditing.value = true
}

const cancelEdit = () => {
  isEditing.value = false
}

const triggerUpload = () => {
  if (fileInputRef.value) {
    fileInputRef.value.click()
  }
}

const handleAvatarUpload = async (event) => {
  const file = event.target.files[0]
  if (!file) return

  uploading.value = true
  try {
    const { uploadPersonAvatar } = await import('@/api/persons')
    const res = await uploadPersonAvatar(personId, file)
    personInfo.value.avatar_url = res.avatar_url
    ElMessage.success('头像上传成功')
  } catch (error) {
    console.error('头像上传失败:', error)
    ElMessage.error('头像上传失败')
  } finally {
    uploading.value = false
    if (fileInputRef.value) {
      fileInputRef.value.value = ''
    }
  }
}

const handleDeleteAvatar = async () => {
  try {
    await ElMessageBox.confirm('确定要删除头像吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    const { deletePersonAvatar } = await import('@/api/persons')
    await deletePersonAvatar(personId)
    personInfo.value.avatar_url = null
    ElMessage.success('头像删除成功')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('头像删除失败:', error)
      ElMessage.error('头像删除失败')
    }
  }
}

const saveEdit = async () => {
  saving.value = true
  try {
    const { updatePerson } = await import('@/api/persons')
    const name = editForm.name || ''
    
    const custom_fields = {}
    if (editForm.notes) {
      custom_fields.notes = editForm.notes
    }
    editForm.customFields.forEach(field => {
      if (field.name.trim()) {
        custom_fields[field.name.trim()] = field.value.trim()
      }
    })
    
    const data = {
      nickname: editForm.nickname || null,
      last_name: name.charAt(0) || null,
      first_name: name.slice(1) || null,
      gender: editForm.gender,
      birth_date: editForm.birth_date || null,
      death_date: editForm.is_deceased ? editForm.death_date || null : null,
      country: editForm.country || null,
      hometown: editForm.hometown || null,
      residence: editForm.residence || null,
      custom_fields: Object.keys(custom_fields).length > 0 ? custom_fields : null
    }
    
    await updatePerson(personId, data)
    ElMessage.success('保存成功')
    isEditing.value = false
    await loadData()
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

const addCustomField = () => {
  editForm.customFields.push({ name: '', value: '' })
}

const removeCustomField = (index) => {
  editForm.customFields.splice(index, 1)
}

const getPersonDetailRelationPreview = () => {
  const currentPerson = personInfo.value
  const personB = availablePersons.value.find(p => p.id === relationForm.person_b_id)

  if (!currentPerson || !personB) {
    return '请选择人物以预览关系'
  }

  const relationLabels = {
    family: { 0: '父亲', 1: '母亲', 2: '儿子', 3: '女儿' },
    spouse: { 0: '丈夫', 1: '妻子', 2: '姨太太', 3: '男朋友', 4: '女朋友' }
  }

  const type = relationForm.relationType
  const relation = relationLabels[type]?.[relationForm.relation] || '未知'

  return `${personB.name}，是${currentPerson.nickname || (currentPerson.last_name || '') + (currentPerson.first_name || '')}的${relation}`
}

const getRelationDescription = (rel) => {
  return rel.relation_name
}

const handleAddRelation = async () => {
  if (!relationForm.person_b_id) {
    ElMessage.warning('请选择人物')
    return
  }

  if (relationForm.person_b_id === personId) {
    ElMessage.warning('不能与自己建立关系')
    return
  }

  try {
    if (relationForm.relationType === 'family') {
      await createFamilyRelation(
        personId,
        relationForm.person_b_id,
        relationForm.relation,
        relationForm.relation_nature
      )
    } else {
      await createSpouseRelation(
        personId,
        relationForm.person_b_id,
        relationForm.relation,
        relationForm.relation_nature
      )
    }
    ElMessage.success('关系添加成功')
    await loadRelations()
    
    // 重置表单
    relationForm.person_b_id = null
    relationForm.relation = 0
    relationForm.relation_nature = 0
  } catch (error) {
    console.error('添加关系失败:', error)
    ElMessage.error('添加关系失败')
  }
}

const handleDeleteRelation = async (rel) => {
  try {
    await ElMessageBox.confirm(`确定要删除与 ${rel.name} 的关系吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    if (typeof rel.relation_type === 'string' && rel.relation_type.startsWith('spouse')) {
      await deleteSpouseRelation(personId, rel.person_id)
    } else {
      await deleteFamilyRelation(personId, rel.person_id)
    }
    ElMessage.success('关系删除成功')
    await loadRelations()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除关系失败:', error)
      ElMessage.error('删除关系失败')
    }
  }
}

const loadData = async () => {
  try {
    const [personData, eventsData, remindersData, countriesData, personsData, eventTypesData, groupsData] = await Promise.all([
      getPerson(personId),
      getPersonEvents(personId),
      getPersonReminders(personId),
      getCountries(),
      getPersons(),
      getEventTypes(),
      getGroups()
    ])

    personInfo.value = personData
    events.value = eventsData
    reminders.value = remindersData
    countries.value = countriesData
    eventTypes.value = eventTypesData
    allGroups.value = groupsData

    // 获取该人物所属的分组
    const personGroupsData = await getPersonGroups(personId)
    personGroups.value = personGroupsData

    availablePersons.value = personsData.map(p => ({
      id: p.id,
      name: p.nickname || `${p.last_name}${p.first_name}`
    })).filter(p => p.id !== personId)

    // 加载关系
    await loadRelations()
  } catch (error) {
    console.error('获取人物信息失败:', error)
  }
}

const loadRelations = async () => {
  try {
    relations.value = await getPersonRelations(personId)
  } catch (error) {
    console.error('获取关系失败:', error)
    relations.value = []
  }
}

onMounted(async () => {
  await loadData()
})

watch(showEditGroups, (val) => {
  if (val) {
    selectedGroups.value = personGroups.value.map(g => g.id)
  }
})

watch(showEditRelation, (val) => {
  if (val) {
    // 重置表单
    relationForm.person_b_id = null
    relationForm.relation = 0
    relationForm.relation_nature = 0
  }
})

// 分组管理函数
const handleSaveGroups = async () => {
  try {
    const currentGroupIds = personGroups.value.map(g => g.id)
    const newGroupIds = selectedGroups.value

    const toAdd = newGroupIds.filter(id => !currentGroupIds.includes(id))
    const toRemove = currentGroupIds.filter(id => !newGroupIds.includes(id))

    for (const groupId of toAdd) {
      await addPersonToGroup(groupId, personId)
    }

    for (const groupId of toRemove) {
      await removePersonFromGroup(groupId, personId)
    }

    personGroups.value = allGroups.value.filter(g => newGroupIds.includes(g.id))

    showEditGroups.value = false
    ElMessage.success('分组更新成功')
  } catch (error) {
    console.error('更新分组失败:', error)
    ElMessage.error('更新分组失败')
  }
}

const openEventDialog = (event = null) => {
  if (event) {
    eventDialogTitle.value = '编辑事件'
    eventForm.id = event.id
    eventForm.title = event.title
    eventForm.event_date = event.event_date
    eventForm.event_type_id = event.event_type_id
    eventForm.description = event.description || ''
    eventForm.location = event.location || ''
  } else {
    eventDialogTitle.value = '添加事件'
    eventForm.id = null
    eventForm.title = ''
    eventForm.event_date = ''
    eventForm.event_type_id = null
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
      person_id: personId,
      title: eventForm.title,
      event_date: eventForm.event_date,
      event_type_id: eventForm.event_type_id,
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
    const eventsData = await getPersonEvents(personId)
    events.value = eventsData
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
    const eventsData = await getPersonEvents(personId)
    events.value = eventsData
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除事件失败:', error)
      ElMessage.error('删除事件失败')
    }
  }
}

const openReminderDialog = (reminder = null) => {
  if (reminder) {
    reminderDialogTitle.value = '编辑提醒'
    reminderForm.id = reminder.id
    reminderForm.title = reminder.title
    reminderForm.remind_date = reminder.remind_date
    reminderForm.is_lunar = reminder.is_lunar
    reminderForm.enabled = reminder.enabled
  } else {
    reminderDialogTitle.value = '添加提醒'
    reminderForm.id = null
    reminderForm.title = ''
    reminderForm.remind_date = ''
    reminderForm.is_lunar = false
    reminderForm.enabled = true
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
      person_id: personId,
      title: reminderForm.title,
      remind_date: reminderForm.remind_date,
      is_lunar: reminderForm.is_lunar,
      enabled: reminderForm.enabled
    }

    if (reminderForm.id) {
      await updateReminder(reminderForm.id, data)
      ElMessage.success('提醒更新成功')
    } else {
      await createReminder(data)
      ElMessage.success('提醒添加成功')
    }

    showReminderDialog.value = false
    const remindersData = await getPersonReminders(personId)
    reminders.value = remindersData
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
    const remindersData = await getPersonReminders(personId)
    reminders.value = remindersData
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
      person_id: personId,
      title: reminder.title,
      remind_date: reminder.remind_date,
      is_lunar: reminder.is_lunar,
      enabled: reminder.enabled
    })
  } catch (error) {
    console.error('更新提醒状态失败:', error)
    ElMessage.error('更新提醒状态失败')
    reminder.enabled = !reminder.enabled
  }
}
</script>

<style scoped>
.person-detail {
  min-height: 100vh;
  background: var(--bg-color, #f5f7fa);
}

.person-name {
  font-size: 24px;
  font-weight: bold;
  margin-right: 12px;
  color: var(--text-primary, #303133);
}

.detail-content {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.info-section {
  background: var(--card-bg, white);
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 20px;
  display: flex;
  gap: 32px;
  box-shadow: var(--box-shadow, 0 2px 12px rgba(0, 0, 0, 0.08));
  border: 1px solid var(--border-color, #dcdfe6);
}

.avatar-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.avatar-container {
  position: relative;
  cursor: pointer;
}

.avatar {
  width: 160px;
  height: 160px;
  border-radius: 50%;
  object-fit: cover;
  border: 4px solid var(--primary-color, #409EFF);
}

.avatar-placeholder {
  width: 160px;
  height: 160px;
  border-radius: 50%;
  background: var(--border-lighter, #f0f0f0);
  display: flex;
  align-items: center;
  justify-content: center;
  border: 4px solid var(--primary-color, #409EFF);
}

.avatar-icon {
  color: var(--primary-color, #409EFF);
}

.avatar-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 160px;
  height: 160px;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  opacity: 0;
  transition: opacity 0.3s;
  border: 4px solid var(--primary-color, #409EFF);
  box-sizing: border-box;
}

.avatar-container:hover .avatar-overlay {
  opacity: 1;
}

.avatar-actions {
  display: flex;
  gap: 8px;
}

.loading-icon {
  animation: rotate 1s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.deceased-marker {
  position: absolute;
  bottom: 4px;
  right: 4px;
  width: 32px;
  height: 32px;
  background: var(--text-secondary, #666);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 12px;
  z-index: 10;
}

.basic-info {
  flex: 1;
}

.info-row {
  display: flex;
  justify-content: space-between;
  padding: 12px 0;
  border-bottom: 1px solid var(--border-lighter, #f0f0f0);
}

.info-row:last-child {
  border-bottom: none;
}

.info-row .label {
  color: var(--text-secondary, #999);
  font-size: 14px;
}

.info-row .value {
  color: var(--text-primary, #333);
  font-size: 14px;
  font-weight: 500;
}

.info-row .edit-input {
  width: 200px;
}

.info-row .edit-textarea {
  width: 300px;
}

.custom-fields-view {
  max-width: 300px;
}

.custom-field-item {
  display: flex;
  margin-bottom: 4px;
}

.custom-field-name {
  color: var(--text-secondary, #999);
  margin-right: 8px;
  flex: 1;
}

.custom-field-value {
  color: var(--text-primary, #333);
  flex: 2;
}

.custom-fields-edit {
  max-width: 300px;
}

.custom-field-row {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 8px;
}

.groups-section,
.relations-section {
  background: var(--card-bg, white);
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 20px;
  box-shadow: var(--box-shadow, 0 2px 12px rgba(0, 0, 0, 0.08));
  border: 1px solid var(--border-color, #dcdfe6);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.section-title {
  font-size: 18px;
  font-weight: bold;
  margin: 0;
  color: var(--text-primary, #303133);
}

.groups-content .groups-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.group-tag {
  margin: 0;
}

.group-checkbox {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
  width: 100%;
}

.group-checkbox .group-desc {
  margin-left: 8px;
  color: var(--text-secondary, #909399);
  font-size: 12px;
}

.relation-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.relation-item {
  padding: 12px;
  background: var(--bg-color-light, #f8f9fa);
  border-radius: 8px;
}

.relation-item.clickable:hover {
  cursor: pointer;
  background: rgba(64, 158, 255, 0.1);
}

.relation-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary, #333);
}

.relation-type {
  font-size: 12px;
  color: var(--text-secondary, #999);
  margin-top: 4px;
}

.nature-tag {
  background: rgba(230, 162, 60, 0.1);
  color: var(--warning-color, #fa8c16);
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  margin-left: 8px;
}

.nature-tag.secondary {
  background: rgba(64, 158, 255, 0.1);
  color: #409EFF;
}

.empty {
  color: var(--text-secondary, #999);
  font-size: 13px;
  padding: 12px;
  background: var(--bg-color-light, #f8f9fa);
  border-radius: 8px;
  text-align: center;
}

.events-reminders-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-top: 24px;
}

@media (max-width: 768px) {
  .events-reminders-grid {
    grid-template-columns: 1fr;
  }
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

.events-card,
.reminders-card {
  background: var(--card-bg, white);
  border: 1px solid var(--border-color, #dcdfe6);
}

.event-list,
.reminder-list {
  margin-top: 16px;
}

.event-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.event-title {
  font-weight: 600;
  font-size: 14px;
  color: var(--text-primary, #333);
}

.event-type-tag {
  font-size: 11px;
}

.event-actions {
  display: flex;
  gap: 4px;
  margin-left: auto;
}

.reminder-item {
  padding: 12px;
  border-bottom: 1px solid var(--border-lighter, #ebeef5);
}

.reminder-item:last-child {
  border-bottom: none;
}

.reminder-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.reminder-title {
  font-size: 14px;
  font-weight: 500;
}

.reminder-date {
  color: #999;
  font-size: 13px;
}

.reminder-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 4px;
}

.reminder-actions {
  display: flex;
  gap: 4px;
}

.relation-edit-section {
  margin-bottom: 24px;
  padding-bottom: 24px;
  border-bottom: 1px solid var(--border-lighter, #ebeef5);
}

.relation-edit-section:last-child {
  border-bottom: none;
  margin-bottom: 0;
  padding-bottom: 0;
}

.relation-edit-section h4 {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary, #303133);
}

.existing-relations {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.existing-relation-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: var(--bg-color-light, #f8f9fa);
  border-radius: 8px;
}

.relation-info {
  display: flex;
  align-items: center;
  gap: 8px;
}
.relation-preview {
  padding: 12px 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 8px;
  color: white;
  text-align: center;
  font-size: 14px;
}
.relation-main {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.relation-type {
  flex: 0 0 auto;
  color: var(--text-secondary, #666);
  min-width: 50px;
}
.relation-name {
  flex: 1;
  font-weight: 500;
  color: var(--text-primary, #333);
}
</style>
