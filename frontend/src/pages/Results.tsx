import { useEffect, useMemo, useState } from 'react';
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
  Typography,
} from 'antd';
import type { ColumnsType } from 'antd/es/table';

import { MobileStickyActionBar } from '../components/MobileStickyActionBar';
import { WorkflowSteps } from '../components/WorkflowSteps';
import { useResponsiveViewport } from '../hooks/useResponsiveViewport';
import {
  fetchBatchMatch,
  fetchBatchValidation,
  fetchRuntimeBatches,
  matchBatch,
  type BatchMatch,
  type BatchValidation,
  type MatchRecord,
  type ValidationIssue,
  validateBatch,
} from '../services/runtime';

const { Title, Text } = Typography;

function severityLabel(value: string): string {
  switch (value) {
    case 'error': return '错误';
    case 'warning': return '警告';
    case 'info': return '提示';
    default: return value;
  }
}

function severityColor(value: string): string {
  switch (value) {
    case 'error': return 'error';
    case 'warning': return 'warning';
    case 'info': return 'processing';
    default: return 'default';
  }
}

function matchLabel(value: string): string {
  switch (value) {
    case 'matched': return '已匹配';
    case 'unmatched': return '未匹配';
    case 'duplicate': return '重复命中';
    case 'low_confidence': return '低置信度';
    default: return value;
  }
}

function matchColor(value: string): string {
  switch (value) {
    case 'matched': return 'success';
    case 'unmatched': return 'error';
    case 'duplicate': return 'warning';
    case 'low_confidence': return 'orange';
    default: return 'default';
  }
}

export function ResultsPage() {
  const colors = useSemanticColors();
  const { isMobile } = useResponsiveViewport();
  const [batches, setBatches] = useState<Array<{ id: string; batch_name: string; status: string; updated_at: string }>>([]);
  const [selectedBatchId, setSelectedBatchId] = useState<string | null>(null);
  const [validation, setValidation] = useState<BatchValidation | null>(null);
  const [matchResult, setMatchResult] = useState<BatchMatch | null>(null);
  const [loading, setLoading] = useState(true);
  const [runningValidation, setRunningValidation] = useState(false);
  const [runningMatch, setRunningMatch] = useState(false);
  const [notice, setNotice] = useState<{ type: 'success' | 'warning'; message: string } | null>(null);
  const [pageError, setPageError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    async function loadBatches() {
      try {
        const result = await fetchRuntimeBatches();
        if (!active) return;
        setBatches(result);
        setPageError(null);
        if (result[0]) {
          setSelectedBatchId(result[0].id);
        }
      } catch {
        if (active) setPageError('运行结果页面暂时无法读取批次列表，请稍后重试。');
      } finally {
        if (active) setLoading(false);
      }
    }
    void loadBatches();
    return () => { active = false; };
  }, []);

  useEffect(() => {
    let active = true;
    async function loadRuntimeState(batchId: string) {
      try {
        const [validationData, matchData] = await Promise.all([
          fetchBatchValidation(batchId).catch(() => null),
          fetchBatchMatch(batchId).catch(() => null),
        ]);
        if (!active) return;
        setValidation(validationData);
        setMatchResult(matchData);
      } catch {
        if (active) setPageError('当前批次的校验或匹配结果加载失败。');
      }
    }
    if (!selectedBatchId) {
      setValidation(null);
      setMatchResult(null);
      return;
    }
    void loadRuntimeState(selectedBatchId);
    return () => { active = false; };
  }, [selectedBatchId]);

  const validationIssues = useMemo<ValidationIssue[]>(
    () => validation?.source_files.flatMap((item) => item.issues) ?? [],
    [validation],
  );
  const matchRows = useMemo<MatchRecord[]>(
    () => matchResult?.source_files.flatMap((item) => item.results) ?? [],
    [matchResult],
  );

  async function refreshBatches(keepId?: string) {
    const result = await fetchRuntimeBatches();
    setBatches(result);
    if (keepId) setSelectedBatchId(keepId);
  }

  async function handleValidate() {
    if (!selectedBatchId) return;
    setRunningValidation(true);
    setNotice(null);
    try {
      const result = await validateBatch(selectedBatchId);
      setValidation(result);
      setNotice({ type: 'success', message: `${result.batch_name} 已完成校验。` });
      await refreshBatches(selectedBatchId);
    } finally {
      setRunningValidation(false);
    }
  }

  async function handleMatch() {
    if (!selectedBatchId) return;
    setRunningMatch(true);
    setNotice(null);
    try {
      const result = await matchBatch(selectedBatchId);
      setMatchResult(result);
      setNotice({
        type: result.blocked_reason ? 'warning' : 'success',
        message: result.blocked_reason ?? `${result.batch_name} 已完成工号匹配。`,
      });
      await refreshBatches(selectedBatchId);
    } finally {
      setRunningMatch(false);
    }
  }

  const primaryActionMode = validation ? 'match' : 'validate';
  const mobilePrimaryLabel = primaryActionMode === 'validate' ? '执行数据校验' : '执行工号匹配';
  const mobilePrimaryDisabled = !selectedBatchId || (primaryActionMode === 'validate' ? runningValidation : runningMatch);
  const mobilePrimaryLoading = primaryActionMode === 'validate' ? runningValidation : runningMatch;
  const mobilePrimaryHelper = !selectedBatchId
    ? '请先选择一个批次。'
    : primaryActionMode === 'match'
      ? '校验结果已就绪，下一步执行工号匹配。'
      : null;

  const issueColumns: ColumnsType<ValidationIssue> = [
    {
      title: '行号',
      dataIndex: 'source_row_number',
      key: 'row',
      fixed: 'left' as const,
      width: 80,
      render: (val: number) => `第 ${val} 行`,
    },
    {
      title: '严重程度',
      dataIndex: 'severity',
      key: 'severity',
      width: 100,
      render: (val: string) => <Tag color={severityColor(val)}>{severityLabel(val)}</Tag>,
    },
    {
      title: '类型',
      dataIndex: 'issue_type',
      key: 'issue_type',
      width: 120,
    },
    {
      title: '字段',
      dataIndex: 'field_name',
      key: 'field_name',
      width: 120,
      render: (val: string | null) => val || '-',
    },
    {
      title: '描述',
      dataIndex: 'message',
      key: 'message',
    },
  ];

  const matchColumns: ColumnsType<MatchRecord> = [
    {
      title: '姓名',
      dataIndex: 'person_name',
      key: 'person_name',
      fixed: 'left' as const,
      width: 100,
      render: (val: string | null) => val ?? '未识别姓名',
    },
    {
      title: '行号',
      dataIndex: 'source_row_number',
      key: 'row',
      width: 80,
      render: (val: number) => `第 ${val} 行`,
    },
    {
      title: '证件号',
      dataIndex: 'id_number',
      key: 'id_number',
      render: (val: string | null) => val ?? '-',
    },
    {
      title: '工号',
      dataIndex: 'employee_id',
      key: 'employee_id',
      render: (val: string | null) => val ?? '-',
    },
    {
      title: '状态',
      dataIndex: 'match_status',
      key: 'match_status',
      width: 100,
      render: (val: string) => <Tag color={matchColor(val)}>{matchLabel(val)}</Tag>,
    },
    {
      title: '依据',
      dataIndex: 'match_basis',
      key: 'match_basis',
      render: (val: string | null, record: MatchRecord) => (
        <span>
          {val ? `依据 ${val}` : '尚未命中匹配依据'}
          {record.confidence !== null ? ` (${record.confidence.toFixed(2)})` : ''}
        </span>
      ),
    },
  ];

  return (
    <div style={isMobile ? { paddingBottom: 96 } : undefined}>
      <Title level={4}>校验匹配</Title>
      <WorkflowSteps />

      {notice && (
        <Alert
          type={notice.type}
          message={notice.message}
          closable
          onClose={() => setNotice(null)}
          style={{ marginBottom: 16 }}
        />
      )}
      {pageError && (
        <Alert type="error" message="页面状态异常" description={pageError} style={{ marginBottom: 16 }} />
      )}

      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col xs={24} md={8}>
          <Card title="批次选择">
            {loading ? (
              <Skeleton active paragraph={{ rows: 2 }} />
            ) : (
              <>
                <Text type="secondary" style={{ display: 'block', marginBottom: 8 }}>
                  {batches.length} 个可用批次
                </Text>
                <Select
                  style={{ width: '100%' }}
                  placeholder="请选择批次"
                  value={selectedBatchId}
                  onChange={(val) => setSelectedBatchId(val)}
                  options={batches.map((b) => ({
                    value: b.id,
                    label: `${b.batch_name} (${b.status})`,
                  }))}
                />
                <div style={{ display: 'flex', gap: 8, marginTop: 12, flexWrap: 'wrap' }}>
                  {!isMobile || primaryActionMode !== 'validate' ? (
                    <Button
                      type={!isMobile ? 'primary' : 'default'}
                      onClick={() => void handleValidate()}
                      disabled={!selectedBatchId || runningValidation}
                      loading={runningValidation}
                    >
                      执行数据校验
                    </Button>
                  ) : null}
                  {!isMobile || primaryActionMode !== 'match' ? (
                    <Button
                      onClick={() => void handleMatch()}
                      disabled={!selectedBatchId || runningMatch}
                      loading={runningMatch}
                    >
                      执行工号匹配
                    </Button>
                  ) : null}
                </div>
              </>
            )}
          </Card>
        </Col>
        <Col xs={24} md={16}>
          <Card>
            <Row gutter={[16, 16]}>
              <Col span={6}>
                <Statistic title="校验问题" value={validation?.total_issue_count ?? 0} />
              </Col>
              <Col span={6}>
                <Statistic title="已匹配" value={matchResult?.matched_count ?? 0} valueStyle={{ color: colors.SUCCESS }} />
              </Col>
              <Col span={6}>
                <Statistic title="未匹配" value={matchResult?.unmatched_count ?? 0} valueStyle={{ color: colors.ERROR }} />
              </Col>
              <Col span={6}>
                <Statistic title="重复命中" value={matchResult?.duplicate_count ?? 0} valueStyle={{ color: colors.WARNING }} />
              </Col>
            </Row>
            <div style={{ marginTop: 12 }}>
              <Text strong>员工主档状态: </Text>
              <Text type="secondary">
                {matchResult
                  ? matchResult.employee_master_available
                    ? `当前可用员工主档 ${matchResult.employee_master_count} 条。`
                    : matchResult.blocked_reason ?? '员工主档暂不可用。'
                  : '选择批次后，这里会显示匹配前置条件。'}
              </Text>
            </div>
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        <Col xs={24} md={12}>
          <Card title="校验问题明细">
            {validationIssues.length > 0 ? (
              <Table
                size="small"
                columns={issueColumns}
                dataSource={validationIssues}
                rowKey={(r) => `${r.normalized_record_id ?? 'none'}-${r.source_row_number}-${r.issue_type}`}
                pagination={{ pageSize: 10, showSizeChanger: true }}
                scroll={{ x: true }}
              />
            ) : (
              <Empty description="暂无校验问题。执行校验后，如果发现缺失、格式或金额问题，这里会展示详细结果。" />
            )}
          </Card>
        </Col>
        <Col xs={24} md={12}>
          <Card title="工号命中明细">
            {matchRows.length > 0 ? (
              <Table
                size="small"
                columns={matchColumns}
                dataSource={matchRows}
                rowKey={(r) => `${r.normalized_record_id ?? 'none'}-${r.source_row_number}`}
                pagination={{ pageSize: 10, showSizeChanger: true }}
                scroll={{ x: true }}
              />
            ) : (
              <Empty description="暂无匹配结果。执行工号匹配后，这里会展示命中、未命中和低置信度候选。" />
            )}
          </Card>
        </Col>
      </Row>
      <MobileStickyActionBar
        visible={isMobile}
        primaryLabel={mobilePrimaryLabel}
        onPrimaryClick={() => {
          if (primaryActionMode === 'validate') {
            void handleValidate();
            return;
          }
          void handleMatch();
        }}
        primaryDisabled={mobilePrimaryDisabled}
        primaryLoading={mobilePrimaryLoading}
        helperText={mobilePrimaryHelper}
      />
    </div>
  );
}
