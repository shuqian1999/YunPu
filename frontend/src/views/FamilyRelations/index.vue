<template>
  <div class="family-relations">
    <div class="page-header">
      <h2 class="page-title">家族关系</h2>
      <div class="page-meta" v-if="data">
        <el-tag type="info" effect="plain">共 {{ data.total }} 人</el-tag>
        <el-tag type="success" effect="plain" v-if="data.me">以「我」为中心</el-tag>
      </div>
    </div>

    <div v-if="loading" class="loading-state">
      <el-skeleton :rows="6" animated />
    </div>

    <el-empty
      v-else-if="!data || data.total === 0"
      description="暂未发现任何亲属关系。先到「人物管理」中创建人物并维护关系吧。"
    />

    <div v-else class="groups">
      <div
        v-for="group in data.groups"
        :key="group.generation_offset"
        class="group"
      >
        <div class="group-header" @click="toggleGroup(group.generation_offset)">
          <div class="group-title">
            <el-icon class="toggle-icon" :class="{ collapsed: collapsedGroups.has(group.generation_offset) }">
              <ArrowDown />
            </el-icon>
            <span class="group-label">{{ group.label }}</span>
            <span class="group-count">{{ group.count }} 人</span>
          </div>
        </div>

        <div
          v-show="!collapsedGroups.has(group.generation_offset)"
          class="group-body"
        >
          <div class="person-grid">
            <div
              v-for="person in group.persons"
              :key="person.id"
              class="person-card"
              @click="goToPerson(person.id)"
            >
              <el-avatar
                :size="56"
                :src="person.avatar_url"
                class="person-avatar"
              >
                <el-icon><UserFilled /></el-icon>
              </el-avatar>

              <div class="person-info">
                <div class="person-name">{{ person.name }}</div>
                <div class="person-relation">
                  <el-tag
                    size="small"
                    :type="getNatureTagType(person)"
                    effect="light"
                    class="relation-tag"
                  >
                    {{ getRelationLabel(person) }}
                  </el-tag>
                </div>
                <div class="person-meta" v-if="person.birth_date">
                  <el-icon><Calendar /></el-icon>
                  <span>{{ formatDate(person.birth_date) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowDown, UserFilled, Calendar } from '@element-plus/icons-vue'
import { getRelationsGrouped } from '@/api/family'

const router = useRouter()

const loading = ref(true)
const data = ref(null)
const collapsedGroups = ref(new Set())

const toggleGroup = (offset) => {
  if (collapsedGroups.value.has(offset)) {
    collapsedGroups.value.delete(offset)
  } else {
    collapsedGroups.value.add(offset)
  }
  // 触发响应式更新
  collapsedGroups.value = new Set(collapsedGroups.value)
}

const getRelationLabel = (person) => {
  // 血亲不显示"亲"前缀，只在非血亲时显示性质
  if (person.is_blood && person.relation_nature === 0) {
    return person.relation_name
  }
  const natureMap = { 0: '亲', 1: '继', 2: '养', 3: '义', 4: '干' }
  const nature = natureMap[person.relation_nature] || '亲'
  return `${nature}·${person.relation_name}`
}

const getNatureTagType = (person) => {
  if (person.is_blood && person.relation_nature === 0) return undefined
  if (person.relation_nature === 1) return 'info'      // 继
  if (person.relation_nature === 2) return 'success'   // 养
  if (person.relation_nature === 3) return 'warning'   // 义
  if (person.relation_nature === 4) return 'warning'   // 干
  return undefined
}

const formatDate = (isoDate) => {
  if (!isoDate) return ''
  return isoDate.substring(0, 10)
}

const goToPerson = (id) => {
  router.push(`/persons/${id}`)
}

const fetchData = async () => {
  loading.value = true
  try {
    const res = await getRelationsGrouped()
    data.value = res
  } catch (err) {
    console.error('获取家族关系失败', err)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped lang="scss">
.family-relations {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
  flex-wrap: wrap;
  gap: 12px;
}

.page-title {
  margin: 0;
  font-size: 22px;
  font-weight: 600;
  color: var(--text-primary, #303133);
}

.page-meta {
  display: flex;
  gap: 8px;
}

.loading-state {
  background: var(--card-bg, #fff);
  padding: 24px;
  border-radius: 8px;
}

.groups {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.group {
  background: var(--card-bg, #fff);
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
  transition: box-shadow 0.2s ease;

  &:hover {
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  }
}

.group-header {
  padding: 14px 20px;
  cursor: pointer;
  user-select: none;
  border-bottom: 1px solid var(--border-lighter, #EBEEF5);
  background: var(--bg-color-light, #fafbfc);

  &:hover {
    background: var(--bg-color-light-hover, #f0f2f5);
  }
}

.group-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.toggle-icon {
  transition: transform 0.2s ease;
  color: var(--text-secondary, #909399);
  font-size: 14px;

  &.collapsed {
    transform: rotate(-90deg);
  }
}

.group-label {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary, #303133);
}

.group-count {
  font-size: 13px;
  color: var(--text-secondary, #909399);
  margin-left: auto;
  background: var(--bg-color, #f5f7fa);
  padding: 2px 10px;
  border-radius: 10px;
}

.group-body {
  padding: 16px 20px 20px;
}

.person-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 12px;
}

.person-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 8px;
  background: var(--bg-color, #f8f9fb);
  cursor: pointer;
  transition: all 0.2s ease;
  border: 1px solid transparent;

  &:hover {
    background: var(--primary-color-light-9, #ecf5ff);
    border-color: var(--primary-color-light-5, #d9ecff);
    transform: translateY(-1px);
  }
}

.person-avatar {
  flex-shrink: 0;
  background: linear-gradient(135deg, #409EFF, #36cfc9);
  color: #fff;
}

.person-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.person-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary, #303133);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.person-relation {
  display: flex;
}

.relation-tag {
  font-size: 12px;
}

.person-meta {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--text-secondary, #909399);
}
</style>
