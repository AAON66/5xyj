import { SwapOutlined } from "@ant-design/icons";
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
  Switch,
  Table,
  Typography,
} from "antd";
import type { ColumnsType } from "antd/es/table";
import { useCallback, useEffect, useMemo, useState } from "react";

import CompareWorkbookDiff from "../components/CompareWorkbookDiff";
import { useResponsiveViewport } from "../hooks/useResponsiveViewport";
import { normalizeApiError } from "../services/api";
import {
  fetchPeriodCompare,
  type PeriodCompareResult,
  type PeriodCompareSummaryGroup,
} from "../services/compare";
import { fetchFilterOptions, type FilterOptions } from "../services/dataManagement";
import { useSemanticColors } from "../theme/useSemanticColors";

const { Title, Text } = Typography;

const PAGE_SIZE = 40;

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

interface SummaryRow extends PeriodCompareSummaryGroup {
  key: string;
}

interface PeriodCompareQuery {
  leftPeriod: string;
  rightPeriod: string;
  region?: string;
  companyName?: string;
  searchText?: string;
  diffOnly: boolean;
}

function fieldLabel(field: string): string {
  return FIELD_LABELS[field] ?? field;
}

export default function PeriodComparePage() {
  const colors = useSemanticColors();
  const { isMobile, isTablet } = useResponsiveViewport();
  const isCompact = isMobile || isTablet;

  const [filterOptions, setFilterOptions] = useState<FilterOptions | null>(null);
  const [leftPeriod, setLeftPeriod] = useState<string | undefined>();
  const [rightPeriod, setRightPeriod] = useState<string | undefined>();
  const [region, setRegion] = useState<string | undefined>();
  const [companyName, setCompanyName] = useState<string | undefined>();
  const [searchText, setSearchText] = useState("");
  const [diffOnly, setDiffOnly] = useState(true);
  const [query, setQuery] = useState<PeriodCompareQuery | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<PeriodCompareResult | null>(null);
  const [currentPage, setCurrentPage] = useState(1);

  useEffect(() => {
    let active = true;
    fetchFilterOptions()
      .then((options) => {
        if (active) {
          setFilterOptions(options);
          const sortedPeriods = [...(options.periods ?? [])].sort();
          if (sortedPeriods.length >= 2) {
            setLeftPeriod((current) => current ?? sortedPeriods[sortedPeriods.length - 2]);
            setRightPeriod((current) => current ?? sortedPeriods[sortedPeriods.length - 1]);
          }
        }
      })
      .catch(() => {});
    return () => {
      active = false;
    };
  }, []);

  const loadCompare = useCallback(async (nextQuery: PeriodCompareQuery, nextPage: number) => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchPeriodCompare(nextQuery.leftPeriod, nextQuery.rightPeriod, {
        region: nextQuery.region,
        companyName: nextQuery.companyName,
        searchText: nextQuery.searchText,
        diffOnly: nextQuery.diffOnly,
        page: nextPage - 1,
        pageSize: PAGE_SIZE,
      });
      setData(result);
    } catch (err) {
      setError(normalizeApiError(err).message);
    } finally {
      setLoading(false);
    }
  }, []);

  const buildQuery = useCallback(
    (): PeriodCompareQuery | null => {
      if (!leftPeriod || !rightPeriod) {
        return null;
      }
      return {
        leftPeriod,
        rightPeriod,
        region,
        companyName,
        searchText: searchText.trim() || undefined,
        diffOnly,
      };
    },
    [companyName, diffOnly, leftPeriod, region, rightPeriod, searchText],
  );

  const handleRunCompare = useCallback(async () => {
    const nextQuery = buildQuery();
    if (!nextQuery) {
      return;
    }
    setQuery(nextQuery);
    setCurrentPage(1);
    await loadCompare(nextQuery, 1);
  }, [buildQuery, loadCompare]);

  useEffect(() => {
    if (!query || currentPage === 1) {
      return;
    }
    void loadCompare(query, currentPage);
  }, [currentPage, loadCompare, query]);

  const summaryRows: SummaryRow[] = useMemo(
    () =>
      (data?.summary_groups ?? []).map((group, index) => ({
        ...group,
        key: `${group.company_name ?? "unknown"}-${group.region ?? "unknown"}-${index}`,
      })),
    [data],
  );

  const summaryColumns: ColumnsType<SummaryRow> = [
    {
      title: "公司",
      dataIndex: "company_name",
      key: "company_name",
      width: 180,
      render: (value: string | null) => value ?? "-",
    },
    {
      title: "地区",
      dataIndex: "region",
      key: "region",
      width: 120,
      render: (value: string | null) => value ?? "-",
    },
    { title: "总数", dataIndex: "total_count", key: "total_count", width: 90 },
    { title: "有差异", dataIndex: "changed_count", key: "changed_count", width: 90 },
    { title: "仅左侧", dataIndex: "left_only_count", key: "left_only_count", width: 90 },
    { title: "仅右侧", dataIndex: "right_only_count", key: "right_only_count", width: 90 },
    { title: "一致", dataIndex: "same_count", key: "same_count", width: 90 },
  ];

  const periodOptions = useMemo(
    () => (filterOptions?.periods ?? []).map((period) => ({ value: period, label: period })),
    [filterOptions],
  );
  const regionOptions = useMemo(
    () => (filterOptions?.regions ?? []).map((item) => ({ value: item, label: item })),
    [filterOptions],
  );
  const companyOptions = useMemo(
    () => (filterOptions?.companies ?? []).map((item) => ({ value: item, label: item })),
    [filterOptions],
  );

  const canRunCompare = Boolean(leftPeriod && rightPeriod);

  return (
    <div>
      <Title level={4} style={{ marginBottom: 16 }}>
        跨期对比
      </Title>

      {error ? (
        <Alert
          type="error"
          message="对比失败"
          description={error}
          closable
          onClose={() => setError(null)}
          style={{ marginBottom: 16 }}
        />
      ) : null}

      <Card style={{ marginBottom: 16 }}>
        <Row gutter={[12, 12]} align="middle" wrap>
          <Col xs={24} sm={12} md="auto">
            <Text type="secondary" style={{ display: "block", marginBottom: 4 }}>
              左侧账期（基线）
            </Text>
            <Select
              data-testid="period-compare-left-period"
              style={{ width: 180 }}
              placeholder="选择左侧账期"
              value={leftPeriod}
              onChange={setLeftPeriod}
              options={periodOptions}
              allowClear
            />
          </Col>
          <Col xs={24} sm="auto" style={{ display: "flex", alignItems: "flex-end", paddingBottom: 4 }}>
            <SwapOutlined style={{ fontSize: 18, color: colors.TEXT_TERTIARY }} />
          </Col>
          <Col xs={24} sm={12} md="auto">
            <Text type="secondary" style={{ display: "block", marginBottom: 4 }}>
              右侧账期（对比）
            </Text>
            <Select
              data-testid="period-compare-right-period"
              style={{ width: 180 }}
              placeholder="选择右侧账期"
              value={rightPeriod}
              onChange={setRightPeriod}
              options={periodOptions}
              allowClear
            />
          </Col>
          <Col xs={24} sm={12} md="auto">
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
          <Col xs={24} sm={12} md="auto">
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
          <Col xs={24} md="auto" flex="auto">
            <Text type="secondary" style={{ display: "block", marginBottom: 4 }}>
              搜索
            </Text>
            <Input.Search
              value={searchText}
              onChange={(event) => setSearchText(event.target.value)}
              onSearch={() => void handleRunCompare()}
              placeholder="姓名、工号、证件号或 compare key"
              allowClear
            />
          </Col>
          <Col xs={24} md="auto">
            <div style={{ display: "flex", alignItems: "center", gap: 8, minHeight: 32 }}>
              <Text type="secondary">仅看差异</Text>
              <Switch
                checked={diffOnly}
                onChange={(checked) => {
                  setDiffOnly(checked);
                  if (query) {
                    const nextQuery = {
                      ...query,
                      diffOnly: checked,
                      searchText: searchText.trim() || undefined,
                    };
                    setQuery(nextQuery);
                    setCurrentPage(1);
                    void loadCompare(nextQuery, 1);
                  }
                }}
              />
            </div>
          </Col>
          <Col xs={24} md="auto">
            <Button type="primary" onClick={() => void handleRunCompare()} disabled={!canRunCompare} loading={loading}>
              运行对比
            </Button>
          </Col>
        </Row>
      </Card>

      {loading && !data ? (
        <Card>
          <Skeleton active paragraph={{ rows: 8 }} />
        </Card>
      ) : null}

      {!loading && !data ? (
        <Card>
          <Empty description="选择两个账期并点击“运行对比”，查看左右账期的 Excel diff 结果。" />
        </Card>
      ) : null}

      {data ? (
        <>
          <Card style={{ marginBottom: 16 }}>
            <Row gutter={[24, 16]}>
              <Col xs={24} sm={12} md="auto">
                <Statistic title="总记录" value={data.total_row_count} />
              </Col>
              <Col xs={24} sm={12} md="auto">
                <Statistic title="有差异" value={data.changed_row_count} valueStyle={{ color: colors.WARNING }} />
              </Col>
              <Col xs={24} sm={12} md="auto">
                <Statistic title="仅左侧" value={data.left_only_count} valueStyle={{ color: colors.ERROR }} />
              </Col>
              <Col xs={24} sm={12} md="auto">
                <Statistic title="仅右侧" value={data.right_only_count} valueStyle={{ color: colors.BRAND }} />
              </Col>
              <Col xs={24} sm={12} md="auto">
                <Statistic title="一致" value={data.same_row_count} />
              </Col>
            </Row>
          </Card>

          <Card style={{ marginBottom: 16 }}>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: isCompact ? "stretch" : "center",
                flexDirection: isCompact ? "column" : "row",
                gap: 12,
                marginBottom: 12,
              }}
            >
              <div>
                <Text strong>差异概览</Text>
                <Text type="secondary" style={{ marginLeft: 8 }}>
                  当前第 {data.page + 1} / {data.total_pages} 页，返回 {data.returned_row_count} 行
                </Text>
              </div>
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                <Button
                  size="small"
                  disabled={loading || currentPage <= 1}
                  onClick={() => setCurrentPage((page) => Math.max(1, page - 1))}
                >
                  上一页
                </Button>
                <Button
                  size="small"
                  disabled={loading || currentPage >= data.total_pages}
                  onClick={() => setCurrentPage((page) => Math.min(data.total_pages, page + 1))}
                >
                  下一页
                </Button>
              </div>
            </div>

            <Table<SummaryRow>
              size="small"
              columns={summaryColumns}
              dataSource={summaryRows}
              rowKey="key"
              pagination={false}
              scroll={{ x: 760 }}
            />
          </Card>

          <Card>
            <CompareWorkbookDiff
              fields={data.fields}
              rows={data.rows}
              leftLabel={`${data.left_period} · 基线`}
              rightLabel={`${data.right_period} · 对比`}
              emptyDescription="当前页没有可展示的差异记录。"
              fieldLabel={fieldLabel}
            />
          </Card>
        </>
      ) : null}
    </div>
  );
}
