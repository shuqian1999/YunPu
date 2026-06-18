<template>
  <el-card class="settings-card">
    <template #header>
      <div class="card-header-flex">
        <span class="card-title">邮件模板</span>
        <el-button type="primary" size="small" @click="openTemplateDialog()">
          <el-icon><Plus /></el-icon>
          新建模板
        </el-button>
      </div>
    </template>

    <el-alert
      title="模板说明"
      type="info"
      :closable="false"
      show-icon
      class="info-alert"
    >
      <p v-for="line in templateVariableLines" :key="line" v-html="line"></p>
      <p>不同事件类型可使用不同模板，留空 event_type 即为通用模板（兜底）</p>
    </el-alert>

    <el-table :data="templates" stripe>
      <el-table-column prop="name" label="模板名称" min-width="140" />
      <el-table-column label="事件类型" width="140">
        <template #default="{ row }">
          <el-tag v-if="row.event_type" :type="getEventTypeTagType(row.event_type)">
            {{ row.event_type }}
          </el-tag>
          <el-tag v-else type="info" effect="plain">通用</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="subject" label="邮件主题" min-width="200" show-overflow-tooltip />
      <el-table-column label="默认" width="80" align="center">
        <template #default="{ row }">
          <el-tag v-if="row.is_default" type="success" size="small">默认</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="220" fixed="right">
        <template #default="{ row }">
          <el-button text type="primary" size="small" @click="previewTemplate(row)">预览</el-button>
          <el-button text type="primary" size="small" @click="openTemplateDialog(row)">编辑</el-button>
          <el-button text type="danger" size="small" :disabled="row.is_default" @click="handleDeleteTemplate(row)">删除</el-button>
        </template>
      </el-table-column>
      <template #empty>
        <el-empty description="暂无模板" />
      </template>
    </el-table>

    <!-- 模板编辑对话框 -->
    <el-dialog
      v-model="templateDialogVisible"
      :title="templateDialogTitle"
      width="780px"
      @closed="resetTemplateForm"
    >
      <el-form :model="templateForm" label-width="100px">
        <el-form-item label="模板名称" required>
          <el-input v-model="templateForm.name" placeholder="如：生日祝福模板" />
        </el-form-item>
        <el-form-item label="关联类型">
          <el-select v-model="templateForm.event_type" placeholder="通用模板（不选择）" clearable style="width: 100%">
            <el-option
              v-for="t in eventTypes"
              :key="t.id"
              :label="t.name"
              :value="t.name"
            >
              <span class="type-option">
                <span class="type-color-dot" :style="{ backgroundColor: t.color }"></span>
                <span>{{ t.name }}</span>
              </span>
            </el-option>
          </el-select>
          <span class="form-hint">留空则作为通用模板（兜底使用）</span>
        </el-form-item>
        <el-form-item label="邮件主题" required>
          <el-input v-model="templateForm.subject" placeholder="支持变量：{{title}} {{days_until}} 等" />
        </el-form-item>
        <el-form-item label="邮件正文" required>
          <el-input
            v-model="templateForm.content"
            type="textarea"
            :rows="10"
            placeholder="支持 HTML 标签和变量"
          />
        </el-form-item>
        <el-form-item label="设为默认">
          <el-switch v-model="templateForm.is_default" />
          <span class="form-hint">通用模板中只能有一个默认</span>
        </el-form-item>
        <el-form-item label="HTML 格式">
          <el-switch v-model="templateForm.is_html" />
        </el-form-item>
        <el-form-item>
          <el-button @click="previewCurrentTemplate">预览效果</el-button>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="templateDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="savingTemplate" @click="handleSaveTemplate">保存</el-button>
      </template>
    </el-dialog>

    <!-- 模板预览对话框 -->
    <el-dialog v-model="previewDialogVisible" title="模板预览" width="700px">
      <el-form label-width="80px">
        <el-form-item label="主题">
          <div class="preview-subject">{{ previewData.subject }}</div>
        </el-form-item>
        <el-form-item label="正文">
          <div class="preview-content" v-html="previewData.content"></div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="previewDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import {
  listEmailTemplates, createEmailTemplate, updateEmailTemplate,
  deleteEmailTemplate, previewEmailTemplate
} from '@/api/email'
import { getEventTypes } from '@/api/event_types'

// 模板变量说明（用 v-html 渲染，避免 mustache 嵌套问题）
const templateVariableLines = [
  '支持变量：<code>{{title}}</code> 标题 · <code>{{name}}</code> 姓名 · <code>{{nickname}}</code> 称呼 · <code>{{date}}</code> 日期',
  '<code>{{days_until}}</code> 距今天数 · <code>{{event_type}}</code> 事件类型 · <code>{{description}}</code> 描述 · <code>{{lunar_date}}</code> 农历',
]

const templates = ref([])
const templateDialogVisible = ref(false)
const templateDialogTitle = ref('新建模板')
const savingTemplate = ref(false)
const templateForm = reactive({
  id: null,
  name: '',
  event_type: '',
  subject: '',
  content: '',
  is_default: false,
  is_html: true
})
const eventTypes = ref([])

const previewDialogVisible = ref(false)
const previewData = reactive({ subject: '', content: '' })

const getEventTypeTagType = (type) => {
  const map = { '生日': 'success', '纪念日': 'warning', '聚会': 'primary', '旅行': 'info', '工作': 'danger', '学习': '', '健康': 'success' }
  return map[type] || 'info'
}

const loadTemplates = async () => {
  try {
    templates.value = await listEmailTemplates()
  } catch (e) {
    console.error('加载模板失败:', e)
  }
}

const loadEventTypes = async () => {
  try {
    eventTypes.value = await getEventTypes()
  } catch (e) {
    console.error('加载事件类型失败:', e)
  }
}

const openTemplateDialog = (template = null) => {
  if (template) {
    templateDialogTitle.value = '编辑模板'
    Object.assign(templateForm, {
      id: template.id,
      name: template.name,
      event_type: template.event_type || '',
      subject: template.subject,
      content: template.content,
      is_default: template.is_default,
      is_html: template.is_html
    })
  } else {
    templateDialogTitle.value = '新建模板'
    Object.assign(templateForm, {
      id: null,
      name: '',
      event_type: '',
      subject: '',
      content: '',
      is_default: false,
      is_html: true
    })
  }
  templateDialogVisible.value = true
}

const resetTemplateForm = () => {
  templateForm.id = null
  templateForm.name = ''
  templateForm.event_type = ''
  templateForm.subject = ''
  templateForm.content = ''
  templateForm.is_default = false
  templateForm.is_html = true
}

const handleSaveTemplate = async () => {
  if (!templateForm.name || !templateForm.subject || !templateForm.content) {
    return ElMessage.warning('请填写完整信息')
  }
  savingTemplate.value = true
  try {
    const data = {
      name: templateForm.name,
      event_type: templateForm.event_type || null,
      subject: templateForm.subject,
      content: templateForm.content,
      is_default: templateForm.is_default,
      is_html: templateForm.is_html
    }
    if (templateForm.id) {
      await updateEmailTemplate(templateForm.id, data)
    } else {
      await createEmailTemplate(data)
    }
    ElMessage.success('保存成功')
    templateDialogVisible.value = false
    await loadTemplates()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '保存失败')
  } finally {
    savingTemplate.value = false
  }
}

const handleDeleteTemplate = async (template) => {
  try {
    await ElMessageBox.confirm(`确定要删除模板 "${template.name}" 吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await deleteEmailTemplate(template.id)
    ElMessage.success('删除成功')
    await loadTemplates()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error(e.response?.data?.detail || '删除失败')
    }
  }
}

const previewTemplate = async (template) => {
  try {
    const res = await previewEmailTemplate(template.id)
    previewData.subject = res.subject
    previewData.content = res.content
    previewDialogVisible.value = true
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '预览失败')
  }
}

const previewCurrentTemplate = async () => {
  if (!templateForm.subject || !templateForm.content) {
    return ElMessage.warning('请先填写主题和正文')
  }
  // 本地预览（未保存的）
  const sample = {
    title: '生日', name: '张三', nickname: '小明',
    date: '2026年06月20日', days_until: 3, event_type: '生日',
    description: '庆祝张三的生日', location: '家',
    is_lunar: '否', lunar_date: ''
  }
  const replace = (str) => {
    let out = str
    for (const [k, v] of Object.entries(sample)) {
      out = out.replaceAll(`{{${k}}}`, v)
    }
    return out
  }
  previewData.subject = replace(templateForm.subject)
  previewData.content = replace(templateForm.content)
  previewDialogVisible.value = true
}

onMounted(() => {
  loadTemplates()
  loadEventTypes()
})
</script>

<style scoped>
.settings-card {
  margin-bottom: 20px;
  background: var(--card-bg, #ffffff);
  border: 1px solid var(--border-color, #dcdfe6);
  border-radius: 12px;
}

.card-title {
  font-size: 18px;
  font-weight: 500;
  color: var(--text-primary, #303133);
}

.card-header-flex {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.info-alert {
  margin-bottom: 16px;
}

.info-alert :deep(p) {
  margin: 4px 0;
}

.info-alert :deep(code) {
  display: inline-block;
  padding: 0 6px;
  margin: 0 2px;
  background: rgba(64, 158, 255, 0.1);
  color: var(--primary-color, #409EFF);
  border-radius: 3px;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 12px;
}

.type-option {
  display: flex;
  align-items: center;
  gap: 8px;
}

.type-color-dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.form-hint {
  margin-left: 12px;
  color: var(--text-secondary, #909399);
  font-size: 12px;
}

.preview-subject {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary, #303133);
  padding: 8px 12px;
  background: var(--bg-color-light, #f5f7fa);
  border-radius: 4px;
  word-break: break-all;
}

.preview-content {
  padding: 16px;
  background: var(--card-bg, #ffffff);
  border: 1px solid var(--border-lighter, #ebeef5);
  border-radius: 4px;
  max-height: 480px;
  overflow-y: auto;
  word-break: break-all;
}
</style>
