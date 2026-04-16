import { useCallback, useEffect, useMemo, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Button, Modal, Space, Spin, Table, Tag, Tooltip, Typography, message, theme } from 'antd';
import { useSemanticColors } from '../theme/useSemanticColors';
import { ClearOutlined, LinkOutlined, SaveOutlined } from '@ant-design/icons';
import {
  ReactFlow,
  Background,
  Controls,
  Handle,
  Position,
  addEdge,
  useNodesState,
  useEdgesState,
  type Node,
  type Edge,
  type OnConnect,
  type NodeTypes,
  BackgroundVariant,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import { normalizeApiError } from '../services/api';
import {
  fetchFeishuFields,
  fetchSyncConfigs,
  saveSyncConfigMapping,
  suggestMapping,
  type FeishuFieldInfo,
  type SyncConfig,
} from '../services/feishu';

const { Title, Text } = Typography;

// ── System fields list ───────────────────────────────────────────

const SYSTEM_FIELDS = [
  { key: 'person_name', label: '姓名' },
  { key: 'id_number', label: '证件号码' },
  { key: 'employee_id', label: '工号' },
  { key: 'company_name', label: '公司名称' },
  { key: 'region', label: '地区' },
  { key: 'billing_period', label: '费款所属期' },
  { key: 'payment_base', label: '缴费基数' },
  { key: 'total_amount', label: '合计金额' },
  { key: 'company_total_amount', label: '单位合计' },
  { key: 'personal_total_amount', label: '个人合计' },
  { key: 'pension_company', label: '养老保险(单位)' },
  { key: 'pension_personal', label: '养老保险(个人)' },
  { key: 'medical_company', label: '医疗保险(单位)' },
  { key: 'medical_personal', label: '医疗保险(个人)' },
  { key: 'medical_maternity_company', label: '生育医疗(单位)' },
  { key: 'unemployment_company', label: '失业保险(单位)' },
  { key: 'unemployment_personal', label: '失业保险(个人)' },
  { key: 'injury_company', label: '工伤保险' },
  { key: 'supplementary_medical_company', label: '补充医疗(单位)' },
  { key: 'supplementary_pension_company', label: '补充养老(单位)' },
  { key: 'large_medical_personal', label: '大额医疗(个人)' },
  { key: 'late_fee', label: '滞纳金' },
  { key: 'interest', label: '利息' },
];

// ── Required fields for save validation ──────────────────────────

const REQUIRED_FIELDS = [
  { key: 'person_name', label: '姓名', level: 'required' as const },
  { key: 'employee_id', label: '工号', level: 'required' as const },
  { key: 'id_number', label: '证件号码', level: 'recommended' as const },
];

// ── Feishu field type labels ─────────────────────────────────────

const FEISHU_TYPE_LABELS: Record<string, { label: string; color: string }> = {
  Text: { label: '文本', color: 'blue' },
  Email: { label: '邮箱', color: 'blue' },
  Barcode: { label: '条码', color: 'blue' },
  Phone: { label: '电话', color: 'blue' },
  Url: { label: '链接', color: 'blue' },
  Number: { label: '数字', color: 'green' },
  Progress: { label: '进度', color: 'green' },
  Currency: { label: '货币', color: 'green' },
  Rating: { label: '评分', color: 'green' },
  DateTime: { label: '日期', color: 'orange' },
  CreatedTime: { label: '创建时间', color: 'orange' },
  ModifiedTime: { label: '更新时间', color: 'orange' },
  SingleSelect: { label: '单选', color: 'purple' },
  MultiSelect: { label: '多选', color: 'purple' },
  Checkbox: { label: '复选框', color: 'default' },
  User: { label: '人员', color: 'default' },
  Attachment: { label: '附件', color: 'default' },
  Formula: { label: '公式', color: 'default' },
  Lookup: { label: '查找引用', color: 'default' },
  SingleLink: { label: '单向关联', color: 'default' },
  DuplexLink: { label: '双向关联', color: 'default' },
  Location: { label: '地理位置', color: 'default' },
  GroupChat: { label: '群组', color: 'default' },
  CreatedUser: { label: '创建人', color: 'default' },
  ModifiedUser: { label: '修改人', color: 'default' },
  AutoNumber: { label: '自动编号', color: 'default' },
};

function getTypeInfo(uiType: string | null | undefined): { label: string; color: string } {
  if (!uiType) return { label: '未知', color: 'default' };
  return FEISHU_TYPE_LABELS[uiType] ?? { label: uiType, color: 'default' };
}

// ── Custom node components ───────────────────────────────────────

function SystemFieldNode({ data }: { data: { label: string } }) {
  const colors = useSemanticColors();
  return (
    <div
      style={{
        width: 200,
        height: 40,
        background: colors.BG_CONTAINER,
        border: `1px solid ${colors.BORDER}`,
        borderRadius: 8,
        display: 'flex',
        alignItems: 'center',
        padding: '0 12px',
        fontSize: 14,
        color: colors.TEXT,
      }}
    >
      {data.label}
      <Handle
        type="source"
        position={Position.Right}
        style={{ background: colors.BRAND }}
      />
    </div>
  );
}

function FeishuColumnNode({ data }: { data: { label: string; uiType?: string | null; fieldType?: number } }) {
  const colors = useSemanticColors();
  const typeInfo = getTypeInfo(data.uiType);
  return (
    <div
      style={{
        width: 280,
        height: 40,
        background: colors.BG_CONTAINER,
        border: `1px solid ${colors.BORDER}`,
        borderRadius: 8,
        display: 'flex',
        alignItems: 'center',
        padding: '0 12px',
        fontSize: 14,
        color: colors.TEXT,
        gap: 8,
      }}
    >
      <Handle
        type="target"
        position={Position.Left}
        style={{ background: colors.BRAND }}
      />
      <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
        {data.label}
      </span>
      <Tooltip title={`${typeInfo.label} (type=${data.fieldType ?? '?'}, ui_type=${data.uiType ?? 'N/A'})`}>
        <Tag color={typeInfo.color} style={{ margin: 0, flexShrink: 0 }}>
          {typeInfo.label}
        </Tag>
      </Tooltip>
    </div>
  );
}

const nodeTypes: NodeTypes = {
  systemField: SystemFieldNode,
  feishuColumn: FeishuColumnNode,
};

// defaultEdgeOptions moved inside component (needs theme token)

// ── Main component ───────────────────────────────────────────────

export function FeishuFieldMappingPage() {
  const colors = useSemanticColors();
  const { token } = theme.useToken();
  const defaultEdgeOptions = useMemo(() => ({
    style: { stroke: colors.BRAND, strokeWidth: 2 },
    type: 'smoothstep' as const,
  }), [colors.BRAND]);
  const { configId } = useParams<{ configId: string }>();
  const [loading, setLoading] = useState(true);
  const [feishuFields, setFeishuFields] = useState<FeishuFieldInfo[]>([]);
  const [configName, setConfigName] = useState('');
  const [saving, setSaving] = useState(false);

  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);

  // Load config and Feishu fields
  useEffect(() => {
    if (!configId) return;
    const currentConfigId = configId;

    async function load() {
      setLoading(true);
      try {
        // Fetch existing config for name and field_mapping
        const configs = await fetchSyncConfigs();
        const config = configs.find((c: SyncConfig) => c.id === currentConfigId);
        if (config) {
          setConfigName(config.name);
        }

        // Fetch Feishu fields
        let fields: FeishuFieldInfo[] = [];
        try {
          fields = await fetchFeishuFields(currentConfigId);
        } catch (err) {
          const errMsg = normalizeApiError(err).message;
          message.warning(`无法获取飞书字段: ${errMsg}。请检查飞书凭证和同步配置中的 app_token / table_id 是否正确。`);
        }
        setFeishuFields(fields);

        // Build nodes
        const systemNodes: Node[] = SYSTEM_FIELDS.map((field, index) => ({
          id: `sys-${field.key}`,
          type: 'systemField',
          position: { x: 50, y: index * 52 },
          data: { label: field.label },
          draggable: false,
        }));

        const feishuNodes: Node[] = fields.map((field, index) => ({
          id: `fs-${field.field_id}`,
          type: 'feishuColumn',
          position: { x: 500, y: index * 52 },
          data: { label: field.field_name, uiType: field.ui_type, fieldType: field.field_type },
          draggable: false,
        }));

        setNodes([...systemNodes, ...feishuNodes]);

        // Build initial edges from existing mapping
        if (config?.field_mapping) {
          const initialEdges: Edge[] = [];
          for (const [sysKey, fsFieldName] of Object.entries(config.field_mapping)) {
            const fsField = fields.find((f) => f.field_name === fsFieldName);
            if (fsField) {
              initialEdges.push({
                id: `edge-${sysKey}-${fsField.field_id}`,
                source: `sys-${sysKey}`,
                target: `fs-${fsField.field_id}`,
                ...defaultEdgeOptions,
              });
            }
          }
          setEdges(initialEdges);
        }
      } catch (err) {
        message.error(normalizeApiError(err).message);
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, [configId, setNodes, setEdges, defaultEdgeOptions]);

  const onConnect: OnConnect = useCallback(
    (connection) => {
      setEdges((eds) =>
        addEdge(
          {
            ...connection,
            ...defaultEdgeOptions,
          },
          eds,
        ),
      );
    },
    [setEdges, defaultEdgeOptions],
  );

  // Auto-match: use backend suggest-mapping API
  const handleAutoMatch = useCallback(async () => {
    if (!configId || feishuFields.length === 0) return;
    try {
      const systemFieldKeys = SYSTEM_FIELDS.map((f) => f.key);
      const result = await suggestMapping(
        configId,
        feishuFields.map((f) => ({ field_name: f.field_name, field_id: f.field_id })),
        systemFieldKeys,
      );

      const newEdges: Edge[] = result.suggestions.map((s) => ({
        id: `edge-${s.canonical_field}-${s.feishu_field_id}`,
        source: `sys-${s.canonical_field}`,
        target: `fs-${s.feishu_field_id}`,
        type: 'smoothstep',
        style: {
          stroke: colors.BRAND,
          strokeWidth: 2,
          ...(s.confidence < 0.9 ? { strokeDasharray: '5 5' } : {}),
        },
        data: { confidence: s.confidence, isAutoSuggestion: true },
      }));

      setEdges(newEdges);
      message.success(`自动匹配完成，已匹配 ${newEdges.length} 个字段（${result.unmatched.length} 个未匹配）`);
    } catch (err) {
      message.error(normalizeApiError(err).message);
    }
  }, [configId, feishuFields, setEdges, colors.BRAND]);

  // ── Two-step save modal state ──────────────────────────────────
  const [warningModalOpen, setWarningModalOpen] = useState(false);
  const [previewModalOpen, setPreviewModalOpen] = useState(false);
  const [missingFields, setMissingFields] = useState<Array<{ key: string; label: string; level: string }>>([]);
  const [mappingPreview, setMappingPreview] = useState<Array<{ sysKey: string; sysLabel: string; fsName: string; fsType: string }>>([]);

  // Build current mapping snapshot
  const buildCurrentMapping = useCallback(() => {
    const mapping: Record<string, string> = {};
    for (const edge of edges) {
      const sysKey = edge.source.replace('sys-', '');
      const fsFieldId = edge.target.replace('fs-', '');
      const fsField = feishuFields.find((f) => f.field_id === fsFieldId);
      if (fsField) {
        mapping[sysKey] = fsField.field_name;
      }
    }
    return mapping;
  }, [edges, feishuFields]);

  // Click save -> check required fields -> show modal
  const handleSaveClick = useCallback(() => {
    const mapping = buildCurrentMapping();

    // Check required fields
    const missing = REQUIRED_FIELDS.filter((rf) => !mapping[rf.key]);
    setMissingFields(missing);

    // Build preview data
    const preview = SYSTEM_FIELDS.map((sf) => {
      const fsName = mapping[sf.key] ?? '';
      const fsField = feishuFields.find((f) => f.field_name === fsName);
      const typeInfo = fsField?.ui_type ? getTypeInfo(fsField.ui_type) : null;
      return {
        sysKey: sf.key,
        sysLabel: sf.label,
        fsName,
        fsType: typeInfo?.label ?? '-',
      };
    }).filter((row) => row.fsName);

    setMappingPreview(preview);

    if (missing.length > 0) {
      setWarningModalOpen(true);
    } else {
      setPreviewModalOpen(true);
    }
  }, [buildCurrentMapping, feishuFields]);

  // Confirm save
  const doSave = useCallback(async () => {
    if (!configId) return;
    setSaving(true);
    setPreviewModalOpen(false);
    setWarningModalOpen(false);
    try {
      const mapping = buildCurrentMapping();
      await saveSyncConfigMapping(configId, mapping);
      message.success('映射已保存');
    } catch (err) {
      message.error(normalizeApiError(err).message);
    } finally {
      setSaving(false);
    }
  }, [configId, buildCurrentMapping]);

  // Clear all edges
  const handleClear = useCallback(() => {
    Modal.confirm({
      title: '确认清除',
      content: '确认清除所有映射？此操作不可撤销。',
      okText: '确认',
      cancelText: '取消',
      okButtonProps: { danger: true },
      onOk: () => setEdges([]),
    });
  }, [setEdges]);

  if (loading) {
    return (
      <div
        style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          height: '60vh',
        }}
      >
        <Spin size="large" tip="加载中..." />
      </div>
    );
  }

  return (
    <div style={{ padding: '24px 24px 0' }}>
      <div style={{ marginBottom: 16 }}>
        <Title level={3} style={{ margin: 0 }}>
          <LinkOutlined style={{ marginRight: 8 }} />
          {configName ? `字段映射 - ${configName}` : '字段映射'}
        </Title>
        <Text type="secondary">
          拖拽连接系统字段与飞书列建立映射关系
        </Text>
      </div>

      <Space style={{ marginBottom: 16 }}>
        <Button onClick={() => void handleAutoMatch()}>
          自动匹配
        </Button>
        <Button
          type="primary"
          icon={<SaveOutlined />}
          loading={saving}
          onClick={handleSaveClick}
        >
          保存映射
        </Button>
        <Button
          danger
          icon={<ClearOutlined />}
          onClick={handleClear}
        >
          清除全部
        </Button>
      </Space>

      <div style={{ width: '100%', height: 'calc(100vh - 200px)' }}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          nodeTypes={nodeTypes}
          defaultEdgeOptions={defaultEdgeOptions}
          minZoom={0.5}
          maxZoom={1.5}
          fitView
        >
          <Background color={token.colorBorder} gap={20} variant={BackgroundVariant.Dots} />
          <Controls position="bottom-left" />
        </ReactFlow>
      </div>

      {/* Warning Modal: missing required fields */}
      <Modal
        title="关键字段未映射"
        open={warningModalOpen}
        onCancel={() => setWarningModalOpen(false)}
        footer={[
          <Button key="back" onClick={() => setWarningModalOpen(false)}>
            返回补全
          </Button>,
          <Button
            key="force"
            type="primary"
            danger
            onClick={() => {
              setWarningModalOpen(false);
              setPreviewModalOpen(true);
            }}
          >
            仍然保存
          </Button>,
        ]}
      >
        <div style={{ marginBottom: 8 }}>以下关键字段尚未建立映射：</div>
        <ul style={{ paddingLeft: 20 }}>
          {missingFields.map((f) => (
            <li
              key={f.key}
              style={{ color: f.level === 'required' ? '#ff4d4f' : '#faad14', marginBottom: 4 }}
            >
              {f.label}（{f.key}）
              {f.level === 'required' ? ' — 必填' : ' — 建议填写'}
            </li>
          ))}
        </ul>
      </Modal>

      {/* Preview Modal: mapping summary before save */}
      <Modal
        title="映射预览"
        open={previewModalOpen}
        width={640}
        onCancel={() => setPreviewModalOpen(false)}
        footer={[
          <Button key="cancel" onClick={() => setPreviewModalOpen(false)}>
            取消
          </Button>,
          <Button
            key="confirm"
            type="primary"
            loading={saving}
            onClick={() => void doSave()}
          >
            确认保存
          </Button>,
        ]}
      >
        <Table
          dataSource={mappingPreview}
          rowKey="sysKey"
          pagination={false}
          size="small"
          columns={[
            { title: '系统字段', dataIndex: 'sysKey', width: 160 },
            { title: '中文名', dataIndex: 'sysLabel', width: 120 },
            { title: '飞书字段', dataIndex: 'fsName', width: 180 },
            { title: '字段类型', dataIndex: 'fsType', width: 100 },
          ]}
        />
        {missingFields.length > 0 && (
          <div style={{ marginTop: 12, color: '#faad14', fontSize: 13 }}>
            注意：有 {missingFields.length} 个关键字段未映射，保存后可能影响数据同步效果。
          </div>
        )}
      </Modal>
    </div>
  );
}

export default FeishuFieldMappingPage;
