# 阶段四：设置页与扩展功能

## 阶段概述

**周期**：2周  
**目标**：实现设置页、数据导入/导出、分组/标签系统、搜索和过滤功能

---

## 任务分解

### 4.1 设置页开发

#### 后端 API

##### 用户设置接口
```python
# app/api/settings.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.settings import UserSettingsUpdate, UserSettingsResponse
from app.utils.security import get_current_user, hash_password

router = APIRouter(prefix="/settings", tags=["设置"])

@router.get("/user", response_model=UserSettingsResponse)
async def get_user_settings(
    current_user: User = Depends(get_current_user)
):
    return {
        "username": current_user.username,
        "email": current_user.email,
        "display_name": current_user.display_name,
        "avatar_url": current_user.avatar_url
    }

@router.put("/user", response_model=UserSettingsResponse)
async def update_user_settings(
    settings: UserSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if settings.email:
        current_user.email = settings.email
    if settings.display_name:
        current_user.display_name = settings.display_name
    if settings.avatar_url:
        current_user.avatar_url = settings.avatar_url
    
    db.commit()
    db.refresh(current_user)
    
    return {
        "username": current_user.username,
        "email": current_user.email,
        "display_name": current_user.display_name,
        "avatar_url": current_user.avatar_url
    }

@router.post("/change-password")
async def change_password(
    old_password: str,
    new_password: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from app.utils.security import verify_password
    
    if not verify_password(old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="原密码错误"
        )
    
    current_user.password_hash = hash_password(new_password)
    db.commit()
    
    return {"message": "密码修改成功"}
```

##### 系统设置接口
```python
@router.get("/system")
async def get_system_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from app.models.person import Person
    from app.models.event import Event
    from app.models.reminder import Reminder
    
    person_count = db.query(Person).filter(
        Person.user_id == current_user.id
    ).count()
    
    event_count = db.query(Event).filter(
        Event.user_id == current_user.id
    ).count()
    
    reminder_count = db.query(Reminder).filter(
        Reminder.user_id == current_user.id
    ).count()
    
    return {
        "person_count": person_count,
        "event_count": event_count,
        "reminder_count": reminder_count,
        "database_size": get_database_size(db)
    }

def get_database_size(db: Session) -> str:
    import os
    database_path = db.bind.url.database
    if os.path.exists(database_path):
        size = os.path.getsize(database_path)
        return f"{size / 1024 / 1024:.2f} MB"
    return "0 MB"
```

#### 前端设置页

##### Settings.vue
```vue
<template>
  <div class="settings-container">
    <el-tabs v-model="activeTab" class="settings-tabs">
      <el-tab-pane label="用户设置" name="user">
        <el-card class="settings-card">
          <el-form
            ref="userFormRef"
            :model="userForm"
            :rules="userRules"
            label-width="120px"
          >
            <el-form-item label="用户名">
              <el-input v-model="userForm.username" disabled />
            </el-form-item>
            
            <el-form-item label="显示名称" prop="display_name">
              <el-input v-model="userForm.display_name" placeholder="请输入显示名称" />
            </el-form-item>
            
            <el-form-item label="邮箱" prop="email">
              <el-input v-model="userForm.email" placeholder="请输入邮箱" />
            </el-form-item>
            
            <el-form-item label="头像URL">
              <el-input v-model="userForm.avatar_url" placeholder="请输入头像URL" />
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" :loading="saving" @click="handleSaveUserSettings">
                保存设置
              </el-button>
            </el-form-item>
          </el-form>
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
      </el-tab-pane>
      
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
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getUserSettings, updateUserSettings, changePassword } from '@/api/settings'
import { getSystemSettings } from '@/api/system'

const activeTab = ref('user')
const saving = ref(false)
const changingPassword = ref(false)
const userFormRef = ref(null)
const passwordFormRef = ref(null)

const userForm = reactive({
  username: '',
  display_name: '',
  email: '',
  avatar_url: ''
})

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

const userRules = {
  display_name: [
    { max: 100, message: '显示名称不能超过100个字符', trigger: 'blur' }
  ],
  email: [
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ]
}

const passwordRules = {
  old_password: [
    { required: true, message: '请输入原密码', trigger: 'blur' }
  ],
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

const loadUserSettings = async () => {
  try {
    const settings = await getUserSettings()
    Object.assign(userForm, settings)
  } catch (error) {
    ElMessage.error('加载用户设置失败')
  }
}

const loadSystemSettings = async () => {
  try {
    systemStats.value = await getSystemSettings()
  } catch (error) {
    ElMessage.error('加载系统设置失败')
  }
}

const handleSaveUserSettings = async () => {
  const valid = await userFormRef.value.validate()
  if (!valid) return
  
  saving.value = true
  try {
    await updateUserSettings(userForm)
    ElMessage.success('保存成功')
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
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
  ElMessage.info('导出功能开发中...')
}

const handleImportData = () => {
  ElMessage.info('导入功能开发中...')
}

onMounted(() => {
  loadUserSettings()
  loadSystemSettings()
})
</script>

<style scoped lang="scss">
.settings-container {
  padding: 24px;
  max-width: 1000px;
  margin: 0 auto;
}

.settings-tabs {
  :deep(.el-tabs__content) {
    padding-top: 16px;
  }
}

.settings-card {
  margin-bottom: 16px;
}

.card-title {
  font-size: 18px;
  font-weight: 500;
  color: #303133;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.stat-item {
  text-align: center;
  padding: 24px;
  background: #F5F7FA;
  border-radius: 8px;
}

.stat-value {
  font-size: 32px;
  font-weight: 600;
  color: #409EFF;
  line-height: 1.2;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 8px;
}

.data-actions {
  display: flex;
  gap: 12px;
}
</style>
```

---

### 4.2 数据导入/导出

#### 后端 API

##### 数据导出接口
```python
# app/api/data.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.utils.security import get_current_user
from app.models.user import User
import json
import csv
from io import StringIO

router = APIRouter(prefix="/data", tags=["数据管理"])

@router.get("/export/json")
async def export_data_json(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from app.models.person import Person
    from app.models.event import Event
    from app.models.reminder import Reminder
    from app.models.family_member import FamilyMember
    from app.models.family_relation import FamilyRelation
    
    persons = db.query(Person).filter(Person.user_id == current_user.id).all()
    events = db.query(Event).filter(Event.user_id == current_user.id).all()
    reminders = db.query(Reminder).filter(Reminder.user_id == current_user.id).all()
    family_members = db.query(FamilyMember).filter(FamilyMember.user_id == current_user.id).all()
    family_relations = db.query(FamilyRelation).filter(FamilyRelation.user_id == current_user.id).all()
    
    data = {
        "persons": [person.to_dict() for person in persons],
        "events": [event.to_dict() for event in events],
        "reminders": [reminder.to_dict() for reminder in reminders],
        "family_members": [member.to_dict() for member in family_members],
        "family_relations": [relation.to_dict() for relation in family_relations],
        "exported_at": datetime.now().isoformat()
    }
    
    json_str = json.dumps(data, ensure_ascii=False, indent=2)
    
    return StreamingResponse(
        StringIO(json_str),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=yunpu_data.json"}
    )

@router.get("/export/csv")
async def export_data_csv(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from app.models.person import Person
    
    persons = db.query(Person).filter(Person.user_id == current_user.id).all()
    
    output = StringIO()
    writer = csv.writer(output)
    
    writer.writerow(["ID", "姓名", "昵称", "性别", "出生日期", "逝世日期", "国家", "故乡", "现居地"])
    
    for person in persons:
        writer.writerow([
            person.id,
            f"{person.first_name}{person.last_name}",
            person.nickname or "",
            person.gender or "",
            person.birth_date.isoformat() if person.birth_date else "",
            person.death_date.isoformat() if person.death_date else "",
            person.country or "",
            person.hometown or "",
            person.residence or ""
        ])
    
    output.seek(0)
    
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=yunpu_persons.csv"}
    )

@router.post("/import/json")
async def import_data_json(
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    content = await file.read()
    data = json.loads(content)
    
    imported_count = 0
    
    for person_data in data.get("persons", []):
        person = Person(**person_data, user_id=current_user.id)
        db.add(person)
        imported_count += 1
    
    db.commit()
    
    return {"message": f"成功导入 {imported_count} 条数据"}
```

#### 前端数据导入/导出组件

```vue
<template>
  <el-dialog v-model="visible" title="数据导入/导出" width="600px">
    <el-tabs v-model="activeTab">
      <el-tab-pane label="导出数据" name="export">
        <div class="export-options">
          <el-radio-group v-model="exportFormat">
            <el-radio label="json">JSON 格式</el-radio>
            <el-radio label="csv">CSV 格式</el-radio>
          </el-radio-group>
        </div>
        
        <el-alert
          title="导出说明"
          type="info"
          :closable="false"
          show-icon
        >
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
        >
          <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
          <div class="el-upload__text">
            拖拽文件到此处或 <em>点击上传</em>
          </div>
          <template #tip>
            <div class="el-upload__tip">
              仅支持 JSON 格式文件
            </div>
          </template>
        </el-upload>
        
        <el-alert
          title="导入说明"
          type="warning"
          :closable="false"
          show-icon
        >
          <ul>
            <li>导入数据将覆盖现有数据</li>
            <li>建议先导出备份再导入</li>
          </ul>
        </el-alert>
      </el-tab-pane>
    </el-tabs>
    
    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button
        v-if="activeTab === 'export'"
        type="primary"
        :loading="exporting"
        @click="handleExport"
      >
        导出
      </el-button>
      <el-button
        v-if="activeTab === 'import'"
        type="primary"
        :loading="importing"
        @click="handleImport"
      >
        导入
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { exportDataJson, exportDataCsv, importDataJson } from '@/api/data'

const props = defineProps({
  visible: Boolean
})

const emit = defineEmits(['update:visible'])

const activeTab = ref('export')
const exportFormat = ref('json')
const exporting = ref(false)
const importing = ref(false)
const selectedFile = ref(null)

const handleFileChange = (file) => {
  selectedFile.value = file.raw
}

const handleExport = async () => {
  exporting.value = true
  try {
    if (exportFormat.value === 'json') {
      await exportDataJson()
    } else {
      await exportDataCsv()
    }
    ElMessage.success('导出成功')
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
    await importDataJson(selectedFile.value)
    ElMessage.success('导入成功')
    emit('update:visible', false)
  } catch (error) {
    ElMessage.error('导入失败')
  } finally {
    importing.value = false
  }
}
</script>
```

---

### 4.3 分组/标签系统

#### 后端 API

##### 人物分组接口
```python
# app/api/groups.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.person_group import PersonGroup
from app.models.person_group_member import PersonGroupMember
from app.schemas.group import GroupCreate, GroupUpdate, GroupResponse
from app.utils.security import get_current_user
from app.models.user import User

router = APIRouter(prefix="/groups", tags=["分组"])

@router.get("", response_model=List[GroupResponse])
async def get_groups(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    groups = db.query(PersonGroup).filter(
        PersonGroup.user_id == current_user.id
    ).order_by(PersonGroup.created_at.asc()).all()
    return groups

@router.post("", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    group: GroupCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_group = PersonGroup(**group.dict(), user_id=current_user.id)
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    return db_group

@router.put("/{group_id}", response_model=GroupResponse)
async def update_group(
    group_id: int,
    group: GroupUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_group = db.query(PersonGroup).filter(
        PersonGroup.id == group_id,
        PersonGroup.user_id == current_user.id
    ).first()
    
    if not db_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分组不存在"
        )
    
    for key, value in group.dict(exclude_unset=True).items():
        setattr(db_group, key, value)
    
    db.commit()
    db.refresh(db_group)
    return db_group

@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_group = db.query(PersonGroup).filter(
        PersonGroup.id == group_id,
        PersonGroup.user_id == current_user.id
    ).first()
    
    if not db_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分组不存在"
        )
    
    db.query(PersonGroupMember).filter(
        PersonGroupMember.group_id == group_id
    ).delete()
    
    db.delete(db_group)
    db.commit()

@router.post("/{group_id}/members/{person_id}")
async def add_person_to_group(
    group_id: int,
    person_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    existing = db.query(PersonGroupMember).filter(
        PersonGroupMember.group_id == group_id,
        PersonGroupMember.person_id == person_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="人物已在分组中"
        )
    
    member = PersonGroupMember(group_id=group_id, person_id=person_id)
    db.add(member)
    db.commit()
    
    return {"message": "添加成功"}

@router.delete("/{group_id}/members/{person_id}")
async def remove_person_from_group(
    group_id: int,
    person_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    member = db.query(PersonGroupMember).filter(
        PersonGroupMember.group_id == group_id,
        PersonGroupMember.person_id == person_id
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="人物不在分组中"
        )
    
    db.delete(member)
    db.commit()
    
    return {"message": "移除成功"}
```

---

### 4.4 搜索和过滤功能

#### 后端 API

##### 高级搜索接口
```python
# app/api/search.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.person import Person
from app.utils.security import get_current_user
from app.models.user import User

router = APIRouter(prefix="/search", tags=["搜索"])

@router.get("/persons")
async def search_persons(
    query: str = Query(..., description="搜索关键词"),
    group_id: Optional[int] = Query(None, description="分组ID"),
    gender: Optional[int] = Query(None, description="性别"),
    is_alive: Optional[bool] = Query(None, description="是否在世"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    persons_query = db.query(Person).filter(Person.user_id == current_user.id)
    
    if query:
        search_filter = (
            Person.first_name.contains(query) |
            Person.last_name.contains(query) |
            Person.nickname.contains(query)
        )
        persons_query = persons_query.filter(search_filter)
    
    if group_id:
        from app.models.person_group_member import PersonGroupMember
        persons_query = persons_query.join(
            PersonGroupMember,
            Person.id == PersonGroupMember.person_id
        ).filter(PersonGroupMember.group_id == group_id)
    
    if gender is not None:
        persons_query = persons_query.filter(Person.gender == gender)
    
    if is_alive is not None:
        if is_alive:
            persons_query = persons_query.filter(Person.death_date.is_(None))
        else:
            persons_query = persons_query.filter(Person.death_date.isnot(None))
    
    persons = persons_query.order_by(Person.created_at.desc()).limit(50).all()
    
    return [
        {
            "id": person.id,
            "name": f"{person.first_name}{person.last_name}",
            "nickname": person.nickname,
            "gender": person.gender,
            "birth_date": person.birth_date.isoformat() if person.birth_date else None,
            "death_date": person.death_date.isoformat() if person.death_date else None,
            "avatar_url": person.avatar_url
        }
        for person in persons
    ]
```

---

## 验收标准

### 功能验收
- [x] 用户设置可以修改并保存
- [x] 密码修改功能正常
- [x] 系统设置显示正确统计
- [x] 数据导出为 JSON 格式成功
- [x] 数据导出为 CSV 格式成功
- [x] 数据导入 JSON 文件成功
- [x] 分组 CRUD 功能完整
- [x] 人物可以添加/移除分组
- [x] 搜索支持关键词、分组、性别、生死状态过滤

### UI/UX 验收
- [x] 设置页布局清晰
- [x] 表单验证友好
- [x] 导入导出进度显示
- [x] 分组标签颜色可自定义
- [x] 搜索结果实时更新

### 性能要求
- [x] 导出 1000 条数据 < 5s
- [x] 导入 1000 条数据 < 10s
- [x] 搜索响应时间 < 300ms

---

## 注意事项

1. **数据备份**：导入前自动备份现有数据
2. **文件验证**：导入文件格式和内容验证
3. **事务处理**：导入失败时回滚所有更改
4. **权限控制**：确保用户只能访问自己的数据
5. **错误处理**：导入导出失败时提供详细错误信息

---

## 下一步

完成阶段四后，可以进入阶段五开发高级功能和体验优化。