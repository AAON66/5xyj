import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Alert,
  Button,
  Card,
  Col,
  Empty,
  Input,
  Row,
  Select,
  Skeleton,
  Statistic,
  Table,
  Tag,
  Typography,
} from "antd";
import { SwapOutlined } from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";
import { normalizeApiError } from "../services/api";
import {
  type CompareRow,
  type PeriodCompareResult,
  type PeriodCompareSummaryGroup,
  fetchPeriodCompare,
} from "../services/compare";
import { fetchFilterOptions, type FilterOptions } from "../services/dataManagement";

const { Title, Text } = Typography;

const FIELD_LABELS: Record<string, string> = {
  person_name: "姓名",
  employee_id: "工号",
  id_number: "证件号码",
  social_security_number: "个人社保号",
  company_name: "公司名称",
  region: "地区",
  payment_base: "缴费基数",
  payment_salary: "缴费工资",
  total_amount: "总金额",
  company_total_amount: "单位合计",
  personal_total_amount: "个人合计",
  pension_company: "养老单位",
  pension_personal: "养老个人",
  medical_company: "医疗单位",
  medical_personal: "医疗个人",
  medical_maternity_company: "医疗生育单位",
  maternity_amount: "生育金额",
  unemployment_company: "失业单位",
  unemployment_personal: "失业个人",
  injury_company: "工伤单位",
  supplementary_medical_company: "补充医疗单位",
  supplementary_pension_company: "补充养老单位",
  large_medical_personal: "大额医疗个人",
  housing_fund_personal: "公积金个人",
  housing_fund_company: "公积金单位",
  housing_fund_total: "公积金合计",
};

function fieldLabel(field: string): string {
  return FIELD_LABELS[field] ?? field;
}

function diffCellStyle(
  leftVal: number | null | undefined,
  rightVal: number | null | undefined,
): React.CSSProperties {
  const l = typeof leftVal === "number" ? leftVal : null;
  const r = typeof rightVal === "number" ? rightVal : null;
  if (l === null || r === null || l === r) return {};
  if (r > l) return { color: "#00B42A" };
  return { color: "#F54A45" };
}

function rowBackground(status: string): string | undefined {
  if (status === "right_only") return "#F0F5FF";
  if (status === "left_only") return "#FFF1F0";
  return undefined;
}

interface SummaryRow extends PeriodCompareSummaryGroup {
  key: string;
}

export default function PeriodComparePage() {
  const [filterOptions, setFilterOptions] = useState<FilterOptions | null>(null);
  const [leftPeriod, setLeftPeriod] = useState<string | undefined>();
  const [rightPeriod, setRightPeriod] = useState<string | undefined>();
  const [region, setRegion] = useState<string | undefined>();
  const [companyName, setCompanyName] = useState<string | undefined>();
  const [searchText, setSearchText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<PeriodCompareResult | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
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

  const handleCompare = useCallback(async () => {
    if (!leftPeriod || !rightPeriod) return;
    setLoading(true);
    setError(null);
    setData(null);
    setCurrentPage(1);
    try {
      const result = await fetchPeriodCompare(leftPeriod, rightPeriod, {
        region,
        companyName,
        page: 0,
        pageSize: 500,
      });
      setData(result);
    } catch (err) {
      setError(normalizeApiError(err).message);
    } finally {
      setLoading(false);
    }
  }, [leftPeriod, rightPeriod, region, companyName]);

  const summaryRows: SummaryRow[] = useMemo(() => {
    if (!data) return [];
    return data.summary_groups.map((g, i) => ({
      ...g,
      key: `${g.company_name ?? "unknown"}-${g.region ?? "unknown"}-${i}`,
    }));
  }, [data]);

  const filteredDetailRows = useMemo(() => {
    if (!data) return [];
    const keyword = searchText.trim().toLowerCase();
    if (!keyword) return data.rows;
    return data.rows.filter((row) => {
      const vals = [
        row.compare_key,
        row.left.values.person_name,
        row.right.values.person_name,
        row.left.values.employee_id,
        row.right.values.employee_id,
        row.left.values.id_number,
        row.right.values.id_number,
      ];
      return vals.some(
        (v) => v !== null && v !== undefined && String(v).toLowerCase().includes(keyword),
      );
    });
  }, [data, searchText]);

  const summaryColumns: ColumnsType<SummaryRow> = [
    { title: "公司", dataIndex: "company_name", key: "company_name", render: (v: string | null) => v ?? "-" },
    { title: "地区", dataIndex: "region", key: "region", render: (v: string | null) => v ?? "-" },
    { title: "总数", dataIndex: "total_count", key: "total_count" },
    {
      title: "有差异",
      dataIndex: "changed_count",
      key: "changed_count",
      render: (v: number) => <span style={{ color: v > 0 ? "#FF7D00" : undefined }}>{v}</span>,
    },
    {
      title: "仅左侧",
      dataIndex: "left_only_count",
      key: "left_only_count",
      render: (v: number) => <span style={{ color: v > 0 ? "#F54A45" : undefined }}>{v}</span>,
    },
    {
      title: "仅右侧",
      dataIndex: "right_only_count",
      key: "right_only_count",
      render: (v: number) => <span style={{ color: v > 0 ? "#3370FF" : undefined }}>{v}</span>,
    },
    { title: "一致", dataIndex: "same_count", key: "same_count" },
  ];

  function buildDetailColumns(fields: string[]): ColumnsType<CompareRow> {
    const cols: ColumnsType<CompareRow> = [
      {
        title: "姓名",
        key: "person_name",
        width: 100,
        render: (_: unknown, row: CompareRow) =>
          String(row.left.values.person_name ?? row.right.values.person_name ?? "-"),
      },
      {
        title: "工号",
        key: "employee_id",
        width: 100,
        render: (_: unknown, row: CompareRow) =>
          String(row.left.values.employee_id ?? row.right.values.employee_id ?? "-"),
      },
      {
        title: "状态",
        key: "diff_status",
        width: 80,
        render: (_: unknown, row: CompareRow) => {
          const m: Record<string, { color: string; label: string }> = {
            same: { color: "default", label: "一致" },
            changed: { color: "warning", label: "有差异" },
            left_only: { color: "error", label: "仅左侧" },
            right_only: { color: "blue", label: "仅右侧" },
          };
          const info = m[row.diff_status] ?? { color: "default", label: row.diff_status };
          return <Tag color={info.color}>{info.label}</Tag>;
        },
      },
    ];

    const diffFields = fields.filter(
      (f) =>
        !["person_name", "employee_id", "id_number", "company_name", "region", "billing_period", "period_start", "period_end"].includes(f),
    );

    for (const field of diffFields) {
      cols.push({
        title: fieldLabel(field),
        key: field,
        width: 140,
        render: (_: unknown, row: CompareRow) => {
          const leftVal = row.left.values[field];
          const rightVal = row.right.values[field];
          const isChanged = row.different_fields.includes(field);
          const cellBg = isChanged ? "#FFF7E6" : undefined;
          const style = diffCellStyle(
            leftVal as number | null | undefined,
            rightVal as number | null | undefined,
          );
          const leftStr = leftVal !== null && leftVal !== undefined ? String(leftVal) : "-";
          const rightStr = rightVal !== null && rightVal !== undefined ? String(rightVal) : "-";
          return (
            <div style={{ background: cellBg, padding: "4px 8px", borderRadius: 4 }}>
              <div>
                <Text type="secondary" style={{ fontSize: 12 }}>
                  左:
                </Text>{" "}
                {leftStr}
              </div>
              <div style={style}>
                <Text type="secondary" style={{ fontSize: 12 }}>
                  右:
                </Text>{" "}
                {rightStr}
              </div>
            </div>
          );
        },
      });
    }
    return cols;
  }

  const expandedRowRender = (record: SummaryRow) => {
    if (!data) return null;
    const rows = filteredDetailRows.filter((row) => {
      const rowCompany = String(row.left.values.company_name ?? row.right.values.company_name ?? "");
      const rowRegion = String(row.left.values.region ?? row.right.values.region ?? "");
      return (
        (record.company_name === null || rowCompany === record.company_name) &&
        (record.region === null || rowRegion === record.region)
      );
    });
    const detailCols = buildDetailColumns(data.fields);
    return (
      <Table
        columns={detailCols}
        dataSource={rows}
        rowKey="compare_key"
        size="small"
        pagination={{ pageSize, current: currentPage, onChange: setCurrentPage }}
        scroll={{ x: "max-content" }}
        rowClassName={(row) => ""}
        onRow={(row) => ({
          style: { background: rowBackground(row.diff_status) },
        })}
      />
    );
  };

  const periodOptions = useMemo(
    () =>
      (filterOptions?.periods ?? []).map((p) => ({
        value: p,
        label: p,
      })),
    [filterOptions],
  );

  const regionOptions = useMemo(
    () =>
      (filterOptions?.regions ?? []).map((r) => ({
        value: r,
        label: r,
      })),
    [filterOptions],
  );

  const companyOptions = useMemo(
    () =>
      (filterOptions?.companies ?? []).map((c) => ({
        value: c,
        label: c,
      })),
    [filterOptions],
  );

  return (
    <div>
      <Title level={4} style={{ marginBottom: 16 }}>
        跨期对比
      </Title>

      {error && (
        <Alert
          type="error"
          message="对比失败"
          description={error}
          closable
          onClose={() => setError(null)}
          style={{ marginBottom: 16 }}
        />
      )}

      {/* Filter row */}
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
          <Col style={{ display: "flex", alignItems: "flex-end", paddingBottom: 4 }}>
            <SwapOutlined style={{ fontSize: 18, color: "#8F959E" }} />
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
          <Col>
            <Text type="secondary" style={{ display: "block", marginBottom: 4 }}>
              地区
            </Text>
            <Select
              style={{ width: 140 }}
              placeholder="全部地区"
              value={region}
              onChange={setRegion}
              options={regionOptions}
              allowClear
            />
          </Col>
          <Col>
            <Text type="secondary" style={{ display: "block", marginBottom: 4 }}>
              公司
            </Text>
            <Select
              style={{ width: 180 }}
              placeholder="全部公司"
              value={companyName}
              onChange={setCompanyName}
              options={companyOptions}
              allowClear
            />
          </Col>
          <Col style={{ display: "flex", alignItems: "flex-end" }}>
            <Button
              type="primary"
              onClick={() => void handleCompare()}
              loading={loading}
              disabled={!leftPeriod || !rightPeriod}
            >
              运行对比
            </Button>
          </Col>
        </Row>
      </Card>

      {/* Summary statistics */}
      {data && (
        <Card style={{ marginBottom: 16 }}>
          <Row gutter={[24, 16]}>
            <Col>
              <Statistic title="总记录" value={data.total_row_count} />
            </Col>
            <Col>
              <Statistic
                title="有差异"
                value={data.changed_row_count}
                valueStyle={{ color: "#FF7D00" }}
              />
            </Col>
            <Col>
              <Statistic
                title="仅左侧"
                value={data.left_only_count}
                valueStyle={{ color: "#F54A45" }}
              />
            </Col>
            <Col>
              <Statistic
                title="仅右侧"
                value={data.right_only_count}
                valueStyle={{ color: "#3370FF" }}
              />
            </Col>
            <Col>
              <Statistic title="一致" value={data.same_row_count} />
            </Col>
          </Row>
        </Card>
      )}

      {/* Search */}
      {data && (
        <Card style={{ marginBottom: 16 }}>
          <Input.Search
            placeholder="按姓名、工号、证件号搜索"
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            style={{ maxWidth: 400 }}
            allowClear
          />
        </Card>
      )}

      {/* Results */}
      {loading && (
        <Card>
          <Skeleton active paragraph={{ rows: 6 }} />
        </Card>
      )}

      {!loading && !data && (
        <Card>
          <Empty description="选择两个账期，点击「运行对比」查看数据差异。" />
        </Card>
      )}

      {!loading && data && data.total_row_count === 0 && (
        <Card>
          <Empty description="所选账期之间没有差异数据。" />
        </Card>
      )}

      {!loading && data && data.total_row_count > 0 && (
        <Card>
          <Table
            columns={summaryColumns}
            dataSource={summaryRows}
            rowKey="key"
            expandable={{ expandedRowRender }}
            pagination={false}
            size="middle"
          />
        </Card>
      )}
    </div>
  );
}
