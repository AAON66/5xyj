import { theme } from 'antd';

export interface CardStatusColors {
  successBorder: string;
  errorBorder: string;
  warningBorder: string;
  primaryBorder: string;
}

export function useCardStatusColors(): CardStatusColors {
  const { token } = theme.useToken();
  return {
    successBorder: token.colorSuccess,
    errorBorder: token.colorError,
    warningBorder: token.colorWarning,
    primaryBorder: token.colorPrimary,
  };
}
