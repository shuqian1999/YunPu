# 阶段五：高级功能与体验优化

## 阶段概述

**周期**：2周  
**目标**：实现周期性提醒与通知、农历支持、关系图谱、深色模式、移动端适配、Docker Compose 部署配置

---

## 任务分解

### 5.1 周期性提醒与通知

#### 后端定时任务

##### 提醒检查服务
```python
# app/services/reminder_service.py
from sqlalchemy.orm import Session
from datetime import datetime, date, timedelta
from app.models.reminder import Reminder
from app.models.notification import Notification
from app.models.person import Person
from typing import List

class ReminderService:
    def __init__(self, db: Session):
        self.db = db
    
    def check_reminders(self, user_id: int) -> List[Notification]:
        today = date.today()
        reminders = self.db.query(Reminder).filter(
            Reminder.user_id == user_id,
            Reminder.enabled == True,
            Reminder.remind_date <= today
        ).all()
        
        notifications = []
        
        for reminder in reminders:
            remind_date = self._calculate_remind_date(reminder)
            if remind_date == today:
                notification = Notification(
                    user_id=user_id,
                    type="reminder",
                    title=reminder.title,
                    content=self._generate_reminder_content(reminder),
                    related_id=reminder.id
                )
                self.db.add(notification)
                notifications.append(notification)
                
                if reminder.repeat_type == "once":
                    reminder.enabled = False
        
        self.db.commit()
        return notifications
    
    def _calculate_remind_date(self, reminder: Reminder) -> date:
        today = date.today()
        base_date = reminder.remind_date
        
        if reminder.repeat_type == "once":
            return base_date
        elif reminder.repeat_type == "yearly":
            year = today.year
            return date(year, base_date.month, base_date.day)
        elif reminder.repeat_type == "monthly":
            day = min(base_date.day, 28)
            return date(today.year, today.month, day)
        elif reminder.repeat_type == "weekly":
            weekday = base_date.weekday()
            days_ahead = weekday - today.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            return today + timedelta(days=days_ahead)
        
        return base_date
    
    def _generate_reminder_content(self, reminder: Reminder) -> str:
        content_parts = []
        
        if reminder.person_id:
            person = self.db.query(Person).filter(
                Person.id == reminder.person_id
            ).first()
            if person:
                name = person.nickname or f"{person.first_name}{person.last_name}"
                content_parts.append(f"人物：{name}")
        
        if reminder.is_lunar:
            content_parts.append("农历")
        
        if reminder.repeat_type != "once":
            repeat_map = {
                "yearly": "每年",
                "monthly": "每月",
                "weekly": "每周"
            }
            content_parts.append(repeat_map.get(reminder.repeat_type, ""))
        
        return "，".join(content_parts)
```

##### 定时任务调度器
```python
# app/tasks/scheduler.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.database import SessionLocal
from app.services.reminder_service import ReminderService

scheduler = AsyncIOScheduler()

async def check_all_reminders():
    db = SessionLocal()
    try:
        from app.models.user import User
        users = db.query(User).all()
        
        for user in users:
            service = ReminderService(db)
            service.check_reminders(user.id)
    finally:
        db.close()

def start_scheduler():
    scheduler.add_job(
        check_all_reminders,
        'cron',
        hour=0,
        minute=0,
        id='check_reminders'
    )
    scheduler.start()
```

#### 前端通知组件

##### NotificationBell.vue
```vue
<template>
  <div class="notification-bell">
    <el-badge :value="unreadCount" :hidden="unreadCount === 0" :max="99">
      <el-button circle @click="handleClick">
        <el-icon><Bell /></el-icon>
      </el-button>
    </el-badge>
    
    <el-popover
      v-model:visible="popoverVisible"
      placement="bottom-end"
      width="400"
      trigger="click"
    >
      <template #reference>
        <div></div>
      </template>
      
      <div class="notification-header">
        <span class="notification-title">通知</span>
        <el-button text type="primary" @click="markAllAsRead">
          全部已读
        </el-button>
      </div>
      
      <el-scrollbar max-height="400px">
        <div v-loading="loading" class="notification-list">
          <div
            v-for="notification in notifications"
            :key="notification.id"
            class="notification-item"
            :class="{ 'unread': !notification.is_read }"
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
              <div class="notification-text">
                {{ notification.content }}
              </div>
              <div class="notification-time">
                {{ formatTime(notification.created_at) }}
              </div>
            </div>
          </div>
          
          <el-empty
            v-if="!loading && notifications.length === 0"
            description="暂无通知"
            :image-size="80"
          />
        </div>
      </el-scrollbar>
    </el-popover>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getNotifications, markAsRead, markAllAsRead } from '@/api/notifications'
import { formatTime } from '@/utils/date'

const router = useRouter()
const popoverVisible = ref(false)
const loading = ref(false)
const notifications = ref([])
const unreadCount = ref(0)

const loadNotifications = async () => {
  loading.value = true
  try {
    const data = await getNotifications()
    notifications.value = data
    unreadCount.value = data.filter(n => !n.is_read).length
  } catch (error) {
    console.error('加载通知失败:', error)
  } finally {
    loading.value = false
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
    await markAsRead(notification.id)
    notification.is_read = true
    unreadCount.value--
  }
  
  if (notification.type === 'reminder') {
    router.push(`/reminders/${notification.related_id}`)
  } else {
    router.push(`/events/${notification.related_id}`)
  }
  
  popoverVisible.value = false
}

const markAllAsRead = async () => {
  try {
    await markAllAsRead()
    notifications.value.forEach(n => n.is_read = true)
    unreadCount.value = 0
  } catch (error) {
    console.error('标记已读失败:', error)
  }
}

onMounted(() => {
  loadNotifications()
})
</script>

<style scoped lang="scss">
.notification-bell {
  position: relative;
}

.notification-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #E4E7ED;
}

.notification-title {
  font-size: 16px;
  font-weight: 500;
  color: #303133;
}

.notification-list {
  padding: 8px 0;
}

.notification-item {
  display: flex;
  gap: 12px;
  padding: 12px 16px;
  cursor: pointer;
  transition: background-color 0.3s;
  
  &:hover {
    background-color: #F5F7FA;
  }
  
  &.unread {
    background-color: #E1F3FF;
    
    &:hover {
      background-color: #D1E9FF;
    }
  }
}

.notification-icon {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #F5F7FA;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #909399;
  flex-shrink: 0;
}

.notification-content {
  flex: 1;
  min-width: 0;
}

.notification-title-text {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 4px;
}

.notification-text {
  font-size: 13px;
  color: #606266;
  margin-bottom: 4px;
  line-height: 1.4;
}

.notification-time {
  font-size: 12px;
  color: #909399;
}
</style>
```

---

### 5.2 农历支持

#### 后端农历转换
```python
# app/utils/lunar.py
from datetime import date
from typing import Tuple

class LunarConverter:
    @staticmethod
    def solar_to_lunar(solar_date: date) -> Tuple[int, int, int, bool]:
        from zhdate import ZhDate
        
        lunar = ZhDate.from_datetime(solar_date)
        
        year = lunar.lunar_year
        month = lunar.lunar_month
        day = lunar.lunar_day
        is_leap = lunar.is_leap
        
        return year, month, day, is_leap
    
    @staticmethod
    def lunar_to_solar(year: int, month: int, day: int, is_leap: bool = False) -> date:
        from zhdate import ZhDate
        
        lunar = ZhDate(year, month, day, is_leap)
        solar = lunar.to_datetime()
        
        return solar.date()
    
    @staticmethod
    def get_lunar_string(solar_date: date) -> str:
        year, month, day, is_leap = LunarConverter.solar_to_lunar(solar_date)
        
        month_str = f"闰{month}" if is_leap else str(month)
        day_str = LunarConverter._get_lunar_day_string(day)
        
        return f"农历{year}年{month_str}月{day_str}"
    
    @staticmethod
    def _get_lunar_day_string(day: int) -> str:
        days = [
            "初一", "初二", "初三", "初四", "初五", "初六", "初七", "初八", "初九", "初十",
            "十一", "十二", "十三", "十四", "十五", "十六", "十七", "十八", "十九", "二十",
            "廿一", "廿二", "廿三", "廿四", "廿五", "廿六", "廿七", "廿八", "廿九", "三十"
        ]
        
        return days[day - 1] if 1 <= day <= 30 else str(day)
```

---

### 5.3 关系图谱

#### 前端关系图谱组件

##### RelationGraph.vue
```vue
<template>
  <div class="relation-graph-container">
    <div class="graph-header">
      <h3 class="graph-title">关系图谱</h3>
      <el-button text type="primary" @click="handleReset">
        <el-icon><Refresh /></el-icon>
        重置
      </el-button>
    </div>
    
    <el-card class="graph-card">
      <div v-loading="loading" class="graph-canvas" ref="graphCanvas">
        <svg
          :width="canvasWidth"
          :height="canvasHeight"
          :viewBox="`0 0 ${canvasWidth} ${canvasHeight}`"
        >
          <g :transform="`translate(${panX}, ${panY}) scale(${zoom})`">
            <line
              v-for="edge in edges"
              :key="edge.id"
              :x1="getNodeX(edge.source)"
              :y1="getNodeY(edge.source)"
              :x2="getNodeX(edge.target)"
              :y2="getNodeY(edge.target)"
              :stroke="edge.relation_nature === 'qin' ? '#409EFF' : '#909399'"
              :stroke-width="2"
              :stroke-dasharray="edge.relation_nature === 'qin' ? 'none' : '5,5'"
            />
            
            <g
              v-for="node in nodes"
              :key="node.id"
              :transform="`translate(${getNodeX(node.id)}, ${getNodeY(node.id)})`"
              class="node-group"
              @click="handleNodeClick(node)"
            >
              <circle
                :r="40"
                :fill="node.relation_level > 0 ? '#E1F3FF' : '#FFE1E1'"
                :stroke="node.relation_level === 0 ? '#409EFF' : '#E4E7ED'"
                :stroke-width="node.relation_level === 0 ? 3 : 1"
              />
              
              <text
                x="0"
                y="5"
                text-anchor="middle"
                font-size="12"
                fill="#303133"
              >
                {{ node.relation_name }}
              </text>
              
              <text
                x="0"
                y="25"
                text-anchor="middle"
                font-size="10"
                fill="#909399"
              >
                {{ node.name }}
              </text>
            </g>
          </g>
        </svg>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getCalculatedRelations } from '@/api/relations'
import { getPerson } from '@/api/persons'

const loading = ref(false)
const nodes = ref([])
const edges = ref([])
const zoom = ref(1)
const panX = ref(0)
const panY = ref(0)
const canvasWidth = ref(800)
const canvasHeight = ref(600)
const graphCanvas = ref(null)

const loadGraph = async () => {
  loading.value = true
  try {
    const relations = await getCalculatedRelations()
    
    nodes.value = await Promise.all(
      relations.map(async (relation) => {
        const person = await getPerson(relation.person_id)
        return {
          id: relation.person_id,
          name: person.nickname || `${person.first_name}${person.last_name}`,
          relation_name: relation.relation_name,
          relation_level: relation.relation_level,
          is_blood: relation.is_blood
        }
      })
    )
    
    edges.value = generateEdges(nodes.value)
  } catch (error) {
    console.error('加载关系图谱失败:', error)
  } finally {
    loading.value = false
  }
}

const generateEdges = (nodes) => {
  const edges = []
  const me = nodes.find(n => n.relation_level === 0)
  
  if (!me) return edges
  
  nodes.forEach(node => {
    if (node.id !== me.id && node.relation_level === 1) {
      edges.push({
        id: `${me.id}-${node.id}`,
        source: me.id,
        target: node.id,
        relation_nature: node.is_blood ? 'qin' : 'gan'
      })
    }
  })
  
  return edges
}

const getNodeX = (nodeId) => {
  const node = nodes.value.find(n => n.id === nodeId)
  if (!node) return 0
  
  const level = node.relation_level
  const levelNodes = nodes.value.filter(n => n.relation_level === level)
  const index = levelNodes.findIndex(n => n.id === nodeId)
  
  const levelWidth = levelNodes.length * 100
  const startX = (canvasWidth.value - levelWidth) / 2 + 50
  
  return startX + index * 100
}

const getNodeY = (nodeId) => {
  const node = nodes.value.find(n => n.id === nodeId)
  if (!node) return 0
  
  const level = node.relation_level
  return 100 + level * 120
}

const handleReset = () => {
  zoom.value = 1
  panX.value = 0
  panY.value = 0
}

const handleNodeClick = (node) => {
  console.log('点击节点:', node)
}

onMounted(() => {
  loadGraph()
})
</script>

<style scoped lang="scss">
.relation-graph-container {
  padding: 16px;
}

.graph-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.graph-title {
  font-size: 16px;
  font-weight: 500;
  color: #303133;
}

.graph-card {
  height: 400px;
}

.graph-canvas {
  width: 100%;
  height: 100%;
  overflow: auto;
  background: #FFFFFF;
}

.node-group {
  cursor: pointer;
  transition: all 0.3s;
  
  &:hover {
    circle:first-child {
      stroke: #409EFF;
      stroke-width: 2;
    }
  }
}
</style>
```

---

### 5.4 深色模式

#### 前端深色模式实现

##### 主题切换组件
```vue
<template>
  <el-switch
    v-model="isDark"
    inline-prompt
    :active-icon="Moon"
    :inactive-icon="Sunny"
    @change="handleThemeChange"
  />
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Moon, Sunny } from '@element-plus/icons-vue'

const isDark = ref(false)

const handleThemeChange = (value) => {
  if (value) {
    document.documentElement.classList.add('dark')
    localStorage.setItem('theme', 'dark')
  } else {
    document.documentElement.classList.remove('dark')
    localStorage.setItem('theme', 'light')
  }
}

onMounted(() => {
  const savedTheme = localStorage.getItem('theme')
  if (savedTheme === 'dark') {
    isDark.value = true
    document.documentElement.classList.add('dark')
  }
})
</script>
```

##### SCSS 深色模式变量
```scss
// styles/variables.scss

:root {
  --primary-color: #409EFF;
  --bg-color: #F5F7FA;
  --card-bg: #FFFFFF;
  --text-primary: #303133;
  --text-secondary: #606266;
  --text-placeholder: #909399;
  --border-color: #E4E7ED;
}

.dark {
  --primary-color: #409EFF;
  --bg-color: #1a1a1a;
  --card-bg: #2d2d2d;
  --text-primary: #E5EAF3;
  --text-secondary: #A3A6AD;
  --text-placeholder: #6B7280;
  --border-color: #4B5563;
}
```

---

### 5.5 移动端适配

#### 响应式布局优化

```scss
// styles/responsive.scss

@media (max-width: 768px) {
  .dashboard-container {
    padding: 12px;
  }
  
  .stats-row {
    grid-template-columns: 1fr;
  }
  
  .content-row {
    grid-template-columns: 1fr;
  }
  
  .detail-layout {
    grid-template-columns: 1fr;
  }
  
  .right-panel {
    position: static;
  }
  
  .persons-grid {
    grid-template-columns: 1fr;
  }
  
  .settings-container {
    padding: 12px;
  }
}
```

---

### 5.6 Docker Compose 部署配置

#### docker-compose.yml
```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./yunpu-backend
      dockerfile: Dockerfile
    container_name: yunpu-backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///./data/yunpu.db
      - SECRET_KEY=${SECRET_KEY}
      - CORS_ORIGINS=http://localhost:3000,http://localhost:5173
    volumes:
      - ./data:/app/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build:
      context: ./yunpu-frontend
      dockerfile: Dockerfile
    container_name: yunpu-frontend
    ports:
      - "3000:80"
    depends_on:
      - backend
    restart: unless-stopped

volumes:
  data:
```

#### 后端 Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 前端 Dockerfile
```dockerfile
FROM node:18-alpine as builder

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

---

## 验收标准

### 功能验收
- [ ] 定时任务每日24点检查提醒
- [ ] 通知正确生成并显示
- [ ] 农历日期正确转换
- [ ] 关系图谱正确显示
- [ ] 深色模式切换正常
- [ ] 移动端布局适配良好
- [ ] Docker Compose 一键部署成功

### UI/UX 验收
- [ ] 通知图标显示未读数量
- [ ] 通知列表实时更新
- [ ] 深色模式颜色对比度符合标准
- [ ] 移动端触摸操作流畅
- [ ] 响应式断点合理

### 性能要求
- [ ] 定时任务执行时间 < 30s
- [ ] 关系图谱渲染时间 < 1s
- [ ] 深色模式切换无卡顿
- [ ] 移动端页面加载时间 < 2s

---

## 注意事项

1. **定时任务**：使用 APScheduler，确保任务不重复执行
2. **农历转换**：使用 zhdate 库，注意闰月处理
3. **深色模式**：确保所有组件都支持深色模式
4. **移动端适配**：测试主流移动设备
5. **Docker 部署**：确保数据持久化，容器重启不丢失数据

---

## 项目完成

完成阶段五后，云谱系统所有功能已开发完成，可以进行测试和部署！