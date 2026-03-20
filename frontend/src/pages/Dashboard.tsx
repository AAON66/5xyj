export function DashboardPage() {
  return (
    <section className="page-card">
      <h1>项目看板骨架</h1>
      <p>
        当前阶段先完成基础工程搭建。后续会在这里接入导入批次、地区覆盖、未识别字段、校验问题和双模板导出统计。
      </p>
      <div className="status-list">
        <div className="status-item">主链路优先级：导入 - 识别 - 标准化 - 过滤 - 匹配 - 校验 - 导出</div>
        <div className="status-item">LLM 策略：规则优先，DeepSeek 仅作为低风险兜底</div>
        <div className="status-item">当前状态：任务 1 基础配置进行中</div>
      </div>
    </section>
  );
}

