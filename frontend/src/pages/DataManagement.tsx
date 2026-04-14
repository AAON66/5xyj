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
  Space,
  Table,
  Tabs,
  Tag,
  Typography,
} from 'antd';
import { FilterOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';

import { ResponsiveFilterDrawer } from '../components/ResponsiveFilterDrawer';
import { useResponsiveViewport } from '../hooks/useResponsiveViewport';
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

interface FilterState {
  regions: string[];
  companies: string[];
  periods: string[];
  matchStatus: string;
  searchText: string;
}

const PAGE_SIZE_OPTIONS = [10, 20, 50];
const ALL_VALUE = '__ALL__';
const EMPTY_FILTERS: FilterState = {
  regions: [],
  companies: [],
  periods: [],
  matchStatus: 'matched',
  searchText: '',
};

function formatAmount(value: number | null): string {
  if (value === null || value === undefined) return '-';
  return value.toFixed(2);
}

function normalizePeriod(period: string | null): string | null {
  if (!period) return null;
  const match = period.trim().match(/(20\d{2})\D*([1-9]|0[1-9]|1[0-2])/);
  if (!match) return null;
  return `${match[1]}-${match[2].padStart(2, '0')}`;
}

function formatPeriod(period: string | null): string {
  const normalized = normalizePeriod(period);
  if (!normalized) return period ?? '-';
  const [year, month] = normalized.split('-');
  return `${year}年${month}月`;
}

function maskIdNumber(id: string | null): string {
  if (!id || id.length < 8) return id ?? '-';
  return `${id.slice(0, 4)}****${id.slice(-4)}`;
}

function countActiveFilters(filters: FilterState): number {
  let count = filters.regions.length + filters.companies.length + filters.periods.length;
  if (filters.matchStatus !== 'matched') count += 1;
  if (filters.searchText.trim()) count += 1;
  return count;
}

function includesSearch(parts: Array<string | null | undefined>, searchText: string): boolean {
  const normalized = searchText.trim().toLowerCase();
  if (!normalized) return true;
  return parts.some((part) => String(part ?? '').toLowerCase().includes(normalized));
}

function getNextMultiValue(currentValues: string[], nextValues: string[], options: string[]): string[] {
  if (!nextValues.includes(ALL_VALUE)) {
    return nextValues;
  }
  const allSelected = currentValues.length === options.length;
  return allSelected ? [] : options;
}

export function DataManagementPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const { isMobile, isTablet } = useResponsiveViewport();
  const isCompactFilter = isMobile || isTablet;

  const appliedFilters = useMemo<FilterState>(() => ({
    regions: searchParams.get('region')?.split(',').filter(Boolean) ?? [],
    companies: searchParams.get('company')?.split(',').filter(Boolean) ?? [],
    periods: searchParams.get('period')?.split(',').filter(Boolean) ?? [],
    matchStatus: searchParams.get('matchStatus') || 'matched',
    searchText: searchParams.get('search') || '',
  }), [searchParams]);

  const activeTab = (searchParams.get('tab') as ActiveTab) || 'detail';
  const summaryMode = (searchParams.get('summaryMode') as SummaryMode) || 'employee';
  const page = Number(searchParams.get('page') || '0');
  const pageSize = Number(searchParams.get('pageSize') || '20');

  const [filterOptions, setFilterOptions] = useState<FilterOptions>({ regions: [], companies: [], periods: [] });
  const [records, setRecords] = useState<NormalizedRecordItem[]>([]);
  const [employeeSummaries, setEmployeeSummaries] = useState<EmployeeSummaryItem[]>([]);
  const [periodSummaries, setPeriodSummaries] = useState<PeriodSummaryItem[]>([]);
  const [totalRecords, setTotalRecords] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedRowKeys, setExpandedRowKeys] = useState<string[]>([]);
  const [filterDrawerOpen, setFilterDrawerOpen] = useState(false);
  const [draftFilters, setDraftFilters] = useState<FilterState>(appliedFilters);

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

  useEffect(() => {
    setDraftFilters(appliedFilters);
  }, [appliedFilters]);

  useEffect(() => {
    let active = true;

    async function loadFilters() {
      try {
        const unscopedOptions = await fetchFilterOptions();
        if (!active) return;

        let scopedCompanies: string[] = unscopedOptions.companies;
        let scopedPeriods: string[] = unscopedOptions.periods;

        if (appliedFilters.regions.length > 0) {
          const regionScoped = await fetchFilterOptions({ regions: appliedFilters.regions });
          if (!active) return;
          scopedCompanies = regionScoped.companies;
          scopedPeriods = regionScoped.periods;

          if (appliedFilters.companies.length > 0) {
            const fullyScoped = await fetchFilterOptions({
              regions: appliedFilters.regions,
              companyNames: appliedFilters.companies,
            });
            if (!active) return;
            scopedPeriods = fullyScoped.periods;
          }
        }

        setFilterOptions({
          regions: unscopedOptions.regions,
          companies: scopedCompanies,
          periods: scopedPeriods,
        });

        const validCompanies = appliedFilters.companies.filter((company) => scopedCompanies.includes(company));
        const validPeriods = appliedFilters.periods.filter((periodValue) => scopedPeriods.includes(periodValue));

        if (
          validCompanies.length !== appliedFilters.companies.length ||
          validPeriods.length !== appliedFilters.periods.length
        ) {
          updateParams({
            company: validCompanies.join(','),
            period: validPeriods.join(','),
            page: '0',
          });
        }
      } catch {
        // Filter loading failure is non-critical.
      }
    }

    void loadFilters();
    return () => {
      active = false;
    };
  }, [appliedFilters.companies, appliedFilters.periods, appliedFilters.regions, updateParams]);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);
    setExpandedRowKeys([]);

    async function loadData() {
      try {
        const filterParams = {
          regions: appliedFilters.regions.length > 0 ? appliedFilters.regions : undefined,
          companyNames: appliedFilters.companies.length > 0 ? appliedFilters.companies : undefined,
          billingPeriods: appliedFilters.periods.length > 0 ? appliedFilters.periods : undefined,
          matchStatus: appliedFilters.matchStatus !== 'all' ? appliedFilters.matchStatus : undefined,
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
            regions: appliedFilters.regions.length > 0 ? appliedFilters.regions : undefined,
            companyNames: appliedFilters.companies.length > 0 ? appliedFilters.companies : undefined,
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
    return () => {
      active = false;
    };
  }, [activeTab, appliedFilters.companies, appliedFilters.matchStatus, appliedFilters.periods, appliedFilters.regions, page, pageSize, summaryMode]);

  const filteredRecords = useMemo(
    () => records.filter((record) => includesSearch([
      record.person_name,
      record.employee_id,
      record.company_name,
      record.id_number,
      record.region,
      record.billing_period,
    ], appliedFilters.searchText)),
    [appliedFilters.searchText, records],
  );

  const filteredEmployeeSummaries = useMemo(
    () => employeeSummaries.filter((item) => includesSearch([
      item.employee_id,
      item.person_name,
      item.company_name,
      item.region,
      item.latest_period,
    ], appliedFilters.searchText)),
    [appliedFilters.searchText, employeeSummaries],
  );

  const filteredPeriodSummaries = useMemo(
    () => periodSummaries.filter((item) => includesSearch([item.billing_period], appliedFilters.searchText)),
    [appliedFilters.searchText, periodSummaries],
  );

  const hasData = activeTab === 'detail'
    ? filteredRecords.length > 0
    : summaryMode === 'employee'
      ? filteredEmployeeSummaries.length > 0
      : filteredPeriodSummaries.length > 0;

  function applyFilters(nextFilters: FilterState) {
    updateParams({
      region: nextFilters.regions.join(','),
      company: nextFilters.companies.join(','),
      period: nextFilters.periods.join(','),
      matchStatus: nextFilters.matchStatus,
      search: nextFilters.searchText.trim(),
      page: '0',
    });
  }

  function openFilterDrawer() {
    setDraftFilters(appliedFilters);
    setFilterDrawerOpen(true);
  }

  function closeFilterDrawer() {
    setDraftFilters(appliedFilters);
    setFilterDrawerOpen(false);
  }

  function applyDraftFilters() {
    applyFilters(draftFilters);
    setFilterDrawerOpen(false);
  }

  function resetFilters() {
    setDraftFilters(EMPTY_FILTERS);
    applyFilters(EMPTY_FILTERS);
    setFilterDrawerOpen(false);
  }

  function handleTabChange(tab: string) {
    updateParams({ tab, page: '0' });
  }

  function handleSummaryModeChange(mode: string) {
    updateParams({ summaryMode: mode, page: '0' });
  }

  const detailColumns: ColumnsType<NormalizedRecordItem> = useMemo(() => [
    { title: '姓名', dataIndex: 'person_name', key: 'person_name', fixed: 'left' as const, width: 80, render: (value: string | null) => value ?? '-' },
    { title: '工号', dataIndex: 'employee_id', key: 'employee_id', width: 80, render: (value: string | null) => value ?? '-' },
    { title: '地区', dataIndex: 'region', key: 'region', width: 70, render: (value: string | null) => value ?? '-' },
    { title: '公司', dataIndex: 'company_name', key: 'company_name', width: 120, ellipsis: true, render: (value: string | null) => value ?? '-' },
    { title: '身份证号', dataIndex: 'id_number', key: 'id_number', width: 140, render: (value: string | null) => maskIdNumber(value) },
    { title: '月份', dataIndex: 'billing_period', key: 'billing_period', width: 80, render: (value: string | null) => formatPeriod(value) },
    { title: '单位合计', dataIndex: 'company_total_amount', key: 'company_total_amount', width: 100, align: 'right' as const, render: (value: number | null) => formatAmount(value) },
    { title: '个人合计', dataIndex: 'personal_total_amount', key: 'personal_total_amount', width: 100, align: 'right' as const, render: (value: number | null) => formatAmount(value) },
    { title: '总额', dataIndex: 'total_amount', key: 'total_amount', width: 100, align: 'right' as const, render: (value: number | null) => formatAmount(value) },
    {
      title: '匹配',
      key: 'match_status',
      width: 70,
      render: (_: unknown, record: NormalizedRecordItem) => (
        record.employee_id ? <Tag color="success">已匹配</Tag> : <Tag color="warning">未匹配</Tag>
      ),
    },
  ], []);

  const expandedRowRender = useCallback((record: NormalizedRecordItem) => (
    <Row gutter={[24, 16]}>
      <Col xs={24} md={12}>
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
      <Col xs={24} md={12}>
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

  const employeeSummaryColumns: ColumnsType<EmployeeSummaryItem> = useMemo(() => [
    { title: '工号', dataIndex: 'employee_id', key: 'employee_id', fixed: 'left' as const, width: 100, render: (value: string | null) => value ?? '-' },
    { title: '姓名', dataIndex: 'person_name', key: 'person_name', render: (value: string | null) => value ?? '-' },
    { title: '公司', dataIndex: 'company_name', key: 'company_name', render: (value: string | null) => value ?? '-' },
    { title: '地区', dataIndex: 'region', key: 'region', render: (value: string | null) => value ?? '-' },
    { title: '最新月份', dataIndex: 'latest_period', key: 'latest_period', render: (value: string | null) => formatPeriod(value) },
    { title: '单位合计', dataIndex: 'company_total', key: 'company_total', align: 'right' as const, render: (value: number | null) => formatAmount(value) },
    { title: '个人合计', dataIndex: 'personal_total', key: 'personal_total', align: 'right' as const, render: (value: number | null) => formatAmount(value) },
    { title: '总额', dataIndex: 'total', key: 'total', align: 'right' as const, render: (value: number | null) => formatAmount(value) },
  ], []);

  const periodSummaryColumns: ColumnsType<PeriodSummaryItem> = useMemo(() => [
    { title: '月份', dataIndex: 'billing_period', key: 'billing_period', fixed: 'left' as const, width: 100, render: (value: string) => formatPeriod(value) },
    { title: '总人数', dataIndex: 'total_count', key: 'total_count' },
    { title: '单位合计', dataIndex: 'company_total', key: 'company_total', align: 'right' as const, render: (value: number | null) => formatAmount(value) },
    { title: '个人合计', dataIndex: 'personal_total', key: 'personal_total', align: 'right' as const, render: (value: number | null) => formatAmount(value) },
    { title: '总额', dataIndex: 'total', key: 'total', align: 'right' as const, render: (value: number | null) => formatAmount(value) },
    { title: '平均个人', dataIndex: 'avg_personal', key: 'avg_personal', align: 'right' as const, render: (value: number | null) => formatAmount(value) },
    { title: '平均单位', dataIndex: 'avg_company', key: 'avg_company', align: 'right' as const, render: (value: number | null) => formatAmount(value) },
  ], []);

  const paginationConfig = useMemo(() => ({
    current: page + 1,
    pageSize,
    total: totalRecords,
    showSizeChanger: true,
    pageSizeOptions: PAGE_SIZE_OPTIONS.map(String),
    showTotal: (total: number) => appliedFilters.searchText.trim()
      ? `本页匹配 ${activeTab === 'detail'
        ? filteredRecords.length
        : summaryMode === 'employee'
          ? filteredEmployeeSummaries.length
          : filteredPeriodSummaries.length} 条 / 共 ${total} 条记录`
      : `共 ${total} 条记录`,
    onChange: (newPage: number, newPageSize: number) => {
      if (newPageSize !== pageSize) {
        updateParams({ pageSize: String(newPageSize), page: '0' });
      } else {
        updateParams({ page: String(newPage - 1) });
      }
    },
  }), [
    activeTab,
    appliedFilters.searchText,
    filteredEmployeeSummaries.length,
    filteredPeriodSummaries.length,
    filteredRecords.length,
    page,
    pageSize,
    summaryMode,
    totalRecords,
    updateParams,
  ]);

  const activeFilterCount = countActiveFilters(appliedFilters);

  const filterFields = (
    <Row gutter={[16, 16]} align="middle">
      <Col xs={24} sm={12} md={12}>
        <Input.Search
          placeholder="搜索姓名、工号、公司或身份证号"
          value={draftFilters.searchText}
          onChange={(event) => setDraftFilters((current) => ({ ...current, searchText: event.target.value }))}
          onSearch={() => {
            if (!isCompactFilter) {
              applyDraftFilters();
            }
          }}
          allowClear
        />
      </Col>
      <Col xs={24} sm={12} md={6}>
        <Select
          mode="multiple"
          showSearch
          allowClear
          maxTagCount={2}
          maxTagPlaceholder={(omitted) => `+${omitted.length}...`}
          placeholder="请选择地区"
          value={draftFilters.regions.length > 0 ? draftFilters.regions : undefined}
          onChange={(values) => setDraftFilters((current) => ({
            ...current,
            regions: getNextMultiValue(current.regions, values, filterOptions.regions),
            companies: [],
            periods: [],
          }))}
          style={{ width: '100%' }}
          options={[
            { label: '全选', value: ALL_VALUE, style: { fontWeight: 600 } },
            ...filterOptions.regions.map((region) => ({ label: region, value: region })),
          ]}
        />
      </Col>
      <Col xs={24} sm={12} md={6}>
        <Select
          mode="multiple"
          showSearch
          allowClear
          maxTagCount={2}
          maxTagPlaceholder={(omitted) => `+${omitted.length}...`}
          placeholder="请选择公司"
          value={draftFilters.companies.length > 0 ? draftFilters.companies : undefined}
          onChange={(values) => setDraftFilters((current) => ({
            ...current,
            companies: getNextMultiValue(current.companies, values, filterOptions.companies),
            periods: [],
          }))}
          style={{ width: '100%' }}
          options={[
            { label: '全选', value: ALL_VALUE, style: { fontWeight: 600 } },
            ...filterOptions.companies.map((company) => ({ label: company, value: company })),
          ]}
        />
      </Col>
      <Col xs={24} sm={12} md={6}>
        <Select
          mode="multiple"
          showSearch
          allowClear
          maxTagCount={2}
          maxTagPlaceholder={(omitted) => `+${omitted.length}...`}
          placeholder="请选择账期"
          value={draftFilters.periods.length > 0 ? draftFilters.periods : undefined}
          onChange={(values) => setDraftFilters((current) => ({
            ...current,
            periods: getNextMultiValue(current.periods, values, filterOptions.periods),
          }))}
          style={{ width: '100%' }}
          options={[
            { label: '全选', value: ALL_VALUE, style: { fontWeight: 600 } },
            ...filterOptions.periods.map((periodValue) => ({ label: formatPeriod(periodValue), value: periodValue })),
          ]}
        />
      </Col>
      <Col xs={24} sm={12} md={4}>
        <Select
          value={draftFilters.matchStatus}
          onChange={(value) => setDraftFilters((current) => ({ ...current, matchStatus: value }))}
          style={{ width: '100%' }}
          options={[
            { label: '全部', value: 'all' },
            { label: '已匹配', value: 'matched' },
            { label: '未匹配', value: 'unmatched' },
          ]}
        />
      </Col>
      {isCompactFilter ? null : (
        <Col xs={24}>
          <Space wrap>
            <Button type="primary" onClick={applyDraftFilters}>查询</Button>
            <Button onClick={resetFilters}>重置</Button>
          </Space>
        </Col>
      )}
    </Row>
  );

  return (
    <div>
      <Row justify="space-between" align="middle" style={{ marginBottom: 16, gap: 12 }}>
        <Col>
          <Title level={4} style={{ margin: 0 }}>数据管理</Title>
        </Col>
        {isCompactFilter ? (
          <Col>
            <Button icon={<FilterOutlined />} onClick={openFilterDrawer}>
              {activeFilterCount > 0 ? `筛选 (${activeFilterCount})` : '筛选'}
            </Button>
          </Col>
        ) : null}
      </Row>

      {isCompactFilter ? (
        <ResponsiveFilterDrawer
          title="筛选条件"
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
                  dataSource={filteredRecords}
                  rowKey="id"
                  size="small"
                  pagination={paginationConfig}
                  scroll={{ x: 1100 }}
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
                      ) : !filteredEmployeeSummaries.length ? (
                        <Empty description="当前没有可显示的记录。请先上传社保文件或调整筛选条件。" />
                      ) : (
                        <Table<EmployeeSummaryItem>
                          columns={employeeSummaryColumns}
                          dataSource={filteredEmployeeSummaries}
                          rowKey={(item, index) => `${item.employee_id ?? ''}-${item.person_name ?? ''}-${index}`}
                          size="small"
                          pagination={paginationConfig}
                          scroll={{ x: 900 }}
                        />
                      ),
                    },
                    {
                      key: 'period',
                      label: '按月份汇总',
                      children: loading ? (
                        <Skeleton active paragraph={{ rows: 8 }} />
                      ) : !filteredPeriodSummaries.length ? (
                        <Empty description="当前没有可显示的记录。请先上传社保文件或调整筛选条件。" />
                      ) : (
                        <Table<PeriodSummaryItem>
                          columns={periodSummaryColumns}
                          dataSource={filteredPeriodSummaries}
                          rowKey="billing_period"
                          size="small"
                          pagination={paginationConfig}
                          scroll={{ x: 900 }}
                        />
                      ),
                    },
                  ]}
                />
              ),
            },
          ]}
        />
      </Card>
    </div>
  );
}
