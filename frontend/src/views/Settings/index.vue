<template>
  <div class="page-container">
    <div class="page-header">
      <div class="page-header-left">
        <h2 class="page-title">设置</h2>
        <span class="page-subtitle">系统配置、邮件通知与个性化</span>
      </div>
    </div>

    <el-tabs v-model="activeTab" class="settings-tabs">
      <el-tab-pane label="系统设置" name="system">
        <SystemSettings />
      </el-tab-pane>

      <el-tab-pane label="邮件通知" name="email">
        <EmailSettings />
        <EmailTemplates />
        <EmailLogs />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import SystemSettings from './components/SystemSettings.vue'
import EmailSettings from './components/EmailSettings.vue'
import EmailTemplates from './components/EmailTemplates.vue'
import EmailLogs from './components/EmailLogs.vue'

const activeTab = ref('system')
</script>

<style scoped>
.settings-tabs {
  background: var(--card-bg, #ffffff);
  border-radius: 12px;
  padding: 8px 16px 0;
  border: 1px solid var(--border-color, #dcdfe6);
}

.settings-tabs :deep(.el-tab-pane) {
  padding-top: 16px;
}
</style>
