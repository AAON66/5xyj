import { Link } from 'react-router-dom';

type WorkspaceRole = 'admin' | 'hr';

interface WorkspaceLink {
  to: string;
  title: string;
  hint: string;
}

const WORKSPACE_CONFIG: Record<
  WorkspaceRole,
  {
    kicker: string;
    title: string;
    description: string;
    primaryAction: WorkspaceLink;
    secondaryAction: WorkspaceLink;
    sections: Array<{ title: string; links: WorkspaceLink[] }>;
  }
> = {
  admin: {
    kicker: 'Administrator Desk',
    title: '管理员工作台',
    description: '管理员负责总览、治理和配置。这里把全链路页面重新编排成一个更适合运营管理的入口。',
    primaryAction: { to: '/aggregate', title: '进入快速聚合', hint: '继续沿用原有一键聚合与双模板导出' },
    secondaryAction: { to: '/dashboard', title: '查看处理看板', hint: '先看批次、异常和导出状态' },
    sections: [
      {
        title: '治理与总览',
        links: [
          { to: '/dashboard', title: '处理看板', hint: '批次总览、异常统计与状态分布' },
          { to: '/compare', title: '月度对比', hint: '查看左右差异并在线修正' },
          { to: '/exports', title: '导出结果', hint: '核查薪酬模板与工具表产物' },
        ],
      },
      {
        title: '基础数据',
        links: [
          { to: '/employees', title: '员工主档', hint: '导入、维护和审计主数据' },
          { to: '/mappings', title: '映射修正', hint: '处理低置信度字段映射' },
          { to: '/imports', title: '批次管理', hint: '钻取到源文件、表头和明细行' },
          { to: '/audit-logs', title: '审计日志', hint: '查看系统操作记录和安全事件' },
        ],
      },
    ],
  },
  hr: {
    kicker: 'HR Ops Desk',
    title: 'HR 工作台',
    description: 'HR 更关心每月经办效率，所以入口聚焦上传、校验、匹配、导出和员工答疑。',
    primaryAction: { to: '/aggregate', title: '开始当月聚合', hint: '上传社保与公积金文件后直接产出结果' },
    secondaryAction: { to: '/results', title: '查看校验匹配', hint: '确认问题记录和工号匹配结果' },
    sections: [
      {
        title: '月度处理',
        links: [
          { to: '/aggregate', title: '快速聚合', hint: '默认入口，适合常规月度处理' },
          { to: '/results', title: '校验匹配', hint: '查看缺失、异常和匹配情况' },
          { to: '/exports', title: '导出结果', hint: '确认两份固定模板都已生成' },
        ],
      },
      {
        title: '辅助入口',
        links: [
          { to: '/imports', title: '批次管理', hint: '需要回溯时查看原始文件和解析详情' },
          { to: '/employees', title: '员工主档', hint: '补录或更新员工信息' },
          { to: '/employee/query', title: '员工查询入口', hint: '转给员工自助核对本月记录' },
        ],
      },
    ],
  },
};

function WorkspacePage({ role }: { role: WorkspaceRole }) {
  const config = WORKSPACE_CONFIG[role];

  return (
    <div className="workspace-shell">
      <header className="workspace-hero">
        <div>
          <p className="portal-kicker">{config.kicker}</p>
          <h1>{config.title}</h1>
          <p>{config.description}</p>
        </div>
        <div className="workspace-hero__actions">
          <Link className="portal-button portal-button--primary" to={config.primaryAction.to}>
            {config.primaryAction.title}
          </Link>
          <Link className="portal-button portal-button--ghost" to={config.secondaryAction.to}>
            {config.secondaryAction.title}
          </Link>
          <Link className="workspace-link" to="/">
            返回系统门户
          </Link>
        </div>
      </header>

      <div className="workspace-grid">
        {config.sections.map((section) => (
          <section key={section.title} className="workspace-panel">
            <h2>{section.title}</h2>
            <div className="workspace-links">
              {section.links.map((item) => (
                <Link key={item.to} to={item.to} className="workspace-card">
                  <strong>{item.title}</strong>
                  <span>{item.hint}</span>
                </Link>
              ))}
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}

export function AdminWorkspacePage() {
  return <WorkspacePage role="admin" />;
}

export function HrWorkspacePage() {
  return <WorkspacePage role="hr" />;
}
