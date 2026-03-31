import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Button,
  Card,
  Form,
  Input,
  message,
  Select,
  Space,
  Switch,
  Typography,
} from 'antd';

import { normalizeApiError } from '../services/api';
import { createEmployeeMaster, fetchRegions } from '../services/employees';

const { Title } = Typography;

interface CreateEmployeeFormValues {
  employee_id: string;
  person_name: string;
  id_number?: string;
  company_name?: string;
  department?: string;
  region?: string;
  active: boolean;
}

export function EmployeeCreatePage() {
  const navigate = useNavigate();
  const [form] = Form.useForm<CreateEmployeeFormValues>();
  const [saving, setSaving] = useState(false);
  const [regions, setRegions] = useState<string[]>([]);

  useEffect(() => {
    fetchRegions().then(setRegions).catch(() => {});
  }, []);

  async function handleSubmit(values: CreateEmployeeFormValues) {
    setSaving(true);

    try {
      const created = await createEmployeeMaster({
        employee_id: values.employee_id.trim(),
        person_name: values.person_name.trim(),
        id_number: values.id_number?.trim() || null,
        company_name: values.company_name?.trim() || null,
        department: values.department?.trim() || null,
        region: values.region?.trim() || null,
        active: values.active ?? true,
      });
      message.success(`员工 ${created.employee_id} 已创建成功`);
      // Preserve company/department/region for next entry
      const keepValues = {
        company_name: values.company_name,
        department: values.department,
        region: values.region,
      };
      form.resetFields();
      form.setFieldsValue({ ...keepValues, active: true });
    } catch (error) {
      message.error(normalizeApiError(error).message || '新增员工主档失败');
    } finally {
      setSaving(false);
    }
  }

  return (
    <div>
      <Title level={4}>新增员工</Title>

      <Card>
        <Form<CreateEmployeeFormValues>
          form={form}
          layout="vertical"
          onFinish={(values) => void handleSubmit(values)}
          initialValues={{ active: true }}
          style={{ maxWidth: 600 }}
        >
          <Form.Item
            label="工号"
            name="employee_id"
            rules={[{ required: true, message: '请输入工号' }]}
          >
            <Input placeholder="例如：E1024" />
          </Form.Item>

          <Form.Item
            label="姓名"
            name="person_name"
            rules={[{ required: true, message: '请输入姓名' }]}
          >
            <Input placeholder="例如：张三" />
          </Form.Item>

          <Form.Item label="身份证号" name="id_number">
            <Input placeholder="可选" />
          </Form.Item>

          <Form.Item label="公司主体" name="company_name">
            <Input placeholder="可选" />
          </Form.Item>

          <Form.Item label="部门" name="department">
            <Input placeholder="可选" />
          </Form.Item>

          <Form.Item label="地区" name="region">
            <Select
              placeholder="请选择地区"
              allowClear
              options={regions.map((r) => ({ label: r, value: r }))}
            />
          </Form.Item>

          <Form.Item label="在职状态" name="active" valuePropName="checked">
            <Switch checkedChildren="在职" unCheckedChildren="停用" />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button
                type="primary"
                htmlType="submit"
                loading={saving}
              >
                创建员工主档
              </Button>
              <Button onClick={() => navigate('/employees')}>
                返回列表
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
}
