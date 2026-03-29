import type { ApiSuccessResponse } from './api';
import { LONG_RUNNING_REQUEST_TIMEOUT_MS, apiClient } from './api';

export interface EmployeeMasterItem {
  id: string;
  employee_id: string;
  person_name: string;
  id_number: string | null;
  company_name: string | null;
  department: string | null;
  region: string | null;
  active: boolean;
  created_at: string;
  updated_at: string;
}

export interface EmployeeMasterList {
  total: number;
  limit?: number | null;
  offset?: number;
  items: EmployeeMasterItem[];
}

export interface EmployeeMasterCreateInput {
  employee_id: string;
  person_name: string;
  id_number: string | null;
  company_name: string | null;
  department: string | null;
  region: string | null;
  active: boolean;
}

export interface EmployeeImportResult {
  file_name: string;
  total_rows: number;
  imported_count: number;
  created_count: number;
  updated_count: number;
  skipped_count: number;
  errors: string[];
  items: EmployeeMasterItem[];
}

export interface EmployeeMasterUpdateInput {
  person_name: string;
  id_number: string | null;
  company_name: string | null;
  department: string | null;
  region: string | null;
  active: boolean;
}

export interface EmployeeMasterStatusInput {
  active: boolean;
  note?: string | null;
}

export interface EmployeeMasterAuditItem {
  id: string;
  employee_master_id: string | null;
  employee_id_snapshot: string;
  action: string;
  note: string | null;
  snapshot: Record<string, unknown> | null;
  created_at: string;
}

export interface EmployeeMasterAuditList {
  total: number;
  items: EmployeeMasterAuditItem[];
}

export interface EmployeeSelfServiceProfile {
  employee_id: string | null;
  person_name: string;
  masked_id_number: string;
  company_name: string | null;
  department: string | null;
  active: boolean | null;
  source: string;
}

export interface EmployeeSelfServiceRecord {
  normalized_record_id: string;
  batch_id: string;
  batch_name: string;
  batch_status: string;
  employee_id: string | null;
  region: string | null;
  company_name: string | null;
  billing_period: string | null;
  period_start: string | null;
  period_end: string | null;
  source_file_name: string | null;
  source_row_number: number;
  total_amount: string | number | null;
  company_total_amount: string | number | null;
  personal_total_amount: string | number | null;
  housing_fund_personal: string | number | null;
  housing_fund_company: string | number | null;
  housing_fund_total: string | number | null;
  created_at: string;
}

export interface EmployeeSelfServiceResult {
  matched_employee_master: boolean;
  profile: EmployeeSelfServiceProfile;
  record_count: number;
  records: EmployeeSelfServiceRecord[];
}

export async function fetchRegions(): Promise<string[]> {
  const response = await apiClient.get<ApiSuccessResponse<string[]>>('/employees/regions');
  return response.data.data;
}

export async function fetchCompanies(): Promise<string[]> {
  const response = await apiClient.get<ApiSuccessResponse<string[]>>('/employees/companies');
  return response.data.data;
}

export async function fetchEmployeeMasters(params?: {
  query?: string;
  activeOnly?: boolean;
  limit?: number;
  offset?: number;
  region?: string;
  companyName?: string;
}): Promise<EmployeeMasterList> {
  const response = await apiClient.get<ApiSuccessResponse<EmployeeMasterList>>('/employees', {
    params: {
      query: params?.query || undefined,
      active_only: params?.activeOnly ?? undefined,
      limit: params?.limit ?? undefined,
      offset: params?.offset ?? undefined,
      region: params?.region || undefined,
      company_name: params?.companyName || undefined,
    },
  });
  return response.data.data;
}

export async function createEmployeeMaster(payload: EmployeeMasterCreateInput): Promise<EmployeeMasterItem> {
  const response = await apiClient.post<ApiSuccessResponse<EmployeeMasterItem>>('/employees', payload);
  return response.data.data;
}

export async function importEmployeeMaster(file: File): Promise<EmployeeImportResult> {
  const formData = new FormData();
  formData.append('file', file);
  const response = await apiClient.post<ApiSuccessResponse<EmployeeImportResult>>('/employees/import', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: LONG_RUNNING_REQUEST_TIMEOUT_MS,
  });
  return response.data.data;
}

export async function updateEmployeeMaster(employeeId: string, payload: EmployeeMasterUpdateInput): Promise<EmployeeMasterItem> {
  const response = await apiClient.patch<ApiSuccessResponse<EmployeeMasterItem>>(`/employees/${employeeId}`, payload);
  return response.data.data;
}

export async function updateEmployeeMasterStatus(employeeId: string, payload: EmployeeMasterStatusInput): Promise<EmployeeMasterItem> {
  const response = await apiClient.post<ApiSuccessResponse<EmployeeMasterItem>>(`/employees/${employeeId}/status`, payload);
  return response.data.data;
}

export async function deleteEmployeeMaster(employeeId: string): Promise<void> {
  await apiClient.delete(`/employees/${employeeId}`);
}

export async function fetchEmployeeMasterAudits(employeeId: string): Promise<EmployeeMasterAuditList> {
  const response = await apiClient.get<ApiSuccessResponse<EmployeeMasterAuditList>>(`/employees/${employeeId}/audits`);
  return response.data.data;
}

export async function deleteEmployeeMasterAudit(employeeId: string, auditId: string): Promise<void> {
  await apiClient.delete(`/employees/${employeeId}/audits/${auditId}`);
}

export async function queryEmployeeSelfService(input: { person_name: string; id_number: string }): Promise<EmployeeSelfServiceResult> {
  const response = await apiClient.post<ApiSuccessResponse<EmployeeSelfServiceResult>>('/employees/self-service/query', input);
  return response.data.data;
}
