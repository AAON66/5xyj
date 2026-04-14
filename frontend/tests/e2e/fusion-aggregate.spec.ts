import { expect, test, type Locator, type Page, type Route } from "@playwright/test";

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
      signedInAt: "2026-04-09T11:33:47.000Z",
      mustChangePassword: false,
    }],
  );
}

async function installMockApi(page: Page, aggregateBodyRef: { current: string }) {
  const syncConfigs = [
    {
      id: "sync-feishu-1",
      name: "承担额配置",
      app_token: "app-token",
      table_id: "tbl-001",
      granularity: "detail",
      field_mapping: {
        员工工号列: "employee_id",
        社保承担列: "personal_social_burden",
      },
      is_active: true,
      created_at: "2026-04-09T11:00:00Z",
      updated_at: "2026-04-09T11:00:00Z",
    },
  ];
  const fusionRules = [
    {
      id: "rule-existing",
      scope_type: "employee_id",
      scope_value: "E8001",
      field_name: "personal_social_burden",
      override_value: "18.80",
      note: "existing",
      is_active: true,
      created_by: "admin.demo",
      created_at: "2026-04-09T11:00:00Z",
      updated_at: "2026-04-09T11:00:00Z",
    },
  ];

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

    if (path === "/employees" && request.method() === "GET") {
      await fulfillJson(route, createSuccess({
        total: 3,
        limit: 20,
        offset: 0,
        items: [],
      }));
      return;
    }

    if (path === "/fusion-rules" && request.method() === "GET") {
      await fulfillJson(route, createSuccess(fusionRules));
      return;
    }

    if (path === "/fusion-rules" && request.method() === "POST") {
      const body = request.postDataJSON() as {
        scope_type: string;
        scope_value: string;
        field_name: string;
        override_value: string;
        note?: string | null;
      };
      const createdRule = {
        id: "rule-created",
        scope_type: body.scope_type,
        scope_value: body.scope_value,
        field_name: body.field_name,
        override_value: body.override_value,
        note: body.note ?? null,
        is_active: true,
        created_by: "admin.demo",
        created_at: "2026-04-09T11:05:00Z",
        updated_at: "2026-04-09T11:05:00Z",
      };
      fusionRules.unshift(createdRule);
      await fulfillJson(route, createSuccess(createdRule), 201);
      return;
    }

    if (path === "/feishu/settings/configs" && request.method() === "GET") {
      await fulfillJson(route, createSuccess(syncConfigs));
      return;
    }

    if (path === "/aggregate/stream" && request.method() === "POST") {
      aggregateBodyRef.current = request.postDataBuffer()?.toString("utf8") ?? request.postData() ?? "";
      await route.fulfill({
        status: 200,
        headers: {
          ...getCorsHeaders(),
          "content-type": "application/x-ndjson",
        },
        body: [
          JSON.stringify({
            event: "progress",
            stage: "export",
            label: "导出双模板",
            message: "正在生成模板。",
            percent: 96,
          }),
          JSON.stringify({
            event: "result",
            data: {
              batch_id: "batch-fusion-01",
              batch_name: "quick-aggregate-fusion",
              status: "exported",
              export_status: "completed",
              blocked_reason: null,
              fusion_messages: [],
              employee_master: null,
              total_issue_count: 0,
              matched_count: 1,
              unmatched_count: 0,
              duplicate_count: 0,
              low_confidence_count: 0,
              source_files: [
                {
                  source_file_id: "source-1",
                  file_name: "social.xlsx",
                  source_kind: "social_security",
                  region: "shenzhen",
                  company_name: "创造欢乐",
                  normalized_record_count: 1,
                  filtered_row_count: 0,
                },
              ],
              artifacts: [
                {
                  template_type: "salary",
                  status: "completed",
                  file_path: "/tmp/salary.xlsx",
                  error_message: null,
                  row_count: 1,
                },
                {
                  template_type: "final_tool",
                  status: "completed",
                  file_path: "/tmp/tool.xlsx",
                  error_message: null,
                  row_count: 1,
                },
              ],
            },
          }),
        ].join("\n"),
      });
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

async function prepareAuthenticatedPage(page: Page, aggregateBodyRef: { current: string }) {
  await seedAuthSession(page);
  await installMockApi(page, aggregateBodyRef);
}

async function expectStickyButton(button: Locator) {
  await expect(button).toBeVisible();
  const parentPosition = await button.evaluate((node) => {
    const parent = node.parentElement;
    return parent ? window.getComputedStyle(parent).position : "";
  });
  expect(parentPosition).toBe("sticky");
}

async function selectAntOptionByText(page: Page, testId: string, optionText: string) {
  await page.locator(`[data-testid="${testId}"]`).click();
  await page.locator(".ant-select-item-option-content").filter({ hasText: optionText }).last().click();
}

test("simple aggregate mobile flow submits burden source and fusion rule payload", async ({ page }) => {
  const aggregateBodyRef = { current: "" };
  await page.setViewportSize({ width: 375, height: 812 });
  await prepareAuthenticatedPage(page, aggregateBodyRef);

  await page.goto("/aggregate");

  const stickyPrimaryButton = page.getByRole("button", { name: "开始聚合并导出" });
  await expect(stickyPrimaryButton).toHaveCount(1);
  await expectStickyButton(stickyPrimaryButton);
  await expect(page.getByRole("button", { name: /工号 E8001/ })).toBeVisible();

  await page.locator('[data-testid="aggregate-social-upload"] input[type="file"]').setInputFiles({
    name: "social.xlsx",
    mimeType: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    buffer: Buffer.from("social-file"),
  });

  await selectAntOptionByText(page, "aggregate-burden-source-select", "选择飞书配置");
  await selectAntOptionByText(page, "aggregate-burden-feishu-select", "承担额配置 | 明细");

  await page.getByRole("button", { name: "新建规则" }).click();
  await page.getByLabel("命中值").fill("E9001");
  await page.getByRole("spinbutton", { name: "覆盖金额" }).fill("88.50");
  await page.getByLabel("备注").fill("fusion rule");
  await page.getByRole("button", { name: "保存规则" }).click();

  await expect(page.getByTestId("aggregate-fusion-rule-select").getByText("工号 E9001 | 个人社保承担额 = 88.50")).toBeVisible();

  await stickyPrimaryButton.click();

  await expect(page.getByText("批次 quick-aggregate-fusion 已完成双模板导出。")).toBeVisible();
  expect(aggregateBodyRef.current).toContain('name="burden_source_mode"');
  expect(aggregateBodyRef.current).toContain("feishu");
  expect(aggregateBodyRef.current).toContain('name="burden_feishu_config_id"');
  expect(aggregateBodyRef.current).toContain("sync-feishu-1");
  expect(aggregateBodyRef.current).toContain('name="fusion_rule_ids"');
  expect(aggregateBodyRef.current).toContain('["rule-created"]');
});
