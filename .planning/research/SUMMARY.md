# Project Research Summary

**Project:** v1.2 飞书深度集成与登录体验升级
**Domain:** 企业内部 SaaS 工具 -- 飞书生态集成 + 登录 UX 升级
**Researched:** 2026-04-14
**Confidence:** HIGH

## Executive Summary

v1.2 是在已验证的社保公积金管理系统（React 18 + FastAPI + SQLite）基础上的三项增量功能：飞书字段映射完善、飞书 OAuth 自动匹配登录、登录页 Three.js 3D 改版。三项功能的后端基础设施（FeishuClient、OAuth 流程、JWT 体系）在 v1.1 中已经构建完成，v1.2 的核心工作是增强 UI 和用户匹配逻辑，而非从零搭建。前端唯一的重大新增依赖是 Three.js 生态（three + @react-three/fiber v8，约 190KB gzipped），后端零新依赖。

推荐按"字段映射 -> OAuth 匹配 -> 登录页改版"的顺序分三阶段构建。字段映射风险最低（纯 UI 增强，后端 API 已有），OAuth 匹配涉及 DB schema 变更和身份绑定逻辑（中等风险），登录页改版引入新前端依赖且需要 WebGL 资源管理（最高复杂度但风险可控）。三阶段总估时 7-10 天。

最关键的风险有四个：飞书 API 字段类型读写不对称（type 1 文本字段读返回富文本数组、写接受 plain string）、OAuth 用户与已有系统用户身份割裂（同一个人产生两个账号）、Three.js Canvas 路由切换内存泄漏（WebGL context 有限）、CSRF state cookie 在生产环境跨域部署下丢失。四个风险均有明确的预防方案且分别对应到各自阶段。

## Key Findings

### Recommended Stack

v1.2 只需 3 个新 npm 包和 1 个 CDN 加载的飞书 SDK，后端零新依赖。Three.js 版本必须锁定在 R3F v8 兼容范围内（three ~0.172.0），因为项目使用 React 18，而 R3F v9 要求 React 19。飞书扫码用官方 QRLogin SDK（CDN 加载），无 npm 包可用。

**Core technologies:**
- `three@~0.172.0` + `@react-three/fiber@^8.17.10`: 登录页 3D 粒子波浪 -- R3F v8 是 React 18 对应版本，v9 绝对不能用
- `@types/three@~0.172.0`: TypeScript 类型定义 -- 版本需与 three 主包对齐
- 飞书 QRLogin SDK 1.0.3 (CDN): 内嵌扫码二维码 -- 官方唯一渠道，处理跨域和安全细节
- 后端无新增: httpx + 现有 FeishuClient 已覆盖所有 API 调用需求

**关于 @react-three/drei 的决策:** STACK.md 推荐安装 drei 用 `<Points>` + `<PointMaterial>`；ARCHITECTURE.md 建议不装 drei，用 raw vertex shader 实现。**建议采用 ARCHITECTURE 方案** -- 粒子波浪用 GPU vertex shader 性能最优（GPU 并行 vs CPU 逐帧循环），且省去约 50KB+ 依赖。drei 不安装。

### Expected Features

**Must have (table stakes):**
- 飞书多维表格字段拉取 + 类型展示（后端 API 已有，前端加 type badge）
- 同义词自动匹配增强（现有精确匹配对中英文映射无效）
- 未映射关键字段警告（person_name/employee_id 未映射时阻断提示）
- OAuth 按姓名自动匹配 EmployeeMaster + 多匹配/无匹配处理
- 登录页左右分栏布局 + 移动端适配 + 暗黑模式兼容

**Should have (differentiators):**
- Three.js 3D 粒子波浪动态背景（视觉冲击力，第一印象）
- 粒子颜色跟随品牌主题 + 暗黑模式联动
- WebGL 不可用时优雅降级为 CSS 渐变
- 映射结果预览 Modal（保存前汇总确认）
- 飞书扫码登录（内嵌二维码替代跳转式）

**Defer (v2+):**
- 飞书通讯录 employee_no 精确拉取（需额外企业应用权限审批）
- 已登录用户绑定飞书账号（需新增绑定 API）
- 映射配置模板导入导出（锦上添花）

### Architecture Approach

三个功能按依赖关系分层：底层是飞书字段映射（纯数据层增强），中层是 OAuth 匹配（身份层改动），顶层是登录页视觉（展示层）。所有后端改动在现有文件中完成，不创建新后端文件。前端仅新建一个 `ParticleWaveBackground.tsx` 组件。DB schema 需新增 User 表的 `employee_master_id` 和 `feishu_name` 两个 nullable 列。

**Major components:**
1. `ParticleWaveBackground.tsx` (new) -- GPU vertex shader 粒子波浪，WebGL 检测 + 降级
2. `feishu_oauth_service.py` (modify) -- OAuth v1->v2 升级 + EmployeeMaster 自动绑定
3. `FeishuFieldMappingPage.tsx` (modify) -- 字段类型展示 + 同义词匹配 + 未映射警告
4. `FeishuSettings.tsx` (modify) -- table_id 下拉联动 + redirect_uri 配置
5. `Login.tsx` (modify) -- 左右分栏布局重做

**Key patterns:**
- Best-Effort Binding: OAuth 匹配是尽力而为，不强制；唯一匹配自动绑定，多人同名标记待确认，无匹配创建新用户
- Canvas Isolation: Three.js Canvas 与 React DOM 严格分层（z-index 隔离），避免事件冲突
- Runtime Settings Merge: 新配置项优先从 system_settings 表读取，fallback 到 .env

### Critical Pitfalls

1. **飞书字段类型读写不对称** -- 文本字段写入是 plain string，读取是 `[{"type":"text","text":"..."}]` 富文本数组。必须建立 `FeishuFieldSerializer` 做类型感知的双向转换，`field_mapping` 结构扩展为含 field_id + field_type
2. **OAuth 用户身份割裂** -- 已有管理员用飞书登录会创建新 employee 用户，同人两账号。必须实现分层匹配（open_id -> 姓名+工号 -> 姓名 -> 创建新用户），匹配成功保留原有 role
3. **Three.js Canvas 内存泄漏** -- 路由切换时 WebGL context 不会被 JS GC 回收。必须在 useEffect cleanup 中执行完整 6 步 dispose 序列，包括 `renderer.forceContextLoss()`
4. **CSRF State Cookie 生产环境丢失** -- 现有 `samesite=lax, secure=False` 在前后端分离部署下会导致 OAuth 100% 失败。必须根据环境动态设置 cookie 参数
5. **field_mapping 向后兼容** -- 从简单 dict 升级到含 field_id/field_type 结构会破坏已有 SyncConfig 记录。需写迁移逻辑兼容旧格式

## Implications for Roadmap

### Phase 1: 飞书字段映射完善
**Rationale:** 最低风险，后端 API 全部就绪，纯 UI 增强。为 Phase 2 热身飞书 API 集成模式。不涉及 auth 变更或新依赖。
**Delivers:** 完善的字段映射 UI（类型展示 + 同义词匹配 + 预览 + 警告）+ table_id 下拉联动选择
**Addresses:** FEATURES 中字段映射完善所有 table stakes 项
**Avoids:** Pitfall #1（字段类型不对称）-- 在此阶段建立 field_type 感知的映射结构
**Estimated:** 1-2 天

### Phase 2: 飞书 OAuth 自动匹配登录
**Rationale:** 涉及 DB schema 变更和身份逻辑，是登录页改版的前置条件（OAuth 流程必须稳定后才改 UI）。包含飞书扫码登录（QRLogin SDK）。
**Delivers:** OAuth v2 升级 + EmployeeMaster 自动绑定 + 多匹配确认 UI + redirect_uri 运行时配置 + 飞书扫码登录
**Addresses:** FEATURES 中 OAuth 自动匹配绑定所有项
**Avoids:** Pitfall #2（身份割裂）和 Pitfall #4（CSRF cookie 跨域）
**Estimated:** 2-3 天

### Phase 3: 登录页面改版
**Rationale:** 纯前端视觉变更 + 新依赖引入，依赖 Phase 2 的 OAuth 流程已稳定。Three.js 粒子波浪是 v1.2 最大的视觉亮点。
**Delivers:** 左右分栏登录页 + Three.js GPU 粒子波浪背景 + 移动端适配 + WebGL 降级 + 暗黑模式适配 + 懒加载优化
**Uses:** three@~0.172.0 + @react-three/fiber@^8.17.10（不使用 drei）
**Avoids:** Pitfall #3（WebGL 内存泄漏）-- 严格的 dispose cleanup + forceContextLoss + 设备检测
**Estimated:** 3-4 天

### Phase Ordering Rationale

- **依赖关系驱动:** 字段映射是独立模块，OAuth 改动影响登录流程，登录页改版依赖 OAuth 稳定。反向顺序会导致返工。
- **风险递增:** 低风险先行建立信心和节奏，高复杂度后行有更多缓冲。
- **功能隔离:** 每个 Phase 交付独立可测试的功能增量。Phase 1 完成后字段映射立即可用；Phase 2 完成后 OAuth 增强立即可用；Phase 3 是纯视觉升级，不影响功能。

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 2:** OAuth v1->v2 API 迁移的响应格式差异需实际验证（v2 在 token 响应中直接包含用户信息 vs v1 需单独调 user info API）；CSRF cookie 策略需在 staging 环境端到端验证；飞书扫码 QRLogin SDK 的 CDN 可达性需在目标部署环境测试
- **Phase 3:** Three.js dispose cleanup 的完整性需通过 Chrome Memory 工具实测验证；R3F v8 与 three@0.172 的实际兼容性需安装后验证；Vite code splitting 是否正确隔离 Three.js chunk 需 bundle analyzer 确认

Phases with standard patterns (skip research-phase):
- **Phase 1:** 飞书 Bitable API 已有完整代码和文档，字段类型映射是标准 CRUD UI 增强，所有后端方法已实现

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | R3F v8 = React 18 关系由 npm 官方确认；飞书 SDK 多个教程验证可用；后端零新依赖 |
| Features | HIGH | 三项功能边界清晰，已有代码基础明确，FEATURES 研究涵盖完整的交互规格 |
| Architecture | HIGH | 基于现有代码深度分析，改动范围精确到文件和行号，数据流清晰 |
| Pitfalls | HIGH | 4 个 critical pitfall 均有现有代码一手证据和社区 issue 支撑 |

**Overall confidence:** HIGH

### Gaps to Address

- **drei 是否最终需要:** 建议 Phase 3 先不装，用 raw shader 实现；如果开发效率不佳再引入
- **飞书 QRLogin SDK CDN 可达性:** 1.0.3 版本需在目标部署环境（可能有网络限制）测试可达性，可能需要自托管
- **Vite code splitting 实际效果:** Three.js lazy import 理论上可隔离到登录页 chunk，需 `vite-bundle-visualizer` 实际验证
- **Python 3.9 兼容性:** v1.2 新增代码需避免 3.10+ 语法（match/case, `X | Y` type union）
- **field_mapping 旧数据迁移:** 结构升级后已有 SyncConfig 记录的兼容性需在 Phase 1 实现时验证

## Sources

### Primary (HIGH confidence)
- [R3F Official Docs](https://r3f.docs.pmnd.rs/getting-started/introduction) -- v8/v9 React 版本对应关系
- [飞书 Bitable API](https://open.feishu.cn/document/server-docs/docs/bitable-v1/bitable-overview) -- list_fields, list_tables, 字段类型枚举
- [飞书 OAuth v2](https://open.feishu.cn/document/authentication-management/access-token/get-user-access-token) -- token exchange 格式
- [飞书 Bitable 数据结构](https://open.feishu.cn/document/docs/bitable-v1/app-table-record/bitable-record-data-structure-overview) -- 字段类型读写格式差异
- [R3F GitHub Issue #514](https://github.com/pmndrs/react-three-fiber/issues/514) -- Canvas unmount 内存泄漏确认
- 项目源码一手分析: feishu_client.py, feishu_auth.py, feishu_oauth_service.py, Login.tsx, user.py

### Secondary (MEDIUM confidence)
- [飞书扫码登录教程](https://open.larkoffice.com/document/qr-code-scanning-login-for-web-app/introduction) -- QRLogin SDK 用法
- [掘金/CSDN 飞书扫码对接](https://juejin.cn/post/7501203502665891866) -- 社区实践验证
- [Three.js 粒子波浪示例](https://threejs.org/examples/webgl_points_waves.html) -- 参考实现
- [R3F 粒子 Shader 教程](https://blog.maximeheckel.com/posts/the-magical-world-of-particles-with-react-three-fiber-and-shaders/) -- GPU shader 方案
- [Codrops: Shader Background with R3F](https://tympanus.net/codrops/2024/10/31/how-to-code-a-subtle-shader-background-effect-with-react-three-fiber/) -- 视觉参考
- [OAuth 2.0 Pitfalls](https://treblle.com/blog/oauth-2.0-for-apis) -- redirect URI, CSRF state 最佳实践

---
*Research completed: 2026-04-14*
*Ready for roadmap: yes*
