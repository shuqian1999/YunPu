<template>
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
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Connection, Promotion, Position } from '@element-plus/icons-vue'
import {
  getEmailConfig, updateEmailConfig, testEmailConnection, testEmailSend, sendEmailNow
} from '@/api/email'

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

// 提醒类型 text <-> array
const onReminderTypesInput = () => {
  emailForm.reminder_types = reminderTypesText.value
    .split(/[,，]/)
    .map(s => s.trim())
    .filter(Boolean)
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
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '发送失败')
  } finally {
    sendingNow.value = false
  }
}

onMounted(() => {
  loadEmailConfig()
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

.email-form {
  max-width: 800px;
}

.form-hint {
  margin-left: 12px;
  color: var(--text-secondary, #909399);
  font-size: 12px;
}
</style>
