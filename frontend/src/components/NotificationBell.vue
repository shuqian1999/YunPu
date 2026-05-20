<template>
  <div class="notification-bell">
    <el-badge :value="unreadCount" :hidden="unreadCount === 0" :max="99">
      <el-button circle @click="handleClick">
        <el-icon><Bell /></el-icon>
      </el-button>
    </el-badge>

    <el-popover
      :visible="popoverVisible"
      placement="bottom-end"
      width="380"
      trigger="click"
      @update:visible="popoverVisible = $event"
    >
      <template #reference>
        <span></span>
      </template>

      <div class="notification-header">
        <span class="notification-title">通知</span>
        <el-button
          v-if="notifications.length > 0"
          text
          type="primary"
          size="small"
          @click="handleMarkAllAsRead"
        >
          全部已读
        </el-button>
      </div>

      <el-scrollbar max-height="400px">
        <div v-loading="loading" class="notification-list">
          <div
            v-for="notification in notifications"
            :key="notification.id"
            class="notification-item"
            :class="{ unread: !notification.is_read }"
            @click="handleNotificationClick(notification)"
          >
            <div class="notification-icon">
              <el-icon v-if="notification.type === 'reminder'"><Bell /></el-icon>
              <el-icon v-else><Document /></el-icon>
            </div>

            <div class="notification-content">
              <div class="notification-title-text">
                {{ notification.title }}
              </div>
              <div v-if="notification.content" class="notification-text">
                {{ notification.content }}
              </div>
              <div class="notification-time">
                {{ formatTime(notification.created_at) }}
              </div>
            </div>

            <el-button
              v-if="!notification.is_read"
              text
              size="small"
              class="mark-read-btn"
              @click.stop="handleMarkAsRead(notification)"
            >
              <el-icon><Check /></el-icon>
            </el-button>
          </div>

          <el-empty
            v-if="!loading && notifications.length === 0"
            description="暂无通知"
            :image-size="60"
          />
        </div>
      </el-scrollbar>
    </el-popover>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { Bell, Document, Check } from '@element-plus/icons-vue'
import { getNotifications, markAsRead, markAllAsRead, getUnreadCount } from '@/api/notifications'

const router = useRouter()
const popoverVisible = ref(false)
const loading = ref(false)
const notifications = ref([])
const unreadCount = ref(0)
let pollInterval = null

const formatTime = (timeStr) => {
  if (!timeStr) return ''
  const date = new Date(timeStr)
  const now = new Date()
  const diff = now - date
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days < 7) return `${days}天前`
  return date.toLocaleDateString()
}

const loadNotifications = async () => {
  loading.value = true
  try {
    const data = await getNotifications()
    notifications.value = data
    await loadUnreadCount()
  } catch (error) {
    console.error('加载通知失败:', error)
  } finally {
    loading.value = false
  }
}

const loadUnreadCount = async () => {
  try {
    const data = await getUnreadCount()
    unreadCount.value = data.count
  } catch (error) {
    console.error('获取未读数量失败:', error)
  }
}

const handleClick = () => {
  popoverVisible.value = !popoverVisible.value
  if (popoverVisible.value) {
    loadNotifications()
  }
}

const handleNotificationClick = async (notification) => {
  if (!notification.is_read) {
    await handleMarkAsRead(notification)
  }

  if (notification.type === 'reminder' && notification.related_id) {
    router.push(`/persons/${notification.related_id}`)
  }

  popoverVisible.value = false
}

const handleMarkAsRead = async (notification) => {
  try {
    await markAsRead(notification.id)
    notification.is_read = true
    unreadCount.value = Math.max(0, unreadCount.value - 1)
  } catch (error) {
    console.error('标记已读失败:', error)
  }
}

const handleMarkAllAsRead = async () => {
  try {
    await markAllAsRead()
    notifications.value.forEach(n => n.is_read = true)
    unreadCount.value = 0
  } catch (error) {
    console.error('标记全部已读失败:', error)
  }
}

onMounted(() => {
  loadUnreadCount()
  // 每分钟刷新未读数量
  pollInterval = setInterval(loadUnreadCount, 60000)
})

onUnmounted(() => {
  if (pollInterval) {
    clearInterval(pollInterval)
  }
})
</script>

<style scoped lang="scss">
.notification-bell {
  display: inline-flex;
  align-items: center;
}

.notification-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.notification-title {
  font-size: 16px;
  font-weight: 500;
  color: var(--el-text-color-primary);
}

.notification-list {
  padding: 8px 0;
}

.notification-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 16px;
  cursor: pointer;
  transition: background-color 0.3s;

  &:hover {
    background-color: var(--el-fill-color-light);
  }

  &.unread {
    background-color: var(--el-color-primary-light-9);

    &:hover {
      background-color: var(--el-color-primary-light-8);
    }
  }
}

.notification-icon {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--el-fill-color-light);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--el-text-color-secondary);
  flex-shrink: 0;
}

.notification-content {
  flex: 1;
  min-width: 0;
}

.notification-title-text {
  font-size: 14px;
  font-weight: 500;
  color: var(--el-text-color-primary);
  margin-bottom: 4px;
}

.notification-text {
  font-size: 13px;
  color: var(--el-text-color-regular);
  margin-bottom: 4px;
  line-height: 1.4;
}

.notification-time {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.mark-read-btn {
  opacity: 0;
  transition: opacity 0.3s;
}

.notification-item:hover .mark-read-btn {
  opacity: 1;
}
</style>
