# Technology Stack

**Project:** v1.2 飞书深度集成与登录体验升级
**Researched:** 2026-04-14

## Scope

本次研究只覆盖 v1.2 里 **新增能力** 所需的技术选型。已验证的基础栈（FastAPI、React 18、Ant Design 5、SQLAlchemy、httpx、PyJWT 等）不在讨论范围。

---

## Executive Summary

v1.2 需要 **4 个新 npm 包**（Three.js 生态）和 **1 个 CDN 加载的飞书 SDK**，后端零新依赖。Three.js 用于登录页 3D 粒子波浪动画，通过 `@react-three/fiber` v8（React 18 对应版本）集成。飞书扫码用官方 QRLogin SDK（CDN 加载，非 npm 包）。飞书字段拉取和 OAuth 流程已有完整实现，只需增强 UI 和用户匹配逻辑，不需要新库。

---

## Recommended Stack Additions

### Frontend -- Three.js 3D 粒子波浪

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `three` | ~0.172.0 | WebGL 3D 渲染引擎 | 粒子波浪动画需要 WebGL；three.js 周下载量 270 万，生态最成熟。锁定 0.172 而非最新 0.183 是因为 R3F v8 的 peerDep 兼容范围在此附近，避免类型不兼容 |
| `@react-three/fiber` | ^8.17.10 | React 18 的 Three.js 渲染器 | **v8 = React 18，v9 = React 19**。当前项目用 React 18，必须用 v8。声明式组件模型 + `useFrame` 渲染循环，比直接操作 Three.js 更符合 React 范式 |
| `@react-three/drei` | ^9.121.0 | R3F 常用 helper 集合 | 提供 `<Points>` + `<PointMaterial>` 开箱即用组件，粒子波浪可直接用而不需手写 BufferGeometry 管理 |
| `@types/three` | ~0.172.0 | TypeScript 类型定义 | 项目用 TS 5.8，必须有类型。版本需与 three 主包对齐 |

**版本锁定说明：** R3F v8.17.10 是 v8 线的最新版本。three.js 版本建议锁定在 R3F v8 兼容范围内（0.160-0.172），安装时用 `npm install three@~0.172.0` 确保兼容性。

**不推荐裸写 Three.js 的原因：** 登录页面本身就是 React 组件树的一部分，裸写 Three.js 需要手动管理 canvas 生命周期、resize、dispose。R3F 把这些全部声明式化了，且不引入额外渲染开销（组件在 React 渲染管线之外渲染）。

### Frontend -- 飞书扫码登录 SDK

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| 飞书 QRLogin JS SDK | 1.0.3 | 在登录页内嵌飞书扫码二维码 | 官方 CDN 加载，无需 npm 安装。SDK 处理了跨域通信、二维码刷新等细节。CDN 地址：`https://lf-package-cn.feishucdn.com/obj/feishu-static/lark/passport/qrcode/LarkSSOSDKWebQRCode-1.0.3.js` |

**加载方式：** 不要把 SDK 装成 npm 包（没有官方 npm 包）。在 React 中通过 `useEffect` 动态插入 `<script>` 标签加载 CDN 资源，加载完成后调用全局 `QRLogin()` 函数。需要为 TypeScript 声明 `window.QRLogin` 的类型。

### Backend -- 无新依赖

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| _(无新增)_ | -- | -- | 飞书 Bitable field listing API 已在 `FeishuClient.list_fields()` 中实现；OAuth token exchange 已在 `feishu_oauth_service.py` 中实现；httpx 已能满足所有 HTTP 调用需求 |

---

## Existing Code That Covers New Features

这些能力已经存在于代码库中，v1.2 只需增强而非从零构建：

### 飞书 Bitable 字段拉取

- **已有：** `FeishuClient.list_fields(app_token, table_id)` -- 分页拉取多维表格全部字段定义（field_id, field_name, field_type, description），支持 page_token 分页
- **已有：** 前端 `fetchFeishuFields(configId)` API 调用
- **已有：** `SyncConfig.field_mapping: Record<string, string>` 数据模型
- **需增强：** 字段类型映射 UI（把拉取到的飞书字段与系统 canonical fields 做一一对应配置），用 Ant Design 的 `<Select>` + `<Table>` 即可

### 飞书 OAuth 登录

- **已有：** 后端 `/auth/feishu/authorize-url` + `/auth/feishu/callback` 完整流程
- **已有：** `exchange_code_for_user()` -- code 换 token 换用户信息 + 自动创建用户 + 签发 JWT
- **已有：** CSRF state cookie 验证、feature flag 开关
- **已有：** 前端 `fetchFeishuAuthorizeUrl()` + `feishuOAuthCallback()` + Login.tsx 中的飞书登录按钮
- **需增强：** (1) 内嵌二维码扫码（替代跳转式授权，需 QRLogin SDK）(2) 用户自动匹配逻辑改进（按姓名/工号绑定已有用户而非每次创建新用户）
- **建议升级（非阻塞）：** 当前用 v1 endpoint `/authen/v1/access_token`，v2 endpoint `/authen/v2/oauth/token` 参数名从 `app_id/app_secret` 改为 `client_id/client_secret`，响应格式更标准

---

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| 3D 渲染 | `three` + R3F | 裸写 Three.js canvas | 需手动管理 canvas 生命周期/resize/dispose，与 React 组件树脱节 |
| 3D 渲染 | `three` + R3F | `Babylon.js` | Three.js 下载量是 Babylon 的 270 倍，粒子波浪是经典 Three.js 示例 |
| 3D 渲染 | `three` + R3F | 纯 CSS/Canvas 2D 动画 | 需求明确要求 Three.js 3D 粒子波浪，CSS 无法实现真 3D 效果 |
| 粒子系统 | `<Points>` + `useFrame` | `three-nebula` / `three.quarks` | 粒子波浪是简单正弦函数动画（2500-5000 个点），不需要完整粒子引擎 |
| 飞书扫码 | 官方 QRLogin SDK (CDN) | 自行实现 iframe 嵌入 | SDK 处理了跨域通信、安全验证、二维码刷新等细节 |
| 飞书扫码 | CDN 动态加载 | npm 包 | 飞书没有发布官方 npm 包，CDN 是唯一官方渠道 |
| OAuth 版本 | 保持 v1（可选升级 v2） | 强制升级 v2 | v1 仍然可用且已经过验证；v2 非紧急 |

---

## What NOT to Add

| Library | Why Not |
|---------|---------|
| `@react-three/postprocessing` | 登录页只需简单粒子动画，不需要 bloom/SSAO 等后处理效果 |
| `@react-three/cannon` / `@react-three/rapier` | 不需要物理引擎 |
| `leva` / `dat.gui` | 开发调试工具，生产环境不需要 |
| `gsap` / `framer-motion-3d` | 粒子波浪用 `useFrame` 即可驱动，不需要额外动画库 |
| `feishu-node-sdk` | Python 后端不适用；且已有自研 `FeishuClient` 类 |
| 任何状态管理库（zustand/jotai） | 粒子动画状态完全在 R3F 组件内部，不需要全局状态 |
| `react-qr-code` | 二维码由飞书 SDK 生成和管理，不需要自行渲染 |

---

## Installation

```bash
# Frontend -- Three.js 生态（4 个包）
cd frontend
npm install three@~0.172.0 @react-three/fiber@^8.17.10 @react-three/drei@^9.121.0
npm install -D @types/three@~0.172.0

# Backend -- 无新依赖
# requirements.txt 不需要修改
```

### 飞书 QRLogin SDK 加载（前端代码层面）

```typescript
// utils/loadFeishuQRSDK.ts
const FEISHU_QR_SDK_URL =
  'https://lf-package-cn.feishucdn.com/obj/feishu-static/lark/passport/qrcode/LarkSSOSDKWebQRCode-1.0.3.js';

export function loadFeishuQRSDK(): Promise<void> {
  return new Promise((resolve, reject) => {
    if ((window as any).QRLogin) {
      resolve();
      return;
    }
    const script = document.createElement('script');
    script.src = FEISHU_QR_SDK_URL;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error('Failed to load Feishu QR SDK'));
    document.head.appendChild(script);
  });
}
```

```typescript
// types/feishu-qr.d.ts
interface QRLoginInstance {
  matchOrigin(origin: string): boolean;
}
interface QRLoginOptions {
  id: string;       // 容器 DOM id
  goto: string;     // 飞书授权 URL
  width?: number;
  height?: number;
  style?: string;   // CSS style string for iframe
}
declare function QRLogin(options: QRLoginOptions): QRLoginInstance;
```

---

## Bundle Size Impact

| Package | Estimated Size (gzipped) | Notes |
|---------|--------------------------|-------|
| `three` | ~150 KB | 核心库，Vite tree-shaking 可削减部分 |
| `@react-three/fiber` | ~40 KB | React 渲染器 |
| `@react-three/drei` | ~20 KB (tree-shakeable) | 只导入 `Points` + `PointMaterial` 时实际贡献很小 |
| 飞书 QR SDK | ~15 KB | CDN 加载，不进入 bundle |
| **Total** | ~210 KB | 仅影响登录页 |

**优化建议：** 登录页组件用 `React.lazy()` + `Suspense` 懒加载。Three.js 相关代码只在登录页路由加载时才下载，其他页面完全不受影响。Vite 6.2 会自动做路由级代码拆分。

---

## Integration Points

### Three.js 粒子波浪与登录页面

- 登录页改为左右分栏布局：左侧 R3F `<Canvas>` 渲染 3D 粒子波浪，右侧保持现有登录表单
- 粒子波浪用 `useFrame` 驱动正弦函数更新 BufferGeometry positions（每帧更新 Y 坐标 = sin(X + time) * cos(Z + time)）
- 暗黑模式兼容：粒子颜色和 Canvas 背景色从 `useSemanticColors()` 获取，跟随主题自动切换
- 响应式：移动端（< md 断点）隐藏左侧 3D 区域，只显示登录表单（用 `Grid.useBreakpoint()`）
- 性能防护：粒子数量控制在 2500-5000，保证低端设备也能 60fps

### 飞书扫码与现有 OAuth 流程

扫码登录流程（与现有跳转式并行提供）：

1. 前端动态加载 QRLogin SDK
2. 构造 goto URL：`https://passport.feishu.cn/suite/passport/oauth/authorize?client_id={APP_ID}&redirect_uri={REDIRECT_URI}&response_type=code&state={STATE}`
3. SDK 在指定 DOM 容器渲染飞书扫码二维码
4. 用户手机扫码后 SDK 通过 `postMessage` 返回 `tmp_code`
5. 前端拼接 `goto + &tmp_code={tmp_code}` 跳转
6. 飞书回调到 redirect_uri 带回 `code` + `state`
7. 复用现有 `feishuOAuthCallback(code, state)` 完成登录

**关键：** 步骤 6-7 完全复用现有后端 `/auth/feishu/callback` 逻辑。

### 飞书用户自动匹配增强

当前 `exchange_code_for_user()` 只按 `feishu_open_id` 查找用户，找不到就创建新用户。v1.2 需增强匹配策略：

1. 按 `feishu_open_id` 精确匹配（已有）
2. 按飞书返回的 `name` 匹配系统中 `display_name` 相同的用户
3. 按飞书返回的 `employee_id`（如果有）匹配系统员工主数据
4. 匹配成功则绑定 `feishu_open_id` 到已有用户，而非创建新用户
5. 无法匹配时仍创建新 employee 用户（保持现有兜底逻辑）

**不需要新依赖**，纯业务逻辑修改。

### 飞书字段映射 UI

- 前端已有 `fetchFeishuFields(configId)` 和 `saveSyncConfigMapping(id, fieldMapping)`
- 需要新增映射 UI 组件：左边显示飞书字段列表（field_name + field_type），右边显示系统 canonical fields，用 `<Select>` 做一一对应
- 数据模型已有 `SyncConfig.field_mapping: Record<string, string>`，持久化链路完整
- 用 Ant Design `<Table>` + `<Select>` 即可，不需要拖拽库

---

## Confidence Assessment

| Area | Confidence | Reason |
|------|------------|--------|
| Three.js + R3F 版本选择 | HIGH | npm 官方确认 R3F v8 对应 React 18，版本对齐关系明确 |
| drei Points/PointMaterial | HIGH | drei 核心组件，大量示例和文档验证 |
| 飞书 QRLogin SDK | MEDIUM | SDK 版本 1.0.3 从多个教程确认可用，但需实际测试 CDN 在目标部署环境下的可达性 |
| 飞书 OAuth v1 可用性 | HIGH | 代码已在生产验证，v1 未被标记为 deprecated |
| 飞书 Bitable list_fields | HIGH | 已有代码且已在生产使用 |
| 无需新后端依赖 | HIGH | 所有后端能力已由 httpx + 现有 FeishuClient 覆盖 |
| Bundle size 控制 | MEDIUM | 理论上 React.lazy 可隔离 Three.js 到登录页，但需实际验证 Vite 分包策略 |

---

## Sources

- [React Three Fiber Official Docs](https://r3f.docs.pmnd.rs/getting-started/introduction) -- v8 = React 18, v9 = React 19
- [React Three Fiber GitHub](https://github.com/pmndrs/react-three-fiber)
- [@react-three/fiber npm](https://www.npmjs.com/package/@react-three/fiber) -- v8.17.10 (React 18) / v9.5.0 (React 19)
- [three.js npm](https://www.npmjs.com/package/three) -- latest 0.183.2
- [Three.js Official Particle Waves Example](https://threejs.org/examples/webgl_points_waves.html)
- [飞书开放平台 -- Bitable List Fields API](https://open.feishu.cn/document/server-docs/docs/bitable-v1/app-table-field/list)
- [飞书开放平台 -- OAuth v2 user_access_token](https://open.feishu.cn/document/authentication-management/access-token/get-user-access-token)
- [飞书开放平台 -- 扫码登录教程](https://open.larkoffice.com/document/qr-code-scanning-login-for-web-app/introduction)
- [掘金：飞书扫码登录全流程](https://juejin.cn/post/7501203502665891866)
- [CSDN：飞书扫码登录对接流程](https://blog.csdn.net/caidingnu/article/details/151404436)
- [Medium: Integrating Three.js with React Performance Guide](https://medium.com/@alfinohatta/integrating-three-js-278774d45973)
