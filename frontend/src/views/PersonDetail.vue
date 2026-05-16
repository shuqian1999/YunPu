<template>
  <div class="person-detail">
    <el-page-header @back="goBack">
      <template #content>
        <span class="person-name">{{ personInfo.nickname || (personInfo.last_name + personInfo.first_name) }}</span>
        <el-tag v-if="personInfo.is_me" type="primary" size="small">我</el-tag>
        <el-tag v-if="personInfo.gender === 'female'" type="success" size="small">女</el-tag>
        <el-tag v-else-if="personInfo.gender === 'male'" type="warning" size="small">男</el-tag>
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
        <h3 class="section-title">家庭关系</h3>
        <div class="relations-content">
          <div class="relation-group">
            <h4>父母</h4>
            <div v-if="relations.parents && relations.parents.length === 0" class="empty">暂无父母信息</div>
            <div v-else-if="relations.parents" class="relation-list">
              <div
                v-for="parent in relations.parents"
                :key="parent.id"
                class="relation-item"
                @click="navigateToPerson(parent.person_id)"
              >
                <div class="relation-name">{{ parent.name }}</div>
                <div class="relation-type">
                  {{ parent.parent_type === 'father' ? '父亲' : '母亲' }}
                  <span v-if="parent.relation_nature !== 'qin'" class="nature-tag">
                    {{ parent.relation_nature === 'ji' ? '继' : '义' }}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <div class="relation-group">
            <h4>子女</h4>
            <div v-if="relations.children && relations.children.length === 0" class="empty">暂无子女信息</div>
            <div v-else-if="relations.children" class="relation-list">
              <div
                v-for="child in relations.children"
                :key="child.id"
                class="relation-item"
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
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { User, MapLocation } from '@element-plus/icons-vue'
import { getPerson, getPersonEvents, getPersonReminders, getPersonRelations } from '@/api/persons'
import { getCountries } from '@/api/countries'

const router = useRouter()
const route = useRoute()
const personId = parseInt(route.params.id)

const personInfo = ref({})
const events = ref([])
const reminders = ref([])
const relations = ref({ parents: [], children: [] })
const activeTab = ref('events')
const countries = ref([])

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

onMounted(async () => {
  try {
    const [personData, eventsData, remindersData, relationsData, countriesData] = await Promise.all([
      getPerson(personId),
      getPersonEvents(personId),
      getPersonReminders(personId),
      getPersonRelations(personId),
      getCountries()
    ])

    personInfo.value = personData
    events.value = eventsData
    reminders.value = remindersData
    relations.value = relationsData
    countries.value = countriesData
  } catch (error) {
    console.error('获取人物信息失败:', error)
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
  margin-bottom: 16px;
}

.info-row:last-child {
  margin-bottom: 0;
}

.label {
  width: 80px;
  color: #999;
  font-weight: 500;
}

.value {
  flex: 1;
  color: #333;
}

.relations-section {
  background: white;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.section-title {
  font-size: 18px;
  font-weight: bold;
  margin-bottom: 20px;
  color: #333;
}

.relations-content {
  display: flex;
  gap: 48px;
}

.relation-group h4 {
  font-size: 14px;
  color: #666;
  margin-bottom: 12px;
}

.relation-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.relation-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: #f8f9fa;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
}

.relation-item:hover {
  background: #eef2f7;
}

.relation-name {
  font-weight: 500;
}

.relation-type {
  font-size: 12px;
  color: #666;
}

.nature-tag {
  margin-left: 4px;
  color: #999;
}

.empty {
  color: #999;
  padding: 16px;
  text-align: center;
  background: #f8f9fa;
  border-radius: 8px;
}

.tabs-section {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.detail-tabs {
  height: 100%;
}

.tab-content {
  padding-top: 20px;
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
}

.event-description {
  color: #666;
  margin-bottom: 8px;
}

.event-location {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #999;
}

.reminder-item {
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.reminder-item:last-child {
  border-bottom: none;
}

.reminder-title {
  font-weight: 500;
}

.reminder-date {
  color: #999;
  font-size: 13px;
}
</style>