import { useEffect, useMemo, useRef, useState, type ChangeEvent } from "react";
import {
  Alert,
  Button,
  Card,
  Checkbox,
  Col,
  Empty,
  Input,
  Progress,
  Row,
  Select,
  Statistic,
  Steps,
  Tabs,
  Tag,
  Typography,
} from "antd";
import {
  CloudUploadOutlined,
  DeleteOutlined,
  ExportOutlined,
  PlayCircleOutlined,
  SwapOutlined,
} from "@ant-design/icons";
import { ApiClientError, normalizeApiError } from "../services/api";
import {
  type BatchCompareResult,
  type CompareCellValue,
  type CompareExportPayload,
  exportBatchCompare,
  fetchBatchCompare,
} from "../services/compare";
import { createImportBatch, fetchImportBatches, parseImportBatch, type ImportBatchSummary } from "../services/imports";
import { fetchBatchExport, type BatchExport } from "../services/runtime";

const { Title, Text } = Typography;

type SourceMode = "existing" | "local";
type Side = "left" | "right";
type CompareTableType = "salary" | "final_tool";

const FIELD_LABELS: Record<string, string> = {
  person_name: "姓名",
  employee_id: "工号",
  id_number: "证件号码",
  social_security_number: "个人社保号",
  housing_fund_account: "公积金账号",
  company_name: "公司名称",
  region: "地区",
  billing_period: "所属期",
  period_start: "所属期起",
  period_end: "所属期止",
  payment_base: "缴费基数",
  payment_salary: "缴费工资",
  housing_fund_base: "公积金基数",
  housing_fund_personal: "公积金个人",
  housing_fund_company: "公积金单位",
  housing_fund_total: "公积金合计",
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
  late_fee: "滞纳金",
  interest: "利息",
  raw_sheet_name: "源工作表",
  raw_header_signature: "表头签名",
  source_file_name: "源文件",
};

const PAGE_SIZE_OPTIONS = [10, 20, 50] as const;

const COMPARE_TABLE_FIELDS: Record<CompareTableType, string[]> = {
  salary: [
    "person_name", "employee_id", "medical_personal", "unemployment_personal",
    "large_medical_personal", "pension_personal", "housing_fund_personal",
    "pension_company", "medical_maternity_company", "unemployment_company",
    "injury_company", "maternity_amount", "supplementary_medical_company",
    "housing_fund_company", "personal_total_amount", "housing_fund_total",
    "company_total_amount", "total_amount",
  ],
  final_tool: [
    "company_name", "region", "person_name", "id_number", "employee_id",
    "medical_personal", "unemployment_personal", "large_medical_personal",
    "pension_personal", "housing_fund_personal", "pension_company",
    "medical_maternity_company", "unemployment_company", "injury_company",
    "maternity_amount", "supplementary_medical_company", "housing_fund_company",
    "personal_total_amount", "company_total_amount", "housing_fund_total",
    "total_amount",
  ],
};

interface UploadEntry {
  id: string;
  name: string;
  meta: string;
}

interface CompareProgressStep {
  key: string;
  label: string;
  message: string;
}

interface CompareProgressState {
  steps: CompareProgressStep[];
  completedKeys: string[];
  currentKey: string | null;
  currentStep: number;
  totalSteps: number;
  label: string;
  message: string;
  percent: number;
}

function fieldLabel(field: string): string {
  return FIELD_LABELS[field] ?? field;
}

function batchLabel(batch: ImportBatchSummary): string {
  return `${batch.batch_name} · ${batch.status}`;
}

function sourceModeLabel(mode: SourceMode): string {
  return mode === "local" ? "本地文件" : "云端批次";
}

function statusLabel(status: string): string {
  switch (status) {
    case "same": return "一致";
    case "changed": return "有差异";
    case "left_only": return "仅左侧";
    case "right_only": return "仅右侧";
    default: return status;
  }
}

function statusColor(status: string): string {
  switch (status) {
    case "same": return "default";
    case "changed": return "warning";
    case "left_only": return "blue";
    case "right_only": return "orange";
    default: return "default";
  }
}

function normalizeCellValue(value: CompareCellValue): string | null {
  if (value === null || value === undefined) return null;
  const normalized = String(value).trim();
  return normalized.length > 0 ? normalized : null;
}

function displayValue(value: CompareCellValue): string {
  return value === null || value === undefined ? "" : String(value);
}

function hasValue(value: CompareCellValue): boolean {
  return normalizeCellValue(value) !== null;
}

function pickRowValue(row: BatchCompareResult["rows"][number], field: string): string {
  return displayValue(row.left.values[field] ?? row.right.values[field] ?? null);
}

function visibleFieldsForRow(data: BatchCompareResult, row: BatchCompareResult["rows"][number], showAllFields: boolean): string[] {
  if (showAllFields) return data.fields;
  if (row.diff_status === "changed" && row.different_fields.length > 0) return row.different_fields;
  const previewFields = [
    "person_name", "employee_id", "id_number", "company_name", "region",
    "billing_period", "total_amount", "company_total_amount", "personal_total_amount",
  ];
  const nonEmpty = previewFields.filter(
    (f) => hasValue(row.left.values[f] ?? null) || hasValue(row.right.values[f] ?? null),
  );
  return nonEmpty.length > 0
    ? nonEmpty
    : data.fields.filter((f) => hasValue(row.left.values[f] ?? null) || hasValue(row.right.values[f] ?? null)).slice(0, 8);
}

function buildCompareSteps(leftMode: SourceMode, rightMode: SourceMode): CompareProgressStep[] {
  const steps: CompareProgressStep[] = [
    { key: "validate", label: "检查数据源", message: "确认左右两侧的来源配置完整。" },
  ];
  if (leftMode === "local") {
    steps.push(
      { key: "left-upload", label: "上传左侧本地文件", message: "正在为左侧本地 Excel 创建临时批次。" },
      { key: "left-parse", label: "解析左侧本地文件", message: "正在解析左侧 Excel。" },
    );
  }
  if (rightMode === "local") {
    steps.push(
      { key: "right-upload", label: "上传右侧本地文件", message: "正在为右侧本地 Excel 创建临时批次。" },
      { key: "right-parse", label: "解析右侧本地文件", message: "正在解析右侧 Excel。" },
    );
  }
  steps.push(
    { key: "compare", label: "拉取对比结果", message: "正在计算左右两侧的差异结果。" },
    { key: "sync", label: "同步页面数据", message: "正在把最新结果同步到页面。" },
  );
  return steps;
}

function buildCompareProgressState(steps: CompareProgressStep[], completedKeys: string[], currentKey: string | null): CompareProgressState {
  const totalSteps = steps.length;
  const activeIndex = currentKey ? Math.max(0, steps.findIndex((s) => s.key === currentKey)) : totalSteps - 1;
  const activeStep = currentKey ? steps[activeIndex] : null;
  const percent = currentKey
    ? Math.max(8, Math.min(98, Math.round(((completedKeys.length + 0.45) / totalSteps) * 100)))
    : 100;
  return {
    steps, completedKeys, currentKey,
    currentStep: currentKey ? activeIndex + 1 : totalSteps,
    totalSteps,
    label: activeStep?.label ?? "对比完成",
    message: activeStep?.message ?? "对比结果已完成同步。",
    percent,
  };
}

function filterCompareDataByTable(data: BatchCompareResult, tableType: CompareTableType): BatchCompareResult {
  const preferredFields = COMPARE_TABLE_FIELDS[tableType];
  const fields = data.fields.filter((f) => preferredFields.includes(f));
  const effectiveFields = fields.length > 0 ? fields : data.fields;
  const rows = data.rows.map((row) => {
    const differentFields = row.different_fields.filter((f) => effectiveFields.includes(f));
    const leftExists = effectiveFields.some((f) => hasValue(row.left.values[f] ?? null)) || Boolean(row.left.source_file_name);
    const rightExists = effectiveFields.some((f) => hasValue(row.right.values[f] ?? null)) || Boolean(row.right.source_file_name);
    let diffStatus = "same";
    if (!leftExists && rightExists) diffStatus = "right_only";
    else if (leftExists && !rightExists) diffStatus = "left_only";
    else if (differentFields.length > 0) diffStatus = "changed";
    return { ...row, diff_status: diffStatus, different_fields: differentFields };
  });
  return {
    ...data, fields: effectiveFields, rows,
    total_row_count: rows.length,
    same_row_count: rows.filter((r) => r.diff_status === "same").length,
    changed_row_count: rows.filter((r) => r.diff_status === "changed").length,
    left_only_count: rows.filter((r) => r.diff_status === "left_only").length,
    right_only_count: rows.filter((r) => r.diff_status === "right_only").length,
  };
}

function isArtifactReady(exportSnapshot: BatchExport | null, tableType: CompareTableType): boolean {
  return Boolean(exportSnapshot?.artifacts.some((a) => a.template_type === tableType && a.status === "completed"));
}

function cloneRowWithFieldUpdate(
  data: BatchCompareResult, compareKey: string, side: Side, field: string, nextValue: string,
): BatchCompareResult {
  const rows = data.rows.map((row) => {
    if (row.compare_key !== compareKey) return row;
    const nextSide = { ...row[side], values: { ...row[side].values, [field]: nextValue.trim().length > 0 ? nextValue : null } };
    const left = side === "left" ? nextSide : row.left;
    const right = side === "right" ? nextSide : row.right;
    const differentFields = data.fields.filter(
      (f) => normalizeCellValue(left.values[f] ?? null) !== normalizeCellValue(right.values[f] ?? null),
    );
    const leftExists = Object.values(left.values).some((v) => normalizeCellValue(v) !== null) || !!left.source_file_name;
    const rightExists = Object.values(right.values).some((v) => normalizeCellValue(v) !== null) || !!right.source_file_name;
    let diffStatus = "same";
    if (!leftExists && rightExists) diffStatus = "right_only";
    else if (leftExists && !rightExists) diffStatus = "left_only";
    else if (differentFields.length > 0) diffStatus = "changed";
    return { ...row, left, right, diff_status: diffStatus, different_fields: diffStatus === "same" ? [] : differentFields };
  });
  return {
    ...data, rows,
    total_row_count: rows.length,
    same_row_count: rows.filter((r) => r.diff_status === "same").length,
    changed_row_count: rows.filter((r) => r.diff_status === "changed").length,
    left_only_count: rows.filter((r) => r.diff_status === "left_only").length,
    right_only_count: rows.filter((r) => r.diff_status === "right_only").length,
  };
}

function fileKey(file: File): string {
  return `${file.name}_${file.size}_${file.lastModified}`;
}

function formatFileSize(size: number): string {
  if (size >= 1024 * 1024) return `${(size / (1024 * 1024)).toFixed(2)} MB`;
  if (size >= 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${size} B`;
}

function mapFilesToEntries(files: File[]): UploadEntry[] {
  return files.map((file) => ({ id: fileKey(file), name: file.name, meta: formatFileSize(file.size) }));
}

function mergeFiles(existing: File[], incoming: File[]): File[] {
  const known = new Set(existing.map((f) => fileKey(f)));
  const next = [...existing];
  for (const file of incoming) {
    const key = fileKey(file);
    if (!known.has(key)) { known.add(key); next.push(file); }
  }
  return next;
}

function buildTempBatchName(side: Side): string {
  const now = new Date();
  const pad = (v: number) => String(v).padStart(2, "0");
  const stamp = `${now.getFullYear()}${pad(now.getMonth() + 1)}${pad(now.getDate())}-${pad(now.getHours())}${pad(now.getMinutes())}${pad(now.getSeconds())}`;
  return `${side === "left" ? "左侧" : "右侧"}本地对比-${stamp}`;
}

function triggerBlobDownload(blob: Blob, fileName: string): void {
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = fileName;
  document.body.appendChild(a);
  a.click(); a.remove();
  window.URL.revokeObjectURL(url);
}

export function ComparePage() {
  const [batches, setBatches] = useState<ImportBatchSummary[]>([]);
  const [leftMode, setLeftMode] = useState<SourceMode>("existing");
  const [rightMode, setRightMode] = useState<SourceMode>("existing");
  const [leftBatchId, setLeftBatchId] = useState("");
  const [rightBatchId, setRightBatchId] = useState("");
  const [leftLocalFiles, setLeftLocalFiles] = useState<File[]>([]);
  const [rightLocalFiles, setRightLocalFiles] = useState<File[]>([]);
  const [compareData, setCompareData] = useState<BatchCompareResult | null>(null);
  const [compareTableType, setCompareTableType] = useState<CompareTableType>("salary");
  const [loadingBatches, setLoadingBatches] = useState(true);
  const [runningCompare, setRunningCompare] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [onlyDifferences, setOnlyDifferences] = useState(true);
  const [showAllFields, setShowAllFields] = useState(false);
  const [searchText, setSearchText] = useState("");
  const [pageSize, setPageSize] = useState<number>(PAGE_SIZE_OPTIONS[1]);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageError, setPageError] = useState<string | null>(null);
  const [notice, setNotice] = useState<{ type: "success" | "info"; message: string } | null>(null);
  const [compareProgress, setCompareProgress] = useState<CompareProgressState | null>(null);
  const [leftExportSnapshot, setLeftExportSnapshot] = useState<BatchExport | null>(null);
  const [rightExportSnapshot, setRightExportSnapshot] = useState<BatchExport | null>(null);

  const leftInputRef = useRef<HTMLInputElement | null>(null);
  const rightInputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    let active = true;
    async function loadBatches() {
      try {
        const result = await fetchImportBatches();
        if (!active) return;
        setBatches(result);
        if (result.length >= 2) {
          setLeftBatchId((c) => c || result[0].id);
          setRightBatchId((c) => c || result[1].id);
        } else if (result[0]) {
          setLeftBatchId((c) => c || result[0].id);
        }
      } catch (error) {
        if (active) setPageError(normalizeApiError(error).message);
      } finally {
        if (active) setLoadingBatches(false);
      }
    }
    void loadBatches();
    return () => { active = false; };
  }, []);

  useEffect(() => {
    let active = true;
    async function loadExportSnapshot(side: Side, batchId: string) {
      try {
        const snapshot = await fetchBatchExport(batchId);
        if (!active) return;
        if (side === "left") setLeftExportSnapshot(snapshot);
        else setRightExportSnapshot(snapshot);
      } catch {
        if (!active) return;
        if (side === "left") setLeftExportSnapshot(null);
        else setRightExportSnapshot(null);
      }
    }
    if (leftMode === "existing" && leftBatchId) void loadExportSnapshot("left", leftBatchId);
    else setLeftExportSnapshot(null);
    if (rightMode === "existing" && rightBatchId) void loadExportSnapshot("right", rightBatchId);
    else setRightExportSnapshot(null);
    return () => { active = false; };
  }, [leftBatchId, leftMode, rightBatchId, rightMode]);

  const displayCompareData = useMemo(
    () => (compareData ? filterCompareDataByTable(compareData, compareTableType) : null),
    [compareData, compareTableType],
  );

  const filteredRows = useMemo(() => {
    if (!displayCompareData) return [];
    const keyword = searchText.trim().toLowerCase();
    return displayCompareData.rows.filter((row) => {
      if (onlyDifferences && row.diff_status === "same") return false;
      if (!keyword) return true;
      const values = [
        row.compare_key,
        row.left.source_file_name ?? "",
        row.right.source_file_name ?? "",
        ...Object.values(row.left.values).map((v) => (v === null ? "" : String(v))),
        ...Object.values(row.right.values).map((v) => (v === null ? "" : String(v))),
      ];
      return values.some((v) => v.toLowerCase().includes(keyword));
    });
  }, [displayCompareData, onlyDifferences, searchText]);

  const totalPages = Math.max(1, Math.ceil(filteredRows.length / pageSize));

  useEffect(() => { setCurrentPage(1); }, [searchText, onlyDifferences, pageSize, compareTableType, displayCompareData?.left_batch.id, displayCompareData?.right_batch.id]);
  useEffect(() => { if (currentPage > totalPages) setCurrentPage(totalPages); }, [currentPage, totalPages]);

  const pagedRows = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredRows.slice(start, start + pageSize);
  }, [currentPage, filteredRows, pageSize]);

  const leftEntries = useMemo(() => mapFilesToEntries(leftLocalFiles), [leftLocalFiles]);
  const rightEntries = useMemo(() => mapFilesToEntries(rightLocalFiles), [rightLocalFiles]);

  function handleFileSelection(side: Side, event: ChangeEvent<HTMLInputElement>) {
    const selected = Array.from(event.target.files ?? []);
    event.target.value = "";
    setPageError(null);
    if (side === "left") setLeftLocalFiles((c) => mergeFiles(c, selected));
    else setRightLocalFiles((c) => mergeFiles(c, selected));
  }

  function removeLocalFile(side: Side, entryId: string) {
    if (side === "left") setLeftLocalFiles((c) => c.filter((f) => fileKey(f) !== entryId));
    else setRightLocalFiles((c) => c.filter((f) => fileKey(f) !== entryId));
  }

  async function resolveSideBatchId(
    side: Side,
    progressHandlers?: { activateStep: (k: string) => void; completeStep: (k: string) => void },
  ): Promise<string> {
    const mode = side === "left" ? leftMode : rightMode;
    const batchId = side === "left" ? leftBatchId : rightBatchId;
    const localFiles = side === "left" ? leftLocalFiles : rightLocalFiles;
    if (mode === "existing") {
      if (!batchId) throw new ApiClientError(`${side === "left" ? "左侧" : "右侧"}还没有选择线上批次。`);
      return batchId;
    }
    if (!localFiles.length) throw new ApiClientError(`${side === "left" ? "左侧" : "右侧"}还没有上传本地文件。`);
    const uploadKey = `${side}-upload`;
    const parseKey = `${side}-parse`;
    progressHandlers?.activateStep(uploadKey);
    const batch = await createImportBatch({ files: localFiles, batchName: buildTempBatchName(side) });
    progressHandlers?.completeStep(uploadKey);
    progressHandlers?.activateStep(parseKey);
    await parseImportBatch(batch.id);
    progressHandlers?.completeStep(parseKey);
    if (side === "left") setLeftBatchId(batch.id);
    else setRightBatchId(batch.id);
    return batch.id;
  }

  async function handleRunCompare() {
    setRunningCompare(true);
    setPageError(null);
    setNotice(null);
    setCompareProgress(null);
    try {
      const steps = buildCompareSteps(leftMode, rightMode);
      let completedKeys: string[] = [];
      const refreshProgress = (currentKey: string | null) => {
        setCompareProgress(buildCompareProgressState(steps, completedKeys, currentKey));
      };
      const activateStep = (key: string) => refreshProgress(key);
      const completeStep = (key: string) => {
        if (!completedKeys.includes(key)) completedKeys = [...completedKeys, key];
        const next = steps.find((s) => !completedKeys.includes(s.key));
        refreshProgress(next?.key ?? null);
      };
      activateStep("validate");
      if (leftMode === "existing" && !leftBatchId) throw new ApiClientError("左侧还没有选择线上批次。");
      if (rightMode === "existing" && !rightBatchId) throw new ApiClientError("右侧还没有选择线上批次。");
      if (leftMode === "local" && !leftLocalFiles.length) throw new ApiClientError("左侧还没有上传本地文件。");
      if (rightMode === "local" && !rightLocalFiles.length) throw new ApiClientError("右侧还没有上传本地文件。");
      completeStep("validate");
      const resolvedLeftBatchId = await resolveSideBatchId("left", { activateStep, completeStep });
      const resolvedRightBatchId = await resolveSideBatchId("right", { activateStep, completeStep });
      if (resolvedLeftBatchId === resolvedRightBatchId) throw new ApiClientError("左侧和右侧不能使用同一个批次。");
      activateStep("compare");
      const result = await fetchBatchCompare(resolvedLeftBatchId, resolvedRightBatchId);
      completeStep("compare");
      activateStep("sync");
      const batchList = await fetchImportBatches().catch(() => null);
      if (batchList) setBatches(batchList);
      setCompareData(result);
      setCurrentPage(1);
      completeStep("sync");
      setNotice({ type: "success", message: "对比结果已刷新。" });
    } catch (error) {
      const normalized = error instanceof ApiClientError ? error : normalizeApiError(error);
      setPageError(normalized.message);
    } finally {
      setRunningCompare(false);
    }
  }

  async function handleExport() {
    if (!compareData) return;
    setExporting(true);
    setPageError(null);
    setNotice(null);
    try {
      const payload: CompareExportPayload = {
        left_batch_name: compareData.left_batch.batch_name,
        right_batch_name: compareData.right_batch.batch_name,
        fields: compareData.fields,
        rows: compareData.rows,
      };
      const { blob, fileName } = await exportBatchCompare(payload);
      triggerBlobDownload(blob, fileName);
      setNotice({ type: "success", message: "已导出当前修改后的对比结果。" });
    } catch (error) {
      const normalized = error instanceof ApiClientError ? error : normalizeApiError(error);
      setPageError(normalized.message);
    } finally {
      setExporting(false);
    }
  }

  function handleCellChange(compareKey: string, side: Side, field: string, nextValue: string) {
    setCompareData((current) => {
      if (!current) return current;
      return cloneRowWithFieldUpdate(current, compareKey, side, field, nextValue);
    });
  }

  function renderSourcePanel(side: Side) {
    const mode = side === "left" ? leftMode : rightMode;
    const batchId = side === "left" ? leftBatchId : rightBatchId;
    const localEntries = side === "left" ? leftEntries : rightEntries;
    const inputRef = side === "left" ? leftInputRef : rightInputRef;
    const title = side === "left" ? "左侧数据源" : "右侧数据源";
    const subtitle = side === "left" ? "本月 / 新融合" : "上月 / 基线";

    return (
      <Card size="small" title={<><Text strong>{title}</Text> <Text type="secondary">{subtitle}</Text></>}>
        <div style={{ marginBottom: 8 }}>
          <Text type="secondary" style={{ display: "block", marginBottom: 4 }}>来源方式</Text>
          <Select
            style={{ width: "100%" }}
            value={mode}
            onChange={(val) => {
              if (side === "left") setLeftMode(val);
              else setRightMode(val);
            }}
            options={[
              { value: "existing", label: "使用线上批次" },
              { value: "local", label: "使用本地 Excel" },
            ]}
          />
        </div>

        {mode === "existing" ? (
          <div>
            <Text type="secondary" style={{ display: "block", marginBottom: 4 }}>选择批次</Text>
            <Select
              style={{ width: "100%" }}
              value={batchId || undefined}
              placeholder="请选择批次"
              onChange={(val) => (side === "left" ? setLeftBatchId(val) : setRightBatchId(val))}
              loading={loadingBatches}
              options={batches.map((b) => ({ value: b.id, label: batchLabel(b) }))}
            />
          </div>
        ) : (
          <>
            <input
              ref={inputRef}
              type="file"
              accept=".xlsx,.xls"
              multiple
              hidden
              onChange={(e) => handleFileSelection(side, e)}
            />
            <div style={{ display: "flex", gap: 8, marginBottom: 8 }}>
              <Button type="primary" icon={<CloudUploadOutlined />} onClick={() => inputRef.current?.click()}>
                选择本地文件
              </Button>
              <Button
                icon={<DeleteOutlined />}
                disabled={!localEntries.length}
                onClick={() => (side === "left" ? setLeftLocalFiles([]) : setRightLocalFiles([]))}
              >
                清空
              </Button>
            </div>
            {localEntries.length > 0 ? (
              <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                {localEntries.map((entry) => (
                  <div key={entry.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "4px 8px", background: "#fafafa", borderRadius: 4 }}>
                    <div>
                      <Text strong style={{ fontSize: 13 }}>{entry.name}</Text>
                      <Text type="secondary" style={{ marginLeft: 8, fontSize: 12 }}>{entry.meta}</Text>
                    </div>
                    <Button type="link" danger size="small" onClick={() => removeLocalFile(side, entry.id)}>删除</Button>
                  </div>
                ))}
              </div>
            ) : (
              <Text type="secondary" style={{ fontSize: 13 }}>上传 Excel 后，这一侧会按本地文件生成临时批次参与对比。</Text>
            )}
          </>
        )}
      </Card>
    );
  }

  function renderTableAvailability(side: Side) {
    const mode = side === "left" ? leftMode : rightMode;
    const batchId = side === "left" ? leftBatchId : rightBatchId;
    const exportSnapshot = side === "left" ? leftExportSnapshot : rightExportSnapshot;
    const sideLabel = side === "left" ? "左侧" : "右侧";
    const tableLabel = compareTableType === "salary" ? "薪酬表格" : "Tool 表格";

    if (mode === "local") {
      return <Tag color="processing">{sideLabel}: 本地文件解析后参与对比</Tag>;
    }
    if (!batchId) {
      return <Tag>{sideLabel}: 未选择云端任务</Tag>;
    }
    if (!exportSnapshot) {
      return <Tag color="processing">{sideLabel}: 正在读取导出记录</Tag>;
    }
    if (isArtifactReady(exportSnapshot, compareTableType)) {
      return <Tag color="success">{sideLabel}: 已有{tableLabel}</Tag>;
    }
    return <Tag color="warning">{sideLabel}: 暂无{tableLabel}记录</Tag>;
  }

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>月度对比</Title>
        <div style={{ display: "flex", gap: 8 }}>
          <Button
            type="primary"
            icon={<PlayCircleOutlined />}
            onClick={() => void handleRunCompare()}
            loading={runningCompare}
          >
            开始对比
          </Button>
          <Button
            icon={<ExportOutlined />}
            onClick={() => void handleExport()}
            disabled={!compareData || exporting}
            loading={exporting}
          >
            导出修改结果
          </Button>
        </div>
      </div>

      {notice && (
        <Alert type={notice.type} message={notice.message} closable onClose={() => setNotice(null)} style={{ marginBottom: 16 }} />
      )}
      {pageError && (
        <Alert type="error" message="页面状态异常" description={pageError} style={{ marginBottom: 16 }} />
      )}

      {/* Source configuration */}
      <Card title="对比源配置" style={{ marginBottom: 16 }}>
        <Text type="secondary" style={{ display: "block", marginBottom: 12 }}>
          左侧和右侧都可以单独选择系统已有批次或本地上传 Excel。
        </Text>
        <Row gutter={[16, 16]}>
          <Col xs={24} md={12}>{renderSourcePanel("left")}</Col>
          <Col xs={24} md={12}>{renderSourcePanel("right")}</Col>
        </Row>
      </Card>

      {/* Table type selection */}
      <Card title="对比表格类型" style={{ marginBottom: 16 }}>
        <Row gutter={[16, 16]} align="middle">
          <Col>
            <Text type="secondary" style={{ marginRight: 8 }}>表格类型</Text>
            <Select
              value={compareTableType}
              onChange={(val) => setCompareTableType(val)}
              options={[
                { value: "salary", label: "Salary 表格" },
                { value: "final_tool", label: "Tool 表格" },
              ]}
              style={{ width: 160 }}
            />
          </Col>
          <Col>
            <div style={{ display: "flex", gap: 8 }}>
              {renderTableAvailability("left")}
              <SwapOutlined />
              {renderTableAvailability("right")}
            </div>
          </Col>
        </Row>
      </Card>

      {/* Progress */}
      {runningCompare && compareProgress && (
        <Card style={{ marginBottom: 16 }}>
          <Progress percent={compareProgress.percent} status="active" />
          <Steps
            size="small"
            current={compareProgress.currentStep - 1}
            style={{ marginTop: 12 }}
            items={compareProgress.steps.map((step) => ({
              title: step.label,
              description: compareProgress.completedKeys.includes(step.key) ? "已完成" : compareProgress.currentKey === step.key ? "进行中" : "等待中",
            }))}
          />
          <Text type="secondary" style={{ display: "block", marginTop: 8 }}>
            {compareProgress.message} 当前组合：左侧{sourceModeLabel(leftMode)}，右侧{sourceModeLabel(rightMode)}。
          </Text>
        </Card>
      )}

      {/* Toolbar */}
      <Card style={{ marginBottom: 16 }}>
        <Row gutter={[12, 12]} align="middle" wrap>
          <Col flex="auto">
            <Input.Search
              placeholder="姓名、工号、证件号、文件名、金额"
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              style={{ maxWidth: 400 }}
              allowClear
            />
          </Col>
          <Col>
            <Checkbox checked={onlyDifferences} onChange={(e) => setOnlyDifferences(e.target.checked)}>
              只看差异行
            </Checkbox>
          </Col>
          <Col>
            <Checkbox checked={showAllFields} onChange={(e) => setShowAllFields(e.target.checked)}>
              展开全部字段
            </Checkbox>
          </Col>
          <Col>
            <Select
              value={pageSize}
              onChange={(val) => setPageSize(val)}
              options={PAGE_SIZE_OPTIONS.map((o) => ({ value: o, label: `${o} 行/页` }))}
              style={{ width: 100 }}
            />
          </Col>
        </Row>

        {displayCompareData && (
          <Row gutter={[16, 16]} style={{ marginTop: 12 }}>
            <Col><Statistic title="总对比行数" value={displayCompareData.total_row_count} /></Col>
            <Col><Statistic title="存在差异" value={displayCompareData.changed_row_count} valueStyle={{ color: "#FF7D00" }} /></Col>
            <Col><Statistic title="仅左侧" value={displayCompareData.left_only_count} valueStyle={{ color: "#3370FF" }} /></Col>
            <Col><Statistic title="仅右侧" value={displayCompareData.right_only_count} valueStyle={{ color: "#FF7D00" }} /></Col>
            <Col><Statistic title="完全一致" value={displayCompareData.same_row_count} /></Col>
          </Row>
        )}
      </Card>

      {/* Results */}
      {!displayCompareData ? (
        <Card>
          <Empty description={'先给左右两侧分别选择线上批次或本地 Excel，然后点击"开始对比"。'} />
        </Card>
      ) : pagedRows.length === 0 ? (
        <Card>
          <Empty description="当前筛选条件下没有可展示的对比记录。" />
        </Card>
      ) : (
        <>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
            <Text type="secondary">第 {currentPage} / {totalPages} 页，共 {filteredRows.length} 行</Text>
            <div style={{ display: "flex", gap: 8 }}>
              <Button size="small" disabled={currentPage <= 1} onClick={() => setCurrentPage((v) => Math.max(1, v - 1))}>上一页</Button>
              <Button size="small" disabled={currentPage >= totalPages} onClick={() => setCurrentPage((v) => Math.min(totalPages, v + 1))}>下一页</Button>
            </div>
          </div>

          {pagedRows.map((row) => {
            const visFields = visibleFieldsForRow(displayCompareData, row, showAllFields);
            const rowName = pickRowValue(row, "person_name") || row.compare_key;
            const rowSubtitle = [
              pickRowValue(row, "employee_id") ? `工号 ${pickRowValue(row, "employee_id")}` : "",
              pickRowValue(row, "company_name"),
              pickRowValue(row, "billing_period"),
            ].filter(Boolean).join(" / ");

            return (
              <Card
                key={row.compare_key}
                size="small"
                title={
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <div>
                      <Text strong>{rowName}</Text>
                      {rowSubtitle && <Text type="secondary" style={{ marginLeft: 8, fontSize: 12 }}>{rowSubtitle}</Text>}
                    </div>
                    <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                      <Tag color={statusColor(row.diff_status)}>{statusLabel(row.diff_status)}</Tag>
                      <Text type="secondary" style={{ fontSize: 12 }}>{visFields.length} 个字段</Text>
                    </div>
                  </div>
                }
                style={{ marginBottom: 12 }}
              >
                <Tabs
                  size="small"
                  items={([
                    { side: "left" as const, label: `左侧 · ${displayCompareData.left_batch.batch_name}`, record: row.left },
                    { side: "right" as const, label: `右侧 · ${displayCompareData.right_batch.batch_name}`, record: row.right },
                  ]).map((panel) => ({
                    key: panel.side,
                    label: panel.label,
                    children: (
                      <div>
                        <div style={{ marginBottom: 8 }}>
                          <Text type="secondary" style={{ fontSize: 12 }}>
                            {panel.record.source_file_name ?? "无来源文件"} / 源行号 {panel.record.source_row_number ?? "-"}
                          </Text>
                        </div>
                        <Row gutter={[8, 8]}>
                          {visFields.map((field) => {
                            const isDiff = row.different_fields.includes(field);
                            return (
                              <Col xs={24} sm={12} md={8} lg={6} key={`${row.compare_key}-${panel.side}-${field}`}>
                                <div style={{ border: isDiff ? "1px solid #FF7D00" : "1px solid #f0f0f0", borderRadius: 4, padding: "4px 8px" }}>
                                  <Text type="secondary" style={{ fontSize: 12, display: "block" }}>{fieldLabel(field)}</Text>
                                  <Input
                                    size="small"
                                    value={displayValue(panel.record.values[field] ?? null)}
                                    onChange={(e) => handleCellChange(row.compare_key, panel.side, field, e.target.value)}
                                    style={{ border: "none", padding: 0, background: "transparent" }}
                                  />
                                </div>
                              </Col>
                            );
                          })}
                        </Row>
                      </div>
                    ),
                  }))}
                />
              </Card>
            );
          })}
        </>
      )}
    </div>
  );
}
