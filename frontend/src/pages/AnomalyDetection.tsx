import { useCallback, useEffect, useMemo, useState } from "react";
import { useSemanticColors } from "../theme/useSemanticColors";
import { getChartColors } from "../theme/chartColors";
import { useThemeMode } from "../theme/useThemeMode";
import {
  Alert,
  Button,
  Card,
  Col,
  Collapse,
  Empty,
  InputNumber,
  message,
  Row,
  Select,
  Slider,
  Statistic,
  Table,
  Tag,
  Tooltip,
  Typography,
} from "antd";
import { AlertOutlined } from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";
import { normalizeApiError } from "../services/api";
import {
  type AnomalyRecord,
  detectAnomalies,
  fetchAnomalies,
  updateAnomalyStatus,
} from "../services/anomaly";
import { fetchFilterOptions, type FilterOptions } from "../services/dataManagement";

const { Title, Text } = Typography;

const FIELD_LABELS: Record<string, string> = {
  payment_base: "缴费基数",
  pension_company: "养老保险（单位）",
  pension_personal: "养老保险（个人）",
  medical_company: "医疗保险（单位）",
  medical_personal: "医疗保险（个人）",
  unemployment_company: "失业保险（单位）",
  unemployment_personal: "失业保险（个人）",
  injury_company: "工伤保险",
  supplementary_medical_company: "补充医疗（单位）",
  supplementary_pension_company: "补充养老（单位）",
  large_medical_personal: "大额医疗（个人）",
  medical_maternity_company: "医疗（含生育）（单位）",
  maternity_amount: "生育保险",
};

function fieldLabel(field: string): string {
  return FIELD_LABELS[field] ?? field;
}

interface ThresholdConfig {
  label: string;
  fields: string[];
  value: number;
}

const DEFAULT_THRESHOLDS: ThresholdConfig[] = [
  { label: "养老保险", fields: ["pension_company", "pension_personal"], value: 20 },
  { label: "医疗保险", fields: ["medical_company", "medical_personal", "medical_maternity_company"], value: 20 },
  { label: "失业保险", fields: ["unemployment_company", "unemployment_personal"], value: 30 },
  { label: "工伤保险", fields: ["injury_company"], value: 50 },
  { label: "生育保险", fields: ["maternity_amount"], value: 30 },
  { label: "补充医疗", fields: ["supplementary_medical_company"], value: 30 },
  { label: "补充养老", fields: ["supplementary_pension_company"], value: 30 },
  { label: "缴费基数", fields: ["payment_base"], value: 15 },
];

const STATUS_OPTIONS = [
  { value: "", label: "全部" },
  { value: "pending", label: "待处理" },
  { value: "confirmed", label: "已确认" },
  { value: "excluded", label: "已排除" },
];

const FIELD_FILTER_OPTIONS = Object.entries(FIELD_LABELS).map(([key, label]) => ({
  value: key,
  label,
}));

export default function AnomalyDetectionPage() {
  const colors = useSemanticColors();
  const { isDark } = useThemeMode();
  const chartCols = useMemo(() => getChartColors(isDark), [isDark]);
  const [filterOptions, setFilterOptions] = useState<FilterOptions | null>(null);
  const [leftPeriod, setLeftPeriod] = useState<string | undefined>();
  const [rightPeriod, setRightPeriod] = useState<string | undefined>();
  const [thresholds, setThresholds] = useState<ThresholdConfig[]>(() =>
    DEFAULT_THRESHOLDS.map((t) => ({ ...t })),
  );
  const [detecting, setDetecting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [anomalies, setAnomalies] = useState<AnomalyRecord[]>([]);
  const [total, setTotal] = useState(0);
  const [hasDetected, setHasDetected] = useState(false);
  const [statusFilter, setStatusFilter] = useState("");
  const [fieldFilter, setFieldFilter] = useState<string[]>([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);
  const [updatingStatus, setUpdatingStatus] = useState(false);
  const pageSize = 20;

  useEffect(() => {
    let active = true;
    fetchFilterOptions()
      .then((opts) => {
        if (active) setFilterOptions(opts);
      })
      .catch(() => {});
    return () => {
      active = false;
    };
  }, []);

  const buildThresholdsMap = useCallback((): Record<string, number> => {
    const map: Record<string, number> = {};
    for (const t of thresholds) {
      for (const field of t.fields) {
        map[field] = t.value;
      }
    }
    return map;
  }, [thresholds]);

  const handleDetect = useCallback(async () => {
    if (!leftPeriod || !rightPeriod) return;
    setDetecting(true);
    setError(null);
    setHasDetected(false);
    setAnomalies([]);
    setSelectedRowKeys([]);
    setCurrentPage(1);
    try {
      const result = await detectAnomalies({
        left_period: leftPeriod,
        right_period: rightPeriod,
        thresholds: buildThresholdsMap(),
      });
      setAnomalies(result);
      setTotal(result.length);
      setHasDetected(true);
      message.success(`检测完成，共发现 ${result.length} 条异常记录。`);
    } catch (err) {
      setError(normalizeApiError(err).message);
    } finally {
      setDetecting(false);
    }
  }, [leftPeriod, rightPeriod, buildThresholdsMap]);

  const loadAnomalies = useCallback(
    async (page: number) => {
      if (!leftPeriod || !rightPeriod) return;
      try {
        const result = await fetchAnomalies({
          left_period: leftPeriod,
          right_period: rightPeriod,
          status: statusFilter || undefined,
          field_name: fieldFilter.length === 1 ? fieldFilter[0] : undefined,
          page: page - 1,
          page_size: pageSize,
        });
        setAnomalies(result.items);
        setTotal(result.total);
      } catch (err) {
        setError(normalizeApiError(err).message);
      }
    },
    [leftPeriod, rightPeriod, statusFilter, fieldFilter],
  );

  useEffect(() => {
    if (hasDetected && leftPeriod && rightPeriod) {
      void loadAnomalies(currentPage);
    }
  }, [hasDetected, currentPage, statusFilter, fieldFilter, loadAnomalies, leftPeriod, rightPeriod]);

  const handleUpdateStatus = useCallback(
    async (status: "confirmed" | "excluded", ids: string[]) => {
      setUpdatingStatus(true);
      try {
        await updateAnomalyStatus(status, ids);
        setSelectedRowKeys([]);
        void loadAnomalies(currentPage);
      } catch (err) {
        setError(normalizeApiError(err).message);
      } finally {
        setUpdatingStatus(false);
      }
    },
    [currentPage, loadAnomalies],
  );

  const updateThreshold = (index: number, value: number) => {
    setThresholds((prev) => {
      const next = [...prev];
      next[index] = { ...next[index], value };
      return next;
    });
  };

  const filteredAnomalies = useMemo(() => {
    if (fieldFilter.length <= 1) return anomalies;
    return anomalies.filter((a) => fieldFilter.includes(a.field_name));
  }, [anomalies, fieldFilter]);

  const stats = useMemo(() => {
    const pending = filteredAnomalies.filter((a) => a.status === "pending").length;
    const confirmed = filteredAnomalies.filter((a) => a.status === "confirmed").length;
    return { total: filteredAnomalies.length, pending, confirmed };
  }, [filteredAnomalies]);

  const periodOptions = useMemo(
    () => (filterOptions?.periods ?? []).map((p) => ({ value: p, label: p })),
    [filterOptions],
  );

  const columns: ColumnsType<AnomalyRecord> = useMemo(() => [
    {
      title: "姓名",
      dataIndex: "person_name",
      key: "person_name",
      width: 100,
      render: (v: string | null) => v ?? "-",
    },
    {
      title: "公司",
      dataIndex: "company_name",
      key: "company_name",
      width: 120,
      ellipsis: true,
      render: (v: string | null) => v ?? "-",
    },
    {
      title: "地区",
      dataIndex: "region",
      key: "region",
      width: 80,
      render: (v: string | null) => v ?? "-",
    },
    {
      title: "异常字段",
      dataIndex: "field_name",
      key: "field_name",
      width: 120,
      render: (v: string) => fieldLabel(v),
    },
    {
      title: "左侧值",
      dataIndex: "left_value",
      key: "left_value",
      width: 100,
      align: "right",
      render: (v: number | null) => (v !== null ? String(v) : "-"),
    },
    {
      title: "右侧值",
      dataIndex: "right_value",
      key: "right_value",
      width: 100,
      align: "right",
      render: (v: number | null) => (v !== null ? String(v) : "-"),
    },
    {
      title: "变化幅度",
      dataIndex: "change_percent",
      key: "change_percent",
      width: 100,
      render: (v: number) => {
        const color = v > 0 ? chartCols.error : v < 0 ? chartCols.success : undefined;
        return <span style={{ color }}>{v > 0 ? "+" : ""}{v.toFixed(1)}%</span>;
      },
    },
    {
      title: "阈值",
      dataIndex: "threshold_percent",
      key: "threshold_percent",
      width: 80,
      render: (v: number) => <Text type="secondary">{v}%</Text>,
    },
    {
      title: "状态",
      dataIndex: "status",
      key: "status",
      width: 100,
      render: (v: string) => {
        const map: Record<string, { color: string; label: string }> = {
          pending: { color: chartCols.warning, label: "待处理" },
          confirmed: { color: chartCols.error, label: "已确认" },
          excluded: { color: chartCols.success, label: "已排除" },
        };
        const info = map[v] ?? { color: "default", label: v };
        return <Tag color={info.color}>{info.label}</Tag>;
      },
    },
    {
      title: "操作",
      key: "action",
      width: 160,
      render: (_: unknown, record: AnomalyRecord) => {
        if (record.status !== "pending") {
          return <Text type="secondary">已处理</Text>;
        }
        return (
          <div style={{ display: "flex", gap: 4 }}>
            <Button
              size="small"
              danger
              onClick={() => void handleUpdateStatus("confirmed", [record.id])}
              loading={updatingStatus}
            >
              确认异常
            </Button>
            <Button
              size="small"
              onClick={() => void handleUpdateStatus("excluded", [record.id])}
              loading={updatingStatus}
            >
              排除
            </Button>
          </div>
        );
      },
    },
  ], [chartCols, handleUpdateStatus, updatingStatus]);

  return (
    <div>
      <Title level={4} style={{ marginBottom: 16 }}>
        异常检测
      </Title>

      {error && (
        <Alert
          type="error"
          message="检测失败"
          description={error}
          closable
          onClose={() => setError(null)}
          style={{ marginBottom: 16 }}
        />
      )}

      {/* Period selectors and detect button */}
      <Card style={{ marginBottom: 16 }}>
        <Row gutter={[12, 12]} align="middle" wrap>
          <Col>
            <Text type="secondary" style={{ display: "block", marginBottom: 4 }}>
              左侧账期（基线）
            </Text>
            <Select
              style={{ width: 180 }}
              placeholder="选择左侧账期"
              value={leftPeriod}
              onChange={setLeftPeriod}
              options={periodOptions}
              allowClear
            />
          </Col>
          <Col>
            <Text type="secondary" style={{ display: "block", marginBottom: 4 }}>
              右侧账期（对比）
            </Text>
            <Select
              style={{ width: 180 }}
              placeholder="选择右侧账期"
              value={rightPeriod}
              onChange={setRightPeriod}
              options={periodOptions}
              allowClear
            />
          </Col>
          <Col style={{ display: "flex", alignItems: "flex-end" }}>
            <Tooltip title="重新检测会覆盖之前同期对的结果">
              <Button
                type="primary"
                icon={<AlertOutlined />}
                onClick={() => void handleDetect()}
                loading={detecting}
                disabled={!leftPeriod || !rightPeriod}
              >
                {detecting ? "正在检测中，请稍候..." : "开始检测"}
              </Button>
            </Tooltip>
          </Col>
        </Row>
      </Card>

      {/* Threshold config */}
      <Card style={{ marginBottom: 16 }}>
        <Collapse
          items={[
            {
              key: "thresholds",
              label: "异常阈值配置",
              children: (
                <div>
                  <Text type="secondary" style={{ display: "block", marginBottom: 12 }}>
                    按险种分别配置变化百分比阈值，超过阈值的记录将被标记为异常。
                  </Text>
                  {thresholds.map((t, index) => (
                    <Row
                      key={t.label}
                      gutter={[12, 8]}
                      align="middle"
                      style={{ marginBottom: 8 }}
                    >
                      <Col style={{ width: 120 }}>
                        <Text>{t.label}</Text>
                      </Col>
                      <Col flex="auto">
                        <Slider
                          min={5}
                          max={80}
                          value={t.value}
                          onChange={(val) => updateThreshold(index, val)}
                        />
                      </Col>
                      <Col style={{ width: 80 }}>
                        <InputNumber
                          min={5}
                          max={80}
                          value={t.value}
                          onChange={(val) => {
                            if (val !== null) updateThreshold(index, val);
                          }}
                          formatter={(val) => `${val}%`}
                          parser={(val) => Number((val ?? "").replace("%", ""))}
                          style={{ width: "100%" }}
                        />
                      </Col>
                    </Row>
                  ))}
                </div>
              ),
            },
          ]}
        />
      </Card>

      {/* Summary statistics */}
      {hasDetected && (
        <Card style={{ marginBottom: 16 }}>
          <Row gutter={[24, 16]}>
            <Col>
              <Statistic title="异常总数" value={stats.total} />
            </Col>
            <Col>
              <Statistic
                title="待处理"
                value={stats.pending}
                valueStyle={{ color: colors.WARNING }}
              />
            </Col>
            <Col>
              <Statistic
                title="已确认"
                value={stats.confirmed}
                valueStyle={{ color: colors.ERROR }}
              />
            </Col>
          </Row>
        </Card>
      )}

      {/* Filters */}
      {hasDetected && (
        <Card style={{ marginBottom: 16 }}>
          <Row gutter={[12, 12]} align="middle" wrap>
            <Col>
              <Text type="secondary" style={{ marginRight: 8 }}>状态</Text>
              <Select
                style={{ width: 140 }}
                value={statusFilter}
                onChange={(v) => {
                  setStatusFilter(v);
                  setCurrentPage(1);
                }}
                options={STATUS_OPTIONS}
              />
            </Col>
            <Col>
              <Text type="secondary" style={{ marginRight: 8 }}>险种</Text>
              <Select
                mode="multiple"
                style={{ minWidth: 200 }}
                placeholder="全部险种"
                value={fieldFilter}
                onChange={(v) => {
                  setFieldFilter(v);
                  setCurrentPage(1);
                }}
                options={FIELD_FILTER_OPTIONS}
                allowClear
              />
            </Col>
            <Col flex="auto" />
            <Col>
              <Button
                danger
                disabled={selectedRowKeys.length === 0 || updatingStatus}
                loading={updatingStatus}
                onClick={() =>
                  void handleUpdateStatus(
                    "confirmed",
                    selectedRowKeys as string[],
                  )
                }
              >
                批量确认
              </Button>
            </Col>
            <Col>
              <Button
                disabled={selectedRowKeys.length === 0 || updatingStatus}
                loading={updatingStatus}
                onClick={() =>
                  void handleUpdateStatus(
                    "excluded",
                    selectedRowKeys as string[],
                  )
                }
              >
                批量排除
              </Button>
            </Col>
          </Row>
        </Card>
      )}

      {/* Results */}
      {!hasDetected && !detecting && (
        <Card>
          <Empty description="选择两个账期并配置阈值，点击「开始检测」查找异常变动。" />
        </Card>
      )}

      {hasDetected && (
        <Card>
          <Table
            columns={columns}
            dataSource={filteredAnomalies}
            rowKey="id"
            size="middle"
            rowSelection={{
              selectedRowKeys,
              onChange: setSelectedRowKeys,
              getCheckboxProps: (record) => ({
                disabled: record.status !== "pending",
              }),
            }}
            pagination={{
              current: currentPage,
              pageSize,
              total,
              onChange: setCurrentPage,
              showSizeChanger: false,
            }}
            scroll={{ x: "max-content" }}
          />
        </Card>
      )}
    </div>
  );
}
