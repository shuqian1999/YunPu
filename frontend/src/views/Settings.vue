<template>
  <div class="settings-container">
    <el-tabs v-model="activeTab" class="settings-tabs">
      <!-- 系统设置 -->
      <el-tab-pane label="系统设置" name="system">
        <el-card class="settings-card">
          <template #header>
            <span class="card-title">数据统计</span>
          </template>

          <div class="stats-grid">
            <div class="stat-item">
              <div class="stat-value">{{ systemStats.person_count }}</div>
              <div class="stat-label">人物总数</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ systemStats.event_count }}</div>
              <div class="stat-label">事件总数</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ systemStats.reminder_count }}</div>
              <div class="stat-label">提醒总数</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ systemStats.database_size }}</div>
              <div class="stat-label">数据库大小</div>
            </div>
          </div>
        </el-card>

        <el-card class="settings-card">
          <template #header>
            <span class="card-title">修改密码</span>
          </template>

          <el-form
            ref="passwordFormRef"
            :model="passwordForm"
            :rules="passwordRules"
            label-width="120px"
          >
            <el-form-item label="原密码" prop="old_password">
              <el-input
                v-model="passwordForm.old_password"
                type="password"
                show-password
                placeholder="请输入原密码"
              />
            </el-form-item>

            <el-form-item label="新密码" prop="new_password">
              <el-input
                v-model="passwordForm.new_password"
                type="password"
                show-password
                placeholder="请输入新密码"
              />
            </el-form-item>

            <el-form-item label="确认密码" prop="confirm_password">
              <el-input
                v-model="passwordForm.confirm_password"
                type="password"
                show-password
                placeholder="请再次输入新密码"
              />
            </el-form-item>

            <el-form-item>
              <el-button type="primary" :loading="changingPassword" @click="handleChangePassword">
                修改密码
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <el-card class="settings-card">
          <template #header>
            <span class="card-title">数据管理</span>
          </template>

          <div class="data-actions">
            <el-button type="primary" @click="handleExportData">
              <el-icon><Download /></el-icon>
              导出数据
            </el-button>
            <el-button @click="handleImportData">
              <el-icon><Upload /></el-icon>
              导入数据
            </el-button>
          </div>
        </el-card>
      </el-tab-pane>

      <!-- 邮件通知 -->
      <el-tab-pane label="邮件通知" name="email">
        <el-card class="settings-card">
          <template #header>
            <div class="card-header-flex">
              <span class="card-title">SMTP 配置</span>
              <el-switch
                v-model="emailForm.enabled"
                active-text="启用"
                inactive-text="停用"
                inline-prompt
              />
            </div>
          </template>

          <el-alert
            title="温馨提示"
            type="info"
            :closable="false"
            show-icon
            class="info-alert"
          >
            <p>邮箱通知需要使用 SMTP 服务，建议使用 QQ邮箱 / 163邮箱 / Gmail 等。</p>
            <p>授权码不是登录密码，请在邮箱设置中生成专用授权码（应用专用密码）。</p>
            <p>常用 SMTP：QQ邮箱 smtp.qq.com:465(SSL) | 163邮箱 smtp.163.com:465(SSL) | Gmail smtp.gmail.com:587(TLS)</p>
          </el-alert>

          <el-form
            ref="emailFormRef"
            :model="emailForm"
            label-width="120px"
            class="email-form"
          >
            <el-form-item label="SMTP 服务器">
              <el-input v-model="emailForm.smtp_host" placeholder="如：smtp.qq.com" clearable />
            </el-form-item>

            <el-form-item label="端口">
              <el-input-number v-model="emailForm.smtp_port" :min="1" :max="65535" />
            </el-form-item>

            <el-form-item label="SSL 加密">
              <el-switch v-model="emailForm.use_ssl" />
              <span class="form-hint">推荐启用（QQ/163 邮箱使用 465+SSL）</span>
            </el-form-item>

            <el-form-item label="发送邮箱" required>
              <el-input v-model="emailForm.username" placeholder="如：example@qq.com" clearable />
            </el-form-item>

            <el-form-item label="授权码" required>
              <el-input
                v-model="emailForm.password"
                type="password"
                show-password
                placeholder="邮箱设置中生成的授权码"
                clearable
              />
            </el-form-item>

            <el-form-item label="接收邮箱" required>
              <el-input
                v-model="emailForm.receivers"
                type="textarea"
                :rows="2"
                placeholder="多个邮箱用英文逗号分隔"
              />
            </el-form-item>

            <el-form-item label="发送时间">
              <el-time-picker
                v-model="sendTimeDate"
                format="HH:mm"
                value-format="HH:mm"
                placeholder="选择发送时间"
                @change="onSendTimeChange"
              />
              <span class="form-hint">每天该时间点发送当天的提醒邮件</span>
            </el-form-item>

            <el-form-item label="提前提醒">
              <el-input-number v-model="emailForm.advance_days" :min="0" :max="30" />
              <span class="form-hint">天，0 表示当天提醒</span>
            </el-form-item>

            <el-form-item label="提醒类型">
              <el-input
                v-model="reminderTypesText"
                placeholder="如：生日,纪念日"
                clearable
              />
              <span class="form-hint">多个用英文逗号分隔，留空表示全部类型</span>
            </el-form-item>

            <el-form-item>
              <el-button type="primary" :loading="savingEmail" @click="handleSaveEmailConfig">
                保存配置
              </el-button>
              <el-button :loading="testingConnection" @click="handleTestConnection">
                <el-icon><Connection /></el-icon>
                测试连接
              </el-button>
              <el-button :loading="testingSend" @click="handleTestSend">
                <el-icon><Promotion /></el-icon>
                发送测试邮件
              </el-button>
              <el-button :loading="sendingNow" type="success" @click="handleSendNow">
                <el-icon><Position /></el-icon>
                立即发送
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <!-- 模板管理 -->
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
        </el-card>

        <!-- 发送日志 -->
        <el-card class="settings-card">
          <template #header>
            <div class="card-header-flex">
              <span class="card-title">发送日志</span>
              <el-button text type="danger" size="small" @click="handleClearLogs">清空日志</el-button>
            </div>
          </template>

          <el-table :data="emailLogs" stripe>
            <el-table-column label="状态" width="100">
              <template #default="{ row }">
                <el-tag v-if="row.status === 'success'" type="success" size="small">成功</el-tag>
                <el-tag v-else type="danger" size="small">失败</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="subject" label="主题" min-width="200" show-overflow-tooltip />
            <el-table-column prop="receivers" label="接收方" min-width="180" show-overflow-tooltip />
            <el-table-column prop="related_count" label="数量" width="80" align="center" />
            <el-table-column label="时间" width="180">
              <template #default="{ row }">
                {{ formatDateTime(row.created_at) }}
              </template>
            </el-table-column>
            <template #empty>
              <el-empty description="暂无日志" />
            </template>
          </el-table>
        </el-card>
      </el-tab-pane>
    </el-tabs>

    <!-- 数据导入导出对话框 -->
    <el-dialog v-model="dataDialogVisible" title="数据导入/导出" width="600px">
      <el-tabs v-model="dataDialogTab">
        <el-tab-pane label="导出数据" name="export">
          <div class="export-options">
            <el-radio-group v-model="exportFormat">
              <el-radio label="json">JSON 格式</el-radio>
              <el-radio label="csv">CSV 格式</el-radio>
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
        <el-button @click="dataDialogVisible = false">取消</el-button>
        <el-button
          v-if="dataDialogTab === 'export'"
          type="primary"
          :loading="exporting"
          @click="handleExport"
        >导出</el-button>
        <el-button
          v-if="dataDialogTab === 'import'"
          type="primary"
          :loading="importing"
          @click="handleImport"
        >导入</el-button>
      </template>
    </el-dialog>

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
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Download, Upload, UploadFilled, Plus, Connection, Promotion, Position
} from '@element-plus/icons-vue'
import { changePassword, getSystemSettings } from '@/api/settings'
import { exportDataJson, exportDataCsv, importDataJson } from '@/api/data'
import {
  getEmailConfig, updateEmailConfig, testEmailConnection, testEmailSend, sendEmailNow,
  listEmailTemplates, createEmailTemplate, updateEmailTemplate, deleteEmailTemplate,
  previewEmailTemplate, listEmailLogs, clearEmailLogs
} from '@/api/email'
import { getEventTypes } from '@/api/event_types'

const activeTab = ref('system')

// 模板变量说明（用 v-html 渲染，避免 mustache 嵌套问题）
const templateVariableLines = [
  '支持变量：<code>{{title}}</code> 标题 · <code>{{name}}</code> 姓名 · <code>{{nickname}}</code> 称呼 · <code>{{date}}</code> 日期',
  '<code>{{days_until}}</code> 距今天数 · <code>{{event_type}}</code> 事件类型 · <code>{{description}}</code> 描述 · <code>{{lunar_date}}</code> 农历',
]

// ============= 系统设置 =============
const changingPassword = ref(false)
const passwordFormRef = ref(null)
const passwordForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: ''
})
const systemStats = ref({
  person_count: 0,
  event_count: 0,
  reminder_count: 0,
  database_size: '0 MB'
})
const passwordRules = {
  old_password: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 8, message: '密码长度不能少于8位', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== passwordForm.new_password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

const dataDialogVisible = ref(false)
const dataDialogTab = ref('export')
const exportFormat = ref('json')
const exporting = ref(false)
const importing = ref(false)
const selectedFile = ref(null)

// ============= 邮件通知 =============
const emailForm = reactive({
  smtp_host: '',
  smtp_port: 465,
  use_ssl: true,
  username: '',
  password: '',
  receivers: '',
  send_time: '08:00',
  enabled: false,
  advance_days: 7,
  reminder_types: []
})
const sendTimeDate = ref('08:00')
const reminderTypesText = ref('')
const savingEmail = ref(false)
const testingConnection = ref(false)
const testingSend = ref(false)
const sendingNow = ref(false)
const emailFormRef = ref(null)

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
const emailLogs = ref([])

const previewDialogVisible = ref(false)
const previewData = reactive({ subject: '', content: '' })

// 提醒类型 text <-> array
const onReminderTypesInput = () => {
  emailForm.reminder_types = reminderTypesText.value
    .split(/[,，]/)
    .map(s => s.trim())
    .filter(Boolean)
}

const formatDateTime = (str) => {
  if (!str) return '-'
  return new Date(str).toLocaleString('zh-CN', { hour12: false })
}

const getEventTypeTagType = (type) => {
  const map = { '生日': 'success', '纪念日': 'warning', '聚会': 'primary', '旅行': 'info', '工作': 'danger', '学习': '', '健康': 'success' }
  return map[type] || 'info'
}

const onSendTimeChange = (val) => {
  if (val) emailForm.send_time = val
}

const loadEmailConfig = async () => {
  try {
    const config = await getEmailConfig()
    Object.assign(emailForm, {
      smtp_host: config.smtp_host || '',
      smtp_port: config.smtp_port || 465,
      use_ssl: config.use_ssl !== false,
      username: config.username || '',
      password: '',
      receivers: config.receivers || '',
      send_time: config.send_time || '08:00',
      enabled: !!config.enabled,
      advance_days: config.advance_days ?? 7,
      reminder_types: config.reminder_types || []
    })
    sendTimeDate.value = emailForm.send_time
    reminderTypesText.value = (emailForm.reminder_types || []).join(',')
  } catch (e) {
    console.error('加载邮件配置失败:', e)
  }
}

const handleSaveEmailConfig = async () => {
  if (emailForm.enabled) {
    if (!emailForm.smtp_host) return ElMessage.warning('请填写 SMTP 服务器')
    if (!emailForm.username) return ElMessage.warning('请填写发送邮箱')
    if (!emailForm.receivers) return ElMessage.warning('请填写接收邮箱')
  }
  onReminderTypesInput()
  savingEmail.value = true
  try {
    await updateEmailConfig({
      smtp_host: emailForm.smtp_host,
      smtp_port: emailForm.smtp_port,
      use_ssl: emailForm.use_ssl,
      username: emailForm.username,
      password: emailForm.password || undefined,
      receivers: emailForm.receivers,
      send_time: emailForm.send_time,
      enabled: emailForm.enabled,
      advance_days: emailForm.advance_days,
      reminder_types: emailForm.reminder_types
    })
    ElMessage.success('配置已保存')
    emailForm.password = ''
    await loadEmailConfig()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '保存失败')
  } finally {
    savingEmail.value = false
  }
}

const handleTestConnection = async () => {
  testingConnection.value = true
  try {
    const res = await testEmailConnection()
    ElMessage.success(res.message || '连接成功')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '连接失败')
  } finally {
    testingConnection.value = false
  }
}

const handleTestSend = async () => {
  testingSend.value = true
  try {
    const res = await testEmailSend(null)
    ElMessage.success(res.message || '测试邮件已发送')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '发送失败')
  } finally {
    testingSend.value = false
  }
}

const handleSendNow = async () => {
  sendingNow.value = true
  try {
    const res = await sendEmailNow({})
    ElMessage.success(res.message || '已发送')
    await loadLogs()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '发送失败')
  } finally {
    sendingNow.value = false
  }
}

// 模板管理
const loadTemplates = async () => {
  try {
    templates.value = await listEmailTemplates()
  } catch (e) {
    console.error('加载模板失败:', e)
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

// 日志
const loadLogs = async () => {
  try {
    emailLogs.value = await listEmailLogs(50)
  } catch (e) {
    console.error('加载日志失败:', e)
  }
}

const handleClearLogs = async () => {
  try {
    await ElMessageBox.confirm('确定要清空所有发送日志吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await clearEmailLogs()
    ElMessage.success('已清空')
    await loadLogs()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('清空失败')
    }
  }
}

const loadEventTypes = async () => {
  try {
    eventTypes.value = await getEventTypes()
  } catch (e) {
    console.error('加载事件类型失败:', e)
  }
}

const loadSystemSettings = async () => {
  try {
    systemStats.value = await getSystemSettings()
  } catch (error) {
    ElMessage.error('加载系统设置失败')
  }
}

const handleChangePassword = async () => {
  const valid = await passwordFormRef.value.validate()
  if (!valid) return
  changingPassword.value = true
  try {
    await changePassword(passwordForm.old_password, passwordForm.new_password)
    ElMessage.success('密码修改成功')
    passwordFormRef.value.resetFields()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '密码修改失败')
  } finally {
    changingPassword.value = false
  }
}

const handleExportData = () => {
  dataDialogVisible.value = true
}
const handleImportData = () => {
  dataDialogVisible.value = true
  dataDialogTab.value = 'import'
}
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
    dataDialogVisible.value = false
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
    dataDialogVisible.value = false
    loadSystemSettings()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '导入失败')
  } finally {
    importing.value = false
    selectedFile.value = null
  }
}

onMounted(async () => {
  await Promise.all([
    loadSystemSettings(),
    loadEmailConfig(),
    loadTemplates(),
    loadLogs(),
    loadEventTypes()
  ])
})
</script>

<style scoped lang="scss">
.settings-container {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.settings-tabs {
  background: var(--card-bg, #ffffff);
  border-radius: 8px;
  padding: 8px 16px 0;
}

.settings-card {
  margin-bottom: 16px;
  background: var(--card-bg, #ffffff);
  border: 1px solid var(--border-color, #dcdfe6);
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

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.stat-item {
  text-align: center;
  padding: 24px;
  background: var(--bg-color-light, #F5F7FA);
  border-radius: 8px;
}

.stat-value {
  font-size: 32px;
  font-weight: 600;
  color: var(--primary-color, #409EFF);
  line-height: 1.2;
}

.stat-label {
  font-size: 14px;
  color: var(--text-secondary, #909399);
  margin-top: 8px;
}

.data-actions {
  display: flex;
  gap: 12px;
}

.export-options {
  margin-bottom: 16px;
}

.upload-area {
  margin-bottom: 16px;
}

.info-alert {
  margin-bottom: 16px;

  :deep(p) {
    margin: 4px 0;
  }

  :deep(code) {
    display: inline-block;
    padding: 0 6px;
    margin: 0 2px;
    background: rgba(64, 158, 255, 0.1);
    color: var(--primary-color, #409EFF);
    border-radius: 3px;
    font-family: 'Consolas', 'Monaco', monospace;
    font-size: 12px;
  }
}

.email-form {
  max-width: 800px;
}

.form-hint {
  margin-left: 12px;
  color: var(--text-secondary, #909399);
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

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
