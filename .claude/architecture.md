# 智能学习计划系统 - 架构设计文档

## 项目概述

用户输入学习目标 + 个人情况 → LLM分析需求 → 生成学习计划 → 推荐学习内容 → 制定学习方式 → 跟踪学习进度

---

## 技术栈

| 层级 | 技术选型 |
|-----|---------|
| 前端 | React + TypeScript + Tailwind CSS |
| 后端 | FastAPI (Python 3.11+) |
| 数据库 | PostgreSQL |
| 认证 | JWT + OAuth2 |
| 文件存储 | MinIO / AWS S3 |
| LLM | DeepSeek R1 |
| 内容推荐 | 基于向量相似度的推荐算法 (scikit-learn) |
| 进度跟踪 | 自定义打卡系统 |

---

## 1. 系统架构图

```mermaid
graph TB
    subgraph Frontend["前端 (React)"]
        UI[用户界面]
        Pages[页面路由]
        Components[组件库]
    end

    subgraph Backend["后端 (FastAPI)"]
        API[REST API]
        Services[业务服务层]
        Auth[认证中间件]
    end

    subgraph Database["数据层"]
        DB[(PostgreSQL)]
        Storage[对象存储<br/>MinIO/S3]
    end

    subgraph External["外部AI服务"]
        DeepSeek[DeepSeek R1<br/>需求分析+计划生成]
    end

    subgraph Analytics["数据分析"]
        Progress[进度统计]
        Recommend[内容推荐引擎<br/>scikit-learn]
    end

    UI --> Pages
    Pages --> Components
    UI --> API
    API --> Auth
    API --> Services
    Services --> DB
    Services --> Storage
    Services --> DeepSeek
    Services --> Progress
    Services --> Recommend
```

---

## 2. 核心业务流程图

> **关键特性**: 每一步都需要用户确认，不满意可重新生成或调整

```mermaid
flowchart TD
    Start([用户开始]) --> Auth{已登录?}
    Auth -->|否| Login[登录/注册]
    Auth -->|是| Input[输入学习目标 + 个人情况]
    Login --> Input

    Input --> CreatePlan[创建学习计划项目]

    %% 阶段1: 需求分析
    CreatePlan --> GenAnalysis[点击"分析需求"]
    GenAnalysis --> LLMAnalysis[调用DeepSeek R1分析]
    LLMAnalysis --> ShowAnalysis[显示需求分析报告]
    ShowAnalysis --> ConfirmAnalysis{用户确认?}
    ConfirmAnalysis -->|不满意| RegenerateAnalysis[重新分析]
    RegenerateAnalysis --> LLMAnalysis
    ConfirmAnalysis -->|满意| ConfirmAnalysisYes[确认分析]

    %% 阶段2: 生成学习计划
    ConfirmAnalysisYes --> GenPlan[点击"生成学习计划"]
    GenPlan --> LLMPlan[LLM生成学习路线图]
    LLMPlan --> ShowPlan[显示学习计划<br/>阶段+里程碑+时间线]
    ShowPlan --> ReviewPlan{用户确认?}
    ReviewPlan -->|不满意| AdjustPlan[调整计划参数]
    AdjustPlan --> LLMPlan
    ReviewPlan -->|满意| ConfirmPlan[确认学习计划]

    %% 阶段3: 推荐学习内容
    ConfirmPlan --> GenContent[点击"推荐学习内容"]
    GenContent --> RecommendLoop[为每个阶段推荐资源]
    RecommendLoop --> ShowContent[显示学习资源列表<br/>课程/书籍/视频/文章]
    ShowContent --> ReviewContent{逐个确认资源}
    ReviewContent -->|某个不满意| ReplaceContent[替换该资源]
    ReplaceContent --> ShowContent
    ReviewContent -->|全部满意| ConfirmContent[确认所有资源]

    %% 阶段4: 制定学习方式
    ConfirmContent --> GenMethod[点击"制定学习方式"]
    GenMethod --> LLMMethod[LLM生成学习方法建议]
    LLMMethod --> ShowMethod[显示学习方式<br/>时间安排/学习技巧/复习策略]
    ShowMethod --> ReviewMethod{用户确认?}
    ReviewMethod -->|不满意| AdjustMethod[调整学习方式]
    AdjustMethod --> LLMMethod
    ReviewMethod -->|满意| StartLearning[开始学习]

    %% 阶段5: 学习跟踪
    StartLearning --> Learning[执行学习计划]
    Learning --> CheckIn[每日打卡]
    CheckIn --> UpdateProgress[更新进度]
    UpdateProgress --> ViewStats[查看统计数据]
    ViewStats --> Adjust{需要调整?}
    Adjust -->|是| AdjustPlanMid[调整计划]
    AdjustPlanMid --> Learning
    Adjust -->|否| Continue{继续学习?}
    Continue -->|是| Learning
    Continue -->|否| Complete[计划完成]

    Complete --> End([结束])
```

### 用户交互流程

```mermaid
stateDiagram-v2
    [*] --> 计划创建
    计划创建 --> 需求分析中: 点击分析需求
    需求分析中 --> 需求待确认: AI分析完成
    需求待确认 --> 需求待确认: 重新分析
    需求待确认 --> 计划生成中: 确认分析
    计划生成中 --> 计划待确认: 计划生成完成
    计划待确认 --> 计划待确认: 调整计划
    计划待确认 --> 内容推荐中: 确认计划
    内容推荐中 --> 内容待确认: 推荐完成
    内容待确认 --> 内容待确认: 替换资源
    内容待确认 --> 方式制定中: 确认内容
    方式制定中 --> 方式待确认: 方式生成完成
    方式待确认 --> 方式待确认: 调整方式
    方式待确认 --> 学习进行中: 开始学习
    学习进行中 --> 学习进行中: 每日打卡
    学习进行中 --> 计划完成: 完成所有阶段
    计划完成 --> [*]
```

---

## 3. 数据模型图

```mermaid
erDiagram
    auth_users ||--o{ learning_plans : creates
    learning_plans ||--o{ need_analysis : has
    learning_plans ||--o{ plan_stages : contains
    plan_stages ||--o{ learning_resources : has
    plan_stages ||--o{ learning_methods : has
    learning_plans ||--o{ progress_records : tracks
    learning_plans ||--o{ check_ins : has

    auth_users {
        uuid id PK
        string email
        string encrypted_password
        datetime created_at
    }

    learning_plans {
        uuid id PK
        uuid user_id FK
        string title "学习计划标题"
        text goal "学习目标"
        text user_background "用户背景信息"
        int total_duration_days "总学习时长(天)"
        string difficulty_level "难度: beginner/intermediate/advanced"
        string status "状态: draft/analysis/planning/content/method/active/completed/paused"
        datetime start_date "开始日期"
        datetime target_end_date "目标结束日期"
        datetime created_at
        datetime updated_at
    }

    need_analysis {
        uuid id PK
        uuid plan_id FK
        text analysis_result "需求分析结果"
        json key_points "关键要点JSON"
        json recommended_path "推荐学习路径JSON"
        boolean confirmed "是否已确认"
        int version "版本号"
        datetime created_at
    }

    plan_stages {
        uuid id PK
        uuid plan_id FK
        int order_index "阶段顺序"
        string stage_name "阶段名称"
        text description "阶段描述"
        int duration_days "阶段时长(天)"
        json milestones "里程碑JSON数组"
        string status "状态: pending/in_progress/completed"
        boolean confirmed "是否已确认"
        datetime created_at
    }

    learning_resources {
        uuid id PK
        uuid stage_id FK
        string resource_type "资源类型: course/book/video/article/practice"
        string title "资源标题"
        text description "资源描述"
        string url "资源链接"
        string provider "提供方"
        int estimated_hours "预计学习时长(小时)"
        string difficulty "难度"
        boolean is_free "是否免费"
        int order_index "推荐顺序"
        boolean user_selected "用户是否选择"
        datetime created_at
    }

    learning_methods {
        uuid id PK
        uuid stage_id FK
        string method_type "方法类型: time_management/study_technique/review_strategy"
        string title "方法标题"
        text content "方法内容"
        json schedule "时间安排JSON"
        int order_index "顺序"
        boolean confirmed "是否已确认"
        datetime created_at
    }

    progress_records {
        uuid id PK
        uuid plan_id FK
        uuid stage_id FK "可选"
        date record_date "记录日期"
        int study_minutes "学习时长(分钟)"
        text content_studied "学习内容"
        int completion_percentage "完成百分比"
        text notes "学习笔记"
        datetime created_at
    }

    check_ins {
        uuid id PK
        uuid plan_id FK
        date check_in_date "打卡日期"
        boolean completed "是否完成"
        int study_minutes "学习时长(分钟)"
        text reflection "学习反思"
        int mood_score "心情评分 1-5"
        datetime created_at
    }
```

### 状态流转说明

| 字段 | 可能值 | 说明 |
|-----|-------|------|
| learning_plans.status | draft | 刚创建，还没开始 |
| | analysis | 需求分析阶段 |
| | planning | 计划生成阶段 |
| | content | 内容推荐阶段 |
| | method | 方式制定阶段 |
| | active | 学习进行中 |
| | completed | 已完成 |
| | paused | 已暂停 |
| plan_stages.status | pending | 等待开始 |
| | in_progress | 进行中 |
| | completed | 已完成 |
| learning_plans.difficulty_level | beginner | 初学者 |
| | intermediate | 中级 |
| | advanced | 高级 |

---

## 4. 页面结构图

```mermaid
graph TB
    subgraph Auth["认证页面"]
        LoginPage[登录页 /login]
        RegisterPage[注册页 /register]
    end

    subgraph Main["主要页面"]
        HomePage[首页 /]
        PlansPage[我的学习计划 /plans]
        CreatePage[创建计划 /create]
        DetailPage[计划详情 /plans/:id]
        ProgressPage[学习进度 /plans/:id/progress]
        StatsPage[数据统计 /plans/:id/stats]
    end

    subgraph DetailFeatures["计划详情页功能"]
        GoalSection[目标展示区]
        AnalysisSection[需求分析区]
        StagesList[学习阶段列表]
        ResourcesList[学习资源列表]
        MethodsSection[学习方式区]
        Actions[操作按钮<br/>重新生成/调整/开始学习]
    end

    subgraph ProgressFeatures["进度页面功能"]
        CheckInCard[每日打卡卡片]
        ProgressChart[进度图表]
        TimelineView[时间线视图]
        NotesSection[学习笔记区]
    end

    HomePage --> CreatePage
    HomePage --> PlansPage
    LoginPage --> HomePage
    RegisterPage --> LoginPage
    PlansPage --> DetailPage
    CreatePage --> DetailPage
    DetailPage --> ProgressPage
    DetailPage --> StatsPage

    DetailPage --> GoalSection
    DetailPage --> AnalysisSection
    DetailPage --> StagesList
    DetailPage --> ResourcesList
    DetailPage --> MethodsSection
    DetailPage --> Actions

    ProgressPage --> CheckInCard
    ProgressPage --> ProgressChart
    ProgressPage --> TimelineView
    ProgressPage --> NotesSection
```

---

## 5. API 设计

### 学习计划 API

| 方法 | 路径 | 描述 |
|-----|------|-----|
| POST | /api/v1/plans | 创建学习计划 |
| GET | /api/v1/plans | 获取学习计划列表 |
| GET | /api/v1/plans/{id} | 获取计划详情（包含所有阶段、资源、方法） |
| PATCH | /api/v1/plans/{id} | 更新计划（标题、目标、背景） |
| DELETE | /api/v1/plans/{id} | 删除计划 |
| POST | /api/v1/plans/{id}/start | 开始执行计划 |
| POST | /api/v1/plans/{id}/pause | 暂停计划 |
| POST | /api/v1/plans/{id}/complete | 完成计划 |

### 需求分析 API

| 方法 | 路径 | 描述 |
|-----|------|-----|
| POST | /api/v1/analysis/generate | LLM分析用户需求 |
| POST | /api/v1/analysis/regenerate | 重新分析需求 |
| POST | /api/v1/analysis/{id}/confirm | 确认需求分析 |

### 学习阶段 API

| 方法 | 路径 | 描述 |
|-----|------|-----|
| GET | /api/v1/plans/{id}/stages | 获取阶段列表 |
| POST | /api/v1/stages/generate | LLM生成学习阶段 |
| POST | /api/v1/stages/regenerate | 重新生成阶段 |
| PATCH | /api/v1/stages/{id} | 修改阶段信息 |
| POST | /api/v1/stages/{id}/confirm | 确认阶段 |
| POST | /api/v1/stages/confirm-all | 确认所有阶段 |

### 学习资源 API

| 方法 | 路径 | 描述 |
|-----|------|-----|
| POST | /api/v1/resources/recommend | 为阶段推荐学习资源 |
| GET | /api/v1/stages/{id}/resources | 获取阶段的资源列表 |
| POST | /api/v1/resources/{id}/select | 用户选择资源 |
| POST | /api/v1/resources/{id}/replace | 替换资源 |
| DELETE | /api/v1/resources/{id} | 删除资源 |

### 学习方式 API

| 方法 | 路径 | 描述 |
|-----|------|-----|
| POST | /api/v1/methods/generate | LLM生成学习方式建议 |
| POST | /api/v1/methods/regenerate | 重新生成学习方式 |
| PATCH | /api/v1/methods/{id} | 修改学习方式 |
| POST | /api/v1/methods/{id}/confirm | 确认学习方式 |

### 进度跟踪 API

| 方法 | 路径 | 描述 |
|-----|------|-----|
| POST | /api/v1/progress/record | 记录学习进度 |
| GET | /api/v1/plans/{id}/progress | 获取计划的进度记录 |
| GET | /api/v1/plans/{id}/stats | 获取统计数据 |
| POST | /api/v1/check-in | 每日打卡 |
| GET | /api/v1/plans/{id}/check-ins | 获取打卡记录 |

---

## 6. 外部 API 集成

### 6.1 DeepSeek R1 (需求分析 + 计划生成)

```python
# 使用 httpx 或 requests 库调用
端点: https://api.deepseek.com/v1/chat/completions
认证: Bearer Token
模型: deepseek-reasoner
```

#### 需求分析请求示例 (Python):
```python
import httpx

async def analyze_learning_needs(goal: str, background: str, api_key: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": "deepseek-reasoner",
                "messages": [
                    {
                        "role": "system",
                        "content": "你是一个专业的学习规划师，擅长分析用户的学习需求并提供个性化建议..."
                    },
                    {
                        "role": "user",
                        "content": f"学习目标: {goal}\n用户背景: {background}\n可用时间: [时间信息]"
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 4000
            }
        )
        return response.json()
```

#### 学习计划生成请求示例 (Python):
```python
async def generate_learning_plan(analysis_result: str, api_key: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": "deepseek-reasoner",
                "messages": [
                    {
                        "role": "system",
                        "content": "你是一个专业的学习规划师，根据需求分析结果制定详细的学习计划..."
                    },
                    {
                        "role": "user",
                        "content": f"需求分析: {analysis_result}\n生成包含阶段、里程碑、时间线的学习计划"
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 4000
            }
        )
        return response.json()
```

---

## 7. 学习资源类型

| 类型ID | 类型名称 | 描述 |
|-------|---------|-----|
| course | 在线课程 | Coursera、Udemy等平台课程 |
| book | 书籍 | 纸质书或电子书 |
| video | 视频教程 | YouTube、B站等视频资源 |
| article | 文章/博客 | 技术文章、教程博客 |
| practice | 实践项目 | 动手项目、练习题 |
| documentation | 官方文档 | 技术官方文档 |
| community | 社区资源 | 论坛、问答社区 |

---

## 8. 学习方式类型

| 方式ID | 方式名称 | 描述 |
|-------|---------|-----|
| time_management | 时间管理 | 番茄工作法、时间块等 |
| study_technique | 学习技巧 | 费曼学习法、思维导图等 |
| review_strategy | 复习策略 | 间隔重复、主动回忆等 |
| note_taking | 笔记方法 | 康奈尔笔记法、卡片笔记等 |
| practice_method | 练习方法 | 刻意练习、项目驱动等 |

---

## 9. Python 项目结构

```
learning-system/
├── backend/                    # FastAPI 后端
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py            # FastAPI 应用入口
│   │   ├── config.py          # 配置管理
│   │   ├── dependencies.py    # 依赖注入
│   │   ├── api/               # API 路由
│   │   │   ├── __init__.py
│   │   │   ├── v1/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── plans.py
│   │   │   │   ├── analysis.py
│   │   │   │   ├── stages.py
│   │   │   │   ├── resources.py
│   │   │   │   ├── methods.py
│   │   │   │   └── progress.py
│   │   ├── models/            # SQLAlchemy 模型
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── plan.py
│   │   │   ├── stage.py
│   │   │   └── progress.py
│   │   ├── schemas/           # Pydantic 模式
│   │   │   ├── __init__.py
│   │   │   ├── plan.py
│   │   │   ├── analysis.py
│   │   │   └── progress.py
│   │   ├── services/          # 业务逻辑层
│   │   │   ├── __init__.py
│   │   │   ├── llm_service.py
│   │   │   ├── plan_service.py
│   │   │   ├── recommendation_service.py
│   │   │   └── progress_service.py
│   │   ├── core/              # 核心功能
│   │   │   ├── __init__.py
│   │   │   ├── security.py    # JWT 认证
│   │   │   ├── database.py    # 数据库连接
│   │   │   └── storage.py     # 文件存储
│   │   └── utils/             # 工具函数
│   │       ├── __init__.py
│   │       └── helpers.py
│   ├── tests/                 # 测试
│   │   ├── __init__.py
│   │   ├── test_api/
│   │   └── test_services/
│   ├── alembic/               # 数据库迁移
│   │   ├── versions/
│   │   └── env.py
│   ├── requirements.txt       # 依赖列表
│   ├── pyproject.toml         # 项目配置
│   └── .env.example           # 环境变量示例
├── frontend/                  # React 前端
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/          # API 调用
│   │   ├── hooks/
│   │   └── utils/
│   ├── package.json
│   └── vite.config.ts
└── docker-compose.yml         # Docker 编排
```

### Python 依赖 (requirements.txt)

```txt
# Web 框架
fastapi==0.115.0
uvicorn[standard]==0.32.0
python-multipart==0.0.12

# 数据库
sqlalchemy==2.0.36
alembic==1.14.0
psycopg2-binary==2.9.10
asyncpg==0.30.0

# 认证
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.12

# HTTP 客户端
httpx==0.28.1
aiohttp==3.11.10

# 数据验证
pydantic==2.10.3
pydantic-settings==2.6.1
email-validator==2.2.0

# 机器学习/推荐
scikit-learn==1.6.0
numpy==2.2.1
pandas==2.2.3

# 对象存储
minio==7.2.11
boto3==1.35.90  # 如果使用 AWS S3

# 缓存 (可选)
redis==5.2.1
hiredis==3.1.0

# 工具
python-dotenv==1.0.1
loguru==0.7.3
```

---

## 10. 环境变量

```env
# 数据库配置
DATABASE_URL=postgresql://user:password@localhost:5432/learning_system
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# JWT 认证
JWT_SECRET_KEY=your_jwt_secret_key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# 对象存储 (MinIO/S3)
STORAGE_ENDPOINT=http://localhost:9000
STORAGE_ACCESS_KEY=your_access_key
STORAGE_SECRET_KEY=your_secret_key
STORAGE_BUCKET_NAME=learning-resources

# DeepSeek API
DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_API_BASE_URL=https://api.deepseek.com/v1

# 应用配置
APP_NAME=智能学习计划系统
APP_VERSION=1.0.0
API_V1_PREFIX=/api/v1
BACKEND_CORS_ORIGINS=["http://localhost:3000", "http://localhost:5173"]

# Redis (可选 - 用于缓存和会话)
REDIS_URL=redis://localhost:6379/0

# 日志配置
LOG_LEVEL=INFO
LOG_FORMAT=json
```

---

## 11. 核心功能特性

### 10.1 智能需求分析
- 基于用户输入的学习目标和背景信息
- LLM深度分析用户的学习需求
- 识别知识盲点和学习路径
- 评估学习难度和所需时间

### 10.2 个性化学习计划
- 根据用户可用时间自动规划
- 分阶段、分里程碑的学习路线
- 灵活调整计划参数
- 支持多种学习节奏（快速/标准/慢速）

### 10.3 智能内容推荐
- 基于学习阶段推荐合适资源
- 多种资源类型（课程/书籍/视频/文章）
- 考虑资源质量、难度、时长
- 支持用户自定义替换资源

### 10.4 学习方式指导
- 提供科学的学习方法建议
- 时间管理和学习技巧
- 复习策略和记忆方法
- 个性化的学习节奏建议

### 10.5 进度跟踪与统计
- 每日打卡系统
- 学习时长统计
- 完成度可视化
- 学习曲线分析
- 学习笔记记录

### 10.6 动态调整机制
- 根据学习进度调整计划
- 识别学习瓶颈
- 提供改进建议
- 支持暂停和恢复

---

## 12. 数据统计指标

### 用户维度
- 总学习时长
- 计划完成率
- 连续打卡天数
- 学习效率趋势

### 计划维度
- 阶段完成进度
- 资源学习进度
- 里程碑达成情况
- 预计完成时间

### 资源维度
- 资源使用率
- 资源完成度
- 资源评价反馈

---

## 13. 未来扩展方向

1. **社区功能**
   - 学习小组
   - 经验分享
   - 互助答疑

2. **AI助教**
   - 智能答疑
   - 知识点测试
   - 学习建议

3. **成就系统**
   - 学习徽章
   - 等级系统
   - 排行榜

4. **多平台同步**
   - 移动端APP
   - 浏览器插件
   - 桌面应用

5. **数据分析**
   - 学习行为分析
   - 效果评估
   - 个性化优化
