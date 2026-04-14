import type { ReactNode } from 'react';
import { Button, Drawer, Space, Tag, theme } from 'antd';
import { CloseOutlined } from '@ant-design/icons';

import { useResponsiveViewport } from '../hooks/useResponsiveViewport';

interface ResponsiveFilterDrawerProps {
  title: string;
  open: boolean;
  onClose: () => void;
  onApply: () => void;
  onReset: () => void;
  activeCount: number;
  children: ReactNode;
  triggerLabel?: string;
}

export function ResponsiveFilterDrawer({
  title,
  open,
  onClose,
  onApply,
  onReset,
  activeCount,
  children,
}: ResponsiveFilterDrawerProps) {
  const { token } = theme.useToken();
  const { isMobile } = useResponsiveViewport();

  return (
    <Drawer
      placement="right"
      open={open}
      onClose={onClose}
      closable={false}
      width={isMobile ? '100vw' : 420}
      title={(
        <Space size={8}>
          <span>{title}</span>
          {activeCount > 0 ? <Tag color="blue">{activeCount}</Tag> : null}
        </Space>
      )}
      extra={(
        <Button
          type="text"
          icon={<CloseOutlined />}
          aria-label="关闭筛选抽屉"
          onClick={onClose}
        />
      )}
      footer={(
        <div
          style={{
            display: 'flex',
            gap: 12,
            padding: '12px 16px calc(12px + env(safe-area-inset-bottom))',
            background: token.colorBgContainer,
            borderTop: `1px solid ${token.colorBorderSecondary}`,
          }}
        >
          <Button style={{ flex: 1 }} onClick={onReset}>
            清空
          </Button>
          <Button style={{ flex: 1 }} type="primary" onClick={onApply}>
            应用筛选
          </Button>
        </div>
      )}
      styles={{
        body: { paddingBottom: 16 },
        footer: { padding: 0 },
      }}
    >
      {children}
    </Drawer>
  );
}
