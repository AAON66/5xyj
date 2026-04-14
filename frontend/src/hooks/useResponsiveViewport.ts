import { useEffect, useState } from 'react';

const MEDIA_QUERIES = {
  isMobile: '(max-width: 767px)',
  isTablet: '(min-width: 768px) and (max-width: 991px)',
  isCompactDesktop: '(min-width: 992px) and (max-width: 1440px)',
  isDesktopWide: '(min-width: 1441px)',
} as const;

type ResponsiveViewportState = Record<keyof typeof MEDIA_QUERIES, boolean>;

function readMatches(): ResponsiveViewportState {
  if (typeof window === 'undefined') {
    return {
      isMobile: false,
      isTablet: false,
      isCompactDesktop: false,
      isDesktopWide: true,
    };
  }

  return {
    isMobile: window.matchMedia(MEDIA_QUERIES.isMobile).matches,
    isTablet: window.matchMedia(MEDIA_QUERIES.isTablet).matches,
    isCompactDesktop: window.matchMedia(MEDIA_QUERIES.isCompactDesktop).matches,
    isDesktopWide: window.matchMedia(MEDIA_QUERIES.isDesktopWide).matches,
  };
}

function subscribe(mediaQuery: MediaQueryList, onChange: () => void) {
  if ('addEventListener' in mediaQuery) {
    mediaQuery.addEventListener('change', onChange);
    return () => mediaQuery.removeEventListener('change', onChange);
  }

  const legacyMediaQuery = mediaQuery as MediaQueryList & {
    addListener?: (listener: () => void) => void;
    removeListener?: (listener: () => void) => void;
  };

  legacyMediaQuery.addListener?.(onChange);
  return () => legacyMediaQuery.removeListener?.(onChange);
}

export function useResponsiveViewport() {
  const [viewport, setViewport] = useState<ResponsiveViewportState>(() => readMatches());

  useEffect(() => {
    if (typeof window === 'undefined') {
      return undefined;
    }

    const syncViewport = () => setViewport(readMatches());
    const mediaQueries = Object.values(MEDIA_QUERIES).map((query) => window.matchMedia(query));
    const cleanups = mediaQueries.map((mediaQuery) => subscribe(mediaQuery, syncViewport));

    syncViewport();

    return () => {
      cleanups.forEach((cleanup) => cleanup());
    };
  }, []);

  return viewport;
}
