<template>
  <div class="social-section">
    <div class="section-header">
      <h3 class="section-title">社会关系</h3>
      <el-button @click="openCreate" type="primary" size="small">
        <el-icon><Plus /></el-icon>
        添加社会关系
      </el-button>
    </div>

    <div class="section-content">
      <div v-if="relations.length === 0" class="empty">暂无社会关系</div>
      <div v-else class="relation-list">
        <div v-for="rel in relations" :key="rel.relation_id" class="relation-item">
          <div class="relation-main">
            <span class="type-dot" :style="{ background: rel.type.color }"></span>
            <span class="relation-type" :class="{ 'is-past': rel.end_date }">
              {{ rel.relation_name }}
            </span>
            <span class="separator">·</span>
            <span class="relation-person" @click="goPerson(rel.other.id)">
              {{ rel.other.name }}
            </span>
            <el-rate
              :model-value="rel.closeness || 0"
              disabled
              size="small"
              class="closeness-stars"
            />
            <span v-if="hasDate(rel)" class="segment-date">{{ formatDate(rel) }}</span>
            <span v-if="rel.introducer" class="introducer">
              介绍人：
              <span class="introducer-name" @click="goPerson(rel.introducer.id)">
                {{ rel.introducer.name }}
              </span>
            </span>
          </div>
          <div class="relation-actions">
            <el-button text type="primary" size="small" @click="openEdit(rel)">
              编辑
            </el-button>
            <el-button text type="danger" size="small" @click="handleDelete(rel)">
              删除
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 添加 / 编辑 关系 -->
    <el-dialog
      :title="form.relation_id ? '编辑社会关系' : '添加社会关系'"
      v-model="showDialog"
      width="560px"
      @closed="resetForm"
    >
      <el-form :model="form" label-width="84px">
        <el-form-item label="关系类型">
          <el-select v-model="form.type_id" placeholder="选择关系类型" style="flex: 1">
            <el-option
              v-for="t in types"
              :key="t.id"
              :label="typeOptionLabel(t)"
              :value="t.id"
            >
              <span class="type-option-dot" :style="{ background: t.color }"></span>
              <span>{{ t.name }}</span>
              <span v-if="t.directed && t.reverse_name" class="type-option-rev">
                （对端：{{ t.reverse_name }}）
              </span>
            </el-option>
          </el-select>
          <el-button text type="primary" @click="openTypeDialog">
            <el-icon><Plus /></el-icon>新建类型
          </el-button>
        </el-form-item>

        <el-form-item label="对方人物">
          <el-select
            v-model="form.other_id"
            placeholder="选择人物"
            filterable
            style="width: 100%"
          >
            <el-option
              v-for="p in otherPersonOptions"
              :key="p.id"
              :label="p.name"
              :value="p.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item v-if="selectedType && selectedType.directed" label="关系方向">
          <el-radio-group v-model="form.direction">
            <el-radio value="forward">
              我是 TA 的{{ selectedType.name }}
              <span class="direction-hint">（TA 是我的{{ selectedType.reverse_name }}）</span>
            </el-radio>
            <el-radio value="reverse">
              TA 是我的{{ selectedType.name }}
              <span class="direction-hint">（我是 TA 的{{ selectedType.reverse_name }}）</span>
            </el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="亲密度">
          <el-rate v-model="form.closeness" clearable />
          <span class="form-hint">可不填，表示关系亲近程度</span>
        </el-form-item>

        <el-form-item label="介绍人">
          <el-select
            v-model="form.introducer_id"
            placeholder="可选"
            filterable
            clearable
            style="width: 100%"
          >
            <el-option
              v-for="p in introducerOptions"
              :key="p.id"
              :label="p.name"
              :value="p.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="开始日期">
          <el-date-picker
            v-model="form.start_date"
            type="date"
            value-format="YYYY-MM-DD"
            placeholder="关系建立日（可选）"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="结束日期">
          <el-date-picker
            v-model="form.end_date"
            type="date"
            value-format="YYYY-MM-DD"
            placeholder="留空表示关系进行中"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>

    <!-- 新建 / 管理 类型 -->
    <el-dialog
      title="管理关系类型"
      v-model="showTypeDialog"
      width="480px"
      append-to-body
    >
      <el-form :model="typeForm" label-width="84px">
        <el-form-item label="类型名称">
          <el-input v-model="typeForm.name" maxlength="20" show-word-limit />
        </el-form-item>
        <el-form-item label="有方向">
          <el-switch v-model="typeForm.directed" />
          <span class="form-hint">如老师→学生；朋友/同事等无需方向</span>
        </el-form-item>
        <el-form-item v-if="typeForm.directed" label="反向称谓">
          <el-input
            v-model="typeForm.reverse_name"
            maxlength="20"
            placeholder="如：老师 / 学生 中的「学生」"
          />
        </el-form-item>
        <el-form-item label="颜色">
          <el-color-picker v-model="typeForm.color" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleCreateType">创建类型</el-button>
        </el-form-item>
      </el-form>

      <el-divider>自建类型</el-divider>
      <div v-if="customTypes.length === 0" class="empty">暂无自建类型</div>
      <div v-for="t in customTypes" :key="t.id" class="custom-type-row">
        <span class="type-dot" :style="{ background: t.color }"></span>
        <span class="custom-type-name">
          {{ t.name }}<template v-if="t.directed"> / {{ t.reverse_name }}</template>
        </span>
        <span class="custom-type-count">{{ t.relation_count }} 条关系</span>
        <el-button
          text
          type="danger"
          size="small"
          :disabled="t.relation_count > 0"
          @click="handleDeleteType(t)"
        >
          删除
        </el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, inject, onMounted } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRouter } from 'vue-router'
import {
  getSocialTypes,
  createSocialType,
  deleteSocialType,
  listSocialRelations,
  createSocialRelation,
  updateSocialRelation,
  deleteSocialRelation
} from '@/api/social'

const props = defineProps({
  personId: { type: Number, required: true }
})

const router = useRouter()
const shared = inject('personShared', null)
const availablePersons = computed(() => shared?.availablePersons?.value || [])

const relations = ref([])
const types = ref([])
const showDialog = ref(false)
const showTypeDialog = ref(false)

const emptyForm = () => ({
  relation_id: null,
  other_id: null,
  type_id: null,
  direction: 'forward',
  closeness: 0,
  start_date: null,
  end_date: null,
  introducer_id: null
})
const form = reactive(emptyForm())

const typeForm = reactive({
  name: '',
  directed: false,
  reverse_name: '',
  color: '#fa8c16'
})

const selectedType = computed(
  () => types.value.find(t => t.id === form.type_id) || null
)

const customTypes = computed(() => types.value.filter(t => !t.is_preset))

// 对方人物：排除自己
const otherPersonOptions = computed(() =>
  availablePersons.value.filter(p => p.id !== props.personId)
)

// 介绍人：排除自己与对方
const introducerOptions = computed(() =>
  availablePersons.value.filter(
    p => p.id !== props.personId && p.id !== form.other_id
  )
)

const typeOptionLabel = (t) =>
  t.directed && t.reverse_name ? `${t.name} / ${t.reverse_name}` : t.name

const hasDate = (rel) => Boolean(rel.start_date || rel.end_date)

const formatDate = (rel) =>
  `${rel.start_date || '?'} ~ ${rel.end_date || '至今'}`

const goPerson = (id) => {
  if (id) router.push(`/persons/${id}`)
}

// ---------------------------------------------------------------- 数据加载
const loadTypes = async () => {
  try {
    types.value = await getSocialTypes()
  } catch (e) {
    console.error('获取社会关系类型失败:', e)
  }
}

const loadRelations = async () => {
  try {
    relations.value = await listSocialRelations(props.personId)
  } catch (e) {
    console.error('获取社会关系失败:', e)
    relations.value = []
  }
}

const resetForm = () => {
  Object.assign(form, emptyForm())
}

// ---------------------------------------------------------------- 对话框
const openCreate = () => {
  resetForm()
  if (types.value.length) form.type_id = types.value[0].id
  showDialog.value = true
}

const openEdit = (rel) => {
  resetForm()
  form.relation_id = rel.relation_id
  form.other_id = rel.other.id
  form.type_id = rel.type.id
  form.direction = rel.direction === 'none' ? 'forward' : rel.direction
  form.closeness = rel.closeness || 0
  form.start_date = rel.start_date
  form.end_date = rel.end_date
  form.introducer_id = rel.introducer ? rel.introducer.id : null
  showDialog.value = true
}

// 按当前人物视角换算存储方向：
// forward = 我是TA的name（我为 a）；reverse = TA是我的name（对方为 a）
const buildPayload = () => {
  const t = selectedType.value
  let aId, bId
  if (t && t.directed && form.direction === 'reverse') {
    aId = form.other_id
    bId = props.personId
  } else {
    aId = props.personId
    bId = form.other_id
  }
  return {
    person_a_id: aId,
    person_b_id: bId,
    type_id: form.type_id,
    closeness: form.closeness || null,
    start_date: form.start_date || null,
    end_date: form.end_date || null,
    introducer_id: form.introducer_id || null
  }
}

const handleSave = async () => {
  if (!form.type_id) {
    ElMessage.warning('请选择关系类型')
    return
  }
  if (!form.other_id) {
    ElMessage.warning('请选择对方人物')
    return
  }
  if (form.start_date && form.end_date && form.end_date < form.start_date) {
    ElMessage.warning('结束日期不能早于开始日期')
    return
  }
  try {
    const payload = buildPayload()
    if (form.relation_id) {
      await updateSocialRelation(form.relation_id, payload)
      ElMessage.success('关系已更新')
    } else {
      await createSocialRelation(payload)
      ElMessage.success('关系已添加')
    }
    showDialog.value = false
    await loadRelations()
    await loadTypes()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '保存失败')
  }
}

const handleDelete = async (rel) => {
  try {
    await ElMessageBox.confirm(
      `确定删除与「${rel.other.name}」的${rel.relation_name}关系吗？`,
      '删除确认',
      { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' }
    )
  } catch {
    return
  }
  try {
    await deleteSocialRelation(rel.relation_id)
    ElMessage.success('关系已删除')
    await loadRelations()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '删除失败')
  }
}

// ---------------------------------------------------------------- 类型管理
const openTypeDialog = () => {
  typeForm.name = ''
  typeForm.directed = false
  typeForm.reverse_name = ''
  typeForm.color = '#fa8c16'
  showTypeDialog.value = true
}

const handleCreateType = async () => {
  if (!typeForm.name.trim()) {
    ElMessage.warning('请输入类型名称')
    return
  }
  if (typeForm.directed && !typeForm.reverse_name.trim()) {
    ElMessage.warning('有向类型必须填写反向称谓')
    return
  }
  try {
    const created = await createSocialType({
      name: typeForm.name.trim(),
      directed: typeForm.directed,
      reverse_name: typeForm.directed ? typeForm.reverse_name.trim() : null,
      color: typeForm.color
    })
    ElMessage.success('类型已创建')
    typeForm.name = ''
    typeForm.directed = false
    typeForm.reverse_name = ''
    await loadTypes()
    form.type_id = created.id
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '创建失败')
  }
}

const handleDeleteType = async (t) => {
  try {
    await deleteSocialType(t.id)
    ElMessage.success('类型已删除')
    await loadTypes()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '删除失败')
  }
}

onMounted(() => {
  loadTypes()
  loadRelations()
})
</script>

<style scoped>
.social-section {
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

.empty {
  color: var(--text-secondary, #909399);
  font-size: 14px;
  padding: 8px 0;
}

.relation-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.relation-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  background: var(--bg-color-light, #f8f9fa);
  border-radius: 8px;
}

.relation-main {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  line-height: 1.5;
  font-size: 14px;
}

.type-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 2px;
}

.relation-type {
  font-weight: 600;
  color: var(--text-primary, #303133);
}

.relation-type.is-past {
  color: var(--text-secondary, #909399);
  font-weight: 500;
}

.separator {
  color: #ccc;
}

.relation-person,
.introducer-name {
  color: var(--primary-color, #409eff);
  cursor: pointer;
}

.relation-person:hover,
.introducer-name:hover {
  text-decoration: underline;
}

.closeness-stars {
  margin: 0 2px;
}

.segment-date {
  color: var(--text-secondary, #909399);
  font-size: 12px;
}

.introducer {
  color: var(--text-secondary, #909399);
  font-size: 13px;
}

.relation-actions {
  flex-shrink: 0;
}

.form-hint {
  margin-left: 10px;
  color: var(--text-secondary, #909399);
  font-size: 12px;
}

.direction-hint {
  color: var(--text-secondary, #909399);
  font-size: 12px;
}

.type-option-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 8px;
}

.type-option-rev {
  color: var(--text-secondary, #909399);
  font-size: 12px;
  margin-left: 4px;
}

.custom-type-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 0;
  font-size: 14px;
}

.custom-type-name {
  flex: 1;
}

.custom-type-count {
  color: var(--text-secondary, #909399);
  font-size: 12px;
}
</style>
