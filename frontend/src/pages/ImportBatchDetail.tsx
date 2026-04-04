import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import {
  Alert,
  Button,
  Card,
  Col,
  Descriptions,
  Empty,
  message,
  Row,
  Select,
  Skeleton,
  Space,
  Table,
  Tag,
  Typography,
} from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { ArrowLeftOutlined, ReloadOutlined } from '@ant-design/icons';

import {
  fetchImportBatch,
  fetchImportBatchPreview,
  parseImportBatch,
  type HeaderMappingPreview,
  type ImportBatchDetail,
  type SourceFilePreview,
} from '../services/imports';
import {
  fetchHeaderMappings,
  updateHeaderMapping,
  type HeaderMappingItem,
} from '../services/mappings';

const { Title } = Typography;

function formatDateTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat('zh-CN', { dateStyle: 'medium', timeStyle: 'short' }).format(date);
}

function formatValue(value: unknown): string {
  if (value === null || value === undefined || value === '') return '-';
  if (typeof value === 'object') return JSON.stringify(value);
  return String(value);
}

function summarizeMapping(mapping: HeaderMappingPreview): string {
  if (mapping.canonical_field) return mapping.canonical_field;
  if (mapping.candidate_fields.length > 0) return `候选: ${mapping.candidate_fields.join(', ')}`;
  return '未识别';
}

function statusTagColor(status: string): string {
  switch (status) {
    case 'parsed': case 'completed': return 'success';
    case 'processing': case 'parsing': return 'processing';
    case 'error': case 'failed': return 'error';
    default: return 'default';
  }
}

function mappingSourceColor(value: string): string {
  switch (value) {
    case 'rule': return 'blue';
    case 'llm': return 'purple';
    case 'manual': return 'green';
    case 'unmapped': return 'red';
    default: return 'default';
  }
}

function confidenceColor(confidence: number | null): string {
  if (confidence === null) return 'default';
  if (confidence >= 0.8) return '#00B42A';
  if (confidence >= 0.5) return '#FF7D00';
  return '#F54A45';
}

export function ImportBatchDetailPage() {
  const { batchId } = useParams<{ batchId: string }>();
  const navigate = useNavigate();
  const [batchDetail, setBatchDetail] = useState<ImportBatchDetail | null>(null);
  const [previewByFileId, setPreviewByFileId] = useState<Record<string, SourceFilePreview>>({});
  const [selectedSourceFileId, setSelectedSourceFileId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [parsing, setParsing] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [pageError, setPageError] = useState<string | null>(null);

  // Inline mapping editor state
  const [inlineMappings, setInlineMappings] = useState<HeaderMappingItem[]>([]);
  const [inlineAvailableFields, setInlineAvailableFields] = useState<string[]>([]);
  const [inlineDrafts, setInlineDrafts] = useState<Record<string, string>>({});
  const [inlineSavingId, setInlineSavingId] = useState<string | null>(null);
  const [inlineMappingsLoading, setInlineMappingsLoading] = useState(false);

  useEffect(() => {
    let active = true;
    async function loadBatch() {
      if (!batchId) { setLoading(false); return; }
      try {
        const detailResult = await fetchImportBatch(batchId);
        if (!active) return;
        setBatchDetail(detailResult);
        setPreviewByFileId({});
        setPageError(null);
        const firstSourceFileId = detailResult.source_files[0]?.id ?? null;
        setSelectedSourceFileId((current) => current ?? firstSourceFileId);
      } catch {
        if (active) setPageError('导入批次详情暂时加载失败，请稍后重试。');
      } finally {
        if (active) setLoading(false);
      }
    }
    void loadBatch();
    return () => { active = false; };
  }, [batchId]);

  const selectedSourceFile = useMemo<SourceFilePreview | null>(() => {
    if (!selectedSourceFileId) return null;
    return previewByFileId[selectedSourceFileId] ?? null;
  }, [previewByFileId, selectedSourceFileId]);

  const previewColumns = useMemo(() => {
    const firstRecord = selectedSourceFile?.preview_records[0];
    return firstRecord ? Object.keys(firstRecord.values) : [];
  }, [selectedSourceFile]);

  useEffect(() => {
    let active = true;
    async function loadSelectedSourcePreview(targetBatchId: string, targetSourceFileId: string) {
      if (previewByFileId[targetSourceFileId]) return;
      setPreviewLoading(true);
      try {
        const previewResult = await fetchImportBatchPreview(targetBatchId, { sourceFileId: targetSourceFileId });
        if (!active) return;
        const filePreview = previewResult.source_files[0];
        if (filePreview) setPreviewByFileId((current) => ({ ...current, [targetSourceFileId]: filePreview }));
        setPageError(null);
      } catch {
        if (active) setPageError('当前文件预览加载失败，请稍后重试。');
      } finally {
        if (active) setPreviewLoading(false);
      }
    }
    if (!batchId || !selectedSourceFileId || batchDetail?.status === 'uploaded') return () => { active = false; };
    void loadSelectedSourcePreview(batchId, selectedSourceFileId);
    return () => { active = false; };
  }, [batchDetail?.status, batchId, previewByFileId, selectedSourceFileId]);

  async function reloadBatchState(targetBatchId: string, preferredSourceFileId?: string | null) {
    setRefreshing(true);
    try {
      const detailResult = await fetchImportBatch(targetBatchId);
      setBatchDetail(detailResult);
      const nextSourceFileId = preferredSourceFileId ?? detailResult.source_files[0]?.id ?? null;
      setSelectedSourceFileId(nextSourceFileId);
      setPageError(null);
      if (nextSourceFileId) {
        const previewResult = await fetchImportBatchPreview(targetBatchId, { sourceFileId: nextSourceFileId }).catch(() => null);
        const filePreview = previewResult?.source_files[0] ?? null;
        if (filePreview) setPreviewByFileId((current) => ({ ...current, [nextSourceFileId]: filePreview }));
      }
    } catch {
      setPageError('批次详情刷新失败，请稍后重试。');
    } finally {
      setRefreshing(false);
    }
  }

  // Load inline mappings for the current batch
  useEffect(() => {
    let active = true;
    async function loadInlineMappings() {
      if (!batchId) return;
      setInlineMappingsLoading(true);
      try {
        const mappingPayload = await fetchHeaderMappings(batchId);
        if (!active) return;
        setInlineMappings(mappingPayload.items);
        setInlineAvailableFields(mappingPayload.available_canonical_fields);
        setInlineDrafts(Object.fromEntries(mappingPayload.items.map((item) => [item.id, item.canonical_field ?? ''])));
      } catch {
        // Silently fail - inline mappings are supplementary
      } finally {
        if (active) setInlineMappingsLoading(false);
      }
    }
    void loadInlineMappings();
    return () => { active = false; };
  }, [batchId, batchDetail?.status]);

  const inlineDirtyIds = useMemo(() => {
    const dirty = new Set<string>();
    for (const item of inlineMappings) {
      const draftValue = inlineDrafts[item.id] ?? '';
      const savedValue = item.canonical_field ?? '';
      if (draftValue !== savedValue) dirty.add(item.id);
    }
    return dirty;
  }, [inlineMappings, inlineDrafts]);

  async function handleInlineSave(mapping: HeaderMappingItem) {
    const nextValue = inlineDrafts[mapping.id] || null;
    setInlineSavingId(mapping.id);
    try {
      const updated = await updateHeaderMapping(mapping.id, nextValue);
      setInlineMappings((current) => current.map((item) => (item.id === updated.id ? updated : item)));
      setInlineDrafts((current) => ({ ...current, [mapping.id]: updated.canonical_field ?? '' }));
      message.success('映射已更新');
    } catch {
      message.error(`保存失败：${mapping.raw_header}`);
    } finally {
      setInlineSavingId(null);
    }
  }

  const inlineMappingColumns: ColumnsType<HeaderMappingItem> = [
    {
      title: '原始表头',
      dataIndex: 'raw_header',
      key: 'raw_header',
      width: 200,
    },
    {
      title: '标准字段',
      key: 'canonical_field',
      width: 200,
      render: (_: unknown, record: HeaderMappingItem) => (
        <Select
          style={{ width: '100%' }}
          size="small"
          value={inlineDrafts[record.id] || undefined}
          placeholder="保持未识别"
          allowClear
          onChange={(val) => setInlineDrafts((current) => ({ ...current, [record.id]: val ?? '' }))}
          options={inlineAvailableFields.map((f) => ({ value: f, label: f }))}
        />
      ),
    },
    {
      title: '映射来源',
      dataIndex: 'mapping_source',
      key: 'mapping_source',
      width: 100,
      render: (val: string) => <Tag color={mappingSourceColor(val)}>{val}</Tag>,
    },
    {
      title: '置信度',
      dataIndex: 'confidence',
      key: 'confidence',
      width: 100,
      render: (val: number | null) => (
        val !== null ? (
          <span style={{ color: confidenceColor(val) }}>{(val * 100).toFixed(0)}%</span>
        ) : (
          <span style={{ color: '#999' }}>-</span>
        )
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_: unknown, record: HeaderMappingItem) => (
        <Button
          size="small"
          onClick={() => void handleInlineSave(record)}
          loading={inlineSavingId === record.id}
          disabled={!inlineDirtyIds.has(record.id)}
        >
          保存修正
        </Button>
      ),
    },
  ];

  async function handleParseBatch() {
    if (!batchId) return;
    setParsing(true);
    try {
      const parsed = await parseImportBatch(batchId);
      setPreviewByFileId(Object.fromEntries(parsed.source_files.map((item) => [item.source_file_id, item])));
      const nextSourceFileId = selectedSourceFileId ?? parsed.source_files[0]?.source_file_id ?? null;
      setSelectedSourceFileId(nextSourceFileId);
      await reloadBatchState(batchId, nextSourceFileId);
      message.success('批次解析已刷新');
    } finally {
      setParsing(false);
    }
  }

  if (loading) {
    return (
      <div>
        <Skeleton active paragraph={{ rows: 10 }} />
      </div>
    );
  }

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Link to="/imports">
          <Button icon={<ArrowLeftOutlined />}>返回批次列表</Button>
        </Link>
        <Title level={4} style={{ margin: 0 }}>{batchDetail?.batch_name ?? '导入批次详情'}</Title>
      </Space>

      {pageError && <Card style={{ marginBottom: 16, borderColor: '#F54A45' }}><Typography.Text type="danger">{pageError}</Typography.Text></Card>}

      {/* Batch info */}
      <Card style={{ marginBottom: 16 }}>
        <Descriptions bordered column={2} size="small">
          <Descriptions.Item label="批次名称">{batchDetail?.batch_name ?? '-'}</Descriptions.Item>
          <Descriptions.Item label="文件数">{batchDetail?.file_count ?? '-'}</Descriptions.Item>
          <Descriptions.Item label="创建时间">{batchDetail ? formatDateTime(batchDetail.created_at) : '-'}</Descriptions.Item>
          <Descriptions.Item label="最后更新">{batchDetail ? formatDateTime(batchDetail.updated_at) : '-'}</Descriptions.Item>
          <Descriptions.Item label="状态">
            {batchDetail ? <Tag color={statusTagColor(batchDetail.status)}>{batchDetail.status}</Tag> : '-'}
          </Descriptions.Item>
          <Descriptions.Item label="预览文件数">{Object.keys(previewByFileId).length}</Descriptions.Item>
        </Descriptions>
        <Space style={{ marginTop: 12 }}>
          {batchId && (
            <Link to={`/mappings?batchId=${batchId}${selectedSourceFileId ? `&sourceFileId=${selectedSourceFileId}` : ''}`}>
              <Button>进入字段修正</Button>
            </Link>
          )}
          <Button
            type="primary"
            icon={<ReloadOutlined />}
            onClick={() => void handleParseBatch()}
            disabled={!batchId || parsing}
            loading={parsing}
          >
            刷新解析结果
          </Button>
        </Space>
      </Card>

      {/* Source files */}
      <Card title="源文件列表" style={{ marginBottom: 16 }}>
        {batchDetail?.source_files.length ? (
          <Row gutter={[12, 12]}>
            {batchDetail.source_files.map((file) => {
              const isActive = selectedSourceFile?.source_file_id === file.id;
              return (
                <Col key={file.id} xs={24} sm={12} md={8} lg={6}>
                  <Card
                    size="small"
                    hoverable
                    onClick={() => setSelectedSourceFileId(file.id)}
                    style={{ borderColor: isActive ? '#3370FF' : undefined }}
                  >
                    <Typography.Text strong ellipsis>{file.file_name}</Typography.Text>
                    <div><Typography.Text type="secondary">{file.region ?? '自动识别地区'}</Typography.Text></div>
                    <div><Typography.Text type="secondary">{file.company_name ?? '未提供公司名'}</Typography.Text></div>
                    <div><Typography.Text type="secondary">{Math.max(1, Math.round(file.file_size / 1024))} KB</Typography.Text></div>
                  </Card>
                </Col>
              );
            })}
          </Row>
        ) : (
          <Empty description="当前批次没有源文件" />
        )}
      </Card>

      {/* Selected file summary */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={12}>
          <Card>
            <Typography.Text type="secondary">命中工作表</Typography.Text>
            <Title level={5}>{selectedSourceFile ? selectedSourceFile.raw_sheet_name : '尚未解析'}</Title>
            <Typography.Text>
              {selectedSourceFile
                ? `${selectedSourceFile.normalized_record_count} 条标准化记录，过滤 ${selectedSourceFile.filtered_row_count} 条非明细行。`
                : '运行解析后显示当前文件命中的工作表。'}
            </Typography.Text>
          </Card>
        </Col>
        <Col span={12}>
          <Card>
            <Typography.Text type="secondary">表头签名</Typography.Text>
            <Title level={5} style={{ wordBreak: 'break-all' }}>{selectedSourceFile?.raw_header_signature ?? '尚未生成'}</Title>
            <Typography.Text>{selectedSourceFile ? '用于追踪规则命中和后续人工修正。' : '解析完成后展示签名。'}</Typography.Text>
          </Card>
        </Col>
      </Row>

      {previewLoading && <Card style={{ marginBottom: 16 }}><Skeleton active paragraph={{ rows: 4 }} /></Card>}

      {/* Header mappings and filtered rows */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={12}>
          <Card title="映射结果 - 表头识别与规则归一化">
            {selectedSourceFile?.header_mappings.length ? (
              selectedSourceFile.header_mappings.map((mapping) => (
                <div key={mapping.raw_header_signature} style={{ marginBottom: 8 }}>
                  <Typography.Text strong>{mapping.raw_header}</Typography.Text>
                  {' '}
                  <Tag color={mapping.canonical_field ? 'success' : 'warning'}>{summarizeMapping(mapping)}</Tag>
                  <div>
                    <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                      {mapping.raw_header_signature} | 来源 {mapping.mapping_source}
                      {mapping.confidence !== null ? ` | 置信度 ${mapping.confidence.toFixed(2)}` : ''}
                      {mapping.llm_attempted ? ` | LLM ${mapping.llm_status}` : ''}
                    </Typography.Text>
                  </div>
                </div>
              ))
            ) : (
              <Empty description="暂无映射结果" image={Empty.PRESENTED_IMAGE_SIMPLE} />
            )}
          </Card>
        </Col>
        <Col span={12}>
          <Card title="过滤结果 - 非明细行">
            {selectedSourceFile?.filtered_rows.length ? (
              selectedSourceFile.filtered_rows.map((row) => (
                <div key={`${row.row_number}-${row.reason}`} style={{ marginBottom: 8 }}>
                  <Tag>第 {row.row_number} 行</Tag>
                  <Typography.Text>{row.reason}</Typography.Text>
                  <div><Typography.Text type="secondary" style={{ fontSize: 12 }}>{row.first_value}</Typography.Text></div>
                </div>
              ))
            ) : (
              <Empty description="没有过滤项" image={Empty.PRESENTED_IMAGE_SIMPLE} />
            )}
          </Card>
        </Col>
      </Row>

      {/* Sample records */}
      <Card title="标准化预览 - 前 20 行标准字段样本" style={{ marginBottom: 16 }}>
        {selectedSourceFile?.preview_records.length ? (
          <Table
            size="small"
            scroll={{ x: true }}
            pagination={false}
            dataSource={selectedSourceFile.preview_records}
            rowKey="source_row_number"
            columns={[
              { title: '源行号', dataIndex: 'source_row_number', key: 'source_row_number', width: 80, fixed: 'left' as const },
              ...previewColumns.map((col) => ({
                title: col,
                key: col,
                render: (_: unknown, record: (typeof selectedSourceFile.preview_records)[0]) => formatValue(record.values[col]),
              })),
            ]}
          />
        ) : (
          <Empty description="暂无标准化样本" />
        )}
      </Card>

      {/* Unmapped fields */}
      <Card title="未识别字段 - 待后续映射或人工修正">
        {selectedSourceFile?.preview_records.some((record) => Object.keys(record.unmapped_values).length > 0) ? (
          <Row gutter={[12, 12]}>
            {selectedSourceFile.preview_records
              .filter((record) => Object.keys(record.unmapped_values).length > 0)
              .slice(0, 6)
              .map((record) => (
                <Col key={`unmapped-${record.source_row_number}`} xs={24} sm={12} md={8}>
                  <Card size="small">
                    <Typography.Text strong>第 {record.source_row_number} 行</Typography.Text>
                    {Object.entries(record.unmapped_values).map(([key, value]) => (
                      <div key={key}>{key}: {formatValue(value)}</div>
                    ))}
                  </Card>
                </Col>
              ))}
          </Row>
        ) : (
          <Empty description="没有未识别字段" image={Empty.PRESENTED_IMAGE_SIMPLE} />
        )}
      </Card>

      {/* Inline mapping editor (D-12) */}
      <Card
        title="字段映射"
        style={{ marginTop: 16 }}
        extra={
          <Button type="link" onClick={() => navigate(`/mappings?batchId=${batchId}`)}>
            查看完整映射管理
          </Button>
        }
      >
        <Alert
          type="warning"
          showIcon
          message="映射修正仅影响当前已导入文件，后续导入仍使用自动映射。"
          style={{ marginBottom: 12 }}
          banner
        />
        {inlineMappingsLoading ? (
          <Skeleton active paragraph={{ rows: 4 }} />
        ) : inlineMappings.length > 0 ? (
          <Table
            size="small"
            columns={inlineMappingColumns}
            dataSource={inlineMappings}
            rowKey="id"
            pagination={{ pageSize: 10, showSizeChanger: true }}
          />
        ) : (
          <Empty description="当前批次还没有可修正的映射记录。请先完成解析，或切换到有预览结果的文件。" />
        )}
      </Card>
    </div>
  );
}
