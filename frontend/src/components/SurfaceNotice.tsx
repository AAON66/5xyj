import type { ReactNode } from 'react';

interface SurfaceNoticeProps {
  tone?: 'info' | 'success' | 'warning' | 'error';
  title?: string;
  message: string;
  action?: ReactNode;
}

export function SurfaceNotice({ tone = 'info', title, message, action }: SurfaceNoticeProps) {
  return (
    <div className={`surface-notice surface-notice--${tone}`} role={tone === 'error' ? 'alert' : 'status'}>
      <div>
        {title ? <strong>{title}</strong> : null}
        <span>{message}</span>
      </div>
      {action ? <div>{action}</div> : null}
    </div>
  );
}
