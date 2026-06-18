<template>
  <el-container class="layout-container">
    <el-header class="layout-header">
      <div class="header-left">
        <div class="logo">
          <el-icon class="logo-icon"><Cloudy /></el-icon>
          <h1 class="app-title">云谱</h1>
        </div>
      </div>

      <div class="header-right">
        <el-tooltip content="切换主题" placement="bottom">
          <div class="header-action">
            <ThemeToggle />
          </div>
        </el-tooltip>

        <el-tooltip content="通知" placement="bottom">
          <div class="header-action">
            <NotificationBell />
          </div>
        </el-tooltip>

        <el-dropdown trigger="click" @command="handleCommand">
          <div class="user-trigger">
            <el-avatar :size="32" class="user-avatar">
              <el-icon><UserFilled /></el-icon>
            </el-avatar>
            <span class="user-name">{{ userName }}</span>
            <el-icon class="user-arrow"><ArrowDown /></el-icon>
          </div>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="logout">
                <el-icon><SwitchButton /></el-icon>
                <span>退出登录</span>
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </el-header>

    <el-container class="main-container">
      <el-aside :width="asideWidth" class="layout-aside">
        <el-menu
          :default-active="activeMenu"
          :collapse="isCollapsed"
          :collapse-transition="false"
          router
          class="layout-menu"
        >
          <el-menu-item index="/dashboard">
            <el-icon><Odometer /></el-icon>
            <template #title>仪表盘</template>
          </el-menu-item>
          <el-menu-item index="/persons">
            <el-icon><User /></el-icon>
            <template #title>人物管理</template>
          </el-menu-item>
          <el-menu-item index="/groups">
            <el-icon><CollectionTag /></el-icon>
            <template #title>分组管理</template>
          </el-menu-item>
          <el-menu-item index="/settings">
            <el-icon><Setting /></el-icon>
            <template #title>设置</template>
          </el-menu-item>
        </el-menu>

        <div class="aside-footer">
          <el-tooltip :content="isCollapsed ? '展开' : '收起'" placement="right">
            <div class="collapse-btn" @click="isCollapsed = !isCollapsed">
              <el-icon>
                <component :is="isCollapsed ? 'Expand' : 'Fold'" />
              </el-icon>
              <span v-if="!isCollapsed" class="collapse-text">收起</span>
            </div>
          </el-tooltip>
        </div>
      </el-aside>

      <el-main class="layout-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  User, UserFilled, Odometer, Setting, SwitchButton,
  CollectionTag, Cloudy, ArrowDown, Fold, Expand
} from '@element-plus/icons-vue'
import NotificationBell from './NotificationBell.vue'
import ThemeToggle from './ThemeToggle.vue'

const router = useRouter()
const route = useRoute()

const activeMenu = computed(() => route.path)
const isCollapsed = ref(false)
const asideWidth = computed(() => isCollapsed.value ? '64px' : '200px')

const userName = computed(() => {
  try {
    const user = JSON.parse(localStorage.getItem('user') || '{}')
    return user.username || user.nickname || '我'
  } catch {
    return '我'
  }
})

const handleCommand = (command) => {
  if (command === 'logout') {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    ElMessage.success('已退出登录')
    router.push('/login')
  }
}
</script>

<style scoped lang="scss">
.layout-container {
  height: 100vh;
}

.layout-header {
  background: var(--card-bg, #FFFFFF);
  border-bottom: 1px solid var(--border-color, #E4E7ED);
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  height: 60px;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.05);
  z-index: 10;
  position: relative;
}

.header-left {
  display: flex;
  align-items: center;
}

.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 8px;
  border-radius: 8px;
  transition: background 0.2s ease;

  &:hover {
    background: var(--bg-color-light, #f5f7fa);
  }
}

.logo-icon {
  font-size: 24px;
  color: var(--primary-color, #409EFF);
}

.app-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary, #303133);
  margin: 0;
  letter-spacing: 1px;
  background: linear-gradient(135deg, #409EFF, #36cfc9);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-action {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  color: var(--text-regular, #606266);

  &:hover {
    background: var(--bg-color-light, #f5f7fa);
    color: var(--primary-color, #409EFF);
  }
}

.user-trigger {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 12px 4px 4px;
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.2s ease;
  margin-left: 4px;

  &:hover {
    background: var(--bg-color-light, #f5f7fa);
  }
}

.user-avatar {
  background: linear-gradient(135deg, #409EFF, #36cfc9);
  color: #fff;
}

.user-name {
  font-size: 14px;
  color: var(--text-primary, #303133);
  font-weight: 500;
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-arrow {
  font-size: 12px;
  color: var(--text-secondary, #909399);
}

.main-container {
  height: calc(100vh - 60px);
}

.layout-aside {
  background: var(--card-bg, #FFFFFF);
  border-right: 1px solid var(--border-color, #E4E7ED);
  display: flex;
  flex-direction: column;
  transition: width 0.2s ease;
  overflow: hidden;
}

.layout-menu {
  border: none;
  flex: 1;
  padding-top: 8px;
}

.aside-footer {
  border-top: 1px solid var(--border-lighter, #EBEEF5);
  padding: 8px 12px;
}

.collapse-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px;
  border-radius: 8px;
  cursor: pointer;
  color: var(--text-secondary, #909399);
  font-size: 14px;
  transition: all 0.2s ease;

  &:hover {
    background: var(--bg-color-light, #f5f7fa);
    color: var(--primary-color, #409EFF);
  }
}

.collapse-text {
  font-size: 14px;
}

.layout-main {
  background: var(--bg-color, #F5F7FA);
  padding: 0;
  overflow-y: auto;
}
</style>
