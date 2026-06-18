<template>
  <div class="page-container-wide">
    <div class="page-header">
      <div class="page-header-left">
        <h2 class="page-title">人物列表</h2>
        <span class="page-subtitle">共 {{ persons.length }} 位人物</span>
      </div>
      <div class="page-header-right">
        <el-radio-group v-model="viewMode" size="default" class="view-switch">
          <el-radio-button value="card">
            <el-icon><Grid /></el-icon>
            卡片
          </el-radio-button>
          <el-radio-button value="list">
            <el-icon><List /></el-icon>
            列表
          </el-radio-button>
        </el-radio-group>
        <el-button type="primary" @click="handleCreate">
          <el-icon><Plus /></el-icon>
          添加人物
        </el-button>
      </div>
    </div>

    <el-card class="page-card search-card">
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
              <span class="group-color-indicator" :style="{ backgroundColor: group.color }"></span>
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

    <!-- 卡片视图 -->
    <div v-if="viewMode === 'card'" v-loading="loading" class="persons-grid">
      <PersonCard
        v-for="person in paginatedPersons"
        :key="person.id"
        :person="person"
        :get-country-name="getCountryName"
        :get-country-flag="getCountryFlag"
        :get-person-age-text="getPersonAgeText"
        :format-birthday="formatBirthday"
        @view="handleView"
        @delete="handleDelete"
      />
      <el-empty v-if="!loading && persons.length === 0" description="暂无人物" />
    </div>

    <!-- 列表视图 -->
    <PersonList
      v-else
      :persons="paginatedPersons"
      :loading="loading"
      :get-country-name="getCountryName"
      :get-country-flag="getCountryFlag"
      :get-person-age-text="getPersonAgeText"
      :format-birthday="formatBirthday"
      @view="handleView"
      @delete="handleDelete"
    />

    <el-pagination
      v-if="persons.length > 0"
      v-model:current-page="currentPage"
      v-model:page-size="pageSize"
      :page-sizes="[12, 24, 48, 96]"
      :total="persons.length"
      layout="total, sizes, prev, pager, next, jumper"
      class="pagination"
      background
    />

    <PersonForm
      v-model:visible="formVisible"
      :person-id="editingPersonId"
      @success="handleFormSuccess"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Plus, Search, RefreshRight, Grid, List } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getPersons, deletePerson } from '@/api/persons'
import { getGroups } from '@/api/groups'
import { searchPersons } from '@/api/search'
import { getCountries } from '@/api/countries'
import PersonForm from '@/components/PersonForm.vue'
import PersonCard from './components/PersonCard.vue'
import PersonList from './components/PersonList.vue'

const router = useRouter()

const loading = ref(false)
const persons = ref([])
const groups = ref([])
const countries = ref({})

const viewMode = ref('card')

const currentPage = ref(1)
const pageSize = ref(24)

const searchQuery = ref('')
const filterGroup = ref(null)
const filterGender = ref(null)
const filterIsAlive = ref(null)

const formVisible = ref(false)
const editingPersonId = ref(null)

const onViewModeChange = (val) => {
  pageSize.value = val === 'list' ? 48 : 24
  currentPage.value = 1
}

watch(viewMode, onViewModeChange)

watch([searchQuery, filterGroup, filterGender, filterIsAlive], () => {
  currentPage.value = 1
})

const loadGroups = async () => {
  try {
    groups.value = await getGroups()
  } catch (error) {
    console.error('加载分组失败', error)
  }
}

const loadCountries = async () => {
  try {
    countries.value = await getCountries()
  } catch (error) {
    console.error('加载国家数据失败', error)
  }
}

const getCountryName = (code) => {
  if (!code) return ''
  return countries.value[code]?.name || ''
}

const getCountryFlag = (code) => {
  if (!code) return ''
  return countries.value[code]?.flag || ''
}

const formatBirthday = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  if (isNaN(date.getTime())) return dateString
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

const loadPersons = async () => {
  loading.value = true
  try {
    if (searchQuery.value || filterGroup.value !== null || filterGender.value !== null || filterIsAlive.value !== null) {
      const response = await searchPersons(searchQuery.value, {
        group_id: filterGroup.value,
        gender: filterGender.value,
        is_alive: filterIsAlive.value
      })
      persons.value = response
    } else {
      const response = await getPersons({
        skip: 0,
        limit: 10000
      })
      persons.value = response
    }
  } catch (error) {
    ElMessage.error('加载人物列表失败')
  } finally {
    loading.value = false
  }
}

const paginatedPersons = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return persons.value.slice(start, start + pageSize.value)
})

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

const calculateAge = (birthDate, endDate) => {
  if (!birthDate) return null
  const birth = new Date(birthDate)
  const end = endDate ? new Date(endDate) : new Date()
  if (isNaN(birth.getTime()) || isNaN(end.getTime())) return null
  if (end < birth) return null

  let years = end.getFullYear() - birth.getFullYear()
  const monthDiff = end.getMonth() - birth.getMonth()
  const dayDiff = end.getDate() - birth.getDate()

  if (monthDiff < 0 || (monthDiff === 0 && dayDiff < 0)) {
    years--
  }

  if (years < 0) return 0
  return years
}

const getPersonAgeText = (person) => {
  if (person.birth_date) {
    const age = calculateAge(person.birth_date, person.death_date)
    if (age === null) return ''

    if (person.death_date) {
      return `${age}岁（已故）`
    }
    return `${age}岁`
  }
  return ''
}

onMounted(() => {
  loadGroups()
  loadCountries()
  loadPersons()
})
</script>

<style scoped>
.search-card {
  margin-bottom: 20px;
  border-radius: 12px;
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

.view-switch {
  margin-right: 12px;
}

.view-switch :deep(.el-radio-button__inner) {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.persons-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 16px;
  min-height: 380px;
  margin-bottom: 16px;
}

.pagination {
  display: flex;
  justify-content: center;
  margin-top: 20px;
  padding: 8px 0;
}
</style>
