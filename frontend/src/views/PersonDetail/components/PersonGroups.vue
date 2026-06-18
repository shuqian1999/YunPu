<template>
  <div class="groups-section">
    <div class="section-header">
      <h3 class="section-title">所属分组</h3>
      <el-button @click="showEditGroups = true" type="primary" size="small">
        <el-icon><Edit /></el-icon>
        编辑分组
      </el-button>
    </div>
    <div class="groups-content">
      <div v-if="personGroups.length === 0" class="empty">暂无分组</div>
      <div v-else class="groups-list">
        <el-tag
          v-for="group in personGroups"
          :key="group.id"
          :color="group.color"
          effect="dark"
          class="group-tag"
        >
          {{ group.name }}
        </el-tag>
      </div>
    </div>

    <el-dialog title="编辑分组" v-model="showEditGroups" width="500px">
      <el-checkbox-group v-model="selectedGroups" v-loading="groupsLoading">
        <div v-if="allGroups.length === 0" class="empty">暂无可用分组，请先创建分组</div>
        <el-checkbox
          v-for="group in allGroups"
          :key="group.id"
          :value="group.id"
          class="group-checkbox"
        >
          <el-tag :color="group.color" size="small" effect="dark">
            {{ group.name }}
          </el-tag>
          <span v-if="group.description" class="group-desc">{{ group.description }}</span>
        </el-checkbox>
      </el-checkbox-group>
      <template #footer>
        <el-button @click="showEditGroups = false">取消</el-button>
        <el-button type="primary" @click="handleSaveGroups">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, inject, watch, onMounted, computed } from 'vue'
import { Edit } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { addPersonToGroup, removePersonFromGroup, getPersonGroups } from '@/api/groups'

const props = defineProps({
  personId: { type: Number, required: true }
})

const shared = inject('personShared', null)
const allGroups = computed(() => shared?.allGroups?.value || [])

const personGroups = ref([])
const selectedGroups = ref([])
const showEditGroups = ref(false)
const groupsLoading = ref(false)

const loadPersonGroups = async () => {
  try {
    const data = await getPersonGroups(props.personId)
    personGroups.value = data
  } catch (error) {
    console.error('获取人物分组失败:', error)
  }
}

watch(showEditGroups, (val) => {
  if (val) {
    selectedGroups.value = personGroups.value.map(g => g.id)
  }
})

const handleSaveGroups = async () => {
  try {
    const currentGroupIds = personGroups.value.map(g => g.id)
    const newGroupIds = selectedGroups.value

    const toAdd = newGroupIds.filter(id => !currentGroupIds.includes(id))
    const toRemove = currentGroupIds.filter(id => !newGroupIds.includes(id))

    for (const groupId of toAdd) {
      await addPersonToGroup(groupId, props.personId)
    }

    for (const groupId of toRemove) {
      await removePersonFromGroup(groupId, props.personId)
    }

    personGroups.value = allGroups.value.filter(g => newGroupIds.includes(g.id))

    showEditGroups.value = false
    ElMessage.success('分组更新成功')
  } catch (error) {
    console.error('更新分组失败:', error)
    ElMessage.error('更新分组失败')
  }
}

onMounted(() => {
  loadPersonGroups()
})
</script>

<style scoped>
.groups-section {
  background: var(--card-bg, white);
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 20px;
  box-shadow: var(--box-shadow, 0 2px 12px rgba(0, 0, 0, 0.08));
  border: 1px solid var(--border-color, #dcdfe6);
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
  color: var(--text-primary, #303133);
}

.groups-content .groups-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.group-tag {
  margin: 0;
}

.group-checkbox {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
  width: 100%;
}

.group-checkbox .group-desc {
  margin-left: 8px;
  color: var(--text-secondary, #909399);
  font-size: 12px;
}

.empty {
  color: var(--text-secondary, #999);
  font-size: 13px;
  padding: 12px;
  background: var(--bg-color-light, #f8f9fa);
  border-radius: 8px;
  text-align: center;
}
</style>
