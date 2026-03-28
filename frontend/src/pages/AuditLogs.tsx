import { useCallback, useEffect, useState } from 'react';

import { PageContainer } from '../components/PageContainer';
import { getApiBaseUrl } from '../config/env';

interface AuditLogItem {
  id: string;
  action: string;
  actor_username: string;
  actor_role: string;
  ip_address: string | null;
  detail: string | null;
  resource_type: string | null;
  resource_id: string | null;
  success: boolean;
  created_at: string;
}

interface AuditLogResponse {
  items: AuditLogItem[];
  total: number;
  page: number;
  page_size: number;
}

const ACTION_LABELS: Record<string, string> = {
  login: '登录成功',
  login_failed: '登录失败',
  export: '数据导出',
  import: '数据导入',
  aggregate: '数据融合',
  user_create: '创建用户',
  user_update: '编辑用户',
  user_disable: '禁用用户',
  employee_verify: '员工验证成功',
  employee_verify_failed: '员工验证失败',
};

const ROLE_LABELS: Record<string, string> = {
  admin: '管理员',
  hr: 'HR',
  employee: '员工',
  unknown: '未知',
};

const PAGE_SIZE = 20;

export function AuditLogsPage() {
  const [items, setItems] = useState<AuditLogItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [action, setAction] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  const fetchLogs = useCallback(async (currentPage: number, filterAction: string, filterStart: string, filterEnd: string) => {
    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('token');
      const params = new URLSearchParams();
      if (filterAction) params.set('action', filterAction);
      if (filterStart) params.set('start_time', filterStart + 'T00:00:00');
      if (filterEnd) params.set('end_time', filterEnd + 'T23:59:59');
      params.set('page', String(currentPage));
      params.set('page_size', String(PAGE_SIZE));

      const response = await fetch(`${getApiBaseUrl()}/audit-logs?${params}`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (!response.ok) {
        throw new Error(`请求失败 (${response.status})`);
      }

      const json = await response.json();
      const data: AuditLogResponse = json.data;
      setItems(data.items);
      setTotal(data.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : '请求审计日志失败');
      setItems([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchLogs(page, action, startDate, endDate);
  }, [page, fetchLogs]);

  function handleSearch() {
    setPage(1);
    fetchLogs(1, action, startDate, endDate);
  }

  function formatTime(isoString: string): string {
    return new Date(isoString).toLocaleString('zh-CN');
  }

  function truncateDetail(detail: string | null): string {
    if (!detail) return '-';
    return detail.length > 50 ? detail.slice(0, 50) + '...' : detail;
  }

  return (
    <PageContainer
      eyebrow="Security & Compliance"
      title="审计日志"
      description="查看系统操作记录，支持按操作类型和时间范围筛选。"
    >
      <div className="audit-filters" style={{ display: 'flex', gap: '12px', alignItems: 'center', flexWrap: 'wrap', marginBottom: '16px' }}>
        <select value={action} onChange={(e) => setAction(e.target.value)} style={{ padding: '6px 10px' }}>
          <option value="">全部操作</option>
          <option value="login">登录成功</option>
          <option value="login_failed">登录失败</option>
          <option value="export">数据导出</option>
          <option value="import">数据导入</option>
          <option value="aggregate">数据融合</option>
          <option value="user_create">创建用户</option>
          <option value="user_update">编辑用户</option>
          <option value="user_disable">禁用用户</option>
          <option value="employee_verify">员工验证成功</option>
          <option value="employee_verify_failed">员工验证失败</option>
        </select>

        <input
          type="date"
          value={startDate}
          onChange={(e) => setStartDate(e.target.value)}
          placeholder="起始日期"
          style={{ padding: '6px 10px' }}
        />

        <input
          type="date"
          value={endDate}
          onChange={(e) => setEndDate(e.target.value)}
          placeholder="结束日期"
          style={{ padding: '6px 10px' }}
        />

        <button type="button" onClick={handleSearch} style={{ padding: '6px 16px' }}>
          查询
        </button>
      </div>

      {loading && <p>加载中...</p>}
      {error && <p style={{ color: 'red' }}>{error}</p>}
      {!loading && !error && items.length === 0 && <p>暂无审计日志</p>}

      {!loading && !error && items.length > 0 && (
        <>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr>
                  <th style={{ textAlign: 'left', padding: '8px', borderBottom: '2px solid #e5e7eb' }}>时间</th>
                  <th style={{ textAlign: 'left', padding: '8px', borderBottom: '2px solid #e5e7eb' }}>操作类型</th>
                  <th style={{ textAlign: 'left', padding: '8px', borderBottom: '2px solid #e5e7eb' }}>操作人</th>
                  <th style={{ textAlign: 'left', padding: '8px', borderBottom: '2px solid #e5e7eb' }}>角色</th>
                  <th style={{ textAlign: 'left', padding: '8px', borderBottom: '2px solid #e5e7eb' }}>IP 地址</th>
                  <th style={{ textAlign: 'left', padding: '8px', borderBottom: '2px solid #e5e7eb' }}>结果</th>
                  <th style={{ textAlign: 'left', padding: '8px', borderBottom: '2px solid #e5e7eb' }}>详情</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <tr key={item.id} style={{ borderBottom: '1px solid #f3f4f6' }}>
                    <td style={{ padding: '8px', whiteSpace: 'nowrap' }}>{formatTime(item.created_at)}</td>
                    <td style={{ padding: '8px' }}>{ACTION_LABELS[item.action] || item.action}</td>
                    <td style={{ padding: '8px' }}>{item.actor_username}</td>
                    <td style={{ padding: '8px' }}>{ROLE_LABELS[item.actor_role] || item.actor_role}</td>
                    <td style={{ padding: '8px' }}>{item.ip_address || '-'}</td>
                    <td style={{ padding: '8px' }}>
                      <span style={{ color: item.success ? '#16a34a' : '#dc2626' }}>
                        {item.success ? '成功' : '失败'}
                      </span>
                    </td>
                    <td style={{ padding: '8px' }} title={item.detail || undefined}>
                      {truncateDetail(item.detail)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '16px' }}>
            <span>共 {total} 条记录</span>
            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
              <button
                type="button"
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                style={{ padding: '4px 12px' }}
              >
                上一页
              </button>
              <span>{page} / {totalPages}</span>
              <button
                type="button"
                disabled={page >= totalPages}
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                style={{ padding: '4px 12px' }}
              >
                下一页
              </button>
            </div>
          </div>
        </>
      )}
    </PageContainer>
  );
}
