# YunPu - 云谱

一个自托管的中文个人CRM系统，帮助您管理人际关系、事件和家族关系。

## ✨ 功能特性

### 📊 仪表盘
- 人物、事件、提醒统计概览
- 事件时间轴展示
- 最近30天提醒列表

### 👥 人物管理
- 人物信息 CRUD
- 支持搜索和筛选
- 自定义分组管理
- 头像上传

### 📅 事件与提醒
- 事件时间轴记录
- 生日/纪念日提醒
- 支持农历日期
- 周期性提醒（年/月/周）

### 👨‍👩‍👧‍👦 家谱功能
- 家族树可视化
- 亲属关系计算
- 关系图谱展示
- 支持亲生/继亲/义亲关系

### ⚙️ 设置管理
- 用户设置与密码修改
- 数据统计展示
- 数据导入/导出（JSON/CSV）

### 🎨 用户体验
- 深色模式支持
- 响应式设计
- 移动端适配
- 实时通知系统

## 🛠️ 技术栈

| 分类 | 技术 | 版本 |
|------|------|------|
| 前端 | Vue.js | 3.x |
| 前端框架 | Element Plus | 2.x |
| 后端 | FastAPI | 0.100+ |
| ORM | SQLAlchemy | 2.x |
| 数据库 | SQLite | 默认 |
| 构建工具 | Vite | 6.x |
| 部署 | Docker Compose | 3.8+ |

## 🚀 快速开始

### 环境要求
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose（可选）

### 开发环境

**后端启动**
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# 修改 .env 中的配置
uvicorn app.main:app --reload
```

**前端启动**
```bash
cd frontend
npm install
cp .env.example .env
# 修改 .env 中的配置
npm run dev
```

### Docker Compose 部署

```bash
# 克隆项目
git clone <repository-url>
cd YunPu

# 创建环境变量文件
cp env.example .env
# 根据需要修改 .env 中的配置，特别是 SECRET_KEY

# 启动服务
docker-compose up -d
```

服务启动后：
- 前端访问：http://localhost:3000
- 后端 API：http://localhost:8000
- Swagger 文档：http://localhost:8000/docs

### 默认账号
```
用户名：admin
密码：admin123
```

> ⚠️ 生产环境请务必修改默认密码！

## 📁 项目结构

```
YunPu/
├── backend/                    # 后端代码
│   ├── app/
│   │   ├── api/v1/            # API 路由
│   │   ├── core/              # 核心配置
│   │   ├── models/            # 数据库模型
│   │   ├── schemas/           # Pydantic 模型
│   │   ├── services/          # 业务服务
│   │   ├── tasks/             # 定时任务
│   │   ├── utils/             # 工具函数
│   │   └── main.py            # 应用入口
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                   # 前端代码
│   ├── src/
│   │   ├── views/             # 页面组件
│   │   ├── components/        # 通用组件
│   │   ├── api/               # API 请求
│   │   ├── router/            # 路由配置
│   │   ├── stores/            # 状态管理
│   │   ├── styles/            # 样式文件
│   │   └── utils/             # 工具函数
│   ├── package.json
│   └── Dockerfile
├── docs/                       # 项目文档
├── docker-compose.yml          # Docker Compose 配置
└── README.md
```

## 🔧 配置说明

### 环境变量

后端配置（`.env`）：
```env
# 数据库配置
DATABASE_URL=sqlite:///./data/yunpu.db

# 安全配置
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# 默认用户
DEFAULT_USERNAME=admin
DEFAULT_PASSWORD=admin123

# CORS配置
CORS_ORIGINS=http://localhost:3000
```

## 📡 API 文档

启动服务后，访问以下地址查看 API 文档：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

### 开发流程
1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/xxx`)
3. 提交更改 (`git commit -m 'feat: xxx'`)
4. 推送到分支 (`git push origin feature/xxx`)
5. 打开 Pull Request

### 代码规范
- 后端：遵循 PEP 8 规范
- 前端：遵循 ESLint 规范

## 📄 许可证

MIT License

## 📧 联系方式

如有问题或建议，欢迎提交 Issue。

---

**云谱** - 记录生命中的每一个重要关系 ✨
