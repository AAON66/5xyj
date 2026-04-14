import { expect, test, type Locator, type Page, type Route } from "@playwright/test";

const API_BASE_URL = "http://127.0.0.1:8000/api/v1";
const APP_ORIGIN = "http://127.0.0.1:4173";
const AUTH_SESSION_KEY = "social-security-auth-session";

type AuthRole = "admin" | "employee";

interface ApiEnvelope<T> {
  success: true;
  message: string;
  data: T;
}

const importBatches = [
  {
    id: "batch-202602",
    batch_name: "202602 批次",
    status: "parsed",
    created_at: "2026-02-10T08:00:00Z",
    updated_at: "2026-02-10T08:00:00Z",
    file_count: 2,
    normalized_record_count: 2,
  },
  {
    id: "batch-202601",
    batch_name: "202601 批次",
    status: "exported",
    created_at: "2026-01-10T08:00:00Z",
    updated_at: "2026-01-10T08:00:00Z",
    file_count: 2,
    normalized_record_count: 2,
  },
];

const dashboardOverview = {
  generated_at: "2026-04-09T11:00:00Z",
  totals: {
    total_batches: 12,
    total_source_files: 38,
    total_normalized_records: 256,
    total_validation_issues: 5,
    total_match_results: 233,
    total_export_jobs: 8,
    active_employee_masters: 52,
  },
  batch_status_counts: {
    parsed: 4,
    matched: 3,
    exported: 5,
  },
  match_status_counts: {
    matched: 210,
    unmatched: 18,
    duplicate: 3,
    low_confidence: 2,
  },
  issue_severity_counts: {
    error: 2,
    warning: 3,
  },
  export_status_counts: {
    completed: 7,
    failed: 1,
  },
  recent_batches: [
    {
      batch_id: "batch-202602",
      batch_name: "202602 批次",
      status: "parsed",
      file_count: 2,
      normalized_record_count: 2,
      validation_issue_count: 1,
      match_result_count: 2,
      export_job_count: 1,
      created_at: "2026-02-10T08:00:00Z",
      updated_at: "2026-02-10T08:00:00Z",
    },
  ],
};

const dashboardQuality = {
  total_missing: 2,
  total_anomalous: 1,
  total_duplicates: 0,
  batches: [
    {
      batch_id: "batch-202602",
      batch_name: "202602 批次",
      record_count: 2,
      missing_fields: 2,
      anomalous_amounts: 1,
      duplicate_records: 0,
    },
  ],
};

const normalizedRecords = {
  items: [
    {
      id: "record-1",
      batch_id: "batch-202602",
      person_name: "张三",
      id_number: "440101199001010011",
      employee_id: "E001",
      company_name: "零一科技",
      region: "深圳",
      billing_period: "202602",
      payment_base: 8000,
      total_amount: 1820,
      company_total_amount: 1200,
      personal_total_amount: 620,
      pension_company: 600,
      pension_personal: 300,
      medical_company: 320,
      medical_personal: 160,
      medical_maternity_company: 0,
      unemployment_company: 30,
      unemployment_personal: 10,
      injury_company: 20,
      supplementary_medical_company: 15,
      supplementary_pension_company: 0,
      large_medical_personal: 5,
      housing_fund_personal: 200,
      housing_fund_company: 200,
      housing_fund_total: 400,
      created_at: "2026-02-10T08:00:00Z",
    },
    {
      id: "record-2",
      batch_id: "batch-202602",
      person_name: "李四",
      id_number: "440101199202020022",
      employee_id: "E002",
      company_name: "零一科技",
      region: "深圳",
      billing_period: "202602",
      payment_base: 9000,
      total_amount: 2010,
      company_total_amount: 1320,
      personal_total_amount: 690,
      pension_company: 650,
      pension_personal: 320,
      medical_company: 340,
      medical_personal: 170,
      medical_maternity_company: 0,
      unemployment_company: 35,
      unemployment_personal: 15,
      injury_company: 20,
      supplementary_medical_company: 20,
      supplementary_pension_company: 0,
      large_medical_personal: 5,
      housing_fund_personal: 250,
      housing_fund_company: 250,
      housing_fund_total: 500,
      created_at: "2026-02-10T08:00:00Z",
    },
  ],
  total: 2,
  page: 0,
  page_size: 20,
};

const filterOptions = {
  regions: ["深圳", "广州"],
  companies: ["零一科技", "零一裂变"],
  periods: ["202601", "202602"],
};

const employeePortalResult = {
  matched_employee_master: true,
  profile: {
    employee_id: "E1001",
    person_name: "王小明",
    masked_id_number: "4401****0011",
    company_name: "零一科技",
    department: "运营",
    active: true,
    source: "employee_master",
  },
  record_count: 2,
  records: [
    {
      normalized_record_id: "portal-202602",
      batch_id: "batch-202602",
      batch_name: "202602 批次",
      batch_status: "matched",
      employee_id: "E1001",
      region: "深圳",
      company_name: "零一科技",
      billing_period: "202602",
      period_start: "2026-02-01",
      period_end: "2026-02-29",
      source_file_name: "深圳社保.xlsx",
      source_row_number: 12,
      total_amount: "1820.00",
      company_total_amount: "1200.00",
      personal_total_amount: "620.00",
      housing_fund_personal: "200.00",
      housing_fund_company: "200.00",
      housing_fund_total: "400.00",
      payment_base: "8000.00",
      pension_company: "600.00",
      pension_personal: "300.00",
      medical_company: "320.00",
      medical_personal: "160.00",
      unemployment_company: "30.00",
      unemployment_personal: "10.00",
      injury_company: "20.00",
      maternity_amount: "0.00",
      created_at: "2026-02-10T08:00:00Z",
    },
    {
      normalized_record_id: "portal-202601",
      batch_id: "batch-202601",
      batch_name: "202601 批次",
      batch_status: "matched",
      employee_id: "E1001",
      region: "深圳",
      company_name: "零一科技",
      billing_period: "202601",
      period_start: "2026-01-01",
      period_end: "2026-01-31",
      source_file_name: "深圳社保.xlsx",
      source_row_number: 9,
      total_amount: "1760.00",
      company_total_amount: "1160.00",
      personal_total_amount: "600.00",
      housing_fund_personal: "180.00",
      housing_fund_company: "180.00",
      housing_fund_total: "360.00",
      payment_base: "7800.00",
      pension_company: "580.00",
      pension_personal: "290.00",
      medical_company: "310.00",
      medical_personal: "155.00",
      unemployment_company: "30.00",
      unemployment_personal: "10.00",
      injury_company: "20.00",
      maternity_amount: "0.00",
      created_at: "2026-01-10T08:00:00Z",
    },
  ],
};

const validationResult = {
  batch_id: "batch-202602",
  batch_name: "202602 批次",
  status: "validated",
  total_issue_count: 1,
  source_files: [
    {
      source_file_id: "file-1",
      file_name: "深圳社保.xlsx",
      raw_sheet_name: "申报明细",
      issue_count: 1,
      issues: [
        {
          normalized_record_id: "record-1",
          source_row_number: 12,
          issue_type: "missing_field",
          severity: "warning",
          field_name: "employee_id",
          message: "员工工号缺失，需人工确认。",
        },
      ],
    },
  ],
};

const exportSnapshot = {
  batch_id: "batch-202602",
  batch_name: "202602 批次",
  status: "completed",
  export_job_id: "export-1",
  export_status: "completed",
  blocked_reason: null,
  artifacts: [
    {
      template_type: "salary",
      status: "completed",
      file_path: "/tmp/salary.xlsx",
      error_message: null,
      row_count: 2,
    },
    {
      template_type: "final_tool",
      status: "completed",
      file_path: "/tmp/final-tool.xlsx",
      error_message: null,
      row_count: 2,
    },
  ],
  completed_at: "2026-02-10T09:00:00Z",
};

const compareResult = {
  left_batch: {
    id: "batch-202602",
    batch_name: "202602 批次",
    status: "parsed",
    record_count: 1,
  },
  right_batch: {
    id: "batch-202601",
    batch_name: "202601 批次",
    status: "exported",
    record_count: 1,
  },
  fields: ["person_name", "employee_id", "company_name", "billing_period", "total_amount"],
  total_row_count: 1,
  same_row_count: 0,
  changed_row_count: 1,
  left_only_count: 0,
  right_only_count: 0,
  rows: [
    {
      compare_key: "E001",
      match_basis: "employee_id",
      diff_status: "changed",
      different_fields: ["billing_period", "total_amount"],
      left: {
        record_id: "record-1",
        source_file_id: "file-left",
        source_file_name: "202602.xlsx",
        source_row_number: 12,
        values: {
          person_name: "张三",
          employee_id: "E001",
          company_name: "零一科技",
          billing_period: "202602",
          total_amount: 1820,
        },
      },
      right: {
        record_id: "record-2",
        source_file_id: "file-right",
        source_file_name: "202601.xlsx",
        source_row_number: 11,
        values: {
          person_name: "张三",
          employee_id: "E001",
          company_name: "零一科技",
          billing_period: "202601",
          total_amount: 1760,
        },
      },
    },
  ],
};

const periodCompareResult = {
  left_period: "202601",
  right_period: "202602",
  fields: ["person_name", "employee_id", "company_name", "region", "billing_period", "total_amount", "company_total_amount", "personal_total_amount"],
  total_row_count: 1,
  same_row_count: 0,
  changed_row_count: 1,
  left_only_count: 0,
  right_only_count: 0,
  rows: compareResult.rows,
  summary_groups: [
    {
      company_name: "零一科技",
      region: "深圳",
      total_count: 1,
      changed_count: 1,
      left_only_count: 0,
      right_only_count: 0,
      same_count: 0,
    },
  ],
};

const feishuFeatureFlags = {
  feishu_sync_enabled: true,
  feishu_oauth_enabled: true,
  feishu_credentials_configured: true,
};

const syncConfigs = [
  {
    id: "config-1",
    name: "社保明细同步",
    app_token: "bascn1234567890",
    table_id: "tbl123456",
    granularity: "detail",
    field_mapping: {},
    is_active: true,
    created_at: "2026-04-08T10:00:00Z",
    updated_at: "2026-04-08T10:00:00Z",
  },
];

function createSuccess<T>(data: T): ApiEnvelope<T> {
  return {
    success: true,
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

async function fulfillNotFound(route: Route, message = "not found") {
  await fulfillJson(
    route,
    {
      success: false,
      error: {
        code: "not_found",
        message,
      },
    },
    404,
  );
}

async function installMockApi(page: Page, role: AuthRole) {
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
        username: role === "employee" ? "employee.demo" : "admin.demo",
        role,
        display_name: role === "employee" ? "员工演示账号" : "管理员演示账号",
        must_change_password: false,
      }));
      return;
    }

    if (path === "/system/health" && request.method() === "GET") {
      await fulfillJson(route, createSuccess({
        status: "ok",
        app_name: "social-security-aggregator",
        version: "0.1.0-test",
      }));
      return;
    }

    if (path === "/dashboard/overview" && request.method() === "GET") {
      await fulfillJson(route, createSuccess(dashboardOverview));
      return;
    }

    if (path === "/dashboard/quality" && request.method() === "GET") {
      await fulfillJson(route, createSuccess(dashboardQuality));
      return;
    }

    if (path === "/employees" && request.method() === "GET") {
      await fulfillJson(route, createSuccess({
        total: 52,
        limit: 20,
        offset: 0,
        items: [],
      }));
      return;
    }

    if (path === "/employees/self-service/my-records" && request.method() === "GET") {
      await fulfillJson(route, createSuccess(employeePortalResult));
      return;
    }

    if (path === "/data-management/filter-options" && request.method() === "GET") {
      await fulfillJson(route, createSuccess(filterOptions));
      return;
    }

    if (path === "/data-management/records" && request.method() === "GET") {
      await fulfillJson(route, createSuccess(normalizedRecords));
      return;
    }

    if (path === "/data-management/summary/employees" && request.method() === "GET") {
      await fulfillJson(route, createSuccess({
        items: [],
        total: 0,
        page: 0,
        page_size: 20,
      }));
      return;
    }

    if (path === "/data-management/summary/periods" && request.method() === "GET") {
      await fulfillJson(route, createSuccess({
        items: [],
        total: 0,
        page: 0,
        page_size: 20,
      }));
      return;
    }

    if (path === "/imports" && request.method() === "GET") {
      await fulfillJson(route, createSuccess(importBatches));
      return;
    }

    if (/^\/imports\/[^/]+\/validation$/.test(path) && request.method() === "GET") {
      await fulfillNotFound(route, "validation not ready");
      return;
    }

    if (/^\/imports\/[^/]+\/validation$/.test(path) && request.method() === "POST") {
      await fulfillJson(route, createSuccess(validationResult));
      return;
    }

    if (/^\/imports\/[^/]+\/match$/.test(path) && request.method() === "GET") {
      await fulfillNotFound(route, "match not ready");
      return;
    }

    if (/^\/imports\/[^/]+\/export$/.test(path) && request.method() === "GET") {
      await fulfillJson(route, createSuccess(exportSnapshot));
      return;
    }

    if (path === "/compare" && request.method() === "GET") {
      await fulfillJson(route, createSuccess(compareResult));
      return;
    }

    if (path === "/compare/periods" && request.method() === "GET") {
      await fulfillJson(route, createSuccess(periodCompareResult));
      return;
    }

    if (path === "/system/features" && request.method() === "GET") {
      await fulfillJson(route, createSuccess(feishuFeatureFlags));
      return;
    }

    if (path === "/feishu/settings/configs" && request.method() === "GET") {
      await fulfillJson(route, createSuccess(syncConfigs));
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

async function seedAuthSession(page: Page, role: AuthRole) {
  const session = {
    accessToken: role === "employee" ? "employee-token" : "admin-token",
    expiresAt: "2099-01-01T00:00:00.000Z",
    username: role === "employee" ? "employee.demo" : "admin.demo",
    role,
    displayName: role === "employee" ? "员工演示账号" : "管理员演示账号",
    signedInAt: "2026-04-09T11:33:47.000Z",
    mustChangePassword: false,
  };

  await page.addInitScript(
    ([storageKey, payload]) => {
      window.localStorage.setItem(storageKey, JSON.stringify(payload));
    },
    [AUTH_SESSION_KEY, session],
  );
}

async function prepareAuthenticatedPage(page: Page, role: AuthRole = "admin") {
  await seedAuthSession(page, role);
  await installMockApi(page, role);
}

async function expectStickyButton(button: Locator) {
  await expect(button).toBeVisible();
  const parentPosition = await button.evaluate((node) => {
    const parent = node.parentElement;
    return parent ? window.getComputedStyle(parent).position : "";
  });
  expect(parentPosition).toBe("sticky");
}

test("mobile dashboard uses stacked cards and drawer navigation closes after route change", async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 812 });
  await prepareAuthenticatedPage(page);

  await page.goto("/dashboard");

  const firstStatCard = page.locator(".ant-card").filter({ has: page.getByText("导入批次") }).first();
  await expect(firstStatCard).toBeVisible();
  const cardBox = await firstStatCard.boundingBox();
  expect(cardBox?.width ?? 0).toBeGreaterThan(300);

  await expect(page.locator(".ant-breadcrumb")).toHaveCount(0);
  await page.getByRole("button", { name: "打开导航菜单" }).click();
  await expect(page.getByRole("button", { name: "关闭导航抽屉" })).toBeVisible();
  await page.getByRole("menuitem", { name: "校验匹配" }).click();

  await expect(page).toHaveURL(/\/results$/);
  await expect(page.getByRole("button", { name: "关闭导航抽屉" })).not.toBeVisible();
});

test("employee self-service renders mobile card flow with latest record expanded by default", async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 812 });
  await prepareAuthenticatedPage(page, "employee");

  await page.goto("/employee/query");

  await expect(page.getByRole("heading", { name: "员工社保查询" })).toBeVisible();
  await expect(page.getByText("2026年02月 缴费汇总")).toBeVisible();
  await expect(page.getByRole("heading", { name: "缴费历史" })).toBeVisible();
  await expect(page.locator(".ant-collapse-item-active")).toHaveCount(1);
  await expect(page.getByText("社保明细")).toBeVisible();
  await expect(page.getByText("公积金明细")).toBeVisible();
});

test("data management mobile filter drawer keeps draft state until apply", async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 812 });
  await prepareAuthenticatedPage(page);

  await page.goto("/data-management");

  await expect(page.getByText("张三")).toBeVisible();
  await expect(page.getByText("李四")).toBeVisible();

  const filterTrigger = page.locator("button").filter({ hasText: /^筛选(?: \(\d+\))?$/ }).first();

  await filterTrigger.dispatchEvent("click");
  await page.getByPlaceholder("搜索姓名、工号、公司或身份证号").fill("李");
  await page.getByRole("button", { name: "关闭筛选抽屉" }).click();

  await expect.poll(() => new URL(page.url()).searchParams.get("search")).toBeNull();
  await expect(page.getByText("张三")).toBeVisible();
  await expect(page.getByText("李四")).toBeVisible();

  await filterTrigger.dispatchEvent("click");
  await page.getByPlaceholder("搜索姓名、工号、公司或身份证号").fill("李");
  await page.getByRole("button", { name: "应用筛选" }).click();

  await expect.poll(() => new URL(page.url()).searchParams.get("search")).toBe("李");
  await expect(page.getByText("李四")).toBeVisible();
  await expect(page.getByText("张三")).not.toBeVisible();
});

test("mobile workflow pages expose a single sticky primary action and results page switches to next step after validation", async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 812 });
  await prepareAuthenticatedPage(page);

  await page.goto("/aggregate");
  const aggregateButton = page.getByRole("button", { name: "开始聚合并导出" });
  await expect(aggregateButton).toHaveCount(1);
  await expectStickyButton(aggregateButton);

  await page.goto("/results");
  const validateButton = page.getByRole("button", { name: "执行数据校验" });
  await expect(validateButton).toHaveCount(1);
  await expectStickyButton(validateButton);
  await validateButton.click();
  await expect(page.getByRole("button", { name: "执行工号匹配" })).toHaveCount(1);

  await page.goto("/exports");
  const exportButton = page.getByRole("button", { name: "执行双模板导出" });
  await expect(exportButton).toHaveCount(1);
  await expectStickyButton(exportButton);
});

test("compare page remains operable on compact viewport and can load compare results", async ({ page }) => {
  await page.setViewportSize({ width: 820, height: 1180 });
  await prepareAuthenticatedPage(page);

  await page.goto("/compare");
  await page.getByRole("button", { name: "开始对比" }).click();

  await expect(page.getByText("对比结果已刷新。")).toBeVisible();
  await expect(page.locator('[data-testid="compare-workbook-diff"]')).toBeVisible();
  await expect(page.locator('[data-testid="compare-workbook-panel-left"] tbody tr').first()).toBeVisible();
  await expect(page.getByText("左侧数据源")).toBeVisible();
  await expect(page.getByText("右侧数据源")).toBeVisible();
});

test("period compare keeps fixed columns and horizontal scrolling on narrow screens", async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 812 });
  await prepareAuthenticatedPage(page);

  await page.goto("/period-compare");
  await expect(page.getByRole("button", { name: "运行对比" })).toBeEnabled();
  await page.getByRole("button", { name: "运行对比" }).click();

  await expect(page.locator('[data-testid="compare-workbook-diff"]')).toBeVisible();
  await expect(page.locator('[data-testid="compare-workbook-panel-left"] tbody tr').first()).toBeVisible();
  const hasHorizontalOverflow = await page.locator('[data-testid="compare-workbook-panel-left"]').evaluate((node) => {
    const element = node as HTMLElement;
    return element.scrollWidth > element.clientWidth;
  });
  expect(hasHorizontalOverflow).toBeTruthy();
});

test("feishu settings remains operable on tablet and phone widths", async ({ page }) => {
  await prepareAuthenticatedPage(page);

  await page.setViewportSize({ width: 820, height: 1180 });
  await page.goto("/feishu-settings");
  await expect(page.getByRole("heading", { name: "飞书设置" })).toBeVisible();
  await expect(page.getByRole("button", { name: "添加同步目标" }).first()).toBeVisible();

  await page.setViewportSize({ width: 375, height: 812 });
  await expect(page.getByRole("button", { name: "添加同步目标" }).first()).toBeVisible();
  await page.getByRole("button", { name: "添加同步目标" }).first().click();
  await expect(page.getByLabel("名称")).toBeVisible();
  const hasHorizontalOverflow = await page.locator(".ant-table-content").first().evaluate((node) => {
    const element = node as HTMLElement;
    return element.scrollWidth > element.clientWidth;
  });
  expect(hasHorizontalOverflow).toBeTruthy();
});
