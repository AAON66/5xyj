import { useEffect, useRef } from 'react';
import {
  AdditiveBlending,
  BufferGeometry,
  Color,
  Float32BufferAttribute,
  PerspectiveCamera,
  Points,
  Scene,
  ShaderMaterial,
  Vector2,
  WebGLRenderer,
} from 'three';

/**
 * Props for {@link ParticleWave}.
 *
 * `isDark` flips the locked UI-SPEC colour ramp between the daytime brand
 * gradient and the dark-mode "deep-sea luminescence" palette (D-06).
 */
export interface ParticleWaveProps {
  isDark: boolean;
}

// Grid layout — 80 × 32 = 2560 particles (D-02 locks the 2000-3000 band;
// UI-SPEC 3D Canvas Contract fixes the exact value at 2560).
const GRID_X = 80;
const GRID_Y = 32;
const SPACING = 0.4;

// Derived world-space half-extents (used to project NDC mouse coords onto
// the particle plane at z = 0).
const PLANE_HALF_WIDTH = (GRID_X * SPACING) / 2; // 16
const PLANE_HALF_HEIGHT = (GRID_Y * SPACING) / 2; // 6.4

// UI-SPEC locked palette (D-04, D-06). DO NOT mutate these hex literals —
// the design system and Plan 03 Playwright assertions depend on them.
const COLORS_LIGHT = {
  bright: '#E8F0FF',
  mid: '#3370FF',
  deep: '#1D4AC7',
};
const COLORS_DARK = {
  bright: '#7FA7FF',
  mid: '#3370FF',
  deep: '#1B2B4D',
};

// Mouse bulge smoothing. A per-frame lerp factor of 0.05 yields a time
// constant of roughly 800ms at 60 fps (1 - (1 - 0.05)^(60 * 0.8) ≈ 0.95),
// matching D-03 "离开后 ~0.8s 平滑回落".
const MOUSE_LERP = 0.05;

/**
 * Three.js GPU particle wave — Phase 23 login page left-panel hero visual.
 *
 * Implementation highlights (see 23-RESEARCH.md Pattern 1 and Pitfalls 1/4/5/6):
 *
 * 1. **All wave math lives in the vertex shader.** Per frame the CPU only
 *    advances `uTime`, `uMouse`, `uMouseStrength`; the GPU displaces all 2560
 *    vertices in parallel. Updating JS positions each frame would burn ~150k
 *    ops/sec and starve the React main thread.
 *
 * 2. **Strict Mode–safe cleanup.** React 18 Strict Mode mount/unmount/mount
 *    pattern is guarded by disposing `geometry`, `material`, `renderer`, then
 *    calling `renderer.forceContextLoss()` and detaching the canvas from DOM.
 *    Skipping any of these leaks a WebGL slot (Safari caps at 16, iOS at 8).
 *
 * 3. **`webglcontextlost` fallback.** The handler calls `event.preventDefault()`
 *    (MDN requirement) and cancels RAF — Plan 03 restarts the pipeline by
 *    forcing a React remount.
 *
 * 4. **Reduced motion honoured.** When `(prefers-reduced-motion: reduce)` is
 *    set, RAF never starts, mouse handlers never attach, and the frozen
 *    particle plane renders once.
 *
 * 5. **Background tab safety.** `document.hidden` skips the render and resets
 *    `lastTime` so `uTime` cannot advance while the tab is occluded (Pitfall 6).
 *    The per-frame delta is also clamped to 0.1s to guard against laptop
 *    lid-close bursts.
 *
 * 6. **Deterministic data attributes.** The `<canvas>` exposes
 *    `data-testid="particle-wave-canvas"` and `data-particle-color="<hex>"`
 *    (lowercased) so the Plan 01 Playwright E2E scaffold can assert palette
 *    switches without reading WebGL pixels.
 */
export default function ParticleWave({ isDark }: ParticleWaveProps) {
  const mountRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const mount = mountRef.current;
    if (!mount) return;

    const reducedMotion =
      typeof window !== 'undefined' &&
      typeof window.matchMedia === 'function' &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const palette = isDark ? COLORS_DARK : COLORS_LIGHT;

    // === 1. Scene / Camera / Renderer ===
    const scene = new Scene();
    const width = mount.clientWidth;
    const height = Math.max(mount.clientHeight, 1);
    const camera = new PerspectiveCamera(55, width / height, 0.1, 100);
    camera.position.set(0, -14, 12);
    camera.lookAt(0, 0, 0);

    const renderer = new WebGLRenderer({ antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(2, window.devicePixelRatio));
    renderer.setSize(width, height);

    const canvas = renderer.domElement;
    canvas.setAttribute('data-testid', 'particle-wave-canvas');
    canvas.setAttribute('data-particle-color', palette.bright.toLowerCase());
    canvas.setAttribute('aria-hidden', 'true');
    canvas.setAttribute('role', 'presentation');
    canvas.style.display = 'block';
    canvas.style.width = '100%';
    canvas.style.height = '100%';
    canvasRef.current = canvas;
    mount.appendChild(canvas);

    // === 2. Geometry: 80 × 32 = 2560 particles on a flat grid ===
    const geometry = new BufferGeometry();
    const count = GRID_X * GRID_Y;
    const positions = new Float32Array(count * 3);
    let i = 0;
    for (let x = 0; x < GRID_X; x++) {
      for (let y = 0; y < GRID_Y; y++, i++) {
        positions[i * 3 + 0] = (x - GRID_X / 2) * SPACING;
        positions[i * 3 + 1] = (y - GRID_Y / 2) * SPACING;
        positions[i * 3 + 2] = 0;
      }
    }
    geometry.setAttribute('position', new Float32BufferAttribute(positions, 3));

    // === 3. ShaderMaterial — wave math + gaussian bulge + circle sprite ===
    const material = new ShaderMaterial({
      uniforms: {
        uTime: { value: 0 },
        uMouse: { value: new Vector2(0, 0) },
        uMouseStrength: { value: 0 },
        uColorBright: { value: new Color(palette.bright) },
        uColorMid: { value: new Color(palette.mid) },
        uColorDeep: { value: new Color(palette.deep) },
      },
      vertexShader: `
        uniform float uTime;
        uniform vec2  uMouse;
        uniform float uMouseStrength;
        varying float vHeight;
        void main() {
          vec3 p = position;
          // Dual-sine wave (D-01, UI-SPEC 3D Canvas Contract)
          //   freq_x = 0.35, speed_x = 0.60, amp_x = 0.6
          //   freq_y = 0.25, speed_y = 0.42, amp_y = 0.4
          float wave = sin(p.x * 0.35 + uTime * 0.60) * 0.6
                     + sin(p.y * 0.25 + uTime * 0.42) * 0.4;
          // Gaussian bulge around the mouse (D-03)
          //   sigma = 3.5, amplitude = 1.2
          float d = distance(p.xy, uMouse);
          float bulge = exp(-(d * d) / (2.0 * 3.5 * 3.5)) * 1.2 * uMouseStrength;
          p.z = wave + bulge;
          vHeight = p.z;
          vec4 mvPosition = modelViewMatrix * vec4(p, 1.0);
          gl_Position = projectionMatrix * mvPosition;
          gl_PointSize = (2.0 + bulge) * (300.0 / max(-mvPosition.z, 0.001));
        }
      `,
      fragmentShader: `
        uniform vec3 uColorBright;
        uniform vec3 uColorMid;
        uniform vec3 uColorDeep;
        varying float vHeight;
        void main() {
          // Circular sprite (D-05) — no external texture needed.
          vec2 uv = gl_PointCoord - 0.5;
          float circle = smoothstep(0.5, 0.4, length(uv));
          if (circle <= 0.0) discard;
          // Three-stop lerp along Z height (D-04, D-06).
          vec3 color = vHeight > 0.0
            ? mix(uColorMid, uColorBright, clamp(vHeight, 0.0, 1.0))
            : mix(uColorDeep, uColorMid, clamp(vHeight + 1.0, 0.0, 1.0));
          gl_FragColor = vec4(color, circle);
        }
      `,
      transparent: true,
      depthWrite: false,
      blending: AdditiveBlending,
    });

    const points = new Points(geometry, material);
    scene.add(points);

    // === 4. Animation loop + reduced-motion / visibility branches ===
    let rafId = 0;
    let mouseTargetStrength = 0;
    let lastTime = performance.now();

    const renderStatic = () => renderer.render(scene, camera);

    const animate = () => {
      // Background-tab guard (Pitfall 6): skip the render, reset the clock
      // so uTime cannot accumulate while the tab is hidden.
      if (document.hidden) {
        rafId = requestAnimationFrame(animate);
        lastTime = performance.now();
        return;
      }
      rafId = requestAnimationFrame(animate);
      const now = performance.now();
      // Clamp the delta to 0.1s to absorb lid-close / throttling spikes.
      const delta = Math.min((now - lastTime) / 1000, 0.1);
      lastTime = now;
      material.uniforms.uTime.value += delta;
      material.uniforms.uMouseStrength.value +=
        (mouseTargetStrength - material.uniforms.uMouseStrength.value) * MOUSE_LERP;
      renderer.render(scene, camera);
    };

    if (reducedMotion) {
      // prefers-reduced-motion: reduce — render a single static frame, no RAF,
      // no mouse interaction (WCAG 2.3.3 compliance, Pitfall 5).
      renderStatic();
    } else {
      rafId = requestAnimationFrame(animate);
    }

    // === 5. Event listeners ===
    const onMove = (e: MouseEvent) => {
      if (reducedMotion) return;
      const rect = mount.getBoundingClientRect();
      if (rect.width === 0 || rect.height === 0) return;
      const ndcX = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      const ndcY = -(((e.clientY - rect.top) / rect.height) * 2 - 1);
      material.uniforms.uMouse.value.set(
        ndcX * PLANE_HALF_WIDTH,
        ndcY * PLANE_HALF_HEIGHT,
      );
      mouseTargetStrength = 1.0;
    };
    const onLeave = () => {
      mouseTargetStrength = 0;
    };
    const onResize = () => {
      const w = mount.clientWidth;
      const h = Math.max(mount.clientHeight, 1);
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
      if (reducedMotion) renderStatic();
    };
    const onContextLost = (event: Event) => {
      // MDN: preventDefault() is required for the browser to attempt restore.
      event.preventDefault();
      cancelAnimationFrame(rafId);
    };

    if (!reducedMotion) {
      mount.addEventListener('mousemove', onMove);
      mount.addEventListener('mouseleave', onLeave);
    }
    window.addEventListener('resize', onResize);
    canvas.addEventListener('webglcontextlost', onContextLost);

    // === 6. Cleanup — Strict Mode safe, idempotent ===
    return () => {
      cancelAnimationFrame(rafId);
      if (!reducedMotion) {
        mount.removeEventListener('mousemove', onMove);
        mount.removeEventListener('mouseleave', onLeave);
      }
      window.removeEventListener('resize', onResize);
      canvas.removeEventListener('webglcontextlost', onContextLost);
      geometry.dispose();
      material.dispose();
      renderer.dispose();
      renderer.forceContextLoss();
      if (canvas.parentNode === mount) {
        mount.removeChild(canvas);
      }
      canvasRef.current = null;
    };
  }, [isDark]);

  return (
    <div
      ref={mountRef}
      data-testid="particle-wave-mount"
      style={{
        position: 'absolute',
        inset: 0,
        width: '100%',
        height: '100%',
      }}
      aria-hidden="true"
    />
  );
}
