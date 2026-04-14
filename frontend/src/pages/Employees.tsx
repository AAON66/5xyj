import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Button,
  Card,
  Col,
  Drawer,
  Empty,
  Form,
  Input,
  message,
  Modal,
  Row,
  Select,
  Skeleton,
  Space,
  Statistic,
  Table,
  Tag,
  Typography,
  Upload,
} from 'antd';
import { UploadOutlined, PlusOutlined, DeleteOutlined, FilterOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';

import { ResponsiveFilterDrawer } from '../components/ResponsiveFilterDrawer';
import { useResponsiveViewport } from '../hooks/useResponsiveViewport';
import { normalizeApiError } from '../services/api';
import { useCardStatusColors } from '../theme/useCardStatusColors';
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

const { Title } = Typography;

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

const PAGE_SIZE_OPTIONS = [10, 20, 50];

interface EmployeeFilterState {
  query: string;
  activeOnly: boolean;
  region: string;
  company: string;
}

function formatDateTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat('zh-CN', { dateStyle: 'medium', timeStyle: 'short' }).format(date);
}

function describeAuditAction(action: string): string {
  switch (action) {
    case 'import_create': return '导入新增';
    case 'import_update': return '导入更新';
    case 'manual_create': return '人工新增';
    case 'manual_update': return '人工编辑';
    case 'status_change': return '状态变更';
    case 'delete': return '删除';
    default: return action;
  }
}

function toFormState(employee: EmployeeMasterItem | null): EmployeeFormState {
  if (!employee) return EMPTY_FORM;
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
  const cardColors = useCardStatusColors();
  const { isMobile, isTablet } = useResponsiveViewport();
  const isCompactFilter = isMobile || isTablet;
  const [employees, setEmployees] = useState<EmployeeMasterItem[]>([]);
  const [totalEmployees, setTotalEmployees] = useState(0);
  const [query, setQuery] = useState('');
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
  const [drawerVisible, setDrawerVisible] = useState(false);
  const [filterDrawerOpen, setFilterDrawerOpen] = useState(false);
  const [draftFilters, setDraftFilters] = useState<EmployeeFilterState>({
    query: '',
    activeOnly: false,
    region: '',
    company: '',
  });

  useEffect(() => {
    fetchRegions().then(setRegions).catch(() => {});
    fetchCompanies().then(setCompanies).catch(() => {});
  }, []);

  useEffect(() => {
    setDraftFilters({
      query,
      activeOnly,
      region: selectedRegion,
      company: selectedCompany,
    });
  }, [query, activeOnly, selectedRegion, selectedCompany]);

  useEffect(() => {
    setPageIndex(0);
  }, [selectedRegion, selectedCompany]);

  async function loadEmployees(
    nextQuery = query,
    nextActiveOnly = activeOnly,
    nextPageSize = pageSize,
    nextPageIndex = pageIndex,
    preferredEmployeeId?: string | null,
    nextRegion = selectedRegion,
    nextCompany = selectedCompany,
  ) {
    const result = await fetchEmployeeMasters({
      query: nextQuery,
      activeOnly: nextActiveOnly,
      limit: nextPageSize,
      offset: nextPageIndex * nextPageSize,
      region: nextRegion || undefined,
      companyName: nextCompany || undefined,
    });
    setEmployees(result.items);
    setTotalEmployees(result.total);
    setPageError(null);
    setSelectedEmployeeId((current) => {
      const targetId = preferredEmployeeId ?? current;
      if (targetId && result.items.some((item) => item.id === targetId)) return targetId;
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
        if (!active) return;
        setEmployees(result.items);
        setTotalEmployees(result.total);
        setSelectedEmployeeId((current) => {
          if (current && result.items.some((item) => item.id === current)) return current;
          return result.items[0]?.id ?? null;
        });
        setPageError(null);
      } catch (error) {
        if (active) setPageError(normalizeApiError(error).message || '员工主档列表暂时无法读取，请稍后重试。');
      } finally {
        if (active) setLoading(false);
      }
    }
    void run();
    return () => { active = false; };
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
      if (!selectedEmployeeId) { setAudits([]); setAuditError(null); return; }
      setLoadingAudits(true);
      try {
        const result = await fetchEmployeeMasterAudits(selectedEmployeeId);
        if (!active) return;
        setAudits(result.items);
        setAuditError(null);
      } catch (error) {
        if (active) setAuditError(normalizeApiError(error).message || '审计记录暂时无法读取。');
      } finally {
        if (active) setLoadingAudits(false);
      }
    }
    void run();
    return () => { active = false; };
  }, [selectedEmployeeId]);

  const summary = useMemo(() => ({
    total: totalEmployees,
    visible: employees.length,
    active: employees.filter((item) => item.active).length,
    companies: new Set(employees.map((item) => item.company_name).filter(Boolean)).size,
  }), [employees, totalEmployees]);

  const isDirty = useMemo(() => {
    if (!selectedEmployee) return false;
    return JSON.stringify(formState) !== JSON.stringify(toFormState(selectedEmployee));
  }, [formState, selectedEmployee]);

  async function refreshAudits(employeeId: string) {
    const result = await fetchEmployeeMasterAudits(employeeId);
    setAudits(result.items);
    setAuditError(null);
  }

  async function handleDeleteAudit(audit: EmployeeMasterAuditItem) {
    if (!selectedEmployee) return;
    setDeletingAuditId(audit.id);
    setAuditError(null);
    setPageError(null);
    try {
      await deleteEmployeeMasterAudit(selectedEmployee.id, audit.id);
      await refreshAudits(selectedEmployee.id);
      message.success(`已删除 1 条${describeAuditAction(audit.action)}留痕`);
    } catch (error) {
      setAuditError(normalizeApiError(error).message || '审计记录删除失败。');
    } finally {
      setDeletingAuditId(null);
    }
  }

  async function handleImport() {
    if (!selectedFile) return;
    setImporting(true);
    setPageError(null);
    try {
      const result = await importEmployeeMaster(selectedFile);
      setImportResult(result);
      message.success(`已导入 ${result.imported_count} 条员工主档`);
      setSelectedFile(null);
      setPageIndex(0);
      fetchCompanies().then(setCompanies).catch(() => {});
      await loadEmployees(
        query,
        activeOnly,
        pageSize,
        0,
        result.items[0]?.id ?? selectedEmployeeId,
        selectedRegion,
        selectedCompany,
      );
    } catch (error) {
      message.error(normalizeApiError(error).message || '员工主档导入失败');
    } finally {
      setImporting(false);
    }
  }

  async function handleSave() {
    if (!selectedEmployee) return;
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
      message.success(`员工 ${updated.employee_id} 已更新`);
      await refreshAudits(updated.id);
    } catch (error) {
      message.error(normalizeApiError(error).message || '员工主档更新失败');
    } finally {
      setSaving(false);
    }
  }

  async function handleToggleStatus() {
    if (!selectedEmployee) return;
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
      message.success(updated.active ? `员工 ${updated.employee_id} 已重新启用` : `员工 ${updated.employee_id} 已停用`);
      await refreshAudits(updated.id);
    } catch (error) {
      message.error(normalizeApiError(error).message || '员工状态更新失败');
    } finally {
      setTogglingStatus(false);
    }
  }

  async function handleDelete() {
    if (!selectedEmployee) return;
    Modal.confirm({
      title: '确认删除',
      content: `确认删除员工主档 ${selectedEmployee.employee_id} 吗？如果已有匹配历史，系统会阻止删除。此操作不可撤销，确定要删除该记录吗？`,
      okText: '确认删除',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        setDeleting(true);
        setPageError(null);
        try {
          const deletingEmployeeCode = selectedEmployee.employee_id;
          await deleteEmployeeMaster(selectedEmployee.id);
          message.success(`员工 ${deletingEmployeeCode} 已删除`);
          setAudits([]);
          setDrawerVisible(false);
          const nextPageIndex = pageIndex > 0 && employees.length === 1 ? pageIndex - 1 : pageIndex;
          if (nextPageIndex !== pageIndex) setPageIndex(nextPageIndex);
          await loadEmployees(query, activeOnly, pageSize, nextPageIndex, null);
        } catch (error) {
          message.error(normalizeApiError(error).message || '员工主档删除失败');
        } finally {
          setDeleting(false);
        }
      },
    });
  }

  function countActiveFilters(filters: EmployeeFilterState) {
    let count = 0;
    if (filters.query.trim()) count += 1;
    if (filters.activeOnly) count += 1;
    if (filters.region) count += 1;
    if (filters.company) count += 1;
    return count;
  }

  function closeFilterDrawer() {
    setDraftFilters({
      query,
      activeOnly,
      region: selectedRegion,
      company: selectedCompany,
    });
    setFilterDrawerOpen(false);
  }

  function applyDraftFilters() {
    const normalizedQuery = draftFilters.query.trim();
    const filtersChanged = (
      normalizedQuery !== query ||
      draftFilters.activeOnly !== activeOnly ||
      draftFilters.region !== selectedRegion ||
      draftFilters.company !== selectedCompany ||
      pageIndex !== 0
    );

    setLoading(true);
    setFilterDrawerOpen(false);

    if (!filtersChanged) {
      void loadEmployees(
        normalizedQuery,
        draftFilters.activeOnly,
        pageSize,
        0,
        selectedEmployeeId,
        draftFilters.region,
        draftFilters.company,
      ).finally(() => setLoading(false));
      return;
    }

    setPageIndex(0);
    setQuery(normalizedQuery);
    setActiveOnly(draftFilters.activeOnly);
    setSelectedRegion(draftFilters.region);
    setSelectedCompany(draftFilters.company);
  }

  function resetFilters() {
    const nextFilters: EmployeeFilterState = {
      query: '',
      activeOnly: false,
      region: '',
      company: '',
    };
    setDraftFilters(nextFilters);

    const filtersChanged = query || activeOnly || selectedRegion || selectedCompany || pageIndex !== 0;
    setLoading(true);
    setFilterDrawerOpen(false);

    if (!filtersChanged) {
      void loadEmployees('', false, pageSize, 0, selectedEmployeeId, '', '').finally(() => setLoading(false));
      return;
    }

    setPageIndex(0);
    setQuery('');
    setActiveOnly(false);
    setSelectedRegion('');
    setSelectedCompany('');
  }

  function openDrawer(employeeId: string) {
    setSelectedEmployeeId(employeeId);
    setDrawerVisible(true);
  }

  const columns: ColumnsType<EmployeeMasterItem> = [
    { title: '工号', dataIndex: 'employee_id', key: 'employee_id', fixed: 'left' as const, width: 100 },
    { title: '姓名', dataIndex: 'person_name', key: 'person_name', width: 80 },
    { title: '公司', dataIndex: 'company_name', key: 'company_name', width: 140, ellipsis: true, render: (v: string | null) => v ?? '-' },
    { title: '地区', dataIndex: 'region', key: 'region', width: 70, render: (v: string | null) => v ?? '-' },
    { title: '部门', dataIndex: 'department', key: 'department', width: 100, render: (v: string | null) => v ?? '-' },
    {
      title: '状态', key: 'active', width: 70,
      render: (_: unknown, record: EmployeeMasterItem) => (
        <Tag color={record.active ? 'success' : 'warning'}>{record.active ? '在职' : '停用'}</Tag>
      ),
    },
    { title: '更新时间', dataIndex: 'updated_at', key: 'updated_at', width: 160, render: (v: string) => formatDateTime(v) },
    {
      title: '操作', key: 'actions', fixed: 'right' as const, width: 120,
      render: (_: unknown, record: EmployeeMasterItem) => (
        <Space>
          <Button type="link" size="small" onClick={() => openDrawer(record.id)}>编辑</Button>
          <Button type="link" size="small" danger onClick={() => {
            setSelectedEmployeeId(record.id);
            // Delay to let state update
            setTimeout(() => void handleDelete(), 0);
          }}>删除</Button>
        </Space>
      ),
    },
  ];

  const activeFilterCount = countActiveFilters({
    query,
    activeOnly,
    region: selectedRegion,
    company: selectedCompany,
  });

  const filterFields = (
    <Row gutter={[16, 16]} align="middle">
      <Col xs={24} sm={12} md={8}>
        <Input.Search
          placeholder="工号 / 姓名 / 身份证号 / 公司"
          value={draftFilters.query}
          onChange={(event) => setDraftFilters((current) => ({ ...current, query: event.target.value }))}
          onSearch={applyDraftFilters}
          allowClear
        />
      </Col>
      <Col xs={24} sm={12} md={5}>
        <Select
          placeholder="筛选范围"
          value={draftFilters.activeOnly ? 'active' : 'all'}
          onChange={(value) => setDraftFilters((current) => ({ ...current, activeOnly: value === 'active' }))}
          style={{ width: '100%' }}
          options={[
            { label: '全部主档', value: 'all' },
            { label: '仅在职主档', value: 'active' },
          ]}
        />
      </Col>
      <Col xs={24} sm={12} md={5}>
        <Select
          placeholder="全部地区"
          allowClear
          value={draftFilters.region || undefined}
          onChange={(value) => setDraftFilters((current) => ({ ...current, region: value ?? '' }))}
          style={{ width: '100%' }}
          options={regions.map((region) => ({ label: region, value: region }))}
        />
      </Col>
      <Col xs={24} sm={12} md={6}>
        <Select
          placeholder="全部公司"
          allowClear
          value={draftFilters.company || undefined}
          onChange={(value) => setDraftFilters((current) => ({ ...current, company: value ?? '' }))}
          style={{ width: '100%' }}
          options={companies.map((company) => ({ label: company, value: company }))}
        />
      </Col>
      {isCompactFilter ? null : (
        <Col xs={24}>
          <Space wrap>
            <Button type="primary" onClick={applyDraftFilters}>搜索主档</Button>
            <Button onClick={resetFilters}>重置</Button>
          </Space>
        </Col>
      )}
    </Row>
  );

  return (
    <div>
      <Row justify="space-between" align="top" gutter={[12, 12]} style={{ marginBottom: 16 }}>
        <Col flex="1 1 240px">
          <Title level={4} style={{ margin: 0 }}>员工主档</Title>
        </Col>
        <Col flex="0 1 auto">
          <Space wrap size={[8, 8]}>
            <Upload
              accept=".csv,.xlsx"
              beforeUpload={(file) => { setSelectedFile(file); return false; }}
              showUploadList={false}
            >
              <Button icon={<UploadOutlined />}>选择文件</Button>
            </Upload>
            <Button
              type="primary"
              onClick={() => void handleImport()}
              disabled={!selectedFile || importing}
              loading={importing}
            >
              导入主档文件
            </Button>
            <Link to="/employees/new">
              <Button icon={<PlusOutlined />}>新增员工主档</Button>
            </Link>
            {isCompactFilter ? (
              <Button icon={<FilterOutlined />} onClick={() => setFilterDrawerOpen(true)}>
                {activeFilterCount > 0 ? `筛选 (${activeFilterCount})` : '筛选'}
              </Button>
            ) : null}
          </Space>
        </Col>
      </Row>

      {/* Import result */}
      {importResult && (
        <Card style={{ marginBottom: 16 }}>
          <Row gutter={[16, 16]}>
            <Col xs={24} sm={12} lg={6}><Statistic title="总行数" value={importResult.total_rows} /></Col>
            <Col xs={24} sm={12} lg={6}><Statistic title="新增" value={importResult.created_count} /></Col>
            <Col xs={24} sm={12} lg={6}><Statistic title="更新" value={importResult.updated_count} /></Col>
            <Col xs={24} sm={12} lg={6}><Statistic title="失败" value={importResult.skipped_count} /></Col>
          </Row>
          {importResult.errors.length > 0 && (
            <div style={{ marginTop: 12 }}>
              {importResult.errors.map((err, i) => (
                <Tag key={i} color="error" style={{ marginBottom: 4 }}>{err}</Tag>
              ))}
            </div>
          )}
        </Card>
      )}

      {pageError && <Card style={{ marginBottom: 16, borderColor: cardColors.errorBorder }}><Typography.Text type="danger">{pageError}</Typography.Text></Card>}

      {isCompactFilter ? (
        <ResponsiveFilterDrawer
          title="筛选员工主档"
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

      {/* Summary stats */}
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col xs={24} sm={12} xl={6}><Card><Statistic title="筛选结果总数" value={summary.total} /></Card></Col>
        <Col xs={24} sm={12} xl={6}><Card><Statistic title="当前页展示" value={summary.visible} /></Card></Col>
        <Col xs={24} sm={12} xl={6}><Card><Statistic title="当前页在职" value={summary.active} /></Card></Col>
        <Col xs={24} sm={12} xl={6}><Card><Statistic title="当前页覆盖公司" value={summary.companies} /></Card></Col>
      </Row>

      {/* Employee table */}
      <Card>
        {loading ? (
          <Skeleton active paragraph={{ rows: 8 }} />
        ) : employees.length === 0 ? (
          <Empty description="先导入员工主档文件，后续批次匹配才会进入可执行状态。" />
        ) : (
          <Table<EmployeeMasterItem>
            columns={columns}
            dataSource={employees}
            rowKey="id"
            size="small"
            scroll={{ x: 980 }}
            pagination={{
              current: pageIndex + 1,
              pageSize,
              total: totalEmployees,
              showSizeChanger: true,
              pageSizeOptions: PAGE_SIZE_OPTIONS.map(String),
              showTotal: (total) => `共 ${total} 条`,
              onChange: (newPage, newPageSize) => {
                setLoading(true);
                if (newPageSize !== pageSize) {
                  setPageIndex(0);
                  setPageSize(newPageSize);
                } else {
                  setPageIndex(newPage - 1);
                }
              },
            }}
          />
        )}
      </Card>

      {/* Edit Drawer */}
      <Drawer
        title={selectedEmployee ? `编辑 ${selectedEmployee.employee_id}` : '编辑员工'}
        width={480}
        open={drawerVisible}
        onClose={() => setDrawerVisible(false)}
      >
        {selectedEmployee ? (
          <>
            <Row gutter={16} style={{ marginBottom: 16 }}>
              <Col span={8}><Statistic title="当前姓名" value={selectedEmployee.person_name} /></Col>
              <Col span={8}><Statistic title="公司主体" value={selectedEmployee.company_name ?? '-'} /></Col>
              <Col span={8}><Statistic title="当前状态" value={selectedEmployee.active ? '在职' : '停用'} /></Col>
            </Row>

            <Form layout="vertical">
              <Form.Item label="姓名">
                <Input value={formState.person_name} onChange={(e) => setFormState((c) => ({ ...c, person_name: e.target.value }))} />
              </Form.Item>
              <Form.Item label="身份证号">
                <Input value={formState.id_number} onChange={(e) => setFormState((c) => ({ ...c, id_number: e.target.value }))} />
              </Form.Item>
              <Form.Item label="公司">
                <Input value={formState.company_name} onChange={(e) => setFormState((c) => ({ ...c, company_name: e.target.value }))} />
              </Form.Item>
              <Form.Item label="部门">
                <Input value={formState.department} onChange={(e) => setFormState((c) => ({ ...c, department: e.target.value }))} />
              </Form.Item>
              <Form.Item label="地区">
                <Select
                  value={formState.region || undefined}
                  onChange={(v) => setFormState((c) => ({ ...c, region: v ?? '' }))}
                  placeholder="请选择地区"
                  allowClear
                  options={regions.map((r) => ({ label: r, value: r }))}
                />
              </Form.Item>
              <Form.Item label="状态备注">
                <Input.TextArea
                  rows={3}
                  value={statusNote}
                  onChange={(e) => setStatusNote(e.target.value)}
                  placeholder="停用或重新启用时可记录原因"
                />
              </Form.Item>
            </Form>

            <Space style={{ marginBottom: 24 }}>
              <Button type="primary" onClick={() => void handleSave()} disabled={!isDirty || saving || !formState.person_name.trim()} loading={saving}>
                保存编辑
              </Button>
              <Button onClick={() => void handleToggleStatus()} disabled={togglingStatus} loading={togglingStatus}>
                {selectedEmployee.active ? '停用主档' : '重新启用'}
              </Button>
              <Button danger onClick={() => void handleDelete()} disabled={deleting} loading={deleting}>
                删除主档
              </Button>
            </Space>

            {/* Audit records */}
            <Title level={5}>审计记录</Title>
            {loadingAudits ? (
              <Skeleton active paragraph={{ rows: 3 }} />
            ) : auditError ? (
              <Empty description={auditError} />
            ) : audits.length === 0 ? (
              <Empty description="当前主档还没有留下可展示的操作历史。" />
            ) : (
              audits.map((audit) => (
                <Card key={audit.id} size="small" style={{ marginBottom: 8 }}>
                  <Row justify="space-between" align="middle">
                    <Col>
                      <Tag>{describeAuditAction(audit.action)}</Tag>
                      <Typography.Text type="secondary" style={{ marginLeft: 8 }}>{formatDateTime(audit.created_at)}</Typography.Text>
                    </Col>
                    <Col>
                      <Button
                        type="text"
                        danger
                        size="small"
                        icon={<DeleteOutlined />}
                        onClick={() => void handleDeleteAudit(audit)}
                        loading={deletingAuditId === audit.id}
                      />
                    </Col>
                  </Row>
                  <div style={{ marginTop: 4 }}>
                    <Typography.Text type="secondary">工号快照: {audit.employee_id_snapshot}</Typography.Text>
                    {audit.note && <Typography.Text type="secondary" style={{ marginLeft: 8 }}>{audit.note}</Typography.Text>}
                  </div>
                </Card>
              ))
            )}
          </>
        ) : (
          <Empty description="从列表选中一条记录后，可以编辑信息" />
        )}
      </Drawer>
    </div>
  );
}
