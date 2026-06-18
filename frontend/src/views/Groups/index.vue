<template>
  <div class="page-container">
    <div class="page-header">
      <div class="page-header-left">
        <h2 class="page-title">分组管理</h2>
        <span class="page-subtitle">共 {{ groups.length }} 个分组</span>
      </div>
      <div class="page-header-right">
        <el-button type="primary" @click="handleCreate">
          <el-icon><Plus /></el-icon>
          新建分组
        </el-button>
      </div>
    </div>

    <div v-loading="loading" class="groups-list">
      <el-empty v-if="!loading && groups.length === 0" description="暂无分组" />

      <GroupCard
        v-for="group in groups"
        :key="group.id"
        :group="group"
        :members="getGroupMembersFromState(group.id)"
        @edit="handleEdit"
        @delete="handleDelete"
        @add-member="handleAddMember"
        @remove-member="handleRemoveMember"
      />
    </div>

    <GroupFormDialog
      v-model:visible="formVisible"
      :group="editingGroup"
      :saving="saving"
      @save="handleSave"
    />

    <AddMemberDialog
      v-model:visible="memberDialogVisible"
      :persons="persons"
      :loading="personsLoading"
      :saving="addingMembers"
      @save="handleSaveMembers"
    />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getGroups,
  createGroup,
  updateGroup,
  deleteGroup,
  addPersonToGroup,
  removePersonFromGroup,
  getGroupMembers
} from '@/api/groups'
import { getPersons } from '@/api/persons'
import GroupCard from './components/GroupCard.vue'
import GroupFormDialog from './components/GroupFormDialog.vue'
import AddMemberDialog from './components/AddMemberDialog.vue'

const loading = ref(false)
const groups = ref([])
const persons = ref([])
const groupMembers = reactive({})

const formVisible = ref(false)
const editingGroup = ref(null)
const saving = ref(false)

const memberDialogVisible = ref(false)
const currentGroupId = ref(null)
const personsLoading = ref(false)
const addingMembers = ref(false)

const loadGroups = async () => {
  loading.value = true
  try {
    groups.value = await getGroups()
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
    groupMembers[groupId] = members
  } catch (error) {
    console.error('加载分组成员失败:', error)
    groupMembers[groupId] = []
  }
}

const loadPersons = async () => {
  personsLoading.value = true
  try {
    persons.value = await getPersons({ skip: 0, limit: 1000 })
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
  formVisible.value = true
}

const handleEdit = (group) => {
  editingGroup.value = group
  formVisible.value = true
}

const handleSave = async (formData) => {
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
  memberDialogVisible.value = true
  await loadPersons()
}

const handleSaveMembers = async (personIds) => {
  if (personIds.length === 0) {
    ElMessage.warning('请选择要添加的成员')
    return
  }

  addingMembers.value = true
  try {
    for (const personId of personIds) {
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

<style scoped>
.groups-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
</style>
