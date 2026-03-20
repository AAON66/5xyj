import { Link } from "react-router-dom";

import { PageContainer } from "../components";

export function NotFoundPage() {
  return (
    <PageContainer
      eyebrow="404"
      title="页面不存在"
      description="当前路由还没有对应页面，先回到主链路入口继续推进导入、解析和导出。"
      actions={
        <Link className="button button--primary" to="/">
          返回看板
        </Link>
      }
    >
      <div className="panel-card">
        <h2>下一步建议</h2>
        <div className="status-list">
          <div className="status-item">从看板确认 API 连接是否正常。</div>
          <div className="status-item">进入导入批次页，为后续上传与解析 API 预留交互位置。</div>
          <div className="status-item">保持前端只负责展示，不把地区解析规则写进界面层。</div>
        </div>
      </div>
    </PageContainer>
  );
}
