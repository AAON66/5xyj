import { useCallback, useEffect, useState } from 'react';
import {
  Alert,
  Button,
  Card,
  Col,
  DatePicker,
  Row,
  Select,
  Table,
  Tag,
  Typography,
} from 'antd';
import { SearchOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import type { Dayjs } from 'dayjs';

import { getApiBaseUrl } from '../config/env';
import { readAuthSession } from '../services/authSession';

const { Title, Text } = Typography;
const { RangePicker } = DatePicker;

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
  const [items, setItems] = useState<AuditLogItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [action, setAction] = useState('');
  const [dateRange, setDateRange] = useState<[Dayjs | null, Dayjs | null] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
  }, [page, fetchLogs]);

  function handleSearch() {
    setPage(1);
    fetchLogs(1, action, dateRange);
  }

  function formatTime(isoString: string): string {
    return new Date(isoString).toLocaleString('zh-CN');
  }

  const columns: ColumnsType<AuditLogItem> = [
    {
      title: '时间',
      dataIndex: 'created_at',
      key: 'created_at',
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

  return (
    <div>
      <Title level={4}>审计日志</Title>

      {error && (
        <Alert type="error" message={error} style={{ marginBottom: 16 }} />
      )}

      <Card style={{ marginBottom: 16 }}>
        <Row gutter={[12, 12]} align="middle">
          <Col>
            <Select
              style={{ width: 160 }}
              value={action}
              onChange={(val) => setAction(val)}
              options={ACTION_OPTIONS}
            />
          </Col>
          <Col>
            <RangePicker
              value={dateRange as [Dayjs, Dayjs] | undefined}
              onChange={(vals) => setDateRange(vals as [Dayjs | null, Dayjs | null] | null)}
            />
          </Col>
          <Col>
            <Button type="primary" icon={<SearchOutlined />} onClick={handleSearch}>
              查询
            </Button>
          </Col>
          <Col flex="auto" style={{ textAlign: 'right' }}>
            <Text type="secondary">共 {total} 条记录</Text>
          </Col>
        </Row>
      </Card>

      <Card>
        <Table
          size="small"
          columns={columns}
          dataSource={items}
          rowKey="id"
          loading={loading}
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
