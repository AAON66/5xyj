import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Button,
  Card,
  Col,
  Empty,
  Input,
  message,
  Modal,
  Row,
  Select,
  Skeleton,
  Space,
  Table,
  Tag,
  Typography,
  Upload,
} from 'antd';
import { InboxOutlined, DeleteOutlined, ReloadOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';

import { normalizeApiError } from '../services/api';
import { useSemanticColors } from '../theme/useSemanticColors';
import {
  bulkDeleteImportBatches,
  createImportBatch,
  deleteImportBatch,
  fetchBatchDeletionImpact,
  fetchImportBatches,
  fetchImportBatch,
  fetchImportBatchPreview,
  parseImportBatch,
  type HeaderMappingPreview,
  type ImportBatchDetail,
  type ImportBatchPreview,
  type ImportBatchSummary,
  type SourceFilePreview,
} from '../services/imports';

const { Title } = Typography;
const { Dragger } = Upload;

const PRESET_REGIONS = [
  { value: '', label: '自动识别 / 不指定' },
  { value: 'guangzhou', label: '广州' },
  { value: 'hangzhou', label: '杭州' },
  { value: 'xiamen', label: '厦门' },
  { value: 'shenzhen', label: '深圳' },
  { value: 'wuhan', label: '武汉' },
  { value: 'changsha', label: '长沙' },
];

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

export function ImportsPage() {
  const colors = useSemanticColors();
  const [batches, setBatches] = useState<ImportBatchSummary[]>([]);
  const [selectedBatchId, setSelectedBatchId] = useState<string | null>(null);
  const [selectedBatch, setSelectedBatch] = useState<ImportBatchDetail | null>(null);
  const [preview, setPreview] = useState<ImportBatchPreview | null>(null);
  const [batchName, setBatchName] = useState('');
  const [region, setRegion] = useState('');
  const [companyName, setCompanyName] = useState('');
  const [files, setFiles] = useState<File[]>([]);
  const [pageLoading, setPageLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [parsing, setParsing] = useState(false);
  const [deletingBatchId, setDeletingBatchId] = useState<string | null>(null);
  const [bulkDeleting, setBulkDeleting] = useState(false);
  const [selectedBatchIds, setSelectedBatchIds] = useState<string[]>([]);
  const [refreshingPreview, setRefreshingPreview] = useState(false);
  const [pageError, setPageError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    async function loadBatches() {
      try {
        const result = await fetchImportBatches();
        if (!active) return;
        setBatches(result);
        setPageError(null);
        if (result[0]) setSelectedBatchId(result[0].id);
      } catch {
        if (active) setPageError('导入批次列表暂时加载失败，请稍后重试。');
      } finally {
        if (active) setPageLoading(false);
      }
    }
    void loadBatches();
    return () => { active = false; };
  }, []);

  useEffect(() => {
    let active = true;
    async function loadBatchState(batchId: string) {
      setRefreshingPreview(true);
      try {
        const detailResult = await fetchImportBatch(batchId);
        if (!active) return;
        const firstSourceFileId = detailResult.source_files[0]?.id;
        setSelectedBatch(detailResult);
        setPreview(null);
        setPageError(null);
        if (!firstSourceFileId || detailResult.status === 'uploaded') return;
        const previewResult = await fetchImportBatchPreview(batchId, { sourceFileId: firstSourceFileId }).catch(() => null);
        if (!active) return;
        setPreview(previewResult);
      } catch {
        if (active) setPageError('当前批次详情加载失败，请重新选择批次或稍后重试。');
      } finally {
        if (active) setRefreshingPreview(false);
      }
    }
    if (!selectedBatchId) { setSelectedBatch(null); setPreview(null); return; }
    void loadBatchState(selectedBatchId);
    return () => { active = false; };
  }, [selectedBatchId]);

  const selectedSourceFile = useMemo<SourceFilePreview | null>(() => preview?.source_files[0] ?? null, [preview]);
  const previewColumns = useMemo(() => {
    const firstRecord = selectedSourceFile?.preview_records[0];
    return firstRecord ? Object.keys(firstRecord.values) : [];
  }, [selectedSourceFile]);

  async function reloadBatches(selectBatchId?: string | null) {
    const result = await fetchImportBatches();
    setBatches(result);
    const availableIds = new Set(result.map((b) => b.id));
    setSelectedBatchIds((current) => current.filter((id) => availableIds.has(id)));
    if (selectBatchId !== undefined) {
      setSelectedBatchId(selectBatchId && availableIds.has(selectBatchId) ? selectBatchId : (result[0]?.id ?? null));
      return;
    }
    setSelectedBatchId((current) => {
      if (current && availableIds.has(current)) return current;
      return result[0]?.id ?? null;
    });
  }

  async function handleCreateBatch() {
    if (files.length === 0) { message.warning('请至少选择一个 Excel 文件。'); return; }
    setSubmitting(true);
    try {
      const created = await createImportBatch({ files, batchName, region, companyName });
      const parsed = await parseImportBatch(created.id);
      setPreview({ ...parsed, source_files: parsed.source_files.slice(0, 1) });
      setSelectedBatchId(created.id);
      setSelectedBatch(created);
      await reloadBatches(created.id);
      setFiles([]);
      setBatchName('');
      message.success(`导入批次已创建: ${created.batch_name}`);
    } finally {
      setSubmitting(false);
    }
  }

  async function handleParseBatch(batchId: string) {
    setParsing(true);
    try {
      const parsed = await parseImportBatch(batchId);
      setPreview({ ...parsed, source_files: parsed.source_files.slice(0, 1) });
      setSelectedBatchId(batchId);
      setSelectedBatch(await fetchImportBatch(batchId));
      await reloadBatches(batchId);
      message.success('批次解析已刷新');
    } finally {
      setParsing(false);
    }
  }

  async function handleDeleteBatch(batchId: string, name: string) {
    setDeletingBatchId(batchId);
    try {
      const impact = await fetchBatchDeletionImpact(batchId);
      Modal.confirm({
        title: '确认删除',
        content: (
          <div>
            <p>确认删除批次&ldquo;{name}&rdquo;吗？</p>
            <p>此操作将同时删除：</p>
            <ul>
              <li>{impact.record_count} 条明细记录</li>
              <li>{impact.match_count} 条匹配结果</li>
              <li>{impact.issue_count} 条校验问题</li>
            </ul>
            <p>删除后无法恢复。</p>
          </div>
        ),
        okText: '确认删除',
        okType: 'danger',
        onOk: async () => {
          await deleteImportBatch(batchId);
          await reloadBatches(selectedBatchId === batchId ? null : undefined);
          setSelectedBatchIds((c) => c.filter((id) => id !== batchId));
          message.success(`批次已删除: ${name}`);
        },
        onCancel: () => {
          setDeletingBatchId(null);
        },
      });
    } catch (error) {
      message.error(normalizeApiError(error).message || '获取删除影响信息失败');
    } finally {
      setDeletingBatchId(null);
    }
  }

  async function handleBulkDelete() {
    if (selectedBatchIds.length === 0) { message.warning('请先勾选至少一个批次。'); return; }
    Modal.confirm({
      title: '确认批量删除',
      content: `确认批量删除 ${selectedBatchIds.length} 个批次吗？此操作将同时删除所有关联的明细记录、匹配结果和校验问题。删除后无法恢复。`,
      okText: '确认删除',
      okType: 'danger',
      onOk: async () => {
        setBulkDeleting(true);
        try {
          const result = await bulkDeleteImportBatches(selectedBatchIds);
          const removedSelectedBatch = selectedBatchId ? selectedBatchIds.includes(selectedBatchId) : false;
          await reloadBatches(removedSelectedBatch ? null : undefined);
          setSelectedBatchIds([]);
          message.success(`已删除 ${result.deleted_count} 个批次`);
        } catch (error) {
          message.error(normalizeApiError(error).message || '批量删除失败');
        } finally {
          setBulkDeleting(false);
        }
      },
    });
  }

  // Batch list table columns
  const batchColumns: ColumnsType<ImportBatchSummary> = useMemo(() => [
    {
      title: '批次名称', dataIndex: 'batch_name', key: 'batch_name', fixed: 'left' as const, width: 150,
      render: (name: string, record: ImportBatchSummary) => (
        <Link to={`/imports/${record.id}`}>{name}</Link>
      ),
    },
    { title: '文件数', dataIndex: 'file_count', key: 'file_count', width: 80 },
    { title: '记录数', dataIndex: 'normalized_record_count', key: 'normalized_record_count', width: 80, render: (v: number | null) => v ?? '-' },
    {
      title: '状态', dataIndex: 'status', key: 'status', width: 100,
      render: (status: string) => <Tag color={statusTagColor(status)}>{status}</Tag>,
    },
    {
      title: '操作人', dataIndex: 'created_by_name', key: 'created_by_name', width: 100,
      render: (v: string | null) => v || '-',
    },
    { title: '更新时间', dataIndex: 'updated_at', key: 'updated_at', width: 160, render: (v: string) => formatDateTime(v) },
    {
      title: '操作', key: 'actions', fixed: 'right' as const, width: 140,
      render: (_: unknown, record: ImportBatchSummary) => (
        <Space>
          <Link to={`/imports/${record.id}`}>
            <Button type="link" size="small">详情</Button>
          </Link>
          <Button
            type="link"
            size="small"
            danger
            onClick={() => void handleDeleteBatch(record.id, record.batch_name)}
            disabled={bulkDeleting || deletingBatchId !== null}
          >
            删除
          </Button>
        </Space>
      ),
    },
  ], [bulkDeleting, deletingBatchId, selectedBatchId]);

  return (
    <div>
      <Title level={4}>批次管理</Title>

      <Row gutter={16} style={{ marginBottom: 16 }}>
        {/* Upload section */}
        <Col xs={24} md={10}>
          <Card title="上传入口">
            <Input
              placeholder="批次名称，例如 2026-02 社保导入"
              value={batchName}
              onChange={(e) => setBatchName(e.target.value)}
              style={{ marginBottom: 12 }}
            />
            <Row gutter={12} style={{ marginBottom: 12 }}>
              <Col span={12}>
                <Select
                  placeholder="地区"
                  value={region || undefined}
                  onChange={(v) => setRegion(v ?? '')}
                  allowClear
                  style={{ width: '100%' }}
                  options={PRESET_REGIONS.map((item) => ({ label: item.label, value: item.value || undefined }))}
                />
              </Col>
              <Col span={12}>
                <Input
                  placeholder="公司（可选）"
                  value={companyName}
                  onChange={(e) => setCompanyName(e.target.value)}
                />
              </Col>
            </Row>
            <Dragger
              accept=".xlsx,.xls"
              multiple
              beforeUpload={(file) => {
                setFiles((prev) => [...prev, file]);
                return false;
              }}
              onRemove={(file) => {
                setFiles((prev) => prev.filter((f) => f !== file.originFileObj && f.name !== file.name));
              }}
              fileList={files.map((f) => ({ uid: `${f.name}-${f.size}`, name: f.name, status: 'done' as const }))}
              style={{ marginBottom: 12 }}
            >
              <p><InboxOutlined style={{ fontSize: 32, color: colors.BRAND }} /></p>
              <p>点击或拖拽上传 Excel 文件</p>
              <p style={{ color: colors.TEXT_TERTIARY }}>支持 .xlsx / .xls</p>
            </Dragger>
            <Space>
              <Button type="primary" onClick={() => void handleCreateBatch()} disabled={submitting || files.length === 0} loading={submitting}>
                创建导入批次
              </Button>
              <Button
                icon={<ReloadOutlined />}
                onClick={() => selectedBatchId ? void handleParseBatch(selectedBatchId) : undefined}
                disabled={!selectedBatchId || parsing}
                loading={parsing}
              >
                刷新当前批次
              </Button>
              <Button
                icon={<DeleteOutlined />}
                onClick={() => void handleBulkDelete()}
                disabled={selectedBatchIds.length === 0 || bulkDeleting}
                loading={bulkDeleting}
              >
                批量删除 ({selectedBatchIds.length})
              </Button>
            </Space>
          </Card>
        </Col>

        {/* Batch list */}
        <Col xs={24} md={14}>
          <Card title="批次列表">
            {pageLoading ? (
              <Skeleton active paragraph={{ rows: 6 }} />
            ) : batches.length === 0 ? (
              <Empty description="还没有导入批次，上传第一批 Excel 后会显示在这里。" />
            ) : (
              <Table<ImportBatchSummary>
                columns={batchColumns}
                dataSource={batches}
                rowKey="id"
                size="small"
                scroll={{ x: 700 }}
                pagination={{ pageSize: 10, showSizeChanger: false }}
                rowSelection={{
                  selectedRowKeys: selectedBatchIds,
                  onChange: (keys) => setSelectedBatchIds(keys as string[]),
                }}
                onRow={(record) => ({
                  onClick: () => setSelectedBatchId(record.id),
                  style: { cursor: 'pointer', background: record.id === selectedBatchId ? colors.HIGHLIGHT_BG_PRIMARY : undefined },
                })}
              />
            )}
          </Card>
        </Col>
      </Row>

      {/* Preview section */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={12}>
          <Card>
            <Typography.Text type="secondary">当前批次</Typography.Text>
            <Title level={5}>{selectedBatch?.batch_name ?? '尚未选择批次'}</Title>
            <Typography.Text>
              {selectedBatch
                ? `${selectedBatch.file_count} 个文件，当前状态为 ${selectedBatch.status}。`
                : '从批次列表中选择一个批次。'}
            </Typography.Text>
            {selectedBatch && (
              <div style={{ marginTop: 8 }}>
                <Link to={`/imports/${selectedBatch.id}`}>打开批次详情页</Link>
              </div>
            )}
          </Card>
        </Col>
        <Col span={12}>
          <Card>
            <Typography.Text type="secondary">首个命中文件</Typography.Text>
            <Title level={5}>{selectedSourceFile ? selectedSourceFile.raw_sheet_name : '尚未解析'}</Title>
            <Typography.Text>
              {selectedSourceFile
                ? `${selectedSourceFile.normalized_record_count} 条标准化记录，过滤 ${selectedSourceFile.filtered_row_count} 条非明细行。`
                : '解析完成后显示首个文件概览。'}
            </Typography.Text>
          </Card>
        </Col>
      </Row>

      {/* Quick preview */}
      <Card title="快速预览 - 当前批次首个文件" extra={
        <Space>
          {refreshingPreview && <Tag color="processing">预览刷新中</Tag>}
          {selectedBatch && <Link to={`/imports/${selectedBatch.id}`}><Button size="small">进入完整详情</Button></Link>}
        </Space>
      }>
        {!selectedSourceFile ? (
          <Empty description="当前批次还没有预览结果" />
        ) : (
          <>
            <Row gutter={16} style={{ marginBottom: 16 }}>
              <Col span={8}>
                <Card size="small">
                  <Typography.Text strong>{selectedSourceFile.file_name}</Typography.Text>
                  <div>sheet: {selectedSourceFile.raw_sheet_name}</div>
                  <div>region: {selectedSourceFile.region ?? '未指定'}</div>
                </Card>
              </Col>
              <Col span={8}>
                <Card size="small">
                  <Typography.Text strong>表头签名</Typography.Text>
                  <div style={{ wordBreak: 'break-all' }}>{selectedSourceFile.raw_header_signature}</div>
                </Card>
              </Col>
              <Col span={8}>
                <Card size="small">
                  <Typography.Text strong>未识别字段</Typography.Text>
                  <div>{selectedSourceFile.unmapped_headers.length > 0 ? selectedSourceFile.unmapped_headers.join(' / ') : '无'}</div>
                </Card>
              </Col>
            </Row>

            {/* Header mappings */}
            <Row gutter={16} style={{ marginBottom: 16 }}>
              <Col span={12}>
                <Card size="small" title="表头映射">
                  {selectedSourceFile.header_mappings.length > 0 ? (
                    selectedSourceFile.header_mappings.slice(0, 8).map((mapping) => (
                      <div key={mapping.raw_header_signature} style={{ marginBottom: 8 }}>
                        <Typography.Text strong>{mapping.raw_header}</Typography.Text>
                        {' '}
                        <Tag color={mapping.canonical_field ? 'success' : 'warning'}>{summarizeMapping(mapping)}</Tag>
                        <div>
                          <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                            来源 {mapping.mapping_source}
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
                <Card size="small" title="非明细行">
                  {selectedSourceFile.filtered_rows.length > 0 ? (
                    selectedSourceFile.filtered_rows.slice(0, 8).map((row) => (
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
            {selectedSourceFile.preview_records.length > 0 && (
              <Card size="small" title="前 20 行标准化预览">
                <Table
                  size="small"
                  scroll={{ x: true }}
                  pagination={false}
                  dataSource={selectedSourceFile.preview_records}
                  rowKey="source_row_number"
                  columns={[
                    { title: '源行号', dataIndex: 'source_row_number', key: 'source_row_number', width: 80 },
                    ...previewColumns.map((col) => ({
                      title: col,
                      key: col,
                      render: (_: unknown, record: (typeof selectedSourceFile.preview_records)[0]) => formatValue(record.values[col]),
                    })),
                  ]}
                />
              </Card>
            )}
          </>
        )}
      </Card>
    </div>
  );
}
