<template>
  <div class="persons-container">
    <div class="persons-header">
      <h2 class="page-title">人物列表</h2>
      <el-button type="primary" @click="handleCreate">
        <el-icon><Plus /></el-icon>
        添加人物
      </el-button>
    </div>
    
    <el-card class="search-card">
      <div class="search-filters">
        <el-input
          v-model="searchQuery"
          placeholder="搜索人物姓名、昵称"
          clearable
          class="search-input"
          @clear="handleSearch"
          @keyup.enter="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        
        <el-select
          v-model="filterGroup"
          placeholder="选择分组"
          clearable
          class="filter-select"
          @change="handleSearch"
        >
          <el-option
            v-for="group in groups"
            :key="group.id"
            :label="group.name"
            :value="group.id"
          >
            <span class="group-option-content">
              <span
                class="group-color-indicator"
                :style="{ backgroundColor: group.color }"
              ></span>
              <span class="group-option-name">{{ group.name }}</span>
            </span>
          </el-option>
        </el-select>
        
        <el-select
          v-model="filterGender"
          placeholder="性别"
          clearable
          class="filter-select"
          @change="handleSearch"
        >
          <el-option label="男" :value="1" />
          <el-option label="女" :value="2" />
          <el-option label="未知" :value="0" />
        </el-select>
        
        <el-select
          v-model="filterIsAlive"
          placeholder="状态"
          clearable
          class="filter-select"
          @change="handleSearch"
        >
          <el-option label="在世" :value="true" />
          <el-option label="已故" :value="false" />
        </el-select>
        
        <el-button type="primary" @click="handleSearch">
          <el-icon><Search /></el-icon>
          搜索
        </el-button>
        
        <el-button @click="handleReset">
          <el-icon><RefreshRight /></el-icon>
          重置
        </el-button>
      </div>
    </el-card>
    
    <div v-loading="loading" class="persons-grid">
      <el-card
        v-for="person in persons"
        :key="person.id"
        class="person-card"
        @click="handleView(person.id)"
      >
        <div class="person-avatar">
          <el-avatar :size="80" :src="person.avatar_url">
            {{ person.nickname || person.first_name || '?' }}
          </el-avatar>
        </div>
        
        <div class="person-info">
          <div class="person-name">
            {{ person.last_name }}{{ person.first_name }}
          </div>
          <div v-if="person.nickname" class="person-nickname">
            {{ person.nickname }}
          </div>
          <div class="person-tags">
            <el-tag v-if="person.is_me" type="primary" size="small">我</el-tag>
            <el-tag v-if="person.gender === 1" type="success" size="small">男</el-tag>
            <el-tag v-else-if="person.gender === 2" type="danger" size="small">女</el-tag>
            <el-tag v-if="person.death_date" type="info" size="small">已故</el-tag>
          </div>
        </div>
        
        <div class="person-actions">
          <el-button
            v-if="!person.is_me"
            type="danger"
            text
            size="small"
            @click.stop="handleDelete(person.id)"
          >
            删除
          </el-button>
        </div>
      </el-card>
      
      <el-empty v-if="!loading && persons.length === 0" description="暂无人物" />
    </div>
    
    <PersonForm
      v-model:visible="formVisible"
      :person-id="editingPersonId"
      @success="handleFormSuccess"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Plus, Search, RefreshRight } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getPersons, deletePerson } from '@/api/persons'
import { getGroups } from '@/api/groups'
import { searchPersons } from '@/api/search'
import PersonForm from '@/components/PersonForm.vue'

const router = useRouter()

const loading = ref(false)
const persons = ref([])
const groups = ref([])

// 搜索和过滤
const searchQuery = ref('')
const filterGroup = ref(null)
const filterGender = ref(null)
const filterIsAlive = ref(null)

const formVisible = ref(false)
const editingPersonId = ref(null)

const loadGroups = async () => {
  try {
    groups.value = await getGroups()
  } catch (error) {
    console.error('加载分组失败', error)
  }
}

const loadPersons = async () => {
  loading.value = true
  try {
    // 如果有任何过滤条件，使用搜索API
    if (searchQuery.value || filterGroup.value !== null || filterGender.value !== null || filterIsAlive.value !== null) {
      const response = await searchPersons(searchQuery.value, {
        group_id: filterGroup.value,
        gender: filterGender.value,
        is_alive: filterIsAlive.value
      })
      persons.value = response
    } else {
      // 否则使用普通列表API
      const response = await getPersons({
        skip: 0,
        limit: 100
      })
      persons.value = response
    }
  } catch (error) {
    ElMessage.error('加载人物列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  loadPersons()
}

const handleReset = () => {
  searchQuery.value = ''
  filterGroup.value = null
  filterGender.value = null
  filterIsAlive.value = null
  loadPersons()
}

const handleCreate = () => {
  editingPersonId.value = null
  formVisible.value = true
}

const handleEdit = (id) => {
  editingPersonId.value = id
  formVisible.value = true
}

const handleView = (id) => {
  router.push(`/persons/${id}`)
}

const handleDelete = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除这个人物吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await deletePerson(id)
    ElMessage.success('删除成功')
    loadPersons()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const handleFormSuccess = () => {
  formVisible.value = false
  loadPersons()
}

onMounted(() => {
  loadGroups()
  loadPersons()
})
</script>

<style scoped lang="scss">
.persons-container {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
}

.persons-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-title {
  font-size: 24px;
  font-weight: 500;
  color: #303133;
}

.search-card {
  margin-bottom: 24px;
  
  :deep(.el-card__body) {
    padding: 16px;
  }
}

.search-filters {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}

.search-input {
  width: 280px;
}

.filter-select {
  width: 140px;
}

.group-option-content {
  display: flex;
  align-items: center;
  gap: 8px;
}

.group-color-indicator {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  flex-shrink: 0;
}

.group-option-name {
  flex: 1;
}

.persons-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
  min-height: 400px;
}

.person-card {
  cursor: pointer;
  transition: all 0.3s;
  
  &:hover {
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
    transform: translateY(-2px);
  }
  
  :deep(.el-card__body) {
    padding: 24px;
    display: flex;
    flex-direction: column;
    align-items: center;
  }
}

.person-avatar {
  margin-bottom: 16px;
}

.person-info {
  text-align: center;
  flex: 1;
  width: 100%;
}

.person-name {
  font-size: 18px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 4px;
}

.person-nickname {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}

.person-tags {
  display: flex;
  justify-content: center;
  gap: 4px;
  flex-wrap: wrap;
  
  .el-tag {
    margin: 0;
  }
}

.person-actions {
  display: flex;
  gap: 8px;
  margin-top: 16px;
}
</style>
