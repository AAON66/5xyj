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

export async function fetchHeaderMappings(batchId?: string, sourceFileId?: string): Promise<HeaderMappingList> {
  const response = await apiClient.get<ApiSuccessResponse<HeaderMappingList>>('/mappings', {
    params: {
      batch_id: batchId || undefined,
      source_file_id: sourceFileId || undefined,
    },
  });
  return response.data.data;
}

export async function updateHeaderMapping(mappingId: string, canonicalField: string | null): Promise<HeaderMappingItem> {
  const response = await apiClient.patch<ApiSuccessResponse<HeaderMappingItem>>(`/mappings/${mappingId}`, {
    canonical_field: canonicalField,
  });
  return response.data.data;
}
