# 阶段二：仪表盘与人物基础

## 阶段概述

**周期**：2-3周  
**目标**：实现仪表盘页面、人物列表页（CRUD）、事件时间轴和日期提醒功能

---

## 任务分解

### 2.1 仪表盘框架搭建

#### 后端 API

##### 仪表盘统计接口
```python
# app/api/dashboard.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.person import Person
from app.models.event import Event
from app.models.reminder import Reminder
from app.utils.security import get_current_user
from app.models.user import User

router = APIRouter(prefix="/dashboard", tags=["仪表盘"])

@router.get("/stats")
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    person_count = db.query(Person).filter(
        Person.user_id == current_user.id
    ).count()
    
    event_count = db.query(Event).filter(
        Event.user_id == current_user.id
    ).count()
    
    reminder_count = db.query(Reminder).filter(
        Reminder.user_id == current_user.id,
        Reminder.enabled == True
    ).count()
    
    return {
        "person_count": person_count,
        "event_count": event_count,
        "reminder_count": reminder_count
    }

@router.get("/events")
async def get_dashboard_events(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    events = db.query(Event).filter(
        Event.user_id == current_user.id
    ).order_by(Event.event_date.desc()).limit(limit).all()
    
    return [
        {
            "id": event.id,
            "title": event.title,
            "description": event.description,
            "event_date": event.event_date.isoformat(),
            "location": event.location,
            "event_type": event.event_type.name,
            "event_type_color": event.event_type.color,
            "person_id": event.person_id,
            "person_name": event.person.nickname if event.person else None
        }
        for event in events
    ]

@router.get("/reminders")
async def get_dashboard_reminders(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from datetime import datetime, timedelta
    
    start_date = datetime.now().date()
    end_date = start_date + timedelta(days=days)
    
    reminders = db.query(Reminder).filter(
        Reminder.user_id == current_user.id,
        Reminder.remind_date >= start_date,
        Reminder.remind_date <= end_date,
        Reminder.enabled == True
    ).order_by(Reminder.remind_date.asc()).all()
    
    return [
        {
            "id": reminder.id,
            "title": reminder.title,
            "remind_date": reminder.remind_date.isoformat(),
            "is_lunar": reminder.is_lunar,
            "person_id": reminder.person_id,
            "person_name": reminder.person.nickname if reminder.person else None
        }
        for reminder in reminders
    ]
```

#### 前端仪表盘组件

##### Dashboard.vue
```vue
<template>
  <div class="dashboard-container">
    <div class="stats-row">
      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon person-icon">
            <el-icon><User /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.person_count }}</div>
            <div class="stat-label">人物总数</div>
          </div>
        </div>
      </el-card>
      
      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon event-icon">
            <el-icon><Document /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.event_count }}</div>
            <div class="stat-label">事件总数</div>
          </div>
        </div>
      </el-card>
      
      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon reminder-icon">
            <el-icon><Bell /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.reminder_count }}</div>
            <div class="stat-label">提醒总数</div>
          </div>
        </div>
      </el-card>
    </div>
    
    <div class="content-row">
      <el-card class="events-card">
        <template #header>
          <div class="card-header">
            <span class="card-title">事件时间轴</span>
            <el-button text type="primary" @click="viewAllEvents">查看全部</el-button>
          </div>
        </template>
        
        <el-timeline class="events-timeline">
          <el-timeline-item
            v-for="event in events"
            :key="event.id"
            :timestamp="formatDate(event.event_date)"
            placement="top"
            :color="event.event_type_color"
          >
            <div class="event-item">
              <div class="event-header">
                <span class="event-title">{{ event.title }}</span>
                <el-tag
                  v-if="event.person_name"
                  size="small"
                  type="info"
                >
                  {{ event.person_name }}
                </el-tag>
              </div>
              <div v-if="event.description" class="event-description">
                {{ event.description }}
              </div>
              <div v-if="event.location" class="event-location">
                <el-icon><Location /></el-icon>
                {{ event.location }}
              </div>
            </div>
          </el-timeline-item>
        </el-timeline>
      </el-card>
      
      <el-card class="reminders-card">
        <template #header>
          <div class="card-header">
            <span class="card-title">最近30天提醒</span>
            <el-button text type="primary" @click="viewAllReminders">查看全部</el-button>
          </div>
        </template>
        
        <div class="reminders-list">
          <div
            v-for="reminder in reminders"
            :key="reminder.id"
            class="reminder-item"
          >
            <div class="reminder-date">
              {{ formatDate(reminder.remind_date) }}
              <el-tag v-if="reminder.is_lunar" size="small" type="warning">农历</el-tag>
            </div>
            <div class="reminder-content">
              <div class="reminder-title">{{ reminder.title }}</div>
              <div v-if="reminder.person_name" class="reminder-person">
                {{ reminder.person_name }}
              </div>
            </div>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getDashboardStats, getDashboardEvents, getDashboardReminders } from '@/api/dashboard'
import { formatDate } from '@/utils/date'

const router = useRouter()
const stats = ref({
  person_count: 0,
  event_count: 0,
  reminder_count: 0
})
const events = ref([])
const reminders = ref([])

const loadDashboard = async () => {
  try {
    stats.value = await getDashboardStats()
    events.value = await getDashboardEvents()
    reminders.value = await getDashboardReminders()
  } catch (error) {
    console.error('加载仪表盘失败:', error)
  }
}

const viewAllEvents = () => {
  router.push('/events')
}

const viewAllReminders = () => {
  router.push('/reminders')
}

onMounted(() => {
  loadDashboard()
})
</script>

<style scoped lang="scss">
.dashboard-container {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  :deep(.el-card__body) {
    padding: 24px;
  }
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  
  &.person-icon {
    background: #E1F3FF;
    color: #409EFF;
  }
  
  &.event-icon {
    background: #E1F3FF;
    color: #409EFF;
  }
  
  &.reminder-icon {
    background: #E1F3FF;
    color: #409EFF;
  }
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 32px;
  font-weight: 600;
  color: #303133;
  line-height: 1.2;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}

.content-row {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-size: 18px;
  font-weight: 500;
  color: #303133;
}

.events-timeline {
  padding: 8px 0;
}

.event-item {
  padding: 8px 0;
}

.event-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.event-title {
  font-size: 16px;
  font-weight: 500;
  color: #303133;
}

.event-description {
  font-size: 14px;
  color: #606266;
  margin-bottom: 4px;
  line-height: 1.6;
}

.event-location {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: #909399;
}

.reminders-list {
  max-height: 500px;
  overflow-y: auto;
}

.reminder-item {
  padding: 12px 0;
  border-bottom: 1px solid #E4E7ED;
  
  &:last-child {
    border-bottom: none;
  }
}

.reminder-date {
  font-size: 14px;
  color: #409EFF;
  font-weight: 500;
  margin-bottom: 4px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.reminder-content {
  padding-left: 12px;
}

.reminder-title {
  font-size: 14px;
  color: #303133;
  margin-bottom: 2px;
}

.reminder-person {
  font-size: 12px;
  color: #909399;
}
</style>
```

---

### 2.2 人物列表页（CRUD 基础）

#### 后端 API

##### 人物 CRUD 接口
```python
# app/api/persons.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.person import Person
from app.schemas.person import PersonCreate, PersonUpdate, PersonResponse
from app.utils.security import get_current_user
from app.models.user import User

router = APIRouter(prefix="/persons", tags=["人物"])

@router.get("", response_model=List[PersonResponse])
async def get_persons(
    skip: int = 0,
    limit: int = 20,
    search: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Person).filter(Person.user_id == current_user.id)
    
    if search:
        query = query.filter(
            (Person.first_name.contains(search)) |
            (Person.last_name.contains(search)) |
            (Person.nickname.contains(search))
        )
    
    persons = query.order_by(Person.created_at.desc()).offset(skip).limit(limit).all()
    return persons

@router.get("/{person_id}", response_model=PersonResponse)
async def get_person(
    person_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    person = db.query(Person).filter(
        Person.id == person_id,
        Person.user_id == current_user.id
    ).first()
    
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="人物不存在"
        )
    
    return person

@router.post("", response_model=PersonResponse, status_code=status.HTTP_201_CREATED)
async def create_person(
    person: PersonCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_person = Person(**person.dict(), user_id=current_user.id)
    db.add(db_person)
    db.commit()
    db.refresh(db_person)
    return db_person

@router.put("/{person_id}", response_model=PersonResponse)
async def update_person(
    person_id: int,
    person: PersonUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_person = db.query(Person).filter(
        Person.id == person_id,
        Person.user_id == current_user.id
    ).first()
    
    if not db_person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="人物不存在"
        )
    
    for key, value in person.dict(exclude_unset=True).items():
        setattr(db_person, key, value)
    
    db.commit()
    db.refresh(db_person)
    return db_person

@router.delete("/{person_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_person(
    person_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_person = db.query(Person).filter(
        Person.id == person_id,
        Person.user_id == current_user.id
    ).first()
    
    if not db_person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="人物不存在"
        )
    
    db.delete(db_person)
    db.commit()
```

#### 前端人物列表页

##### Persons.vue
```vue
<template>
  <div class="persons-container">
    <div class="persons-header">
      <h2 class="page-title">人物列表</h2>
      <el-button type="primary" @click="handleCreate">
        <el-icon><Plus /></el-icon>
        添加人物
      </el-button>
    </div>
    
    <el-card class="search-card">
      <el-input
        v-model="searchQuery"
        placeholder="搜索人物姓名、昵称"
        clearable
        @clear="handleSearch"
        @keyup.enter="handleSearch"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
        <template #append>
          <el-button @click="handleSearch">搜索</el-button>
        </template>
      </el-input>
    </el-card>
    
    <div v-loading="loading" class="persons-grid">
      <el-card
        v-for="person in persons"
        :key="person.id"
        class="person-card"
        @click="handleView(person.id)"
      >
        <div class="person-avatar">
          <el-avatar :size="80" :src="person.avatar_url">
            {{ person.nickname || person.first_name }}
          </el-avatar>
        </div>
        
        <div class="person-info">
          <div class="person-name">
            {{ person.first_name }}{{ person.last_name }}
          </div>
          <div v-if="person.nickname" class="person-nickname">
            {{ person.nickname }}
          </div>
          <div v-if="person.is_me" class="person-me-tag">
            <el-tag type="primary" size="small">我</el-tag>
          </div>
        </div>
        
        <div class="person-actions">
          <el-button
            type="primary"
            text
            size="small"
            @click.stop="handleEdit(person.id)"
          >
            编辑
          </el-button>
          <el-button
            type="danger"
            text
            size="small"
            @click.stop="handleDelete(person.id)"
          >
            删除
          </el-button>
        </div>
      </el-card>
    </div>
    
    <el-pagination
      v-model:current-page="currentPage"
      v-model:page-size="pageSize"
      :total="total"
      :page-sizes="[12, 24, 48]"
      layout="total, sizes, prev, pager, next"
      @size-change="loadPersons"
      @current-change="loadPersons"
    />
    
    <PersonForm
      v-model:visible="formVisible"
      :person-id="editingPersonId"
      @success="handleFormSuccess"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getPersons, deletePerson } from '@/api/persons'
import PersonForm from '@/components/PersonForm.vue'

const router = useRouter()
const loading = ref(false)
const persons = ref([])
const searchQuery = ref('')
const currentPage = ref(1)
const pageSize = ref(12)
const total = ref(0)
const formVisible = ref(false)
const editingPersonId = ref(null)

const loadPersons = async () => {
  loading.value = true
  try {
    const response = await getPersons({
      skip: (currentPage.value - 1) * pageSize.value,
      limit: pageSize.value,
      search: searchQuery.value || undefined
    })
    persons.value = response
    total.value = response.length
  } catch (error) {
    ElMessage.error('加载人物列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  currentPage.value = 1
  loadPersons()
}

const handleCreate = () => {
  editingPersonId.value = null
  formVisible.value = true
}

const handleEdit = (id) => {
  editingPersonId.value = id
  formVisible.value = true
}

const handleView = (id) => {
  router.push(`/persons/${id}`)
}

const handleDelete = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除这个人物吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await deletePerson(id)
    ElMessage.success('删除成功')
    loadPersons()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const handleFormSuccess = () => {
  formVisible.value = false
  loadPersons()
}

onMounted(() => {
  loadPersons()
})
</script>

<style scoped lang="scss">
.persons-container {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
}

.persons-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-title {
  font-size: 24px;
  font-weight: 500;
  color: #303133;
}

.search-card {
  margin-bottom: 24px;
}

.persons-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
  min-height: 400px;
}

.person-card {
  cursor: pointer;
  transition: all 0.3s;
  
  &:hover {
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
    transform: translateY(-2px);
  }
  
  :deep(.el-card__body) {
    padding: 24px;
    display: flex;
    flex-direction: column;
    align-items: center;
  }
}

.person-avatar {
  margin-bottom: 16px;
}

.person-info {
  text-align: center;
  flex: 1;
  width: 100%;
}

.person-name {
  font-size: 18px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 4px;
}

.person-nickname {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}

.person-me-tag {
  margin-bottom: 8px;
}

.person-actions {
  display: flex;
  gap: 8px;
  margin-top: 16px;
}
</style>
```

---

### 2.3 事件时间轴组件

#### 后端 API

##### 事件 CRUD 接口
```python
# app/api/events.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.event import Event
from app.schemas.event import EventCreate, EventUpdate, EventResponse
from app.utils.security import get_current_user
from app.models.user import User

router = APIRouter(prefix="/events", tags=["事件"])

@router.get("", response_model=List[EventResponse])
async def get_events(
    person_id: int = None,
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Event).filter(Event.user_id == current_user.id)
    
    if person_id:
        query = query.filter(Event.person_id == person_id)
    
    events = query.order_by(Event.event_date.desc()).offset(skip).limit(limit).all()
    return events

@router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    event: EventCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_event = Event(**event.dict(), user_id=current_user.id)
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event
```

---

### 2.4 日期提醒功能

#### 后端 API

##### 提醒 CRUD 接口
```python
# app/api/reminders.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.reminder import Reminder
from app.schemas.reminder import ReminderCreate, ReminderUpdate, ReminderResponse
from app.utils.security import get_current_user
from app.models.user import User

router = APIRouter(prefix="/reminders", tags=["提醒"])

@router.get("", response_model=List[ReminderResponse])
async def get_reminders(
    person_id: int = None,
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Reminder).filter(Reminder.user_id == current_user.id)
    
    if person_id:
        query = query.filter(Reminder.person_id == person_id)
    
    reminders = query.order_by(Reminder.remind_date.asc()).offset(skip).limit(limit).all()
    return reminders

@router.post("", response_model=ReminderResponse, status_code=status.HTTP_201_CREATED)
async def create_reminder(
    reminder: ReminderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_reminder = Reminder(**reminder.dict(), user_id=current_user.id)
    db.add(db_reminder)
    db.commit()
    db.refresh(db_reminder)
    return db_reminder
```

---

## 验收标准

### 功能验收
- [ ] 仪表盘显示人物、事件、提醒统计
- [ ] 事件时间轴按时间倒序显示
- [ ] 最近30天提醒按日期升序显示
- [ ] 人物列表支持搜索（姓名、昵称）
- [ ] 人物 CRUD 功能完整（创建、读取、更新、删除）
- [ ] 事件 CRUD 功能完整
- [ ] 提醒 CRUD 功能完整
- [ ] 分页功能正常

### UI/UX 验收
- [ ] 使用天蓝 #409EFF 和云朵白 #F5F7FA 主色调
- [ ] 卡片悬停效果流畅
- [ ] 加载状态显示正常
- [ ] 空状态提示友好
- [ ] 响应式布局适配平板和桌面

### 性能要求
- [ ] 仪表盘加载时间 < 1s
- [ ] 人物列表加载时间 < 500ms
- [ ] 搜索响应时间 < 300ms

---

## 注意事项

1. **分页优化**：大数据量时使用游标分页而非偏移分页
2. **搜索优化**：使用全文索引提高搜索性能
3. **缓存策略**：仪表盘统计数据可缓存5分钟
4. **权限控制**：确保用户只能访问自己的数据
5. **数据验证**：前端和后端都需要进行数据验证

---

## 下一步

完成阶段二后，可以进入阶段三开发人物详情页和家谱可视化功能。