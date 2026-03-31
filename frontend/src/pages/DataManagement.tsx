import { useCallback, useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  Button,
  Card,
  Col,
  Empty,
  Input,
  Row,
  Select,
  Skeleton,
  Table,
  Tabs,
  Tag,
  Typography,
} from 'antd';
import type { ColumnsType } from 'antd/es/table';

import { normalizeApiError } from '../services/api';
import {
  fetchEmployeeSummary,
  fetchFilterOptions,
  fetchNormalizedRecords,
  fetchPeriodSummary,
  type EmployeeSummaryItem,
  type FilterOptions,
  type NormalizedRecordItem,
  type PeriodSummaryItem,
} from '../services/dataManagement';

const { Title } = Typography;

type ActiveTab = 'detail' | 'summary';
type SummaryMode = 'employee' | 'period';

const PAGE_SIZE_OPTIONS = [10, 20, 50];

function formatAmount(value: number | null): string {
  if (value === null || value === undefined) return '-';
  return value.toFixed(2);
}

function formatPeriod(period: string | null): string {
  if (!period || period.length < 6) return period ?? '-';
  return `${period.slice(0, 4)}年${period.slice(4)}月`;
}

function maskIdNumber(id: string | null): string {
  if (!id || id.length < 8) return id ?? '-';
  return `${id.slice(0, 4)}****${id.slice(-4)}`;
}

export function DataManagementPage() {
  const [searchParams, setSearchParams] = useSearchParams();

  // Read state from URL
  const region = searchParams.get('region') || '';
  const company = searchParams.get('company') || '';
  const period = searchParams.get('period') || '';
  const activeTab = (searchParams.get('tab') as ActiveTab) || 'detail';
  const summaryMode = (searchParams.get('summaryMode') as SummaryMode) || 'employee';
  const page = Number(searchParams.get('page') || '0');
  const pageSize = Number(searchParams.get('pageSize') || '20');

  // Filter options
  const [filterOptions, setFilterOptions] = useState<FilterOptions>({ regions: [], companies: [], periods: [] });

  // Data states
  const [records, setRecords] = useState<NormalizedRecordItem[]>([]);
  const [employeeSummaries, setEmployeeSummaries] = useState<EmployeeSummaryItem[]>([]);
  const [periodSummaries, setPeriodSummaries] = useState<PeriodSummaryItem[]>([]);
  const [totalRecords, setTotalRecords] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedRowKeys, setExpandedRowKeys] = useState<string[]>([]);
  const [searchText, setSearchText] = useState('');

  // Helper to update URL params
  const updateParams = useCallback(
    (updates: Record<string, string>) => {
      setSearchParams((prev) => {
        const next = new URLSearchParams(prev);
        for (const [key, value] of Object.entries(updates)) {
          if (value) {
            next.set(key, value);
          } else {
            next.delete(key);
          }
        }
        return next;
      }, { replace: true });
    },
    [setSearchParams],
  );

  // Load filter options on mount and when cascading params change
  useEffect(() => {
    let active = true;

    async function loadFilters() {
      try {
        const unscopedOptions = await fetchFilterOptions();
        if (!active) return;

        let companies: string[] = unscopedOptions.companies;
        let periods: string[] = unscopedOptions.periods;

        if (region) {
          const regionScoped = await fetchFilterOptions({ region });
          if (!active) return;
          companies = regionScoped.companies;
          periods = regionScoped.periods;

          if (company) {
            const fullScoped = await fetchFilterOptions({ region, companyName: company });
            if (!active) return;
            periods = fullScoped.periods;
          }
        }

        setFilterOptions({
          regions: unscopedOptions.regions,
          companies,
          periods,
        });

        if (company && !companies.includes(company)) {
          updateParams({ company: '', period: '', page: '0' });
        } else if (period && !periods.includes(period)) {
          updateParams({ period: '', page: '0' });
        }
      } catch {
        // Filter loading failure is non-critical
      }
    }

    void loadFilters();
    return () => { active = false; };
  }, [region, company, updateParams]);

  // Load data when filters/tab/page change
  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);
    setExpandedRowKeys([]);

    async function loadData() {
      try {
        const filterParams = {
          region: region || undefined,
          companyName: company || undefined,
          billingPeriod: period || undefined,
          page,
          pageSize,
        };

        if (activeTab === 'detail') {
          const result = await fetchNormalizedRecords(filterParams);
          if (!active) return;
          setRecords(result.items);
          setTotalRecords(result.total);
        } else if (summaryMode === 'employee') {
          const result = await fetchEmployeeSummary(filterParams);
          if (!active) return;
          setEmployeeSummaries(result.items);
          setTotalRecords(result.total);
        } else {
          const result = await fetchPeriodSummary({
            region: region || undefined,
            companyName: company || undefined,
            page,
            pageSize,
          });
          if (!active) return;
          setPeriodSummaries(result.items);
          setTotalRecords(result.total);
        }
      } catch (err) {
        if (active) {
          setError(normalizeApiError(err).message || '数据加载失败');
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void loadData();
    return () => { active = false; };
  }, [region, company, period, activeTab, summaryMode, page, pageSize]);

  function handleRegionChange(newRegion: string) {
    updateParams({ region: newRegion, company: '', period: '', page: '0' });
  }

  function handleCompanyChange(newCompany: string) {
    updateParams({ company: newCompany, period: '', page: '0' });
    if (region && newCompany) {
      fetchFilterOptions({ region, companyName: newCompany })
        .then((opts) => setFilterOptions((prev) => ({ ...prev, periods: opts.periods })))
        .catch(() => {});
    }
  }

  function handlePeriodChange(newPeriod: string) {
    updateParams({ period: newPeriod, page: '0' });
  }

  function handleTabChange(tab: string) {
    updateParams({ tab, page: '0' });
  }

  function handleSummaryModeChange(mode: string) {
    updateParams({ summaryMode: mode, page: '0' });
  }

  function handleResetFilters() {
    updateParams({ region: '', company: '', period: '', page: '0' });
    setSearchText('');
  }

  // Detail table columns
  const detailColumns: ColumnsType<NormalizedRecordItem> = useMemo(() => [
    { title: '姓名', dataIndex: 'person_name', key: 'person_name', fixed: 'left' as const, width: 80, render: (v: string | null) => v ?? '-' },
    { title: '工号', dataIndex: 'employee_id', key: 'employee_id', width: 80, render: (v: string | null) => v ?? '-' },
    { title: '地区', dataIndex: 'region', key: 'region', width: 70, render: (v: string | null) => v ?? '-' },
    { title: '公司', dataIndex: 'company_name', key: 'company_name', width: 120, ellipsis: true, render: (v: string | null) => v ?? '-' },
    { title: '身份证号', dataIndex: 'id_number', key: 'id_number', width: 140, render: (v: string | null) => maskIdNumber(v) },
    { title: '月份', dataIndex: 'billing_period', key: 'billing_period', width: 80, render: (v: string | null) => formatPeriod(v) },
    { title: '单位合计', dataIndex: 'company_total_amount', key: 'company_total_amount', width: 100, align: 'right' as const, render: (v: number | null) => formatAmount(v) },
    { title: '个人合计', dataIndex: 'personal_total_amount', key: 'personal_total_amount', width: 100, align: 'right' as const, render: (v: number | null) => formatAmount(v) },
    { title: '总额', dataIndex: 'total_amount', key: 'total_amount', width: 100, align: 'right' as const, render: (v: number | null) => formatAmount(v) },
    {
      title: '匹配', key: 'match_status', width: 70,
      render: (_: unknown, record: NormalizedRecordItem) => {
        if (record.employee_id) return <Tag color="success">已匹配</Tag>;
        return <Tag color="warning">未匹配</Tag>;
      },
    },
  ], []);

  const expandedRowRender = useCallback((record: NormalizedRecordItem) => (
    <Row gutter={[24, 16]}>
      <Col span={12}>
        <Card size="small" title="单位各险种">
          <Row gutter={[8, 4]}>
            <Col span={12}>养老保险: {formatAmount(record.pension_company)}</Col>
            <Col span={12}>医疗保险: {formatAmount(record.medical_company)}</Col>
            <Col span={12}>医疗(含生育): {formatAmount(record.medical_maternity_company)}</Col>
            <Col span={12}>失业保险: {formatAmount(record.unemployment_company)}</Col>
            <Col span={12}>工伤保险: {formatAmount(record.injury_company)}</Col>
            <Col span={12}>补充医疗: {formatAmount(record.supplementary_medical_company)}</Col>
            <Col span={12}>补充养老: {formatAmount(record.supplementary_pension_company)}</Col>
            <Col span={12}>公积金(单位): {formatAmount(record.housing_fund_company)}</Col>
          </Row>
        </Card>
      </Col>
      <Col span={12}>
        <Card size="small" title="个人各险种">
          <Row gutter={[8, 4]}>
            <Col span={12}>养老保险: {formatAmount(record.pension_personal)}</Col>
            <Col span={12}>医疗保险: {formatAmount(record.medical_personal)}</Col>
            <Col span={12}>失业保险: {formatAmount(record.unemployment_personal)}</Col>
            <Col span={12}>大额医疗: {formatAmount(record.large_medical_personal)}</Col>
            <Col span={12}>公积金(个人): {formatAmount(record.housing_fund_personal)}</Col>
            <Col span={12}>缴费基数: {formatAmount(record.payment_base)}</Col>
          </Row>
        </Card>
      </Col>
    </Row>
  ), []);

  // Employee summary columns
  const employeeSummaryColumns: ColumnsType<EmployeeSummaryItem> = useMemo(() => [
    { title: '工号', dataIndex: 'employee_id', key: 'employee_id', fixed: 'left' as const, width: 100, render: (v: string | null) => v ?? '-' },
    { title: '姓名', dataIndex: 'person_name', key: 'person_name', render: (v: string | null) => v ?? '-' },
    { title: '公司', dataIndex: 'company_name', key: 'company_name', render: (v: string | null) => v ?? '-' },
    { title: '地区', dataIndex: 'region', key: 'region', render: (v: string | null) => v ?? '-' },
    { title: '最新月份', dataIndex: 'latest_period', key: 'latest_period', render: (v: string | null) => formatPeriod(v) },
    { title: '单位合计', dataIndex: 'company_total', key: 'company_total', align: 'right' as const, render: (v: number | null) => formatAmount(v) },
    { title: '个人合计', dataIndex: 'personal_total', key: 'personal_total', align: 'right' as const, render: (v: number | null) => formatAmount(v) },
    { title: '总额', dataIndex: 'total', key: 'total', align: 'right' as const, render: (v: number | null) => formatAmount(v) },
  ], []);

  // Period summary columns
  const periodSummaryColumns: ColumnsType<PeriodSummaryItem> = useMemo(() => [
    { title: '月份', dataIndex: 'billing_period', key: 'billing_period', fixed: 'left' as const, width: 100, render: (v: string) => formatPeriod(v) },
    { title: '总人数', dataIndex: 'total_count', key: 'total_count' },
    { title: '单位合计', dataIndex: 'company_total', key: 'company_total', align: 'right' as const, render: (v: number | null) => formatAmount(v) },
    { title: '个人合计', dataIndex: 'personal_total', key: 'personal_total', align: 'right' as const, render: (v: number | null) => formatAmount(v) },
    { title: '总额', dataIndex: 'total', key: 'total', align: 'right' as const, render: (v: number | null) => formatAmount(v) },
    { title: '平均个人', dataIndex: 'avg_personal', key: 'avg_personal', align: 'right' as const, render: (v: number | null) => formatAmount(v) },
    { title: '平均单位', dataIndex: 'avg_company', key: 'avg_company', align: 'right' as const, render: (v: number | null) => formatAmount(v) },
  ], []);

  const paginationConfig = useMemo(() => ({
    current: page + 1,
    pageSize,
    total: totalRecords,
    showSizeChanger: true,
    pageSizeOptions: PAGE_SIZE_OPTIONS.map(String),
    showTotal: (total: number) => `共 ${total} 条记录`,
    onChange: (newPage: number, newPageSize: number) => {
      if (newPageSize !== pageSize) {
        updateParams({ pageSize: String(newPageSize), page: '0' });
      } else {
        updateParams({ page: String(newPage - 1) });
      }
    },
  }), [page, pageSize, totalRecords, updateParams]);

  const hasData = activeTab === 'detail'
    ? records.length > 0
    : summaryMode === 'employee'
      ? employeeSummaries.length > 0
      : periodSummaries.length > 0;

  return (
    <div>
      <Title level={4}>数据管理</Title>

      {/* Filter card */}
      <Card style={{ marginBottom: 16 }}>
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} sm={12} md={6}>
            <Select
              placeholder="选择地区"
              allowClear
              value={region || undefined}
              onChange={(v) => handleRegionChange(v ?? '')}
              style={{ width: '100%' }}
              options={filterOptions.regions.map((r) => ({ label: r, value: r }))}
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Select
              placeholder="选择公司"
              allowClear
              value={company || undefined}
              onChange={(v) => handleCompanyChange(v ?? '')}
              style={{ width: '100%' }}
              options={filterOptions.companies.map((c) => ({ label: c, value: c }))}
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Select
              placeholder="选择月份"
              allowClear
              value={period || undefined}
              onChange={(v) => handlePeriodChange(v ?? '')}
              style={{ width: '100%' }}
              options={filterOptions.periods.map((p) => ({ label: formatPeriod(p), value: p }))}
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Input.Search
              placeholder="搜索姓名或工号"
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              onSearch={() => updateParams({ page: '0' })}
              allowClear
            />
          </Col>
          <Col>
            <Button type="primary" onClick={() => updateParams({ page: '0' })}>查询</Button>
          </Col>
          <Col>
            <Button onClick={handleResetFilters}>重置</Button>
          </Col>
        </Row>
      </Card>

      {/* Tabs */}
      <Card>
        <Tabs
          activeKey={activeTab}
          onChange={handleTabChange}
          items={[
            {
              key: 'detail',
              label: '明细数据',
              children: loading ? (
                <Skeleton active paragraph={{ rows: 8 }} />
              ) : error ? (
                <Empty description={error} />
              ) : !hasData ? (
                <Empty description="当前没有可显示的记录。请先上传社保文件或调整筛选条件。" />
              ) : (
                <Table<NormalizedRecordItem>
                  columns={detailColumns}
                  dataSource={records}
                  rowKey="id"
                  size="small"
                  pagination={paginationConfig}
                  scroll={{ x: 1000 }}
                  expandable={{
                    expandedRowKeys,
                    onExpandedRowsChange: (keys) => setExpandedRowKeys(keys as string[]),
                    expandedRowRender,
                  }}
                />
              ),
            },
            {
              key: 'summary',
              label: '全员汇总',
              children: (
                <>
                  <Tabs
                    activeKey={summaryMode}
                    onChange={handleSummaryModeChange}
                    size="small"
                    style={{ marginBottom: 16 }}
                    items={[
                      {
                        key: 'employee',
                        label: '按员工汇总',
                        children: loading ? (
                          <Skeleton active paragraph={{ rows: 8 }} />
                        ) : !employeeSummaries.length ? (
                          <Empty description="当前没有可显示的记录。请先上传社保文件或调整筛选条件。" />
                        ) : (
                          <Table<EmployeeSummaryItem>
                            columns={employeeSummaryColumns}
                            dataSource={employeeSummaries}
                            rowKey={(item, idx) => `${item.employee_id ?? ''}-${item.person_name ?? ''}-${idx}`}
                            size="small"
                            pagination={paginationConfig}
                            scroll={{ x: 800 }}
                          />
                        ),
                      },
                      {
                        key: 'period',
                        label: '按月份汇总',
                        children: loading ? (
                          <Skeleton active paragraph={{ rows: 8 }} />
                        ) : !periodSummaries.length ? (
                          <Empty description="当前没有可显示的记录。请先上传社保文件或调整筛选条件。" />
                        ) : (
                          <Table<PeriodSummaryItem>
                            columns={periodSummaryColumns}
                            dataSource={periodSummaries}
                            rowKey="billing_period"
                            size="small"
                            pagination={paginationConfig}
                            scroll={{ x: 800 }}
                          />
                        ),
                      },
                    ]}
                  />
                </>
              ),
            },
          ]}
        />
      </Card>
    </div>
  );
}
