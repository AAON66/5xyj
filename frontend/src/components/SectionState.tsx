interface SectionStateProps {
  tone?: 'info' | 'warning' | 'error';
  title: string;
  message: string;
}

export function SectionState({ tone = 'info', title, message }: SectionStateProps) {
  return (
    <div className={`section-state section-state--${tone}`} role={tone === 'error' ? 'alert' : 'status'}>
      <strong>{title}</strong>
      <span>{message}</span>
    </div>
  );
}
