# Feature Landscape

**Domain:** 飞书深度集成与登录体验升级（社保公积金管理系统 v1.2）
**Researched:** 2026-04-14
**Scope:** v1.2 三大新特性 — 飞书字段映射完善、飞书 OAuth 自动登录、登录页面改版

## Table Stakes

用户期望一定存在的功能。缺失 = 产品感觉不完整。

### 飞书字段映射完善

| Feature | Why Expected | Complexity | Dependencies | Notes |
|---------|--------------|------------|--------------|-------|
| 从飞书多维表格拉取真实字段列表 | 现有映射页右侧飞书字段依赖 `list_fields` API；用户需要看到真实飞书列名而非猜测 | Low | `FeishuClient.list_fields()` 已实现，前端 `fetchFeishuFields(configId)` 已调用 | 后端 API `GET /bitable/v1/apps/{app_token}/tables/{table_id}/fields` 已封装 |
| 字段类型展示（文本/数字/单选等） | 用户需知道飞书端字段类型以避免类型不匹配的推送错误（飞书 API 返回 `type` 数字枚举 + `ui_type` 显示名） | Low | list_fields 已返回 type/ui_type | 在 FeishuColumnNode 中加 type badge（如 "文本"、"数字"、"单选"） |
| 自动匹配优化（同义词库） | 现有自动匹配只做 label 包含检查，对 "养老保险(单位)" vs "pension_company" 之类中英文映射无效 | Med | 现有 `manual_field_aliases.py` 同义词规则 | 后端提供同义词匹配接口，或前端内嵌中文同义词表 |
| 未映射关键字段警告 | person_name、employee_id 等核心字段未映射时，保存前弹出警告 | Low | 纯前端校验 | 阻断式 Modal.confirm |
| 映射保存与加载 | 保存映射到后端、下次打开自动加载已有映射 | Done | `saveSyncConfigMapping` 已实现 | 现有功能已完整 |

### 飞书 OAuth 扫码登录 + 自动匹配绑定

| Feature | Why Expected | Complexity | Dependencies | Notes |
|---------|--------------|------------|--------------|-------|
| 扫码/重定向登录基础流程 | 已有后端 `/auth/feishu/authorize-url` + `/auth/feishu/callback`；前端 Login.tsx 已有飞书按钮和 callback 处理 | Done | OAuth 骨架已完成 | 用户点击 -> 跳转飞书授权页 -> code 回调 -> 换取 JWT |
| 按姓名自动匹配 EmployeeMaster | OAuth 回调拿到飞书 `name` 后，查 `EmployeeMaster` 表按 `person_name` 匹配，唯一匹配则自动绑定 | Med | EmployeeMaster 表已有 person_name 索引 | 当前 `exchange_code_for_user` 只创建新 User，不做 EmployeeMaster 匹配 |
| 多匹配/无匹配处理 | 飞书姓名匹配到 0 个或多个员工时，需引导用户手动确认（选择或输入工号） | Med | 前端需新增"匹配确认"步骤 | 0 匹配 -> 创建无绑定的 employee 用户；多匹配 -> 展示候选列表让用户选择 |
| 已绑定用户直接登录 | `User.feishu_open_id` 已存在时跳过匹配步骤直接签发 JWT | Done | User 表已有 feishu_open_id 字段和查询 | 当前行为已正确 |
| CSRF state 校验 | 防止攻击者将自己的飞书账号绑定到受害者系统账号 | Done | HMAC-signed cookie 已实现 | feishu_auth.py 中完整实现 |
| 登录后角色正确 | 飞书登录用户默认 employee 角色，管理员可在用户管理页提升 | Low | 当前已默认 employee 角色 | 行为已正确 |

### 登录页面改版

| Feature | Why Expected | Complexity | Dependencies | Notes |
|---------|--------------|------------|--------------|-------|
| 左右分栏布局 | 左侧视觉展示区 + 右侧登录表单；企业 SaaS 登录页标准模式 | Low | CSS Grid/Flexbox | 50/50 分栏，右侧迁移现有 Login.tsx 全部内容 |
| 右侧完整保留现有登录功能 | Tabs（账号登录/员工查询）+ 飞书登录按钮 + 员工查询入口链接 | Low | 现有 Login.tsx | 代码结构迁移，无功能改动 |
| 移动端适配 | 小屏幕（<768px）隐藏左侧展示区，只显示登录表单 | Low | useResponsiveViewport 已有 | 媒体查询 `display: none` |
| 暗黑模式兼容 | 登录页在暗黑模式下背景、表单卡片颜色正确 | Low | 暗黑模式已在 v1.1 完成 | token 引用即可 |

## Differentiators

不一定被期望，但能显著提升产品感知价值的功能。

| Feature | Value Proposition | Complexity | Dependencies | Notes |
|---------|-------------------|------------|--------------|-------|
| Three.js 3D 粒子波浪动态背景 | 视觉冲击力强，让内部工具看起来专业且现代；登录页是用户第一印象 | High | 需引入 `three` + `@react-three/fiber` + `@react-three/drei` | 打破 v1.1 "零新依赖"策略，但这是 v1.2 的明确需求 |
| 粒子颜色跟随品牌主题 | 粒子使用飞书蓝（#3370FF）/品牌色，与 Ant Design theme token 联动 | Med | Three.js Canvas 外需读取 CSS 变量或 token | 暗黑模式下颜色也需联动 |
| 鼠标交互效果（视差/跟随） | 鼠标移动时粒子产生微妙的波动跟随，增强沉浸感 | Med | `useFrame` + mouse position | 性能需谨慎，粒子数量控制在 5000-10000 |
| 飞书通讯录 employee_no 精确拉取 | OAuth 时不仅拿 name，还通过 `contact/v3/users/{user_id}` 拉取工号，实现精确匹配 | Med | 需 "查看成员工号" 权限（`contact:user.employee_id:readonly`） | 需飞书应用后台配置额外权限 |
| 已登录用户绑定飞书账号 | 用户设置页/个人信息页新增"绑定飞书"入口 | Med | 需新增绑定接口 + 前端 UI | 复用 OAuth 流程，绑定而非创建新用户 |
| 映射结果预览 | 保存映射前 Modal 汇总"系统字段 X -> 飞书列 Y" | Low | 纯前端 | 减少误操作 |
| 映射配置模板导入导出 | 将字段映射导出为 JSON，方便跨环境复用 | Low | 纯前端 | 锦上添花 |
| 左侧面板品牌信息 | 公司名称 + 产品名 + 核心功能亮点文案 | Low | 纯 UI 内容 | 覆盖在 3D 背景上 |
| WebGL 不可用时优雅降级 | 检测 WebGL 支持，不可用时显示 CSS 渐变动画背景 | Low | `try { canvas.getContext('webgl') }` | 兼顾极少数不支持 WebGL 的环境 |

## Anti-Features

明确不应构建的功能。

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| 飞书字段自动创建/删除 | 修改用户的飞书多维表格结构风险极高，可能破坏其他应用数据 | 只读取字段列表，映射操作在本系统内完成 |
| 飞书 OAuth 替代所有登录方式 | 管理员/HR 需要独立密码登录作为飞书不可用时的降级方案 | 飞书登录作为补充选项，不取代现有双模式登录 |
| 复杂 3D 场景（模型/物理引擎） | 登录页只需视觉氛围，大型 3D 资源会严重拖慢首屏 | 轻量粒子系统，纯 shader/geometry，无外部模型文件 |
| 自动同步飞书通讯录到员工主数据 | SQLite 不支持并发后台任务，且通讯录同步涉及隐私合规 | 仅在 OAuth 登录时按需拉取当前用户信息 |
| 飞书字段双向同步（修改飞书字段定义） | 破坏飞书端用户自定义字段配置 | 只支持"系统字段 -> 飞书列"的单向映射 |
| WebGL 复杂降级方案 | 在不支持 WebGL 的极少数浏览器上做复杂降级成本过高 | 检测 WebGL，不支持时隐藏左侧面板显示静态渐变 |
| 飞书登录用户自动提升角色 | 安全风险，角色提升应由管理员显式操作 | 飞书登录默认 employee 角色，管理员在用户管理页手动提升 |
| 粒子动画持续运行（用户登录后） | 浪费 GPU 资源，影响应用性能 | 登录成功后立即 unmount Canvas 组件 |

## Feature Dependencies

```
[飞书字段映射完善]
  飞书凭证配置(Done) -> list_fields API(Done) -> 字段类型展示(新)
  飞书凭证配置(Done) -> list_fields API(Done) -> 同义词自动匹配(新)
  同义词自动匹配 -> 映射结果预览(新)
  映射结果预览 -> 未映射关键字段警告(新)

[飞书 OAuth 自动登录]
  飞书凭证配置(Done) -> authorize-url(Done) -> exchange_code_for_user(Done)
  exchange_code_for_user -> 按姓名匹配 EmployeeMaster(新)
  按姓名匹配 -> 多匹配确认 UI(新)
  按姓名匹配 -> 无匹配处理(新)
  [可选] contact/v3 拉取 employee_no -> 精确工号匹配

[登录页面改版]
  左右分栏布局(新) -> 右侧表单迁移(新)
  Three.js 依赖安装(新) -> 粒子波浪组件(新) -> 左侧面板集成(新)
  暗黑模式(Done) -> Three.js 颜色主题适配(新)
  响应式(Done) -> 移动端适配(新)

[跨Feature依赖]
  飞书 OAuth 自动匹配 -> 登录页飞书按钮交互可能需要更新
  登录页改版 -> 飞书按钮位置/样式调整
```

## MVP Recommendation

**优先级排序（基于风险递增、依赖关系、用户价值）：**

1. **飞书字段映射完善** — 最低风险，基础设施全部就绪
   - 字段类型展示 + 同义词自动匹配 + 未映射警告 + 预览
   - 无新依赖，现有 ReactFlow 映射页增强
   - 预计 1-2 天

2. **飞书 OAuth 自动匹配绑定** — 中等风险，核心新逻辑在后端
   - 修改 `exchange_code_for_user` 增加 EmployeeMaster 匹配
   - 多匹配/无匹配前端确认流程
   - 预计 2-3 天

3. **登录页面改版** — 最高视觉冲击但也最高复杂度
   - 先做左右分栏布局（不含 Three.js），确保功能完整
   - 再加 Three.js 粒子背景（需 3 个新包：three、@react-three/fiber、@react-three/drei）
   - 预计 3-4 天

**Defer to later:**
- 飞书通讯录 employee_no 拉取：需额外企业应用权限审批，不阻塞核心流程
- 映射配置模板导入导出：锦上添花
- 已登录用户绑定飞书：需新增绑定 API，可在 v1.3

## Detailed Feature Specifications

### 1. 飞书字段映射 — 期望行为

**现有状态：** FeishuFieldMappingPage.tsx 已使用 ReactFlow 实现左右连线 UI：
- 左侧：23 个系统标准字段（SYSTEM_FIELDS 数组，key + 中文 label）
- 右侧：从 `fetchFeishuFields(configId)` 拉取的飞书字段
- 拖拽连线创建映射，保存到 `saveSyncConfigMapping(configId, mapping)`
- 自动匹配：精确 label 匹配 + 包含检查

**需要完善：**

1. **字段类型 badge**
   - 飞书 API 返回 `type`（1=文本, 2=数字, 3=单选, ...）和 `ui_type`（"Text", "Number", "SingleSelect"）
   - 在 FeishuColumnNode 右侧加 Tag 显示类型
   - 类型不匹配时（如系统数字字段连到飞书文本字段）连线标红警告

2. **同义词自动匹配增强**
   - 现有匹配只看 `field_name.includes(sysField.label)` 或反向
   - 增加：中文同义词表（如 "养老保险(单位)" 应匹配 field_name 含 "养老" 且含 "单位"）
   - 增加：系统 key 到常见中文名的映射（pension_company -> ["养老", "基本养老", "养老保险"] + ["单位", "企业"]）
   - 匹配逻辑：模糊包含多个关键词都命中则视为匹配

3. **未映射警告**
   - 核心字段列表：`person_name`, `employee_id`, `billing_period`
   - 保存时检查这些字段是否有映射连线
   - 未映射 -> Modal.confirm 警告（可忽略继续保存）

4. **映射预览 Modal**
   - 保存按钮点击后先弹出预览 Modal
   - 表格展示：系统字段名 | 飞书列名 | 飞书列类型
   - 底部展示未映射的系统字段列表
   - 确认后再调用 saveSyncConfigMapping

### 2. 飞书 OAuth 自动匹配 — 期望行为

**匹配策略（分层，后端实现）：**

```
Step 1: 查 User.feishu_open_id == open_id
  -> 找到 -> 直接签发 JWT（已实现）

Step 2: 用飞书返回的 name 查 EmployeeMaster.person_name
  -> 唯一匹配 -> 自动绑定 open_id 到对应 User（或创建 User 并关联）
  -> 多匹配 -> 返回候选列表给前端，用户选择后绑定
  -> 无匹配 -> 创建新 employee 用户（当前行为），标记为"未绑定员工"

Step 3 (可选): 如果有 contact/v3 权限，用 user_id 拉取 employee_no
  -> 精确匹配 EmployeeMaster.employee_id
  -> 比姓名匹配更可靠
```

**前端交互流程：**

```
用户点击"飞书登录" -> 跳转飞书授权页 -> 回调 code+state
  -> 后端返回以下之一:
     a) { status: "logged_in", access_token, ... }  -> 直接进入系统
     b) { status: "need_confirm", candidates: [...] }  -> 展示匹配确认 Modal
     c) { status: "new_user", access_token, ... }  -> 进入系统，提示"未绑定员工主数据"
```

**匹配确认 Modal（多匹配情况）：**
- 标题："检测到多个同名员工，请选择您的账号"
- 列表展示：姓名 + 工号 + 公司 + 部门
- 用户点击选择 -> 调用绑定 API -> 签发 JWT -> 进入系统

**后端 API 变更：**
- 修改 `exchange_code_for_user` 增加 EmployeeMaster 查询逻辑
- 新增返回 schema：包含 `status` 字段区分直接登录/需确认/新用户
- 新增 `POST /auth/feishu/confirm-bind`：多匹配时用户选择后确认绑定

### 3. 登录页面改版 — 期望行为

**布局结构：**

```
+------------------------------------------+
|   Left Panel (50%)   |  Right Panel (50%)  |
|                      |                     |
|   Three.js Canvas    |  品牌标题            |
|   (粒子波浪背景)      |  Tabs 登录表单       |
|                      |  飞书登录按钮         |
|   品牌文案叠加        |  员工查询链接         |
|   (半透明白字)        |                     |
|                      |                     |
+------------------------------------------+

移动端 (<768px):
+---------------------+
|  品牌标题            |
|  Tabs 登录表单       |
|  飞书登录按钮         |
|  员工查询链接         |
+---------------------+
```

**Three.js 粒子波浪实现要点：**

- 使用 `@react-three/fiber` 的 `Canvas` 组件
- 粒子数量：5000-8000 个（平衡视觉效果与性能）
- 波浪动画：`useFrame` 中通过 sin/cos 函数更新粒子 Y 坐标
- 颜色：品牌蓝 #3370FF 渐变到 #667EEA，暗黑模式下降低亮度
- 鼠标交互（可选）：鼠标位置影响波浪振幅
- Canvas 设置 `position: absolute; z-index: 0`，品牌文案 `z-index: 1`

**Three.js 技术方案：**

```typescript
// 推荐: @react-three/fiber（R3F）声明式 API
import { Canvas, useFrame } from '@react-three/fiber';
import { Points, PointMaterial } from '@react-three/drei';

function ParticleWave() {
  const ref = useRef<THREE.Points>(null);
  useFrame(({ clock }) => {
    // 更新每个粒子的 Y 坐标形成波浪
    const positions = ref.current!.geometry.attributes.position.array;
    for (let i = 0; i < positions.length; i += 3) {
      positions[i + 1] = Math.sin(positions[i] * 0.5 + clock.elapsedTime) * 0.5;
    }
    ref.current!.geometry.attributes.position.needsUpdate = true;
  });
  return (
    <Points ref={ref}>
      <bufferGeometry>
        <bufferAttribute ... />
      </bufferGeometry>
      <PointMaterial size={0.02} color="#3370FF" />
    </Points>
  );
}
```

**新增依赖评估：**

| Package | Size (gzip) | Purpose | Risk |
|---------|-------------|---------|------|
| three | ~150KB | 3D 渲染核心 | 必须，R3F peer dep |
| @react-three/fiber | ~40KB | React 声明式 Three.js | 推荐方案 |
| @react-three/drei | ~80KB | 工具组件（Points, PointMaterial 等） | 可选但大幅降低开发量 |
| **Total** | **~270KB gzip** | | 首屏影响可通过 lazy import 缓解 |

**性能优化：**
- `React.lazy(() => import('./ParticleWave'))` 懒加载 Canvas 组件
- 登录表单先渲染，3D 背景异步加载不阻塞交互
- 登录成功后 unmount Canvas 释放 GPU 资源

## Complexity Summary

| Feature Area | Estimated Effort | Risk | Key Challenge |
|-------------|-----------------|------|---------------|
| 字段映射 UI 完善 | 1-2 天 | Low | 纯前端改进，后端已就绪 |
| 字段同义词匹配 | 0.5-1 天 | Low | 词表维护 |
| OAuth 后端匹配逻辑 | 1-2 天 | Med | 多匹配/无匹配边界 |
| OAuth 前端确认 UI | 1 天 | Med | 新增 Modal/步骤 |
| 登录页左右分栏 | 0.5-1 天 | Low | 纯 CSS 布局 |
| Three.js 粒子波浪 | 2-3 天 | High | 新依赖 + 性能 + 暗黑适配 |
| 移动端适配 | 0.5 天 | Low | 隐藏左侧面板 |
| **Total** | **7-10 天** | | |

## Sources

- [飞书 Bitable API 概述](https://open.feishu.cn/document/server-docs/docs/bitable-v1/bitable-overview) - HIGH confidence
- [飞书 Bitable 字段列表 API](https://open.feishu.cn/document/server-docs/docs/bitable-v1/app-table-field/list) - HIGH confidence，已验证返回 field_id/field_name/type/ui_type
- [飞书 Bitable 数据结构](https://open.feishu.cn/document/server-docs/docs/bitable-v1/bitable-structure) - HIGH confidence
- [飞书 OAuth 授权登录实践](https://iamazing.cn/page/feishu-oauth-login) - MEDIUM confidence
- [飞书通讯录用户信息 API](https://open.feishu.cn/document/server-docs/contact-v3/user/get) - HIGH confidence，确认 employee_no 需 "查看成员工号" 权限
- [飞书 user_access_token 获取](https://open.feishu.cn/document/authentication-management/access-token/get-user-access-token) - HIGH confidence
- [React Three Fiber 官方文档](https://r3f.docs.pmnd.rs/tutorials/basic-animations) - HIGH confidence
- [Codrops: Shader Background with R3F](https://tympanus.net/codrops/2024/10/31/how-to-code-a-subtle-shader-background-effect-with-react-three-fiber/) - MEDIUM confidence
- [Three.js Particle Wave CodePen](https://codepen.io/hellobrophy/pen/rKqYRo) - MEDIUM confidence，参考实现
- [Split Panel Login 设计参考 (Dribbble)](https://dribbble.com/search/split-screen-login) - MEDIUM confidence
- [50+ SaaS Login Page Examples](https://www.eleken.co/blog-posts/login-page-examples) - MEDIUM confidence
- [Motion for React Three Fiber](https://motion.dev/docs/react-three-fiber) - MEDIUM confidence
