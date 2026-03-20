import { Link } from "react-router-dom";

import { PageContainer } from "../components";

const importCapabilities = [
  "多文件上传会收敛到单个导入批次，不依赖固定 sheet 名或固定起始行。",
  "批次详情会展示有效 sheet、表头识别、标准字段映射和未识别字段。",
  "后续上传接口会同时落批次状态、源文件元信息和解析进度。",
];

export function ImportsPage() {
  return (
    <PageContainer
      eyebrow="Imports"
      title="导入批次"
      description="这里将承载 Excel 多文件上传、批次列表、解析状态和标准化预览。当前先把页面容器、说明信息和操作入口固定下来。"
      actions={
        <div className="button-row">
          <button type="button" className="button button--primary">
            新建导入批次
          </button>
          <button type="button" className="button button--ghost">
            查看最近批次
          </button>
        </div>
      }
    >
      <div className="panel-card">
        <h2>即将接入的能力</h2>
        <div className="status-list">
          {importCapabilities.map((item) => (
            <div key={item} className="status-item">
              {item}
            </div>
          ))}
        </div>
      </div>
      <div className="panel-grid panel-grid--two">
        <article className="panel-card">
          <span className="panel-label">样例覆盖</span>
          <strong>广州 / 杭州 / 厦门 / 深圳 / 武汉 / 长沙</strong>
          <p>后续每个解析步骤都要尽量用多个地区样例回归，优先覆盖复合表头和非标准表头。</p>
        </article>
        <article className="panel-card">
          <span className="panel-label">链路约束</span>
          <strong>规则优先，保留溯源</strong>
          <p>标准化结果不能只留规范字段，必须保留原始值、源文件、sheet 和行号。</p>
        </article>
      </div>
      <div className="inline-tip">
        真实上传接口完成前，可以先从<Link to="/">看板</Link>确认后端连接状态是否正常。
      </div>
    </PageContainer>
  );
}
