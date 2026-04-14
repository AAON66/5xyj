import { useCallback, useEffect, useMemo, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useSemanticColors } from '../theme/useSemanticColors';
import {
  Alert,
  Button,
  Card,
  Col,
  Empty,
  Row,
  Select,
  Skeleton,
  Statistic,
  Table,
  Tag,
  Tooltip,
  Typography,
  message,
} from 'antd';
import type { ColumnsType } from 'antd/es/table';

import { useResponsiveViewport } from '../hooks/useResponsiveViewport';
import { fetchImportBatch, fetchImportBatches, type ImportBatchDetail, type ImportBatchSummary } from '../services/imports';
import { fetchHeaderMappings, updateHeaderMapping, type HeaderMappingItem, type MappingListParams } from '../services/mappings';

const { Title, Text } = Typography;

function mappingLabel(value: string): string {
  switch (value) {
    case 'rule': return '规则命中';
    case 'llm': return 'LLM 兜底';
    case 'manual': return '人工修正';
    case 'unmapped': return '未识别';
    default: return value;
  }
}

function mappingSourceColor(value: string): string {
  switch (value) {
    case 'rule': return 'success';
    case 'llm': return 'processing';
    case 'manual': return 'blue';
    case 'unmapped': return 'error';
    default: return 'default';
  }
}

function confidenceColor(confidence: number | null): string {
  if (confidence === null) return 'default';
  if (confidence >= 0.8) return 'success';
  if (confidence >= 0.5) return 'warning';
  return 'error';
}

function confidenceLabel(confidence: number | null): string {
  if (confidence === null) return '无置信度';
  if (confidence >= 0.8) return '高';
  if (confidence >= 0.5) return '中';
  return '低';
}

type ConfidenceRange = 'high' | 'medium' | 'low';

function confidenceRangeToParams(range: ConfidenceRange | undefined): { confidenceMin?: number; confidenceMax?: number } {
  switch (range) {
    case 'high': return { confidenceMin: 0.8 };
    case 'medium': return { confidenceMin: 0.5, confidenceMax: 0.8 };
    case 'low': return { confidenceMax: 0.5 };
    default: return {};
  }
}

export function MappingsPage() {
  const colors = useSemanticColors();
  const { isMobile } = useResponsiveViewport();
  const [searchParams, setSearchParams] = useSearchParams();
  const [batches, setBatches] = useState<ImportBatchSummary[]>([]);
  const [selectedBatchId, setSelectedBatchId] = useState<string | null>(searchParams.get('batchId'));
  const [selectedSourceFileId, setSelectedSourceFileId] = useState<string | null>(searchParams.get('sourceFileId'));
  const [batchDetail, setBatchDetail] = useState<ImportBatchDetail | null>(null);
  const [mappings, setMappings] = useState<HeaderMappingItem[]>([]);
  const [availableFields, setAvailableFields] = useState<string[]>([]);
  const [drafts, setDrafts] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [savingId, setSavingId] = useState<string | null>(null);
  const [batchSaving, setBatchSaving] = useState(false);
  const [pageError, setPageError] = useState<string | null>(null);

  // Filter state
  const [filterMappingSource, setFilterMappingSource] = useState<string | undefined>(undefined);
  const [filterConfidence, setFilterConfidence] = useState<ConfidenceRange | undefined>(undefined);

  useEffect(() => {
    let active = true;
    async function loadBatches() {
      try {
        const result = await fetchImportBatches();
        if (!active) return;
        setBatches(result);
        setPageError(null);
        const initialBatchId = searchParams.get('batchId') ?? result[0]?.id ?? null;
        setSelectedBatchId((current) => current ?? initialBatchId);
      } catch {
        if (active) setPageError('字段映射页面暂时无法读取批次列表。');
      } finally {
        if (active) setLoading(false);
      }
    }
    void loadBatches();
    return () => { active = false; };
  }, [searchParams]);

  const loadMappings = useCallback(async (batchId: string, sourceFileId: string | null) => {
    try {
      const params: MappingListParams = {
        batchId,
        sourceFileId: sourceFileId ?? undefined,
        mappingSource: filterMappingSource,
        ...confidenceRangeToParams(filterConfidence),
      };
      const [detail, mappingPayload] = await Promise.all([
        fetchImportBatch(batchId),
        fetchHeaderMappings(params),
      ]);
      setBatchDetail(detail);
      setMappings(mappingPayload.items);
      setAvailableFields(mappingPayload.available_canonical_fields);
      const nextSourceFileId = sourceFileId ?? mappingPayload.items[0]?.source_file_id ?? detail.source_files[0]?.id ?? null;
      setSelectedSourceFileId(nextSourceFileId);
      setDrafts(Object.fromEntries(mappingPayload.items.map((item) => [item.id, item.canonical_field ?? ''])));
      setPageError(null);
    } catch {
      setPageError('当前批次的映射记录加载失败，请稍后重试。');
    }
  }, [filterMappingSource, filterConfidence]);

  useEffect(() => {
    if (!selectedBatchId) {
      setBatchDetail(null);
      setMappings([]);
      setAvailableFields([]);
      setDrafts({});
      return;
    }
    void loadMappings(selectedBatchId, selectedSourceFileId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedBatchId, selectedSourceFileId, filterMappingSource, filterConfidence]);

  useEffect(() => {
    const params = new URLSearchParams();
    if (selectedBatchId) params.set('batchId', selectedBatchId);
    if (selectedSourceFileId) params.set('sourceFileId', selectedSourceFileId);
    setSearchParams(params, { replace: true });
  }, [selectedBatchId, selectedSourceFileId, setSearchParams]);

  const sourceFiles = batchDetail?.source_files ?? [];
  const visibleMappings = useMemo(() => {
    if (!selectedSourceFileId) return mappings;
    return mappings.filter((item) => item.source_file_id === selectedSourceFileId);
  }, [mappings, selectedSourceFileId]);

  const summary = useMemo(
    () => ({
      total: visibleMappings.length,
      manual: visibleMappings.filter((item) => item.mapping_source === 'manual' || item.manually_overridden).length,
      unmapped: visibleMappings.filter((item) => !item.canonical_field).length,
    }),
    [visibleMappings],
  );

  // Track dirty rows (rows where draft differs from saved value)
  const dirtyIds = useMemo(() => {
    const dirty = new Set<string>();
    for (const item of visibleMappings) {
      const draftValue = drafts[item.id] ?? '';
      const savedValue = item.canonical_field ?? '';
      if (draftValue !== savedValue) dirty.add(item.id);
    }
    return dirty;
  }, [visibleMappings, drafts]);

  async function handleSave(mapping: HeaderMappingItem) {
    const nextValue = drafts[mapping.id] || null;
    setSavingId(mapping.id);
    try {
      const updated = await updateHeaderMapping(mapping.id, nextValue);
      setMappings((current) => current.map((item) => (item.id === updated.id ? updated : item)));
      setDrafts((current) => ({ ...current, [mapping.id]: updated.canonical_field ?? '' }));
      message.success(`已更新字段映射：${mapping.raw_header}`);
    } catch {
      message.error(`保存失败：${mapping.raw_header}`);
    } finally {
      setSavingId(null);
    }
  }

  async function handleBatchSave() {
    if (dirtyIds.size === 0) return;
    setBatchSaving(true);
    let savedCount = 0;
    let failCount = 0;
    try {
      for (const id of dirtyIds) {
        const nextValue = drafts[id] || null;
        try {
          const updated = await updateHeaderMapping(id, nextValue);
          setMappings((current) => current.map((item) => (item.id === updated.id ? updated : item)));
          setDrafts((current) => ({ ...current, [id]: updated.canonical_field ?? '' }));
          savedCount++;
        } catch {
          failCount++;
        }
      }
      if (failCount === 0) {
        message.success(`已保存 ${savedCount} 条映射修正`);
      } else {
        message.warning(`已保存 ${savedCount} 条，${failCount} 条保存失败`);
      }
    } finally {
      setBatchSaving(false);
    }
  }

  const mappingColumns: ColumnsType<HeaderMappingItem> = [
    {
      title: '原始字段名',
      dataIndex: 'raw_header',
      key: 'raw_header',
      fixed: 'left',
      width: 220,
      render: (val: string, record: HeaderMappingItem) => (
        <div>
          <Text strong>{val}</Text>
          <br />
          <Text type="secondary" style={{ fontSize: 12 }}>{record.raw_header_signature}</Text>
        </div>
      ),
    },
    {
      title: '标准字段',
      key: 'canonical_field',
      width: 200,
      render: (_: unknown, record: HeaderMappingItem) => (
        <Select
          style={{ width: '100%' }}
          size="small"
          value={drafts[record.id] || undefined}
          placeholder="保持未识别"
          allowClear
          onChange={(val) => setDrafts((current) => ({ ...current, [record.id]: val ?? '' }))}
          options={availableFields.map((f) => ({ value: f, label: f }))}
        />
      ),
    },
    {
      title: '置信度',
      dataIndex: 'confidence',
      key: 'confidence',
      width: 100,
      render: (val: number | null) => (
        <Tag color={confidenceColor(val)}>
          {confidenceLabel(val)} {val !== null ? `(${val.toFixed(2)})` : ''}
        </Tag>
      ),
    },
    {
      title: '来源',
      dataIndex: 'mapping_source',
      key: 'mapping_source',
      width: 120,
      render: (val: string, record: HeaderMappingItem) => (
        <>
          <Tag color={mappingSourceColor(val)}>{mappingLabel(val)}</Tag>
          {record.manually_overridden && (
            <Tooltip title="已手动修正">
              <Tag color="green">手动</Tag>
            </Tooltip>
          )}
        </>
      ),
    },
    {
      title: '文件',
      dataIndex: 'source_file_name',
      key: 'source_file_name',
      ellipsis: true,
      responsive: ['lg'],
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_: unknown, record: HeaderMappingItem) => (
        <Button
          type="primary"
          size="small"
          onClick={() => void handleSave(record)}
          loading={savingId === record.id}
          disabled={batchSaving || !dirtyIds.has(record.id)}
        >
          保存修正
        </Button>
      ),
    },
  ];

  return (
    <div>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: isMobile ? 'stretch' : 'center',
          marginBottom: 16,
          flexWrap: 'wrap',
          gap: 12,
          flexDirection: isMobile ? 'column' : 'row',
        }}
      >
        <Title level={4} style={{ margin: 0 }}>映射修正</Title>
        {selectedBatchId && (
          <Link to={`/imports/${selectedBatchId}`}>
            <Button>返回批次详情</Button>
          </Link>
        )}
      </div>

      <Alert
        type="warning"
        showIcon
        message="映射修正仅影响当前已导入文件，后续导入仍使用自动映射。如需永久修改映射规则，请联系管理员。"
        style={{ marginBottom: 16 }}
      />

      {pageError && (
        <Alert type="error" message="页面状态异常" description={pageError} style={{ marginBottom: 16 }} />
      )}

      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col xs={24} md={8}>
          <Card title="筛选条件">
            {loading ? (
              <Skeleton active paragraph={{ rows: 2 }} />
            ) : (
              <>
                <div style={{ marginBottom: 12 }}>
                  <Text type="secondary" style={{ display: 'block', marginBottom: 4 }}>导入批次</Text>
                  <Select
                    style={{ width: '100%' }}
                    placeholder="请选择批次"
                    value={selectedBatchId}
                    onChange={(val) => setSelectedBatchId(val || null)}
                    options={batches.map((b) => ({ value: b.id, label: b.batch_name }))}
                    allowClear
                  />
                </div>
                <div style={{ marginBottom: 12 }}>
                  <Text type="secondary" style={{ display: 'block', marginBottom: 4 }}>源文件</Text>
                  <Select
                    style={{ width: '100%' }}
                    placeholder="全部文件"
                    value={selectedSourceFileId}
                    onChange={(val) => setSelectedSourceFileId(val || null)}
                    disabled={!sourceFiles.length}
                    allowClear
                    options={sourceFiles.map((f) => ({ value: f.id, label: f.file_name }))}
                  />
                </div>
                <div style={{ marginBottom: 12 }}>
                  <Text type="secondary" style={{ display: 'block', marginBottom: 4 }}>映射来源</Text>
                  <Select
                    style={{ width: '100%' }}
                    placeholder="映射来源"
                    value={filterMappingSource}
                    onChange={(val) => setFilterMappingSource(val || undefined)}
                    allowClear
                    options={[
                      { label: '规则映射', value: 'rule' },
                      { label: 'LLM映射', value: 'llm' },
                      { label: '手动修正', value: 'manual' },
                      { label: '未映射', value: 'unmapped' },
                    ]}
                  />
                </div>
                <div>
                  <Text type="secondary" style={{ display: 'block', marginBottom: 4 }}>置信度</Text>
                  <Select
                    style={{ width: '100%' }}
                    placeholder="置信度"
                    value={filterConfidence}
                    onChange={(val) => setFilterConfidence(val || undefined)}
                    allowClear
                    options={[
                      { label: '高 (>=80%)', value: 'high' },
                      { label: '中 (50%-80%)', value: 'medium' },
                      { label: '低 (<50%)', value: 'low' },
                    ]}
                  />
                </div>
              </>
            )}
          </Card>
        </Col>
        <Col xs={24} md={16}>
          <Card>
            <Row gutter={[16, 16]}>
              <Col xs={24} sm={8}>
                <Statistic title="当前映射条目" value={summary.total} />
              </Col>
              <Col xs={24} sm={8}>
                <Statistic title="人工修正条目" value={summary.manual} valueStyle={{ color: colors.BRAND }} />
              </Col>
              <Col xs={24} sm={8}>
                <Statistic title="仍未识别条目" value={summary.unmapped} valueStyle={{ color: colors.ERROR }} />
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>

      <Card
        title="映射清单"
        extra={
          dirtyIds.size > 0 ? (
            <Button
              type="primary"
              onClick={() => void handleBatchSave()}
              loading={batchSaving}
            >
              批量保存 ({dirtyIds.size})
            </Button>
          ) : null
        }
      >
        {loading ? (
          <Skeleton active paragraph={{ rows: 4 }} />
        ) : visibleMappings.length ? (
          <Table
            size="small"
            columns={mappingColumns}
            dataSource={visibleMappings}
            rowKey="id"
            scroll={{ x: 'max-content' }}
            pagination={{ pageSize: 20, showSizeChanger: true }}
          />
        ) : (
          <Empty description="当前批次还没有可修正的映射记录。请先完成解析，或切换到有预览结果的文件。" />
        )}
      </Card>
    </div>
  );
}
