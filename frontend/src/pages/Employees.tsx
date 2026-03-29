import { useEffect, useMemo, useState, type FormEvent } from 'react';

import { Link } from 'react-router-dom';

import { PageContainer, SectionState, SurfaceNotice } from '../components';
import { normalizeApiError } from '../services/api';
import {
  deleteEmployeeMasterAudit,
  deleteEmployeeMaster,
  fetchCompanies,
  fetchEmployeeMasterAudits,
  fetchEmployeeMasters,
  fetchRegions,
  importEmployeeMaster,
  updateEmployeeMaster,
  updateEmployeeMasterStatus,
  type EmployeeImportResult,
  type EmployeeMasterAuditItem,
  type EmployeeMasterItem,
  type EmployeeMasterUpdateInput,
} from '../services/employees';

interface EmployeeFormState {
  person_name: string;
  id_number: string;
  company_name: string;
  department: string;
  region: string;
  active: boolean;
}

const EMPTY_FORM: EmployeeFormState = {
  person_name: '',
  id_number: '',
  company_name: '',
  department: '',
  region: '',
  active: true,
};

const PAGE_SIZE_OPTIONS = [10, 20, 50] as const;

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

function describeAuditAction(action: string): string {
  switch (action) {
    case 'import_create':
      return '导入新增';
    case 'import_update':
      return '导入更新';
    case 'manual_create':
      return '人工新增';
    case 'manual_update':
      return '人工编辑';
    case 'status_change':
      return '状态变更';
    case 'delete':
      return '删除';
    default:
      return action;
  }
}

function toFormState(employee: EmployeeMasterItem | null): EmployeeFormState {
  if (!employee) {
    return EMPTY_FORM;
  }
  return {
    person_name: employee.person_name,
    id_number: employee.id_number ?? '',
    company_name: employee.company_name ?? '',
    department: employee.department ?? '',
    region: employee.region ?? '',
    active: employee.active,
  };
}

export function EmployeesPage() {
  const [employees, setEmployees] = useState<EmployeeMasterItem[]>([]);
  const [totalEmployees, setTotalEmployees] = useState(0);
  const [query, setQuery] = useState('');
  const [draftQuery, setDraftQuery] = useState('');
  const [activeOnly, setActiveOnly] = useState(false);
  const [pageSize, setPageSize] = useState<number>(10);
  const [pageIndex, setPageIndex] = useState(0);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(true);
  const [importing, setImporting] = useState(false);
  const [saving, setSaving] = useState(false);
  const [togglingStatus, setTogglingStatus] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [pageError, setPageError] = useState<string | null>(null);
  const [actionNotice, setActionNotice] = useState<string | null>(null);
  const [importResult, setImportResult] = useState<EmployeeImportResult | null>(null);
  const [selectedEmployeeId, setSelectedEmployeeId] = useState<string | null>(null);
  const [formState, setFormState] = useState<EmployeeFormState>(EMPTY_FORM);
  const [statusNote, setStatusNote] = useState('');
  const [audits, setAudits] = useState<EmployeeMasterAuditItem[]>([]);
  const [loadingAudits, setLoadingAudits] = useState(false);
  const [deletingAuditId, setDeletingAuditId] = useState<string | null>(null);
  const [auditError, setAuditError] = useState<string | null>(null);
  const [regions, setRegions] = useState<string[]>([]);
  const [companies, setCompanies] = useState<string[]>([]);
  const [selectedRegion, setSelectedRegion] = useState<string>('');
  const [selectedCompany, setSelectedCompany] = useState<string>('');

  useEffect(() => {
    fetchRegions().then(setRegions).catch(() => {});
    fetchCompanies().then(setCompanies).catch(() => {});
  }, []);

  useEffect(() => { setPageIndex(0); }, [selectedRegion, selectedCompany]);

  async function loadEmployees(
    nextQuery = query,
    nextActiveOnly = activeOnly,
    nextPageSize = pageSize,
    nextPageIndex = pageIndex,
    preferredEmployeeId?: string | null,
  ) {
    const result = await fetchEmployeeMasters({
      query: nextQuery,
      activeOnly: nextActiveOnly,
      limit: nextPageSize,
      offset: nextPageIndex * nextPageSize,
      region: selectedRegion || undefined,
      companyName: selectedCompany || undefined,
    });
    setEmployees(result.items);
    setTotalEmployees(result.total);
    setPageError(null);
    setSelectedEmployeeId((current) => {
      const targetId = preferredEmployeeId ?? current;
      if (targetId && result.items.some((item) => item.id === targetId)) {
        return targetId;
      }
      return result.items[0]?.id ?? null;
    });
  }

  useEffect(() => {
    let active = true;

    async function run() {
      try {
        const result = await fetchEmployeeMasters({
          query,
          activeOnly,
          limit: pageSize,
          offset: pageIndex * pageSize,
          region: selectedRegion || undefined,
          companyName: selectedCompany || undefined,
        });
        if (!active) {
          return;
        }
        setEmployees(result.items);
        setTotalEmployees(result.total);
        setSelectedEmployeeId((current) => {
          if (current && result.items.some((item) => item.id === current)) {
            return current;
          }
          return result.items[0]?.id ?? null;
        });
        setPageError(null);
      } catch (error) {
        if (active) {
          setPageError(normalizeApiError(error).message || '员工主档列表暂时无法读取，请稍后重试。');
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void run();
    return () => {
      active = false;
    };
  }, [query, activeOnly, pageIndex, pageSize, selectedRegion, selectedCompany]);

  const selectedEmployee = useMemo(
    () => employees.find((item) => item.id === selectedEmployeeId) ?? null,
    [employees, selectedEmployeeId],
  );

  useEffect(() => {
    setFormState(toFormState(selectedEmployee));
    setStatusNote('');
  }, [selectedEmployee]);

  useEffect(() => {
    let active = true;

    async function run() {
      if (!selectedEmployeeId) {
        setAudits([]);
        setAuditError(null);
        return;
      }

      setLoadingAudits(true);
      try {
        const result = await fetchEmployeeMasterAudits(selectedEmployeeId);
        if (!active) {
          return;
        }
        setAudits(result.items);
        setAuditError(null);
      } catch (error) {
        if (active) {
          setAuditError(normalizeApiError(error).message || '审计记录暂时无法读取。');
        }
      } finally {
        if (active) {
          setLoadingAudits(false);
        }
      }
    }

    void run();
    return () => {
      active = false;
    };
  }, [selectedEmployeeId]);

  const summary = useMemo(
    () => ({
      total: totalEmployees,
      visible: employees.length,
      active: employees.filter((item) => item.active).length,
      companies: new Set(employees.map((item) => item.company_name).filter(Boolean)).size,
    }),
    [employees, totalEmployees],
  );

  const totalPages = useMemo(
    () => Math.max(1, Math.ceil(totalEmployees / pageSize)),
    [pageSize, totalEmployees],
  );

  const currentRange = useMemo(() => {
    if (!totalEmployees || !employees.length) {
      return { start: 0, end: 0 };
    }
    const start = pageIndex * pageSize + 1;
    return { start, end: start + employees.length - 1 };
  }, [employees.length, pageIndex, pageSize, totalEmployees]);

  const isDirty = useMemo(() => {
    if (!selectedEmployee) {
      return false;
    }
    return JSON.stringify(formState) !== JSON.stringify(toFormState(selectedEmployee));
  }, [formState, selectedEmployee]);

  async function refreshAudits(employeeId: string) {
    const result = await fetchEmployeeMasterAudits(employeeId);
    setAudits(result.items);
    setAuditError(null);
  }

  async function handleDeleteAudit(audit: EmployeeMasterAuditItem) {
    if (!selectedEmployee) {
      return;
    }
    const confirmed = window.confirm(`确认删除这条“${describeAuditAction(audit.action)}”留痕吗？删除后将不会再展示在审计列表中。`);
    if (!confirmed) {
      return;
    }

    setDeletingAuditId(audit.id);
    setAuditError(null);
    setPageError(null);
    try {
      await deleteEmployeeMasterAudit(selectedEmployee.id, audit.id);
      await refreshAudits(selectedEmployee.id);
      setActionNotice(`已删除 1 条${describeAuditAction(audit.action)}留痕。`);
    } catch (error) {
      setAuditError(normalizeApiError(error).message || '审计记录删除失败。');
    } finally {
      setDeletingAuditId(null);
    }
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
      setActionNotice(`已导入 ${result.imported_count} 条员工主档，新增 ${result.created_count} 条，更新 ${result.updated_count} 条。`);
      setSelectedFile(null);
      setPageIndex(0);
      fetchCompanies().then(setCompanies).catch(() => {});
      await loadEmployees(query, activeOnly, pageSize, 0, result.items[0]?.id ?? selectedEmployeeId);
    } catch (error) {
      setPageError(normalizeApiError(error).message || '员工主档导入失败，请检查文件格式和必要字段后重试。');
    } finally {
      setImporting(false);
    }
  }

  async function handleSave() {
    if (!selectedEmployee) {
      return;
    }
    setSaving(true);
    setPageError(null);
    try {
      const payload: EmployeeMasterUpdateInput = {
        person_name: formState.person_name.trim(),
        id_number: formState.id_number.trim() || null,
        company_name: formState.company_name.trim() || null,
        department: formState.department.trim() || null,
        region: formState.region.trim() || null,
        active: formState.active,
      };
      const updated = await updateEmployeeMaster(selectedEmployee.id, payload);
      setEmployees((current) => current.map((item) => (item.id === updated.id ? updated : item)));
      setFormState(toFormState(updated));
      setActionNotice(`员工 ${updated.employee_id} 已更新。`);
      await refreshAudits(updated.id);
    } catch (error) {
      setPageError(normalizeApiError(error).message || '员工主档更新失败。');
    } finally {
      setSaving(false);
    }
  }

  async function handleToggleStatus() {
    if (!selectedEmployee) {
      return;
    }
    setTogglingStatus(true);
    setPageError(null);
    try {
      const updated = await updateEmployeeMasterStatus(selectedEmployee.id, {
        active: !selectedEmployee.active,
        note: statusNote.trim() || null,
      });
      setEmployees((current) => current.map((item) => (item.id === updated.id ? updated : item)));
      setFormState(toFormState(updated));
      setStatusNote('');
      setActionNotice(updated.active ? `员工 ${updated.employee_id} 已重新启用。` : `员工 ${updated.employee_id} 已停用。`);
      await refreshAudits(updated.id);
    } catch (error) {
      setPageError(normalizeApiError(error).message || '员工状态更新失败。');
    } finally {
      setTogglingStatus(false);
    }
  }

  async function handleDelete() {
    if (!selectedEmployee) {
      return;
    }
    const confirmed = window.confirm(`确认删除员工主档 ${selectedEmployee.employee_id} 吗？如果已有匹配历史，系统会阻止删除。`);
    if (!confirmed) {
      return;
    }
    setDeleting(true);
    setPageError(null);
    try {
      const deletingEmployeeId = selectedEmployee.id;
      const deletingEmployeeCode = selectedEmployee.employee_id;
      await deleteEmployeeMaster(deletingEmployeeId);
      setActionNotice(`员工 ${deletingEmployeeCode} 已删除。`);
      setAudits([]);
      const nextPageIndex = pageIndex > 0 && employees.length === 1 ? pageIndex - 1 : pageIndex;
      if (nextPageIndex !== pageIndex) {
        setPageIndex(nextPageIndex);
      }
      await loadEmployees(query, activeOnly, pageSize, nextPageIndex, null);
    } catch (error) {
      setPageError(normalizeApiError(error).message || '员工主档删除失败。');
    } finally {
      setDeleting(false);
    }
  }

  function handleSearchSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setPageIndex(0);
    setQuery(draftQuery.trim());
  }

  return (
    <PageContainer
      eyebrow="Employees"
      title="员工主档管理"
      description="上传员工主档、人工修正基础信息、停用无效主档，并查看每次导入和手工调整留下的审计记录。"
      actions={
        <div className="button-row">
          <Link to="/employees/new" className="button button--ghost">
            新增员工主档
          </Link>
          <button type="button" className="button button--primary" onClick={() => void handleImport()} disabled={!selectedFile || importing}>
            {importing ? '导入中...' : '导入主档文件'}
          </button>
        </div>
      }
    >
      {importResult ? (
        <div className="panel-card" style={{ marginBottom: '1rem' }}>
          <div className="section-heading">
            <div>
              <span className="panel-label">导入结果</span>
              <h2>文件: {importResult.file_name}</h2>
            </div>
          </div>
          <div className="status-grid" style={{ marginBottom: importResult.errors.length > 0 ? '0.75rem' : '0' }}>
            <article className="status-item">
              <strong>{importResult.total_rows}</strong>
              <div>总行数</div>
            </article>
            <article className="status-item">
              <strong>{importResult.created_count}</strong>
              <div>新增</div>
            </article>
            <article className="status-item">
              <strong>{importResult.updated_count}</strong>
              <div>更新</div>
            </article>
            <article className="status-item">
              <strong>{importResult.skipped_count}</strong>
              <div>失败</div>
            </article>
          </div>
          {importResult.errors.length > 0 && (
            <details style={{ padding: '0 1rem 1rem' }}>
              <summary style={{ cursor: 'pointer', fontWeight: 500 }}>
                失败明细 ({importResult.errors.length} 条)
              </summary>
              <ul style={{ marginTop: '0.5rem', paddingLeft: '1.25rem' }}>
                {importResult.errors.map((err, i) => (
                  <li key={i} style={{ color: 'var(--color-error, #c00)', marginBottom: '0.25rem' }}>{err}</li>
                ))}
              </ul>
            </details>
          )}
        </div>
      ) : null}
      {actionNotice ? <SurfaceNotice tone="success" title="操作完成" message={actionNotice} /> : null}
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
            <input type="file" accept=".csv,.xlsx" onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)} />
          </label>
          <div className="status-item">
            <strong>{selectedFile ? selectedFile.name : '尚未选择文件'}</strong>
            <div>{selectedFile ? '准备导入员工主档。' : '请上传包含工号和姓名的主档文件。'}</div>
          </div>
        </section>

        <section className="panel-card employee-summary-grid">
          <article className="status-item">
            <strong>{summary.total}</strong>
            <div>筛选结果总数</div>
          </article>
          <article className="status-item">
            <strong>{summary.visible}</strong>
            <div>当前页展示</div>
          </article>
          <article className="status-item">
            <strong>{summary.active}</strong>
            <div>当前页在职</div>
          </article>
          <article className="status-item">
            <strong>{summary.companies}</strong>
            <div>当前页覆盖公司</div>
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
            <select
              value={activeOnly ? 'active' : 'all'}
              onChange={(event) => {
                setLoading(true);
                setPageIndex(0);
                setActiveOnly(event.target.value === 'active');
              }}
            >
              <option value="all">全部主档</option>
              <option value="active">仅在职主档</option>
            </select>
          </label>
          <label className="form-field employee-toolbar__toggle">
            <span>地区</span>
            <select
              value={selectedRegion}
              onChange={(event) => {
                setLoading(true);
                setSelectedRegion(event.target.value);
              }}
            >
              <option value="">全部地区</option>
              {regions.map((r) => (
                <option key={r} value={r}>{r}</option>
              ))}
            </select>
          </label>
          <label className="form-field employee-toolbar__toggle">
            <span>公司</span>
            <select
              value={selectedCompany}
              onChange={(event) => {
                setLoading(true);
                setSelectedCompany(event.target.value);
              }}
            >
              <option value="">全部公司</option>
              {companies.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </label>
          <label className="form-field employee-toolbar__toggle">
            <span>每页展示</span>
            <select
              value={String(pageSize)}
              onChange={(event) => {
                setLoading(true);
                setPageIndex(0);
                setPageSize(Number(event.target.value));
              }}
            >
              {PAGE_SIZE_OPTIONS.map((value) => (
                <option key={value} value={value}>
                  {value} 条
                </option>
              ))}
            </select>
          </label>
          <button type="submit" className="button button--ghost">
            搜索主档
          </button>
        </form>

        {loading ? (
          <SectionState title="正在加载员工主档" message="系统正在同步当前可用于匹配的员工主档记录。" />
        ) : employees.length ? (
          <div className="employee-management-grid">
            <div className="employee-table-panel">
              <div className="preview-table-wrap">
                <table className="preview-table">
                  <thead>
                    <tr>
                      <th>工号</th>
                      <th>姓名</th>
                      <th>公司</th>
                      <th>地区</th>
                      <th>部门</th>
                      <th>状态</th>
                      <th>更新时间</th>
                      <th>操作</th>
                    </tr>
                  </thead>
                  <tbody>
                    {employees.map((employee) => {
                      const isSelected = employee.id === selectedEmployeeId;
                      return (
                        <tr key={employee.id} className={isSelected ? 'employee-table-row employee-table-row--active' : 'employee-table-row'}>
                          <td>{employee.employee_id}</td>
                          <td>{employee.person_name}</td>
                          <td>{employee.company_name ?? '-'}</td>
                          <td>{employee.region ?? '-'}</td>
                          <td>{employee.department ?? '-'}</td>
                          <td>
                            <span className={`dashboard-pill ${employee.active ? 'dashboard-pill--ok' : 'dashboard-pill--warn'}`}>
                              {employee.active ? '在职' : '停用'}
                            </span>
                          </td>
                          <td>{formatDateTime(employee.updated_at)}</td>
                          <td>
                            <div className="employee-table-actions">
                              <button type="button" className="button button--ghost" onClick={() => setSelectedEmployeeId(employee.id)}>
                                {isSelected ? '已选中' : '管理'}
                              </button>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              <div className="employee-pagination">
                <div className="employee-pagination__summary">
                  {summary.total ? `显示第 ${currentRange.start}-${currentRange.end} 条，共 ${summary.total} 条` : '当前没有可展示的主档记录'}
                </div>
                <div className="button-row employee-pagination__actions">
                  <button
                    type="button"
                    className="button button--ghost"
                    onClick={() => {
                      setLoading(true);
                      setPageIndex((current) => Math.max(0, current - 1));
                    }}
                    disabled={loading || pageIndex <= 0}
                  >
                    上一页
                  </button>
                  <span className="employee-pagination__page">{`第 ${Math.min(pageIndex + 1, totalPages)} / ${totalPages} 页`}</span>
                  <button
                    type="button"
                    className="button button--ghost"
                    onClick={() => {
                      setLoading(true);
                      setPageIndex((current) => (current + 1 < totalPages ? current + 1 : current));
                    }}
                    disabled={loading || pageIndex + 1 >= totalPages}
                  >
                    下一页
                  </button>
                </div>
              </div>
            </div>

            <div className="employee-side-panels">
              <section className="panel-card employee-editor-card">
                <div className="section-heading">
                  <div>
                    <span className="panel-label">人工编辑</span>
                    <h2>{selectedEmployee ? `编辑 ${selectedEmployee.employee_id}` : '选择一条主档'}</h2>
                  </div>
                </div>

                {selectedEmployee ? (
                  <>
                    <div className="employee-editor-meta status-grid">
                      <article className="status-item">
                        <strong>{selectedEmployee.person_name}</strong>
                        <div>当前姓名</div>
                      </article>
                      <article className="status-item">
                        <strong>{selectedEmployee.company_name ?? '-'}</strong>
                        <div>公司主体</div>
                      </article>
                      <article className="status-item">
                        <strong>{selectedEmployee.active ? '在职' : '停用'}</strong>
                        <div>当前状态</div>
                      </article>
                    </div>

                    <div className="employee-form-grid">
                      <label className="form-field">
                        <span>姓名</span>
                        <input value={formState.person_name} onChange={(event) => setFormState((current) => ({ ...current, person_name: event.target.value }))} />
                      </label>
                      <label className="form-field">
                        <span>身份证号</span>
                        <input value={formState.id_number} onChange={(event) => setFormState((current) => ({ ...current, id_number: event.target.value }))} />
                      </label>
                      <label className="form-field">
                        <span>公司</span>
                        <input value={formState.company_name} onChange={(event) => setFormState((current) => ({ ...current, company_name: event.target.value }))} />
                      </label>
                      <label className="form-field">
                        <span>部门</span>
                        <input value={formState.department} onChange={(event) => setFormState((current) => ({ ...current, department: event.target.value }))} />
                      </label>
                      <label className="form-field">
                        <span>地区</span>
                        <select value={formState.region} onChange={(event) => setFormState((current) => ({ ...current, region: event.target.value }))}>
                          <option value="">请选择地区</option>
                          {regions.map((r) => (
                            <option key={r} value={r}>{r}</option>
                          ))}
                        </select>
                      </label>
                    </div>

                    <label className="form-field employee-status-note">
                      <span>状态备注</span>
                      <textarea
                        rows={3}
                        value={statusNote}
                        onChange={(event) => setStatusNote(event.target.value)}
                        placeholder="停用或重新启用时可记录原因，例如：员工离职、重复主档、恢复匹配资格。"
                      />
                    </label>

                    <div className="button-row employee-editor-actions">
                      <button type="button" className="button button--primary" onClick={() => void handleSave()} disabled={!isDirty || saving || !formState.person_name.trim()}>
                        {saving ? '保存中...' : '保存编辑'}
                      </button>
                      <button type="button" className="button button--ghost" onClick={() => void handleToggleStatus()} disabled={togglingStatus}>
                        {togglingStatus ? '提交中...' : selectedEmployee.active ? '停用主档' : '重新启用'}
                      </button>
                      <button type="button" className="button button--ghost employee-delete-button" onClick={() => void handleDelete()} disabled={deleting}>
                        {deleting ? '删除中...' : '删除主档'}
                      </button>
                    </div>
                  </>
                ) : (
                  <SectionState title="尚未选择主档" message="从左侧列表选中一条记录后，可以编辑信息、停用记录或发起删除。" />
                )}
              </section>

              <section className="panel-card employee-audit-card">
                <div className="section-heading">
                  <div>
                    <span className="panel-label">审计记录</span>
                    <h2>导入与人工操作留痕</h2>
                  </div>
                </div>

                {!selectedEmployee ? (
                  <SectionState title="暂无审计对象" message="选中主档后，这里会展示最近的导入、编辑和状态变更记录。" />
                ) : loadingAudits ? (
                  <SectionState title="正在加载审计" message="系统正在读取该员工主档的历史操作记录。" />
                ) : auditError ? (
                  <SectionState tone="error" title="审计读取失败" message={auditError} />
                ) : audits.length ? (
                  <div className="employee-audit-list">
                    {audits.map((audit) => (
                      <article key={audit.id} className="employee-audit-item">
                        <div className="employee-audit-item__head">
                          <strong>{describeAuditAction(audit.action)}</strong>
                          <span>{formatDateTime(audit.created_at)}</span>
                        </div>
                        <div className="employee-audit-item__meta">
                          <span>工号快照：{audit.employee_id_snapshot}</span>
                          <span>{audit.note ?? '无备注'}</span>
                        </div>
                        <div className="employee-audit-item__actions">
                          <button
                            type="button"
                            className="button button--ghost employee-audit-delete-button"
                            onClick={() => void handleDeleteAudit(audit)}
                            disabled={deletingAuditId === audit.id}
                          >
                            {deletingAuditId === audit.id ? '删除中...' : '删除记录'}
                          </button>
                        </div>
                      </article>
                    ))}
                  </div>
                ) : (
                  <SectionState title="暂无审计记录" message="当前主档还没有留下可展示的操作历史。" />
                )}
              </section>
            </div>
          </div>
        ) : (
          <SectionState title="暂无员工主档" message="先导入员工主档文件，后续批次匹配才会进入可执行状态。" />
        )}
      </section>
    </PageContainer>
  );
}
