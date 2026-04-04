# Requirements: 社保公积金管理系统

**Defined:** 2026-03-27
**Core Value:** 社保公积金数据从多地区 Excel 汇入系统后，任何角色都能在正确的权限范围内快速查询和管理数据。

## v1 Requirements

### 导出稳定化 (EXPORT)

- [ ] **EXPORT-01**: Tool 模板导出的字段与标题正确匹配，不再错位
- [ ] **EXPORT-02**: Salary 模板导出保持完美运行（回归测试覆盖）
- [ ] **EXPORT-03**: 导出器代码拆分为独立模块（salary_exporter / tool_exporter / export_utils）
- [ ] **EXPORT-04**: 两份模板可同时成功导出

### 认证与权限 (AUTH)

- [x] **AUTH-01**: 管理员/HR 可通过用户名+密码登录
- [x] **AUTH-02**: 员工可通过工号+身份证号+姓名验证身份并查询
- [x] **AUTH-03**: 三角色 RBAC 权限体系生效（管理员/HR/员工）
- [x] **AUTH-04**: 管理员可管理用户账号（创建/编辑/禁用）
- [x] **AUTH-05**: 用户会话在浏览器刷新后保持
- [x] **AUTH-06**: PyJWT 替换已废弃的 python-jose
- [ ] **AUTH-07**: API Key 认证机制（供外部程序调用）
- [ ] **AUTH-08**: 管理员可创建和管理 API Key

### 安全加固 (SEC)

- [x] **SEC-01**: 所有包含 PII 数据的端点必须要求认证
- [x] **SEC-02**: 员工查询端点有频率限制（防止身份证号枚举）
- [x] **SEC-03**: 关键操作记录审计日志（登录/导出/数据修改）
- [x] **SEC-04**: 身份证号在非必要场景下脱敏显示

### 员工门户 (PORTAL)

- [x] **PORTAL-01**: 员工可查看个人社保明细（按月份）
- [x] **PORTAL-02**: 员工可查看个人公积金明细（按月份）
- [x] **PORTAL-03**: 员工可查看历史缴费记录（多期浏览）
- [x] **PORTAL-04**: 员工只能看到自己的数据，无法访问他人信息
- [x] **PORTAL-05**: 查询结果展示缴费基数、单位/个人各险种金额

### 员工主数据 (MASTER)

- [x] **MASTER-01**: HR 可维护员工主数据（姓名/工号/身份证号/所属公司/地区）
- [x] **MASTER-02**: HR 可批量导入员工主数据
- [x] **MASTER-03**: 员工主数据支持搜索和筛选
- [x] **MASTER-04**: 导入的社保数据自动与员工主数据匹配

### 数据管理 (DATA)

- [x] **DATA-01**: HR 可按地区、公司、月份筛选社保数据
- [x] **DATA-02**: HR 可查看全员社保公积金汇总
- [x] **DATA-03**: 数据校验仪表盘展示导入质量（缺失/异常/重复）
- [x] **DATA-04**: 导入历史可追溯（文件名、时间、操作人、记录数）

### 前端重设计 (UI)

- [x] **UI-01**: 采用 Ant Design 5.x 重建所有页面
- [x] **UI-02**: 飞书风格主题（简洁、卡片化、专业感）
- [x] **UI-03**: 页面切换和滚动有流畅的动画效果
- [x] **UI-04**: 背景和网页设计有精致的细节配合
- [x] **UI-05**: 角色感知路由（不同角色看到不同导航菜单）
- [x] **UI-06**: 响应式布局适配主流分辨率
- [x] **UI-07**: 中文本地化完整
- [x] **UI-08**: 上传/解析/导出流程操作逻辑顺畅

### API 体系 (API)

- [x] **API-01**: RESTful API 覆盖所有核心功能（社保查询/员工管理/导入导出）
- [x] **API-02**: API 文档自动生成（OpenAPI/Swagger）
- [x] **API-03**: API 响应格式统一且规范
- [ ] **API-04**: 外部程序可通过 API Key 调用所有公开接口

### 飞书集成 (FEISHU)

- [x] **FEISHU-01**: 系统数据可推送到飞书多维表格（push sync）
- [x] **FEISHU-02**: 飞书多维表格数据可拉取到系统（pull sync）
- [x] **FEISHU-03**: 同步状态可查看（成功/失败/冲突记录）
- [x] **FEISHU-04**: 同步操作为手动触发（非后台自动）
- [x] **FEISHU-05**: 飞书 OAuth 登录支持（可选功能，feature flag 控制）

### 智能与完善 (INTEL)

- [x] **INTEL-01**: 跨期对比视图（多月份数据对比）
- [x] **INTEL-02**: 异常检测（缴费基数突变、金额异常偏高/偏低）
- [ ] **INTEL-03**: 公积金数据全地区标准化覆盖
- [ ] **INTEL-04**: 字段映射覆盖 UI（HR 可手动修正映射）

## v2 Requirements

### 高级功能

- **ADV-01**: 推送通知（新数据导入后通知相关员工）
- **ADV-02**: 数据导出为 PDF 格式（个人社保证明）
- **ADV-03**: 多维度统计报表（按部门/地区/险种汇总）
- **ADV-04**: 飞书机器人消息通知
- **ADV-05**: 后台定时同步飞书（需迁移到 PostgreSQL）

## Out of Scope

| Feature | Reason |
|---------|--------|
| 薪资计算 | 本系统只管社保公积金数据，不涉及薪资核算 |
| 政府社保网站直接申报 | 各城市门户不同，合规面太大 |
| 自定义报表生成器 | 飞书多维表格已覆盖临时分析需求 |
| 多租户 / SaaS | 单公司使用，无需租户隔离 |
| 移动端原生 App | 当前阶段只做 Web |
| Salary 模板融合逻辑修改 | 已完美运行，禁止修改 |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| EXPORT-01 | Phase 1 | Pending |
| EXPORT-02 | Phase 1 | Pending |
| EXPORT-03 | Phase 1 | Pending |
| EXPORT-04 | Phase 1 | Pending |
| AUTH-01 | Phase 2 | Complete |
| AUTH-02 | Phase 2 | Complete |
| AUTH-03 | Phase 2 | Complete |
| AUTH-04 | Phase 2 | Complete |
| AUTH-05 | Phase 2 | Complete |
| AUTH-06 | Phase 2 | Complete |
| SEC-01 | Phase 3 | Complete |
| SEC-02 | Phase 3 | Complete |
| SEC-03 | Phase 3 | Complete |
| SEC-04 | Phase 3 | Complete |
| MASTER-01 | Phase 4 | Complete |
| MASTER-02 | Phase 4 | Complete |
| MASTER-03 | Phase 4 | Complete |
| MASTER-04 | Phase 4 | Complete |
| PORTAL-01 | Phase 5 | Complete |
| PORTAL-02 | Phase 5 | Complete |
| PORTAL-03 | Phase 5 | Complete |
| PORTAL-04 | Phase 5 | Complete |
| PORTAL-05 | Phase 5 | Complete |
| DATA-01 | Phase 6 | Complete |
| DATA-02 | Phase 6 | Complete |
| DATA-03 | Phase 6 | Complete |
| DATA-04 | Phase 6 | Complete |
| UI-01 | Phase 7 | Complete |
| UI-02 | Phase 7 | Complete |
| UI-03 | Phase 7 | Complete |
| UI-04 | Phase 7 | Complete |
| UI-05 | Phase 8 | Complete |
| UI-06 | Phase 8 | Complete |
| UI-07 | Phase 8 | Complete |
| UI-08 | Phase 8 | Complete |
| API-01 | Phase 9 | Complete |
| API-02 | Phase 9 | Complete |
| API-03 | Phase 9 | Complete |
| API-04 | Phase 9 | Pending |
| AUTH-07 | Phase 9 | Pending |
| AUTH-08 | Phase 9 | Pending |
| FEISHU-01 | Phase 10 | Complete |
| FEISHU-02 | Phase 10 | Complete |
| FEISHU-03 | Phase 10 | Complete |
| FEISHU-04 | Phase 10 | Complete |
| FEISHU-05 | Phase 10 | Complete |
| INTEL-01 | Phase 11 | Complete |
| INTEL-02 | Phase 11 | Complete |
| INTEL-03 | Phase 11 | Pending |
| INTEL-04 | Phase 11 | Pending |

**Coverage:**
- v1 requirements: 49 total
- Mapped to phases: 49
- Unmapped: 0

---
*Requirements defined: 2026-03-27*
*Last updated: 2026-03-27 after roadmap creation (11 phases, fine granularity)*
