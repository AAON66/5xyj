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
        <span>当前界面只承载基础链路，后续会逐步接入真实导入、解析、匹配与导出能力。</span>
        <Link to="/imports">进入导入批次</Link>
      </footer>
    </section>
  );
}
