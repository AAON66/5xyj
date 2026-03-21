import { useEffect, useMemo, useState, type FormEvent } from 'react';

import { PageContainer, SectionState, SurfaceNotice } from '../components';
import { fetchEmployeeMasters, importEmployeeMaster, type EmployeeImportResult, type EmployeeMasterItem } from '../services/employees';

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

export function EmployeesPage() {
  const [employees, setEmployees] = useState<EmployeeMasterItem[]>([]);
  const [query, setQuery] = useState('');
  const [draftQuery, setDraftQuery] = useState('');
  const [activeOnly, setActiveOnly] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(true);
  const [importing, setImporting] = useState(false);
  const [pageError, setPageError] = useState<string | null>(null);
  const [importResult, setImportResult] = useState<EmployeeImportResult | null>(null);

  useEffect(() => {
    let active = true;

    async function loadEmployees() {
      try {
        const result = await fetchEmployeeMasters({ query, activeOnly });
        if (!active) {
          return;
        }
        setEmployees(result.items);
        setPageError(null);
      } catch {
        if (active) {
          setPageError('员工主档列表暂时无法读取，请稍后重试。');
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void loadEmployees();
    return () => {
      active = false;
    };
  }, [query, activeOnly]);

  const summary = useMemo(
    () => ({
      total: employees.length,
      active: employees.filter((item) => item.active).length,
      companies: new Set(employees.map((item) => item.company_name).filter(Boolean)).size,
    }),
    [employees],
  );

  async function reloadEmployees(nextQuery = query, nextActiveOnly = activeOnly) {
    const result = await fetchEmployeeMasters({ query: nextQuery, activeOnly: nextActiveOnly });
    setEmployees(result.items);
  }

  async function handleImport() {
    if (!selectedFile) {
      return;
    }
    setImporting(true);
    setPageError(null);
    try {
      const result = await importEmployeeMaster(selectedFile);
      setImportResult(result);
      setSelectedFile(null);
      await reloadEmployees();
    } catch {
      setPageError('员工主档导入失败，请检查文件格式和必要字段后重试。');
    } finally {
      setImporting(false);
    }
  }

  function handleSearchSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setQuery(draftQuery.trim());
  }

  return (
    <PageContainer
      eyebrow="Employees"
      title="员工主档导入与浏览"
      description="上传员工主档文件，统一写入匹配基准数据，并按工号、姓名、证件号或公司快速检索当前可用主档。"
      actions={
        <div className="button-row">
          <button type="button" className="button button--primary" onClick={() => void handleImport()} disabled={!selectedFile || importing}>
            {importing ? '导入中...' : '导入主档文件'}
          </button>
        </div>
      }
    >
      {importResult ? (
        <SurfaceNotice
          tone="success"
          title="导入完成"
          message={`文件 ${importResult.file_name} 已导入 ${importResult.imported_count} 条，新增 ${importResult.created_count} 条，更新 ${importResult.updated_count} 条。`}
        />
      ) : null}
      {pageError ? <SurfaceNotice tone="error" title="页面状态异常" message={pageError} /> : null}

      <div className="panel-grid panel-grid--two employee-page-grid">
        <section className="panel-card employee-upload-card">
          <div>
            <span className="panel-label">主档导入</span>
            <strong>支持 CSV / XLSX</strong>
            <p>必填字段至少包含工号和姓名，其它字段会在导入时按表头别名自动归并。</p>
          </div>
          <label className="form-field">
            <span>选择文件</span>
            <input
              type="file"
              accept=".csv,.xlsx"
              onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
            />
          </label>
          <div className="status-item">
            <strong>{selectedFile ? selectedFile.name : '尚未选择文件'}</strong>
            <div>{selectedFile ? '准备导入员工主档。' : '请上传包含工号和姓名的主档文件。'}</div>
          </div>
        </section>

        <section className="panel-card employee-summary-grid">
          <article className="status-item">
            <strong>{summary.total}</strong>
            <div>当前主档记录</div>
          </article>
          <article className="status-item">
            <strong>{summary.active}</strong>
            <div>在职可匹配</div>
          </article>
          <article className="status-item">
            <strong>{summary.companies}</strong>
            <div>覆盖公司</div>
          </article>
        </section>
      </div>

      <section className="panel-card employee-list-card">
        <div className="section-heading">
          <div>
            <span className="panel-label">主档列表</span>
            <h2>按工号和公司浏览</h2>
          </div>
        </div>

        <form className="employee-toolbar" onSubmit={handleSearchSubmit}>
          <label className="form-field employee-toolbar__search">
            <span>搜索关键字</span>
            <input value={draftQuery} onChange={(event) => setDraftQuery(event.target.value)} placeholder="工号 / 姓名 / 身份证号 / 公司" />
          </label>
          <label className="form-field employee-toolbar__toggle">
            <span>筛选范围</span>
            <select value={activeOnly ? 'active' : 'all'} onChange={(event) => { setLoading(true); setActiveOnly(event.target.value === 'active'); }}>
              <option value="all">全部主档</option>
              <option value="active">仅在职主档</option>
            </select>
          </label>
          <button type="submit" className="button button--ghost">
            搜索主档
          </button>
        </form>

        {loading ? (
          <SectionState title="正在加载员工主档" message="系统正在同步当前可用于匹配的员工主档记录。" />
        ) : employees.length ? (
          <div className="preview-table-wrap">
            <table className="preview-table">
              <thead>
                <tr>
                  <th>工号</th>
                  <th>姓名</th>
                  <th>身份证号</th>
                  <th>公司</th>
                  <th>部门</th>
                  <th>状态</th>
                  <th>写入时间</th>
                </tr>
              </thead>
              <tbody>
                {employees.map((employee) => (
                  <tr key={employee.id}>
                    <td>{employee.employee_id}</td>
                    <td>{employee.person_name}</td>
                    <td>{employee.id_number ?? '-'}</td>
                    <td>{employee.company_name ?? '-'}</td>
                    <td>{employee.department ?? '-'}</td>
                    <td>
                      <span className={`dashboard-pill ${employee.active ? 'dashboard-pill--ok' : 'dashboard-pill--warn'}`}>
                        {employee.active ? '在职' : '停用'}
                      </span>
                    </td>
                    <td>{formatDateTime(employee.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <SectionState title="暂无员工主档" message="先导入员工主档文件，后续批次匹配才会进入可执行状态。" />
        )}
      </section>
    </PageContainer>
  );
}
