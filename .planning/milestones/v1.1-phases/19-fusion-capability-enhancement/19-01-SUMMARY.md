---
phase: 19-fusion-capability-enhancement
plan: 01
title: "Phase 19 Plan 01: FusionRule 模型与 CRUD API"
subsystem: backend
tags: [fusion, rules, api, rbac, sqlalchemy]
dependency_graph:
  requires: []
  provides: [fusion-rule-model, fusion-rule-crud-api]
  affects: [aggregate-runtime, simple-aggregate-ui]
tech_stack:
  added: []
  patterns: [sqlalchemy-model, fastapi-router, admin-hr-rbac]
key_files:
  created:
    - backend/app/models/fusion_rule.py
    - backend/app/schemas/fusion_rules.py
    - backend/app/services/fusion_rule_service.py
    - backend/app/api/v1/fusion_rules.py
    - backend/alembic/versions/20260409_0010_add_fusion_rules.py
  modified:
    - backend/app/models/__init__.py
    - backend/app/api/v1/router.py
decisions:
  - "规则命中范围仅允许 `employee_id` 和 `id_number`，禁止姓名等低置信键"
  - "字段白名单只开放 `personal_social_burden` 与 `personal_housing_burden`，避免任意金额字段被越权覆盖"
metrics:
  duration: "n/a"
  completed: "2026-04-09T15:33:56+08:00"
  tasks_completed: 2
  tasks_total: 2
  files_modified: 7
requirements:
  - FUSE-03
---

# Phase 19 Plan 01: FusionRule 模型与 CRUD API Summary

Phase 19 的规则持久化底座已经就位，管理员和 HR 可以创建、更新、删除和复用特殊覆盖规则。

## What Was Done

### Task 1: 建立 FusionRule 持久化模型与约束
- 新增 `fusion_rules` 表、Alembic migration，以及 `FusionRule` SQLAlchemy 模型
- 用数据库 check constraint 和 service 白名单同时约束 `scope_type` 与 `field_name`
- 在 `models/__init__.py` 暴露模型，供 API 和 runtime 复用

### Task 2: 提供带权限边界的 CRUD API
- 新增 `fusion_rules` schema、service 和 FastAPI router
- 暴露 `GET/POST/PUT/DELETE /api/v1/fusion-rules`
- 在 API v1 router 中挂载 admin/hr 角色依赖，员工角色默认无权访问

## Verification Results

- `python3 -m pytest backend/tests/test_fusion_rules_api.py -q`
- 通过，覆盖 admin/hr CRUD、employee forbidden、字段和 scope 校验

## Deviations from Plan

None - plan executed as intended.

## Commits

Deferred. Phase 19 在本轮中以内联执行完成，没有额外创建提交。

## Self-Check: PASSED

- `FusionRule` 模型、migration、service、router 均已落盘
- admin/hr 可访问，employee 被拒绝
- 规则范围和字段范围都有显式白名单保护
