import { test, expect } from '@playwright/test';

// Keep these literals in sync with:
// - frontend/src/theme/ThemeModeProvider.tsx:14  (STORAGE_KEY = 'theme-mode')
// - frontend/tests/e2e/feishu-settings.spec.ts:5 (AUTH_SESSION_KEY = 'social-security-auth-session')
const THEME_STORAGE_KEY = 'theme-mode';
const AUTH_SESSION_KEY = 'social-security-auth-session';

test.describe('Login redesign', () => {
  // Dev server may reuse between suites; a stale auth session in localStorage
  // causes Login.tsx:118-120 to `<Navigate />` away before any DOM renders,
  // which makes every DOM assertion below time out. Clear it before page JS
  // runs by injecting an init script for every context.
  test.beforeEach(async ({ page }) => {
    await page.addInitScript((key) => {
      try {
        window.localStorage.removeItem(key);
      } catch {
        /* Safari private mode */
      }
    }, AUTH_SESSION_KEY);
  });

  test('layout — desktop split shows brand panel', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto('/login');
    // Brand panel only renders on desktop breakpoints (>=1024px, UI-SPEC Layout Contract).
    await expect(page.getByTestId('brand-panel')).toBeVisible();
    // Credential tab still reachable (preserved from current Login.tsx).
    await expect(page.getByRole('tab', { name: '账号登录' })).toBeVisible();
  });

  test('layout — mobile form-only hides brand panel', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto('/login');
    // Mobile (<768px): brand panel must not be rendered at all.
    await expect(page.getByTestId('brand-panel')).toHaveCount(0);
    // Form stays visible.
    await expect(page.getByRole('tab', { name: '账号登录' })).toBeVisible();
  });

  test('particle — canvas renders when webgl is available', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto('/login');
    // ParticleWave is lazy-loaded; allow up to 10s for the dynamic chunk.
    const canvas = page.getByTestId('particle-wave-canvas');
    await expect(canvas).toBeVisible({ timeout: 10_000 });
    const width = await canvas.evaluate((el) => (el as HTMLCanvasElement).clientWidth);
    expect(width).toBeGreaterThan(0);
  });

  test('webgl fallback — renders css gradient when getContext returns null', async ({ page }) => {
    // Stub `getContext` before the page's own scripts run so useWebGLSupport probe fails.
    await page.addInitScript(() => {
      const orig = HTMLCanvasElement.prototype.getContext;
      HTMLCanvasElement.prototype.getContext = function (type: string, ...rest: unknown[]) {
        if (type === 'webgl' || type === 'webgl2' || type === 'experimental-webgl') {
          return null;
        }
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        return (orig as any).apply(this, [type, ...rest]);
      } as typeof HTMLCanvasElement.prototype.getContext;
    });
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto('/login');
    await expect(page.getByTestId('css-gradient-background')).toBeVisible();
    await expect(page.getByTestId('particle-wave-canvas')).toHaveCount(0);
  });

  test('dark mode — glass card backdrop-filter and particle color swap', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    // Seed theme into localStorage before React boots. Key MUST match
    // ThemeModeProvider.tsx:14 STORAGE_KEY = 'theme-mode' (NOT any other prefix).
    await page.addInitScript((key) => {
      window.localStorage.setItem(key, 'dark');
    }, THEME_STORAGE_KEY);
    await page.goto('/login');
    const card = page.getByTestId('login-form-card');
    await expect(card).toBeVisible();
    const backdropFilter = await card.evaluate((el) => {
      const s = window.getComputedStyle(el);
      return s.backdropFilter || s.webkitBackdropFilter || '';
    });
    expect(backdropFilter).toMatch(/blur/);
    // ParticleWave (implemented in Plan 02) exposes `data-particle-color` with
    // the dark ramp's bright stop. Lowercase comparison to tolerate browser
    // serialization differences on attribute values.
    const particleColor = await page
      .getByTestId('particle-wave-canvas')
      .getAttribute('data-particle-color');
    expect(particleColor?.toLowerCase()).toContain('#7fa7ff');
  });
});
