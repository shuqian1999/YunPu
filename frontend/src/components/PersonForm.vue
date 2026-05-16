<template>
  <el-dialog
    v-model="dialogVisible"
    :title="isEdit ? '编辑人物' : '添加人物'"
    width="600px"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="100px"
    >
      <el-form-item label="姓氏" prop="last_name">
        <el-input v-model="form.last_name" placeholder="请输入姓氏" />
      </el-form-item>
      
      <el-form-item label="名字" prop="first_name">
        <el-input v-model="form.first_name" placeholder="请输入名字" />
      </el-form-item>
      
      <el-form-item label="昵称" prop="nickname">
        <el-input v-model="form.nickname" placeholder="请输入昵称" />
      </el-form-item>
      
      <el-form-item label="性别" prop="gender">
        <el-radio-group v-model="form.gender">
          <el-radio :label="1">男</el-radio>
          <el-radio :label="2">女</el-radio>
          <el-radio :label="0">未知</el-radio>
        </el-radio-group>
      </el-form-item>
      
      <el-form-item label="出生日期" prop="birth_date">
        <el-date-picker
          v-model="form.birth_date"
          type="date"
          placeholder="选择出生日期"
          value-format="YYYY-MM-DD"
          style="width: 100%"
        />
      </el-form-item>
      
      <el-form-item label="国家" prop="country">
        <el-input v-model="form.country" placeholder="请输入国家" />
      </el-form-item>
      
      <el-form-item label="家乡" prop="hometown">
        <el-input v-model="form.hometown" placeholder="请输入家乡" />
      </el-form-item>
      
      <el-form-item label="居住地" prop="residence">
        <el-input v-model="form.residence" placeholder="请输入居住地" />
      </el-form-item>
      
      <el-form-item label="标记为我自己">
        <el-switch v-model="form.is_me" />
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
import { ref, computed, watch } from 'vue'
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
  first_name: '',
  last_name: '',
  nickname: '',
  gender: 0,
  birth_date: '',
  country: '',
  hometown: '',
  residence: '',
  is_me: false
})

const rules = {
  first_name: [
    { required: true, message: '请输入名字', trigger: 'blur' }
  ],
  last_name: [
    { required: true, message: '请输入姓氏', trigger: 'blur' }
  ]
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
    form.value = {
      first_name: data.first_name || '',
      last_name: data.last_name || '',
      nickname: data.nickname || '',
      gender: data.gender || 0,
      birth_date: data.birth_date || '',
      country: data.country || '',
      hometown: data.hometown || '',
      residence: data.residence || '',
      is_me: data.is_me || false
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
    if (isEdit.value) {
      await updatePerson(props.personId, form.value)
      ElMessage.success('更新成功')
    } else {
      await createPerson(form.value)
      ElMessage.success('创建成功')
    }
    emit('success')
  } catch (error) {
    ElMessage.error(isEdit.value ? '更新失败' : '创建失败')
  } finally {
    loading.value = false
  }
}

const handleClose = () => {
  formRef.value?.resetFields()
  form.value = {
    first_name: '',
    last_name: '',
    nickname: '',
    gender: 0,
    birth_date: '',
    country: '',
    hometown: '',
    residence: '',
    is_me: false
  }
  dialogVisible.value = false
}

watch(() => props.visible, (val) => {
  if (val) {
    loadPerson()
  }
})
</script>