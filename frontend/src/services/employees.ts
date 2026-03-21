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
