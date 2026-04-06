// Static fallback constants (use useSemanticColors hook for runtime dynamic values)
export const LIGHT_SEMANTIC_COLORS = {
  BRAND: '#3370FF',
  SUCCESS: '#00B42A',
  ERROR: '#F54A45',
  WARNING: '#FF7D00',
  TEXT: '#1F2329',
  TEXT_TERTIARY: '#8F959E',
  HIGHLIGHT_BG: '#FFF7E6',
  HIGHLIGHT_BG_PRIMARY: '#F0F5FF',
  HIGHLIGHT_BG_ERROR: '#FFF1F0',
  BG_CONTAINER: '#FFFFFF',
  BG_LAYOUT: '#F5F6F7',
  BORDER: '#DEE0E3',
  BORDER_SECONDARY: '#E8E8E8',
  FILL_QUATERNARY: '#F5F5F5',
} as const;

export type SemanticColorKey = keyof typeof LIGHT_SEMANTIC_COLORS;
