import { useEffect, useState } from "react";

import { PageContainer } from "../components";
import { fetchSystemHealth, type SystemHealth } from "../services/system";

const deliveryMilestones = [
  "导入 -> 识别 -> 标准化 -> 过滤 -> 匹配 -> 校验 -> 双模板导出",
  "规则优先，DeepSeek 只在低置信度场景兜底",
  "每条标准化结果都需要保留源文件、表头和行号溯源信息",
];

export function DashboardPage() {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;

    async function loadHealth() {
      try {
        const result = await fetchSystemHealth();
        if (active) {
          setHealth(result);
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void loadHealth();

    return () => {
      active = false;
    };
  }, []);

  return (
    <PageContainer
      eyebrow="Dashboard"
      title="项目看板骨架"
      description="先把后端可连接、路由可达、错误可见这层打牢，再继续接导入批次、字段识别和双模板导出。"
      actions={<span className="pill">任务 5: React 前端初始化</span>}
    >
      <div className="dashboard-grid">
        <article className="panel-card panel-card--accent">
          <span className="panel-label">后端连通性</span>
          <strong>{loading ? "检测中..." : health?.status === "ok" ? "已连接" : "未连接"}</strong>
          <p>
            {loading
              ? "正在请求 /api/v1/system/health。"
              : health
                ? `${health.app_name} · ${health.version}`
                : "未拿到健康检查结果，请查看顶部错误提示。"}
          </p>
        </article>
        <article className="panel-card">
          <span className="panel-label">当前重点</span>
          <strong>基础链路先稳住</strong>
          <p>前端已具备统一 API 请求、全局错误提示、基础导航和页面容器能力。</p>
        </article>
        <article className="panel-card">
          <span className="panel-label">下一阶段</span>
          <strong>文件上传与批次管理</strong>
          <p>接下来会优先进入上传、批次状态和解析预览，不把地区差异散落到前端。</p>
        </article>
      </div>
      <div className="panel-card">
        <h2>交付原则</h2>
        <div className="status-list">
          {deliveryMilestones.map((item) => (
            <div key={item} className="status-item">
              {item}
            </div>
          ))}
        </div>
      </div>
    </PageContainer>
  );
}
