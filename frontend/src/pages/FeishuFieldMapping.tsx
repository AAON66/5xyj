import { useCallback, useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Button, Modal, Space, Spin, Typography, message } from 'antd';
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

// ── Custom node components ───────────────────────────────────────

function SystemFieldNode({ data }: { data: { label: string } }) {
  return (
    <div
      style={{
        width: 200,
        height: 40,
        background: '#FFFFFF',
        border: '1px solid #DEE0E3',
        borderRadius: 8,
        display: 'flex',
        alignItems: 'center',
        padding: '0 12px',
        fontSize: 14,
        color: '#1F2329',
      }}
    >
      {data.label}
      <Handle
        type="source"
        position={Position.Right}
        style={{ background: '#3370FF' }}
      />
    </div>
  );
}

function FeishuColumnNode({ data }: { data: { label: string } }) {
  return (
    <div
      style={{
        width: 200,
        height: 40,
        background: '#FFFFFF',
        border: '1px solid #DEE0E3',
        borderRadius: 8,
        display: 'flex',
        alignItems: 'center',
        padding: '0 12px',
        fontSize: 14,
        color: '#1F2329',
      }}
    >
      <Handle
        type="target"
        position={Position.Left}
        style={{ background: '#3370FF' }}
      />
      {data.label}
    </div>
  );
}

const nodeTypes: NodeTypes = {
  systemField: SystemFieldNode,
  feishuColumn: FeishuColumnNode,
};

const defaultEdgeOptions = {
  style: { stroke: '#3370FF', strokeWidth: 2 },
  type: 'smoothstep' as const,
};

// ── Main component ───────────────────────────────────────────────

export function FeishuFieldMappingPage() {
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
        } catch {
          // Feishu fields may not be available (no credentials)
          // Continue with empty right column
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
          position: { x: 450, y: index * 52 },
          data: { label: field.field_name },
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
  }, [configId, setNodes, setEdges]);

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
    [setEdges],
  );

  // Auto-match: exact label match first, then containment
  const handleAutoMatch = useCallback(() => {
    const newEdges: Edge[] = [];

    for (const sysField of SYSTEM_FIELDS) {
      // Try exact match first
      let matched = feishuFields.find(
        (f) => f.field_name === sysField.label,
      );

      // Then try containment
      if (!matched) {
        matched = feishuFields.find(
          (f) =>
            f.field_name.includes(sysField.label) ||
            sysField.label.includes(f.field_name),
        );
      }

      if (matched) {
        newEdges.push({
          id: `edge-${sysField.key}-${matched.field_id}`,
          source: `sys-${sysField.key}`,
          target: `fs-${matched.field_id}`,
          ...defaultEdgeOptions,
        });
      }
    }

    setEdges(newEdges);
    message.success(`自动匹配完成，已匹配 ${newEdges.length} 个字段`);
  }, [feishuFields, setEdges]);

  // Save mapping
  const handleSave = useCallback(async () => {
    if (!configId) return;
    setSaving(true);

    try {
      const mapping: Record<string, string> = {};
      for (const edge of edges) {
        const sysKey = edge.source.replace('sys-', '');
        const fsFieldId = edge.target.replace('fs-', '');
        const fsField = feishuFields.find((f) => f.field_id === fsFieldId);
        if (fsField) {
          mapping[sysKey] = fsField.field_name;
        }
      }

      await saveSyncConfigMapping(configId, mapping);
      message.success('映射已保存');
    } catch (err) {
      message.error(normalizeApiError(err).message);
    } finally {
      setSaving(false);
    }
  }, [configId, edges, feishuFields]);

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
        <Button onClick={handleAutoMatch}>
          自动匹配
        </Button>
        <Button
          type="primary"
          icon={<SaveOutlined />}
          loading={saving}
          onClick={() => void handleSave()}
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
          <Background color="#DEE0E3" gap={20} variant={BackgroundVariant.Dots} />
          <Controls position="bottom-left" />
        </ReactFlow>
      </div>
    </div>
  );
}

export default FeishuFieldMappingPage;
