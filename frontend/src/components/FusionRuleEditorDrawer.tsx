import { useEffect, useState } from "react";
import { App, Button, Drawer, Form, Input, InputNumber, Popconfirm, Select, Space } from "antd";

import { normalizeApiError } from "../services/api";
import {
  createFusionRule,
  deleteFusionRule,
  type FusionRule,
  type FusionRuleFieldName,
  type FusionRuleScopeType,
  updateFusionRule,
} from "../services/fusionRules";

interface FusionRuleEditorDrawerProps {
  open: boolean;
  rule: FusionRule | null;
  onClose: () => void;
  onSaved: (rule: FusionRule) => void;
  onDeleted: (ruleId: string) => void;
}

interface FusionRuleFormValues {
  scopeType: FusionRuleScopeType;
  scopeValue: string;
  targetField: FusionRuleFieldName;
  overrideValue: number;
  note?: string;
}

const TARGET_FIELD_OPTIONS = [
  { value: "personal_social_burden", label: "个人社保承担额" },
  { value: "personal_housing_burden", label: "个人公积金承担额" },
] as const;

const SCOPE_TYPE_OPTIONS = [
  { value: "employee_id", label: "工号" },
  { value: "id_number", label: "身份证号" },
] as const;

export function FusionRuleEditorDrawer({
  open,
  rule,
  onClose,
  onSaved,
  onDeleted,
}: FusionRuleEditorDrawerProps) {
  const { message } = App.useApp();
  const [form] = Form.useForm<FusionRuleFormValues>();
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!open) {
      return;
    }
    if (rule) {
      form.setFieldsValue({
        scopeType: rule.scope_type,
        scopeValue: rule.scope_value,
        targetField: rule.field_name,
        overrideValue: Number(rule.override_value),
        note: rule.note ?? undefined,
      });
      return;
    }
    form.resetFields();
    form.setFieldsValue({
      scopeType: "employee_id",
      targetField: "personal_social_burden",
    });
  }, [form, open, rule]);

  async function handleSubmit(values: FusionRuleFormValues) {
    setSubmitting(true);
    try {
      const payload = {
        scope_type: values.scopeType,
        scope_value: values.scopeValue.trim(),
        field_name: values.targetField,
        override_value: values.overrideValue.toFixed(2),
        note: values.note?.trim() || null,
      };
      const savedRule = rule
        ? await updateFusionRule(rule.id, payload)
        : await createFusionRule(payload);
      message.success(rule ? "规则已更新" : "规则已创建");
      onSaved(savedRule);
      onClose();
    } catch (error) {
      message.error(normalizeApiError(error).message);
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete() {
    if (!rule) {
      return;
    }
    setSubmitting(true);
    try {
      await deleteFusionRule(rule.id);
      message.success("规则已删除");
      onDeleted(rule.id);
      onClose();
    } catch (error) {
      message.error(normalizeApiError(error).message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Drawer
      title={rule ? "编辑特殊规则" : "新建特殊规则"}
      open={open}
      onClose={onClose}
      width={420}
      destroyOnClose
      footer={(
        <Space style={{ width: "100%", justifyContent: "space-between" }}>
          <div>
            {rule ? (
              <Popconfirm
                title="确认删除这条规则？"
                okText="删除"
                cancelText="取消"
                onConfirm={() => void handleDelete()}
              >
                <Button danger loading={submitting}>删除规则</Button>
              </Popconfirm>
            ) : null}
          </div>
          <Space>
            <Button onClick={onClose}>取消</Button>
            <Button type="primary" loading={submitting} onClick={() => void form.submit()}>
              保存规则
            </Button>
          </Space>
        </Space>
      )}
    >
      <Form<FusionRuleFormValues>
        form={form}
        layout="vertical"
        onFinish={(values) => void handleSubmit(values)}
      >
        <Form.Item<FusionRuleFormValues>
          label="命中方式"
          name="scopeType"
          rules={[{ required: true, message: "请选择命中方式" }]}
        >
          <Select options={SCOPE_TYPE_OPTIONS.map((item) => ({ value: item.value, label: item.label }))} />
        </Form.Item>

        <Form.Item<FusionRuleFormValues>
          label="命中值"
          name="scopeValue"
          rules={[{ required: true, message: "请输入工号或身份证号" }]}
        >
          <Input placeholder="例如：E9001 或 440101199001010011" />
        </Form.Item>

        <Form.Item<FusionRuleFormValues>
          label="覆盖字段"
          name="targetField"
          rules={[{ required: true, message: "请选择覆盖字段" }]}
        >
          <Select options={TARGET_FIELD_OPTIONS.map((item) => ({ value: item.value, label: item.label }))} />
        </Form.Item>

        <Form.Item<FusionRuleFormValues>
          label="覆盖金额"
          name="overrideValue"
          rules={[{ required: true, message: "请输入覆盖金额" }]}
        >
          <InputNumber
            min={0}
            precision={2}
            step={0.01}
            style={{ width: "100%" }}
            placeholder="例如：88.50"
          />
        </Form.Item>

        <Form.Item<FusionRuleFormValues> label="备注" name="note">
          <Input.TextArea rows={3} placeholder="记录规则用途或来源" />
        </Form.Item>
      </Form>
    </Drawer>
  );
}
