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
      <el-input
        v-model="searchQuery"
        placeholder="搜索人物姓名、昵称"
        clearable
        @clear="handleSearch"
        @keyup.enter="handleSearch"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
        <template #append>
          <el-button @click="handleSearch">搜索</el-button>
        </template>
      </el-input>
    </el-card>
    
    <div v-loading="loading" class="persons-grid">
      <el-card
        v-for="person in persons"
        :key="person.id"
        class="person-card"
        @click="handleView(person.id)"
      >
        <div class="person-avatar">
          <el-avatar :size="80">
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
          <div v-if="person.is_me" class="person-me-tag">
            <el-tag type="primary" size="small">我</el-tag>
          </div>
        </div>
        
        <div class="person-actions">
          <el-button
            type="primary"
            text
            size="small"
            @click.stop="handleEdit(person.id)"
          >
            编辑
          </el-button>
          <el-button
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
import { Plus, Search } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getPersons, deletePerson } from '@/api/persons'
import PersonForm from '@/components/PersonForm.vue'

const loading = ref(false)
const persons = ref([])
const searchQuery = ref('')
const formVisible = ref(false)
const editingPersonId = ref(null)

const loadPersons = async () => {
  loading.value = true
  try {
    const response = await getPersons({
      skip: 0,
      limit: 100,
      search: searchQuery.value || undefined
    })
    persons.value = response
  } catch (error) {
    ElMessage.error('加载人物列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
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
  console.log('查看人物', id)
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

.person-me-tag {
  margin-bottom: 8px;
}

.person-actions {
  display: flex;
  gap: 8px;
  margin-top: 16px;
}
</style>