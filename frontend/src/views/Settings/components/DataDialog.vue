<template>
  <el-dialog :model-value="visible" @update:model-value="$emit('update:visible', $event)" title="数据导入/导出" width="600px" @close="reset">
    <el-tabs v-model="activeTab">
      <el-tab-pane label="导出数据" name="export">
        <div class="export-options">
          <el-radio-group v-model="exportFormat">
            <el-radio value="json">JSON 格式</el-radio>
            <el-radio value="csv">CSV 格式</el-radio>
          </el-radio-group>
        </div>

        <el-alert title="导出说明" type="info" :closable="false" show-icon>
          <ul>
            <li>JSON 格式：包含所有数据，适合完整备份</li>
            <li>CSV 格式：仅包含人物数据，适合Excel编辑</li>
          </ul>
        </el-alert>
      </el-tab-pane>

      <el-tab-pane label="导入数据" name="import">
        <el-upload
          drag
          :auto-upload="false"
          :on-change="handleFileChange"
          accept=".json"
          class="upload-area"
        >
          <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
          <div class="el-upload__text">
            拖拽文件到此处或 <em>点击上传</em>
          </div>
          <template #tip>
            <div class="el-upload__tip">仅支持 JSON 格式文件</div>
          </template>
        </el-upload>

        <el-alert title="导入说明" type="warning" :closable="false" show-icon>
          <ul>
            <li>导入数据将添加到现有数据中</li>
            <li>建议先导出备份再导入</li>
          </ul>
        </el-alert>
      </el-tab-pane>
    </el-tabs>

    <template #footer>
      <el-button @click="$emit('update:visible', false)">取消</el-button>
      <el-button
        v-if="activeTab === 'export'"
        type="primary"
        :loading="exporting"
        @click="handleExport"
      >导出</el-button>
      <el-button
        v-if="activeTab === 'import'"
        type="primary"
        :loading="importing"
        @click="handleImport"
      >导入</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import { exportDataJson, exportDataCsv, importDataJson } from '@/api/data'

const props = defineProps({
  visible: { type: Boolean, default: false },
  defaultTab: { type: String, default: 'export' }
})

const emit = defineEmits(['update:visible', 'completed'])

const activeTab = ref('export')
const exportFormat = ref('json')
const exporting = ref(false)
const importing = ref(false)
const selectedFile = ref(null)

watch(() => props.visible, (val) => {
  if (val) {
    activeTab.value = props.defaultTab
    selectedFile.value = null
  }
})

const handleFileChange = (file) => {
  selectedFile.value = file.raw
}

const handleExport = async () => {
  exporting.value = true
  try {
    let blob, filename
    if (exportFormat.value === 'json') {
      blob = await exportDataJson()
      filename = 'yunpu_data.json'
    } else {
      blob = await exportDataCsv()
      filename = 'yunpu_persons.csv'
    }
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
    emit('update:visible', false)
    emit('completed')
  } catch (error) {
    ElMessage.error('导出失败')
  } finally {
    exporting.value = false
  }
}

const handleImport = async () => {
  if (!selectedFile.value) {
    ElMessage.warning('请选择要导入的文件')
    return
  }
  importing.value = true
  try {
    const result = await importDataJson(selectedFile.value)
    ElMessage.success(result.message)
    emit('update:visible', false)
    emit('completed')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '导入失败')
  } finally {
    importing.value = false
    selectedFile.value = null
  }
}

const reset = () => {
  selectedFile.value = null
  exportFormat.value = 'json'
}
</script>

<style scoped>
.export-options {
  margin-bottom: 16px;
}

.upload-area {
  margin-bottom: 16px;
}
</style>
