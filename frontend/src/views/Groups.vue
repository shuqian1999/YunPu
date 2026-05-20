<template>
  <div class="groups-container">
    <div class="groups-header">
      <h2 class="page-title">分组管理</h2>
      <el-button type="primary" @click="handleCreate">
        <el-icon><Plus /></el-icon>
        新建分组
      </el-button>
    </div>

    <div v-loading="loading" class="groups-list">
      <el-empty v-if="!loading && groups.length === 0" description="暂无分组" />
      
      <el-card
        v-for="group in groups"
        :key="group.id"
        class="group-card"
      >
        <div class="group-header">
          <div class="group-info">
            <el-tag :color="group.color" effect="dark" class="group-color-tag">
              {{ group.name }}
            </el-tag>
            <span v-if="group.description" class="group-description">
              {{ group.description }}
            </span>
          </div>
          <div class="group-actions">
            <el-button type="primary" text size="small" @click="handleEdit(group)">
              <el-icon><Edit /></el-icon>
            </el-button>
            <el-button type="danger" text size="small" @click="handleDelete(group.id)">
              <el-icon><Delete /></el-icon>
            </el-button>
          </div>
        </div>
        
        <div class="group-members">
          <div class="members-header">
            <span class="members-title">成员列表</span>
            <el-button type="primary" link size="small" @click="handleAddMember(group.id)">
              <el-icon><Plus /></el-icon>
              添加成员
            </el-button>
          </div>
          
          <div v-if="getGroupMembersFromState(group.id).length > 0" class="members-list">
                  <el-tag
                    v-for="member in getGroupMembersFromState(group.id)"
              :key="member.id"
              closable
              class="member-tag"
              @close="handleRemoveMember(group.id, member.person_id)"
            >
              {{ member.person_name }}
            </el-tag>
          </div>
          <el-empty v-else description="暂无成员" :image-size="60" />
        </div>
      </el-card>
    </div>

    <!-- 分组表单对话框 -->
    <el-dialog
      v-model="formVisible"
      :title="editingGroup ? '编辑分组' : '新建分组'"
      width="500px"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="80px"
      >
        <el-form-item label="分组名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入分组名称" />
        </el-form-item>
        
        <el-form-item label="分组颜色" prop="color">
          <el-color-picker v-model="formData.color" show-alpha />
        </el-form-item>
        
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="formData.description"
            type="textarea"
            rows="3"
            placeholder="请输入分组描述（可选）"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="formVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">
          保存
        </el-button>
      </template>
    </el-dialog>

    <!-- 添加成员对话框 -->
    <el-dialog
      v-model="memberDialogVisible"
      title="添加成员"
      width="600px"
    >
      <el-input
        v-model="memberSearchQuery"
        placeholder="搜索人物"
        clearable
        class="member-search"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      
      <div v-loading="personsLoading" class="persons-list">
        <el-checkbox-group v-model="selectedPersons">
          <el-checkbox
            v-for="person in filteredPersons"
            :key="person.id"
            :label="person.id"
            class="person-checkbox"
          >
            <div class="person-option">
              <el-avatar :size="32" :src="person.avatar_url">
                {{ person.nickname || person.first_name || '?' }}
              </el-avatar>
              <span class="person-name">{{ person.last_name }}{{ person.first_name }}</span>
              <span v-if="person.nickname" class="person-nickname">({{ person.nickname }})</span>
            </div>
          </el-checkbox>
        </el-checkbox-group>
        
        <el-empty v-if="filteredPersons.length === 0" description="没有可用的人物" />
      </div>
      
      <template #footer>
        <el-button @click="memberDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="addingMembers" @click="handleSaveMembers">
          添加
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { Plus, Edit, Delete, Search } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getGroups, createGroup, updateGroup, deleteGroup, addPersonToGroup, removePersonFromGroup, getGroupMembers } from '@/api/groups'
import { getPersons } from '@/api/persons'

const loading = ref(false)
const groups = ref([])
const persons = ref([])
const groupMembers = reactive({}) // groupId -> members mapping

// 分组表单
const formVisible = ref(false)
const formRef = ref(null)
const editingGroup = ref(null)
const saving = ref(false)
const formData = reactive({
  name: '',
  color: '#409EFF',
  description: ''
})

const formRules = {
  name: [
    { required: true, message: '请输入分组名称', trigger: 'blur' },
    { max: 50, message: '分组名称不能超过50个字符', trigger: 'blur' }
  ]
}

// 成员管理
const memberDialogVisible = ref(false)
const currentGroupId = ref(null)
const memberSearchQuery = ref('')
const personsLoading = ref(false)
const selectedPersons = ref([])
const addingMembers = ref(false)

const filteredPersons = computed(() => {
  if (!memberSearchQuery.value) return persons.value
  const query = memberSearchQuery.value.toLowerCase()
  return persons.value.filter(p => 
    (p.first_name && p.first_name.toLowerCase().includes(query)) ||
    (p.last_name && p.last_name.toLowerCase().includes(query)) ||
    (p.nickname && p.nickname.toLowerCase().includes(query))
  )
})

const loadGroups = async () => {
  loading.value = true
  try {
    groups.value = await getGroups()
    // 加载每个分组的成员
    for (const group of groups.value) {
      await loadGroupMembers(group.id)
    }
  } catch (error) {
    ElMessage.error('加载分组列表失败')
  } finally {
    loading.value = false
  }
}

const loadGroupMembers = async (groupId) => {
  try {
    const members = await getGroupMembers(groupId)
    // reactive 对象可以直接赋值
    groupMembers[groupId] = members
    console.log(`加载分组成员成功，分组ID: ${groupId}，成员数: ${members.length}`)
  } catch (error) {
    console.error('加载分组成员失败:', error)
    groupMembers[groupId] = []
  }
}

const loadPersons = async () => {
  personsLoading.value = true
  try {
    const response = await getPersons({ skip: 0, limit: 1000 })
    persons.value = response
  } catch (error) {
    ElMessage.error('加载人物列表失败')
  } finally {
    personsLoading.value = false
  }
}

const getGroupMembersFromState = (groupId) => {
  return groupMembers[groupId] || []
}

const handleCreate = () => {
  editingGroup.value = null
  formData.name = ''
  formData.color = '#409EFF'
  formData.description = ''
  formVisible.value = true
}

const handleEdit = (group) => {
  editingGroup.value = group
  formData.name = group.name
  formData.color = group.color
  formData.description = group.description || ''
  formVisible.value = true
}

const handleSave = async () => {
  const valid = await formRef.value.validate()
  if (!valid) return

  saving.value = true
  try {
    if (editingGroup.value) {
      await updateGroup(editingGroup.value.id, formData)
      ElMessage.success('分组更新成功')
    } else {
      await createGroup(formData)
      ElMessage.success('分组创建成功')
    }
    formVisible.value = false
    loadGroups()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

const handleDelete = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除这个分组吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await deleteGroup(id)
    ElMessage.success('删除成功')
    loadGroups()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const handleAddMember = async (groupId) => {
  currentGroupId.value = groupId
  selectedPersons.value = []
  memberSearchQuery.value = ''
  await loadPersons()
  memberDialogVisible.value = true
}

const handleSaveMembers = async () => {
  if (selectedPersons.value.length === 0) {
    ElMessage.warning('请选择要添加的成员')
    return
  }

  addingMembers.value = true
  try {
    for (const personId of selectedPersons.value) {
      await addPersonToGroup(currentGroupId.value, personId)
    }
    ElMessage.success('成员添加成功')
    memberDialogVisible.value = false
    loadGroupMembers(currentGroupId.value)
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '添加成员失败')
  } finally {
    addingMembers.value = false
  }
}

const handleRemoveMember = async (groupId, personId) => {
  try {
    await ElMessageBox.confirm('确定要移除这个成员吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await removePersonFromGroup(groupId, personId)
    ElMessage.success('移除成功')
    loadGroupMembers(groupId)
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('移除失败')
    }
  }
}

onMounted(() => {
  loadGroups()
})
</script>

<style scoped lang="scss">
.groups-container {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
}

.groups-header {
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

.groups-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.group-card {
  :deep(.el-card__body) {
    padding: 20px;
  }
}

.group-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #EBEEF5;
}

.group-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.group-color-tag {
  font-size: 14px;
  padding: 6px 12px;
}

.group-description {
  color: #909399;
  font-size: 14px;
}

.group-actions {
  display: flex;
  gap: 8px;
}

.group-members {
  .members-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
  }
  
  .members-title {
    font-size: 14px;
    font-weight: 500;
    color: #606266;
  }
  
  .members-list {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }
  
  .member-tag {
    margin-right: 0;
  }
}

.member-search {
  margin-bottom: 16px;
}

.persons-list {
  max-height: 400px;
  overflow-y: auto;
}

.person-checkbox {
  display: flex;
  width: 100%;
  margin-right: 0;
  margin-bottom: 8px;
  padding: 8px;
  border-radius: 4px;
  
  &:hover {
    background-color: var(--bg-color, #F5F7FA);
  }
  
  :deep(.el-checkbox__label) {
    flex: 1;
  }
}

.person-option {
  display: flex;
  align-items: center;
  gap: 12px;
}

.person-name {
  font-size: 14px;
  color: #303133;
}

.person-nickname {
  font-size: 12px;
  color: #909399;
}
</style>
