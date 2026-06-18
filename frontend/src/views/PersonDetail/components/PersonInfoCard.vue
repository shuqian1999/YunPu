<template>
  <el-card class="info-section" shadow="never">
    <div class="info-header">
      <div class="info-header-left">
        <span class="person-name">{{ displayName }}</span>
        <el-tag v-if="personInfo.is_me" type="primary" size="small">我</el-tag>
        <el-tag v-if="personInfo.gender === 2" type="success" size="small">女</el-tag>
        <el-tag v-else-if="personInfo.gender === 1" type="warning" size="small">男</el-tag>
      </div>
      <div class="info-header-right">
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
      </div>
    </div>

    <div class="info-body">
      <!-- 头像 -->
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

      <!-- 基本信息 -->
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
          <span v-if="!isEditing" class="value">{{ genderText }}</span>
          <el-radio-group v-else v-model="editForm.gender">
            <el-radio :value="1">男</el-radio>
            <el-radio :value="2">女</el-radio>
          </el-radio-group>
        </div>
        <div class="info-row">
          <span class="label">出生日期</span>
          <span v-if="!isEditing" class="value date-value">
            <template v-if="personInfo.birth_date">
              {{ formatDate(personInfo.birth_date) }}
              <el-tag v-if="personInfo.is_lunar_birth" type="warning" size="small" class="lunar-mini-tag">农历</el-tag>
            </template>
            <template v-else>-</template>
          </span>
          <div v-else class="edit-input birth-edit-group">
            <el-date-picker
              v-model="editForm.birth_date"
              type="date"
              placeholder="选择出生日期"
              value-format="YYYY-MM-DD"
              format="YYYY年M月D日"
              style="flex: 1"
            />
            <el-tooltip :content="editForm.is_lunar_birth ? '此日期按农历记录' : '此日期按公历记录'" placement="top">
              <el-switch v-model="editForm.is_lunar_birth" active-text="农历" inactive-text="公历" inline-prompt class="lunar-switch" />
            </el-tooltip>
          </div>
        </div>
        <div class="info-row">
          <span class="label">是否已故</span>
          <span v-if="!isEditing" class="value">{{ personInfo.death_date ? '是' : '否' }}</span>
          <el-switch v-else v-model="editForm.is_deceased" active-text="是" inactive-text="否" />
        </div>
        <div class="info-row">
          <span class="label">逝世日期</span>
          <span v-if="!isEditing" class="value date-value">
            <template v-if="personInfo.death_date">
              {{ formatDate(personInfo.death_date) }}
              <el-tag v-if="personInfo.is_lunar_death" type="warning" size="small" class="lunar-mini-tag">农历</el-tag>
            </template>
            <template v-else>-</template>
          </span>
          <div v-else class="edit-input birth-edit-group">
            <el-date-picker
              v-model="editForm.death_date"
              type="date"
              placeholder="选择逝世日期"
              value-format="YYYY-MM-DD"
              format="YYYY年M月D日"
              :disabled="!editForm.is_deceased"
              style="flex: 1"
            />
            <el-tooltip :content="editForm.is_lunar_death ? '此日期按农历记录' : '此日期按公历记录'" placement="top">
              <el-switch v-model="editForm.is_lunar_death" active-text="农历" inactive-text="公历" inline-prompt :disabled="!editForm.is_deceased" class="lunar-switch" />
            </el-tooltip>
          </div>
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
        <div class="info-row info-row-stack">
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
  </el-card>
</template>

<script setup>
import { ref, reactive, inject, computed } from 'vue'
import { User, Edit, Camera, Loading } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { updatePerson, uploadPersonAvatar, deletePersonAvatar } from '@/api/persons'

const props = defineProps({
  personId: { type: Number, required: true }
})

const emit = defineEmits(['refresh'])

// 共享数据通过 inject 获取
const shared = inject('personShared', null)

const personInfo = computed(() => shared?.personInfo?.value || {})
const countries = computed(() => shared?.countries?.value || {})

const isEditing = ref(false)
const saving = ref(false)
const uploading = ref(false)
const fileInputRef = ref(null)

const editForm = reactive({
  nickname: '',
  name: '',
  gender: null,
  birth_date: '',
  is_lunar_birth: false,
  is_deceased: false,
  death_date: '',
  is_lunar_death: false,
  country: '',
  hometown: '',
  residence: '',
  notes: '',
  customFields: []
})

const displayName = computed(() => {
  return personInfo.value.nickname || ((personInfo.value.last_name || '') + (personInfo.value.first_name || ''))
})

const genderText = computed(() => {
  if (personInfo.value.gender === 1) return '男'
  if (personInfo.value.gender === 2) return '女'
  return '-'
})

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

const startEdit = () => {
  const p = personInfo.value
  editForm.nickname = p.nickname || ''
  editForm.name = p.last_name ? p.last_name + p.first_name : ''
  editForm.gender = p.gender || null
  editForm.birth_date = p.birth_date || ''
  editForm.is_lunar_birth = !!p.is_lunar_birth
  editForm.is_deceased = !!p.death_date
  editForm.death_date = p.death_date || ''
  editForm.is_lunar_death = !!p.is_lunar_death
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
    const res = await uploadPersonAvatar(props.personId, file)
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

    await deletePersonAvatar(props.personId)
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
  // 校验：姓名和称呼至少有一个不为空
  const name = (editForm.name || '').trim()
  const nickname = (editForm.nickname || '').trim()
  if (!name && !nickname) {
    ElMessage.error('姓名和称呼至少需要填写一个')
    return
  }

  saving.value = true
  try {
    const submitName = editForm.name || ''

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
      last_name: submitName.charAt(0) || null,
      first_name: submitName.slice(1) || null,
      gender: editForm.gender,
      birth_date: editForm.birth_date || null,
      is_lunar_birth: editForm.is_lunar_birth,
      death_date: editForm.is_deceased ? (editForm.death_date || null) : null,
      is_lunar_death: editForm.is_deceased ? editForm.is_lunar_death : false,
      country: editForm.country || null,
      hometown: editForm.hometown || null,
      residence: editForm.residence || null,
      custom_fields: Object.keys(custom_fields).length > 0 ? custom_fields : null
    }

    await updatePerson(props.personId, data)
    ElMessage.success('保存成功')
    isEditing.value = false
    emit('refresh')
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
</script>

<style scoped>
.info-section {
  margin-bottom: 20px;
  background: var(--card-bg, white);
  border: 1px solid var(--border-color, #dcdfe6);
  border-radius: 12px;
  overflow: hidden;
}

.info-section :deep(.el-card__body) {
  padding: 0;
}

.info-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  border-bottom: 1px solid var(--border-lighter, #EBEEF5);
  background: var(--bg-color-light, #fafbfc);
}

.info-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.person-name {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary, #303133);
}

.info-header-right {
  display: flex;
  gap: 8px;
}

.info-body {
  padding: 24px;
  display: flex;
  gap: 32px;
}

.avatar-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  flex-shrink: 0;
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
  min-width: 0;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid var(--border-lighter, #f0f0f0);
  gap: 16px;
}

.info-row:last-child {
  border-bottom: none;
}

.info-row .label {
  color: var(--text-secondary, #999);
  font-size: 14px;
  flex-shrink: 0;
  width: 80px;
}

.info-row .value {
  color: var(--text-primary, #333);
  font-size: 14px;
  font-weight: 500;
  flex: 1;
  text-align: right;
  min-width: 0;
  word-break: break-word;
}

.info-row .edit-input {
  width: 220px;
  flex-shrink: 0;
}

/* 自定义字段行：纵向布局，不被遮挡 */
.info-row-stack {
  flex-direction: column;
  align-items: stretch;
  gap: 12px;
}

.info-row-stack .label {
  width: auto;
  text-align: left;
}

.info-row-stack .value,
.info-row-stack .custom-fields-edit {
  width: 100%;
  max-width: none;
  text-align: left;
}

.birth-edit-group {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 280px;
}

.lunar-switch {
  flex-shrink: 0;
}

.lunar-mini-tag {
  margin-left: 6px;
  font-size: 10px;
  height: 18px;
  line-height: 18px;
  padding: 0 4px;
}

.date-value {
  display: inline-flex;
  align-items: center;
  justify-content: flex-end;
}

.info-row .edit-textarea {
  width: 300px;
}

.custom-fields-view {
  max-width: 300px;
  text-align: right;
}

.custom-field-item {
  display: flex;
  margin-bottom: 4px;
  justify-content: flex-end;
  gap: 8px;
}

.custom-field-name {
  color: var(--text-secondary, #999);
  flex-shrink: 0;
}

.custom-field-value {
  color: var(--text-primary, #333);
}

.custom-fields-edit {
  width: 100%;
  flex: 1;
}

.custom-field-row {
  display: grid;
  grid-template-columns: minmax(120px, 1fr) minmax(180px, 2fr) auto;
  gap: 8px;
  align-items: center;
  margin-bottom: 8px;
}
</style>
