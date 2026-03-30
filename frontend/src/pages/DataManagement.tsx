import { useCallback, useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';

import { PageContainer, SectionState } from '../components';
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

type ActiveTab = 'detail' | 'summary';
type SummaryMode = 'employee' | 'period';

const PAGE_SIZE_OPTIONS = [10, 20, 50] as const;

function formatAmount(value: number | null): string {
  if (value === null || value === undefined) return '-';
  return value.toFixed(2);
}

function formatPeriod(period: string | null): string {
  if (!period || period.length < 6) return period ?? '-';
  return `${period.slice(0, 4)}年${period.slice(4)}月`;
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
  const [expandedRowId, setExpandedRowId] = useState<string | null>(null);

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
        // Always fetch unscoped for regions
        const unscopedOptions = await fetchFilterOptions();
        if (!active) return;

        let companies: string[] = unscopedOptions.companies;
        let periods: string[] = unscopedOptions.periods;

        // If region is set, fetch companies scoped by region
        if (region) {
          const regionScoped = await fetchFilterOptions({ region });
          if (!active) return;
          companies = regionScoped.companies;
          periods = regionScoped.periods;

          // If company is also set, fetch periods scoped by region+company
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

        // Stale param handling: if current company/period not in new options, clear them
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
    setExpandedRowId(null);

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

  const totalPages = useMemo(
    () => Math.max(1, Math.ceil(totalRecords / pageSize)),
    [totalRecords, pageSize],
  );

  function handleRegionChange(newRegion: string) {
    updateParams({ region: newRegion, company: '', period: '', page: '0' });
  }

  function handleCompanyChange(newCompany: string) {
    updateParams({ company: newCompany, period: '', page: '0' });
    // Fetch periods scoped by region+company
    if (region && newCompany) {
      fetchFilterOptions({ region, companyName: newCompany })
        .then((opts) => setFilterOptions((prev) => ({ ...prev, periods: opts.periods })))
        .catch(() => {});
    }
  }

  function handlePeriodChange(newPeriod: string) {
    updateParams({ period: newPeriod, page: '0' });
  }

  function handleTabChange(tab: ActiveTab) {
    updateParams({ tab, page: '0' });
  }

  function handleSummaryModeChange(mode: SummaryMode) {
    updateParams({ summaryMode: mode, page: '0' });
  }

  function handlePageSizeChange(newSize: number) {
    updateParams({ pageSize: String(newSize), page: '0' });
  }

  function handleResetFilters() {
    updateParams({ region: '', company: '', period: '', page: '0' });
  }

  function renderDetailTable() {
    return (
      <>
        <div className="preview-table-wrap">
          <table className="preview-table">
            <thead>
              <tr>
                <th style={{ width: 80 }}>姓名</th>
                <th style={{ width: 80 }}>工号</th>
                <th style={{ width: 70 }}>地区</th>
                <th style={{ width: 120 }}>公司</th>
                <th style={{ width: 80 }}>月份</th>
                <th style={{ width: 90, textAlign: 'right' }}>单位合计</th>
                <th style={{ width: 90, textAlign: 'right' }}>个人合计</th>
                <th style={{ width: 90, textAlign: 'right' }}>总额</th>
                <th style={{ width: 60 }}>操作</th>
              </tr>
            </thead>
            <tbody>
              {records.map((record) => (
                <>
                  <tr key={record.id}>
                    <td>{record.person_name ?? '-'}</td>
                    <td>{record.employee_id ?? '-'}</td>
                    <td>{record.region ?? '-'}</td>
                    <td>{record.company_name ?? '-'}</td>
                    <td>{formatPeriod(record.billing_period)}</td>
                    <td style={{ textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>{formatAmount(record.company_total_amount)}</td>
                    <td style={{ textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>{formatAmount(record.personal_total_amount)}</td>
                    <td style={{ textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>{formatAmount(record.total_amount)}</td>
                    <td>
                      <button
                        type="button"
                        className="button button--ghost"
                        style={{ padding: '4px 8px', fontSize: '0.85rem' }}
                        onClick={() => setExpandedRowId(expandedRowId === record.id ? null : record.id)}
                      >
                        {expandedRowId === record.id ? '收起详情' : '展开详情'}
                      </button>
                    </td>
                  </tr>
                  {expandedRowId === record.id && (
                    <tr key={`${record.id}-expand`} className="detail-expand-row">
                      <td colSpan={9}>
                        <div className="detail-expand-grid">
                          <div>
                            <h4>单位各险种</h4>
                            <dl>
                              <dt>养老保险</dt>
                              <dd>{formatAmount(record.pension_company)}</dd>
                              <dt>医疗保险</dt>
                              <dd>{formatAmount(record.medical_company)}</dd>
                              <dt>医疗(含生育)</dt>
                              <dd>{formatAmount(record.medical_maternity_company)}</dd>
                              <dt>失业保险</dt>
                              <dd>{formatAmount(record.unemployment_company)}</dd>
                              <dt>工伤保险</dt>
                              <dd>{formatAmount(record.injury_company)}</dd>
                              <dt>补充医疗</dt>
                              <dd>{formatAmount(record.supplementary_medical_company)}</dd>
                              <dt>补充养老</dt>
                              <dd>{formatAmount(record.supplementary_pension_company)}</dd>
                              <dt>公积金(单位)</dt>
                              <dd>{formatAmount(record.housing_fund_company)}</dd>
                            </dl>
                          </div>
                          <div>
                            <h4>个人各险种</h4>
                            <dl>
                              <dt>养老保险</dt>
                              <dd>{formatAmount(record.pension_personal)}</dd>
                              <dt>医疗保险</dt>
                              <dd>{formatAmount(record.medical_personal)}</dd>
                              <dt>失业保险</dt>
                              <dd>{formatAmount(record.unemployment_personal)}</dd>
                              <dt>大额医疗</dt>
                              <dd>{formatAmount(record.large_medical_personal)}</dd>
                              <dt>公积金(个人)</dt>
                              <dd>{formatAmount(record.housing_fund_personal)}</dd>
                              <dt>缴费基数</dt>
                              <dd>{formatAmount(record.payment_base)}</dd>
                            </dl>
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                </>
              ))}
            </tbody>
          </table>
        </div>
        {renderPagination()}
      </>
    );
  }

  function renderEmployeeSummaryTable() {
    return (
      <>
        <div className="preview-table-wrap">
          <table className="preview-table">
            <thead>
              <tr>
                <th>工号</th>
                <th>姓名</th>
                <th>公司</th>
                <th>地区</th>
                <th>最新月份</th>
                <th style={{ textAlign: 'right' }}>单位合计</th>
                <th style={{ textAlign: 'right' }}>个人合计</th>
                <th style={{ textAlign: 'right' }}>总额</th>
              </tr>
            </thead>
            <tbody>
              {employeeSummaries.map((item, idx) => (
                <tr key={`${item.employee_id ?? ''}-${item.person_name ?? ''}-${idx}`}>
                  <td>{item.employee_id ?? '-'}</td>
                  <td>{item.person_name ?? '-'}</td>
                  <td>{item.company_name ?? '-'}</td>
                  <td>{item.region ?? '-'}</td>
                  <td>{formatPeriod(item.latest_period)}</td>
                  <td style={{ textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>{formatAmount(item.company_total)}</td>
                  <td style={{ textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>{formatAmount(item.personal_total)}</td>
                  <td style={{ textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>{formatAmount(item.total)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {renderPagination()}
      </>
    );
  }

  function renderPeriodSummaryTable() {
    return (
      <>
        <div className="preview-table-wrap">
          <table className="preview-table">
            <thead>
              <tr>
                <th>月份</th>
                <th>总人数</th>
                <th style={{ textAlign: 'right' }}>单位合计</th>
                <th style={{ textAlign: 'right' }}>个人合计</th>
                <th style={{ textAlign: 'right' }}>总额</th>
                <th style={{ textAlign: 'right' }}>平均个人</th>
                <th style={{ textAlign: 'right' }}>平均单位</th>
              </tr>
            </thead>
            <tbody>
              {periodSummaries.map((item) => (
                <tr key={item.billing_period}>
                  <td>{formatPeriod(item.billing_period)}</td>
                  <td>{item.total_count}</td>
                  <td style={{ textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>{formatAmount(item.company_total)}</td>
                  <td style={{ textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>{formatAmount(item.personal_total)}</td>
                  <td style={{ textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>{formatAmount(item.total)}</td>
                  <td style={{ textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>{formatAmount(item.avg_personal)}</td>
                  <td style={{ textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>{formatAmount(item.avg_company)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {renderPagination()}
      </>
    );
  }

  function renderPagination() {
    return (
      <div className="employee-pagination">
        <div className="employee-pagination__summary">
          {totalRecords > 0
            ? `第${page + 1}页 / 共${totalPages}页, 共${totalRecords}条记录`
            : '暂无记录'}
        </div>
        <div className="button-row employee-pagination__actions">
          <button
            type="button"
            className="button button--ghost"
            onClick={() => updateParams({ page: String(Math.max(0, page - 1)) })}
            disabled={loading || page <= 0}
          >
            上一页
          </button>
          <label className="form-field" style={{ margin: 0, minWidth: 'auto' }}>
            <select
              value={String(pageSize)}
              onChange={(e) => handlePageSizeChange(Number(e.target.value))}
              style={{ padding: '4px 8px' }}
            >
              {PAGE_SIZE_OPTIONS.map((v) => (
                <option key={v} value={v}>{v} 条/页</option>
              ))}
            </select>
          </label>
          <button
            type="button"
            className="button button--ghost"
            onClick={() => updateParams({ page: String(page + 1) })}
            disabled={loading || page + 1 >= totalPages}
          >
            下一页
          </button>
        </div>
      </div>
    );
  }

  const hasData = activeTab === 'detail'
    ? records.length > 0
    : summaryMode === 'employee'
      ? employeeSummaries.length > 0
      : periodSummaries.length > 0;

  return (
    <PageContainer
      eyebrow="Data Management"
      title="社保数据管理"
      description="按地区、公司和月份筛选全量社保明细，查看全员汇总数据。"
    >
      {/* Filter bar */}
      <div className="employee-toolbar">
        <label className="form-field employee-toolbar__toggle">
          <span>地区</span>
          <select value={region} onChange={(e) => handleRegionChange(e.target.value)}>
            <option value="">全部地区</option>
            {filterOptions.regions.map((r) => (
              <option key={r} value={r}>{r}</option>
            ))}
          </select>
        </label>
        <label className="form-field employee-toolbar__toggle">
          <span>公司</span>
          <select value={company} onChange={(e) => handleCompanyChange(e.target.value)}>
            <option value="">全部公司</option>
            {filterOptions.companies.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </label>
        <label className="form-field employee-toolbar__toggle">
          <span>月份</span>
          <select value={period} onChange={(e) => handlePeriodChange(e.target.value)}>
            <option value="">全部月份</option>
            {filterOptions.periods.map((p) => (
              <option key={p} value={p}>{formatPeriod(p)}</option>
            ))}
          </select>
        </label>
        <button type="button" className="button button--ghost" onClick={handleResetFilters}>
          重置筛选
        </button>
      </div>

      {/* Primary tab bar */}
      <div className="tab-bar" style={{ marginBottom: 16 }}>
        <button
          type="button"
          className={`tab-bar__item${activeTab === 'detail' ? ' is-active' : ''}`}
          onClick={() => handleTabChange('detail')}
        >
          明细数据
        </button>
        <button
          type="button"
          className={`tab-bar__item${activeTab === 'summary' ? ' is-active' : ''}`}
          onClick={() => handleTabChange('summary')}
        >
          全员汇总
        </button>
      </div>

      {/* Secondary tab bar for summary mode */}
      {activeTab === 'summary' && (
        <div className="tab-bar" style={{ marginBottom: 16 }}>
          <button
            type="button"
            className={`tab-bar__item${summaryMode === 'employee' ? ' is-active' : ''}`}
            onClick={() => handleSummaryModeChange('employee')}
          >
            按员工汇总
          </button>
          <button
            type="button"
            className={`tab-bar__item${summaryMode === 'period' ? ' is-active' : ''}`}
            onClick={() => handleSummaryModeChange('period')}
          >
            按月份汇总
          </button>
        </div>
      )}

      {/* Content */}
      <section className="panel-card">
        {loading ? (
          <SectionState title="正在加载社保数据" message="系统正在读取当前筛选条件下的社保记录。" />
        ) : error ? (
          <SectionState tone="error" title="数据加载失败" message="社保记录暂时无法读取，请刷新页面或联系管理员检查后端服务。" />
        ) : !hasData ? (
          <SectionState title="暂无匹配记录" message="当前筛选条件下没有可展示的社保记录，请调整地区、公司或月份后重试。" />
        ) : activeTab === 'detail' ? (
          renderDetailTable()
        ) : summaryMode === 'employee' ? (
          renderEmployeeSummaryTable()
        ) : (
          renderPeriodSummaryTable()
        )}
      </section>
    </PageContainer>
  );
}
