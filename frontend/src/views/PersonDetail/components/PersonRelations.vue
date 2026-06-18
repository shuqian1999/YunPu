<template>
  <div class="relations-section">
    <div class="section-header">
      <h3 class="section-title">家庭关系</h3>
      <el-button @click="showEditRelation = true" type="primary" size="small">
        <el-icon><Edit /></el-icon>
        编辑关系
      </el-button>
    </div>
    <div class="relations-content">
      <div v-if="relations.length === 0" class="empty">暂无关系信息</div>
      <div v-else class="relation-list">
        <div
          v-for="rel in relations"
          :key="rel.person_id"
          class="relation-item clickable"
          @click="navigateToPerson(rel.person_id)"
        >
          <div class="relation-main">
            <span class="relation-item-label" :class="getNatureTagClass(rel.relation_nature)">
              {{ rel.relation_nature > 0 ? getRelationNatureLabel(rel.relation_nature) : '亲' }}
            </span>
            <span class="relation-item-separator">·</span>
            <span class="relation-item-label" :class="getRelationTypeClass(rel.relation_name)">
              {{ rel.relation_name }}
            </span>
            <span class="relation-item-separator">·</span>
            <span class="relation-item-label relation-person">{{ rel.name }}</span>
          </div>
        </div>
      </div>
    </div>

    <el-dialog title="编辑家族关系" v-model="showEditRelation" width="600px">
      <div class="relation-edit-section">
        <h4>添加关系</h4>
        <el-form :model="relationForm" label-width="80px">
          <el-form-item label="关系类型">
            <el-radio-group v-model="relationForm.relationType">
              <el-radio value="family">家庭关系</el-radio>
              <el-radio value="spouse">配偶关系</el-radio>
            </el-radio-group>
          </el-form-item>

          <el-form-item label="选择人物">
            <el-select v-model="relationForm.person_b_id" placeholder="选择人物" filterable>
              <el-option
                v-for="p in availablePersons"
                :key="p.id"
                :label="p.name"
                :value="p.id"
              />
            </el-select>
          </el-form-item>

          <el-form-item label="关系">
            <el-select v-model="relationForm.relation">
              <el-option
                v-for="(label, value) in currentRelationLabels"
                :key="value"
                :label="label"
                :value="Number(value)"
              />
            </el-select>
          </el-form-item>

          <el-form-item label="关系性质">
            <el-select v-model="relationForm.relation_nature">
              <el-option
                v-for="(label, value) in currentNatureLabels"
                :key="value"
                :label="label"
                :value="Number(value)"
              />
            </el-select>
          </el-form-item>

          <el-form-item>
            <div class="relation-preview">
              <strong>{{ getRelationPreview() }}</strong>
            </div>
          </el-form-item>

          <el-form-item>
            <el-button type="primary" @click="handleAddRelation">添加关系</el-button>
          </el-form-item>
        </el-form>
      </div>

      <div class="relation-edit-section">
        <h4>现有关系</h4>
        <div v-if="relations.length === 0" class="empty">暂无关系</div>
        <div v-else class="existing-relations">
          <div
            v-for="rel in relations"
            :key="rel.person_id + '-' + rel.relation_type"
            class="existing-relation-item"
          >
            <div class="relation-info">
              <span class="relation-name">{{ rel.name }}</span>
              <span class="relation-type">{{ rel.relation_name }}</span>
              <span v-if="rel.relation_nature > 0" class="nature-tag secondary">
                {{ getRelationNatureLabel(rel.relation_nature) }}
              </span>
            </div>
            <el-button
              @click="handleDeleteRelation(rel)"
              text
              type="danger"
              size="small"
            >
              删除
            </el-button>
          </div>
        </div>
      </div>

      <template #footer>
        <el-button @click="showEditRelation = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, inject, computed, onMounted, watch } from 'vue'
import { Edit } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRouter } from 'vue-router'
import { getPersonRelations } from '@/api/persons'
import {
  createFamilyRelation, createSpouseRelation,
  deleteFamilyRelation, deleteSpouseRelation, getRelationNatureLabel
} from '@/api/family'

const props = defineProps({
  personId: { type: Number, required: true }
})

const shared = inject('personShared', null)
const personInfo = computed(() => shared?.personInfo?.value || {})
const availablePersons = computed(() => shared?.availablePersons?.value || [])

const router = useRouter()

const relations = ref([])
const showEditRelation = ref(false)
const relationForm = reactive({
  relationType: 'family',
  person_b_id: null,
  relation: 0,
  relation_nature: 0
})

// 关系枚举
const familyLabels = { 0: '父亲', 1: '母亲', 2: '儿子', 3: '女儿' }
const spouseLabels = { 0: '丈夫', 1: '妻子', 2: '姨太太', 3: '男朋友', 4: '女朋友' }
const familyNatureLabels = { 0: '亲（血亲）', 1: '继（继亲）', 2: '养（收养）', 3: '义（结义）', 4: '干（干亲）' }
const spouseNatureLabels = { 0: '现任', 1: '前任' }

const currentRelationLabels = computed(() => {
  return relationForm.relationType === 'family' ? familyLabels : spouseLabels
})

const currentNatureLabels = computed(() => {
  return relationForm.relationType === 'family' ? familyNatureLabels : spouseNatureLabels
})

// 切换关系类型时，重置关系和关系性质
watch(() => relationForm.relationType, () => {
  relationForm.relation = 0
  relationForm.relation_nature = 0
})

watch(showEditRelation, (val) => {
  if (val) {
    relationForm.person_b_id = null
    relationForm.relation = 0
    relationForm.relation_nature = 0
  }
})

const navigateToPerson = (id) => {
  router.push(`/persons/${id}`)
}

const getRelationPreview = () => {
  const currentPerson = personInfo.value
  const personB = availablePersons.value.find(p => p.id === relationForm.person_b_id)

  if (!currentPerson || !personB) {
    return '请选择人物以预览关系'
  }

  const relation = currentRelationLabels.value[relationForm.relation] || '未知'
  const currentName = currentPerson.nickname || ((currentPerson.last_name || '') + (currentPerson.first_name || ''))
  return `${personB.name}，是${currentName}的${relation}`
}

const getRelationTypeClass = (relationName) => {
  const parentRelations = ['父亲', '母亲', '爸爸', '妈妈']
  const childRelations = ['儿子', '女儿']
  const spouseRelations = ['丈夫', '妻子', '姨太太', '男朋友', '女朋友']

  if (parentRelations.includes(relationName)) return 'relation-parent'
  if (childRelations.includes(relationName)) return 'relation-child'
  if (spouseRelations.includes(relationName)) return 'relation-spouse'
  return 'relation-other'
}

const getNatureTagClass = (nature) => {
  if (nature === 0) return 'relation-nature-blood'
  if (nature === 1) return 'relation-nature-step'
  if (nature === 2) return 'relation-nature-adopt'
  if (nature === 3) return 'relation-nature-sworn'
  if (nature === 4) return 'relation-nature-god'
  return 'relation-nature-other'
}

const sortRelations = (rels) => {
  const orderMap = {
    '父亲': 1, '母亲': 1, '爸爸': 1, '妈妈': 1,
    '丈夫': 2, '妻子': 2, '姨太太': 2, '男朋友': 2, '女朋友': 2,
    '儿子': 3, '女儿': 3
  }

  return [...rels].sort((a, b) => {
    const aOrder = orderMap[a.relation_name] || 99
    const bOrder = orderMap[b.relation_name] || 99
    if (aOrder !== bOrder) {
      return aOrder - bOrder
    }
    return (a.name || '').localeCompare(b.name || '', 'zh-CN')
  })
}

const loadRelations = async () => {
  try {
    const res = await getPersonRelations(props.personId)
    relations.value = sortRelations(res)
  } catch (error) {
    console.error('获取关系失败:', error)
    relations.value = []
  }
}

const handleAddRelation = async () => {
  if (!relationForm.person_b_id) {
    ElMessage.warning('请选择人物')
    return
  }

  if (relationForm.person_b_id === props.personId) {
    ElMessage.warning('不能与自己建立关系')
    return
  }

  try {
    if (relationForm.relationType === 'family') {
      await createFamilyRelation(
        props.personId,
        relationForm.person_b_id,
        relationForm.relation,
        relationForm.relation_nature
      )
    } else {
      await createSpouseRelation(
        props.personId,
        relationForm.person_b_id,
        relationForm.relation,
        relationForm.relation_nature
      )
    }
    ElMessage.success('关系添加成功')
    await loadRelations()

    relationForm.person_b_id = null
    relationForm.relation = 0
    relationForm.relation_nature = 0
  } catch (error) {
    console.error('添加关系失败:', error)
    ElMessage.error('添加关系失败')
  }
}

const handleDeleteRelation = async (rel) => {
  try {
    await ElMessageBox.confirm(`确定要删除与 ${rel.name} 的关系吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    if (typeof rel.relation_type === 'string' && rel.relation_type.startsWith('spouse')) {
      await deleteSpouseRelation(props.personId, rel.person_id)
    } else {
      await deleteFamilyRelation(props.personId, rel.person_id)
    }
    ElMessage.success('关系删除成功')
    await loadRelations()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除关系失败:', error)
      ElMessage.error('删除关系失败')
    }
  }
}

onMounted(() => {
  loadRelations()
})
</script>

<style scoped>
.relations-section {
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

.relation-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.relation-item {
  padding: 12px;
  background: var(--bg-color-light, #f8f9fa);
  border-radius: 8px;
}

.relation-item.clickable:hover {
  cursor: pointer;
  background: rgba(64, 158, 255, 0.1);
}

.relation-main {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: nowrap;
  line-height: 1.5;
}

.relation-item-label {
  font-size: 14px;
  font-weight: 500;
}

.relation-item-separator {
  color: #ccc;
  font-size: 14px;
  margin: 0 2px;
}

.relation-person {
  color: var(--text-primary, #333);
  font-weight: 600;
}

.empty {
  color: var(--text-secondary, #999);
  font-size: 13px;
  padding: 12px;
  background: var(--bg-color-light, #f8f9fa);
  border-radius: 8px;
  text-align: center;
}

.relation-edit-section {
  margin-bottom: 24px;
  padding-bottom: 24px;
  border-bottom: 1px solid var(--border-lighter, #ebeef5);
}

.relation-edit-section:last-child {
  border-bottom: none;
  margin-bottom: 0;
  padding-bottom: 0;
}

.relation-edit-section h4 {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary, #303133);
}

.existing-relations {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.existing-relation-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: var(--bg-color-light, #f8f9fa);
  border-radius: 8px;
}

.relation-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.relation-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary, #333);
}

.relation-type {
  font-size: 12px;
  color: var(--text-secondary, #999);
}

.nature-tag {
  background: rgba(230, 162, 60, 0.1);
  color: var(--warning-color, #fa8c16);
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  margin-left: 8px;
}

.nature-tag.secondary {
  background: rgba(64, 158, 255, 0.1);
  color: #409EFF;
}

.relation-preview {
  padding: 12px 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 8px;
  color: white;
  text-align: center;
  font-size: 14px;
}

.relation-nature-blood { color: #e6a23c; }
.relation-nature-step { color: #909399; }
.relation-nature-adopt { color: #67c23a; }
.relation-nature-sworn { color: #f56c6c; }
.relation-nature-god { color: #409eff; }
.relation-nature-other { color: #909399; }
.relation-parent { color: #e6a23c; }
.relation-child { color: #67c23a; }
.relation-spouse { color: #f56c6c; }
.relation-other { color: #409eff; }
</style>
