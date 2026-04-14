---
phase: 20-compare-redesign-and-feishu-enhancement
plan: 03
title: "Phase 20 Plan 03: 飞书 runtime settings 持久化与 effective settings 服务"
subsystem: backend
tags: [feishu, settings, sqlite, effective-settings, security]
dependency_graph:
  requires: []
  provides: [db-backed-feishu-runtime-settings, effective-feishu-settings]
  affects: [system-features, feishu-auth, feishu-sync, feishu-settings-api]
tech_stack:
  added: []
  patterns: [sqlite-settings-table, effective-settings-service, masked-secret-contract]
key_files:
  created:
    - backend/app/models/system_setting.py
    - backend/app/services/system_setting_service.py
    - backend/alembic/versions/20260409_0011_add_system_settings.py
    - backend/tests/test_feishu_settings_api.py
  modified:
    - backend/app/models/__init__.py
    - backend/app/schemas/feishu.py
    - backend/app/api/v1/system.py
    - backend/app/api/v1/feishu_auth.py
    - backend/app/api/v1/feishu_sync.py
    - backend/app/api/v1/feishu_settings.py
    - backend/app/services/feishu_client.py
decisions:
  - "前端写入的飞书开关与凭证落到 `system_settings`，再由 effective settings 统一覆盖 env 默认值"
  - "所有对外读取只返回 `masked_app_id` 与 `secret_configured`，不允许任何 API 回显明文 secret"
  - "OAuth、feature flags、sync client、settings client 全部复用同一 effective settings 来源，禁止分叉读取"
metrics:
  duration: "n/a"
  completed: "2026-04-09T23:22:19+08:00"
  tasks_completed: 2
  tasks_total: 2
  files_modified: 11
requirements:
  - FEISHU-01
---

# Phase 20 Plan 03: 飞书 runtime settings 持久化与 effective settings 服务 Summary

飞书运行时设置的后端闭环已经补齐：前端现在不再只能读环境变量，而是可以通过 API 写入 DB-backed settings，并让 auth/sync/features 统一读取同一份 effective state。

## What Was Done

### Task 1: 新增 system_settings 模型与 effective settings 服务
- 新增 `SystemSetting` 模型和 Alembic migration
- 实现 `system_setting_service.py`，统一管理 sync 开关、oauth 开关、app id、app secret 以及脱敏展示
- `get_effective_feishu_settings()` 会把数据库覆盖值和应用默认设置合并成一份运行时视图

### Task 2: 让 Feishu auth/sync/settings/system features 共用 effective settings
- `/system/features`、`/auth/feishu/*`、`/feishu/sync/*`、`/feishu/settings/*` 全部切到 effective settings
- `feishu_client` 根据显式凭证重建/缓存 client，避免旧 client 绑死旧凭证
- 新增 `backend/tests/test_feishu_settings_api.py`，覆盖 runtime settings、RBAC、feature flag/effective settings 联动

## Verification Results

- `python3 -m pytest backend/tests/test_feishu_settings_api.py -q`
- `python3 -m pytest backend/tests/test_compare_api.py backend/tests/test_feishu_settings_api.py -q`
- 通过；仅剩测试环境 JWT key 长度 warning，不影响 Phase 20 结论

## Deviations from Plan

None - plan executed as intended.

## Commits

Deferred. Phase 20 本轮以内联执行完成，没有额外创建提交。

## Self-Check: PASSED

- 运行时飞书开关/凭证已可持久化
- effective settings 已统一驱动 features/auth/sync/settings
- secret 只写不回显的合同已落实到 schema 和测试
