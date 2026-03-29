import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { normalizeApiError } from '../services/api';
import { fetchPortalRecords, type EmployeeSelfServiceRecord, type EmployeeSelfServiceResult } from '../services/employees';

function formatDateTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat('zh-CN', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date);
}

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
  // period format: "202602" -> "2026年02月"
  if (/^\d{6}$/.test(period)) {
    return `${period.slice(0, 4)}年${period.slice(4, 6)}月`;
  }
  return period;
}

const styles = {
  container: {
    maxWidth: 960,
    margin: '0 auto',
    padding: '32px 24px',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", sans-serif',
  } as React.CSSProperties,
  loadingContainer: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    minHeight: 400,
    color: '#8c8c8c',
    fontSize: 16,
  } as React.CSSProperties,
  errorContainer: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    minHeight: 400,
    color: '#ff4d4f',
    fontSize: 16,
    flexDirection: 'column' as const,
    gap: 12,
  } as React.CSSProperties,
  expiredContainer: {
    display: 'flex',
    flexDirection: 'column' as const,
    justifyContent: 'center',
    alignItems: 'center',
    minHeight: 400,
    gap: 16,
  } as React.CSSProperties,
  expiredIcon: {
    fontSize: 48,
    color: '#faad14',
  } as React.CSSProperties,
  expiredText: {
    fontSize: 18,
    color: '#595959',
    fontWeight: 500,
  } as React.CSSProperties,
  expiredSub: {
    fontSize: 14,
    color: '#8c8c8c',
  } as React.CSSProperties,
  emptyContainer: {
    display: 'flex',
    flexDirection: 'column' as const,
    justifyContent: 'center',
    alignItems: 'center',
    minHeight: 400,
    gap: 12,
    color: '#8c8c8c',
  } as React.CSSProperties,
  emptyTitle: {
    fontSize: 18,
    fontWeight: 500,
    color: '#595959',
  } as React.CSSProperties,
  emptyHint: {
    fontSize: 14,
  } as React.CSSProperties,
  profileCard: {
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    borderRadius: 16,
    padding: '28px 32px',
    color: '#fff',
    marginBottom: 24,
  } as React.CSSProperties,
  profileName: {
    fontSize: 28,
    fontWeight: 700,
    margin: '0 0 8px 0',
  } as React.CSSProperties,
  profileMeta: {
    display: 'flex',
    gap: 24,
    flexWrap: 'wrap' as const,
    fontSize: 14,
    opacity: 0.9,
  } as React.CSSProperties,
  profileMetaItem: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: 2,
  } as React.CSSProperties,
  profileMetaLabel: {
    fontSize: 12,
    opacity: 0.7,
    textTransform: 'uppercase' as const,
    letterSpacing: 0.5,
  } as React.CSSProperties,
  summarySection: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: 16,
    marginBottom: 32,
  } as React.CSSProperties,
  summaryCard: {
    background: '#fff',
    borderRadius: 12,
    padding: '20px 24px',
    border: '1px solid #f0f0f0',
    boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
  } as React.CSSProperties,
  summaryLabel: {
    fontSize: 13,
    color: '#8c8c8c',
    margin: '0 0 6px 0',
  } as React.CSSProperties,
  summaryValue: {
    fontSize: 24,
    fontWeight: 700,
    color: '#262626',
    margin: 0,
  } as React.CSSProperties,
  summaryPeriod: {
    fontSize: 12,
    color: '#bfbfbf',
    marginTop: 4,
  } as React.CSSProperties,
  historySection: {
    marginTop: 8,
  } as React.CSSProperties,
  historyTitle: {
    fontSize: 20,
    fontWeight: 600,
    color: '#262626',
    margin: '0 0 16px 0',
  } as React.CSSProperties,
  recordCard: {
    background: '#fff',
    borderRadius: 12,
    border: '1px solid #f0f0f0',
    marginBottom: 12,
    overflow: 'hidden',
    boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
  } as React.CSSProperties,
  recordHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '16px 20px',
    cursor: 'pointer',
    transition: 'background 0.15s',
    userSelect: 'none' as const,
  } as React.CSSProperties,
  recordHeaderLeft: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: 4,
  } as React.CSSProperties,
  recordPeriod: {
    fontSize: 16,
    fontWeight: 600,
    color: '#262626',
  } as React.CSSProperties,
  recordMeta: {
    fontSize: 13,
    color: '#8c8c8c',
  } as React.CSSProperties,
  recordHeaderRight: {
    display: 'flex',
    alignItems: 'center',
    gap: 16,
  } as React.CSSProperties,
  recordAmount: {
    fontSize: 18,
    fontWeight: 600,
    color: '#262626',
    textAlign: 'right' as const,
  } as React.CSSProperties,
  recordAmountLabel: {
    fontSize: 11,
    color: '#bfbfbf',
    textAlign: 'right' as const,
  } as React.CSSProperties,
  expandIcon: {
    fontSize: 18,
    color: '#8c8c8c',
    transition: 'transform 0.2s',
  } as React.CSSProperties,
  expandedContent: {
    padding: '0 20px 20px',
    borderTop: '1px solid #f5f5f5',
  } as React.CSSProperties,
  detailGrid: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: 20,
    marginTop: 16,
  } as React.CSSProperties,
  detailBlock: {
    background: '#fafafa',
    borderRadius: 10,
    padding: '16px 20px',
  } as React.CSSProperties,
  detailBlockTitle: {
    fontSize: 14,
    fontWeight: 600,
    color: '#434343',
    margin: '0 0 12px 0',
    paddingBottom: 8,
    borderBottom: '1px solid #f0f0f0',
  } as React.CSSProperties,
  detailTable: {
    width: '100%',
    fontSize: 13,
    borderCollapse: 'collapse' as const,
  } as React.CSSProperties,
  detailTh: {
    textAlign: 'left' as const,
    color: '#8c8c8c',
    fontWeight: 400,
    padding: '6px 0',
    fontSize: 12,
  } as React.CSSProperties,
  detailTd: {
    textAlign: 'right' as const,
    color: '#262626',
    fontWeight: 500,
    padding: '6px 0',
  } as React.CSSProperties,
  detailTdSpan: {
    textAlign: 'center' as const,
    color: '#262626',
    fontWeight: 500,
    padding: '6px 0',
  } as React.CSSProperties,
  '@media (max-width: 640px)': {
    detailGrid: {
      gridTemplateColumns: '1fr',
    },
  },
};

function InsuranceDetail({ record }: { record: EmployeeSelfServiceRecord }) {
  const insuranceRows = [
    { label: '养老保险', company: record.pension_company, personal: record.pension_personal },
    { label: '医疗保险', company: record.medical_company, personal: record.medical_personal },
    { label: '失业保险', company: record.unemployment_company, personal: record.unemployment_personal },
    { label: '工伤保险', company: record.injury_company, personal: null },
    { label: '生育保险', company: record.maternity_amount, personal: null },
  ];

  const hasHousingFund =
    record.housing_fund_company !== null ||
    record.housing_fund_personal !== null ||
    record.housing_fund_total !== null;

  return (
    <div style={styles.detailGrid}>
      <div style={styles.detailBlock}>
        <h4 style={styles.detailBlockTitle}>社保明细</h4>
        <table style={styles.detailTable}>
          <thead>
            <tr>
              <th style={styles.detailTh}>险种</th>
              <th style={{ ...styles.detailTh, textAlign: 'right' }}>单位</th>
              <th style={{ ...styles.detailTh, textAlign: 'right' }}>个人</th>
            </tr>
          </thead>
          <tbody>
            {insuranceRows.map((row) => (
              <tr key={row.label}>
                <td style={{ ...styles.detailTd, textAlign: 'left', fontWeight: 400 }}>{row.label}</td>
                <td style={styles.detailTd}>{formatMoney(row.company)}</td>
                <td style={styles.detailTd}>{row.personal !== null ? formatMoney(row.personal) : '-'}</td>
              </tr>
            ))}
            <tr>
              <td style={{ ...styles.detailTd, textAlign: 'left', fontWeight: 400, borderTop: '1px solid #e8e8e8', paddingTop: 8 }}>
                缴费基数
              </td>
              <td colSpan={2} style={{ ...styles.detailTdSpan, borderTop: '1px solid #e8e8e8', paddingTop: 8 }}>
                {formatMoney(record.payment_base)}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div style={styles.detailBlock}>
        <h4 style={styles.detailBlockTitle}>公积金明细</h4>
        {hasHousingFund ? (
          <table style={styles.detailTable}>
            <thead>
              <tr>
                <th style={styles.detailTh}>项目</th>
                <th style={{ ...styles.detailTh, textAlign: 'right' }}>单位</th>
                <th style={{ ...styles.detailTh, textAlign: 'right' }}>个人</th>
                <th style={{ ...styles.detailTh, textAlign: 'right' }}>合计</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td style={{ ...styles.detailTd, textAlign: 'left', fontWeight: 400 }}>住房公积金</td>
                <td style={styles.detailTd}>{formatMoney(record.housing_fund_company)}</td>
                <td style={styles.detailTd}>{formatMoney(record.housing_fund_personal)}</td>
                <td style={styles.detailTd}>{formatMoney(record.housing_fund_total)}</td>
              </tr>
            </tbody>
          </table>
        ) : (
          <p style={{ color: '#bfbfbf', fontSize: 13, margin: 0 }}>暂无公积金数据</p>
        )}
      </div>
    </div>
  );
}

export function EmployeeSelfServicePage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [expired, setExpired] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [data, setData] = useState<EmployeeSelfServiceResult | null>(null);
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());

  const latestRecord = useMemo(() => data?.records[0] ?? null, [data]);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const result = await fetchPortalRecords();
        if (!cancelled) {
          setData(result);
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
    load();
    return () => { cancelled = true; };
  }, []);

  // Token expired: redirect after 2 seconds
  useEffect(() => {
    if (!expired) return;
    const timer = setTimeout(() => {
      navigate('/login', { replace: true });
    }, 2000);
    return () => clearTimeout(timer);
  }, [expired, navigate]);

  function toggleExpand(recordId: string) {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(recordId)) {
        next.delete(recordId);
      } else {
        next.add(recordId);
      }
      return next;
    });
  }

  if (expired) {
    return (
      <div style={styles.container}>
        <div style={styles.expiredContainer}>
          <div style={styles.expiredIcon}>&#9888;</div>
          <p style={styles.expiredText}>登录已过期，请重新验证</p>
          <p style={styles.expiredSub}>2 秒后自动跳转到登录页面...</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div style={styles.container}>
        <div style={styles.loadingContainer}>加载中...</div>
      </div>
    );
  }

  if (errorMessage) {
    return (
      <div style={styles.container}>
        <div style={styles.errorContainer}>
          <p>{errorMessage}</p>
        </div>
      </div>
    );
  }

  if (!data || data.record_count === 0) {
    return (
      <div style={styles.container}>
        {data?.profile && (
          <div style={styles.profileCard}>
            <h1 style={styles.profileName}>{data.profile.person_name}</h1>
            <div style={styles.profileMeta}>
              <div style={styles.profileMetaItem}>
                <span style={styles.profileMetaLabel}>工号</span>
                <span>{data.profile.employee_id || '未匹配'}</span>
              </div>
              <div style={styles.profileMetaItem}>
                <span style={styles.profileMetaLabel}>公司</span>
                <span>{data.profile.company_name || '未登记'}</span>
              </div>
              <div style={styles.profileMetaItem}>
                <span style={styles.profileMetaLabel}>身份证号</span>
                <span>{data.profile.masked_id_number}</span>
              </div>
            </div>
          </div>
        )}
        <div style={styles.emptyContainer}>
          <p style={styles.emptyTitle}>暂无社保缴费记录，请联系 HR 确认</p>
          <p style={styles.emptyHint}>系统未找到与您匹配的社保或公积金导入记录。</p>
        </div>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      {/* Profile Card */}
      <div style={styles.profileCard}>
        <h1 style={styles.profileName}>{data.profile.person_name}</h1>
        <div style={styles.profileMeta}>
          <div style={styles.profileMetaItem}>
            <span style={styles.profileMetaLabel}>工号</span>
            <span>{data.profile.employee_id || '未匹配'}</span>
          </div>
          <div style={styles.profileMetaItem}>
            <span style={styles.profileMetaLabel}>公司</span>
            <span>{data.profile.company_name || '未登记'}</span>
          </div>
          <div style={styles.profileMetaItem}>
            <span style={styles.profileMetaLabel}>身份证号</span>
            <span>{data.profile.masked_id_number}</span>
          </div>
          <div style={styles.profileMetaItem}>
            <span style={styles.profileMetaLabel}>部门</span>
            <span>{data.profile.department || '未登记'}</span>
          </div>
        </div>
      </div>

      {/* Latest Period Summary */}
      {latestRecord && (
        <>
          <h3 style={{ fontSize: 14, color: '#8c8c8c', margin: '0 0 12px 0', fontWeight: 400 }}>
            {formatBillingPeriod(latestRecord.billing_period)} 缴费汇总
          </h3>
          <div style={styles.summarySection}>
            <div style={styles.summaryCard}>
              <p style={styles.summaryLabel}>社保总额</p>
              <p style={styles.summaryValue}>{formatMoney(latestRecord.total_amount)}</p>
            </div>
            <div style={styles.summaryCard}>
              <p style={styles.summaryLabel}>单位合计</p>
              <p style={styles.summaryValue}>{formatMoney(latestRecord.company_total_amount)}</p>
            </div>
            <div style={styles.summaryCard}>
              <p style={styles.summaryLabel}>个人合计</p>
              <p style={styles.summaryValue}>{formatMoney(latestRecord.personal_total_amount)}</p>
            </div>
            {(latestRecord.housing_fund_total !== null) && (
              <div style={styles.summaryCard}>
                <p style={styles.summaryLabel}>公积金合计</p>
                <p style={styles.summaryValue}>{formatMoney(latestRecord.housing_fund_total)}</p>
              </div>
            )}
          </div>
        </>
      )}

      {/* History */}
      <div style={styles.historySection}>
        <h2 style={styles.historyTitle}>缴费历史</h2>
        {data.records.map((record) => {
          const isExpanded = expandedIds.has(record.normalized_record_id);
          return (
            <div key={record.normalized_record_id} style={styles.recordCard}>
              <div
                style={styles.recordHeader}
                onClick={() => toggleExpand(record.normalized_record_id)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    toggleExpand(record.normalized_record_id);
                  }
                }}
              >
                <div style={styles.recordHeaderLeft}>
                  <span style={styles.recordPeriod}>{formatBillingPeriod(record.billing_period)}</span>
                  <span style={styles.recordMeta}>
                    {record.region || '未知地区'} &middot; {record.company_name || '未知公司'}
                  </span>
                </div>
                <div style={styles.recordHeaderRight}>
                  <div>
                    <div style={styles.recordAmount}>{formatMoney(record.total_amount)}</div>
                    <div style={styles.recordAmountLabel}>社保总额</div>
                  </div>
                  <span style={{ ...styles.expandIcon, transform: isExpanded ? 'rotate(180deg)' : 'rotate(0deg)' }}>
                    &#9660;
                  </span>
                </div>
              </div>
              {isExpanded && (
                <div style={styles.expandedContent}>
                  <InsuranceDetail record={record} />
                  <p style={{ fontSize: 12, color: '#bfbfbf', marginTop: 12, marginBottom: 0 }}>
                    来源: {record.source_file_name || '未知'} (第 {record.source_row_number} 行) &middot; 导入时间: {formatDateTime(record.created_at)}
                  </p>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
