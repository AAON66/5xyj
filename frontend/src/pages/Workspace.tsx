import { Link } from 'react-router-dom';
import { Button, Card, Col, Row, Typography } from 'antd';
import {
  AppstoreOutlined,
  AuditOutlined,
  BarChartOutlined,
  CloudUploadOutlined,
  DiffOutlined,
  ExportOutlined,
  FileSearchOutlined,
  HomeOutlined,
  NodeIndexOutlined,
  SearchOutlined,
  SolutionOutlined,
  TeamOutlined,
  UnorderedListOutlined,
  UserOutlined,
} from '@ant-design/icons';
import type { ReactNode } from 'react';

import { useSemanticColors } from '../theme/useSemanticColors';

const { Title, Text, Paragraph } = Typography;

type WorkspaceRole = 'admin' | 'hr';

interface WorkspaceLink {
  to: string;
  title: string;
  hint: string;
  icon: ReactNode;
}

const WORKSPACE_CONFIG: Record<
  WorkspaceRole,
  {
    title: string;
    description: string;
    primaryAction: { to: string; title: string };
    secondaryAction: { to: string; title: string };
    sections: Array<{ title: string; icon: ReactNode; links: WorkspaceLink[] }>;
  }
> = {
  admin: {
    title: '管理员工作台',
    description: '管理员负责总览、治理和配置。这里把全链路页面重新编排成一个更适合运营管理的入口。',
    primaryAction: { to: '/aggregate', title: '进入快速聚合' },
    secondaryAction: { to: '/dashboard', title: '查看处理看板' },
    sections: [
      {
        title: '治理与总览',
        icon: <BarChartOutlined />,
        links: [
          { to: '/dashboard', title: '处理看板', hint: '批次总览、异常统计与状态分布', icon: <AppstoreOutlined /> },
          { to: '/compare', title: '月度对比', hint: '查看左右差异并在线修正', icon: <DiffOutlined /> },
          { to: '/exports', title: '导出结果', hint: '核查薪酬模板与工具表产物', icon: <ExportOutlined /> },
        ],
      },
      {
        title: '基础数据',
        icon: <UnorderedListOutlined />,
        links: [
          { to: '/employees', title: '员工主档', hint: '导入、维护和审计主数据', icon: <TeamOutlined /> },
          { to: '/mappings', title: '映射修正', hint: '处理低置信度字段映射', icon: <NodeIndexOutlined /> },
          { to: '/imports', title: '批次管理', hint: '钻取到源文件、表头和明细行', icon: <FileSearchOutlined /> },
          { to: '/audit-logs', title: '审计日志', hint: '查看系统操作记录和安全事件', icon: <AuditOutlined /> },
        ],
      },
    ],
  },
  hr: {
    title: 'HR 工作台',
    description: 'HR 更关心每月经办效率，所以入口聚焦上传、校验、匹配、导出和员工答疑。',
    primaryAction: { to: '/aggregate', title: '开始当月聚合' },
    secondaryAction: { to: '/results', title: '查看校验匹配' },
    sections: [
      {
        title: '月度处理',
        icon: <CloudUploadOutlined />,
        links: [
          { to: '/aggregate', title: '快速聚合', hint: '默认入口，适合常规月度处理', icon: <CloudUploadOutlined /> },
          { to: '/results', title: '校验匹配', hint: '查看缺失、异常和匹配情况', icon: <SearchOutlined /> },
          { to: '/exports', title: '导出结果', hint: '确认两份固定模板都已生成', icon: <ExportOutlined /> },
        ],
      },
      {
        title: '辅助入口',
        icon: <SolutionOutlined />,
        links: [
          { to: '/imports', title: '批次管理', hint: '需要回溯时查看原始文件和解析详情', icon: <FileSearchOutlined /> },
          { to: '/employees', title: '员工主档', hint: '补录或更新员工信息', icon: <TeamOutlined /> },
          { to: '/employee/query', title: '员工查询入口', hint: '转给员工自助核对本月记录', icon: <UserOutlined /> },
        ],
      },
    ],
  },
};

function WorkspacePage({ role }: { role: WorkspaceRole }) {
  const config = WORKSPACE_CONFIG[role];
  const colors = useSemanticColors();

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <Title level={4}>{config.title}</Title>
        <Paragraph type="secondary">{config.description}</Paragraph>
        <div style={{ display: 'flex', gap: 12 }}>
          <Link to={config.primaryAction.to}>
            <Button type="primary" size="large">{config.primaryAction.title}</Button>
          </Link>
          <Link to={config.secondaryAction.to}>
            <Button size="large">{config.secondaryAction.title}</Button>
          </Link>
          <Link to="/">
            <Button icon={<HomeOutlined />}>返回系统门户</Button>
          </Link>
        </div>
      </div>

      {config.sections.map((section) => (
        <div key={section.title} style={{ marginBottom: 24 }}>
          <Title level={5} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            {section.icon}
            {section.title}
          </Title>
          <Row gutter={[16, 16]}>
            {section.links.map((item) => (
              <Col xs={24} sm={12} md={8} key={item.to}>
                <Link to={item.to} style={{ display: 'block' }}>
                  <Card hoverable>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
                      <span style={{ fontSize: 20, color: colors.BRAND }}>{item.icon}</span>
                      <Text strong>{item.title}</Text>
                    </div>
                    <Text type="secondary">{item.hint}</Text>
                  </Card>
                </Link>
              </Col>
            ))}
          </Row>
        </div>
      ))}
    </div>
  );
}

export function AdminWorkspacePage() {
  return <WorkspacePage role="admin" />;
}

export function HrWorkspacePage() {
  return <WorkspacePage role="hr" />;
}
