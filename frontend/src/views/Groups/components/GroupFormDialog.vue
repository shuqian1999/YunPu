<template>
  <el-dialog
    :model-value="visible"
    @update:model-value="$emit('update:visible', $event)"
    :title="group ? '编辑分组' : '新建分组'"
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
          :rows="3"
          placeholder="请输入分组描述（可选）"
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="$emit('update:visible', false)">取消</el-button>
      <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'

const props = defineProps({
  visible: { type: Boolean, default: false },
  group: { type: Object, default: null },
  saving: { type: Boolean, default: false }
})

const emit = defineEmits(['update:visible', 'save'])

const formRef = ref(null)
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

watch(
  () => props.group,
  (val) => {
    if (val) {
      formData.name = val.name
      formData.color = val.color
      formData.description = val.description || ''
    } else {
      formData.name = ''
      formData.color = '#409EFF'
      formData.description = ''
    }
  },
  { immediate: true }
)

const handleSave = async () => {
  const valid = await formRef.value.validate()
  if (!valid) return
  emit('save', { ...formData })
}

defineExpose({ resetForm: () => formRef.value?.resetFields() })
</script>
