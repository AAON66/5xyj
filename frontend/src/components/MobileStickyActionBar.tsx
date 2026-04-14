import type { ReactNode } from 'react';
import { Button, Typography, theme } from 'antd';

interface MobileStickyActionBarProps {
  visible: boolean;
  primaryLabel: string;
  onPrimaryClick: () => void;
  primaryDisabled?: boolean;
  primaryLoading?: boolean;
  helperText?: string | null;
  icon?: ReactNode;
}

export function MobileStickyActionBar({
  visible,
  primaryLabel,
  onPrimaryClick,
  primaryDisabled = false,
  primaryLoading = false,
  helperText = null,
  icon,
}: MobileStickyActionBarProps) {
  const { token } = theme.useToken();

  if (!visible) {
    return null;
  }

  return (
    <div
      style={{
        position: 'sticky',
        bottom: 0,
        zIndex: 20,
        marginTop: 16,
        padding: '12px 16px calc(12px + env(safe-area-inset-bottom))',
        background: token.colorBgContainer,
        borderTop: `1px solid ${token.colorBorderSecondary}`,
        boxShadow: token.boxShadowSecondary,
      }}
    >
      {helperText ? (
        <Typography.Text
          type="secondary"
          style={{ display: 'block', marginBottom: 8 }}
        >
          {helperText}
        </Typography.Text>
      ) : null}
      <Button
        block
        type="primary"
        icon={icon}
        loading={primaryLoading}
        disabled={primaryDisabled}
        onClick={onPrimaryClick}
      >
        {primaryLabel}
      </Button>
    </div>
  );
}
