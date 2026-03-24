import { useMemo, useState, type FormEvent } from 'react';
import { Link } from 'react-router-dom';

import { normalizeApiError } from '../services/api';
import { queryEmployeeSelfService, type EmployeeSelfServiceRecord, type EmployeeSelfServiceResult } from '../services/employees';

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

function batchStatusLabel(value: string): string {
  switch (value) {
    case 'exported':
      return '已导出';
    case 'matched':
      return '已匹配';
    case 'validated':
      return '已校验';
    case 'normalized':
      return '已标准化';
    case 'failed':
      return '失败';
    case 'blocked':
      return '阻塞';
    default:
      return value;
  }
}

function periodLabel(record: EmployeeSelfServiceRecord): string {
  return record.billing_period || [record.period_start, record.period_end].filter(Boolean).join(' - ') || '未提供所属期';
}

export function EmployeeSelfServicePage() {
  const [personName, setPersonName] = useState('');
  const [idNumber, setIdNumber] = useState('');
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [result, setResult] = useState<EmployeeSelfServiceResult | null>(null);

  const latestRecord = useMemo(() => result?.records[0] ?? null, [result]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setErrorMessage(null);
    try {
      const payload = await queryEmployeeSelfService({
        person_name: personName.trim(),
        id_number: idNumber.trim(),
      });
      setResult(payload);
    } catch (error) {
      setResult(null);
      setErrorMessage(normalizeApiError(error).message || '暂时无法查询到该员工的社保公积金记录。');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="self-service-shell">
      <section className="self-service-hero">
        <div className="self-service-hero__copy">
          <p className="portal-kicker">Employee Self Service</p>
          <h1>员工社保公积金查询</h1>
          <p>
            无需登录。输入姓名和身份证号后，系统会返回最近的社保公积金记录摘要，便于员工自助核对。
          </p>
          <div className="portal-actions">
            <Link className="portal-button portal-button--ghost" to="/">
              返回系统门户
            </Link>
            <Link className="portal-button portal-button--ghost" to="/workspace/hr">
              前往 HR 工作台
            </Link>
          </div>
        </div>
        <form className="self-service-form" onSubmit={handleSubmit}>
          <label>
            <span>姓名</span>
            <input value={personName} onChange={(event) => setPersonName(event.target.value)} placeholder="请输入姓名" />
          </label>
          <label>
            <span>身份证号</span>
            <input value={idNumber} onChange={(event) => setIdNumber(event.target.value)} placeholder="请输入身份证号" />
          </label>
          <button type="submit" disabled={loading || !personName.trim() || !idNumber.trim()}>
            {loading ? '查询中...' : '开始查询'}
          </button>
          <small>当前入口只做查询，不做登录或身份验证。</small>
        </form>
      </section>

      {errorMessage ? <div className="self-service-notice self-service-notice--error">{errorMessage}</div> : null}

      {result ? (
        <div className="self-service-results">
          <section className="self-service-profile">
            <div>
              <p className="portal-kicker">Profile</p>
              <h2>{result.profile.person_name}</h2>
              <p>
                {result.profile.company_name || '未登记主体'} · {result.profile.masked_id_number || '未登记证件号'}
              </p>
            </div>
            <dl>
              <div>
                <dt>员工工号</dt>
                <dd>{result.profile.employee_id || '未匹配'}</dd>
              </div>
              <div>
                <dt>数据来源</dt>
                <dd>{result.matched_employee_master ? '员工主档 + 标准化记录' : '标准化记录'}</dd>
              </div>
              <div>
                <dt>部门</dt>
                <dd>{result.profile.department || '未登记'}</dd>
              </div>
              <div>
                <dt>状态</dt>
                <dd>{result.profile.active == null ? '未知' : result.profile.active ? '在职' : '停用'}</dd>
              </div>
            </dl>
          </section>

          {latestRecord ? (
            <section className="self-service-highlight">
              <div>
                <p className="portal-kicker">Latest Record</p>
                <h2>{periodLabel(latestRecord)}</h2>
                <p>
                  {latestRecord.company_name || '未登记公司'} · {latestRecord.region || '未识别地区'} · {batchStatusLabel(latestRecord.batch_status)}
                </p>
              </div>
              <div className="self-service-highlight__metrics">
                <div>
                  <span>社保个人</span>
                  <strong>{formatMoney(latestRecord.personal_total_amount)}</strong>
                </div>
                <div>
                  <span>社保单位</span>
                  <strong>{formatMoney(latestRecord.company_total_amount)}</strong>
                </div>
                <div>
                  <span>公积金合计</span>
                  <strong>{formatMoney(latestRecord.housing_fund_total)}</strong>
                </div>
              </div>
            </section>
          ) : null}

          <section className="self-service-records">
            <div className="self-service-records__heading">
              <div>
                <p className="portal-kicker">Records</p>
                <h2>最近查询记录</h2>
              </div>
              <strong>{result.record_count} 条</strong>
            </div>
            <div className="self-service-records__list">
              {result.records.map((record) => (
                <article key={record.normalized_record_id} className="self-service-record">
                  <header>
                    <div>
                      <strong>{periodLabel(record)}</strong>
                      <span>
                        {record.company_name || '未登记公司'} · {record.region || '未识别地区'}
                      </span>
                    </div>
                    <span className="self-service-badge">{batchStatusLabel(record.batch_status)}</span>
                  </header>
                  <div className="self-service-record__grid">
                    <div>
                      <label>社保个人合计</label>
                      <strong>{formatMoney(record.personal_total_amount)}</strong>
                    </div>
                    <div>
                      <label>社保单位合计</label>
                      <strong>{formatMoney(record.company_total_amount)}</strong>
                    </div>
                    <div>
                      <label>社保总额</label>
                      <strong>{formatMoney(record.total_amount)}</strong>
                    </div>
                    <div>
                      <label>公积金个人</label>
                      <strong>{formatMoney(record.housing_fund_personal)}</strong>
                    </div>
                    <div>
                      <label>公积金单位</label>
                      <strong>{formatMoney(record.housing_fund_company)}</strong>
                    </div>
                    <div>
                      <label>公积金合计</label>
                      <strong>{formatMoney(record.housing_fund_total)}</strong>
                    </div>
                  </div>
                  <footer>
                    <span>{record.source_file_name || '未知来源文件'}</span>
                    <span>第 {record.source_row_number} 行</span>
                    <span>{formatDateTime(record.created_at)}</span>
                  </footer>
                </article>
              ))}
            </div>
          </section>
        </div>
      ) : (
        <div className="self-service-empty">
          <strong>输入姓名和身份证号后开始查询</strong>
          <span>当前入口只做查询，不做登录校验，也不会生成任何会话。</span>
        </div>
      )}
    </div>
  );
}
