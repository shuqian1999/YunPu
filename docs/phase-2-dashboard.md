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
    <div class="dashboard-grid">
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

      <el-card class="events-card">
        <template #header>
          <div class="card-header">
            <span class="card-title">事件时间轴</span>
          </div>
        </template>
        
        <el-timeline v-if="events.length > 0" class="events-timeline">
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
        <el-empty v-else description="暂无事件" />
      </el-card>
      
      <el-card class="reminders-card">
        <template #header>
          <div class="card-header">
            <span class="card-title">最近30天提醒</span>
          </div>
        </template>
        
        <div v-if="reminders.length > 0" class="reminders-list">
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
        <el-empty v-else description="暂无提醒" />
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { User, Document, Bell, Location } from '@element-plus/icons-vue'
import { getDashboardStats, getDashboardEvents, getDashboardReminders } from '@/api/dashboard'

const stats = ref({
  person_count: 0,
  event_count: 0,
  reminder_count: 0
})
const events = ref([])
const reminders = ref([])

const formatDate = (dateStr) => {
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  })
}

const loadDashboard = async () => {
  try {
    stats.value = await getDashboardStats()
    events.value = await getDashboardEvents({ limit: 10 })
    reminders.value = await getDashboardReminders({ days: 30 })
  } catch (error) {
    console.error('加载仪表盘失败:', error)
  }
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
  box-sizing: border-box;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.stat-card {
  display: flex;
  align-items: stretch;

  :deep(.el-card__body) {
    padding: 24px;
    width: 100%;
  }
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
  height: 100%;
}

.stat-icon {
  flex-shrink: 0;
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
  min-width: 0;
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

.events-card {
  grid-column: span 2;

  :deep(.el-card__body) {
    padding: 20px;
  }

  :deep(.el-card__header) {
    padding: 16px 20px;
    border-bottom: 1px solid #EBEEF5;
  }
}

.reminders-card {
  :deep(.el-card__body) {
    padding: 20px;
  }

  :deep(.el-card__header) {
    padding: 16px 20px;
    border-bottom: 1px solid #EBEEF5;
  }
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
  padding: 12px 0;
}

.event-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  flex-wrap: wrap;
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
  padding-left: 24px;
}

.event-location {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: #909399;
  padding-left: 24px;
}

.reminders-list {
  max-height: 480px;
  overflow-y: auto;
}

.reminder-item {
  padding: 16px 0;
  border-bottom: 1px solid #EBEEF5;
  
  &:last-child {
    border-bottom: none;
  }
}

.reminder-date {
  font-size: 14px;
  color: #409EFF;
  font-weight: 500;
  margin-bottom: 8px;
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
  margin-bottom: 4px;
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

#### 国家选择数据（新增）
```python
# app/core/countries.py
COUNTRIES = {
    "CN": {"name": "中国", "flag": "🇨🇳"},
    "US": {"name": "美国", "flag": "🇺🇸"},
    "JP": {"name": "日本", "flag": "🇯🇵"},
    "KR": {"name": "韩国", "flag": "🇰🇷"},
    "GB": {"name": "英国", "flag": "🇬🇧"},
    "DE": {"name": "德国", "flag": "🇩🇪"},
    "FR": {"name": "法国", "flag": "🇫🇷"},
    "IT": {"name": "意大利", "flag": "🇮🇹"},
    "ES": {"name": "西班牙", "flag": "🇪🇸"},
    "PT": {"name": "葡萄牙", "flag": "🇵🇹"},
    "BR": {"name": "巴西", "flag": "🇧🇷"},
    "RU": {"name": "俄罗斯", "flag": "🇷🇺"},
    "AU": {"name": "澳大利亚", "flag": "🇦🇺"},
    "CA": {"name": "加拿大", "flag": "🇨🇦"},
    "MX": {"name": "墨西哥", "flag": "🇲🇽"},
    "IN": {"name": "印度", "flag": "🇮🇳"},
    "ID": {"name": "印度尼西亚", "flag": "🇮🇩"},
    "TH": {"name": "泰国", "flag": "🇹🇭"},
    "SG": {"name": "新加坡", "flag": "🇸🇬"},
    "MY": {"name": "马来西亚", "flag": "🇲🇾"},
    "HK": {"name": "中国香港", "flag": "🇭🇰"},
    "TW": {"name": "中国台湾", "flag": "🇹🇼"},
    "MO": {"name": "中国澳门", "flag": "🇲🇴"},
    "NZ": {"name": "新西兰", "flag": "🇳🇿"},
    "ZA": {"name": "南非", "flag": "🇿🇦"},
    "EG": {"name": "埃及", "flag": "🇪🇬"},
    "NG": {"name": "尼日利亚", "flag": "🇳🇬"},
    "KE": {"name": "肯尼亚", "flag": "🇰🇪"},
    "AR": {"name": "阿根廷", "flag": "🇦🇷"},
    "CL": {"name": "智利", "flag": "🇨🇱"},
    "CO": {"name": "哥伦比亚", "flag": "🇨🇴"},
    "PE": {"name": "秘鲁", "flag": "🇵🇪"},
    "VE": {"name": "委内瑞拉", "flag": "🇻🇪"},
    "IE": {"name": "爱尔兰", "flag": "🇮🇪"},
    "NL": {"name": "荷兰", "flag": "🇳🇱"},
    "BE": {"name": "比利时", "flag": "🇧🇪"},
    "AT": {"name": "奥地利", "flag": "🇦🇹"},
    "CH": {"name": "瑞士", "flag": "🇨🇭"},
    "SE": {"name": "瑞典", "flag": "🇸🇪"},
    "NO": {"name": "挪威", "flag": "🇳🇴"},
    "DK": {"name": "丹麦", "flag": "🇩🇰"},
    "FI": {"name": "芬兰", "flag": "🇫🇮"},
    "PL": {"name": "波兰", "flag": "🇵🇱"},
    "CZ": {"name": "捷克", "flag": "🇨🇿"},
    "HU": {"name": "匈牙利", "flag": "🇭🇺"},
    "RO": {"name": "罗马尼亚", "flag": "🇷🇴"},
    "BG": {"name": "保加利亚", "flag": "🇧🇬"},
    "GR": {"name": "希腊", "flag": "🇬🇷"},
    "TR": {"name": "土耳其", "flag": "🇹🇷"},
    "AE": {"name": "阿联酋", "flag": "🇦🇪"},
    "SA": {"name": "沙特阿拉伯", "flag": "🇸🇦"},
    "IL": {"name": "以色列", "flag": "🇮🇱"}
}
```

##### 国家列表接口（新增）
```python
# app/api/countries.py
from fastapi import APIRouter
from app.core.countries import COUNTRIES

router = APIRouter(prefix="/countries", tags=["国家"])

@router.get("")
async def get_countries():
    return COUNTRIES
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
            {{ person.nickname || person.last_name }}
          </el-avatar>
        </div>
        
        <div class="person-info">
          <div class="person-name">
            {{ person.last_name }}{{ person.first_name }}
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
const formVisible = ref(false)
const editingPersonId = ref(null)

const loadPersons = async () => {
  loading.value = true
  try {
    const response = await getPersons({
      search: searchQuery.value || undefined
    })
    persons.value = response
  } catch (error) {
    ElMessage.error('加载人物列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
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

##### PersonForm.vue
```vue
<template>
  <el-dialog
    :title="editingPersonId ? '编辑人物' : '添加人物'"
    :visible.sync="visible"
    width="500px"
  >
    <el-form :model="form" label-width="80px">
      <el-form-item label="姓名">
        <el-row :gutter="12">
          <el-col :span="12">
            <el-input v-model="form.last_name" placeholder="姓" />
          </el-col>
          <el-col :span="12">
            <el-input v-model="form.first_name" placeholder="名" />
          </el-col>
        </el-row>
      </el-form-item>
      
      <el-form-item label="昵称">
        <el-input v-model="form.nickname" placeholder="昵称（可选）" />
      </el-form-item>
      
      <el-form-item label="国家">
        <el-select v-model="form.country" placeholder="请选择国家">
          <el-option
            v-for="(country, code) in countries"
            :key="code"
            :label="`${country.flag} ${country.name}`"
            :value="code"
          />
        </el-select>
      </el-form-item>
      
      <el-form-item label="地址">
        <el-input v-model="form.address" placeholder="地址（可选）" />
      </el-form-item>
      
      <el-form-item label="电话">
        <el-input v-model="form.phone" placeholder="电话（可选）" />
      </el-form-item>
      
      <el-form-item label="邮箱">
        <el-input v-model="form.email" placeholder="邮箱（可选）" />
      </el-form-item>
      
      <el-form-item label="备注">
        <el-input type="textarea" v-model="form.notes" placeholder="备注（可选）" />
      </el-form-item>
    </el-form>
    
    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" @click="handleSubmit">保存</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { createPerson, updatePerson, getPerson } from '@/api/persons'
import { getCountries } from '@/api/countries'

const props = defineProps({
  visible: Boolean,
  personId: [Number, null]
})

const emit = defineEmits(['update:visible', 'success'])

const form = ref({
  last_name: '',
  first_name: '',
  nickname: '',
  country: '',
  address: '',
  phone: '',
  email: '',
  notes: ''
})

const countries = ref({})

const resetForm = () => {
  form.value = {
    last_name: '',
    first_name: '',
    nickname: '',
    country: '',
    address: '',
    phone: '',
    email: '',
    notes: ''
  }
}

const handleSubmit = async () => {
  try {
    const data = { ...form.value }
    Object.keys(data).forEach(key => {
      if (data[key] === '') {
        data[key] = null
      }
    })
    
    if (props.personId) {
      await updatePerson(props.personId, data)
      ElMessage.success('更新成功')
    } else {
      await createPerson(data)
      ElMessage.success('创建成功')
    }
    
    emit('success')
    emit('update:visible', false)
    resetForm()
  } catch (error) {
    ElMessage.error(props.personId ? '更新失败' : '创建失败')
  }
}

watch(() => props.visible, async (val) => {
  if (val && props.personId) {
    try {
      const person = await getPerson(props.personId)
      form.value = {
        last_name: person.last_name || '',
        first_name: person.first_name || '',
        nickname: person.nickname || '',
        country: person.country || '',
        address: person.address || '',
        phone: person.phone || '',
        email: person.email || '',
        notes: person.notes || ''
      }
    } catch (error) {
      console.error('加载人物信息失败:', error)
    }
  } else if (val) {
    resetForm()
  }
})

onMounted(async () => {
  try {
    countries.value = await getCountries()
  } catch (error) {
    console.error('加载国家列表失败:', error)
  }
})
</script>
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

@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    event = db.query(Event).filter(
        Event.id == event_id,
        Event.user_id == current_user.id
    ).first()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="事件不存在"
        )
    
    return event

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

@router.put("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: int,
    event: EventUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_event = db.query(Event).filter(
        Event.id == event_id,
        Event.user_id == current_user.id
    ).first()
    
    if not db_event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="事件不存在"
        )
    
    for key, value in event.dict(exclude_unset=True).items():
        setattr(db_event, key, value)
    
    db.commit()
    db.refresh(db_event)
    return db_event

@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_event = db.query(Event).filter(
        Event.id == event_id,
        Event.user_id == current_user.id
    ).first()
    
    if not db_event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="事件不存在"
        )
    
    db.delete(db_event)
    db.commit()
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

@router.get("/{reminder_id}", response_model=ReminderResponse)
async def get_reminder(
    reminder_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    reminder = db.query(Reminder).filter(
        Reminder.id == reminder_id,
        Reminder.user_id == current_user.id
    ).first()
    
    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="提醒不存在"
        )
    
    return reminder

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

@router.put("/{reminder_id}", response_model=ReminderResponse)
async def update_reminder(
    reminder_id: int,
    reminder: ReminderUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_reminder = db.query(Reminder).filter(
        Reminder.id == reminder_id,
        Reminder.user_id == current_user.id
    ).first()
    
    if not db_reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="提醒不存在"
        )
    
    for key, value in reminder.dict(exclude_unset=True).items():
        setattr(db_reminder, key, value)
    
    db.commit()
    db.refresh(db_reminder)
    return db_reminder

@router.delete("/{reminder_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reminder(
    reminder_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_reminder = db.query(Reminder).filter(
        Reminder.id == reminder_id,
        Reminder.user_id == current_user.id
    ).first()
    
    if not db_reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="提醒不存在"
        )
    
    db.delete(db_reminder)
    db.commit()
```

---

## 数据库模型

### 事件类型模型
```python
# app/models/event_type.py
from sqlalchemy import Column, Integer, String
from app.database import Base

class EventType(Base):
    __tablename__ = "event_types"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True)
    color = Column(String(20), default="#409EFF")
```

### 事件模型
```python
# app/models/event.py
from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Event(Base):
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    person_id = Column(Integer, ForeignKey("persons.id"), nullable=True)
    event_type_id = Column(Integer, ForeignKey("event_types.id"), nullable=True)
    title = Column(String(200), nullable=False)
    description = Column(String(1000))
    event_date = Column(Date, nullable=False)
    location = Column(String(200))
    
    user = relationship("User", back_populates="events")
    person = relationship("Person", back_populates="events")
    event_type = relationship("EventType", back_populates="events")
```

### 提醒模型
```python
# app/models/reminder.py
from sqlalchemy import Column, Integer, String, Date, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Reminder(Base):
    __tablename__ = "reminders"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    person_id = Column(Integer, ForeignKey("persons.id"), nullable=True)
    title = Column(String(200), nullable=False)
    remind_date = Column(Date, nullable=False)
    is_lunar = Column(Boolean, default=False)
    enabled = Column(Boolean, default=True)
    
    user = relationship("User", back_populates="reminders")
    person = relationship("Person", back_populates="reminders")
```

---

## 验收标准

### 功能验收
- [x] 仪表盘显示人物、事件、提醒统计
- [x] 事件时间轴按时间倒序显示
- [x] 最近30天提醒按日期升序显示
- [x] 人物列表支持搜索（姓名、昵称）
- [x] 人物 CRUD 功能完整（创建、读取、更新、删除）
- [x] 事件 CRUD 功能完整
- [x] 提醒 CRUD 功能完整
- [x] 国家下拉选择（带国旗 emoji）
- [x] 中文姓名顺序（姓在前，名在后）
- [ ] 分页功能正常（待完善）
- [ ] 人物详情页（待开发）

### UI/UX 验收
- [x] 使用天蓝 #409EFF 和云朵白 #F5F7FA 主色调
- [x] 卡片悬停效果流畅
- [x] 加载状态显示正常
- [x] 空状态提示友好
- [x] 统一网格布局对齐

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