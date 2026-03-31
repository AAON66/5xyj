import { useEffect, useMemo, useRef, useState, type ChangeEvent } from 'react';
import { Link } from 'react-router-dom';
import {
  App,
  Button,
  Card,
  Col,
  Empty,
  Modal,
  Progress,
  Result,
  Row,
  Select,
  Space,
  Spin,
  Steps,
  Table,
  Tag,
  Typography,
  Upload,
} from 'antd';
import type { ColumnsType } from 'antd/es/table';
import {
  CloudUploadOutlined,
  DeleteOutlined,
  DownloadOutlined,
  ExportOutlined,
  InboxOutlined,
  StopOutlined,
  UndoOutlined,
} from '@ant-design/icons';

import { useAggregateSession } from '../hooks';
import { WorkflowSteps } from '../components/WorkflowSteps';
import { downloadAggregateArtifact, type AggregateArtifact, type AggregateProgressEvent } from '../services/aggregate';
import { cancelAggregateSession, clearAggregateSession, startAggregateSession } from '../services/aggregateSessionStore';
import { fetchEmployeeMasters } from '../services/employees';
import { fetchSystemHealth, type SystemHealth } from '../services/system';

const { Title, Text } = Typography;
const { Dragger } = Upload;

const TEXT = {
  title: '快速融合',
  description: '默认走完整主链路：自动识别社保与公积金表头、过滤非明细行、执行校验和工号匹配，最后同时输出薪酬模板和工具表最终版。',
  start: '开始聚合并导出',
  running: '正在聚合...',
  cancel: '取消当前聚合',
  clear: '清除当前记录',
  advanced: '进入高级页面',
  failedTitle: '本次聚合失败',
  successTitle: '两份文件已生成',
  masterTitle: '已同步导入员工主档',
  blockedTitle: '链路已继续但需要关注',
  socialTitle: '社保文件',
  housingTitle: '公积金文件',
  employeeTitle: '可选主数据',
  employeeHint: '可以与本次聚合一起上传，用于工号匹配。',
  employeeModeNone: '本次不使用',
  employeeModeExisting: '使用服务器已有主档',
  employeeModeUpload: '上传新主档',
  employeeExistingLoading: '正在读取服务器已有主档...',
  employeeExistingEmpty: '当前服务器还没有可用的员工主档。',
  employeeExistingReady: '本次将直接使用服务器现有的在职员工主档进行工号匹配。',
  employeeNoneMessage: '本次将不使用员工主档，仍可以继续聚合并导出结果。',
  batchPlaceholder: '例如：2026-02 社保公积金聚合',
  batchTip: '聚合开始后可以切换到其他页面，这里会保留本次记录，直到你主动取消或清除。',
  selectionRequired: '请至少选择一个社保或公积金 Excel 文件。',
  employeeExistingRequired: '当前还没有可用的服务器员工主档，请先上传新主档或切换为不使用。',
  employeeUploadRequired: '你已选择"上传新主档"，请先选择一个员工主档文件。',
  waitingTitle: '等你开始聚合',
  waitingMessage: '上传社保、公积金文件后，这里会直接显示进度、双模板结果和下载入口。',
  unknownRegion: '未识别地区',
  unknownCompany: '未识别公司',
  socialKind: '社保',
  housingKind: '公积金',
};

const PROGRESS_STEPS = [
  { key: 'employee_import', label: '员工主档' },
  { key: 'batch_upload', label: '上传批次' },
  { key: 'parse', label: '解析识别' },
  { key: 'validate', label: '数据校验' },
  { key: 'match', label: '工号匹配' },
  { key: 'export', label: '双模板导出' },
] as const;

function artifactLabel(value: string): string {
  return value === 'salary' ? '薪酬模板' : '工具表最终版';
}

function artifactTone(artifact: AggregateArtifact): 'success' | 'warning' | 'error' {
  if (artifact.status === 'completed') return 'success';
  if (artifact.status === 'failed') return 'error';
  return 'warning';
}

function statusLabel(value: string | null): string {
  switch (value) {
    case 'completed':
    case 'exported':
      return '已完成';
    case 'failed':
      return '已失败';
    case 'matched':
      return '已匹配';
    case 'validated':
      return '已校验';
    case 'normalized':
      return '已标准化';
    default:
      return value ?? '-';
  }
}

function formatArtifactMessage(artifact: AggregateArtifact): string {
  const path = artifact.file_path ?? artifact.error_message ?? '暂无输出路径';
  if (artifact.row_count > 0 && artifact.file_path) {
    return `${path} | ${artifact.row_count} 行`;
  }
  return path;
}

function getStepIndex(progress: AggregateProgressEvent | null): number {
  if (!progress) return -1;
  return PROGRESS_STEPS.findIndex((item) => item.key === progress.stage);
}

function sourceKindLabel(value: string): string {
  return value === 'housing_fund' ? TEXT.housingKind : TEXT.socialKind;
}

function fileKey(file: File): string {
  return `${file.name}_${file.size}_${file.lastModified}`;
}

function mergeFiles(existing: File[], incoming: File[]): File[] {
  if (!incoming.length) return existing;
  const merged = [...existing];
  const known = new Set(existing.map((f) => fileKey(f)));
  incoming.forEach((f) => {
    const key = fileKey(f);
    if (!known.has(key)) {
      known.add(key);
      merged.push(f);
    }
  });
  return merged;
}

function formatFileSize(size: number): string {
  if (size >= 1024 * 1024) return `${(size / (1024 * 1024)).toFixed(2)} MB`;
  if (size >= 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${size} B`;
}

function triggerBlobDownload(blob: Blob, fileName: string): void {
  const url = window.URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = fileName;
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  window.URL.revokeObjectURL(url);
}

export function SimpleAggregatePage() {
  const aggregateSession = useAggregateSession();
  const { message: messageApi } = App.useApp();
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [existingEmployeeMasterCount, setExistingEmployeeMasterCount] = useState(0);
  const [loadingEmployeeMasters, setLoadingEmployeeMasters] = useState(true);
  const [socialFiles, setSocialFiles] = useState<File[]>([]);
  const [housingFundFiles, setHousingFundFiles] = useState<File[]>([]);
  const [employeeMasterFile, setEmployeeMasterFile] = useState<File | null>(null);
  const [employeeMasterMode, setEmployeeMasterMode] = useState<'none' | 'upload' | 'existing'>('none');
  const [batchName, setBatchName] = useState('');
  const [selectionError, setSelectionError] = useState<string | null>(null);
  const [downloadingTemplate, setDownloadingTemplate] = useState<string | null>(null);

  const employeeInputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    let active = true;
    fetchSystemHealth()
      .then((payload) => { if (active) setHealth(payload); })
      .catch(() => { if (active) setHealth(null); });
    return () => { active = false; };
  }, []);

  useEffect(() => {
    let active = true;
    setLoadingEmployeeMasters(true);
    fetchEmployeeMasters({ activeOnly: true })
      .then((payload) => { if (active) setExistingEmployeeMasterCount(payload.total); })
      .catch(() => { if (active) setExistingEmployeeMasterCount(0); })
      .finally(() => { if (active) setLoadingEmployeeMasters(false); });
    return () => { active = false; };
  }, []);

  const running = aggregateSession.status === 'running';
  const hasSessionRecord = aggregateSession.status !== 'idle';
  const progress = aggregateSession.progress;
  const result = aggregateSession.result;
  const pageError = selectionError ?? aggregateSession.error;
  const lockSelection = hasSessionRecord;
  const effectiveEmployeeMasterMode = hasSessionRecord ? aggregateSession.selection.employeeMasterMode : employeeMasterMode;

  const outputArtifacts = useMemo(() => result?.artifacts ?? [], [result]);
  const normalizedCount = useMemo(() => result?.source_files.reduce((sum, item) => sum + item.normalized_record_count, 0) ?? 0, [result]);
  const filteredCount = useMemo(() => result?.source_files.reduce((sum, item) => sum + item.filtered_row_count, 0) ?? 0, [result]);
  const parseSummary = progress?.parse_summary;
  const parseFiles = progress?.parse_files ?? [];

  function handleEmployeeMasterSelected(event: ChangeEvent<HTMLInputElement>) {
    const selectedFile = event.target.files?.[0] ?? null;
    event.target.value = '';
    setSelectionError(null);
    setEmployeeMasterFile(selectedFile);
    if (selectedFile) setEmployeeMasterMode('upload');
  }

  async function handleRun() {
    if (!socialFiles.length && !housingFundFiles.length) {
      setSelectionError(TEXT.selectionRequired);
      return;
    }
    if (employeeMasterMode === 'existing' && existingEmployeeMasterCount <= 0) {
      setSelectionError(TEXT.employeeExistingRequired);
      return;
    }
    if (employeeMasterMode === 'upload' && !employeeMasterFile) {
      setSelectionError(TEXT.employeeUploadRequired);
      return;
    }

    setSelectionError(null);
    try {
      await startAggregateSession({
        files: socialFiles,
        housingFundFiles,
        employeeMasterFile: employeeMasterMode === 'upload' ? employeeMasterFile : null,
        employeeMasterMode,
        batchName,
      });
    } catch {
      return;
    }
  }

  function handleCancelConfirm() {
    Modal.confirm({
      title: '确认取消',
      content: '确定要取消当前聚合任务吗？已完成的部分不会保留。',
      okText: '确认取消',
      okType: 'danger',
      cancelText: '继续运行',
      onOk: () => cancelAggregateSession(),
    });
  }

  function handleClearRecord() {
    clearAggregateSession();
    setSelectionError(null);
  }

  async function handleDownloadArtifact(templateType: string) {
    if (!result?.batch_id) return;

    setDownloadingTemplate(templateType);
    setSelectionError(null);
    try {
      const { blob, fileName } = await downloadAggregateArtifact(result.batch_id, templateType);
      triggerBlobDownload(blob, fileName);
      messageApi.success('导出完成，文件已开始下载');
    } catch (error) {
      messageApi.error(error instanceof Error ? error.message : '下载失败，请稍后重试。');
    } finally {
      setDownloadingTemplate(null);
    }
  }

  const canStart = !running && !hasSessionRecord && (socialFiles.length > 0 || housingFundFiles.length > 0);

  // Steps current index for the Steps component
  const currentStepIndex = getStepIndex(progress);
  const stepsItems = PROGRESS_STEPS.map((step, idx) => {
    let status: 'wait' | 'process' | 'finish' | 'error' = 'wait';
    if (currentStepIndex >= 0) {
      if (idx < currentStepIndex || (idx === currentStepIndex && (progress?.percent ?? 0) >= 100)) {
        status = 'finish';
      } else if (idx === currentStepIndex) {
        status = 'process';
      }
    }
    if (aggregateSession.status === 'failed' && idx === currentStepIndex) {
      status = 'error';
    }
    return { title: step.label, status: status as 'wait' | 'process' | 'finish' | 'error' };
  });

  const sourceFileColumns: ColumnsType<NonNullable<typeof result>['source_files'][number]> = [
    { title: '文件名', dataIndex: 'file_name', key: 'file_name' },
    {
      title: '类型',
      dataIndex: 'source_kind',
      key: 'source_kind',
      render: (val: string) => <Tag>{sourceKindLabel(val)}</Tag>,
    },
    {
      title: '地区',
      dataIndex: 'region',
      key: 'region',
      render: (val: string | null) => val ?? TEXT.unknownRegion,
    },
    {
      title: '公司',
      dataIndex: 'company_name',
      key: 'company_name',
      render: (val: string | null) => val ?? TEXT.unknownCompany,
    },
    { title: '明细行', dataIndex: 'normalized_record_count', key: 'normalized_record_count', align: 'right' },
    { title: '过滤行', dataIndex: 'filtered_row_count', key: 'filtered_row_count', align: 'right' },
  ];

  // Build the social file list from files or session
  const socialDisplayList = hasSessionRecord && !socialFiles.length
    ? aggregateSession.selection.socialFiles.map((name, i) => ({ uid: `social-${i}`, name, size: 0, status: 'done' as const }))
    : socialFiles.map((f) => ({ uid: fileKey(f), name: f.name, size: f.size, status: 'done' as const }));

  const housingDisplayList = hasSessionRecord && !housingFundFiles.length
    ? aggregateSession.selection.housingFundFiles.map((name, i) => ({ uid: `housing-${i}`, name, size: 0, status: 'done' as const }))
    : housingFundFiles.map((f) => ({ uid: fileKey(f), name: f.name, size: f.size, status: 'done' as const }));

  const employeeDisplayName =
    effectiveEmployeeMasterMode === 'upload' ? (employeeMasterFile?.name ?? aggregateSession.selection.employeeMasterFile) : null;

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <Title level={4} style={{ margin: 0 }}>{TEXT.title}</Title>
          <Text type="secondary">{TEXT.description}</Text>
        </div>
        <Space>
          <Button type="primary" disabled={!canStart} loading={running} onClick={() => void handleRun()} icon={<CloudUploadOutlined />}>
            {running ? TEXT.running : TEXT.start}
          </Button>
          {running && (
            <Button danger onClick={handleCancelConfirm} icon={<StopOutlined />}>{TEXT.cancel}</Button>
          )}
          {!running && hasSessionRecord && (
            <Button onClick={handleClearRecord} icon={<UndoOutlined />}>{TEXT.clear}</Button>
          )}
          <Link to="/imports"><Button icon={<ExportOutlined />}>{TEXT.advanced}</Button></Link>
        </Space>
      </div>

      <WorkflowSteps />

      {health && (
        <Card size="small" style={{ marginBottom: 16, borderColor: '#00B42A' }}>
          <Text type="success">后端已就绪 - 社保表格聚合工具 {health.version}</Text>
        </Card>
      )}

      {pageError && (
        <Card size="small" style={{ marginBottom: 16, borderColor: '#F54A45' }}>
          <Text type="danger">{pageError}</Text>
        </Card>
      )}

      {result && result.export_status === 'completed' && (
        <Result status="success" title={TEXT.successTitle} subTitle={`批次 ${result.batch_name} 已完成双模板导出。`} style={{ padding: '16px 0', marginBottom: 16 }} />
      )}

      {result && result.employee_master && (
        <Card size="small" style={{ marginBottom: 16 }}>
          <Text>{TEXT.masterTitle}: {result.employee_master.file_name} | 新增 {result.employee_master.created_count} | 更新 {result.employee_master.updated_count}</Text>
        </Card>
      )}

      {result && result.blocked_reason && (
        <Card size="small" style={{ marginBottom: 16, borderColor: '#FF7D00' }}>
          <Text type="warning">{TEXT.blockedTitle}: {result.blocked_reason}</Text>
        </Card>
      )}

      {/* Steps indicator */}
      {hasSessionRecord && (
        <Card size="small" style={{ marginBottom: 16 }}>
          <Steps size="small" current={currentStepIndex >= 0 ? currentStepIndex : 0} items={stepsItems} />
        </Card>
      )}

      <Row gutter={16}>
        {/* Left column: File selection */}
        <Col span={12}>
          <Card title="步骤 1: 选择文件" style={{ marginBottom: 16 }}>
            <input ref={employeeInputRef} type="file" accept=".csv,.xlsx,.xlsm" hidden onChange={handleEmployeeMasterSelected} />

            {/* Social files dragger */}
            <Title level={5} style={{ marginBottom: 8 }}>社保文件</Title>
            <Dragger
              multiple
              accept=".xlsx,.xls"
              fileList={socialDisplayList}
              beforeUpload={(file) => {
                setSocialFiles((current) => mergeFiles(current, [file]));
                setSelectionError(null);
                return false;
              }}
              onRemove={(file) => {
                setSocialFiles((current) => current.filter((f) => fileKey(f) !== file.uid));
              }}
              disabled={lockSelection}
              style={{ marginBottom: 16 }}
            >
              <p><InboxOutlined style={{ fontSize: 48, color: '#3370FF' }} /></p>
              <p>点击或拖拽社保 Excel 文件到此区域</p>
              <p style={{ color: '#8F959E', fontSize: 12 }}>支持 .xlsx, .xls 格式，可多选</p>
            </Dragger>

            {/* Housing fund files dragger */}
            <Title level={5} style={{ marginTop: 16, marginBottom: 8 }}>公积金文件</Title>
            <Dragger
              multiple
              accept=".xlsx,.xls"
              fileList={housingDisplayList}
              beforeUpload={(file) => {
                setHousingFundFiles((current) => mergeFiles(current, [file]));
                setSelectionError(null);
                return false;
              }}
              onRemove={(file) => {
                setHousingFundFiles((current) => current.filter((f) => fileKey(f) !== file.uid));
              }}
              disabled={lockSelection}
              style={{ marginBottom: 16 }}
            >
              <p><InboxOutlined style={{ fontSize: 48, color: '#3370FF' }} /></p>
              <p>点击或拖拽公积金 Excel 文件到此区域</p>
              <p style={{ color: '#8F959E', fontSize: 12 }}>支持 .xlsx, .xls 格式，可多选</p>
            </Dragger>

            {/* Employee master section */}
            <Card size="small" title="员工主档（可选）" style={{ marginTop: 16 }}>
              <div style={{ marginBottom: 12 }}>
                <Text type="secondary">{TEXT.employeeHint}</Text>
              </div>
              <div style={{ marginBottom: 12 }}>
                <Text strong style={{ marginRight: 8 }}>主档来源:</Text>
                <Select
                  value={effectiveEmployeeMasterMode}
                  onChange={(val) => {
                    setEmployeeMasterMode(val);
                    if (val !== 'upload') setEmployeeMasterFile(null);
                    setSelectionError(null);
                  }}
                  disabled={lockSelection}
                  style={{ width: 200 }}
                  options={[
                    { value: 'none', label: TEXT.employeeModeNone },
                    { value: 'existing', label: TEXT.employeeModeExisting, disabled: loadingEmployeeMasters || existingEmployeeMasterCount <= 0 },
                    { value: 'upload', label: TEXT.employeeModeUpload },
                  ]}
                />
              </div>
              {effectiveEmployeeMasterMode === 'upload' && (
                <Space direction="vertical" style={{ width: '100%' }}>
                  <Space>
                    <Button onClick={() => employeeInputRef.current?.click()} disabled={lockSelection}>
                      {employeeMasterFile ? '重新选择' : '添加主档'}
                    </Button>
                    {employeeDisplayName && (
                      <Button danger icon={<DeleteOutlined />} onClick={() => setEmployeeMasterFile(null)} disabled={lockSelection}>
                        删除文件
                      </Button>
                    )}
                  </Space>
                  {employeeDisplayName ? (
                    <Card size="small">
                      <Text strong>{employeeDisplayName}</Text>
                      <br />
                      <Text type="secondary">{employeeMasterFile ? formatFileSize(employeeMasterFile.size) : '记录已保留'}</Text>
                    </Card>
                  ) : (
                    <Text type="secondary">未附带员工主档，也可以先直接导出结果。</Text>
                  )}
                </Space>
              )}
              {effectiveEmployeeMasterMode === 'existing' && (
                <Card size="small">
                  <Text strong>
                    {loadingEmployeeMasters
                      ? TEXT.employeeExistingLoading
                      : existingEmployeeMasterCount > 0
                        ? `${existingEmployeeMasterCount} 条在职员工主档`
                        : TEXT.employeeExistingEmpty}
                  </Text>
                  <br />
                  <Text type="secondary">{existingEmployeeMasterCount > 0 ? TEXT.employeeExistingReady : ''}</Text>
                </Card>
              )}
              {effectiveEmployeeMasterMode === 'none' && (
                <Text type="secondary">{TEXT.employeeNoneMessage}</Text>
              )}
            </Card>

            {/* Batch name */}
            <Card size="small" title="批次设置" style={{ marginTop: 16 }}>
              <div style={{ marginBottom: 8 }}>
                <Text>批次名称（可选）</Text>
              </div>
              <input
                value={hasSessionRecord && !batchName ? aggregateSession.selection.batchName : batchName}
                onChange={(event) => setBatchName(event.target.value)}
                placeholder={TEXT.batchPlaceholder}
                disabled={lockSelection}
                style={{
                  width: '100%',
                  padding: '4px 11px',
                  border: '1px solid #DEE0E3',
                  borderRadius: 4,
                  fontSize: 14,
                  lineHeight: '22px',
                }}
              />
              <Text type="secondary" style={{ display: 'block', marginTop: 8, fontSize: 12 }}>
                {TEXT.batchTip}
              </Text>
            </Card>
          </Card>
        </Col>

        {/* Right column: Results */}
        <Col span={12}>
          <Card title="步骤 2: 查看结果">
            {running && progress ? (
              <Spin spinning>
                <div style={{ textAlign: 'center', padding: '24px 0' }}>
                  <Progress
                    type="circle"
                    percent={progress.percent}
                    status={aggregateSession.status === 'failed' ? 'exception' : 'active'}
                  />
                  <div style={{ marginTop: 16 }}>
                    <Title level={5}>{progress.label}</Title>
                    <Text type="secondary">{progress.message}</Text>
                  </div>
                  {progress.batch_name && (
                    <div style={{ marginTop: 12 }}>
                      <Text strong>{progress.batch_name}</Text>
                      <br />
                      <Text type="secondary">{progress.batch_id ?? '批次编号生成中'}</Text>
                    </div>
                  )}
                </div>

                {/* Parse details during parse stage */}
                {progress.stage === 'parse' && parseSummary && (
                  <Card size="small" title="解析总览" style={{ marginTop: 16 }}>
                    <Row gutter={[8, 8]}>
                      <Col span={8}><Text type="secondary">总文件数:</Text> <Text strong>{parseSummary.total_files}</Text></Col>
                      <Col span={8}><Text type="secondary">并行路数:</Text> <Text strong>{parseSummary.worker_count}</Text></Col>
                      <Col span={8}><Text type="secondary">排队中:</Text> <Text strong>{parseSummary.queued_count}</Text></Col>
                      <Col span={8}><Text type="secondary">解析中:</Text> <Text strong>{parseSummary.active_count}</Text></Col>
                      <Col span={8}><Text type="secondary">待保存:</Text> <Text strong>{Math.max(0, parseSummary.analyzed_count - parseSummary.saved_count)}</Text></Col>
                      <Col span={8}><Text type="secondary">已保存:</Text> <Text strong>{parseSummary.saved_count}</Text></Col>
                    </Row>
                    {parseFiles.length > 0 && (
                      <div style={{ marginTop: 12, maxHeight: 200, overflowY: 'auto' }}>
                        {parseFiles.map((item) => (
                          <div key={item.source_file_id ?? `${item.file_index}_${item.file_name}`} style={{ padding: '4px 0', borderBottom: '1px solid #E8E8E8' }}>
                            <Text strong>{`${item.file_index}. ${item.file_name}`}</Text>
                            <Tag style={{ marginLeft: 8 }} color={item.phase === 'parse_saved' ? 'success' : item.phase === 'parse_started' ? 'processing' : 'default'}>
                              {item.phase === 'parse_saved' ? '已保存' : item.phase === 'parse_started' ? '解析中' : item.phase === 'parse_analyzed' ? '待保存' : '排队中'}
                            </Tag>
                            <br />
                            <Text type="secondary" style={{ fontSize: 12 }}>
                              {sourceKindLabel(item.source_kind ?? 'social_security')} / {item.region ?? TEXT.unknownRegion} / {item.company_name ?? TEXT.unknownCompany}
                              {typeof item.normalized_record_count === 'number' ? ` / 明细 ${item.normalized_record_count}` : ''}
                              {typeof item.filtered_row_count === 'number' ? ` / 过滤 ${item.filtered_row_count}` : ''}
                            </Text>
                          </div>
                        ))}
                      </div>
                    )}
                  </Card>
                )}
              </Spin>
            ) : result ? (
              <div>
                {/* Summary statistics */}
                <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
                  <Col span={6}>
                    <Card size="small">
                      <Text type="secondary">导出状态</Text>
                      <div><Tag color={result.export_status === 'completed' ? 'success' : 'warning'}>{statusLabel(result.export_status)}</Tag></div>
                    </Card>
                  </Col>
                  <Col span={6}>
                    <Card size="small">
                      <Text type="secondary">聚合记录</Text>
                      <div><Text strong style={{ fontSize: 18 }}>{normalizedCount}</Text></div>
                    </Card>
                  </Col>
                  <Col span={6}>
                    <Card size="small">
                      <Text type="secondary">已过滤行</Text>
                      <div><Text strong style={{ fontSize: 18 }}>{filteredCount}</Text></div>
                    </Card>
                  </Col>
                  <Col span={6}>
                    <Card size="small">
                      <Text type="secondary">匹配成功</Text>
                      <div><Text strong style={{ fontSize: 18 }}>{result.matched_count}</Text></div>
                    </Card>
                  </Col>
                </Row>

                {/* Artifacts download */}
                <Card size="small" title="输出文件" style={{ marginBottom: 16 }}>
                  <Space direction="vertical" style={{ width: '100%' }}>
                    {outputArtifacts.map((artifact) => (
                      <Card
                        key={artifact.template_type}
                        size="small"
                        style={{
                          borderColor: artifact.status === 'completed' ? '#00B42A' : artifact.status === 'failed' ? '#F54A45' : '#FF7D00',
                        }}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <div>
                            <Text strong>{artifactLabel(artifact.template_type)}</Text>
                            <br />
                            <Text type="secondary" style={{ fontSize: 12 }}>{formatArtifactMessage(artifact)}</Text>
                          </div>
                          {artifact.status === 'completed' && result.batch_id ? (
                            <Button
                              icon={<DownloadOutlined />}
                              onClick={() => void handleDownloadArtifact(artifact.template_type)}
                              loading={downloadingTemplate === artifact.template_type}
                            >
                              下载文件
                            </Button>
                          ) : (
                            <Tag color={artifactTone(artifact)}>{artifact.status}</Tag>
                          )}
                        </div>
                      </Card>
                    ))}
                  </Space>
                </Card>

                {/* Source file details */}
                <Card size="small" title="源文件详情">
                  <Table
                    dataSource={result.source_files}
                    columns={sourceFileColumns}
                    rowKey="source_file_id"
                    size="small"
                    pagination={false}
                  />
                </Card>
              </div>
            ) : (
              <Empty
                description={
                  <div>
                    <Text strong>{TEXT.waitingTitle}</Text>
                    <br />
                    <Text type="secondary">{TEXT.waitingMessage}</Text>
                  </div>
                }
              />
            )}
          </Card>
        </Col>
      </Row>
    </div>
  );
}
