import type { ReactNode } from "react";
import { Link } from "react-router-dom";

interface PageContainerProps {
  eyebrow?: string;
  title: string;
  description: string;
  actions?: ReactNode;
  children: ReactNode;
}

export function PageContainer({ eyebrow, title, description, actions, children }: PageContainerProps) {
  return (
    <section className="page-stack">
      <header className="page-hero">
        <div>
          {eyebrow ? <p className="page-eyebrow">{eyebrow}</p> : null}
          <h1>{title}</h1>
          <p>{description}</p>
        </div>
        {actions ? <div className="page-actions">{actions}</div> : null}
      </header>
      {children}
      <footer className="page-footer-note">
        <span>当前页面已经接入真实导入、解析、校验、匹配和导出链路；如果你要看批次级明细和人工修正，再进入高级页面。</span>
        <Link to="/imports">进入导入批次</Link>
      </footer>
    </section>
  );
}
