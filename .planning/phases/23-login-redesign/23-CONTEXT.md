# Phase 23: 登录页面改版 - Context

**Gathered:** 2026-04-17
**Status:** Ready for planning

<domain>
## Phase Boundary

登录页升级为专业品牌形象：左右分栏布局（左侧品牌展示+Three.js 3D 粒子波浪动画，右侧登录表单），移动端只显示表单。支持 WebGL 降级和暗黑模式适配。

现有登录功能（账号密码登录、飞书 OAuth、员工查询入口、CandidateSelectModal）保持不变，只做视觉升级。

</domain>

<decisions>
## Implementation Decisions

### 粒子动画效果
- **D-01:** 海浪流动感风格 — 粒子排布成波浪形态，连续起伏流动，像海面一样柔和
- **D-02:** 粒子密度 2000-3000 个，在视觉效果和性能之间取平衡
- **D-03:** 鼠标交互采用柔和推波方式 — 鼠标移到哪里，波浪在那里轻柔隆起，离开后慢慢恢复
- **D-04:** 粒子颜色使用品牌主色系（#3370FF 渐变色谱），与系统整体视觉统一
- **D-05:** 粒子形状为圆形点，经典简约

### 暗黑模式适配
- **D-06:** 暗黑模式下粒子变亮色/发光效果 + 深色背景，形成"深海荧光"感
- **D-07:** 右侧表单卡片暗黑模式下使用半透明模糊效果（backdrop-filter blur），能透出背后粒子效果，增强科技融合感

### WebGL 降级策略
- **D-08:** 不支持 WebGL 时降级为 CSS 渐变背景 + 轻微 CSS animation 浮动效果，不完全静态
- **D-09:** 组件 mount 时即检测 WebGL 支持，尝试创建 WebGL context，失败则立即降级

### Claude's Discretion
- 左右分栏具体比例（建议 55:45 或 60:40）
- 移动端断点阈值
- 左侧品牌区域 logo/slogan 内容和排版
- 粒子波浪的具体参数（振幅、频率、速度）
- 降级动画的具体 CSS 实现
- Three.js lazy loading 策略

</decisions>

<canonical_refs>
## Canonical References

No external specs — requirements fully captured in decisions above and REQUIREMENTS.md (LOGIN-01 through LOGIN-04).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `frontend/src/pages/Login.tsx` — 当前登录页，包含密码登录、飞书 OAuth、CandidateSelectModal，需要重构布局但保留所有功能
- `frontend/src/theme/useThemeMode.ts` — 暗黑/亮色模式 hook，可用于切换粒子配色
- `frontend/src/theme/index.ts` — 主题配置，主色 #3370FF，暗黑模式算法已配置
- `frontend/src/hooks/useFeishuFeatureFlag.ts` — 飞书功能开关 hook

### Established Patterns
- Ant Design 组件库 + ConfigProvider 主题
- `isDark` 状态驱动暗黑模式切换
- `colors.BG_LAYOUT` 用于页面背景色

### Integration Points
- Three.js 需要作为新依赖引入（项目目前没有 Three.js）
- 粒子组件作为独立 React 组件，嵌入登录页左侧
- WebGL 检测逻辑封装为 hook 或工具函数

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 23-login-redesign*
*Context gathered: 2026-04-17*
