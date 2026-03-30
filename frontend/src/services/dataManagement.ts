import type { ApiSuccessResponse } from './api';
import { apiClient } from './api';

export interface NormalizedRecordItem {
  id: string;
  batch_id: string;
  person_name: string | null;
  id_number: string | null;
  employee_id: string | null;
  company_name: string | null;
  region: string | null;
  billing_period: string | null;
  payment_base: number | null;
  total_amount: number | null;
  company_total_amount: number | null;
  personal_total_amount: number | null;
  pension_company: number | null;
  pension_personal: number | null;
  medical_company: number | null;
  medical_personal: number | null;
  medical_maternity_company: number | null;
  unemployment_company: number | null;
  unemployment_personal: number | null;
  injury_company: number | null;
  supplementary_medical_company: number | null;
  supplementary_pension_company: number | null;
  large_medical_personal: number | null;
  housing_fund_personal: number | null;
  housing_fund_company: number | null;
  housing_fund_total: number | null;
  created_at: string;
}

export interface PaginatedRecords {
  items: NormalizedRecordItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface FilterOptions {
  regions: string[];
  companies: string[];
  periods: string[];
}

export interface EmployeeSummaryItem {
  employee_id: string | null;
  person_name: string | null;
  company_name: string | null;
  region: string | null;
  latest_period: string | null;
  company_total: number;
  personal_total: number;
  total: number;
}

export interface PaginatedEmployeeSummary {
  items: EmployeeSummaryItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface PeriodSummaryItem {
  billing_period: string;
  total_count: number;
  company_total: number;
  personal_total: number;
  total: number;
  avg_personal: number;
  avg_company: number;
}

export interface PaginatedPeriodSummary {
  items: PeriodSummaryItem[];
  total: number;
  page: number;
  page_size: number;
}

export async function fetchNormalizedRecords(params: {
  region?: string;
  companyName?: string;
  billingPeriod?: string;
  page?: number;
  pageSize?: number;
}): Promise<PaginatedRecords> {
  const searchParams = new URLSearchParams();
  if (params.region) searchParams.set('region', params.region);
  if (params.companyName) searchParams.set('company_name', params.companyName);
  if (params.billingPeriod) searchParams.set('billing_period', params.billingPeriod);
  if (params.page !== undefined) searchParams.set('page', String(params.page));
  if (params.pageSize !== undefined) searchParams.set('page_size', String(params.pageSize));

  const response = await apiClient.get<ApiSuccessResponse<PaginatedRecords>>(
    `/data-management/records?${searchParams.toString()}`,
  );
  return response.data.data;
}

export async function fetchFilterOptions(params?: {
  region?: string;
  companyName?: string;
}): Promise<FilterOptions> {
  const searchParams = new URLSearchParams();
  if (params?.region) searchParams.set('region', params.region);
  if (params?.companyName) searchParams.set('company_name', params.companyName);

  const qs = searchParams.toString();
  const url = qs ? `/data-management/filter-options?${qs}` : '/data-management/filter-options';
  const response = await apiClient.get<ApiSuccessResponse<FilterOptions>>(url);
  return response.data.data;
}

export async function fetchEmployeeSummary(params: {
  region?: string;
  companyName?: string;
  billingPeriod?: string;
  page?: number;
  pageSize?: number;
}): Promise<PaginatedEmployeeSummary> {
  const searchParams = new URLSearchParams();
  if (params.region) searchParams.set('region', params.region);
  if (params.companyName) searchParams.set('company_name', params.companyName);
  if (params.billingPeriod) searchParams.set('billing_period', params.billingPeriod);
  if (params.page !== undefined) searchParams.set('page', String(params.page));
  if (params.pageSize !== undefined) searchParams.set('page_size', String(params.pageSize));

  const response = await apiClient.get<ApiSuccessResponse<PaginatedEmployeeSummary>>(
    `/data-management/summary/employees?${searchParams.toString()}`,
  );
  return response.data.data;
}

export async function fetchPeriodSummary(params: {
  region?: string;
  companyName?: string;
  page?: number;
  pageSize?: number;
}): Promise<PaginatedPeriodSummary> {
  const searchParams = new URLSearchParams();
  if (params.region) searchParams.set('region', params.region);
  if (params.companyName) searchParams.set('company_name', params.companyName);
  if (params.page !== undefined) searchParams.set('page', String(params.page));
  if (params.pageSize !== undefined) searchParams.set('page_size', String(params.pageSize));

  const response = await apiClient.get<ApiSuccessResponse<PaginatedPeriodSummary>>(
    `/data-management/summary/periods?${searchParams.toString()}`,
  );
  return response.data.data;
}
