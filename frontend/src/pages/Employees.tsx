import { PageContainer } from "../components";

const employeePrinciples = [
  "身份证号优先精确匹配，姓名 + 公司作为辅助匹配依据。",
  "未匹配、重复匹配、低置信度匹配都必须有可解释结果。",
  "人工修正后的工号结果需要能够回写并被后续导出链路消费。",
];

export function EmployeesPage() {
  return (
    <PageContainer
      eyebrow="Employees"
      title="员工主数据"
      description="这里会用于导入和维护员工主档，为后续工号匹配流程提供稳定的基准数据。"
      actions={<span className="pill">任务 6 预备页</span>}
    >
      <div className="panel-grid panel-grid--two">
        <article className="panel-card panel-card--soft">
          <span className="panel-label">主档字段</span>
          <strong>工号、姓名、身份证号、公司、部门、在职状态</strong>
          <p>后续会补批量导入、唯一性校验、查询接口和模糊匹配辅助字段。</p>
        </article>
        <article className="panel-card panel-card--soft">
          <span className="panel-label">匹配策略</span>
          <strong>精确优先，人工兜底</strong>
          <p>低置信度结果不会被静默接受，前后端都需要保留依据和状态。</p>
        </article>
      </div>
      <div className="panel-card">
        <h2>后续实现约束</h2>
        <div className="status-list">
          {employeePrinciples.map((item) => (
            <div key={item} className="status-item">
              {item}
            </div>
          ))}
        </div>
      </div>
    </PageContainer>
  );
}
