import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Alert,
  Button,
  Card,
  Col,
  DatePicker,
  Row,
  Select,
  Space,
  Table,
  Tag,
  Typography,
} from 'antd';
import { FilterOutlined, SearchOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import type { Dayjs } from 'dayjs';

import { ResponsiveFilterDrawer } from '../components/ResponsiveFilterDrawer';
import { useResponsiveViewport } from '../hooks/useResponsiveViewport';
import { getApiBaseUrl } from '../config/env';
import { readAuthSession } from '../services/authSession';

const { Title, Text } = Typography;

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

const ACTION_OPTIONS = [
  { value: '', label: '全部操作' },
  { value: 'login', label: '登录成功' },
  { value: 'login_failed', label: '登录失败' },
  { value: 'export', label: '数据导出' },
  { value: 'import', label: '数据导入' },
  { value: 'aggregate', label: '数据融合' },
  { value: 'user_create', label: '创建用户' },
  { value: 'user_update', label: '编辑用户' },
  { value: 'user_disable', label: '禁用用户' },
  { value: 'employee_verify', label: '员工验证成功' },
  { value: 'employee_verify_failed', label: '员工验证失败' },
];

const ACTION_LABELS: Record<string, string> = Object.fromEntries(
  ACTION_OPTIONS.filter((o) => o.value).map((o) => [o.value, o.label]),
);

const ROLE_LABELS: Record<string, string> = {
  admin: '管理员',
  hr: 'HR',
  employee: '员工',
  unknown: '未知',
};

const PAGE_SIZE = 20;

export function AuditLogsPage() {
  const { isMobile, isTablet } = useResponsiveViewport();
  const isCompactFilter = isMobile || isTablet;
  const [items, setItems] = useState<AuditLogItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [action, setAction] = useState('');
  const [dateRange, setDateRange] = useState<[Dayjs | null, Dayjs | null] | null>(null);
  const [draftAction, setDraftAction] = useState('');
  const [draftDateRange, setDraftDateRange] = useState<[Dayjs | null, Dayjs | null] | null>(null);
  const [filterDrawerOpen, setFilterDrawerOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const allLocalIp = useMemo(() => {
    if (!items || items.length < 5) return false;
    return items.every(
      (log) => !log.ip_address || log.ip_address === '127.0.0.1'
    );
  }, [items]);

  const fetchLogs = useCallback(async (currentPage: number, filterAction: string, filterDateRange: [Dayjs | null, Dayjs | null] | null) => {
    setLoading(true);
    setError(null);

    try {
      const session = readAuthSession();
      const token = session?.accessToken;
      const params = new URLSearchParams();
      if (filterAction) params.set('action', filterAction);
      if (filterDateRange?.[0]) params.set('start_time', filterDateRange[0].format('YYYY-MM-DD') + 'T00:00:00');
      if (filterDateRange?.[1]) params.set('end_time', filterDateRange[1].format('YYYY-MM-DD') + 'T23:59:59');
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
    fetchLogs(page, action, dateRange);
  }, [action, dateRange, page, fetchLogs]);

  useEffect(() => {
    setDraftAction(action);
    setDraftDateRange(dateRange);
  }, [action, dateRange]);

  function countActiveFilters() {
    let count = 0;
    if (action) count += 1;
    if (dateRange?.[0] || dateRange?.[1]) count += 1;
    return count;
  }

  function closeFilterDrawer() {
    setDraftAction(action);
    setDraftDateRange(dateRange);
    setFilterDrawerOpen(false);
  }

  function applyDraftFilters() {
    const sameFilters =
      draftAction === action &&
      draftDateRange?.[0]?.valueOf() === dateRange?.[0]?.valueOf() &&
      draftDateRange?.[1]?.valueOf() === dateRange?.[1]?.valueOf();

    setFilterDrawerOpen(false);

    if (sameFilters && page === 1) {
      void fetchLogs(1, draftAction, draftDateRange);
      return;
    }

    setAction(draftAction);
    setDateRange(draftDateRange);
    setPage(1);
  }

  function resetFilters() {
    setDraftAction('');
    setDraftDateRange(null);
    setFilterDrawerOpen(false);

    if (!action && !dateRange && page === 1) {
      void fetchLogs(1, '', null);
      return;
    }

    setAction('');
    setDateRange(null);
    setPage(1);
  }

  function formatTime(isoString: string): string {
    return new Date(isoString).toLocaleString('zh-CN');
  }

  const columns: ColumnsType<AuditLogItem> = [
    {
      title: '时间',
      dataIndex: 'created_at',
      key: 'created_at',
      fixed: 'left',
      width: 180,
      render: (val: string) => formatTime(val),
    },
    {
      title: '操作类型',
      dataIndex: 'action',
      key: 'action',
      width: 120,
      render: (val: string) => ACTION_LABELS[val] || val,
    },
    {
      title: '操作人',
      dataIndex: 'actor_username',
      key: 'actor_username',
      width: 100,
    },
    {
      title: '角色',
      dataIndex: 'actor_role',
      key: 'actor_role',
      width: 80,
      render: (val: string) => <Tag>{ROLE_LABELS[val] || val}</Tag>,
    },
    {
      title: 'IP 地址',
      dataIndex: 'ip_address',
      key: 'ip_address',
      width: 130,
      render: (val: string | null) => val || '-',
    },
    {
      title: '结果',
      dataIndex: 'success',
      key: 'success',
      width: 80,
      render: (val: boolean) => (
        <Tag color={val ? 'success' : 'error'}>{val ? '成功' : '失败'}</Tag>
      ),
    },
    {
      title: '详情',
      dataIndex: 'detail',
      key: 'detail',
      ellipsis: true,
      render: (val: string | null) => val || '-',
    },
  ];

  const activeFilterCount = countActiveFilters();
  const filterFields = (
    <Row gutter={[12, 12]} align="middle">
      <Col xs={24} sm={12}>
        <Select
          style={{ width: '100%' }}
          value={draftAction}
          onChange={(value) => setDraftAction(value)}
          options={ACTION_OPTIONS}
        />
      </Col>
      <Col xs={24} sm={12}>
        <DatePicker.RangePicker
          style={{ width: '100%' }}
          value={draftDateRange as [Dayjs, Dayjs] | undefined}
          onChange={(values) => setDraftDateRange(values as [Dayjs | null, Dayjs | null] | null)}
        />
      </Col>
      {isCompactFilter ? null : (
        <Col xs={24}>
          <Space wrap>
            <Button type="primary" icon={<SearchOutlined />} onClick={applyDraftFilters}>
              查询
            </Button>
            <Button onClick={resetFilters}>清空</Button>
            <Text type="secondary">共 {total} 条记录</Text>
          </Space>
        </Col>
      )}
    </Row>
  );

  return (
    <div>
      <Row justify="space-between" align="middle" style={{ marginBottom: 16, gap: 12 }}>
        <Col>
          <Title level={4} style={{ margin: 0 }}>审计日志</Title>
        </Col>
        {isCompactFilter ? (
          <Col>
            <Button icon={<FilterOutlined />} onClick={() => setFilterDrawerOpen(true)}>
              {activeFilterCount > 0 ? `筛选 (${activeFilterCount})` : '筛选'}
            </Button>
          </Col>
        ) : null}
      </Row>

      {error && (
        <Alert type="error" message={error} style={{ marginBottom: 16 }} />
      )}

      {allLocalIp && (
        <Alert
          type="warning"
          showIcon
          message="所有审计日志的 IP 地址均为 127.0.0.1"
          description="这通常是因为系统通过反向代理（如 nginx）访问但未配置 X-Forwarded-For 头。请参考部署文档 docs/nginx-reverse-proxy.md 配置 nginx。"
          style={{ marginBottom: 16 }}
        />
      )}

      {isCompactFilter ? (
        <ResponsiveFilterDrawer
          title="筛选审计日志"
          open={filterDrawerOpen}
          onClose={closeFilterDrawer}
          onApply={applyDraftFilters}
          onReset={resetFilters}
          activeCount={activeFilterCount}
        >
          {filterFields}
        </ResponsiveFilterDrawer>
      ) : (
        <Card style={{ marginBottom: 16 }}>
          {filterFields}
        </Card>
      )}

      <Card>
        <Table
          size="small"
          columns={columns}
          dataSource={items}
          rowKey="id"
          loading={loading}
          scroll={{ x: 880 }}
          pagination={{
            current: page,
            pageSize: PAGE_SIZE,
            total,
            onChange: (p) => setPage(p),
            showTotal: (t) => `共 ${t} 条`,
          }}
        />
      </Card>
    </div>
  );
}
