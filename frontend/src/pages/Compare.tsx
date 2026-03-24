import { useEffect, useMemo, useRef, useState, type ChangeEvent } from "react";

import { PageContainer, SectionState, SurfaceNotice } from "../components";
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
    "person_name",
    "employee_id",
    "medical_personal",
    "unemployment_personal",
    "large_medical_personal",
    "pension_personal",
    "housing_fund_personal",
    "pension_company",
    "medical_maternity_company",
    "unemployment_company",
    "injury_company",
    "maternity_amount",
    "supplementary_medical_company",
    "housing_fund_company",
    "personal_total_amount",
    "housing_fund_total",
    "company_total_amount",
    "total_amount",
  ],
  final_tool: [
    "company_name",
    "region",
    "person_name",
    "id_number",
    "employee_id",
    "medical_personal",
    "unemployment_personal",
    "large_medical_personal",
    "pension_personal",
    "housing_fund_personal",
    "pension_company",
    "medical_maternity_company",
    "unemployment_company",
    "injury_company",
    "maternity_amount",
    "supplementary_medical_company",
    "housing_fund_company",
    "personal_total_amount",
    "company_total_amount",
    "housing_fund_total",
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

function compareTableLabel(type: CompareTableType): string {
  return type === "salary" ? "薪酬表格" : "Tool 表格";
}

function statusLabel(status: string): string {
  switch (status) {
    case "same":
      return "一致";
    case "changed":
      return "有差异";
    case "left_only":
      return "仅左侧";
    case "right_only":
      return "仅右侧";
    default:
      return status;
  }
}

function statusClassName(status: string): string {
  return `compare-status compare-status--${status}`;
}

function normalizeCellValue(value: CompareCellValue): string | null {
  if (value === null || value === undefined) {
    return null;
  }
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

function describeRow(row: BatchCompareResult["rows"][number]): { title: string; subtitle: string } {
  const title = pickRowValue(row, "person_name") || row.compare_key;
  const subtitle = [
    pickRowValue(row, "employee_id") ? `工号 ${pickRowValue(row, "employee_id")}` : "",
    pickRowValue(row, "company_name"),
    pickRowValue(row, "billing_period"),
  ]
    .filter(Boolean)
    .join(" · ");

  return {
    title,
    subtitle,
  };
}

function visibleFieldsForRow(data: BatchCompareResult, row: BatchCompareResult["rows"][number], showAllFields: boolean): string[] {
  if (showAllFields) {
    return data.fields;
  }

  if (row.diff_status === "changed" && row.different_fields.length > 0) {
    return row.different_fields;
  }

  const previewFields = [
    "person_name",
    "employee_id",
    "id_number",
    "company_name",
    "region",
    "billing_period",
    "total_amount",
    "company_total_amount",
    "personal_total_amount",
  ];

  const nonEmptyPreviewFields = previewFields.filter(
    (field) => hasValue(row.left.values[field] ?? null) || hasValue(row.right.values[field] ?? null),
  );

  return nonEmptyPreviewFields.length > 0
    ? nonEmptyPreviewFields
    : data.fields.filter((field) => hasValue(row.left.values[field] ?? null) || hasValue(row.right.values[field] ?? null)).slice(0, 8);
}

function buildCompareSteps(leftMode: SourceMode, rightMode: SourceMode): CompareProgressStep[] {
  const steps: CompareProgressStep[] = [
    {
      key: "validate",
      label: "检查数据源",
      message: "确认左右两侧的来源配置完整，可以开始发起对比。",
    },
  ];

  if (leftMode === "local") {
    steps.push(
      {
        key: "left-upload",
        label: "上传左侧本地文件",
        message: "正在为左侧本地 Excel 创建临时批次。",
      },
      {
        key: "left-parse",
        label: "解析左侧本地文件",
        message: "正在解析左侧 Excel 并转换为可对比数据。",
      },
    );
  }

  if (rightMode === "local") {
    steps.push(
      {
        key: "right-upload",
        label: "上传右侧本地文件",
        message: "正在为右侧本地 Excel 创建临时批次。",
      },
      {
        key: "right-parse",
        label: "解析右侧本地文件",
        message: "正在解析右侧 Excel 并转换为可对比数据。",
      },
    );
  }

  steps.push(
    {
      key: "compare",
      label: "拉取对比结果",
      message: "正在计算左右两侧的差异结果。",
    },
    {
      key: "sync",
      label: "同步页面数据",
      message: "正在把最新结果同步到页面。",
    },
  );

  return steps;
}

function buildCompareProgressState(steps: CompareProgressStep[], completedKeys: string[], currentKey: string | null): CompareProgressState {
  const totalSteps = steps.length;
  const activeIndex = currentKey ? Math.max(0, steps.findIndex((step) => step.key === currentKey)) : totalSteps - 1;
  const activeStep = currentKey ? steps[activeIndex] : null;
  const percent = currentKey
    ? Math.max(8, Math.min(98, Math.round(((completedKeys.length + 0.45) / totalSteps) * 100)))
    : 100;

  return {
    steps,
    completedKeys,
    currentKey,
    currentStep: currentKey ? activeIndex + 1 : totalSteps,
    totalSteps,
    label: activeStep?.label ?? "对比完成",
    message: activeStep?.message ?? "对比结果已完成同步。",
    percent,
  };
}

function getCompareProgressStepState(stepKey: string, progress: CompareProgressState): "done" | "active" | "pending" {
  if (progress.completedKeys.includes(stepKey)) {
    return "done";
  }
  if (progress.currentKey === stepKey) {
    return "active";
  }
  return "pending";
}

function filterCompareDataByTable(data: BatchCompareResult, tableType: CompareTableType): BatchCompareResult {
  const preferredFields = COMPARE_TABLE_FIELDS[tableType];
  const fields = data.fields.filter((field) => preferredFields.includes(field));
  const effectiveFields = fields.length > 0 ? fields : data.fields;

  const rows = data.rows.map((row) => {
    const differentFields = row.different_fields.filter((field) => effectiveFields.includes(field));
    const leftExists = effectiveFields.some((field) => hasValue(row.left.values[field] ?? null)) || Boolean(row.left.source_file_name);
    const rightExists = effectiveFields.some((field) => hasValue(row.right.values[field] ?? null)) || Boolean(row.right.source_file_name);

    let diffStatus = "same";
    if (!leftExists && rightExists) {
      diffStatus = "right_only";
    } else if (leftExists && !rightExists) {
      diffStatus = "left_only";
    } else if (differentFields.length > 0) {
      diffStatus = "changed";
    }

    return {
      ...row,
      diff_status: diffStatus,
      different_fields: differentFields,
    };
  });

  return {
    ...data,
    fields: effectiveFields,
    rows,
    total_row_count: rows.length,
    same_row_count: rows.filter((row) => row.diff_status === "same").length,
    changed_row_count: rows.filter((row) => row.diff_status === "changed").length,
    left_only_count: rows.filter((row) => row.diff_status === "left_only").length,
    right_only_count: rows.filter((row) => row.diff_status === "right_only").length,
  };
}

function isArtifactReady(exportSnapshot: BatchExport | null, tableType: CompareTableType): boolean {
  return Boolean(exportSnapshot?.artifacts.some((artifact) => artifact.template_type === tableType && artifact.status === "completed"));
}

function cloneRowWithFieldUpdate(
  data: BatchCompareResult,
  compareKey: string,
  side: Side,
  field: string,
  nextValue: string,
): BatchCompareResult {
  const rows = data.rows.map((row) => {
    if (row.compare_key !== compareKey) {
      return row;
    }

    const nextSide = {
      ...row[side],
      values: {
        ...row[side].values,
        [field]: nextValue.trim().length > 0 ? nextValue : null,
      },
    };

    const left = side === "left" ? nextSide : row.left;
    const right = side === "right" ? nextSide : row.right;
    const differentFields = data.fields.filter(
      (currentField) => normalizeCellValue(left.values[currentField] ?? null) !== normalizeCellValue(right.values[currentField] ?? null),
    );

    let diffStatus = "same";
    const leftExists = Object.values(left.values).some((value) => normalizeCellValue(value) !== null) || !!left.source_file_name;
    const rightExists = Object.values(right.values).some((value) => normalizeCellValue(value) !== null) || !!right.source_file_name;

    if (!leftExists && rightExists) {
      diffStatus = "right_only";
    } else if (leftExists && !rightExists) {
      diffStatus = "left_only";
    } else if (differentFields.length > 0) {
      diffStatus = "changed";
    }

    return {
      ...row,
      left,
      right,
      diff_status: diffStatus,
      different_fields: diffStatus === "same" ? [] : differentFields,
    };
  });

  return {
    ...data,
    rows,
    total_row_count: rows.length,
    same_row_count: rows.filter((row) => row.diff_status === "same").length,
    changed_row_count: rows.filter((row) => row.diff_status === "changed").length,
    left_only_count: rows.filter((row) => row.diff_status === "left_only").length,
    right_only_count: rows.filter((row) => row.diff_status === "right_only").length,
  };
}

function fileKey(file: File): string {
  return `${file.name}_${file.size}_${file.lastModified}`;
}

function formatFileSize(size: number): string {
  if (size >= 1024 * 1024) {
    return `${(size / (1024 * 1024)).toFixed(2)} MB`;
  }
  if (size >= 1024) {
    return `${(size / 1024).toFixed(1)} KB`;
  }
  return `${size} B`;
}

function mapFilesToEntries(files: File[]): UploadEntry[] {
  return files.map((file) => ({
    id: fileKey(file),
    name: file.name,
    meta: formatFileSize(file.size),
  }));
}

function mergeFiles(existing: File[], incoming: File[]): File[] {
  const known = new Set(existing.map((file) => fileKey(file)));
  const next = [...existing];
  for (const file of incoming) {
    const key = fileKey(file);
    if (!known.has(key)) {
      known.add(key);
      next.push(file);
    }
  }
  return next;
}

function buildTempBatchName(side: Side): string {
  const now = new Date();
  const pad = (value: number) => String(value).padStart(2, "0");
  const stamp = `${now.getFullYear()}${pad(now.getMonth() + 1)}${pad(now.getDate())}-${pad(now.getHours())}${pad(now.getMinutes())}${pad(now.getSeconds())}`;
  return `${side === "left" ? "左侧" : "右侧"}本地对比-${stamp}`;
}

function triggerBlobDownload(blob: Blob, fileName: string): void {
  const url = window.URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = fileName;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
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
  const [panelNotice, setPanelNotice] = useState<{ tone: "success" | "info"; message: string } | null>(null);
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
        if (!active) {
          return;
        }
        setBatches(result);
        if (result.length >= 2) {
          setLeftBatchId((current) => current || result[0].id);
          setRightBatchId((current) => current || result[1].id);
        } else if (result[0]) {
          setLeftBatchId((current) => current || result[0].id);
        }
      } catch (error) {
        if (active) {
          setPageError(normalizeApiError(error).message);
        }
      } finally {
        if (active) {
          setLoadingBatches(false);
        }
      }
    }

    void loadBatches();
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    let active = true;

    async function loadExportSnapshot(side: Side, batchId: string) {
      try {
        const snapshot = await fetchBatchExport(batchId);
        if (!active) {
          return;
        }
        if (side === "left") {
          setLeftExportSnapshot(snapshot);
        } else {
          setRightExportSnapshot(snapshot);
        }
      } catch {
        if (!active) {
          return;
        }
        if (side === "left") {
          setLeftExportSnapshot(null);
        } else {
          setRightExportSnapshot(null);
        }
      }
    }

    if (leftMode === "existing" && leftBatchId) {
      void loadExportSnapshot("left", leftBatchId);
    } else {
      setLeftExportSnapshot(null);
    }

    if (rightMode === "existing" && rightBatchId) {
      void loadExportSnapshot("right", rightBatchId);
    } else {
      setRightExportSnapshot(null);
    }

    return () => {
      active = false;
    };
  }, [leftBatchId, leftMode, rightBatchId, rightMode]);

  const displayCompareData = useMemo(
    () => (compareData ? filterCompareDataByTable(compareData, compareTableType) : null),
    [compareData, compareTableType],
  );

  const filteredRows = useMemo(() => {
    if (!displayCompareData) {
      return [];
    }

    const keyword = searchText.trim().toLowerCase();
    return displayCompareData.rows.filter((row) => {
      if (onlyDifferences && row.diff_status === "same") {
        return false;
      }
      if (!keyword) {
        return true;
      }

      const values = [
        row.compare_key,
        row.left.source_file_name ?? "",
        row.right.source_file_name ?? "",
        ...Object.values(row.left.values).map((value) => (value === null ? "" : String(value))),
        ...Object.values(row.right.values).map((value) => (value === null ? "" : String(value))),
      ];
      return values.some((value) => value.toLowerCase().includes(keyword));
    });
  }, [displayCompareData, onlyDifferences, searchText]);

  const totalPages = Math.max(1, Math.ceil(filteredRows.length / pageSize));

  useEffect(() => {
    setCurrentPage(1);
  }, [searchText, onlyDifferences, pageSize, compareTableType, displayCompareData?.left_batch.id, displayCompareData?.right_batch.id]);

  useEffect(() => {
    if (currentPage > totalPages) {
      setCurrentPage(totalPages);
    }
  }, [currentPage, totalPages]);

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
    if (side === "left") {
      setLeftLocalFiles((current) => mergeFiles(current, selected));
    } else {
      setRightLocalFiles((current) => mergeFiles(current, selected));
    }
  }

  function removeLocalFile(side: Side, entryId: string) {
    if (side === "left") {
      setLeftLocalFiles((current) => current.filter((file) => fileKey(file) !== entryId));
    } else {
      setRightLocalFiles((current) => current.filter((file) => fileKey(file) !== entryId));
    }
  }

  async function resolveSideBatchId(
    side: Side,
    progressHandlers?: {
      activateStep: (key: string) => void;
      completeStep: (key: string) => void;
    },
  ): Promise<string> {
    const mode = side === "left" ? leftMode : rightMode;
    const batchId = side === "left" ? leftBatchId : rightBatchId;
    const localFiles = side === "left" ? leftLocalFiles : rightLocalFiles;

    if (mode === "existing") {
      if (!batchId) {
        throw new ApiClientError(`${side === "left" ? "左侧" : "右侧"}还没有选择线上批次。`);
      }
      return batchId;
    }

    if (!localFiles.length) {
      throw new ApiClientError(`${side === "left" ? "左侧" : "右侧"}还没有上传本地文件。`);
    }

    const uploadKey = `${side}-upload`;
    const parseKey = `${side}-parse`;

    progressHandlers?.activateStep(uploadKey);
    const batch = await createImportBatch({
      files: localFiles,
      batchName: buildTempBatchName(side),
    });
    progressHandlers?.completeStep(uploadKey);

    progressHandlers?.activateStep(parseKey);
    await parseImportBatch(batch.id);
    progressHandlers?.completeStep(parseKey);
    if (side === "left") {
      setLeftBatchId(batch.id);
    } else {
      setRightBatchId(batch.id);
    }
    return batch.id;
  }

  async function handleRunCompare() {
    setRunningCompare(true);
    setPageError(null);
    setPanelNotice(null);
    setCompareProgress(null);

    try {
      const steps = buildCompareSteps(leftMode, rightMode);
      let completedKeys: string[] = [];

      const refreshProgress = (currentKey: string | null) => {
        setCompareProgress(buildCompareProgressState(steps, completedKeys, currentKey));
      };

      const activateStep = (key: string) => {
        refreshProgress(key);
      };

      const completeStep = (key: string) => {
        if (!completedKeys.includes(key)) {
          completedKeys = [...completedKeys, key];
        }
        const nextStep = steps.find((step) => !completedKeys.includes(step.key));
        refreshProgress(nextStep?.key ?? null);
      };

      activateStep("validate");

      if (leftMode === "existing" && !leftBatchId) {
        throw new ApiClientError("左侧还没有选择线上批次。");
      }
      if (rightMode === "existing" && !rightBatchId) {
        throw new ApiClientError("右侧还没有选择线上批次。");
      }
      if (leftMode === "local" && !leftLocalFiles.length) {
        throw new ApiClientError("左侧还没有上传本地文件。");
      }
      if (rightMode === "local" && !rightLocalFiles.length) {
        throw new ApiClientError("右侧还没有上传本地文件。");
      }

      completeStep("validate");

      const resolvedLeftBatchId = await resolveSideBatchId("left", { activateStep, completeStep });
      const resolvedRightBatchId = await resolveSideBatchId("right", { activateStep, completeStep });

      if (resolvedLeftBatchId === resolvedRightBatchId) {
        throw new ApiClientError("左侧和右侧不能使用同一个批次，请重新选择。");
      }

      activateStep("compare");
      const result = await fetchBatchCompare(resolvedLeftBatchId, resolvedRightBatchId);
      completeStep("compare");

      activateStep("sync");
      const batchList = await fetchImportBatches().catch(() => null);
      if (batchList) {
        setBatches(batchList);
      }
      setCompareData(result);
      setCurrentPage(1);
      completeStep("sync");
      setPanelNotice({
        tone: "success",
        message: "对比结果已刷新。现在支持左边本地、右边线上，或反过来混合对比。",
      });
    } catch (error) {
      const normalized = error instanceof ApiClientError ? error : normalizeApiError(error);
      setPageError(normalized.message);
    } finally {
      setRunningCompare(false);
    }
  }

  async function handleExport() {
    if (!compareData) {
      return;
    }

    setExporting(true);
    setPageError(null);
    setPanelNotice(null);
    try {
      const payload: CompareExportPayload = {
        left_batch_name: compareData.left_batch.batch_name,
        right_batch_name: compareData.right_batch.batch_name,
        fields: compareData.fields,
        rows: compareData.rows,
      };
      const { blob, fileName } = await exportBatchCompare(payload);
      triggerBlobDownload(blob, fileName);
      setPanelNotice({ tone: "success", message: "已导出当前修改后的对比结果。" });
    } catch (error) {
      const normalized = error instanceof ApiClientError ? error : normalizeApiError(error);
      setPageError(normalized.message);
    } finally {
      setExporting(false);
    }
  }

  function handleCellChange(compareKey: string, side: Side, field: string, nextValue: string) {
    setCompareData((current) => {
      if (!current) {
        return current;
      }
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
      <section className="compare-source-panel">
        <div className="section-heading">
          <div>
            <span className="panel-label">{title}</span>
            <h2>{subtitle}</h2>
          </div>
        </div>

        <label className="form-field">
          <span>来源方式</span>
          <select
            value={mode}
            onChange={(event) => {
              const nextMode = event.target.value as SourceMode;
              if (side === "left") {
                setLeftMode(nextMode);
              } else {
                setRightMode(nextMode);
              }
            }}
          >
            <option value="existing">使用线上批次</option>
            <option value="local">使用本地 Excel</option>
          </select>
        </label>

        {mode === "existing" ? (
          <label className="form-field">
            <span>选择批次</span>
            <select value={batchId} onChange={(event) => (side === "left" ? setLeftBatchId(event.target.value) : setRightBatchId(event.target.value))} disabled={loadingBatches}>
              <option value="">请选择批次</option>
              {batches.map((batch) => (
                <option key={`${side}-${batch.id}`} value={batch.id}>
                  {batchLabel(batch)}
                </option>
              ))}
            </select>
          </label>
        ) : (
          <>
            <input
              ref={inputRef}
              type="file"
              accept=".xlsx,.xls"
              multiple
              hidden
              onChange={(event) => handleFileSelection(side, event)}
            />
            <div className="button-row">
              <button type="button" className="button button--primary" onClick={() => inputRef.current?.click()}>
                选择本地文件
              </button>
              <button
                type="button"
                className="button button--ghost"
                disabled={!localEntries.length}
                onClick={() => (side === "left" ? setLeftLocalFiles([]) : setRightLocalFiles([]))}
              >
                清空
              </button>
            </div>
            {localEntries.length ? (
              <div className="upload-file-list">
                {localEntries.map((entry) => (
                  <div key={entry.id} className="upload-file-chip">
                    <div className="upload-file-chip__meta">
                      <strong>{entry.name}</strong>
                      <span>{entry.meta}</span>
                    </div>
                    <button type="button" className="button button--ghost upload-file-chip__remove" onClick={() => removeLocalFile(side, entry.id)}>
                      删除
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <div className="upload-panel__empty">上传 Excel 后，这一侧会按本地文件生成临时批次参与对比。</div>
            )}
          </>
        )}
      </section>
    );
  }

  function renderTableAvailability(side: Side) {
    const mode = side === "left" ? leftMode : rightMode;
    const batchId = side === "left" ? leftBatchId : rightBatchId;
    const exportSnapshot = side === "left" ? leftExportSnapshot : rightExportSnapshot;
    const title = side === "left" ? "左侧任务" : "右侧任务";

    if (mode === "local") {
      return (
        <article className="compare-table-status compare-table-status--info">
          <strong>{title}</strong>
          <span>{`本地文件会在解析后按“${compareTableLabel(compareTableType)}”视图参与对比。`}</span>
        </article>
      );
    }

    if (!batchId) {
      return (
        <article className="compare-table-status">
          <strong>{title}</strong>
          <span>还没有选择云端任务。</span>
        </article>
      );
    }

    if (!exportSnapshot) {
      return (
        <article className="compare-table-status">
          <strong>{title}</strong>
          <span>正在读取该云端任务的历史导出记录。</span>
        </article>
      );
    }

    if (isArtifactReady(exportSnapshot, compareTableType)) {
      return (
        <article className="compare-table-status compare-table-status--ready">
          <strong>{title}</strong>
          <span>{`该云端任务已有可用的${compareTableLabel(compareTableType)}。`}</span>
        </article>
      );
    }

    return (
      <article className="compare-table-status compare-table-status--warn">
        <strong>{title}</strong>
        <span>{`该云端任务暂未找到${compareTableLabel(compareTableType)}导出记录。`}</span>
      </article>
    );
  }

  return (
    <PageContainer
      eyebrow="Compare"
      title="月度数据对比"
      description="数据源配置已经合并为一套对比工具，左侧和右侧都能独立选择系统内批次或本地 Excel，支持云端对本地、双云端、双本地三种组合。"
      actions={
        <div className="button-row">
          <button type="button" className="button button--primary" onClick={() => void handleRunCompare()} disabled={runningCompare}>
            {runningCompare ? "对比中..." : "开始对比"}
          </button>
          <button type="button" className="button button--ghost" onClick={() => void handleExport()} disabled={!compareData || exporting}>
            {exporting ? "导出中..." : "导出修改结果"}
          </button>
        </div>
      }
    >
      {panelNotice ? <SurfaceNotice tone={panelNotice.tone} message={panelNotice.message} /> : null}
      {pageError ? <SurfaceNotice tone="error" title="页面状态异常" message={pageError} /> : null}

      <section className="panel-card compare-config-card">
        <div className="section-heading">
          <div>
            <span className="panel-label">对比源配置</span>
            <h2>一个入口，自由组合左右数据来源</h2>
          </div>
          <p className="compare-config-card__hint">左侧和右侧都可以单独选择“系统已有批次”或“本地上传 Excel”，不再区分两套对比入口。</p>
        </div>

        <div className="compare-source-grid">
          {renderSourcePanel("left")}
          {renderSourcePanel("right")}
        </div>
      </section>

      <section className="panel-card compare-table-card">
        <div className="section-heading">
          <div>
            <span className="panel-label">对比表格</span>
            <h2>单独选择这次要对比的表格视图</h2>
          </div>
          <p className="compare-config-card__hint">这里单独控制 `salary` 还是 `tool` 视图，不再放进“使用线上批次”里面。云端任务只负责选任务，表格类型在这里统一决定。</p>
        </div>

        <div className="compare-table-grid">
          <label className="form-field">
            <span>表格类型</span>
            <select value={compareTableType} onChange={(event) => setCompareTableType(event.target.value as CompareTableType)}>
              <option value="salary">Salary 表格</option>
              <option value="final_tool">Tool 表格</option>
            </select>
          </label>
          {renderTableAvailability("left")}
          {renderTableAvailability("right")}
        </div>
      </section>

      {runningCompare && compareProgress ? (
        <section className="panel-card progress-card progress-card--active compare-progress-card">
          <div className="progress-card__summary">
            <div className="loading-pill" aria-hidden="true">
              <span className="loading-pill__core" />
            </div>
            <div>
              <strong>{compareProgress.percent}%</strong>
              <span>{`${compareProgress.label} · ${compareProgress.currentStep}/${compareProgress.totalSteps}`}</span>
              <p>{`${compareProgress.message} 当前组合：左侧${sourceModeLabel(leftMode)}，右侧${sourceModeLabel(rightMode)}。`}</p>
            </div>
          </div>
          <div className="progress-bar progress-bar--active" aria-hidden="true">
            <div className="progress-bar__track">
              <div className="progress-bar__fill" style={{ width: `${compareProgress.percent}%` }} />
            </div>
          </div>
          <div className="progress-step-list">
            {compareProgress.steps.map((step) => {
              const stepState = getCompareProgressStepState(step.key, compareProgress);
              return (
                <div key={step.key} className={`progress-step progress-step--${stepState}`}>
                  <strong>{step.label}</strong>
                  <span>{stepState === "done" ? "已完成" : stepState === "active" ? "进行中" : "等待中"}</span>
                </div>
              );
            })}
          </div>
        </section>
      ) : null}

      <section className="panel-card compare-toolbar-card">
        <div className="compare-toolbar">
          <label className="form-field compare-toolbar__search">
            <span>搜索</span>
            <input value={searchText} onChange={(event) => setSearchText(event.target.value)} placeholder="姓名、工号、证件号、文件名、金额" />
          </label>
          <label className="compare-toggle">
            <input type="checkbox" checked={onlyDifferences} onChange={(event) => setOnlyDifferences(event.target.checked)} />
            <span>只看差异行</span>
          </label>
          <label className="compare-toggle">
            <input type="checkbox" checked={showAllFields} onChange={(event) => setShowAllFields(event.target.checked)} />
            <span>展开全部字段</span>
          </label>
          <label className="form-field compare-toolbar__size">
            <span>每页显示</span>
            <select value={pageSize} onChange={(event) => setPageSize(Number(event.target.value))}>
              {PAGE_SIZE_OPTIONS.map((option) => (
                <option key={option} value={option}>
                  {option} 行
                </option>
              ))}
            </select>
          </label>
        </div>

        {displayCompareData ? (
          <div className="compare-summary-grid">
            <article className="status-item">
              <strong>{displayCompareData.total_row_count}</strong>
              <div>总对比行数</div>
            </article>
            <article className="status-item compare-summary-item compare-summary-item--changed">
              <strong>{displayCompareData.changed_row_count}</strong>
              <div>存在差异</div>
            </article>
            <article className="status-item compare-summary-item compare-summary-item--left">
              <strong>{displayCompareData.left_only_count}</strong>
              <div>仅左侧存在</div>
            </article>
            <article className="status-item compare-summary-item compare-summary-item--right">
              <strong>{displayCompareData.right_only_count}</strong>
              <div>仅右侧存在</div>
            </article>
            <article className="status-item">
              <strong>{displayCompareData.same_row_count}</strong>
              <div>完全一致</div>
            </article>
          </div>
        ) : null}
      </section>

      {!displayCompareData ? (
        <SectionState title="等待开始对比" message="先给左右两侧分别选择线上批次或本地 Excel，然后点击“开始对比”。" />
      ) : (
        <>
          <section className="panel-card compare-pagination-bar">
            <div className="compare-pagination">
              <button type="button" className="button button--ghost" onClick={() => setCurrentPage((value) => Math.max(1, value - 1))} disabled={currentPage <= 1}>
                上一页
              </button>
              <span>{`第 ${currentPage} / ${totalPages} 页，共 ${filteredRows.length} 行`}</span>
              <button type="button" className="button button--ghost" onClick={() => setCurrentPage((value) => Math.min(totalPages, value + 1))} disabled={currentPage >= totalPages}>
                下一页
              </button>
            </div>
          </section>

          {pagedRows.length === 0 ? (
            <SectionState title="没有匹配结果" message="当前筛选条件下没有可展示的对比记录，请调整搜索词或筛选条件。" />
          ) : (
            <div className="compare-row-list">
              {pagedRows.map((row) => {
              const visibleFields = visibleFieldsForRow(displayCompareData, row, showAllFields);
              const rowInfo = describeRow(row);
              const leftHasContent =
                visibleFields.some((field) => hasValue(row.left.values[field] ?? null)) || Boolean(row.left.source_file_name || row.left.source_row_number);
              const rightHasContent =
                visibleFields.some((field) => hasValue(row.right.values[field] ?? null)) || Boolean(row.right.source_file_name || row.right.source_row_number);

              return (
                <article
                  key={row.compare_key}
                  className={row.diff_status === "same" ? "compare-pair-card" : `compare-pair-card compare-pair-card--${row.diff_status}`}
                >
                  <header className="compare-pair-card__header">
                    <div>
                      <span className="panel-label">对比键</span>
                      <h2>{rowInfo.title}</h2>
                      <p>{rowInfo.subtitle || row.compare_key}</p>
                    </div>
                    <div className="compare-row-meta">
                      <span className={statusClassName(row.diff_status)}>{statusLabel(row.diff_status)}</span>
                      <span>{row.compare_key}</span>
                      <span>{`显示 ${visibleFields.length} 个字段`}</span>
                    </div>
                  </header>

                  <div className="compare-split">
                    {([
                      { side: "left" as const, title: "左侧", batchName: displayCompareData.left_batch.batch_name, record: row.left, hasContent: leftHasContent },
                      { side: "right" as const, title: "右侧", batchName: displayCompareData.right_batch.batch_name, record: row.right, hasContent: rightHasContent },
                    ]).map((panel) => (
                      <section key={`${row.compare_key}-${panel.side}`} className="compare-side">
                        <div className="compare-side__header">
                          <div>
                            <strong>{`${panel.title} · ${panel.batchName}`}</strong>
                            <div className="compare-side__meta">
                              <span>{panel.record.source_file_name ?? "无来源文件"}</span>
                              <span>{panel.record.source_row_number ? `源行号 ${panel.record.source_row_number}` : "源行号 -"} </span>
                            </div>
                          </div>
                          <span>{panel.side === "left" ? "原始值" : "对照值"}</span>
                        </div>

                        {!panel.hasContent ? <div className="compare-side__empty">当前侧暂无内容，可以直接补录需要的字段。</div> : null}

                        <div className="compare-field-grid">
                          {visibleFields.map((field) => (
                            <label
                              key={`${row.compare_key}-${panel.side}-${field}`}
                              className={row.different_fields.includes(field) ? "compare-field compare-field--changed" : "compare-field"}
                            >
                              <span>{fieldLabel(field)}</span>
                              <input
                                value={displayValue(panel.record.values[field] ?? null)}
                                onChange={(event) => handleCellChange(row.compare_key, panel.side, field, event.target.value)}
                              />
                            </label>
                          ))}
                        </div>
                      </section>
                    ))}
                  </div>
                </article>
              );
            })}
            </div>
          )}
        </>
      )}
    </PageContainer>
  );
}
