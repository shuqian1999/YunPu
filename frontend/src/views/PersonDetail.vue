<template>
  <div class="person-detail">
    <el-page-header @back="goBack">
      <template #content>
        <span class="person-name">{{ personInfo.nickname || (personInfo.last_name + personInfo.first_name) }}</span>
        <el-tag v-if="personInfo.is_me" type="primary" size="small">我</el-tag>
        <el-tag v-if="personInfo.gender === 'female'" type="success" size="small">女</el-tag>
        <el-tag v-else-if="personInfo.gender === 'male'" type="warning" size="small">男</el-tag>
      </template>
      <template #extra>
        <el-button @click="editPerson" type="primary" size="small">
          <el-icon><Edit /></el-icon>
          编辑
        </el-button>
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
            <span class="label">出生日期</span>
            <span class="value">{{ formatDate(personInfo.birth_date) }}</span>
          </div>
          <div class="info-row">
            <span class="label">逝世日期</span>
            <span class="value">{{ personInfo.death_date ? formatDate(personInfo.death_date) : '-' }}</span>
          </div>
          <div class="info-row">
            <span class="label">国籍</span>
            <span class="value">{{ getCountryName(personInfo.nationality) }}</span>
          </div>
          <div class="info-row">
            <span class="label">电话</span>
            <span class="value">{{ personInfo.phone || '-' }}</span>
          </div>
          <div class="info-row">
            <span class="label">邮箱</span>
            <span class="value">{{ personInfo.email || '-' }}</span>
          </div>
          <div class="info-row">
            <span class="label">地址</span>
            <span class="value">{{ personInfo.address || '-' }}</span>
          </div>
          <div class="info-row">
            <span class="label">备注</span>
            <span class="value">{{ personInfo.notes || '-' }}</span>
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
            <div v-if="family.father" class="relation-item clickable" @click="navigateToPerson(family.father.person_id)">
              <div class="relation-name">{{ family.father.name }}</div>
              <div class="relation-type">
                <span v-if="family.father.relation_nature !== 'qin'" class="nature-tag">
                  {{ family.father.relation_nature === 'ji' ? '继父' : '义父' }}
                </span>
              </div>
            </div>
            <div v-else class="empty">暂无父亲信息</div>
          </div>

          <div class="relation-group">
            <h4>母亲</h4>
            <div v-if="family.mother" class="relation-item clickable" @click="navigateToPerson(family.mother.person_id)">
              <div class="relation-name">{{ family.mother.name }}</div>
              <div class="relation-type">
                <span v-if="family.mother.relation_nature !== 'qin'" class="nature-tag">
                  {{ family.mother.relation_nature === 'ji' ? '继母' : '义母' }}
                </span>
              </div>
            </div>
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
                <el-list-item
                  v-for="reminder in reminders"
                  :key="reminder.id"
                  class="reminder-item"
                >
                  <el-list-item-meta>
                    <template #title>
                      <span class="reminder-title">{{ reminder.title }}</span>
                      <el-tag v-if="reminder.is_lunar" type="info" size="small">农历</el-tag>
                    </template>
                    <template #description>
                      <span class="reminder-date">{{ formatDate(reminder.remind_date) }}</span>
                    </template>
                  </el-list-item-meta>
                </el-list-item>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </div>

    <el-dialog title="编辑家族关系" v-model="showEditFamily" width="500px">
      <el-form :model="familyForm" label-width="100px">
        <el-form-item label="父亲">
          <el-select v-model="familyForm.father_id" placeholder="选择父亲">
            <el-option 
              v-for="member in availableFamilyMembers" 
              :key="member.id" 
              :label="member.name" 
              :value="member.id"
            />
          </el-select>
          <el-select 
            v-if="familyForm.father_id" 
            v-model="familyForm.father_relation_nature" 
            placeholder="关系性质"
          >
            <el-option label="亲生" value="qin" />
            <el-option label="继父" value="ji" />
            <el-option label="义父" value="yi" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="母亲">
          <el-select v-model="familyForm.mother_id" placeholder="选择母亲">
            <el-option 
              v-for="member in availableFamilyMembers" 
              :key="member.id" 
              :label="member.name" 
              :value="member.id"
            />
          </el-select>
          <el-select 
            v-if="familyForm.mother_id" 
            v-model="familyForm.mother_relation_nature" 
            placeholder="关系性质"
          >
            <el-option label="亲生" value="qin" />
            <el-option label="继母" value="ji" />
            <el-option label="义母" value="yi" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="子女">
          <el-select 
            v-model="familyForm.children" 
            multiple 
            placeholder="选择子女"
          >
            <el-option 
              v-for="member in availableFamilyMembers" 
              :key="member.id" 
              :label="member.name" 
              :value="member.id"
            />
          </el-select>
          <div v-if="familyForm.children.length > 0" class="children-nature">
            <div 
              v-for="childId in familyForm.children" 
              :key="childId"
              class="child-nature-item"
            >
              <span>{{ getMemberName(childId) }}</span>
              <el-select v-model="childRelationNatures[childId]">
                <el-option label="亲生" value="qin" />
                <el-option label="继" value="ji" />
                <el-option label="义" value="yi" />
              </el-select>
            </div>
          </div>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showEditFamily = false">取消</el-button>
        <el-button @click="submitFamily" type="primary">保存</el-button>
      </template>
    </el-dialog>

    <PersonForm
      v-model:visible="showEditPerson"
      :person-id="personId"
      @success="handleEditSuccess"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { User, MapLocation, Edit } from '@element-plus/icons-vue'
import { getPerson, getPersonEvents, getPersonReminders, getPersonDetail, updatePersonFamily, getPersons } from '@/api/persons'
import { getCountries } from '@/api/countries'
import PersonForm from '@/components/PersonForm.vue'

const router = useRouter()
const route = useRoute()
const personId = parseInt(route.params.id)

const personInfo = ref({})
const events = ref([])
const reminders = ref([])
const family = ref({ father: null, mother: null, children: [] })
const activeTab = ref('events')
const countries = ref([])
const availableFamilyMembers = ref([])
const showEditFamily = ref(false)
const showEditPerson = ref(false)

const familyForm = reactive({
  father_id: null,
  father_relation_nature: 'qin',
  mother_id: null,
  mother_relation_nature: 'qin',
  children: [],
  children_nature: {}
})

const childRelationNatures = reactive({})

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
  const country = countries.value.find(c => c.code === countryCode)
  return country ? country.name : countryCode
}

const navigateToPerson = (id) => {
  router.push(`/persons/${id}`)
}

const goBack = () => {
  router.back()
}

const editPerson = () => {
  showEditPerson.value = true
}

const handleEditSuccess = async () => {
  showEditPerson.value = false
  await loadData()
}

const getMemberName = (memberId) => {
  const member = availableFamilyMembers.value.find(m => m.id === memberId)
  return member ? member.name : '未知'
}

const initFamilyForm = () => {
  familyForm.father_id = family.value.father?.id || null
  familyForm.father_relation_nature = family.value.father?.relation_nature || 'qin'
  familyForm.mother_id = family.value.mother?.id || null
  familyForm.mother_relation_nature = family.value.mother?.relation_nature || 'qin'
  familyForm.children = family.value.children.map(c => c.id)
  
  family.value.children.forEach(child => {
    childRelationNatures[child.id] = child.relation_nature || 'qin'
  })
}

const submitFamily = async () => {
  try {
    const childrenData = familyForm.children.map(childId => ({
      id: childId,
      relation_nature: childRelationNatures[childId] || 'qin'
    }))
    
    await updatePersonFamily(personId, {
      father_id: familyForm.father_id,
      father_relation_nature: familyForm.father_relation_nature,
      mother_id: familyForm.mother_id,
      mother_relation_nature: familyForm.mother_relation_nature,
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

    personInfo.value = personData.person
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

.reminder-title {
  font-size: 14px;
  font-weight: 500;
  margin-right: 8px;
}

.reminder-date {
  color: #999;
  font-size: 13px;
}

.children-nature {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.child-nature-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #f8f9fa;
  border-radius: 6px;
}

.child-nature-item span {
  font-size: 13px;
}
</style>