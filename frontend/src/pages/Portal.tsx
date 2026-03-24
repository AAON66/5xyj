import { Link } from 'react-router-dom';

const ROLE_CARDS = [
  {
    to: '/workspace/admin',
    eyebrow: 'Administrator',
    title: '管理员入口',
    description: '查看全链路运行状态，维护模板、映射、导入批次、员工主档与月度比对。',
    bullets: ['总览看板与异常治理', '导入批次、映射修正、员工主档', '导出结果与月度对比'],
  },
  {
    to: '/workspace/hr',
    eyebrow: 'HR Ops',
    title: 'HR 入口',
    description: '聚焦每月实操链路，从上传、校验、匹配到双模板导出都能在一个工作台里完成。',
    bullets: ['快速聚合与批次追踪', '校验匹配与导出检查', '员工自助查询入口转发'],
  },
  {
    to: '/employee/query',
    eyebrow: 'Self Service',
    title: '员工查询入口',
    description: '无需登录，只需输入姓名和身份证号即可查看最近的社保公积金记录。',
    bullets: ['姓名 + 身份证号查询', '查看最近批次与金额摘要', '适合员工自助核对'],
  },
];

const DIRECT_LINKS = [
  { to: '/aggregate', label: '快速聚合', hint: '保留原有上传即导出双模板能力' },
  { to: '/dashboard', label: '处理看板', hint: '查看状态分布、最近批次与异常' },
  { to: '/employees', label: '员工主档', hint: '导入、维护与审计员工主数据' },
];

export function ManagementPortalPage() {
  return (
    <div className="portal-shell">
      <section className="portal-hero">
        <div className="portal-hero__content">
          <p className="portal-kicker">Social Security & Housing Fund Management</p>
          <h1>社保公积金管理系统</h1>
          <p className="portal-summary">
            保留原有社保表格聚合、规则识别、校验匹配、双模板导出与月度对比能力，同时新增管理员、HR 和员工自助查询三类入口。
          </p>
          <div className="portal-actions">
            <Link className="portal-button portal-button--primary" to="/workspace/admin">
              进入管理员工作台
            </Link>
            <Link className="portal-button portal-button--ghost" to="/employee/query">
              员工免登录查询
            </Link>
          </div>
        </div>
        <div className="portal-hero__panel">
          <span>系统能力</span>
          <strong>导入识别</strong>
          <strong>字段标准化</strong>
          <strong>非明细过滤</strong>
          <strong>工号匹配</strong>
          <strong>双模板导出</strong>
        </div>
      </section>

      <section className="portal-lanes">
        {ROLE_CARDS.map((item) => (
          <Link key={item.to} to={item.to} className="portal-lane">
            <p>{item.eyebrow}</p>
            <h2>{item.title}</h2>
            <span>{item.description}</span>
            <ul>
              {item.bullets.map((bullet) => (
                <li key={bullet}>{bullet}</li>
              ))}
            </ul>
          </Link>
        ))}
      </section>

      <section className="portal-direct">
        <div>
          <p className="portal-kicker">Legacy Workflow</p>
          <h2>原有页面保持不变</h2>
          <p>
            如果你已经习惯原来的工作方式，仍然可以直接进入聚合、看板、批次管理、结果校验和导出页面。
          </p>
        </div>
        <div className="portal-direct__links">
          {DIRECT_LINKS.map((item) => (
            <Link key={item.to} to={item.to} className="portal-direct__link">
              <strong>{item.label}</strong>
              <span>{item.hint}</span>
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}
