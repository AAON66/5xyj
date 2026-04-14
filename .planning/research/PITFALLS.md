# Pitfalls Research

**Domain:** 飞书深度集成与登录体验升级 (v1.2 — Feishu Deep Integration + Login UX Upgrade)
**Researched:** 2026-04-14
**Confidence:** HIGH (基于现有代码深度分析 + 飞书官方文档 + Three.js/OAuth 社区报告)

---

## Critical Pitfalls

### Pitfall 1: 飞书字段类型序列化不对称 — 读写数据格式不一致

**What goes wrong:**
飞书多维表格 API 的字段值在读取和写入时使用不同的 JSON 结构。Text 字段 (type=1) 写入时是 plain string，读取时是 `[{"type": "text", "text": "..."}]` 的富文本数组。Number 字段 (type=2) 读取时可能返回 string 而非 number。Date 字段 (type=5) 使用毫秒级 Unix 时间戳，显示时区默认 UTC+8。现有 `feishu_client.py` 的 `batch_create_records` 直接发送原始 dict（第 88 行 `{"records": [{"fields": r} for r in records]}`），没有做类型感知的序列化。飞书字段类型编码完整列表：type 1=文本, 2=数字, 3=单选, 4=多选, 5=日期, 7=复选框, 11=人员, 13=电话, 15=超链接, 17=附件, 18/21=关联, 20=公式, 1001-1005=系统字段。

**Why it happens:**
这是飞书 API 的设计决策——读/写 contract 不对称。开发者通常假设"读出来的格式就是写进去的格式"，但实际上数据结构完全不同。现有 `SyncConfig.field_mapping` 只存 field_name 对应关系（JSON dict），不存 field_type，无法在写入时做类型转换。

**How to avoid:**
- 建立 `FeishuFieldSerializer` 类，根据 field_type 做双向转换（system -> feishu 和 feishu -> system）
- `SyncConfig.field_mapping` 结构扩展为 `{canonical_field: {field_id, field_name, field_type}}`（从当前简单 dict 升级）
- Date 字段统一 UTC 存储，写入飞书时转毫秒时间戳
- Number 字段读取后强制 `float()` 转换
- 为每种 field_type 编写序列化/反序列化单元测试

**Warning signs:**
- 同步到飞书后数字字段变成文本，飞书端公式和求和失效
- 拉取数据时 `TypeError: expected string, got list`
- 日期偏差 8 小时

**Phase to address:**
飞书字段映射完善（第一阶段）— 这是所有后续飞书功能的基础

---

### Pitfall 2: OAuth 登录与现有用户的身份割裂

**What goes wrong:**
飞书 OAuth 登录创建的用户（`feishu_{open_id[:16]}`）与现有管理员/HR 用户使用同一个 JWT 体系，但 OAuth 新建用户默认 role=employee。当一个已有管理员通过飞书 OAuth 登录时，`feishu_oauth_service.py:58` 只按 `feishu_open_id` 查找 User，未找到则在 `:64-72` 创建新 employee 用户（username=`feishu_{open_id[:16]}`，role=`employee`）。同一个人在系统中产生两个账号——一个 admin 一个 employee，JWT token 和审计日志完全割裂。

**Why it happens:**
现有代码没有"飞书身份 -> 系统已有用户"的智能匹配层。OAuth 流程按 open_id 查找失败后直接创建新用户，没有尝试按姓名、工号等信息关联已有账号。User 模型（`user.py`）有 `feishu_open_id` 和 `feishu_union_id` 字段，但初始值为 None，需要手动或自动绑定。

**How to avoid:**
- OAuth 回调时匹配顺序：(1) `feishu_open_id` 精确查找 -> (2) 飞书返回的 `name` + `employee_no`(需通讯录权限) 双因子匹配已有 User -> (3) 单独 `name` 匹配标记为"待确认" -> (4) 全部未命中才创建新用户
- 匹配成功后绑定 `feishu_open_id`/`feishu_union_id` 到已有用户，保留原有 role
- 管理后台提供"飞书账号绑定管理"页面，列出所有待确认和已绑定的映射
- Employee master 已有 `employee_id`（工号）和 `person_name`（姓名），可作为匹配依据

**Warning signs:**
- 管理员飞书登录后只看到员工自助查询功能
- `users` 表中出现大量 `feishu_` 前缀的 username
- 审计日志中同一个人出现两个 username

**Phase to address:**
飞书 OAuth 自动登录（第二阶段）— 这是核心用户体验问题

---

### Pitfall 3: Three.js Canvas 在 React SPA 路由切换时内存泄漏

**What goes wrong:**
用户登录后路由离开登录页，Three.js 的 WebGLRenderer、BufferGeometry、Material 等 GPU 资源未释放。多次进出登录页后，浏览器内存持续增长，动画帧率下降。Chrome 限制约 16 个 WebGL context，泄漏会导致后续 Canvas 创建失败（黑屏）。react-three-fiber (R3F) 的 `<Canvas>` 组件卸载时也存在已知的 WebGLRenderer 泄漏问题（GitHub Issue #514）。

**Why it happens:**
React 组件卸载时 `useEffect` cleanup 只清理 JS 对象引用，但 Three.js 的 GPU 资源需要显式调用 `dispose()` 方法。WebGL context 是浏览器全局有限资源，不会被 JavaScript GC 回收。这是 React 声明式范式与 Three.js 命令式资源管理之间的根本冲突。

**How to avoid:**
- 使用 raw Three.js 而非 react-three-fiber（登录页是单一粒子波浪场景，不需要 R3F 声明式组件系统；省去 R3F + drei 约 50KB+ gzipped 依赖）
- `useEffect` cleanup 必须严格执行以下序列：
  1. `cancelAnimationFrame(animationId)`
  2. `scene.traverse(obj => { obj.geometry?.dispose(); obj.material?.dispose(); })`
  3. `renderer.dispose()`
  4. `renderer.forceContextLoss()`（释放 WebGL context）
  5. 移除 resize event listener
  6. 从 DOM 移除 canvas 元素
- Canvas 初始化使用低功耗配置：`{ alpha: true, antialias: false, powerPreference: 'low-power' }`

**Warning signs:**
- Chrome DevTools Performance > Memory 中 `WebGLRenderingContext` 实例数随路由切换递增
- 控制台出现 `WARNING: Too many active WebGL contexts. Oldest context will be lost`
- 动画帧率随使用时间下降

**Phase to address:**
登录页面改版（第三阶段）

---

### Pitfall 4: CSRF State Cookie 在生产环境跨域场景下丢失

**What goes wrong:**
现有 `feishu_auth.py:76-80` 设置 state cookie 参数为 `samesite="lax"` + `secure=False`。飞书授权页 (`accounts.feishu.cn`) 重定向回来时，如果前后端部署在不同域名/端口（生产环境 nginx 反代），浏览器因 SameSite 策略拒绝在 cross-site POST 中发送 cookie，导致 state 验证永远失败。开发环境 `localhost` 同源，此问题不会出现。

**Why it happens:**
OAuth 重定向是 cross-site navigation。SameSite=Lax 只允许 top-level GET 导航携带 cookie，不允许 cross-site POST。飞书 OAuth callback 是 GET 重定向，但如果前端将 code/state 通过 POST 发送给后端 `/auth/feishu/callback`（当前实现方式），cookie 不会被浏览器附带。

**How to avoid:**
- 生产环境设置 `secure=True` + `samesite="none"`（需 HTTPS）
- 或者改用 server-side session 存储 state（将 state 存 DB 或内存，不依赖 cookie 传输）
- `feishu_auth.py` 中根据 `settings.debug` 或环境变量动态设置 cookie 参数
- 部署检查清单中加入"飞书 OAuth callback 端到端测试"

**Warning signs:**
- 生产环境飞书登录 100% 失败："OAuth state 验证失败，请重新登录"
- 开发环境测试全部通过

**Phase to address:**
飞书 OAuth 自动登录（第二阶段）

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| field_mapping 只存 field_name 不存 field_id/field_type | 实现简单，少一层查找 | 飞书端重命名字段后映射失效；类型序列化缺失导致数据错误 | Never — field_id 是稳定标识，field_type 决定序列化方式 |
| Three.js 打进主 bundle 不做 code splitting | 省去 dynamic import 配置 | 所有页面初始加载多 155KB+ gzipped | Never — 只有登录页需要 Three.js |
| OAuth 用户直接创建 employee 不尝试匹配已有用户 | 避免匹配逻辑复杂度 | 同一个人两个账号，权限割裂，审计混乱 | 仅首个迭代可临时接受，但必须在下个 sprint 修复 |
| 粒子数量/分辨率桌面/移动端统一 | 少写设备检测逻辑 | 移动端登录体验极差（5-10fps） | Never — 移动端用户会直接放弃登录 |
| state cookie 写死 `secure=False, samesite=lax` | 开发环境即刻可用 | 生产环境 OAuth 100% 失败 | 仅开发阶段，上线前必须改为环境感知 |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| 飞书 Bitable list_fields | 每次打开映射 UI 都调 API，触发频率限制 | 本地缓存 TTL 5 分钟（已有 `_semaphore` 限流但不够） |
| 飞书 Bitable batch_create | 用 field_id 作为 record fields 的 key | 必须用 field_name 作为 key；field_id 只用于映射查找，写入时转回最新 field_name |
| 飞书 OAuth redirect_uri | 只在后端 Settings 配置 | 三处必须精确一致：飞书开放平台安全设置、后端 `feishu_oauth_redirect_uri`、前端回调 URL |
| 飞书 token 类型混用 | tenant_access_token 和 user_access_token 互相替代 | OAuth 用 app_access_token 换 user info；Bitable 操作用 tenant_access_token（现有架构正确，不要改） |
| 飞书 OAuth authorize URL | 硬编码 `accounts.feishu.cn`（`feishu_auth.py:69`） | 国际版用 `accounts.larksuite.com`；按部署环境配置化 |
| Three.js dispose | 只清理顶层 scene.children | 必须 `scene.traverse()` 递归遍历，每个 mesh 的 geometry + material + texture 都要 dispose |
| Three.js + React useEffect | 在 useEffect 中创建 renderer 但 cleanup 不完整 | cleanup 必须执行全部 6 步（见 Pitfall 3） |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Three.js 粒子数量未适配设备 | 移动端 5-10fps，登录表单输入卡顿 | 移动端完全禁用 Three.js 动画或降到 1/4 粒子数；用 `useResponsiveViewport` 已有 hook 判断 | devicePixelRatio > 2 或 CPU 较弱的移动设备 |
| Canvas pixelRatio 未限制 | 高 DPI 屏渲染像素是逻辑像素的 4-9 倍 | `renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))` | Retina/高 DPI 屏幕（iPhone 3x, MacBook 2x） |
| 飞书字段列表未缓存 | 每次打开映射 UI 等待 1-2s + API 频率消耗 | 内存缓存 + TTL 5 分钟 | 多个 SyncConfig 同时操作时 |
| Three.js 未做 dynamic import | 主 bundle 膨胀 155KB+ gzipped | `React.lazy(() => import('./ThreeWaveBackground'))` + Vite manualChunks | 首屏加载感知 |
| 登录页 Three.js 动画持续 rAF | 即使窗口最小化仍在渲染 | `document.visibilitychange` 事件暂停/恢复动画 | 笔记本电脑电池消耗 |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| OAuth state cookie SameSite/Secure 配置不当 | CSRF 攻击 / 生产环境 OAuth 100% 失败 | 生产环境 `secure=True, samesite=none`(HTTPS) |
| 飞书 app_secret 存明文 system_settings 表 | 数据库泄露 = 飞书应用完全暴露 | 考虑 AES 加密存储或 keyring |
| OAuth 自动绑定无二次确认 | 同名用户绑定错误 -> 权限越级 | 姓名+工号双因子匹配；同名标记为"待确认" |
| redirect_uri 未做严格校验 | Open redirect 攻击 | 严格匹配预注册的 redirect_uri，不允许通配符 |
| 飞书 OAuth code 未校验 audience | JWT 混淆攻击（不同应用的 code 互用） | 验证 code 对应的 app_id 与当前配置一致 |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| 登录页三个入口（账号/员工/飞书）无主次区分 | 用户不知道该用哪个入口 | 飞书登录（如启用）视觉最突出；账号密码和员工查询为次级备选 |
| 飞书登录后默认 employee 权限 | 管理员困惑"功能变少了" | 自动匹配已有用户并保留原角色 |
| 粒子动画遮挡表单输入区域 | 登录信息看不清楚 | 左右分栏严格隔离：动画在左、表单在右，互不干扰 |
| 移动端粒子动画卡顿 | 输入文字时手指跟不上光标 | 移动端禁用 Three.js 动画，用轻量 CSS 渐变替代 |
| 飞书登录失败无明确原因 | 用户只看到"登录失败" | 区分具体原因：飞书服务不可用 / 未绑定系统用户 / 飞书应用权限不足 / state 过期 |
| 字段映射 UI 无预览效果 | HR 不知道映射是否正确 | 映射保存后提供"预览同步"——展示 5 条示例数据的映射结果 |

## "Looks Done But Isn't" Checklist

- [ ] **飞书字段映射:** 看起来映射成功，但没有验证 Number/Date 类型值的序列化 — 用数字和日期字段创建记录后在飞书端检查值是否正确、公式是否可用
- [ ] **OAuth 登录:** 看起来能登录，但没测试已有管理员用飞书登录的场景 — 用已有 admin 的飞书账号测试，验证返回 role=admin 而非 employee
- [ ] **OAuth 登录:** 看起来安全，但没在生产环境测试 CSRF state — staging 环境（前后端分离部署 + HTTPS）跑完整 OAuth 流程
- [ ] **Three.js 动画:** 看起来很炫，但没检查路由切换后的内存 — 来回切换登录页 5 次，Chrome Memory 快照对比 WebGLRenderingContext 实例数
- [ ] **Three.js 动画:** 看起来桌面端流畅，但没在真实手机上测试 — iPhone SE + Android 低端机测试
- [ ] **redirect_uri:** 后端配置了，但飞书开放平台安全设置没加 — 三处检查清单
- [ ] **Python 3.9:** 本地 3.11 跑通所有测试，但新代码可能用了 3.10+ 语法 — CI 中用 Python 3.9 跑测试
- [ ] **field_mapping 迁移:** 从简单 dict 升级到含 field_id/field_type 的结构，但旧数据没迁移 — 写 migration 脚本处理已有 SyncConfig 记录
- [ ] **打包体积:** Three.js 加入了项目，但没确认 code splitting 是否生效 — `npx vite-bundle-visualizer` 检查 three.js chunk 独立性

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| #1 字段类型序列化错误 | MEDIUM | 建 FeishuFieldSerializer，修改 field_mapping 结构，重新同步受影响的记录 |
| #2 用户身份割裂 | HIGH | 手动合并重复账号（数据迁移脚本迁移审计日志等关联数据），通知受影响用户 |
| #3 WebGL 内存泄漏 | LOW | 补全 dispose cleanup 代码，无需改架构 |
| #4 CSRF cookie 跨域 | LOW | 修改 cookie 参数为环境感知，或改用 server-side state 存储 |
| #5 field_name 映射失效 | MEDIUM | 迁移 field_mapping 结构加入 field_id，写迁移脚本重新拉取 field_id |
| Three.js 打包未分离 | LOW | 加 dynamic import + Vite manualChunks 配置 |
| 移动端性能灾难 | LOW | 加设备检测条件渲染，禁用动画 |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| #1 字段类型序列化不对称 | 飞书字段映射完善（Phase 1） | 创建含 Number + Date 字段的记录，飞书端验证值格式正确、公式可用 |
| #2 用户身份割裂 | 飞书 OAuth 自动登录（Phase 2） | 已有 admin 用户用飞书 OAuth 登录，验证 JWT role 保持 admin |
| #3 WebGL 内存泄漏 | 登录页面改版（Phase 3） | 路由切换 5 次后 Chrome Memory 中 WebGLRenderingContext 数 = 0 |
| #4 CSRF cookie 跨域 | 飞书 OAuth 自动登录（Phase 2） | Staging 环境（HTTPS + 前后端分离）跑完整 OAuth 流程成功 |
| field_name vs field_id | 飞书字段映射完善（Phase 1） | 飞书端重命名已映射字段后，系统自动检测并提示更新 |
| 移动端性能 | 登录页面改版（Phase 3） | iPhone SE 真机上登录页保持 30fps+ 且表单输入流畅 |
| redirect_uri 三处一致 | 飞书 OAuth 自动登录（Phase 2） | 部署检查脚本自动验证三处 URI 一致性 |
| 同名自动绑定 | 飞书 OAuth 自动登录（Phase 2） | 两个同名用户用飞书登录，系统标记为"待确认"而非自动绑定 |
| 打包体积膨胀 | 登录页面改版（Phase 3） | `vite-bundle-visualizer` 确认 three.js 在独立 chunk 且不影响其他页面首屏 |
| Python 3.9 兼容 | 所有阶段 | CI 在 Python 3.9 环境跑通全部测试（含新增代码） |

---

## Cross-Feature Integration Pitfalls

### 飞书字段映射 + 现有同步流程的向后兼容

**Risk:** 扩展 `SyncConfig.field_mapping` 结构（从 `{canonical: feishu_name}` 到 `{canonical: {field_id, field_name, field_type}}`）会破坏所有已有的 SyncConfig 记录和同步逻辑。`feishu_sync_service.py` 中现有的映射读取代码会报 KeyError 或 TypeError。

**Mitigation:** 写 field_mapping 迁移逻辑：读取时检测旧格式（value 是 string）自动转换为新格式（value 是 dict），或者在 SyncConfig 模型上加 `@property` 做兼容适配。

### OAuth 登录 + 现有 RBAC 三角色体系

**Risk:** 飞书 OAuth 创建的用户默认 role=employee。现有 RBAC 中 employee 角色的路由保护（`RoleRoute allowedRoles`）限制了可访问的页面。如果 OAuth 匹配绑定了已有 admin/HR 用户，JWT 中的 role 来自已有用户，一切正常。但如果创建了新 employee 用户，该用户无法通过前端看到管理功能——这可能是期望的行为，也可能不是（取决于飞书用户是否应该有更高权限）。

**Mitigation:** 明确定义：飞书 OAuth 未匹配已有用户时，新用户的默认角色。建议保持 employee（最小权限原则），管理员可在后台提升角色。

### Three.js 登录页 + 现有暗黑模式

**Risk:** 登录页 Three.js 粒子动画的颜色方案需要适配暗黑/明亮两种模式。如果粒子颜色在明亮模式下是深色、暗黑模式下仍是深色，视觉效果会在其中一种模式下很差。

**Mitigation:** 粒子颜色和背景色都从 theme token 读取（`useSemanticColors` 或 `useThemeMode`），确保两种模式下都有良好对比度。

---

## Sources

- [飞书 Bitable 记录数据结构](https://open.feishu.cn/document/docs/bitable-v1/app-table-record/bitable-record-data-structure-overview) — 字段类型及 JSON 格式 (HIGH confidence)
- [飞书 Bitable 字段编辑指南](https://open.feishu.cn/document/server-docs/docs/bitable-v1/app-table-field/guide) — 字段类型编码完整列表（1-1005+3001） (HIGH confidence)
- [飞书 List Fields API](https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/reference/bitable-v1/app-table-field/list) — 字段列表接口 (HIGH confidence)
- [Three.js Forum: R3F Memory Leak](https://discourse.threejs.org/t/r3f-threejs-memory-leak-when-canvas-is-scrolled-out-of-view/48440) — Canvas 内存泄漏社区讨论 (HIGH confidence)
- [R3F Issue #514: Leaking WebGLRenderer on unmount](https://github.com/pmndrs/react-three-fiber/issues/514) — 官方 issue 确认卸载泄漏 (HIGH confidence)
- [R3F Bundle Size Discussion #812](https://github.com/pmndrs/react-three-fiber/discussions/812) — Three.js ~155KB gzipped 基础开销 (MEDIUM confidence)
- [React Three Fiber vs Three.js 2026 比较](https://graffersid.com/react-three-fiber-vs-three-js/) — 性能和体积对比 (MEDIUM confidence)
- [JWT Security Best Practices](https://curity.io/resources/learn/jwt-best-practices/) — JWT 签名验证和 claims 校验 (HIGH confidence)
- [OAuth 2.0 Pitfalls](https://treblle.com/blog/oauth-2.0-for-apis) — redirect URI、PKCE、token 存储 (MEDIUM confidence)
- [SSO Protocol Security Vulnerabilities 2025](https://guptadeepak.com/security-vulnerabilities-in-saml-oauth-2-0-openid-connect-and-jwt/) — CSRF state、算法混淆攻击 (MEDIUM confidence)
- 项目源码一手分析：`feishu_client.py`、`feishu_auth.py`、`feishu_oauth_service.py`、`feishu_settings.py`、`Login.tsx`、`FeishuSync.tsx`、`user.py`、`sync_config.py`、`auth.py` (HIGH confidence)

---
*Pitfalls research for: v1.2 飞书深度集成与登录体验升级*
*Researched: 2026-04-14*
