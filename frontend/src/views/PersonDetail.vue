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
        <div class="avatar-container">
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
        </div>

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

      <div class="relations-section">
        <div class="section-header">
          <h3 class="section-title">家庭关系</h3>
          <el-button @click="showEditFamily = true" type="primary" size="small">
            <el-icon><Edit /></el-icon>
            编辑关系
          </el-button>
        </div>
        <div class="relations-content">
          <div class="relation-group">
            <h4>父亲</h4>
            <template v-if="fathers.length > 0">
              <div
                v-for="parent in fathers"
                :key="parent.id"
                class="relation-item clickable"
                @click="navigateToPerson(parent.person_id)"
              >
                <div class="relation-name">{{ parent.name }}</div>
                <div class="relation-type">
                  <span class="nature-tag">{{ getRelationLabel(parent) }}</span>
                </div>
              </div>
            </template>
            <div v-else class="empty">暂无父亲信息</div>
          </div>

          <div class="relation-group">
            <h4>母亲</h4>
            <template v-if="mothers.length > 0">
              <div
                v-for="parent in mothers"
                :key="parent.id"
                class="relation-item clickable"
                @click="navigateToPerson(parent.person_id)"
              >
                <div class="relation-name">{{ parent.name }}</div>
                <div class="relation-type">
                  <span class="nature-tag">{{ getRelationLabel(parent) }}</span>
                </div>
              </div>
            </template>
            <div v-else class="empty">暂无母亲信息</div>
          </div>

          <div class="relation-group">
            <h4>子女</h4>
            <div v-if="family.children && family.children.length === 0" class="empty">暂无子女信息</div>
            <div v-else-if="family.children" class="relation-list">
              <div
                v-for="child in family.children"
                :key="child.id"
                class="relation-item clickable"
                @click="navigateToPerson(child.person_id)"
              >
                <div class="relation-name">{{ child.name }}</div>
                <div class="relation-type">
                  {{ child.parent_type === 'father' ? '儿子' : '女儿' }}
                  <span v-if="child.relation_nature !== 'qin'" class="nature-tag">
                    {{ child.relation_nature === 'ji' ? '继' : '义' }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="tabs-section">
        <el-tabs v-model="activeTab" class="detail-tabs">
          <el-tab-pane label="事件记录" name="events">
            <div class="tab-content">
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
            </div>
          </el-tab-pane>

          <el-tab-pane label="提醒事项" name="reminders">
            <div class="tab-content">
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
                  </div>
                  <span class="reminder-date">{{ formatDate(reminder.remind_date) }}</span>
                </div>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </div>

    <el-dialog title="编辑家族关系" v-model="showEditFamily" width="560px">
      <el-form :model="familyForm" label-width="80px">
        <el-form-item label="父母">
          <div class="multi-relation-list">
            <div
              v-for="(parent, index) in familyForm.parents"
              :key="index"
              class="multi-relation-row"
            >
              <el-select v-model="parent.person_id" placeholder="选择人物" filterable>
                <el-option
                  v-for="member in availableFamilyMembers"
                  :key="member.id"
                  :label="member.name"
                  :value="member.id"
                />
              </el-select>
              <el-select v-model="parent.parent_type" placeholder="关系">
                <el-option label="父亲" value="father" />
                <el-option label="母亲" value="mother" />
              </el-select>
              <el-select v-model="parent.relation_nature" placeholder="性质">
                <el-option label="亲生" value="qin" />
                <el-option label="继亲" value="ji" />
                <el-option label="养亲" value="yang" />
                <el-option label="义亲" value="yi" />
              </el-select>
              <el-button
                v-if="familyForm.parents.length > 1"
                @click="removeParent(index)"
                text
                type="danger"
                size="small"
              >删除</el-button>
            </div>
            <el-button @click="addParent" text type="primary" size="small">
              + 添加父母
            </el-button>
          </div>
        </el-form-item>

        <el-form-item label="子女">
          <div class="multi-relation-list">
            <div
              v-for="(child, index) in familyForm.children"
              :key="index"
              class="multi-relation-row"
            >
              <el-select v-model="child.person_id" placeholder="选择人物" filterable>
                <el-option
                  v-for="member in availableFamilyMembers"
                  :key="member.id"
                  :label="member.name"
                  :value="member.id"
                />
              </el-select>
              <el-select v-model="child.parent_type" placeholder="作为">
                <el-option label="儿子" value="father" />
                <el-option label="女儿" value="mother" />
              </el-select>
              <el-select v-model="child.relation_nature" placeholder="性质">
                <el-option label="亲生" value="qin" />
                <el-option label="继亲" value="ji" />
                <el-option label="养亲" value="yang" />
                <el-option label="义亲" value="yi" />
              </el-select>
              <el-button
                v-if="familyForm.children.length > 1"
                @click="removeChild(index)"
                text
                type="danger"
                size="small"
              >删除</el-button>
            </div>
            <el-button @click="addChild" text type="primary" size="small">
              + 添加子女
            </el-button>
          </div>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showEditFamily = false">取消</el-button>
        <el-button @click="submitFamily" type="primary">保存</el-button>
      </template>
    </el-dialog>

  </div>
</template>

<script setup>
import { ref, onMounted, reactive, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { User, MapLocation, Edit } from '@element-plus/icons-vue'
import { getPerson, getPersonEvents, getPersonReminders, getPersonDetail, updatePersonFamily, getPersons, updatePerson } from '@/api/persons'
import { getCountries } from '@/api/countries'
import { ElMessage } from 'element-plus'

const router = useRouter()
const route = useRoute()
const personId = parseInt(route.params.id)

const personInfo = ref({})
const events = ref([])
const reminders = ref([])
const family = ref({ parents: [], children: [] })
const activeTab = ref('events')
const countries = ref([])
const availableFamilyMembers = ref([])
const showEditFamily = ref(false)

const isEditing = ref(false)
const saving = ref(false)

const fathers = computed(() => {
  return family.value.parents.filter(p => p.parent_type === 'father')
})

const mothers = computed(() => {
  return family.value.parents.filter(p => p.parent_type === 'mother')
})

const getRelationLabel = (parent) => {
  const typeLabel = parent.parent_type === 'father' ? '父' : '母'
  const natureMap = {
    qin: `亲生${typeLabel}`,
    ji: `继${typeLabel}`,
    yang: `养${typeLabel}`,
    yi: `义${typeLabel}`
  }
  return natureMap[parent.relation_nature] || `${typeLabel}(${parent.relation_nature})`
}

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

const familyForm = reactive({
  parents: [],
  children: []
})

const usedPersonIds = computed(() => {
  const ids = new Set()
  familyForm.parents.forEach(p => { if (p.person_id) ids.add(p.person_id) })
  familyForm.children.forEach(c => { if (c.person_id) ids.add(c.person_id) })
  return ids
})

const availableParentOptions = computed(() => {
  return availableFamilyMembers.value.filter(m => !usedPersonIds.value.has(m.id))
})

const availableChildOptions = computed(() => {
  return availableFamilyMembers.value.filter(m => !usedPersonIds.value.has(m.id))
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

const saveEdit = async () => {
  saving.value = true
  try {
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

const getMemberName = (memberId) => {
  const member = availableFamilyMembers.value.find(m => m.id === memberId)
  return member ? member.name : '未知'
}

const addParent = () => {
  familyForm.parents.push({ person_id: null, parent_type: 'father', relation_nature: 'qin' })
}

const removeParent = (index) => {
  familyForm.parents.splice(index, 1)
}

const addChild = () => {
  familyForm.children.push({ person_id: null, parent_type: 'father', relation_nature: 'qin' })
}

const removeChild = (index) => {
  familyForm.children.splice(index, 1)
}

const initFamilyForm = () => {
  familyForm.parents = family.value.parents.map(p => ({
    person_id: p.person_id,
    parent_type: p.parent_type,
    relation_nature: p.relation_nature
  }))
  if (familyForm.parents.length === 0) {
    familyForm.parents.push({ person_id: null, parent_type: 'father', relation_nature: 'qin' })
  }
  familyForm.children = family.value.children.map(c => ({
    person_id: c.person_id,
    parent_type: c.parent_type,
    relation_nature: c.relation_nature
  }))
  if (familyForm.children.length === 0) {
    familyForm.children.push({ person_id: null, parent_type: 'father', relation_nature: 'qin' })
  }
}

const submitFamily = async () => {
  try {
    const parentsData = familyForm.parents
      .filter(p => p.person_id)
      .map(p => ({
        id: p.person_id,
        parent_type: p.parent_type,
        relation_nature: p.relation_nature
      }))

    const childrenData = familyForm.children
      .filter(c => c.person_id)
      .map(c => ({
        id: c.person_id,
        parent_type: c.parent_type,
        relation_nature: c.relation_nature
      }))

    await updatePersonFamily(personId, {
      parents: parentsData,
      children: childrenData
    })

    showEditFamily.value = false
    await loadData()

    ElMessage.success('关系更新成功')
  } catch (error) {
    console.error('更新关系失败:', error)
    ElMessage.error('更新关系失败')
  }
}

const loadData = async () => {
  try {
    const [personData, eventsData, remindersData, countriesData, personsData] = await Promise.all([
      getPersonDetail(personId),
      getPersonEvents(personId),
      getPersonReminders(personId),
      getCountries(),
      getPersons()
    ])

    personInfo.value = personData
    family.value = personData.family
    events.value = eventsData
    reminders.value = remindersData
    countries.value = countriesData
    
    availableFamilyMembers.value = personsData.map(p => ({
      id: p.id,
      name: p.nickname || `${p.last_name}${p.first_name}`
    })).filter(p => p.id !== personId)
  } catch (error) {
    console.error('获取人物信息失败:', error)
  }
}

onMounted(async () => {
  await loadData()
})

watch(showEditFamily, (val) => {
  if (val) {
    initFamilyForm()
  }
})
</script>

<style scoped>
.person-detail {
  min-height: 100vh;
  background: #f5f7fa;
}

.person-name {
  font-size: 24px;
  font-weight: bold;
  margin-right: 12px;
}

.detail-content {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.info-section {
  background: white;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 20px;
  display: flex;
  gap: 32px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.avatar-container {
  position: relative;
}

.avatar {
  width: 160px;
  height: 160px;
  border-radius: 50%;
  object-fit: cover;
  border: 4px solid #409EFF;
}

.avatar-placeholder {
  width: 160px;
  height: 160px;
  border-radius: 50%;
  background: #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 4px solid #409EFF;
}

.avatar-icon {
  color: #409EFF;
}

.deceased-marker {
  position: absolute;
  bottom: 4px;
  right: 4px;
  width: 32px;
  height: 32px;
  background: #666;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 12px;
}

.basic-info {
  flex: 1;
}

.info-row {
  display: flex;
  justify-content: space-between;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.info-row:last-child {
  border-bottom: none;
}

.info-row .label {
  color: #999;
  font-size: 14px;
}

.info-row .value {
  color: #333;
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
  color: #999;
  margin-right: 8px;
}

.custom-field-value {
  color: #333;
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

.custom-field-name {
  flex: 1;
}

.custom-field-value {
  flex: 2;
}

.relations-section {
  background: white;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
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
}

.relations-content {
  display: flex;
  gap: 40px;
}

.relation-group {
  flex: 1;
}

.relation-group h4 {
  font-size: 14px;
  color: #666;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 2px solid #f0f0f0;
}

.relation-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.relation-item {
  padding: 12px;
  background: #f8f9fa;
  border-radius: 8px;
}

.relation-item.clickable:hover {
  cursor: pointer;
  background: #e8f4fd;
}

.relation-name {
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.relation-type {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

.nature-tag {
  background: #fff3e0;
  color: #fa8c16;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  margin-left: 8px;
}

.empty {
  color: #999;
  font-size: 13px;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 8px;
  text-align: center;
}

.tabs-section {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.detail-tabs {
  margin-top: 16px;
}

.tab-content {
  padding: 16px 0;
}

.event-list {
  margin-top: 16px;
}

.event-card {
  margin-bottom: 16px;
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
}

.event-type-tag {
  font-size: 11px;
}

.event-description {
  color: #666;
  font-size: 13px;
  margin: 0;
  line-height: 1.6;
}

.event-location {
  display: flex;
  align-items: center;
  color: #999;
  font-size: 12px;
  margin-top: 8px;
  gap: 4px;
}

.reminder-list {
  margin-top: 16px;
}

.reminder-item {
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
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

.multi-relation-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
}

.multi-relation-row {
  display: flex;
  gap: 8px;
  align-items: center;
}

.multi-relation-row .el-select {
  flex: 1;
  min-width: 0;
}
</style>