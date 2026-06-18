<template>
  <el-dialog
    :model-value="visible"
    @update:model-value="$emit('update:visible', $event)"
    title="添加成员"
    width="600px"
  >
    <el-input
      v-model="searchQuery"
      placeholder="搜索人物"
      clearable
      class="member-search"
    >
      <template #prefix>
        <el-icon><Search /></el-icon>
      </template>
    </el-input>

    <div v-loading="loading" class="persons-list">
      <el-checkbox-group v-model="selected">
        <el-checkbox
          v-for="person in filteredPersons"
          :key="person.id"
          :value="person.id"
          class="person-checkbox"
        >
          <div class="person-option">
            <el-avatar :size="32" :src="person.avatar_url">
              {{ getInitial(person) }}
            </el-avatar>
            <span class="person-name">{{ getDisplayName(person) }}</span>
            <span v-if="getSecondaryName(person)" class="person-nickname">
              ({{ getSecondaryName(person) }})
            </span>
          </div>
        </el-checkbox>
      </el-checkbox-group>

      <el-empty v-if="filteredPersons.length === 0" description="没有可用的人物" />
    </div>

    <template #footer>
      <el-button @click="$emit('update:visible', false)">取消</el-button>
      <el-button type="primary" :loading="saving" @click="$emit('save', [...selected])">添加</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { Search } from '@element-plus/icons-vue'

const props = defineProps({
  visible: { type: Boolean, default: false },
  persons: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  saving: { type: Boolean, default: false }
})

const emit = defineEmits(['update:visible', 'save'])

const searchQuery = ref('')
const selected = ref([])

watch(
  () => props.visible,
  (val) => {
    if (val) {
      selected.value = []
      searchQuery.value = ''
    }
  }
)

const filteredPersons = computed(() => {
  if (!searchQuery.value) return props.persons
  const query = searchQuery.value.toLowerCase()
  return props.persons.filter(p =>
    (p.first_name && p.first_name.toLowerCase().includes(query)) ||
    (p.last_name && p.last_name.toLowerCase().includes(query)) ||
    (p.nickname && p.nickname.toLowerCase().includes(query))
  )
})

const getDisplayName = (person) => {
  const fullName = ((person.last_name || '') + (person.first_name || '')).trim()
  if (fullName) return fullName
  return person.nickname || '未知'
}

const getSecondaryName = (person) => {
  const fullName = ((person.last_name || '') + (person.first_name || '')).trim()
  if (fullName && person.nickname) return person.nickname
  return ''
}

const getInitial = (person) => {
  if (person.first_name && person.first_name.trim()) return person.first_name.trim()
  if (person.nickname && person.nickname.trim()) return person.nickname.trim()
  return '?'
}

const reset = () => {
  selected.value = []
  searchQuery.value = ''
}

defineExpose({ reset })
</script>

<style scoped>
.member-search {
  margin-bottom: 16px;
}

.member-search :deep(.el-input__wrapper) {
  background: var(--card-bg, #ffffff);
  box-shadow: 0 0 0 1px var(--border-color, #dcdfe6);
}

.member-search :deep(.el-input__inner) {
  color: var(--text-primary, #303133);
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
}

.person-checkbox:hover {
  background-color: var(--bg-color-light, #F5F7FA);
}

.person-checkbox :deep(.el-checkbox__label) {
  flex: 1;
}

.person-option {
  display: flex;
  align-items: center;
  gap: 12px;
}

.person-name {
  font-size: 14px;
  color: var(--text-primary, #303133);
}

.person-nickname {
  font-size: 12px;
  color: var(--text-secondary, #909399);
}
</style>
