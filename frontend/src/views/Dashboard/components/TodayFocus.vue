<template>
  <el-card class="page-card today-card" v-loading="loading">
    <template #header>
      <div class="today-header">
        <span class="today-title">
          <el-icon class="title-icon"><Sunny /></el-icon>
          今日关注
        </span>
        <span class="today-date">{{ todayText }}</span>
      </div>
    </template>

    <div class="focus-grid">
      <!-- 近期生日 -->
      <div class="focus-col">
        <div class="col-title">
          <el-icon><Present /></el-icon>
          <span>近期生日</span>
        </div>
        <div v-if="data.birthdays.length === 0" class="col-empty">近期暂无生日</div>
        <div
          v-for="item in data.birthdays"
          :key="`b-${item.person_id}`"
          class="focus-item"
          @click="goPerson(item.person_id)"
        >
          <PersonAvatar :name="item.name" :src="item.avatar_url" :size="36" />
          <div class="item-main">
            <div class="item-name">{{ item.name }}</div>
            <div class="item-sub">
              {{ formatDate(item.date) }}
              <el-tag v-if="item.is_lunar" size="small" type="warning" effect="plain">农历</el-tag>
            </div>
          </div>
          <el-tag :type="item.days_until === 0 ? 'danger' : 'info'" size="small">
            {{ item.days_until === 0 ? '今天' : `${item.days_until}天后` }}
          </el-tag>
        </div>
      </div>

      <!-- 近期提醒 -->
      <div class="focus-col">
        <div class="col-title">
          <el-icon><Bell /></el-icon>
          <span>待办提醒</span>
        </div>
        <div v-if="data.reminders.length === 0" class="col-empty">近期暂无提醒</div>
        <div
          v-for="item in data.reminders"
          :key="`r-${item.id}`"
          class="focus-item"
          :class="{ clickable: item.person_id }"
          @click="item.person_id && goPerson(item.person_id)"
        >
          <el-avatar :size="36" class="type-avatar" :style="{ background: item.event_type_color || '#909399' }">
            <el-icon><Bell /></el-icon>
          </el-avatar>
          <div class="item-main">
            <div class="item-name">{{ item.title }}</div>
            <div class="item-sub">{{ item.person_name || '通用提醒' }}</div>
          </div>
          <el-tag :type="item.days_until === 0 ? 'danger' : 'warning'" size="small">
            {{ item.days_until === 0 ? '今天' : `${item.days_until}天后` }}
          </el-tag>
        </div>
      </div>

      <!-- 久未联系 -->
      <div class="focus-col">
        <div class="col-title">
          <el-icon><ChatLineRound /></el-icon>
          <span>久未联系</span>
        </div>
        <div v-if="data.stale_contacts.length === 0" class="col-empty">关注的人近期都有联系</div>
        <div
          v-for="item in data.stale_contacts"
          :key="`s-${item.person_id}`"
          class="focus-item"
          @click="goPerson(item.person_id)"
        >
          <PersonAvatar :name="item.name" :src="item.avatar_url" :size="36" />
          <div class="item-main">
            <div class="item-name">{{ item.name }}</div>
            <div class="item-sub stale-sub" :class="staleLevel(item.days_since)">
              {{ item.never_contacted ? '还没有交往记录' : `已 ${item.days_since} 天未联系` }}
            </div>
          </div>
          <el-button type="primary" text size="small" @click.stop="goPerson(item.person_id)">
            去联系
          </el-button>
        </div>
      </div>
    </div>
  </el-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Sunny, Present, Bell, ChatLineRound } from '@element-plus/icons-vue'
import { getDashboardToday } from '@/api/dashboard'
import PersonAvatar from '@/components/PersonAvatar.vue'

const router = useRouter()
const loading = ref(false)
const data = ref({ birthdays: [], reminders: [], stale_contacts: [] })

const todayText = new Date().toLocaleDateString('zh-CN', {
  month: 'long',
  day: 'numeric',
  weekday: 'long'
})

const formatDate = (dateString) => {
  if (!dateString) return ''
  return new Date(dateString).toLocaleDateString('zh-CN', {
    month: 'long',
    day: 'numeric'
  })
}

const staleLevel = (days) => {
  if (days === null || days === undefined) return 'level-none'
  if (days >= 90) return 'level-high'
  if (days >= 60) return 'level-mid'
  return 'level-low'
}

const goPerson = (personId) => {
  if (personId) router.push(`/persons/${personId}`)
}

const load = async () => {
  loading.value = true
  try {
    data.value = await getDashboardToday()
  } catch (error) {
    console.error('加载今日关注失败:', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  load()
})
</script>

<style scoped>
.today-card {
  margin-bottom: 16px;
}

.today-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.today-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary, #303133);
}

.title-icon {
  color: var(--warning-color, #e6a23c);
}

.today-date {
  font-size: 13px;
  color: var(--text-secondary, #909399);
}

.focus-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.focus-col {
  min-width: 0;
}

.col-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-regular, #606266);
  margin-bottom: 12px;
}

.col-empty {
  font-size: 13px;
  color: var(--text-secondary, #909399);
  padding: 12px;
  text-align: center;
  background: var(--bg-color-light, #f8f9fa);
  border-radius: 8px;
}

.focus-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s ease;
}

.focus-item.clickable {
  cursor: pointer;
}

.focus-item:hover {
  background: var(--bg-color-light, #f5f7fa);
}

.item-main {
  flex: 1;
  min-width: 0;
}

.item-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary, #303133);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.item-sub {
  font-size: 12px;
  color: var(--text-secondary, #909399);
  margin-top: 2px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.type-avatar {
  color: #fff;
}

.stale-sub.level-high {
  color: var(--danger-color, #f56c6c);
  font-weight: 600;
}

.stale-sub.level-mid {
  color: var(--warning-color, #e6a23c);
}

.stale-sub.level-low {
  color: var(--text-secondary, #909399);
}

@media (max-width: 992px) {
  .focus-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }
}
</style>
