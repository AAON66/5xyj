import { useEffect, useMemo, useState, type FormEvent } from 'react';

import { PageContainer, SectionState, SurfaceNotice } from '../components';
import { normalizeApiError } from '../services/api';
import {
  deleteEmployeeMaster,
  fetchEmployeeMasterAudits,
  fetchEmployeeMasters,
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
  active: boolean;
}

const EMPTY_FORM: EmployeeFormState = {
  person_name: '',
  id_number: '',
  company_name: '',
  department: '',
  active: true,
};

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
    active: employee.active,
  };
}

export function EmployeesPage() {
  const [employees, setEmployees] = useState<EmployeeMasterItem[]>([]);
  const [query, setQuery] = useState('');
  const [draftQuery, setDraftQuery] = useState('');
  const [activeOnly, setActiveOnly] = useState(false);
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
  const [auditError, setAuditError] = useState<string | null>(null);

  async function loadEmployees(nextQuery = query, nextActiveOnly = activeOnly, preferredEmployeeId?: string | null) {
    const result = await fetchEmployeeMasters({ query: nextQuery, activeOnly: nextActiveOnly });
    setEmployees(result.items);
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
        const result = await fetchEmployeeMasters({ query, activeOnly });
        if (!active) {
          return;
        }
        setEmployees(result.items);
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
  }, [query, activeOnly]);

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
      total: employees.length,
      active: employees.filter((item) => item.active).length,
      companies: new Set(employees.map((item) => item.company_name).filter(Boolean)).size,
    }),
    [employees],
  );

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
      await loadEmployees(query, activeOnly, result.items[0]?.id ?? selectedEmployeeId);
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
      await loadEmployees(query, activeOnly, null);
    } catch (error) {
      setPageError(normalizeApiError(error).message || '员工主档删除失败。');
    } finally {
      setDeleting(false);
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
      title="员工主档管理"
      description="上传员工主档、人工修正基础信息、停用无效主档，并查看每次导入和手工调整留下的审计记录。"
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
          <div className="employee-management-grid">
            <div className="preview-table-wrap">
              <table className="preview-table">
                <thead>
                  <tr>
                    <th>工号</th>
                    <th>姓名</th>
                    <th>公司</th>
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
