import type { CSSProperties } from 'react';

/**
 * Props for {@link CssGradientBackground}.
 *
 * `isDark` selects the dark colour ramp; the caller (Login.tsx) derives this
 * from {@link ThemeModeContext.isDark} and passes it down unchanged.
 */
export interface CssGradientBackgroundProps {
  isDark: boolean;
}

/**
 * WebGL fallback background for the login page left panel (Phase 23 D-08).
 *
 * Renders a 135° linear gradient in the Phase 23 brand ramp with a 20s gentle
 * drift animation, honouring `prefers-reduced-motion`. All colour literals are
 * sourced verbatim from 23-UI-SPEC "WebGL Fallback Color" to keep the visual
 * contract auditable.
 *
 * The component is rendered as a pure decorative layer (`aria-hidden="true"`,
 * `role="presentation"`) because it conveys no information to assistive tech.
 * The keyframes are injected via a colocated `<style>` element rather than a
 * global CSS file to keep the contract self-contained; this is a plain JSX
 * form, no raw HTML injection API is used (see security audit T-23-03).
 */
export function CssGradientBackground({ isDark }: CssGradientBackgroundProps) {
  const style: CSSProperties = {
    position: 'absolute',
    inset: 0,
    width: '100%',
    height: '100%',
    backgroundImage: isDark
      ? 'linear-gradient(135deg, #1B2B4D 0%, #3370FF 60%, #7FA7FF 100%)'
      : 'linear-gradient(135deg, #E8F0FF 0%, #3370FF 60%, #1D4AC7 100%)',
    backgroundSize: '200% 200%',
    animation: 'cssGradientDrift 20s ease-in-out infinite',
  };
  return (
    <>
      <div
        style={style}
        aria-hidden="true"
        role="presentation"
        data-testid="css-gradient-background"
        data-is-dark={isDark ? 'true' : 'false'}
      />
      <style>{`
        @keyframes cssGradientDrift {
          0%   { background-position: 0% 50%; }
          50%  { background-position: 100% 50%; }
          100% { background-position: 0% 50%; }
        }
        @media (prefers-reduced-motion: reduce) {
          [data-testid="css-gradient-background"] { animation: none !important; }
        }
      `}</style>
    </>
  );
}
