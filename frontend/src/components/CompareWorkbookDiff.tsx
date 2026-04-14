import { Empty, Input, Tag, Typography } from "antd";
import { useMemo, useRef, type CSSProperties, type MutableRefObject, type UIEvent } from "react";

import { useResponsiveViewport } from "../hooks/useResponsiveViewport";
import type { CompareCellValue, CompareRow } from "../services/compare";
import { useSemanticColors } from "../theme/useSemanticColors";

const { Text } = Typography;

type CompareSide = "left" | "right";

const DEFAULT_IDENTITY_FIELDS = ["person_name", "employee_id", "id_number"] as const;
const STATUS_COLUMN_WIDTH = 92;
const IDENTITY_COLUMN_WIDTH = 124;
const DATA_COLUMN_WIDTH = 136;
const PANEL_MAX_HEIGHT = 560;

const STATUS_META: Record<string, { label: string; color: string }> = {
  same: { label: "一致", color: "default" },
  changed: { label: "有差异", color: "warning" },
  left_only: { label: "仅左侧", color: "error" },
  right_only: { label: "仅右侧", color: "blue" },
};

export interface CompareWorkbookDiffProps {
  fields: string[];
  rows: CompareRow[];
  leftLabel: string;
  rightLabel: string;
  loading?: boolean;
  editable?: boolean;
  emptyDescription?: string;
  identityFields?: string[];
  onCellChange?: (compareKey: string, side: CompareSide, field: string, nextValue: string) => void;
  fieldLabel?: (field: string) => string;
}

interface DisplayColumn {
  field: string;
  label: string;
  width: number;
  stickyLeft?: number;
}

export function CompareWorkbookDiff({
  fields,
  rows,
  leftLabel,
  rightLabel,
  editable = false,
  emptyDescription = "当前没有可展示的对比结果。",
  identityFields,
  onCellChange,
  fieldLabel,
}: CompareWorkbookDiffProps) {
  const colors = useSemanticColors();
  const { isMobile, isTablet } = useResponsiveViewport();
  const isCompact = isMobile || isTablet;
  const leftPanelRef = useRef<HTMLDivElement | null>(null);
  const rightPanelRef = useRef<HTMLDivElement | null>(null);
  const syncingSideRef = useRef<CompareSide | null>(null);

  const resolvedIdentityFields = useMemo(
    () => (identityFields?.length ? identityFields : [...DEFAULT_IDENTITY_FIELDS]),
    [identityFields],
  );

  const columns = useMemo<DisplayColumn[]>(() => {
    const existingIdentityFields = resolvedIdentityFields.filter((field) => fields.includes(field));
    const remainingFields = fields.filter((field) => !existingIdentityFields.includes(field));

    const displayColumns: DisplayColumn[] = [
      {
        field: "__status__",
        label: "状态",
        width: STATUS_COLUMN_WIDTH,
        stickyLeft: 0,
      },
    ];

    let stickyOffset = STATUS_COLUMN_WIDTH;
    for (const field of existingIdentityFields) {
      displayColumns.push({
        field,
        label: fieldLabel?.(field) ?? field,
        width: IDENTITY_COLUMN_WIDTH,
        stickyLeft: stickyOffset,
      });
      stickyOffset += IDENTITY_COLUMN_WIDTH;
    }

    for (const field of remainingFields) {
      displayColumns.push({
        field,
        label: fieldLabel?.(field) ?? field,
        width: DATA_COLUMN_WIDTH,
      });
    }

    return displayColumns;
  }, [fieldLabel, fields, resolvedIdentityFields]);

  const totalWidth = useMemo(
    () => columns.reduce((sum, column) => sum + column.width, 0),
    [columns],
  );

  const handlePanelScroll = (side: CompareSide) => (event: UIEvent<HTMLDivElement>) => {
    if (syncingSideRef.current && syncingSideRef.current !== side) {
      return;
    }
    const source = event.currentTarget;
    const target = side === "left" ? rightPanelRef.current : leftPanelRef.current;
    if (!target) {
      return;
    }
    syncingSideRef.current = side;
    syncScrollPosition(target, source.scrollTop, source.scrollLeft);
    requestAnimationFrame(() => {
      if (syncingSideRef.current === side) {
        syncingSideRef.current = null;
      }
    });
  };

  if (!rows.length) {
    return <Empty description={emptyDescription} />;
  }

  return (
    <div
      data-testid="compare-workbook-diff"
      style={{
        display: "flex",
        gap: 16,
        flexDirection: isCompact ? "column" : "row",
        alignItems: "stretch",
      }}
    >
      {renderPanel({
        side: "left",
        label: leftLabel,
        rows,
        columns,
        totalWidth,
        colors,
        editable,
        onCellChange,
        panelRef: leftPanelRef,
        onScroll: handlePanelScroll("left"),
      })}
      {renderPanel({
        side: "right",
        label: rightLabel,
        rows,
        columns,
        totalWidth,
        colors,
        editable,
        onCellChange,
        panelRef: rightPanelRef,
        onScroll: handlePanelScroll("right"),
      })}
    </div>
  );
}

interface RenderPanelArgs {
  side: CompareSide;
  label: string;
  rows: CompareRow[];
  columns: DisplayColumn[];
  totalWidth: number;
  colors: ReturnType<typeof useSemanticColors>;
  editable: boolean;
  onCellChange?: CompareWorkbookDiffProps["onCellChange"];
  panelRef: MutableRefObject<HTMLDivElement | null>;
  onScroll: (event: UIEvent<HTMLDivElement>) => void;
}

function renderPanel({
  side,
  label,
  rows,
  columns,
  totalWidth,
  colors,
  editable,
  onCellChange,
  panelRef,
  onScroll,
}: RenderPanelArgs) {
  return (
    <section
      style={{
        flex: 1,
        minWidth: 0,
        border: `1px solid ${colors.BORDER}`,
        borderRadius: 16,
        overflow: "hidden",
        background: colors.BG_CONTAINER,
      }}
    >
      <div
        style={{
          padding: "12px 14px",
          borderBottom: `1px solid ${colors.BORDER}`,
          background: colors.BG_LAYOUT,
        }}
      >
        <Text strong>{label}</Text>
        <Text type="secondary" style={{ marginLeft: 8 }}>
          {rows.length} 行
        </Text>
      </div>
      <div
        ref={panelRef}
        data-testid={`compare-workbook-panel-${side}`}
        onScroll={onScroll}
        style={{
          overflow: "auto",
          maxHeight: PANEL_MAX_HEIGHT,
        }}
      >
        <table
          style={{
            borderCollapse: "separate",
            borderSpacing: 0,
            minWidth: totalWidth,
            tableLayout: "fixed",
            width: totalWidth,
          }}
        >
          <thead>
            <tr>
              {columns.map((column, index) => (
                <th
                  key={`${side}-${column.field}-head`}
                  style={cellStyle({
                    colors,
                    width: column.width,
                    stickyTop: true,
                    stickyLeft: column.stickyLeft,
                    zIndex: column.stickyLeft !== undefined ? 6 : 4,
                    background: colors.BG_LAYOUT,
                  })}
                >
                  <div style={{ padding: "10px 12px", textAlign: "left", fontWeight: 600 }}>
                    {column.label}
                    {index === 0 ? (
                      <Text type="secondary" style={{ marginLeft: 6, fontSize: 12 }}>
                        {side === "left" ? "L" : "R"}
                      </Text>
                    ) : null}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => {
              const rowBg = rowBackground(row.diff_status, colors);
              return (
                <tr key={`${side}-${row.compare_key}`} data-row-status={row.diff_status}>
                  {columns.map((column) => {
                    const isStatusColumn = column.field === "__status__";
                    const field = column.field;
                    const isChangedCell = !isStatusColumn && row.different_fields.includes(field);
                    const value = isStatusColumn ? null : row[side].values[field];
                    return (
                      <td
                        key={`${side}-${row.compare_key}-${column.field}`}
                        data-diff-cell={isChangedCell ? "true" : "false"}
                        style={cellStyle({
                          colors,
                          width: column.width,
                          stickyLeft: column.stickyLeft,
                          zIndex: column.stickyLeft !== undefined ? 3 : 1,
                          background: isChangedCell ? colors.HIGHLIGHT_BG : rowBg,
                        })}
                      >
                        <div style={{ padding: "8px 10px" }}>
                          {isStatusColumn ? (
                            <Tag color={(STATUS_META[row.diff_status] ?? STATUS_META.same).color}>
                              {(STATUS_META[row.diff_status] ?? STATUS_META.same).label}
                            </Tag>
                          ) : editable && onCellChange ? (
                            <Input
                              aria-label={`${side}-${row.compare_key}-${field}`}
                              size="small"
                              variant="borderless"
                              value={displayCellValue(value)}
                              placeholder="-"
                              onChange={(event) => onCellChange(row.compare_key, side, field, event.target.value)}
                            />
                          ) : (
                            <Text>{displayCellValue(value) || "-"}</Text>
                          )}
                        </div>
                      </td>
                    );
                  })}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function displayCellValue(value: CompareCellValue): string {
  return value === null || value === undefined ? "" : String(value);
}

function rowBackground(status: string, colors: ReturnType<typeof useSemanticColors>): string | undefined {
  if (status === "left_only") {
    return colors.HIGHLIGHT_BG_ERROR;
  }
  if (status === "right_only") {
    return colors.HIGHLIGHT_BG_PRIMARY;
  }
  return undefined;
}

function syncScrollPosition(target: HTMLDivElement, top: number, left: number) {
  if (Math.abs(target.scrollTop - top) > 1) {
    target.scrollTop = top;
  }
  if (Math.abs(target.scrollLeft - left) > 1) {
    target.scrollLeft = left;
  }
}

function cellStyle({
  colors,
  width,
  stickyTop = false,
  stickyLeft,
  zIndex,
  background,
}: {
  colors: ReturnType<typeof useSemanticColors>;
  width: number;
  stickyTop?: boolean;
  stickyLeft?: number;
  zIndex: number;
  background?: string;
}): CSSProperties {
  const style: CSSProperties = {
    width,
    minWidth: width,
    maxWidth: width,
    borderRight: `1px solid ${colors.BORDER_SECONDARY}`,
    borderBottom: `1px solid ${colors.BORDER_SECONDARY}`,
    background: background ?? colors.BG_CONTAINER,
  };
  if (stickyTop || stickyLeft !== undefined) {
    style.position = "sticky";
    style.zIndex = zIndex;
  }
  if (stickyTop) {
    style.top = 0;
  }
  if (stickyLeft !== undefined) {
    style.left = stickyLeft;
  }
  return style;
}

export default CompareWorkbookDiff;
