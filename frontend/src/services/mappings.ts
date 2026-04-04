import type { ApiSuccessResponse } from './api';
import { apiClient } from './api';

export interface HeaderMappingItem {
  id: string;
  batch_id: string;
  batch_name: string;
  source_file_id: string;
  source_file_name: string;
  raw_header: string;
  raw_header_signature: string;
  canonical_field: string | null;
  mapping_source: string;
  confidence: number | null;
  candidate_fields: string[];
  manually_overridden: boolean;
}

export interface HeaderMappingList {
  items: HeaderMappingItem[];
  available_canonical_fields: string[];
}

export interface MappingListParams {
  batchId?: string;
  sourceFileId?: string;
  mappingSource?: string;
  confidenceMin?: number;
  confidenceMax?: number;
}

export async function fetchHeaderMappings(
  batchIdOrParams?: string | MappingListParams,
  sourceFileId?: string,
): Promise<HeaderMappingList> {
  let params: Record<string, string | number | undefined>;

  if (typeof batchIdOrParams === 'object' && batchIdOrParams !== null) {
    params = {
      batch_id: batchIdOrParams.batchId || undefined,
      source_file_id: batchIdOrParams.sourceFileId || undefined,
      mapping_source: batchIdOrParams.mappingSource || undefined,
      confidence_min: batchIdOrParams.confidenceMin,
      confidence_max: batchIdOrParams.confidenceMax,
    };
  } else {
    params = {
      batch_id: batchIdOrParams || undefined,
      source_file_id: sourceFileId || undefined,
    };
  }

  const response = await apiClient.get<ApiSuccessResponse<HeaderMappingList>>('/mappings', { params });
  return response.data.data;
}

export async function updateHeaderMapping(mappingId: string, canonicalField: string | null): Promise<HeaderMappingItem> {
  const response = await apiClient.patch<ApiSuccessResponse<HeaderMappingItem>>(`/mappings/${mappingId}`, {
    canonical_field: canonicalField,
  });
  return response.data.data;
}
