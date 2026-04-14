import type { ApiSuccessResponse } from "./api";
import { apiClient } from "./api";

export type FusionRuleScopeType = "employee_id" | "id_number";
export type FusionRuleFieldName = "personal_social_burden" | "personal_housing_burden";

export interface FusionRule {
  id: string;
  scope_type: FusionRuleScopeType;
  scope_value: string;
  field_name: FusionRuleFieldName;
  override_value: string;
  note: string | null;
  is_active: boolean;
  created_by: string | null;
  created_at: string;
  updated_at: string;
}

export interface FusionRuleCreateInput {
  scope_type: FusionRuleScopeType;
  scope_value: string;
  field_name: FusionRuleFieldName;
  override_value: string;
  note?: string | null;
}

export interface FusionRuleUpdateInput {
  scope_type?: FusionRuleScopeType;
  scope_value?: string;
  field_name?: FusionRuleFieldName;
  override_value?: string;
  note?: string | null;
  is_active?: boolean;
}

export async function fetchFusionRules(params?: {
  isActive?: boolean;
  fieldName?: FusionRuleFieldName;
}): Promise<FusionRule[]> {
  const response = await apiClient.get<ApiSuccessResponse<FusionRule[]>>("/fusion-rules", {
    params: {
      is_active: params?.isActive,
      field_name: params?.fieldName,
    },
  });
  return response.data.data;
}

export async function createFusionRule(payload: FusionRuleCreateInput): Promise<FusionRule> {
  const response = await apiClient.post<ApiSuccessResponse<FusionRule>>("/fusion-rules", payload);
  return response.data.data;
}

export async function updateFusionRule(ruleId: string, payload: FusionRuleUpdateInput): Promise<FusionRule> {
  const response = await apiClient.put<ApiSuccessResponse<FusionRule>>(`/fusion-rules/${ruleId}`, payload);
  return response.data.data;
}

export async function deleteFusionRule(ruleId: string): Promise<void> {
  await apiClient.delete(`/fusion-rules/${ruleId}`);
}
