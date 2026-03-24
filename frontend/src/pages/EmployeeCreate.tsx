import { useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import { PageContainer, SurfaceNotice } from '../components';
import { normalizeApiError } from '../services/api';
import { createEmployeeMaster } from '../services/employees';

interface CreateEmployeeFormState {
  employee_id: string;
  person_name: string;
  id_number: string;
  company_name: string;
  department: string;
  active: boolean;
}

const EMPTY_FORM: CreateEmployeeFormState = {
  employee_id: '',
  person_name: '',
  id_number: '',
  company_name: '',
  department: '',
  active: true,
};

export function EmployeeCreatePage() {
  const navigate = useNavigate();
  const [formState, setFormState] = useState<CreateEmployeeFormState>(EMPTY_FORM);
  const [saving, setSaving] = useState(false);
  const [pageError, setPageError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setPageError(null);
    setSuccessMessage(null);

    try {
      const created = await createEmployeeMaster({
        employee_id: formState.employee_id.trim(),
        person_name: formState.person_name.trim(),
        id_number: formState.id_number.trim() || null,
        company_name: formState.company_name.trim() || null,
        department: formState.department.trim() || null,
        active: formState.active,
      });
      setSuccessMessage(`员工 ${created.employee_id} 已创建，可以返回员工主档页继续管理。`);
      setFormState({
        ...EMPTY_FORM,
        company_name: formState.company_name,
        department: formState.department,
      });
    } catch (error) {
      setPageError(normalizeApiError(error).message || '新增员工主档失败。');
    } finally {
      setSaving(false);
    }
  }

  return (
    <PageContainer
      eyebrow="Employees"
      title="新增员工主档"
      description="手动补录单个员工主档。适合导入前临时补齐工号、姓名、身份证号和主体信息，方便后续匹配。"
      actions={
        <div className="button-row">
          <button type="button" className="button button--ghost" onClick={() => navigate('/employees')}>
            返回员工主档
          </button>
        </div>
      }
    >
      {successMessage ? <SurfaceNotice tone="success" title="创建完成" message={successMessage} /> : null}
      {pageError ? <SurfaceNotice tone="error" title="提交失败" message={pageError} /> : null}

      <section className="panel-card employee-create-card">
        <div className="section-heading">
          <div>
            <span className="panel-label">手动新增</span>
            <h2>填写员工主档信息</h2>
          </div>
        </div>

        <form className="employee-create-form" onSubmit={handleSubmit}>
          <div className="employee-form-grid">
            <label className="form-field">
              <span>工号</span>
              <input
                value={formState.employee_id}
                onChange={(event) => setFormState((current) => ({ ...current, employee_id: event.target.value }))}
                placeholder="例如：E1024"
                required
              />
            </label>
            <label className="form-field">
              <span>姓名</span>
              <input
                value={formState.person_name}
                onChange={(event) => setFormState((current) => ({ ...current, person_name: event.target.value }))}
                placeholder="例如：张三"
                required
              />
            </label>
            <label className="form-field">
              <span>身份证号</span>
              <input
                value={formState.id_number}
                onChange={(event) => setFormState((current) => ({ ...current, id_number: event.target.value }))}
                placeholder="可选"
              />
            </label>
            <label className="form-field">
              <span>公司主体</span>
              <input
                value={formState.company_name}
                onChange={(event) => setFormState((current) => ({ ...current, company_name: event.target.value }))}
                placeholder="可选"
              />
            </label>
            <label className="form-field">
              <span>部门</span>
              <input
                value={formState.department}
                onChange={(event) => setFormState((current) => ({ ...current, department: event.target.value }))}
                placeholder="可选"
              />
            </label>
            <label className="form-field">
              <span>在职状态</span>
              <select
                value={formState.active ? 'active' : 'inactive'}
                onChange={(event) => setFormState((current) => ({ ...current, active: event.target.value === 'active' }))}
              >
                <option value="active">在职</option>
                <option value="inactive">停用</option>
              </select>
            </label>
          </div>

          <div className="employee-create-actions button-row">
            <button
              type="submit"
              className="button button--primary"
              disabled={saving || !formState.employee_id.trim() || !formState.person_name.trim()}
            >
              {saving ? '创建中...' : '创建员工主档'}
            </button>
            <Link to="/employees" className="button button--ghost">
              返回列表
            </Link>
          </div>
        </form>
      </section>
    </PageContainer>
  );
}
