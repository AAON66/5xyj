import { expect, test, type Page, type Route } from "@playwright/test";

const API_BASE_URL = "http://127.0.0.1:8000/api/v1";
const APP_ORIGIN = "http://127.0.0.1:4173";
const AUTH_SESSION_KEY = "social-security-auth-session";

function createSuccess<T>(data: T) {
  return {
    success: true as const,
    message: "ok",
    data,
  };
}

function getCorsHeaders() {
  return {
    "access-control-allow-origin": APP_ORIGIN,
    "access-control-allow-methods": "GET,POST,PUT,PATCH,DELETE,OPTIONS",
    "access-control-allow-headers": "Content-Type, Authorization",
  };
}

async function fulfillJson(route: Route, payload: unknown, status = 200) {
  await route.fulfill({
    status,
    headers: {
      ...getCorsHeaders(),
      "content-type": "application/json",
    },
    body: JSON.stringify(payload),
  });
}

async function seedAuthSession(page: Page) {
  await page.addInitScript(
    ([storageKey, payload]) => {
      window.localStorage.setItem(storageKey, JSON.stringify(payload));
    },
    [AUTH_SESSION_KEY, {
      accessToken: "admin-token",
      expiresAt: "2099-01-01T00:00:00.000Z",
      username: "admin.demo",
      role: "admin",
      displayName: "管理员演示账号",
      signedInAt: "2026-04-09T12:00:00.000Z",
      mustChangePassword: false,
    }],
  );
}

function buildRowValues(index: number) {
  return {
    person_name: `员工${String(index).padStart(2, "0")}`,
    employee_id: `E${String(index).padStart(3, "0")}`,
    id_number: `44010119900101${String(index).padStart(4, "0")}`,
    company_name: index % 2 === 0 ? "零一科技" : "零一裂变",
    region: index % 2 === 0 ? "深圳" : "广州",
    billing_period: "202602",
    total_amount: 1800 + index,
    personal_total_amount: 620 + index,
    company_total_amount: 1180 + index,
    pension_company: 520 + index,
    pension_personal: 260 + index,
    medical_maternity_company: 180 + index,
    unemployment_company: 24 + index,
    housing_fund_company: 200 + index,
    housing_fund_personal: 200 + index,
  };
}

function buildCompareRow(index: number, status: "changed" | "left_only" | "right_only" | "same") {
  const leftValues = buildRowValues(index);
  const rightValues = buildRowValues(index + 100);
  if (status === "changed") {
    rightValues.total_amount = leftValues.total_amount + 55;
    rightValues.personal_total_amount = leftValues.personal_total_amount + 22;
  }
  return {
    compare_key: `key-${index}`,
    match_basis: "employee_id",
    diff_status: status,
    different_fields: status === "changed" ? ["total_amount", "personal_total_amount"] : [],
    left: {
      record_id: `left-${index}`,
      source_file_id: `file-left-${index}`,
      source_file_name: "left.xlsx",
      source_row_number: index + 10,
      values: status === "right_only" ? {} : leftValues,
    },
    right: {
      record_id: `right-${index}`,
      source_file_id: `file-right-${index}`,
      source_file_name: status === "left_only" ? null : "right.xlsx",
      source_row_number: status === "left_only" ? null : index + 20,
      values: status === "left_only" ? {} : rightValues,
    },
  };
}

async function selectAntOptionByTestId(page: Page, testId: string, optionText: string) {
  await page.locator(`[data-testid="${testId}"] .ant-select-selector`).click({ force: true });
  await page.locator(".ant-select-item-option-content").filter({ hasText: optionText }).last().click();
}

async function installMockApi(page: Page, periodCompareRequests: string[]) {
  const importBatches = [
    {
      id: "batch-current",
      batch_name: "202602 批次",
      status: "parsed",
      created_at: "2026-02-10T08:00:00Z",
      updated_at: "2026-02-10T08:00:00Z",
      file_count: 2,
      normalized_record_count: 41,
    },
    {
      id: "batch-baseline",
      batch_name: "202601 批次",
      status: "exported",
      created_at: "2026-01-10T08:00:00Z",
      updated_at: "2026-01-10T08:00:00Z",
      file_count: 2,
      normalized_record_count: 41,
    },
  ];

  const exportSnapshots = {
    "batch-current": {
      batch_id: "batch-current",
      batch_name: "202602 批次",
      status: "exported",
      export_job_id: "job-current",
      export_status: "completed",
      blocked_reason: null,
      artifacts: [
        { template_type: "salary", status: "completed", file_path: "/tmp/current-salary.xlsx", error_message: null, row_count: 41 },
        { template_type: "final_tool", status: "completed", file_path: "/tmp/current-tool.xlsx", error_message: null, row_count: 41 },
      ],
      completed_at: "2026-04-09T12:00:00Z",
    },
    "batch-baseline": {
      batch_id: "batch-baseline",
      batch_name: "202601 批次",
      status: "exported",
      export_job_id: "job-baseline",
      export_status: "completed",
      blocked_reason: null,
      artifacts: [
        { template_type: "salary", status: "completed", file_path: "/tmp/baseline-salary.xlsx", error_message: null, row_count: 41 },
        { template_type: "final_tool", status: "completed", file_path: "/tmp/baseline-tool.xlsx", error_message: null, row_count: 41 },
      ],
      completed_at: "2026-04-09T12:00:00Z",
    },
  } as const;

  const batchCompareResult = {
    left_batch: {
      id: "batch-current",
      batch_name: "202602 批次",
      status: "parsed",
      record_count: 3,
    },
    right_batch: {
      id: "batch-baseline",
      batch_name: "202601 批次",
      status: "exported",
      record_count: 3,
    },
    fields: [
      "person_name",
      "employee_id",
      "company_name",
      "region",
      "billing_period",
      "total_amount",
      "personal_total_amount",
      "company_total_amount",
      "pension_company",
      "medical_maternity_company",
      "housing_fund_company",
      "housing_fund_personal",
    ],
    total_row_count: 3,
    same_row_count: 1,
    changed_row_count: 1,
    left_only_count: 1,
    right_only_count: 0,
    rows: [
      buildCompareRow(1, "changed"),
      buildCompareRow(2, "left_only"),
      buildCompareRow(3, "same"),
    ],
  };

  const periodRowsPage0 = Array.from({ length: 24 }, (_, index) =>
    buildCompareRow(index + 10, index % 6 === 0 ? "left_only" : "changed"),
  );
  const periodRowsPage1 = Array.from({ length: 17 }, (_, index) =>
    buildCompareRow(index + 40, index % 4 === 0 ? "right_only" : "changed"),
  );

  await page.route(`${API_BASE_URL}/**`, async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const path = url.pathname.replace("/api/v1", "");

    if (request.method() === "OPTIONS") {
      await route.fulfill({
        status: 204,
        headers: getCorsHeaders(),
      });
      return;
    }

    if (path === "/auth/me" && request.method() === "GET") {
      await fulfillJson(route, createSuccess({
        username: "admin.demo",
        role: "admin",
        display_name: "管理员演示账号",
        must_change_password: false,
      }));
      return;
    }

    if (path === "/system/health" && request.method() === "GET") {
      await fulfillJson(route, createSuccess({
        status: "ok",
        app_name: "social-security-aggregator",
        version: "0.2.0-test",
      }));
      return;
    }

    if (path === "/system/features" && request.method() === "GET") {
      await fulfillJson(route, createSuccess({
        feishu_sync_enabled: true,
        feishu_oauth_enabled: true,
        feishu_credentials_configured: true,
      }));
      return;
    }

    if (path === "/data-management/filter-options" && request.method() === "GET") {
      await fulfillJson(route, createSuccess({
        regions: ["深圳", "广州"],
        companies: ["零一科技", "零一裂变"],
        periods: ["202601", "202602"],
      }));
      return;
    }

    if (path === "/imports" && request.method() === "GET") {
      await fulfillJson(route, createSuccess(importBatches));
      return;
    }

    if (path.startsWith("/imports/") && path.endsWith("/export") && request.method() === "GET") {
      const batchId = path.split("/")[2];
      await fulfillJson(route, createSuccess(exportSnapshots[batchId as keyof typeof exportSnapshots]));
      return;
    }

    if (path === "/compare" && request.method() === "GET") {
      await fulfillJson(route, createSuccess(batchCompareResult));
      return;
    }

    if (path === "/compare/periods" && request.method() === "GET") {
      periodCompareRequests.push(url.search);
      const pageIndex = Number(url.searchParams.get("page") ?? "0");
      const rows = pageIndex === 1 ? periodRowsPage1 : periodRowsPage0;
      await fulfillJson(route, createSuccess({
        left_period: "202601",
        right_period: "202602",
        fields: batchCompareResult.fields,
        total_row_count: 41,
        page: pageIndex,
        page_size: 40,
        total_pages: 2,
        returned_row_count: rows.length,
        diff_only: true,
        search_text: null,
        same_row_count: 0,
        changed_row_count: 30,
        left_only_count: 6,
        right_only_count: 5,
        rows,
        summary_groups: [
          {
            company_name: "零一科技",
            region: "深圳",
            total_count: 24,
            changed_count: 18,
            left_only_count: 4,
            right_only_count: 2,
            same_count: 0,
          },
          {
            company_name: "零一裂变",
            region: "广州",
            total_count: 17,
            changed_count: 12,
            left_only_count: 2,
            right_only_count: 3,
            same_count: 0,
          },
        ],
      }));
      return;
    }

    await fulfillJson(
      route,
      {
        success: false,
        error: {
          code: "unmocked_endpoint",
          message: `Unhandled mock endpoint: ${request.method()} ${path}`,
        },
      },
      500,
    );
  });
}

test("PeriodCompare renders shared diff viewer and paginates on the server", async ({ page }) => {
  const periodCompareRequests: string[] = [];
  await seedAuthSession(page);
  await installMockApi(page, periodCompareRequests);

  await page.goto("/period-compare");
  await page.getByRole("button", { name: "运行对比" }).click();

  await expect(page.locator('[data-testid="compare-workbook-diff"]')).toBeVisible();
  await expect(page.locator('[data-testid="compare-workbook-panel-left"] [data-diff-cell="true"]').first()).toBeVisible();
  await expect(page.locator('[data-testid="compare-workbook-panel-left"] tr[data-row-status="left_only"]').first()).toBeVisible();
  await expect(page.getByText("当前第 1 / 2 页")).toBeVisible();
  expect(periodCompareRequests[0]).toContain("page=0");
  expect(periodCompareRequests[0]).toContain("page_size=40");
  expect(periodCompareRequests[0]).toContain("diff_only=true");

  await page.getByRole("button", { name: "下一页" }).click();
  await expect(page.getByText("当前第 2 / 2 页")).toBeVisible();
  expect(periodCompareRequests[1]).toContain("page=1");

  const leftPanel = page.locator('[data-testid="compare-workbook-panel-left"]');
  const rightPanel = page.locator('[data-testid="compare-workbook-panel-right"]');
  await leftPanel.evaluate((node) => {
    node.scrollTo({ top: 320, left: 260 });
    node.dispatchEvent(new Event("scroll"));
  });
  await page.waitForTimeout(120);
  const leftScrollTop = await leftPanel.evaluate((node) => node.scrollTop);
  const leftScrollLeft = await leftPanel.evaluate((node) => node.scrollLeft);
  const rightScrollTop = await rightPanel.evaluate((node) => node.scrollTop);
  const rightScrollLeft = await rightPanel.evaluate((node) => node.scrollLeft);
  expect(rightScrollTop).toBeGreaterThan(120);
  expect(rightScrollLeft).toBeGreaterThan(200);
  expect(Math.abs(rightScrollTop - leftScrollTop)).toBeLessThan(8);
  expect(Math.abs(rightScrollLeft - leftScrollLeft)).toBeLessThan(8);
});

test("Compare reuses the shared diff viewer and keeps local filters on the current page", async ({ page }) => {
  const periodCompareRequests: string[] = [];
  await seedAuthSession(page);
  await installMockApi(page, periodCompareRequests);

  await page.goto("/compare");
  await page.locator('[data-testid="compare-run-button"]').click();

  await expect(page.locator('[data-testid="compare-workbook-diff"]')).toBeVisible();
  await expect(page.locator('[data-testid="compare-workbook-panel-left"] tr[data-row-status="changed"]').first()).toBeVisible();
  await expect(page.locator('[data-testid="compare-workbook-panel-left"] tr[data-row-status="left_only"]').first()).toBeVisible();
  await expect(page.locator('[data-testid="compare-workbook-panel-left"] tbody tr')).toHaveCount(2);
  await expect(page.locator('[data-testid="compare-workbook-panel-left"] th').filter({ hasText: "公司名称" })).toHaveCount(0);

  await page.getByRole("checkbox", { name: "只看差异行" }).uncheck();
  await expect(page.locator('[data-testid="compare-workbook-panel-left"] tbody tr')).toHaveCount(3);

  await selectAntOptionByTestId(page, "compare-table-type", "Tool 表格");
  await expect(page.locator('[data-testid="compare-workbook-panel-left"] th').filter({ hasText: "公司名称" })).toHaveCount(1);
  await expect(page.locator('[data-testid="compare-workbook-panel-left"] th').filter({ hasText: "地区" })).toHaveCount(1);
});
