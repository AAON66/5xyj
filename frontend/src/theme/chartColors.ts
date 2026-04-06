export interface ChartColors {
  brand: string;
  success: string;
  error: string;
  warning: string;
  textTertiary: string;
  highlightBg: string;
}

export const LIGHT_CHART_COLORS: ChartColors = {
  brand: '#3370FF',
  success: '#00B42A',
  error: '#F54A45',
  warning: '#FF7D00',
  textTertiary: '#8F959E',
  highlightBg: '#FFF7E6',
};

// NOTE: 暗模色值为 AntD darkAlgorithm 推导近似值。
// 实现后建议在 DevTools 中用 useToken() 校准实际值并更新此处。
// 若需精确值，可在组件内 useMemo 中用 useToken 替代此常量。
export const DARK_CHART_COLORS: ChartColors = {
  brand: '#3C89E8',
  success: '#49AA19',
  error: '#DC4446',
  warning: '#D89614',
  textTertiary: '#7D8390',
  highlightBg: '#2B2111',
};

export function getChartColors(isDark: boolean): ChartColors {
  return isDark ? DARK_CHART_COLORS : LIGHT_CHART_COLORS;
}
