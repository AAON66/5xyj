import { useEffect, useState } from 'react';

/**
 * WebGL capability states exposed by {@link useWebGLSupport}.
 *
 * - `'loading'`: SSR-safe initial value. Returned synchronously on first render
 *   so that client markup matches server markup; no decision has been made yet.
 * - `'webgl'`: A probe WebGL / WebGL2 / experimental-webgl context was
 *   successfully created. The probe is released immediately (see note below).
 * - `'fallback'`: No WebGL context could be created, or probe creation threw.
 *   Callers should render a CSS-only fallback (e.g. `CssGradientBackground`).
 */
export type WebGLSupport = 'loading' | 'webgl' | 'fallback';

/**
 * Detects WebGL support at mount time (per Phase 23 D-09).
 *
 * Implementation notes:
 * - Initial state is `'loading'` (NOT `'fallback'`) to stay SSR-safe and avoid
 *   a flash of the fallback UI before the check resolves on the client.
 * - After probing, the probe context is released synchronously via the
 *   `WEBGL_lose_context.loseContext()` extension. iOS Safari caps the active
 *   WebGLRenderingContext pool around 8, so leaving a probe context attached
 *   would steal a slot from `ParticleWave` (Pitfall 1 in 23-RESEARCH).
 * - `experimental-webgl` is tried last as a long-tail fallback for legacy
 *   Firefox / IE11 behaviour.
 * - Any exception (OOM, security, policy) collapses to `'fallback'` — the
 *   caller must never see the error.
 */
export function useWebGLSupport(): WebGLSupport {
  const [support, setSupport] = useState<WebGLSupport>('loading');

  useEffect(() => {
    if (typeof window === 'undefined') {
      setSupport('fallback');
      return;
    }
    try {
      const canvas = document.createElement('canvas');
      const gl =
        (canvas.getContext('webgl2') as WebGLRenderingContext | null) ??
        (canvas.getContext('webgl') as WebGLRenderingContext | null) ??
        (canvas.getContext('experimental-webgl') as WebGLRenderingContext | null);
      if (!gl) {
        setSupport('fallback');
        return;
      }
      // Release probe context immediately so ParticleWave can claim its own slot.
      const loseExt = gl.getExtension('WEBGL_lose_context');
      loseExt?.loseContext();
      setSupport('webgl');
    } catch {
      setSupport('fallback');
    }
  }, []);

  return support;
}
