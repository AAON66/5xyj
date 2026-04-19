# Roadmap: 社保公积金管理系统

## Milestones

- ✅ **v1.0 社保公积金管理系统** — Phases 1-12 (shipped 2026-04-04)
- ✅ **v1.1 体验优化与功能完善** — Phases 13-20 (shipped 2026-04-14)
- 🚧 **v1.2 飞书深度集成与登录体验升级** — Phases 21-23 (in progress)

## Phases

<details>
<summary>✅ v1.0 社保公积金管理系统 (Phases 1-12) — SHIPPED 2026-04-04</summary>

- [x] Phase 1: Export Stabilization (2/2 plans)
- [x] Phase 2: Authentication & RBAC (3/3 plans)
- [x] Phase 3: Security Hardening (2/2 plans)
- [x] Phase 4: Employee Master Data (2/2 plans) — completed 2026-03-29
- [x] Phase 5: Employee Portal (2/2 plans) — completed 2026-03-30
- [x] Phase 6: Data Management (2/2 plans)
- [x] Phase 7: Design System & UI Foundation (4/4 plans)
- [x] Phase 8: Page Rebuild & UX Flow (2/2 plans)
- [x] Phase 9: API System (2/2 plans)
- [x] Phase 10: Feishu Integration (4/4 plans) — completed 2026-04-02
- [x] Phase 11: Intelligence & Polish (5/5 plans) — completed 2026-04-04
- [x] Phase 12: Integration Wiring Fix (1/1 plan) — completed 2026-04-04

**Total:** 12 phases, 31 plans, 56 tasks

See: `.planning/milestones/v1.0-ROADMAP.md` for full details

</details>

<details>
<summary>✅ v1.1 体验优化与功能完善 (Phases 13-20) — SHIPPED 2026-04-14</summary>

- [x] Phase 13: 基础准备与部署适配 (4/4 plans) — completed 2026-04-05
- [x] Phase 14: 样式 Token 化与暗黑模式 (4/4 plans) — completed 2026-04-07
- [x] Phase 15: 菜单重组与设置导航 (2/2 plans) — completed 2026-04-07
- [x] Phase 16: 账号管理 (2/2 plans) — completed 2026-04-08
- [x] Phase 17: 数据管理增强 (3/3 plans) — completed 2026-04-08
- [x] Phase 18: 全页面响应式适配 (5/5 plans) — completed 2026-04-09
- [x] Phase 19: 融合能力增强 (4/4 plans) — completed 2026-04-09
- [x] Phase 20: 对比重做与飞书完善 (4/4 plans) — completed 2026-04-09

**Total:** 8 phases, 28 plans, 57 tasks

See: `.planning/milestones/v1.1-ROADMAP.md` for full details

</details>

### v1.2 飞书深度集成与登录体验升级 (In Progress)

**Milestone Goal:** 打通飞书字段映射闭环、实现飞书 OAuth 自动登录、重做登录页面视觉体验

- [x] **Phase 21: 飞书字段映射完善** - 拉取飞书真实字段并实现类型感知的智能映射 UI (completed 2026-04-16)
- [x] **Phase 22: 飞书 OAuth 自动匹配登录** - 飞书扫码登录 + 按姓名/工号自动绑定系统用户 (completed 2026-04-17)
- [ ] **Phase 23: 登录页面改版** - 左右分栏布局 + Three.js 3D 粒子波浪动态背景

## Phase Details

### Phase 21: 飞书字段映射完善
**Goal**: 用户能在映射 UI 中看到飞书多维表格的真实字段及其类型，并获得智能映射推荐和完整性校验
**Depends on**: Nothing (v1.1 Phase 20 飞书基础已完成)
**Requirements**: FMAP-01, FMAP-02, FMAP-03, FMAP-04
**Success Criteria** (what must be TRUE):
  1. 用户打开飞书字段映射页时，能看到从飞书 API 实时拉取的字段列表（而非手动输入）
  2. 每个飞书字段旁边显示类型标签（文本/数字/单选等），用户可据此判断字段性质
  3. 用户保存映射配置时，如果 person_name 或 employee_id 等核心字段未映射，系统弹出明确警告
  4. 系统根据中英文同义词库自动推荐映射候选项，用户可一键接受或手动调整
**Plans**: 2 plans

Plans:
- [x] 21-01-PLAN.md — 后端 FeishuFieldInfo 扩展 ui_type + suggest-mapping API + 前端服务层
- [x] 21-02-PLAN.md — 前端 UI 增强（类型 Tag + 智能连线 + 两步 Modal 保存流程）

**UI hint**: yes

### Phase 22: 飞书 OAuth 自动匹配登录
**Goal**: 用户能通过飞书扫码或自动登录进入系统，系统自动将飞书身份与已有员工数据绑定
**Depends on**: Phase 21 (field_mapping 结构升级需先完成，避免 schema 冲突)
**Requirements**: OAUTH-01, OAUTH-02, OAUTH-03, OAUTH-04
**Success Criteria** (what must be TRUE):
  1. 用户在登录页点击"飞书登录"后，通过扫码或本设备飞书自动完成登录，进入系统主页
  2. 飞书登录后若姓名/工号在 EmployeeMaster 中唯一匹配，系统自动绑定该员工身份，用户无需手动操作
  3. 飞书登录后若存在同名多人，系统展示候选列表让用户选择绑定目标；无匹配时创建无绑定的 employee 用户
  4. 已登录用户可在个人设置页通过"绑定飞书"入口主动关联自己的飞书账号
**Plans**: 3 plans

Plans:
- [x] 22-01-PLAN.md — 后端三级匹配逻辑 + confirm-bind + bind/unbind 端点 + 测试
- [x] 22-02-PLAN.md — 前端 Login.tsx OAuth 回调处理 + CandidateSelectModal 候选人选择
- [x] 22-03-PLAN.md — 前端 Settings.tsx 飞书账号绑定卡片

**UI hint**: yes

### Phase 23: 登录页面改版
**Goal**: 登录页面呈现专业品牌形象，左侧 3D 粒子波浪动态背景提升视觉冲击力，同时兼容各种设备和环境
**Depends on**: Phase 22 (OAuth 流程必须稳定后才改登录 UI，避免返工)
**Requirements**: LOGIN-01, LOGIN-02, LOGIN-03, LOGIN-04
**Success Criteria** (what must be TRUE):
  1. 桌面端登录页呈现左右分栏布局（左侧品牌展示+动画背景，右侧登录表单），移动端只显示表单
  2. 登录页左侧展示 Three.js 3D 粒子波浪动画，粒子随鼠标移动产生交互跟随效果
  3. 在不支持 WebGL 的环境下，登录页自动降级为静态渐变背景，不影响登录功能
  4. 登录页粒子颜色和表单卡片在暗黑模式下自动切换为适配的配色方案
**Plans**: 3 plans

Plans:
- [ ] 23-01-PLAN.md — three 依赖 + useWebGLSupport hook + CssGradientBackground + Wave 0 E2E 脚手架
- [ ] 23-02-PLAN.md — ParticleWave.tsx (Three.js 2560 粒子 + GPU shader 波浪 + 鼠标 gaussian 隆起 + cleanup)
- [ ] 23-03-PLAN.md — BrandPanel + Login.tsx 分栏重构 + 玻璃卡片 + human-verify checkpoint

**UI hint**: yes

## Progress

**Execution Order:**
Phases execute in numeric order: 21 -> 22 -> 23

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Export Stabilization | v1.0 | 2/2 | Complete | - |
| 2. Authentication & RBAC | v1.0 | 3/3 | Complete | - |
| 3. Security Hardening | v1.0 | 2/2 | Complete | - |
| 4. Employee Master Data | v1.0 | 2/2 | Complete | 2026-03-29 |
| 5. Employee Portal | v1.0 | 2/2 | Complete | 2026-03-30 |
| 6. Data Management | v1.0 | 2/2 | Complete | - |
| 7. Design System & UI Foundation | v1.0 | 4/4 | Complete | - |
| 8. Page Rebuild & UX Flow | v1.0 | 2/2 | Complete | - |
| 9. API System | v1.0 | 2/2 | Complete | - |
| 10. Feishu Integration | v1.0 | 4/4 | Complete | 2026-04-02 |
| 11. Intelligence & Polish | v1.0 | 5/5 | Complete | 2026-04-04 |
| 12. Integration Wiring Fix | v1.0 | 1/1 | Complete | 2026-04-04 |
| 13. 基础准备与部署适配 | v1.1 | 4/4 | Complete | 2026-04-05 |
| 14. 样式 Token 化与暗黑模式 | v1.1 | 4/4 | Complete | 2026-04-07 |
| 15. 菜单重组与设置导航 | v1.1 | 2/2 | Complete | 2026-04-07 |
| 16. 账号管理 | v1.1 | 2/2 | Complete | 2026-04-08 |
| 17. 数据管理增强 | v1.1 | 3/3 | Complete | 2026-04-08 |
| 18. 全页面响应式适配 | v1.1 | 5/5 | Complete | 2026-04-09 |
| 19. 融合能力增强 | v1.1 | 4/4 | Complete | 2026-04-09 |
| 20. 对比重做与飞书完善 | v1.1 | 4/4 | Complete | 2026-04-09 |
| 21. 飞书字段映射完善 | v1.2 | 2/2 | Complete    | 2026-04-16 |
| 22. 飞书 OAuth 自动匹配登录 | v1.2 | 3/3 | Complete    | 2026-04-17 |
| 23. 登录页面改版 | v1.2 | 0/3 | Planned     | - |
