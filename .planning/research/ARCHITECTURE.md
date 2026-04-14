# Architecture Patterns

**Domain:** v1.2 飞书深度集成与登录体验升级
**Researched:** 2026-04-14

## Recommended Architecture

三个功能按依赖关系分为独立但互相关联的三层：

```
┌──────────────────────────────────────────────────────────────┐
│                      Login Page (Feature 3)                   │
│   ┌─────────────────────┐  ┌──────────────────────────────┐  │
│   │  Left: Three.js      │  │  Right: Auth Forms            │  │
│   │  Particle Wave       │  │  (existing tabs + Feishu btn) │  │
│   │  (new component)     │  │  (modified Login.tsx)         │  │
│   └─────────────────────┘  └──────────────────────────────┘  │
├──────────────────────────────────────────────────────────────┤
│                  Feishu OAuth Enhancement (Feature 2)         │
│   ┌───────────────┐  ┌─────────────────┐  ┌──────────────┐  │
│   │ feishu_auth.py │  │ feishu_oauth_    │  │ User model   │  │
│   │ (modify v1→v2) │  │ service.py      │  │ (add fields) │  │
│   │               │  │ (add auto-bind)  │  │              │  │
│   └───────────────┘  └─────────────────┘  └──────────────┘  │
├──────────────────────────────────────────────────────────────┤
│              Feishu Field Mapping (Feature 1)                 │
│   ┌──────────────────┐  ┌────────────────────────────────┐   │
│   │ feishu_client.py  │  │ FeishuFieldMapping.tsx          │   │
│   │ (add list_tables) │  │ (add table selector, enhance)  │   │
│   └──────────────────┘  └────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

### Component Boundaries

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| `ParticleWaveBackground` (new) | Three.js 3D 粒子波浪渲染，纯视觉组件 | Login.tsx (包裹关系) |
| `LoginPage` (modified) | 左右分栏布局，右侧复用现有表单 | ParticleWaveBackground, AuthContext, feishu service |
| `feishu_oauth_service.py` (modified) | OAuth v2 token 交换 + 用户自动绑定 | User model, EmployeeMaster model, Feishu API |
| `feishu_auth.py` (modified) | OAuth 路由端点，增加 redirect_uri 运行时配置 | feishu_oauth_service, system_setting_service |
| `feishu_client.py` (modified) | 增加 list_tables 方法 | Feishu Bitable API |
| `FeishuFieldMappingPage` (modified) | 增加表格选择器、字段类型显示、匹配增强 | feishu service (frontend) |
| `FeishuSettings.tsx` (modified) | table_id 改为下拉选择、增加 redirect_uri 配置 | feishu service (frontend) |
| `feishu_settings.py` (modified) | 增加 list_tables 端点、redirect_uri 运行时配置 | feishu_client |

### Data Flow

**Feature 1 - 飞书字段映射完善:**

```
用户配置同步目标 → 输入 app_token
                 → [新] 调用 list_tables API 获取数据表列表
                 → 用户选择具体数据表 (table_id)
                 → 进入映射页 → 拉取该表字段列表 (list_fields API, 已有)
                 → [增强] 显示字段类型标签
                 → ReactFlow 拖拽映射 (已有)
                 → 保存 field_mapping 到 SyncConfig (已有)
```

**Feature 2 - 飞书 OAuth 自动登录:**

```
用户点击飞书登录 → GET /auth/feishu/authorize-url
                → 重定向到飞书授权页 (授权入口 URL 不变)
                → 飞书回调带 code → 前端 POST /auth/feishu/callback
                → [修改] 后端用 v2 API (/authen/v2/oauth/token) 换 user_access_token
                → 获取 open_id + name
                → [新] 按姓名匹配 EmployeeMaster (best-effort)
                → [新] 自动绑定 User.employee_master_id (匹配成功时)
                → 签发 JWT, 返回 role + token + bind_status
```

**Feature 3 - 登录页改版:**

```
/login 路由 → [修改] LoginPage 组件
            → 全屏左右分栏
            → 左侧: <ParticleWaveBackground /> (新组件, WebGL)
            → 右侧: 现有 Tabs (账号登录 / 员工查询) + 飞书登录按钮
            → 移动端: 左侧隐藏, 仅显示右侧表单
            → WebGL 不支持时: 静默降级为 CSS 渐变背景
```

## New Components (to create)

### Backend - New Files

无需创建新文件。所有后端改动在现有文件中完成。

### Frontend - New Files

| File | Purpose |
|------|---------|
| `src/components/ParticleWaveBackground.tsx` | Three.js 3D 粒子波浪动画组件 |

### Frontend - New Dependencies

| Package | Version | Purpose | Why |
|---------|---------|---------|-----|
| `three` | `^0.171.0` | Three.js 核心库 | 3D 渲染必需 |
| `@react-three/fiber` | `^8.x` | React 18 的 Three.js 渲染器 | 声明式 R3F，React 18 必须用 v8 (v9 需 React 19) |
| `@types/three` | `^0.171.0` | TypeScript 类型 | 开发时类型安全 |

**CRITICAL:** 当前项目使用 React 18.3.1。`@react-three/fiber@9` 需要 React 19，绝对不能安装 v9。必须锁定 `@react-three/fiber@^8`。

`@react-three/drei` 不需要安装 -- 粒子波浪只需要 `Canvas`, `useFrame` 和 custom shader，不需要 drei 的辅助组件。

## Existing Code Modifications - Detailed

### Backend Modifications

#### 1. `backend/app/services/feishu_client.py` -- 新增方法

**新增:** `list_tables(app_token: str) -> list[dict]`

```python
async def list_tables(self, app_token: str) -> list[dict]:
    """Fetch all tables from a Bitable app."""
    items: list[dict] = []
    page_token: Optional[str] = None
    while True:
        params: dict = {"page_size": 100}
        if page_token:
            params["page_token"] = page_token
        async with self._semaphore:
            resp = await self._http.get(
                f"/bitable/v1/apps/{app_token}/tables",
                headers=await self._headers(), params=params,
            )
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != 0:
            raise FeishuApiError(data.get("msg", "list_tables failed"), data.get("code"))
        items.extend(data["data"]["items"])
        if not data["data"].get("has_more"):
            break
        page_token = data["data"].get("page_token")
    return items
```

**风险:** 极低 -- 纯新增方法，与现有代码无交叉。

#### 2. `backend/app/services/feishu_oauth_service.py` -- 核心改动

**改动清单:**

1. **升级到 v2 API:** 将 `/authen/v1/access_token` 替换为 `/authen/v2/oauth/token`。请求体从 `{"grant_type": "authorization_code", "code": code}` + Bearer header 改为 `{"client_id": ..., "client_secret": ..., "grant_type": "authorization_code", "code": code}` (标准 OAuth 2.0，无需 app_access_token 中间步骤)。
2. **v2 响应差异处理:** v2 的 `expires_in` 是秒数 (如 `7200`)，v1 是时间戳。v2 在 token 响应中直接包含 `open_id`, `union_id`, `name` 等用户字段。
3. **自动绑定逻辑:** OAuth 获取用户信息后，按 `name` 在 `EmployeeMaster` 中匹配。仅唯一匹配时自动绑定。

```python
async def exchange_code_for_user(db: Session, code: str, settings: Settings) -> dict:
    async with httpx.AsyncClient() as http:
        # v2 API: 标准 OAuth token exchange (不再需要先获取 app_access_token)
        token_resp = await http.post(
            "https://open.feishu.cn/open-apis/authen/v2/oauth/token",
            json={
                "client_id": settings.feishu_app_id,
                "client_secret": settings.feishu_app_secret,
                "grant_type": "authorization_code",
                "code": code,
            },
        )
        token_resp.raise_for_status()
        token_data = token_resp.json()
        if "error" in token_data:
            raise FeishuOAuthError(f"Token exchange failed: {token_data.get('error_description', token_data['error'])}")

    open_id = token_data["open_id"]
    union_id = token_data.get("union_id", "")
    feishu_name = token_data.get("name", "Feishu User")

    # Find existing user by feishu_open_id
    user = db.query(User).filter(User.feishu_open_id == open_id).first()

    if not user:
        # Create new user
        username = f"feishu_{open_id[:16]}"
        user = User(
            username=username,
            hashed_password=hash_password(secrets.token_urlsafe(32)),
            role="employee",
            display_name=feishu_name,
            is_active=True,
            must_change_password=False,
            feishu_open_id=open_id,
            feishu_union_id=union_id,
            feishu_name=feishu_name,
        )
        db.add(user)

    # NEW: Auto-bind to EmployeeMaster by name
    bind_status = "unbound"
    if not user.employee_master_id:
        from backend.app.models.employee_master import EmployeeMaster
        matches = db.query(EmployeeMaster).filter(
            EmployeeMaster.person_name == feishu_name,
            EmployeeMaster.active.is_(True),
        ).all()
        if len(matches) == 1:
            user.employee_master_id = matches[0].id
            bind_status = "auto_bound"
        elif len(matches) > 1:
            bind_status = "ambiguous"  # 多人同名，需手动绑定
    else:
        bind_status = "already_bound"

    db.commit()
    db.refresh(user)

    token, exp = issue_access_token(...)
    return {
        "access_token": token,
        "expires_at": exp.isoformat(),
        "role": user.role,
        "username": user.username,
        "display_name": user.display_name,
        "bind_status": bind_status,
    }
```

**风险:** 中 -- v1 → v2 API 迁移需验证。v2 响应结构与 v1 不同 (v2 在 token 响应体直接包含用户信息，v1 需要单独调用用户信息 API)。

#### 3. `backend/app/models/user.py` -- 新增字段

```python
# 新增: 关联到 EmployeeMaster
employee_master_id: Mapped[Optional[str]] = mapped_column(
    String(100), ForeignKey("employee_master.id"), nullable=True, index=True
)
# 新增: 飞书显示名 (保留 OAuth 来源)
feishu_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
```

**风险:** 需要 DB schema 变更。当前项目使用 SQLAlchemy `create_all` 模式 (不使用 Alembic)。新增 nullable 列在 SQLite 中可以通过 `ALTER TABLE ADD COLUMN` 实现，无需重建表。需在 app startup 时添加 migration 逻辑。

#### 4. `backend/app/api/v1/feishu_auth.py` -- 小改

**改动:** `redirect_uri` 从 `getattr(settings, "feishu_oauth_redirect_uri", "")` 改为从 `system_settings` 读取 (与现有 app_id/app_secret 一致的 runtime settings 模式)。

```python
# Before:
redirect_uri = getattr(settings, "feishu_oauth_redirect_uri", "")

# After:
from backend.app.services.system_setting_service import get_setting, FEISHU_OAUTH_REDIRECT_URI_KEY
redirect_uri = get_setting(db, FEISHU_OAUTH_REDIRECT_URI_KEY) or getattr(settings, "feishu_oauth_redirect_uri", "")
```

**风险:** 极低。

#### 5. `backend/app/api/v1/feishu_settings.py` -- 新增端点 + 设置项

**新增端点:**

```python
@router.get("/tables", summary="获取飞书多维表格的数据表列表")
async def list_feishu_tables(
    app_token: str,  # query parameter
    client: Optional[FeishuClient] = Depends(_get_client_safe),
    ...
):
    tables = await client.list_tables(app_token)
    return success_response([
        {"table_id": t["table_id"], "name": t.get("name", ""), "revision": t.get("revision", 0)}
        for t in tables
    ])
```

**新增 runtime settings CRUD:** `feishu_oauth_redirect_uri` 加入 `/runtime` GET/PUT 端点。

**风险:** 低 -- 纯新增。

#### 6. `backend/app/core/config.py` -- 一行新增

```python
feishu_oauth_redirect_uri: str = ''
```

#### 7. `backend/app/services/system_setting_service.py` -- 一行新增

```python
FEISHU_OAUTH_REDIRECT_URI_KEY = "feishu_oauth_redirect_uri"
```

### Frontend Modifications

#### 1. `src/pages/Login.tsx` -- 布局重做 (高影响)

**当前结构:**
```
<div (flex center, 100vh)>
  <Card (w=400)>
    <Title>社保公积金管理系统</Title>
    <Tabs>账号登录 / 员工查询</Tabs>
    {feishu_oauth_enabled && <飞书登录按钮>}
  </Card>
</div>
```

**目标结构:**
```
<div (flex row, 100vh)>
  <div (flex: 1, left panel)>             -- 移动端隐藏
    <ParticleWaveBackground />             -- 绝对定位
    <div (overlay text, z-index: 1)>       -- 系统标题 + 品牌信息
      <Title>社保公积金管理系统</Title>
    </div>
  </div>
  <div (w=480, right panel, flex center)>  -- 移动端 100%
    <Card (w=100%)>
      <Tabs>账号登录 / 员工查询</Tabs>
      {feishu_oauth_enabled && <飞书登录按钮>}
    </Card>
  </div>
</div>
```

**风险:** 表单逻辑和 state 完全不变，仅改布局。但需要处理：
- 移动端响应式 (useResponsiveViewport 检测，窄屏隐藏左栏)
- 暗黑模式下右侧面板背景色适配 (useSemanticColors 已在用)
- Three.js Canvas 生命周期 (路由离开时自动销毁)

#### 2. `src/components/ParticleWaveBackground.tsx` -- 新建

**技术方案:** GPU vertex shader 粒子波浪，性能最优。

```tsx
import { Canvas, useFrame } from '@react-three/fiber';
import { useMemo, useRef, useState } from 'react';
import * as THREE from 'three';

function ParticleWave() {
  const count = 10000; // 100x100 grid
  const shaderRef = useRef<THREE.ShaderMaterial>(null);

  const positions = useMemo(() => {
    const pos = new Float32Array(count * 3);
    for (let i = 0; i < 100; i++) {
      for (let j = 0; j < 100; j++) {
        const idx = (i * 100 + j) * 3;
        pos[idx] = (i - 50) * 0.3;
        pos[idx + 1] = 0;
        pos[idx + 2] = (j - 50) * 0.3;
      }
    }
    return pos;
  }, []);

  useFrame(({ clock }) => {
    if (shaderRef.current) {
      shaderRef.current.uniforms.uTime.value = clock.elapsedTime;
    }
  });

  return (
    <points>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          array={positions}
          count={count}
          itemSize={3}
        />
      </bufferGeometry>
      <shaderMaterial
        ref={shaderRef}
        transparent
        uniforms={{ uTime: { value: 0 }, uColor: { value: new THREE.Color(0.3, 0.5, 1.0) } }}
        vertexShader={`
          uniform float uTime;
          void main() {
            vec3 pos = position;
            float wave = sin(pos.x * 0.5 + uTime) * cos(pos.z * 0.5 + uTime * 0.5);
            pos.y = wave * 1.5;
            gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
            gl_PointSize = 2.0;
          }
        `}
        fragmentShader={`
          uniform vec3 uColor;
          void main() {
            float dist = length(gl_PointCoord - vec2(0.5));
            if (dist > 0.5) discard;
            gl_FragColor = vec4(uColor, 0.8 * (1.0 - dist * 2.0));
          }
        `}
      />
    </points>
  );
}

export function ParticleWaveBackground() {
  const [supported] = useState(() => {
    try {
      const c = document.createElement('canvas');
      return !!(c.getContext('webgl2') || c.getContext('webgl'));
    } catch { return false; }
  });

  if (!supported) return null;

  return (
    <Canvas camera={{ position: [0, 15, 30], fov: 60 }} style={{ background: 'transparent' }}>
      <ParticleWave />
    </Canvas>
  );
}
```

**关键设计决策:**
- GPU vertex shader 而非 CPU `useFrame` 逐帧 -- 10K 粒子 GPU 无压力，CPU 会卡
- Fragment shader 使用圆形粒子 (discard > 0.5 radius) 而非方形默认点
- `uColor` uniform 方便暗黑模式切换粒子颜色
- WebGL 检测：不支持时返回 null，登录页 CSS 渐变背景接管

#### 3. `src/pages/FeishuFieldMapping.tsx` -- 功能增强

**改动:**
1. 飞书侧节点增加字段类型 Tag 显示 (文本/数字/日期等)
2. 自动匹配增强：增加同义词模糊匹配
3. 空状态优化：无字段时显示引导提示

**字段类型映射表** (用于在 UI 上显示可读标签):

```typescript
const FIELD_TYPE_LABELS: Record<number, string> = {
  1: '文本', 2: '数字', 3: '单选', 4: '多选',
  5: '日期', 7: '复选框', 11: '人员', 13: '电话',
  15: '链接', 17: '附件', 20: '公式',
  1001: '创建时间', 1002: '更新时间',
};
```

#### 4. `src/pages/FeishuSettings.tsx` -- UX 优化

**改动:**
1. Drawer 中 `table_id` 输入框改为「先输入 app_token → 拉取表列表 → 下拉选择 table_id」联动模式
2. 增加 `redirect_uri` 配置入口 (在运行时开关 Card 旁)

#### 5. `src/services/feishu.ts` -- 新增函数和类型

```typescript
export interface FeishuTableInfo {
  table_id: string;
  name: string;
  revision: number;
}

export async function fetchFeishuTables(appToken: string): Promise<FeishuTableInfo[]> {
  const resp = await api.get(`/feishu/settings/tables`, { params: { app_token: appToken } });
  return resp.data.data;
}
```

## Patterns to Follow

### Pattern 1: Runtime Settings Merge (已有模式)

**What:** 所有飞书配置项优先从 `system_settings` 表读取，fallback 到 `.env` 环境变量。
**When:** 新增 `feishu_oauth_redirect_uri` 配置项时。
**Example:** 参照 `get_effective_feishu_settings()` 中 `_resolve_text_setting(db, key, env_default)` 的实现模式。

### Pattern 2: Feature Flag Guard (已有模式)

**What:** 功能开关控制 API 端点和前端渲染。
**When:** OAuth 登录流程中所有端点必须检查 `feishu_oauth_enabled`。
**Example:** `feishu_auth.py` 每个端点首行 `if not effective_settings.feishu_oauth_enabled: return error_response(...)`.

### Pattern 3: Canvas Isolation for Three.js

**What:** Three.js Canvas 必须与 React DOM 树在视觉层隔离，避免事件冲突。
**When:** 登录页嵌入 3D 背景时。
**Example:**
```tsx
<div style={{ position: 'relative' }}>
  {/* Canvas 在底层 */}
  <div style={{ position: 'absolute', inset: 0, zIndex: 0 }}>
    <Canvas>...</Canvas>
  </div>
  {/* 文字叠加在上层 */}
  <div style={{ position: 'relative', zIndex: 1, pointerEvents: 'none' }}>
    <Title>...</Title>
  </div>
</div>
```

### Pattern 4: Graceful Degradation

**What:** 3D 效果在不支持 WebGL 的设备上静默降级。
**When:** ParticleWaveBackground 加载时。
**Example:** 组件内 `useState(() => checkWebGL())`, 不支持则 `return null`, 父组件用 CSS 渐变兜底。

### Pattern 5: Best-Effort Binding (新模式)

**What:** OAuth 用户自动绑定到 EmployeeMaster 是 best-effort，不强制。
**When:** `exchange_code_for_user` 中匹配员工时。
**Rules:**
- 唯一匹配 → 自动绑定, `bind_status = "auto_bound"`
- 多人同名 → 不绑定, `bind_status = "ambiguous"`
- 无匹配 → 不绑定, `bind_status = "unbound"`
- 已绑定 → 跳过, `bind_status = "already_bound"`

管理员和 HR 可能没有 EmployeeMaster 记录，绝不能因匹配失败拒绝登录。

## Anti-Patterns to Avoid

### Anti-Pattern 1: OAuth v1/v2 混用

**What:** 授权入口用 v1，token 交换也用 v1。
**Why bad:** v1 的 `expires_in` 返回时间戳而非秒数，且 v1 已标记为 legacy。v2 是标准 OAuth 2.0 流程，不需要先获取 `app_access_token` 中间步骤。
**Instead:** 授权入口 URL 保持 `/authen/v1/authorize` (唯一入口，未被替代)，token 交换统一用 v2 `/authen/v2/oauth/token` (直接用 client_id + client_secret)。

### Anti-Pattern 2: 在 Canvas 内使用 DOM 元素

**What:** 试图在 R3F Canvas 内放 HTML 表单。
**Why bad:** Canvas 是 WebGL 渲染上下文。虽然 `@react-three/drei` 的 `Html` 组件可以嵌入 DOM，但在登录页场景下完全没必要 -- 表单是纯 DOM 内容。
**Instead:** 左右分栏布局，Canvas 和表单各自独立渲染。

### Anti-Pattern 3: CPU 粒子动画

**What:** 用 `useFrame` + JavaScript 循环逐个更新粒子位置。
**Why bad:** 10000 个粒子意味着每帧循环 30000 个数组元素 (x, y, z)，加上 `bufferAttribute.needsUpdate = true` 触发 CPU→GPU 数据传输，在中低端设备上会掉帧。
**Instead:** 将 sine wave 计算放在 vertex shader 内，仅传递一个 `uTime` uniform (4 字节/帧)。GPU 并行计算 10000 个粒子毫无压力。

### Anti-Pattern 4: 强制绑定 OAuth 用户到员工

**What:** OAuth 登录时如果找不到匹配的 EmployeeMaster 就拒绝登录。
**Why bad:** 管理员和 HR 角色可能没有对应的员工主数据记录。
**Instead:** 匹配是 best-effort。找到唯一匹配就绑定，否则创建独立 User。仅在匹配成功时填充 `employee_master_id`。返回 `bind_status` 让前端可以提示用户绑定结果。

### Anti-Pattern 5: @react-three/fiber v9 with React 18

**What:** 安装 `@react-three/fiber@latest` (当前 v9+) 并搭配 React 18 使用。
**Why bad:** R3F v9 要求 React 19。编译可能通过，但运行时会出现 reconciler 不兼容错误。
**Instead:** 明确安装 `@react-three/fiber@^8.17.10` (v8 最新版本，支持 React 18)。

## Database Schema Changes

### User 表新增字段

```sql
ALTER TABLE users ADD COLUMN employee_master_id VARCHAR(100) REFERENCES employee_master(id);
ALTER TABLE users ADD COLUMN feishu_name VARCHAR(255);
-- feishu_open_id 和 feishu_union_id 已存在，无需新增
```

### SystemSettings 表新增 key

| Key | Value Example | Purpose |
|-----|---------------|---------|
| `feishu_oauth_redirect_uri` | `http://localhost:5173/login` | OAuth 回调地址 |

**Migration 策略:** 当前项目不使用 Alembic。在 app startup 时用 SQLite `PRAGMA table_info(users)` 检测列是否存在，不存在则 `ALTER TABLE ADD COLUMN`。这与项目现有的 `create_all` 模式一致。

## Scalability Considerations

| Concern | 当前 (单机 SQLite) | 备注 |
|---------|-------------------|------|
| Three.js 首次加载 | ~160KB gzipped (three.js) + ~30KB (R3F) | 仅登录页需要，可 lazy import |
| Three.js 运行时内存 | ~20-30MB GPU memory (10K particles) | 登录后路由切换自动释放 |
| 飞书 API 调用频率 | list_fields / list_tables 偶尔调用 | 已有信号量限流 (15 并发) |
| OAuth token 管理 | 无需持久化飞书 token | 系统签发自己的 JWT，飞书 token 仅用于单次交换 |
| 移动端 3D 性能 | 低端手机可能卡顿 | 通过 `navigator.hardwareConcurrency` 或直接隐藏解决 |
| 自动绑定冲突 | 同名员工产生歧义 | bind_status="ambiguous" 提示，后续可增加手动绑定页面 |

## Suggested Build Order

基于依赖关系和风险评估，推荐三阶段构建：

### Phase 1: 飞书字段映射完善 (Feature 1)

**理由:** 最低风险，不涉及 auth 变更或新依赖，纯功能增强。为 Phase 2 热身飞书 API 集成。

**步骤:**
1. `feishu_client.py` 新增 `list_tables` 方法
2. `feishu_settings.py` 新增 `/tables` 端点
3. `feishu.ts` 新增 `fetchFeishuTables` 函数 + `FeishuTableInfo` 类型
4. `FeishuSettings.tsx` Drawer 中 table_id 改为「输入 app_token → 拉取列表 → 下拉选择」联动
5. `FeishuFieldMapping.tsx` 增加字段类型 Tag 显示 + 自动匹配增强
6. 测试: 有/无飞书凭证时的降级行为

### Phase 2: 飞书 OAuth 自动登录 (Feature 2)

**理由:** 涉及 auth 流程改动和 DB schema 变更，需仔细测试。是 Feature 3 的前置条件 (登录页改版需要 OAuth 流程稳定)。

**步骤:**
1. `User` model 新增 `employee_master_id`, `feishu_name` 字段
2. App startup migration 逻辑 (ALTER TABLE)
3. `config.py` 新增 `feishu_oauth_redirect_uri` 环境变量
4. `system_setting_service.py` 新增 `FEISHU_OAUTH_REDIRECT_URI_KEY`
5. `feishu_oauth_service.py` 升级 v2 API + 自动绑定逻辑
6. `feishu_auth.py` redirect_uri 走 runtime settings
7. `FeishuSettings.tsx` 增加 redirect_uri 配置输入
8. 前端 OAuth callback 处理增加 `bind_status` 提示
9. 测试: 无凭证降级 / OAuth 完整流程 / 自动绑定各场景 (唯一匹配/同名/无匹配)

### Phase 3: 登录页面改版 (Feature 3)

**理由:** 纯前端视觉变更，需要 Feature 2 的 OAuth 流程已稳定。Three.js 是新依赖引入。

**步骤:**
1. `npm install three @react-three/fiber@^8 @types/three`
2. 新建 `ParticleWaveBackground.tsx` 组件
3. `Login.tsx` 改版为左右分栏布局
4. 移动端响应式适配 (窄屏隐藏左侧 3D)
5. WebGL 降级处理 (不支持时 CSS 渐变兜底)
6. 暗黑模式下粒子颜色适配 (读取 theme mode 切换 uColor)
7. Three.js 懒加载优化 (React.lazy + Suspense)
8. 测试: Chrome/Firefox/Safari + 移动端 + WebGL fallback + 暗黑模式

## Sources

- [React Three Fiber 官方文档](https://r3f.docs.pmnd.rs/getting-started/introduction)
- [R3F 粒子动画教程 (Maxime Heckel)](https://blog.maximeheckel.com/posts/the-magical-world-of-particles-with-react-three-fiber-and-shaders/)
- [React Three Fiber GitHub](https://github.com/pmndrs/react-three-fiber) -- v8 = React 18, v9 = React 19
- [飞书 OAuth v2 获取 user_access_token](https://open.feishu.cn/document/authentication-management/access-token/get-user-access-token)
- [飞书 OAuth v1 (legacy)](https://open.feishu.cn/document/server-docs/authentication-management/access-token/create-2)
- [飞书获取授权码](https://open.feishu.cn/document/authentication-management/access-token/obtain-oauth-code)
- [飞书 Bitable 数据结构概述](https://open.feishu.cn/document/server-docs/docs/bitable-v1/bitable-structure)
- [飞书字段编辑指南 (field_type 枚举)](https://open.feishu.cn/document/server-docs/docs/bitable-v1/app-table-field/guide)
- [飞书获取单个用户信息 (通讯录)](https://open.feishu.cn/document/server-docs/contact-v3/user/get)
- [飞书 Web SSO 概述](https://open.feishu.cn/document/common-capabilities/sso/web-application-sso/web-app-overview)
- [飞书如何获取 Open ID](https://open.feishu.cn/document/faq/trouble-shooting/how-to-obtain-openid)

---

*Architecture research for v1.2: 2026-04-14*
