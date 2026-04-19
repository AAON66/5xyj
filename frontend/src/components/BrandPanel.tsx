import type { CSSProperties } from 'react';
import { Typography } from 'antd';

const { Text } = Typography;

/**
 * Props for {@link BrandPanel}.
 *
 * `isDark` selects the dark wordmark / slogan colour ramp. The caller
 * (Login.tsx) derives this from `useThemeMode().isDark` and passes it
 * down unchanged — this component does not subscribe to theme context
 * directly so it remains trivially testable in isolation.
 */
interface BrandPanelProps {
  isDark: boolean;
}

/**
 * Login page left-panel brand text overlay (Phase 23).
 *
 * Rendered as a decorative text layer sitting ABOVE the left-panel canvas
 * (ParticleWave or CssGradientBackground). The component owns only the
 * wordmark, slogan, sub-slogan and copyright copy — the background itself
 * is the parent's concern.
 *
 * Contract (23-UI-SPEC Brand Panel Content + Typography):
 * - 3 font sizes only: 20, 28, 14
 * - 2 font weights only: 400, 600
 * - pointerEvents: 'none' so ParticleWave mousemove events pass through
 * - zIndex: 2 to sit above the full-bleed canvas (canvas is zIndex 0/1)
 * - textShadow on light overlays to preserve ≥ 4.5:1 contrast against the
 *   light-mode particle gradient (WCAG 2.1 AA)
 * - No accent colours (accent is reserved for CTAs per UI-SPEC)
 * - No raw HTML injection API used — all copy via JSX text nodes and Typography (T-23-03 mitigation)
 */
export function BrandPanel({ isDark }: BrandPanelProps) {
  const wordmarkColor = isDark ? '#F0F5FF' : '#FFFFFF';
  const sloganColor = isDark ? '#E8F0FF' : '#FFFFFF';

  const rootStyle: CSSProperties = {
    position: 'absolute',
    inset: 0,
    padding: 48,
    pointerEvents: 'none',
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'space-between',
    zIndex: 2,
  };

  const wordmarkStyle: CSSProperties = {
    fontSize: 20,
    fontWeight: 600,
    lineHeight: 1.3,
    color: wordmarkColor,
    textShadow: '0 1px 2px rgba(0, 0, 0, 0.25)',
  };

  const centerBlockStyle: CSSProperties = {
    display: 'flex',
    flexDirection: 'column',
    gap: 16,
    maxWidth: 420,
  };

  const sloganStyle: CSSProperties = {
    fontSize: 28,
    fontWeight: 600,
    lineHeight: 1.25,
    color: sloganColor,
    margin: 0,
    textShadow: '0 2px 6px rgba(0, 0, 0, 0.25)',
  };

  const subSloganStyle: CSSProperties = {
    fontSize: 14,
    fontWeight: 400,
    lineHeight: 1.5714,
    color: 'rgba(255, 255, 255, 0.72)',
    margin: 0,
  };

  const copyrightStyle: CSSProperties = {
    fontSize: 14,
    fontWeight: 400,
    lineHeight: 1.5714,
    color: 'rgba(255, 255, 255, 0.5)',
  };

  return (
    <div
      style={rootStyle}
      data-testid="brand-panel"
      data-is-dark={isDark ? 'true' : 'false'}
    >
      <Text style={wordmarkStyle}>社保公积金管理系统</Text>
      <div style={centerBlockStyle}>
        <h1 style={sloganStyle}>多地区社保数据，一个系统统一汇聚</h1>
        <p style={subSloganStyle}>自动识别 · 智能映射 · 一键导出</p>
      </div>
      <Text style={copyrightStyle}>© 社保公积金管理系统</Text>
    </div>
  );
}
