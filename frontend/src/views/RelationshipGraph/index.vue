<template>
  <div class="relationship-page">
    <div class="page-header">
      <h2 class="page-title">关系图谱</h2>
      <div class="page-sub" v-if="mode === 'global'">
        全局 3D 链接图 · 仅展示直接关系 · 点击人物进入个人中心网络
      </div>
      <div class="page-sub" v-else>
        个人中心网络 · 以「{{ egoData?.center?.name }}」为中心的一级关系
      </div>
    </div>

    <!-- 全局模式 -->
    <template v-if="mode === 'global'">
      <div class="filter-bar">
        <span class="filter-label">关系类型</span>
        <el-checkbox-group v-model="filters.types" size="small" @change="scheduleLoad">
          <el-checkbox-button value="family">亲子</el-checkbox-button>
          <el-checkbox-button value="spouse">伴侣</el-checkbox-button>
          <el-checkbox-button value="social">社会</el-checkbox-button>
          <el-checkbox-button value="group">同分组</el-checkbox-button>
          <el-checkbox-button value="tag">同标签</el-checkbox-button>
        </el-checkbox-group>

        <span class="filter-label">重要度</span>
        <el-select v-model="filters.importanceMin" size="small" class="filter-select" @change="scheduleLoad">
          <el-option label="全部" :value="0" />
          <el-option label="≥ 2" :value="2" />
          <el-option label="≥ 3" :value="3" />
          <el-option label="≥ 4" :value="4" />
          <el-option label="仅 5（至亲）" :value="5" />
        </el-select>

        <el-switch
          v-model="filters.aliveOnly"
          active-text="仅在世"
          inline-prompt
          @change="scheduleLoad"
        />

        <el-input
          v-model="filters.keyword"
          size="small"
          class="filter-keyword"
          placeholder="按姓名筛选"
          clearable
          :prefix-icon="Search"
          @input="scheduleLoad"
          @clear="scheduleLoad"
        />

        <el-button size="small" :icon="Refresh" @click="loadGlobal">刷新</el-button>
      </div>

      <GlobalGraph3D :data="globalData" :loading="globalLoading" @select="enterEgo" />
    </template>

    <!-- 个人中心网络 -->
    <template v-else>
      <EgoNetwork
        :data="egoData"
        :loading="egoLoading"
        @back="backToGlobal"
        @recenter="enterEgo"
        @view-detail="goDetail"
      />
    </template>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Search, Refresh } from '@element-plus/icons-vue'
import { getRelationshipGraph, getEgoNetwork } from '@/api/relationships'
import GlobalGraph3D from './components/GlobalGraph3D.vue'
import EgoNetwork from './components/EgoNetwork.vue'

const router = useRouter()
const route = useRoute()

const mode = ref('global') // global | ego
const globalData = ref(null)
const globalLoading = ref(false)
const egoData = ref(null)
const egoLoading = ref(false)
let loadTimer = null

const filters = reactive({
  types: ['family', 'spouse', 'social', 'group'],
  importanceMin: 0,
  aliveOnly: false,
  keyword: ''
})

const scheduleLoad = () => {
  if (loadTimer) clearTimeout(loadTimer)
  loadTimer = setTimeout(loadGlobal, 320)
}

const loadGlobal = async () => {
  globalLoading.value = true
  try {
    globalData.value = await getRelationshipGraph({
      types: filters.types.length ? filters.types : ['family'],
      importanceMin: filters.importanceMin,
      aliveOnly: filters.aliveOnly,
      keyword: filters.keyword?.trim()
    })
  } catch (err) {
    console.error('加载关系图谱失败', err)
  } finally {
    globalLoading.value = false
  }
}

const enterEgo = async (personId) => {
  mode.value = 'ego'
  egoLoading.value = true
  try {
    egoData.value = await getEgoNetwork(personId)
    window.scrollTo({ top: 0 })
  } catch (err) {
    console.error('加载个人中心网络失败', err)
    egoData.value = null
  } finally {
    egoLoading.value = false
  }
}

const backToGlobal = () => {
  mode.value = 'global'
}

const goDetail = (id) => {
  router.push(`/persons/${id}`)
}

onMounted(() => {
  loadGlobal()
  // 支持 /relationships?ego=<人物id> 深链直接进入个人中心网络
  const egoId = Number(route.query.ego)
  if (egoId > 0) enterEgo(egoId)
})
onBeforeUnmount(() => {
  if (loadTimer) clearTimeout(loadTimer)
})
</script>

<style scoped lang="scss">
.relationship-page {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 16px;
}

.page-title {
  margin: 0;
  font-size: 22px;
  font-weight: 600;
  color: var(--text-primary, #303133);
}

.page-sub {
  margin-top: 6px;
  font-size: 13px;
  color: var(--text-secondary, #909399);
}

.filter-bar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  padding: 12px 16px;
  margin-bottom: 14px;
  background: var(--card-bg, #ffffff);
  border: 1px solid var(--border-color, #dcdfe6);
  border-radius: var(--radius-lg, 12px);
}

.filter-label {
  font-size: 13px;
  color: var(--text-secondary, #909399);
  font-weight: 500;
}

.filter-select {
  width: 132px;
}

.filter-keyword {
  width: 180px;
  margin-left: auto;
}

@media (max-width: 768px) {
  .filter-keyword {
    margin-left: 0;
    width: 100%;
  }
}
</style>
