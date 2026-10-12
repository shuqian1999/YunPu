<template>
  <el-container class="layout-container" :class="{ 'is-mobile': isMobile }">
    <el-header class="layout-header">
      <div class="header-left">
        <div class="logo">
          <el-icon class="logo-icon"><Cloudy /></el-icon>
          <h1 class="app-title">云谱</h1>
        </div>
      </div>

      <div class="header-right">
        <div class="search-trigger" data-guide="search" @click="openCommandPalette">
          <el-icon class="search-icon"><Search /></el-icon>
          <span class="search-placeholder">搜索人物 / 跳转…</span>
          <kbd class="search-kbd">Ctrl K</kbd>
        </div>

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
              <el-dropdown-item command="onboarding">
                <el-icon><Reading /></el-icon>
                <span>新手引导</span>
              </el-dropdown-item>
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
      <el-aside v-if="!isMobile" :width="asideWidth" class="layout-aside" data-guide="nav">
        <el-menu
          :default-active="activeMenu"
          :collapse="isCollapsed"
          :collapse-transition="false"
          router
          class="layout-menu"
        >
          <el-menu-item index="/dashboard" data-guide="nav-dashboard">
            <el-icon><Odometer /></el-icon>
            <template #title>仪表盘</template>
          </el-menu-item>
          <el-menu-item index="/persons" data-guide="nav-persons">
            <el-icon><User /></el-icon>
            <template #title>人物管理</template>
          </el-menu-item>
          <el-menu-item index="/family" data-guide="nav-family">
            <el-icon><Share /></el-icon>
            <template #title>家族关系</template>
          </el-menu-item>
          <el-menu-item index="/relationships" data-guide="nav-graph">
            <el-icon><Connection /></el-icon>
            <template #title>关系图谱</template>
          </el-menu-item>
          <el-menu-item index="/groups" data-guide="nav-groups">
            <el-icon><CollectionTag /></el-icon>
            <template #title>分组管理</template>
          </el-menu-item>
          <el-menu-item index="/settings" data-guide="nav-settings">
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

    <!-- 移动端底部 Tab Bar -->
    <nav v-if="isMobile" class="mobile-tabbar" data-guide="tabbar">
      <div
        v-for="tab in mobileTabs"
        :key="tab.path"
        class="tabbar-item"
        :class="{ active: isTabActive(tab) }"
        :data-guide="tab.guide"
        @click="router.push(tab.path)"
      >
        <el-icon class="tabbar-icon"><component :is="tab.icon" /></el-icon>
        <span class="tabbar-label">{{ tab.label }}</span>
      </div>
    </nav>

    <CommandPalette ref="commandPaletteRef" />
    <OnboardingGuide ref="onboardingRef" :is-mobile="isMobile" />
  </el-container>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  User, UserFilled, Odometer, Setting, SwitchButton,
  CollectionTag, Cloudy, ArrowDown, Fold, Expand, Share, Search,
  Connection, Reading
} from '@element-plus/icons-vue'
import NotificationBell from './NotificationBell.vue'
import ThemeToggle from './ThemeToggle.vue'
import CommandPalette from './CommandPalette.vue'
import OnboardingGuide from './OnboardingGuide.vue'

const router = useRouter()
const route = useRoute()

const commandPaletteRef = ref(null)
const onboardingRef = ref(null)
const openCommandPalette = () => commandPaletteRef.value?.open()

// 响应式：≤768px 切换为移动端形态（隐藏侧栏，显示底部 Tab Bar）
const isMobile = ref(false)
const mql = window.matchMedia('(max-width: 768px)')
const syncMobile = (e) => { isMobile.value = e.matches }
syncMobile(mql)

const mobileTabs = [
  { path: '/dashboard', label: '首页', icon: Odometer, guide: 'tab-dashboard', match: ['/dashboard'] },
  { path: '/persons', label: '人物', icon: User, guide: 'tab-persons', match: ['/persons'] },
  { path: '/relationships', label: '关系', icon: Connection, guide: 'tab-graph', match: ['/relationships', '/family'] },
  { path: '/groups', label: '分组', icon: CollectionTag, guide: 'tab-groups', match: ['/groups'] },
  { path: '/settings', label: '我的', icon: Setting, guide: 'tab-settings', match: ['/settings'] }
]

const isTabActive = (tab) => tab.match.some((p) => route.path === p || route.path.startsWith(`${p}/`))

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
  } else if (command === 'onboarding') {
    onboardingRef.value?.start()
  }
}

onMounted(() => {
  mql.addEventListener('change', syncMobile)
  // 首次登录的用户自动播放一次新手引导
  setTimeout(() => onboardingRef.value?.autoStart(), 600)
})

onBeforeUnmount(() => {
  mql.removeEventListener('change', syncMobile)
})
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

.search-trigger {
  display: flex;
  align-items: center;
  gap: 8px;
  height: 36px;
  min-width: 210px;
  padding: 0 12px;
  margin-right: 8px;
  border-radius: 8px;
  border: 1px solid var(--border-color, #dcdfe6);
  background: var(--bg-color, #f5f7fa);
  color: var(--text-secondary, #909399);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    border-color: var(--primary-color-light-5, #a0cfff);
    background: var(--card-bg, #ffffff);
    box-shadow: 0 0 0 3px var(--primary-color-light-9, #ecf5ff);
  }
}

.search-icon {
  font-size: 16px;
  flex-shrink: 0;
}

.search-placeholder {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.search-kbd {
  font-family: inherit;
  font-size: 11px;
  line-height: 1;
  color: var(--text-secondary, #909399);
  background: var(--card-bg, #ffffff);
  border: 1px solid var(--border-color, #dcdfe6);
  border-radius: 4px;
  padding: 3px 5px;
}

@media (max-width: 768px) {
  .search-trigger {
    min-width: 0;
    width: 36px;
    padding: 0;
    justify-content: center;
  }
  .search-placeholder,
  .search-kbd {
    display: none;
  }
}

/* ---------------- 移动端 ---------------- */
.mobile-tabbar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 100;
  display: flex;
  height: calc(56px + env(safe-area-inset-bottom, 0px));
  padding-bottom: env(safe-area-inset-bottom, 0px);
  background: var(--card-bg, #ffffff);
  border-top: 1px solid var(--border-color, #e4e7ed);
  box-shadow: 0 -2px 12px rgba(0, 21, 41, 0.06);
}

.tabbar-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 3px;
  height: 56px;
  color: var(--text-secondary, #909399);
  font-size: 11px;
  cursor: pointer;
  transition: color 0.2s ease;
  user-select: none;
  -webkit-tap-highlight-color: transparent;

  &:active {
    background: var(--bg-color-light, #f5f7fa);
  }

  &.active {
    color: var(--primary-color, #409eff);
    font-weight: 500;
  }
}

.tabbar-icon {
  font-size: 21px;
}

.is-mobile {
  .layout-header {
    padding: 0 12px;
  }

  .user-name,
  .user-arrow {
    display: none;
  }

  .user-trigger {
    padding: 4px;
    margin-left: 0;
  }

  .main-container {
    height: calc(100vh - 60px);
  }

  .layout-main {
    padding-bottom: calc(56px + env(safe-area-inset-bottom, 0px));
  }
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
