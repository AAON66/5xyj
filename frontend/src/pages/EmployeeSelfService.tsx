import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Button,
  Card,
  Col,
  Collapse,
  Descriptions,
  Empty,
  Result,
  Row,
  Skeleton,
  Statistic,
  Table,
  Typography,
} from 'antd';
import { DownOutlined, UpOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';

import { useResponsiveViewport } from '../hooks/useResponsiveViewport';
import { normalizeApiError } from '../services/api';
import { fetchPortalRecords, type EmployeeSelfServiceRecord, type EmployeeSelfServiceResult } from '../services/employees';

const { Title, Text } = Typography;

function formatMoney(value: string | number | null): string {
  if (value === null || value === undefined || value === '') {
    return '-';
  }
  const amount = Number(value);
  if (!Number.isFinite(amount)) {
    return String(value);
  }
  return new Intl.NumberFormat('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount);
}

function formatBillingPeriod(period: string | null): string {
  if (!period) return '未知月份';
  if (/^\d{6}$/.test(period)) {
    return `${period.slice(0, 4)}年${period.slice(4, 6)}月`;
  }
  return period;
}

function InsuranceDetailTable({
  record,
  stacked,
}: {
  record: EmployeeSelfServiceRecord;
  stacked: boolean;
}) {
  const insuranceRows = [
    { key: '1', label: '养老保险', company: formatMoney(record.pension_company), personal: formatMoney(record.pension_personal) },
    { key: '2', label: '医疗保险', company: formatMoney(record.medical_company), personal: formatMoney(record.medical_personal) },
    { key: '3', label: '失业保险', company: formatMoney(record.unemployment_company), personal: formatMoney(record.unemployment_personal) },
    { key: '4', label: '工伤保险', company: formatMoney(record.injury_company), personal: '-' },
    { key: '5', label: '生育保险', company: formatMoney(record.maternity_amount), personal: '-' },
    { key: '6', label: '缴费基数', company: formatMoney(record.payment_base), personal: formatMoney(record.payment_base) },
  ];

  const insuranceCols: ColumnsType<typeof insuranceRows[number]> = [
    { title: '险种', dataIndex: 'label', key: 'label' },
    { title: '单位', dataIndex: 'company', key: 'company', align: 'right' },
    { title: '个人', dataIndex: 'personal', key: 'personal', align: 'right' },
  ];

  const hasHousingFund =
    record.housing_fund_company !== null ||
    record.housing_fund_personal !== null ||
    record.housing_fund_total !== null;

  const housingRows = hasHousingFund
    ? [
        {
          key: '1',
          label: '住房公积金',
          company: formatMoney(record.housing_fund_company),
          personal: formatMoney(record.housing_fund_personal),
          total: formatMoney(record.housing_fund_total),
        },
      ]
    : [];

  const housingCols: ColumnsType<typeof housingRows[number]> = [
    { title: '项目', dataIndex: 'label', key: 'label' },
    { title: '单位', dataIndex: 'company', key: 'company', align: 'right' },
    { title: '个人', dataIndex: 'personal', key: 'personal', align: 'right' },
    { title: '合计', dataIndex: 'total', key: 'total', align: 'right' },
  ];

  return (
    <Row gutter={[16, 16]}>
      <Col xs={24} md={stacked ? 24 : 12}>
        <Card size="small" title="社保明细">
          <Table
            size="small"
            columns={insuranceCols}
            dataSource={insuranceRows}
            pagination={false}
          />
        </Card>
      </Col>
      <Col xs={24} md={stacked ? 24 : 12}>
        <Card size="small" title="公积金明细">
          {hasHousingFund ? (
            <Table
              size="small"
              columns={housingCols}
              dataSource={housingRows}
              pagination={false}
            />
          ) : (
            <Empty description="暂无公积金数据" image={Empty.PRESENTED_IMAGE_SIMPLE} />
          )}
        </Card>
      </Col>
    </Row>
  );
}

function buildHistoryLabel(record: EmployeeSelfServiceRecord) {
  return (
    <div style={{ display: 'grid', gap: 4 }}>
      <Text strong>{formatBillingPeriod(record.billing_period)}</Text>
      <Text type="secondary">
        {(record.region || '未知地区')}
        {' · '}
        {(record.company_name || '未知公司')}
      </Text>
      <Text type="secondary">社保总额 {formatMoney(record.total_amount)}</Text>
    </div>
  );
}

export function EmployeeSelfServicePage() {
  const navigate = useNavigate();
  const { isMobile } = useResponsiveViewport();
  const [loading, setLoading] = useState(true);
  const [expired, setExpired] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [data, setData] = useState<EmployeeSelfServiceResult | null>(null);
  const [expandedKeys, setExpandedKeys] = useState<string[]>([]);

  const latestRecord = data?.records[0] ?? null;
  const containerStyle = {
    maxWidth: 960,
    margin: '0 auto',
    padding: isMobile ? '16px 12px 24px' : '32px 24px',
  };

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const result = await fetchPortalRecords();
        if (!cancelled) {
          setData(result);
          if (result.records[0]) {
            setExpandedKeys([result.records[0].normalized_record_id]);
          }
          setLoading(false);
        }
      } catch (error) {
        if (cancelled) return;
        const apiErr = normalizeApiError(error);
        if (apiErr.statusCode === 401) {
          setExpired(true);
          setLoading(false);
        } else {
          setErrorMessage(apiErr.message || '加载数据失败，请稍后重试。');
          setLoading(false);
        }
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!expired) return;
    const timer = setTimeout(() => {
      navigate('/login', { replace: true });
    }, 2000);
    return () => clearTimeout(timer);
  }, [expired, navigate]);

  if (expired) {
    return (
      <Result
        status="warning"
        title="登录已过期，请重新验证"
        subTitle="2 秒后自动跳转到登录页面..."
      />
    );
  }

  if (loading) {
    return (
      <div style={containerStyle}>
        <Skeleton active paragraph={{ rows: 6 }} />
      </div>
    );
  }

  if (errorMessage) {
    return (
      <Result
        status="error"
        title="加载失败"
        subTitle={errorMessage}
        extra={<Button type="primary" onClick={() => window.location.reload()}>重试</Button>}
      />
    );
  }

  if (!data || data.record_count === 0) {
    return (
      <div style={containerStyle}>
        {data?.profile ? (
          <Card style={{ marginBottom: 24 }}>
            <Descriptions title={data.profile.person_name} column={{ xs: 1, sm: 2, md: 4 }}>
              <Descriptions.Item label="工号">{data.profile.employee_id || '未匹配'}</Descriptions.Item>
              <Descriptions.Item label="公司">{data.profile.company_name || '未登记'}</Descriptions.Item>
              <Descriptions.Item label="身份证号">{data.profile.masked_id_number}</Descriptions.Item>
            </Descriptions>
          </Card>
        ) : null}
        <Empty description="未找到匹配的社保记录" />
      </div>
    );
  }

  const historyColumns: ColumnsType<EmployeeSelfServiceRecord> = [
    {
      title: '所属期',
      dataIndex: 'billing_period',
      key: 'billing_period',
      render: (val: string) => formatBillingPeriod(val),
    },
    {
      title: '地区',
      dataIndex: 'region',
      key: 'region',
      render: (val: string | null) => val || '未知地区',
    },
    {
      title: '公司',
      dataIndex: 'company_name',
      key: 'company_name',
      render: (val: string | null) => val || '未知公司',
    },
    {
      title: '社保总额',
      dataIndex: 'total_amount',
      key: 'total_amount',
      align: 'right',
      render: (val: string | number | null) => formatMoney(val),
    },
    {
      title: '公积金合计',
      dataIndex: 'housing_fund_total',
      key: 'housing_fund_total',
      align: 'right',
      render: (val: string | number | null) => formatMoney(val),
    },
  ];

  return (
    <div style={containerStyle}>
      <Title level={4}>员工社保查询</Title>

      <Card style={{ marginBottom: 24 }}>
        <Descriptions title={data.profile.person_name} column={{ xs: 1, sm: 2, md: 4 }}>
          <Descriptions.Item label="工号">{data.profile.employee_id || '未匹配'}</Descriptions.Item>
          <Descriptions.Item label="公司">{data.profile.company_name || '未登记'}</Descriptions.Item>
          <Descriptions.Item label="身份证号">{data.profile.masked_id_number}</Descriptions.Item>
          <Descriptions.Item label="部门">{data.profile.department || '未登记'}</Descriptions.Item>
        </Descriptions>
      </Card>

      {latestRecord ? (
        <>
          <Text type="secondary" style={{ display: 'block', marginBottom: 12 }}>
            {formatBillingPeriod(latestRecord.billing_period)} 缴费汇总
          </Text>
          <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
            <Col xs={12} md={6}>
              <Card>
                <Statistic title="社保总额" value={Number(latestRecord.total_amount) || 0} precision={2} />
              </Card>
            </Col>
            <Col xs={12} md={6}>
              <Card>
                <Statistic title="单位合计" value={Number(latestRecord.company_total_amount) || 0} precision={2} />
              </Card>
            </Col>
            <Col xs={12} md={6}>
              <Card>
                <Statistic title="个人合计" value={Number(latestRecord.personal_total_amount) || 0} precision={2} />
              </Card>
            </Col>
            {latestRecord.housing_fund_total !== null ? (
              <Col xs={12} md={6}>
                <Card>
                  <Statistic title="公积金合计" value={Number(latestRecord.housing_fund_total) || 0} precision={2} />
                </Card>
              </Col>
            ) : null}
          </Row>
        </>
      ) : null}

      <Title level={5}>缴费历史</Title>
      {isMobile ? (
        <Collapse
          activeKey={expandedKeys}
          onChange={(keys) => {
            const nextKeys = Array.isArray(keys)
              ? keys.map(String)
              : keys
                ? [String(keys)]
                : [];
            setExpandedKeys(nextKeys);
          }}
          items={data.records.map((record) => ({
            key: record.normalized_record_id,
            label: buildHistoryLabel(record),
            children: <InsuranceDetailTable record={record} stacked />,
          }))}
        />
      ) : (
        <Card>
          <Table
            size="small"
            columns={historyColumns}
            dataSource={data.records}
            rowKey="normalized_record_id"
            expandable={{
              expandedRowKeys: expandedKeys,
              onExpandedRowsChange: (keys) => setExpandedKeys(keys as string[]),
              expandedRowRender: (record) => <InsuranceDetailTable record={record} stacked={false} />,
              expandIcon: ({ expanded, onExpand, record }) => (
                expanded ? (
                  <UpOutlined onClick={(e) => onExpand(record, e)} style={{ cursor: 'pointer' }} />
                ) : (
                  <DownOutlined onClick={(e) => onExpand(record, e)} style={{ cursor: 'pointer' }} />
                )
              ),
            }}
            pagination={{ pageSize: 10, showSizeChanger: false }}
            footer={() => (
              <Text type="secondary" style={{ fontSize: 12 }}>
                共 {data.records.length} 条缴费记录
              </Text>
            )}
          />
        </Card>
      )}
    </div>
  );
}
