# Requirements: 社保公积金管理系统

**Defined:** 2026-04-04
**Core Value:** 社保公积金数据从多地区 Excel 汇入系统后，任何角色都能在正确的权限范围内快速查询和管理数据。

## v1.1 Requirements

Requirements for v1.1 release. Each maps to roadmap phases.

### 基础设施 (INFRA)

- [ ] **INFRA-01**: 系统适配 Python 3.9 运行环境（移除 slots=True、确保类型注解兼容、依赖版本锁定）
- [ ] **INFRA-02**: 清理 v1.0 遗留技术债（废弃组件删除、缺失测试补充）
- [ ] **INFRA-03**: 审计日志获取真实客户端 IP 地址（X-Forwarded-For / X-Real-IP 解析）
- [ ] **INFRA-04**: 审计日志内容增强（更完整的操作记录和上下文信息）

### 前端体验 (UX)

- [ ] **UX-01**: 内联样式 token 化（将硬编码颜色替换为 Ant Design 主题 token）
- [ ] **UX-02**: 用户可切换暗黑模式，偏好持久化到 localStorage
- [ ] **UX-03**: 全页面响应式自适应（手机端+平板+不同窗口尺寸，所有数据页面逐一适配）
- [ ] **UX-04**: 左侧菜单多级折叠（低频功能收进高级设置等子菜单）
- [ ] **UX-05**: 设置页支持搜索并快速导航到对应设置项

### 账号管理 (ACCT)

- [ ] **ACCT-01**: 管理员可创建新用户账号
- [ ] **ACCT-02**: 管理员可修改用户角色权限
- [ ] **ACCT-03**: 管理员可重置用户密码
- [ ] **ACCT-04**: 用户可修改自己的密码

### 数据管理 (DATA)

- [ ] **DATA-01**: 数据管理筛选支持多选（地区、公司等下拉框）
- [ ] **DATA-02**: 数据管理新增已匹配/未匹配过滤选项，默认选择已匹配
- [ ] **DATA-03**: 批次删除时联动清理关联的月份数据（NormalizedRecords + MatchResults + ValidationIssues）
- [ ] **DATA-04**: 个人险种缴费基数数据修复（显示真实基数而非错误值）

### 月度对比 (COMP)

- [ ] **COMP-01**: 月度对比改为代码 diff 风格（左右 Excel 表格样式 + 差异单元格高亮）

### 融合增强 (FUSE)

- [ ] **FUSE-01**: 融合增加个人社保承担额和个人公积金承担额（支持 Excel 上传或飞书文档同步输入）
- [ ] **FUSE-02**: 快速融合页面显示已上传文件计数
- [ ] **FUSE-03**: 快速融合支持特殊规则配置（选人+选字段+覆盖值，规则可保存复用）
- [ ] **FUSE-04**: 员工主档默认选择使用服务器已有主档

### 飞书集成 (FEISHU)

- [ ] **FEISHU-01**: 飞书相关配置（凭证、同步设置等）可在前端页面直接修改

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

- **DEPLOY-01**: 迁移到 PostgreSQL 以支持后台定时同步飞书
- **DEPLOY-02**: Docker 容器化部署方案
- **MOBILE-01**: 移动端原生 App

## Out of Scope

| Feature | Reason |
|---------|--------|
| 移动端原生 App | 当前只做 Web 响应式 |
| 薪资计算 | 本系统只管社保公积金数据 |
| 多租户/SaaS | 单公司内部使用 |
| Salary 模板融合逻辑改动 | 已完美运行，禁止修改 |
| 后台定时同步飞书 | 需迁移到 PostgreSQL，v2 考虑 |
| PostgreSQL 迁移 | v1.1 保持 SQLite，v2 考虑 |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| INFRA-01 | — | Pending |
| INFRA-02 | — | Pending |
| INFRA-03 | — | Pending |
| INFRA-04 | — | Pending |
| UX-01 | — | Pending |
| UX-02 | — | Pending |
| UX-03 | — | Pending |
| UX-04 | — | Pending |
| UX-05 | — | Pending |
| ACCT-01 | — | Pending |
| ACCT-02 | — | Pending |
| ACCT-03 | — | Pending |
| ACCT-04 | — | Pending |
| DATA-01 | — | Pending |
| DATA-02 | — | Pending |
| DATA-03 | — | Pending |
| DATA-04 | — | Pending |
| COMP-01 | — | Pending |
| FUSE-01 | — | Pending |
| FUSE-02 | — | Pending |
| FUSE-03 | — | Pending |
| FUSE-04 | — | Pending |
| FEISHU-01 | — | Pending |

**Coverage:**
- v1.1 requirements: 23 total
- Mapped to phases: 0
- Unmapped: 23 ⚠️

---
*Requirements defined: 2026-04-04*
*Last updated: 2026-04-04 after initial definition*
