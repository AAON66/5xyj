import type { ThemeConfig } from 'antd';

export const theme: ThemeConfig = {
  token: {
    // Color
    colorPrimary: '#3370FF',
    colorBgContainer: '#FFFFFF',
    colorBgLayout: '#F5F6F7',
    colorBgElevated: '#FFFFFF',
    colorText: '#1F2329',
    colorTextSecondary: '#646A73',
    colorTextTertiary: '#8F959E',
    colorBorder: '#DEE0E3',
    colorBorderSecondary: '#E8E8E8',
    colorError: '#F54A45',
    colorWarning: '#FF7D00',
    colorSuccess: '#00B42A',
    colorInfo: '#3370FF',

    // Typography
    fontFamily: '"PingFang SC", "Microsoft YaHei", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    fontSize: 14,
    fontSizeHeading1: 24,
    fontSizeHeading2: 20,
    fontSizeHeading3: 16,
    fontSizeSM: 12,
    fontWeightStrong: 600,
    lineHeight: 1.5714,

    // Spacing & Shape
    borderRadius: 8,
    borderRadiusSM: 4,
    borderRadiusLG: 12,
    controlHeight: 32,
    controlHeightSM: 24,
    controlHeightLG: 40,
    padding: 16,
    paddingSM: 12,
    paddingXS: 8,
    margin: 16,
    marginSM: 12,
    marginXS: 8,

    // Motion
    motionDurationSlow: '0.3s',
    motionDurationMid: '0.2s',
    motionDurationFast: '0.1s',
    motionEaseInOut: 'cubic-bezier(0.645, 0.045, 0.355, 1)',
  },
  components: {
    Layout: {
      siderBg: '#1F2329',
      headerBg: '#FFFFFF',
      bodyBg: '#F5F6F7',
      headerHeight: 56,
      headerPadding: '0 24px',
    },
    Menu: {
      darkItemBg: '#1F2329',
      darkItemColor: 'rgba(255, 255, 255, 0.75)',
      darkItemHoverColor: '#FFFFFF',
      darkItemSelectedBg: 'rgba(51, 112, 255, 0.15)',
      darkItemSelectedColor: '#3370FF',
      itemHeight: 40,
      iconSize: 18,
      collapsedIconSize: 20,
    },
    Table: {
      headerBg: '#F5F6F7',
      headerColor: '#1F2329',
      rowHoverBg: '#F0F5FF',
      cellPaddingBlockSM: 8,
      cellPaddingInlineSM: 12,
    },
    Card: {
      paddingLG: 20,
      borderRadiusLG: 8,
    },
    Button: {
      primaryShadow: '0 2px 0 rgba(51, 112, 255, 0.1)',
      borderRadiusSM: 4,
    },
  },
};
