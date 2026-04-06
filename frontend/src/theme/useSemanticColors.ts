import { theme } from 'antd';

export interface SemanticColors {
  BRAND: string;
  SUCCESS: string;
  ERROR: string;
  WARNING: string;
  TEXT: string;
  TEXT_TERTIARY: string;
  HIGHLIGHT_BG: string;
  HIGHLIGHT_BG_PRIMARY: string;
  HIGHLIGHT_BG_ERROR: string;
  BG_CONTAINER: string;
  BG_LAYOUT: string;
  BORDER: string;
  BORDER_SECONDARY: string;
  FILL_QUATERNARY: string;
}

export function useSemanticColors(): SemanticColors {
  const { token } = theme.useToken();
  return {
    BRAND: token.colorPrimary,
    SUCCESS: token.colorSuccess,
    ERROR: token.colorError,
    WARNING: token.colorWarning,
    TEXT: token.colorText,
    TEXT_TERTIARY: token.colorTextTertiary,
    HIGHLIGHT_BG: token.colorWarningBg,           // D-05
    HIGHLIGHT_BG_PRIMARY: token.colorPrimaryBg,
    HIGHLIGHT_BG_ERROR: token.colorErrorBg,
    BG_CONTAINER: token.colorBgContainer,
    BG_LAYOUT: token.colorBgLayout,
    BORDER: token.colorBorder,
    BORDER_SECONDARY: token.colorBorderSecondary,
    FILL_QUATERNARY: token.colorFillQuaternary,
  };
}
