# 阶段一：项目初始化与安全基础

## 阶段概述

**周期**：1-2周  
**目标**：搭建项目基础架构，实现登录验证和权限控制，确保系统能正常启动并安全访问

---

## 任务分解

### 1.1 项目结构搭建

#### 后端结构
```
yunpu-backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI 应用入口
│   ├── config.py               # 配置管理
│   ├── database.py             # 数据库连接
│   ├── models/                 # SQLAlchemy 模型
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── person.py
│   │   └── ...
│   ├── schemas/                # Pydantic 模型
│   │   ├── __init__.py
│   │   ├── user.py
│   │   └── ...
│   ├── api/                    # API 路由
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   └── ...
│   ├── services/               # 业务逻辑
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   └── ...
│   ├── utils/                  # 工具函数
│   │   ├── __init__.py
│   │   ├── security.py
│   │   └── ...
│   └── core/                   # 核心配置
│       ├── __init__.py
│       ├── security.py
│       └── ...
├── tests/                      # 测试
├── .env                        # 环境变量
├── requirements.txt            # Python 依赖
├── Dockerfile                  # Docker 镜像
└── docker-compose.yml          # Docker Compose 配置
```

#### 前端结构
```
yunpu-frontend/
├── public/
│   └── index.html
├── src/
│   ├── main.js                 # Vue 应用入口
│   ├── App.vue                 # 根组件
│   ├── router/                 # 路由配置
│   │   ├── index.js
│   │   └── routes.js
│   ├── store/                  # Vuex 状态管理
│   │   ├── index.js
│   │   └── modules/
│   ├── api/                    # API 请求
│   │   ├── index.js
│   │   └── auth.js
│   ├── views/                  # 页面组件
│   │   ├── Login.vue
│   │   └── ...
│   ├── components/             # 通用组件
│   │   └── ...
│   ├── styles/                 # 样式文件
│   │   ├── variables.scss      # 样式变量（天蓝、云朵白）
│   │   ├── mixins.scss
│   │   └── global.scss
│   └── utils/                  # 工具函数
│       ├── request.js
│       └── ...
├── package.json
├── vite.config.js              # Vite 配置
└── Dockerfile
```

---

### 1.2 环境配置（.env）

#### 后端环境变量
```env
# 数据库配置
DATABASE_URL=sqlite:///./yunpu.db

# 安全配置
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# 默认用户配置
DEFAULT_USERNAME=admin
DEFAULT_PASSWORD=admin123

# CORS 配置
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# 应用配置
APP_NAME=云谱
APP_VERSION=1.0.0
DEBUG=True
```

#### 前端环境变量
```env
# API 地址
VITE_API_BASE_URL=http://localhost:8000/api

# 应用配置
VITE_APP_NAME=云谱
VITE_APP_VERSION=1.0.0
```

---

### 1.3 数据库初始化（SQLAlchemy 模型）

#### User 模型
```python
# app/models/user.py
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

#### Person 模型
```python
# app/models/person.py
from sqlalchemy import Column, Integer, String, Date, Boolean, DateTime, JSON
from sqlalchemy.sql import func
from app.database import Base

class Person(Base):
    __tablename__ = "persons"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    first_name = Column(String(50))
    last_name = Column(String(50))
    nickname = Column(String(50))
    gender = Column(Integer)
    birth_date = Column(Date)
    death_date = Column(Date)
    country = Column(String(50))
    hometown = Column(String(100))
    residence = Column(String(100))
    custom_fields = Column(JSON)
    is_me = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_contact_at = Column(DateTime(timezone=True))
```

#### 数据库初始化脚本
```python
# app/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./yunpu.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def init_db():
    from app.models import user, person
    Base.metadata.create_all(bind=engine)
```

---

### 1.4 登录页开发

#### 后端 API

##### 登录接口
```python
# app/api/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.utils.security import verify_password, create_access_token
from app.schemas.user import Token, UserLogin

router = APIRouter(prefix="/auth", tags=["认证"])

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}
```

##### 初始化用户接口
```python
@router.post("/init")
async def init_user(
    username: str,
    password: str,
    db: Session = Depends(get_db)
):
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户已存在"
        )
    
    user = User(
        username=username,
        password_hash=hash_password(password)
    )
    db.add(user)
    db.commit()
    
    return {"message": "用户创建成功"}
```

#### 前端登录页

##### Login.vue
```vue
<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <h1 class="login-title">云谱</h1>
        <p class="login-subtitle">自托管的中文个人CRM系统</p>
      </div>
      
      <el-form
        ref="loginForm"
        :model="loginForm"
        :rules="loginRules"
        class="login-form"
        @submit.prevent="handleLogin"
      >
        <el-form-item prop="username">
          <el-input
            v-model="loginForm.username"
            placeholder="用户名"
            size="large"
            prefix-icon="User"
          />
        </el-form-item>
        
        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="密码"
            size="large"
            prefix-icon="Lock"
            show-password
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        
        <el-form-item>
          <el-button
            type="primary"
            size="large"
            :loading="loading"
            class="login-button"
            @click="handleLogin"
          >
            登录
          </el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { login } from '@/api/auth'

const router = useRouter()
const loginForm = reactive({
  username: '',
  password: ''
})

const loginRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' }
  ]
}

const loading = ref(false)
const loginFormRef = ref(null)

const handleLogin = async () => {
  const valid = await loginFormRef.value.validate()
  if (!valid) return
  
  loading.value = true
  try {
    const response = await login(loginForm)
    localStorage.setItem('token', response.access_token)
    ElMessage.success('登录成功')
    router.push('/dashboard')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped lang="scss">
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #E1F3FF 0%, #F5F7FA 100%);
}

.login-card {
  width: 400px;
  padding: 48px;
  background: #FFFFFF;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.login-title {
  font-size: 28px;
  font-weight: 600;
  color: #409EFF;
  margin-bottom: 8px;
}

.login-subtitle {
  font-size: 14px;
  color: #909399;
}

.login-form {
  margin-top: 24px;
}

.login-button {
  width: 100%;
  height: 44px;
  font-size: 16px;
}
</style>
```

---

### 1.5 会话管理与权限控制

#### 后端安全工具
```python
# app/utils/security.py
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user
```

#### 前端请求拦截器
```javascript
// src/utils/request.js
import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 10000
})

request.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

request.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    if (error.response?.status === 401) {
      ElMessage.error('登录已过期，请重新登录')
      localStorage.removeItem('token')
      router.push('/login')
    } else {
      ElMessage.error(error.response?.data?.detail || '请求失败')
    }
    return Promise.reject(error)
  }
)

export default request
```

---

## 技术实现要点

### 后端技术栈
- **FastAPI**：现代 Python Web 框架
- **SQLAlchemy**：ORM 框架
- **Pydantic**：数据验证
- **python-jose**：JWT 令牌处理
- **passlib**：密码哈希
- **python-dotenv**：环境变量管理

### 前端技术栈
- **Vue 3**：渐进式 JavaScript 框架
- **Vite**：构建工具
- **Element Plus**：UI 组件库
- **Vue Router**：路由管理
- **Pinia**：状态管理
- **Axios**：HTTP 客户端

### 安全措施
1. 密码使用 bcrypt 哈希存储
2. JWT 令牌认证
3. CORS 跨域配置
4. 环境变量隔离敏感信息
5. SQL 注入防护（ORM 自动处理）

---

## 验收标准

### 功能验收
- [ ] 项目结构完整，前后端分离
- [ ] 数据库表创建成功（users、persons）
- [ ] 登录功能正常，用户名/密码验证通过
- [ ] JWT 令牌生成和验证正常
- [ ] 未登录用户无法访问受保护路由
- [ ] 登录过期后自动跳转登录页

### 代码质量
- [ ] 代码符合 PEP 8 规范
- [ ] API 文档自动生成（Swagger UI）
- [ ] 前端代码符合 ESLint 规范
- [ ] 样式使用 SCSS 变量（天蓝 #409EFF、云朵白 #F5F7FA）

### 性能要求
- [ ] 登录响应时间 < 500ms
- [ ] 数据库连接池配置合理
- [ ] 前端打包体积 < 1MB

---

## 注意事项

1. **默认用户**：首次启动时需要创建默认用户，可通过 API 或数据库脚本实现
2. **密钥安全**：生产环境必须修改 SECRET_KEY，不要使用默认值
3. **密码强度**：建议添加密码强度验证（至少8位，包含字母和数字）
4. **HTTPS**：生产环境必须使用 HTTPS 传输
5. **日志记录**：登录失败需要记录日志，防止暴力破解

---

## 下一步

完成阶段一后，系统基础架构已搭建完成，可以进入阶段二开发仪表盘和人物管理功能。