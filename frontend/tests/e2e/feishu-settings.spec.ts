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
      signedInAt: "2026-04-09T12:30:00.000Z",
      mustChangePassword: false,
    }],
  );
}

async function installMockApi(
  page: Page,
  options: {
    syncEnabled?: boolean;
    oauthEnabled?: boolean;
    credentialsConfigured?: boolean;
  } = {},
) {
  const {
    syncEnabled = true,
    oauthEnabled = false,
    credentialsConfigured = false,
  } = options;
  const featureFlags = {
    feishu_sync_enabled: syncEnabled,
    feishu_oauth_enabled: oauthEnabled,
    feishu_credentials_configured: credentialsConfigured,
  };

  const runtimeSettings = {
    feishu_sync_enabled: syncEnabled,
    feishu_oauth_enabled: oauthEnabled,
    feishu_credentials_configured: credentialsConfigured,
    masked_app_id: credentialsConfigured ? "cli_ap****90" : (null as string | null),
    secret_configured: credentialsConfigured,
  };

  const syncConfigs = [
    {
      id: "sync-001",
      name: "社保明细同步",
      app_token: "app_token_seed",
      table_id: "tbl_seed",
      granularity: "detail",
      field_mapping: {},
      is_active: true,
      created_at: "2026-04-09T12:00:00Z",
      updated_at: "2026-04-09T12:00:00Z",
    },
  ];

  const syncHistory = [
    {
      id: "job-001",
      config_id: "sync-001",
      direction: "push",
      status: "success",
      total_records: 8,
      success_records: 8,
      failed_records: 0,
      error_message: null,
      detail: null,
      triggered_by: "admin.demo",
      created_at: "2026-04-09T12:05:00Z",
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

    if (path === "/system/features" && request.method() === "GET") {
      await fulfillJson(route, createSuccess(featureFlags));
      return;
    }

    if (path === "/feishu/settings/runtime" && request.method() === "GET") {
      await fulfillJson(route, createSuccess(runtimeSettings));
      return;
    }

    if (path === "/feishu/settings/runtime" && request.method() === "PUT") {
      const body = request.postDataJSON() as {
        feishu_sync_enabled?: boolean;
        feishu_oauth_enabled?: boolean;
      };
      if (body.feishu_sync_enabled !== undefined) {
        runtimeSettings.feishu_sync_enabled = body.feishu_sync_enabled;
        featureFlags.feishu_sync_enabled = body.feishu_sync_enabled;
      }
      if (body.feishu_oauth_enabled !== undefined) {
        runtimeSettings.feishu_oauth_enabled = body.feishu_oauth_enabled;
        featureFlags.feishu_oauth_enabled = body.feishu_oauth_enabled;
      }
      await fulfillJson(route, createSuccess(runtimeSettings));
      return;
    }

    if (path === "/feishu/settings/credentials" && request.method() === "PUT") {
      const body = request.postDataJSON() as { app_id: string; app_secret: string };
      runtimeSettings.masked_app_id = `${body.app_id.slice(0, 6)}****${body.app_id.slice(-2)}`;
      runtimeSettings.secret_configured = Boolean(body.app_secret);
      runtimeSettings.feishu_credentials_configured = true;
      featureFlags.feishu_credentials_configured = true;
      await fulfillJson(route, createSuccess(runtimeSettings));
      return;
    }

    if (path === "/feishu/settings/configs" && request.method() === "GET") {
      await fulfillJson(route, createSuccess(syncConfigs));
      return;
    }

    if (path === "/feishu/settings/configs" && request.method() === "POST") {
      const body = request.postDataJSON() as {
        name: string;
        app_token: string;
        table_id: string;
        granularity: "detail" | "summary";
        field_mapping?: Record<string, string>;
      };
      const created = {
        id: `sync-${syncConfigs.length + 1}`,
        name: body.name,
        app_token: body.app_token,
        table_id: body.table_id,
        granularity: body.granularity,
        field_mapping: body.field_mapping ?? {},
        is_active: true,
        created_at: "2026-04-09T12:10:00Z",
        updated_at: "2026-04-09T12:10:00Z",
      };
      syncConfigs.push(created);
      await fulfillJson(route, createSuccess(created), 201);
      return;
    }

    if (path.startsWith("/feishu/settings/configs/") && request.method() === "PUT") {
      const configId = path.split("/")[4];
      const body = request.postDataJSON() as Partial<(typeof syncConfigs)[number]>;
      const target = syncConfigs.find((config) => config.id === configId);
      if (!target) {
        await fulfillJson(route, { success: false }, 404);
        return;
      }
      Object.assign(target, body, { updated_at: "2026-04-09T12:11:00Z" });
      await fulfillJson(route, createSuccess(target));
      return;
    }

    if (path.startsWith("/feishu/settings/configs/") && request.method() === "DELETE") {
      const configId = path.split("/")[4];
      const index = syncConfigs.findIndex((config) => config.id === configId);
      if (index >= 0) {
        syncConfigs.splice(index, 1);
      }
      await fulfillJson(route, createSuccess(null), 204);
      return;
    }

    if (path === "/feishu/sync/history" && request.method() === "GET") {
      await fulfillJson(route, createSuccess(syncHistory));
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

test("Feishu settings save flow refreshes sync state without exposing the secret", async ({ page }) => {
  await seedAuthSession(page);
  await installMockApi(page);

  await page.goto("/feishu-sync");
  await expect(page.getByText("飞书应用凭证未配置")).toBeVisible();
  await expect(page.locator('[data-testid="feishu-settings-cta"]')).toBeVisible();
  await expect(page.locator('[data-testid="feishu-sync-push"]')).toBeDisabled();

  await page.locator('[data-testid="feishu-settings-cta"]').click();
  await expect(page).toHaveURL(/\/feishu-settings$/);
  const runtimeSaveButton = page.getByRole("button", { name: "保存开关" });
  await expect(runtimeSaveButton).toBeVisible();

  await page.locator('[data-testid="feishu-oauth-toggle"]').evaluate((node) => {
    (node as HTMLButtonElement).click();
  });
  await runtimeSaveButton.evaluate((node) => {
    (node as HTMLButtonElement).click();
  });
  await expect(page.locator(".ant-tag").filter({ hasText: "已启用" })).toHaveCount(2);

  await page.locator('[data-testid="feishu-app-id-input"]').fill("cli_app_1234567890");
  await page.getByLabel("App Secret").fill("super-secret-value");
  await page.locator('[data-testid="feishu-credentials-save"]').click();

  await expect(page.getByText("cli_ap****90")).toBeVisible();
  await expect(page.getByText("super-secret-value")).toHaveCount(0);

  await page.getByRole("button", { name: "前往同步页" }).click();
  await expect(page).toHaveURL(/\/feishu-sync$/);
  await expect(page.locator('[data-testid="feishu-sync-push"]')).toBeEnabled();
});

test("Feishu settings mobile drawer still supports creating a sync config", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await seedAuthSession(page);
  await installMockApi(page);

  await page.goto("/feishu-settings");
  await page.locator('[data-testid="feishu-sync-config-add"]').click();

  await page.getByLabel("名称").fill("移动端新建同步");
  await page.getByLabel("多维表格 App Token").fill("app_token_mobile");
  await page.getByLabel("数据表 Table ID").fill("tbl_mobile");
  await page.getByRole("radio", { name: "汇总" }).check();
  await page.locator('[data-testid="feishu-config-submit"]').click();

  await expect(page.getByText("移动端新建同步")).toBeVisible();
  await expect(page.locator("table").getByText("汇总")).toBeVisible();
});

test("FeishuSync shows a settings CTA when runtime sync is disabled", async ({ page }) => {
  await seedAuthSession(page);
  await installMockApi(page, { syncEnabled: false });

  await page.goto("/feishu-sync");
  await expect(page.getByText("飞书同步已关闭")).toBeVisible();
  await expect(page.locator('[data-testid="feishu-settings-cta"]')).toBeVisible();
  await expect(page.locator('[data-testid="feishu-sync-push"]')).toHaveCount(0);
});
