<template>
  <div class="person-detail">
    <!-- 顶部导航栏 -->
    <div class="top-nav">
      <el-button @click="goBack" text class="back-btn">
        <el-icon><ArrowLeft /></el-icon>
        <span>返回</span>
      </el-button>
    </div>

    <!-- key 跟随人物 id：详情页是同一路由组件复用，切换人物时强制各分区重新挂载拉取数据 -->
    <div class="detail-content" :key="personId">
      <!-- 人物信息卡片 -->
      <PersonInfoCard
        :person-id="personId"
        @refresh="loadSharedData"
      />

      <!-- 所属分组 -->
      <PersonGroups :person-id="personId" />

      <!-- 家庭关系 -->
      <PersonRelations :person-id="personId" />

      <!-- 社会关系 -->
      <PersonSocialRelations :person-id="personId" />

      <!-- 交往记录 -->
      <PersonContactRecords :person-id="personId" @refresh="loadSharedData" />

      <!-- 事件与提醒（双列） -->
      <div class="events-reminders-grid">
        <PersonEvents :person-id="personId" />
        <PersonReminders :person-id="personId" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, provide, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'
import { usePerson } from './composables/usePerson'
import PersonInfoCard from './components/PersonInfoCard.vue'
import PersonGroups from './components/PersonGroups.vue'
import PersonRelations from './components/PersonRelations.vue'
import PersonSocialRelations from './components/PersonSocialRelations.vue'
import PersonContactRecords from './components/PersonContactRecords.vue'
import PersonEvents from './components/PersonEvents.vue'
import PersonReminders from './components/PersonReminders.vue'

const route = useRoute()
const router = useRouter()
const personId = computed(() => parseInt(route.params.id))

// 加载共享数据
const shared = usePerson(personId.value)

// 暴露给模板的刷新方法
const loadSharedData = (id) => {
  shared.loadSharedData(id ?? personId.value)
}

// 同一路由组件内切换人物（点击家庭/社会关系人物）：重载共享数据并回到页首
watch(personId, (newId) => {
  shared.loadSharedData(newId)
  window.scrollTo({ top: 0 })
})

// 通过 provide 共享给子组件
provide('personShared', {
  personInfo: shared.personInfo,
  countries: shared.countries,
  eventTypes: shared.eventTypes,
  allGroups: shared.allGroups,
  availablePersons: shared.availablePersons,
  loadSharedData
})

const goBack = () => {
  router.back()
}
</script>

<style scoped>
.person-detail {
  min-height: 100vh;
  background: var(--bg-color, #f5f7fa);
}

.top-nav {
  max-width: 1200px;
  margin: 0 auto;
  padding: 16px 20px 0;
}

.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 14px;
  color: var(--text-secondary, #909399);
  padding: 4px 8px;
}

.back-btn:hover {
  color: var(--primary-color, #409EFF);
  background: var(--bg-color-light, #f5f7fa);
}

.detail-content {
  padding: 16px 20px 40px;
  max-width: 1200px;
  margin: 0 auto;
}

.events-reminders-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-top: 24px;
}

@media (max-width: 768px) {
  .top-nav {
    padding: 10px 12px 0;
  }

  .detail-content {
    padding: 10px 12px 32px;
  }

  .events-reminders-grid {
    grid-template-columns: 1fr;
    gap: 0;
    margin-top: 16px;
  }
}
</style>
