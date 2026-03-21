import type { ApiSuccessResponse } from './api';
import { apiClient } from './api';

export interface EmployeeMasterItem {
  id: string;
  employee_id: string;
  person_name: string;
  id_number: string | null;
  company_name: string | null;
  department: string | null;
  active: boolean;
  created_at: string;
  updated_at: string;
}

export interface EmployeeMasterList {
  total: number;
  items: EmployeeMasterItem[];
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

export async function fetchEmployeeMasters(params?: { query?: string; activeOnly?: boolean }): Promise<EmployeeMasterList> {
  const response = await apiClient.get<ApiSuccessResponse<EmployeeMasterList>>('/employees', {
    params: {
      query: params?.query || undefined,
      active_only: params?.activeOnly ?? undefined,
    },
  });
  return response.data.data;
}

export async function importEmployeeMaster(file: File): Promise<EmployeeImportResult> {
  const formData = new FormData();
  formData.append('file', file);
  const response = await apiClient.post<ApiSuccessResponse<EmployeeImportResult>>('/employees/import', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
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
