<template>
  <el-dialog
    v-model="dialogVisible"
    :title="isEdit ? '编辑人物' : '添加人物'"
    width="500px"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="80px"
    >
      <el-alert type="info" :closable="false" class="form-tip">
        姓名与称呼至少填写一项
      </el-alert>

      <el-form-item label="姓名" prop="name">
        <el-input v-model="form.name" placeholder="如：李四、张三" />
      </el-form-item>

      <el-form-item label="称呼" prop="nickname">
        <el-input v-model="form.nickname" placeholder="如：爸爸、妈妈、小明" />
      </el-form-item>

      <el-form-item label="性别" prop="gender">
        <el-radio-group v-model="form.gender">
          <el-radio value="male">男</el-radio>
          <el-radio value="female">女</el-radio>
        </el-radio-group>
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" :loading="loading" @click="handleSubmit">
        确定
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getPerson, createPerson, updatePerson } from '@/api/persons'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  personId: {
    type: Number,
    default: null
  }
})

const emit = defineEmits(['update:visible', 'success'])

const formRef = ref(null)
const loading = ref(false)
const form = ref({
  nickname: '',
  name: '',
  gender: ''
})

// 自定义校验：姓名和称呼至少有一个不为空
const validateNameOrNickname = (rule, value, callback) => {
  const name = (form.value.name || '').trim()
  const nickname = (form.value.nickname || '').trim()
  if (!name && !nickname) {
    callback(new Error('姓名和称呼至少需要填写一个'))
  } else {
    callback()
  }
}

const rules = {
  name: [{ validator: validateNameOrNickname, trigger: 'blur' }],
  nickname: [{ validator: validateNameOrNickname, trigger: 'blur' }]
}


const dialogVisible = computed({
  get: () => props.visible,
  set: (val) => emit('update:visible', val)
})

const isEdit = computed(() => props.personId !== null)

const loadPerson = async () => {
  if (!props.personId) return

  try {
    const data = await getPerson(props.personId)
    const genderMap = { 1: 'male', 2: 'female' }
    form.value = {
      nickname: data.nickname || '',
      name: data.last_name ? data.last_name + data.first_name : '',
      gender: data.gender ? genderMap[data.gender] : ''
    }
  } catch (error) {
    ElMessage.error('加载人物信息失败')
  }
}

const handleSubmit = async () => {
  const valid = await formRef.value.validate()
  if (!valid) return

  loading.value = true
  try {
    const name = form.value.name || ''
    const last_name = name.charAt(0) || ''
    const first_name = name.slice(1) || ''
    
    const genderMap = { male: 1, female: 2 }
    const genderValue = form.value.gender ? genderMap[form.value.gender] : null
    
    const data = {
      nickname: form.value.nickname,
      last_name: last_name,
      first_name: first_name,
      gender: genderValue
    }

    if (isEdit.value) {
      await updatePerson(props.personId, data)
      ElMessage.success('更新成功')
    } else {
      await createPerson(data)
      ElMessage.success('创建成功')
    }
    emit('success')
  } catch (error) {
    const detail = error?.response?.data?.detail
    let msg = isEdit.value ? '更新失败' : '创建失败'
    if (typeof detail === 'string') {
      msg = detail
    } else if (Array.isArray(detail) && detail.length > 0) {
      const raw = detail[0]?.msg || msg
      msg = raw.replace(/^Value error,\s*/i, '')
    }
    ElMessage.error(msg)
  } finally {
    loading.value = false
  }
}

const handleClose = () => {
  formRef.value?.resetFields()
  form.value = {
    nickname: '',
    name: '',
    gender: ''
  }
  dialogVisible.value = false
}

watch(() => props.visible, (val) => {
  if (val) {
    loadPerson()
  }
})
</script>

<style scoped>
.form-tip {
  margin-bottom: 16px;
  padding: 8px 12px;
}

.form-tip :deep(.el-alert__content) {
  padding: 0;
}

.form-tip :deep(.el-alert__title) {
  font-size: 13px;
  color: var(--text-regular, #606266);
}
</style>