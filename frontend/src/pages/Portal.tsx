import { useMemo } from 'react';
import { Link } from 'react-router-dom';
import { Button, Card, Col, Row, Typography } from 'antd';
import {
  AppstoreOutlined,
  CloudUploadOutlined,
  DashboardOutlined,
  SearchOutlined,
  TeamOutlined,
  UserOutlined,
} from '@ant-design/icons';

import { useSemanticColors } from '../theme/useSemanticColors';

const { Title, Text, Paragraph } = Typography;

const DIRECT_LINKS = [
  { to: '/aggregate', label: '快速聚合', hint: '保留原有上传即导出双模板能力', icon: <CloudUploadOutlined /> },
  { to: '/dashboard', label: '处理看板', hint: '查看状态分布、最近批次与异常', icon: <DashboardOutlined /> },
  { to: '/employees', label: '员工主档', hint: '导入、维护与审计员工主数据', icon: <SearchOutlined /> },
];

export function ManagementPortalPage() {
  const colors = useSemanticColors();

  const ROLE_CARDS = useMemo(() => [
    {
      to: '/workspace/admin',
      icon: <AppstoreOutlined style={{ fontSize: 28, color: colors.BRAND }} />,
      title: '管理员入口',
      description: '查看全链路运行状态，维护模板、映射、导入批次、员工主档与月度比对。',
      bullets: ['总览看板与异常治理', '导入批次、映射修正、员工主档', '导出结果与月度对比'],
    },
    {
      to: '/workspace/hr',
      icon: <TeamOutlined style={{ fontSize: 28, color: colors.BRAND }} />,
      title: 'HR 入口',
      description: '聚焦每月实操链路，从上传、校验、匹配到双模板导出都能在一个工作台里完成。',
      bullets: ['快速聚合与批次追踪', '校验匹配与导出检查', '员工自助查询入口转发'],
    },
    {
      to: '/employee/query',
      icon: <UserOutlined style={{ fontSize: 28, color: colors.BRAND }} />,
      title: '员工查询入口',
      description: '无需登录，只需输入姓名和身份证号即可查看最近的社保公积金记录。',
      bullets: ['姓名 + 身份证号查询', '查看最近批次与金额摘要', '适合员工自助核对'],
    },
  ], [colors.BRAND]);

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto', padding: '32px 24px' }}>
      <div style={{ textAlign: 'center', marginBottom: 48 }}>
        <Text type="secondary">Social Security & Housing Fund Management</Text>
        <Title level={2} style={{ marginTop: 8 }}>社保公积金管理系统</Title>
        <Paragraph type="secondary" style={{ maxWidth: 640, margin: '0 auto' }}>
          保留原有社保表格聚合、规则识别、校验匹配、双模板导出与月度对比能力，同时新增管理员、HR 和员工自助查询三类入口。
        </Paragraph>
        <div style={{ display: 'flex', gap: 12, justifyContent: 'center', marginTop: 24 }}>
          <Link to="/workspace/admin">
            <Button type="primary" size="large">进入管理员工作台</Button>
          </Link>
          <Link to="/employee/query">
            <Button size="large">员工免登录查询</Button>
          </Link>
        </div>
      </div>

      <Row gutter={[24, 24]} style={{ marginBottom: 48 }}>
        {ROLE_CARDS.map((item) => (
          <Col xs={24} md={8} key={item.to}>
            <Link to={item.to} style={{ display: 'block' }}>
              <Card hoverable style={{ height: '100%' }}>
                <div style={{ marginBottom: 12 }}>{item.icon}</div>
                <Title level={5}>{item.title}</Title>
                <Paragraph type="secondary">{item.description}</Paragraph>
                <ul style={{ paddingLeft: 16, margin: 0 }}>
                  {item.bullets.map((bullet) => (
                    <li key={bullet}>
                      <Text type="secondary" style={{ fontSize: 13 }}>{bullet}</Text>
                    </li>
                  ))}
                </ul>
              </Card>
            </Link>
          </Col>
        ))}
      </Row>

      <Card>
        <Row gutter={[24, 16]} align="middle">
          <Col xs={24} md={8}>
            <Text type="secondary">Legacy Workflow</Text>
            <Title level={5} style={{ marginTop: 4 }}>原有页面保持不变</Title>
            <Paragraph type="secondary" style={{ marginBottom: 0 }}>
              如果你已经习惯原来的工作方式，仍然可以直接进入聚合、看板、批次管理、结果校验和导出页面。
            </Paragraph>
          </Col>
          <Col xs={24} md={16}>
            <Row gutter={[16, 16]}>
              {DIRECT_LINKS.map((item) => (
                <Col xs={24} sm={8} key={item.to}>
                  <Link to={item.to}>
                    <Card size="small" hoverable>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                        {item.icon}
                        <Text strong>{item.label}</Text>
                      </div>
                      <Text type="secondary" style={{ fontSize: 12 }}>{item.hint}</Text>
                    </Card>
                  </Link>
                </Col>
              ))}
            </Row>
          </Col>
        </Row>
      </Card>
    </div>
  );
}
