# Requirements: 社保公积金管理系统

**Defined:** 2026-04-14
**Core Value:** 社保公积金数据从多地区 Excel 汇入系统后，任何角色都能在正确的权限范围内快速查询和管理数据。

## v1.2 Requirements

Requirements for milestone v1.2: 飞书深度集成与登录体验升级。

### 飞书字段映射

- [ ] **FMAP-01**: 用户可在飞书字段映射页看到从飞书多维表格 API 拉取的真实字段列表
- [ ] **FMAP-02**: 用户可在映射 UI 中看到每个飞书字段的类型标签（文本/数字/单选等）
- [ ] **FMAP-03**: 用户保存映射时，系统检查核心字段（person_name、employee_id 等）是否已映射，未映射则弹出警告
- [ ] **FMAP-04**: 系统基于中英文同义词库自动推荐字段映射候选项（如 "养老保险(单位)" ↔ pension_company）

### 飞书 OAuth 登录

- [ ] **OAUTH-01**: 用户可在登录页通过飞书扫码或本设备飞书自动登录进入系统
- [ ] **OAUTH-02**: 飞书登录后系统自动按姓名/工号查询 EmployeeMaster，唯一匹配时自动绑定系统用户
- [ ] **OAUTH-03**: 同名多人时系统展示候选列表让用户选择绑定目标，无匹配时创建无绑定的 employee 用户
- [ ] **OAUTH-04**: 已登录用户可在个人设置页通过"绑定飞书"入口关联自己的飞书账号

### 登录页面改版

- [ ] **LOGIN-01**: 登录页采用左右分栏布局（左侧品牌展示+动画背景，右侧登录表单），移动端只显示表单
- [ ] **LOGIN-02**: 登录页左侧使用 Three.js 3D 粒子波浪动态背景，支持鼠标交互跟随效果
- [ ] **LOGIN-03**: 不支持 WebGL 的环境下登录页优雅降级为静态渐变背景
- [ ] **LOGIN-04**: 登录页粒子颜色和表单卡片适配暗黑模式

## Future Requirements

### 飞书增强

- **FMAP-05**: 映射配置模板导入导出（JSON 格式跨环境复用）
- **FMAP-06**: 映射结果保存前 Modal 汇总预览
- **OAUTH-05**: 飞书通讯录 employee_no 精确拉取（需额外权限审批）

## Out of Scope

| Feature | Reason |
|---------|--------|
| 飞书字段自动创建/删除 | 修改用户飞书多维表格结构风险极高 |
| 飞书 OAuth 替代所有登录方式 | 管理员/HR 需要独立密码登录作为降级方案 |
| 复杂 3D 场景（模型/物理引擎） | 登录页只需视觉氛围，不需重型 3D 资源 |
| 飞书通讯录自动同步到员工主数据 | SQLite 不支持并发后台任务，涉及隐私合规 |
| 飞书登录用户自动提升角色 | 安全风险，角色提升应由管理员显式操作 |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| FMAP-01 | — | Pending |
| FMAP-02 | — | Pending |
| FMAP-03 | — | Pending |
| FMAP-04 | — | Pending |
| OAUTH-01 | — | Pending |
| OAUTH-02 | — | Pending |
| OAUTH-03 | — | Pending |
| OAUTH-04 | — | Pending |
| LOGIN-01 | — | Pending |
| LOGIN-02 | — | Pending |
| LOGIN-03 | — | Pending |
| LOGIN-04 | — | Pending |

**Coverage:**
- v1.2 requirements: 12 total
- Mapped to phases: 0
- Unmapped: 12

---
*Requirements defined: 2026-04-14*
*Last updated: 2026-04-14 after initial definition*
