import { useState, useMemo, useRef, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Input, Card, Row, Col, Typography, Switch, Empty, theme } from 'antd';
import { SunOutlined, MoonOutlined } from '@ant-design/icons';

import { useAuth } from '../hooks/useAuth';
import { useFeishuFeatureFlag } from '../hooks/useFeishuFeatureFlag';
import { useThemeMode } from '../theme/useThemeMode';

const { Title, Text } = Typography;

interface SettingsCardConfig {
  key: string;
  title: string;
  description: string;
  keywords: string[];
  linkTo?: string;
  roles: string[];
  feishuOnly?: boolean;
}

const SETTINGS_CARDS: SettingsCardConfig[] = [
  {
    key: 'theme',
    title: '外观设置',
    description: '切换亮色/暗黑主题模式',
    keywords: ['主题', '外观', '暗黑', '亮色', 'dark', 'light', '模式'],
    roles: ['admin', 'hr'],
  },
  {
    key: 'audit',
    title: '审计日志',
    description: '查看系统操作记录和用户行为追踪',
    keywords: ['日志', '审计', '操作记录', '行为'],
    linkTo: '/audit-logs',
    roles: ['admin'],
  },
  {
    key: 'api-keys',
    title: 'API 密钥',
    description: '管理 DeepSeek 等外部服务 API 密钥',
    keywords: ['密钥', 'API', 'DeepSeek', '外部服务'],
    linkTo: '/api-keys',
    roles: ['admin'],
  },
  {
    key: 'feishu',
    title: '飞书集成',
    description: '飞书同步和文档映射配置',
    keywords: ['飞书', '同步', '集成', '文档映射'],
    linkTo: '/feishu-settings',
    roles: ['admin'],
    feishuOnly: true,
  },
];

function highlightText(text: string, keyword: string, highlightBg: string): React.ReactNode {
  if (!keyword) return text;
  const lowerText = text.toLowerCase();
  const lowerKeyword = keyword.toLowerCase();
  const parts: React.ReactNode[] = [];
  let lastIndex = 0;
  let index = lowerText.indexOf(lowerKeyword, lastIndex);
  let partKey = 0;
  while (index !== -1) {
    if (index > lastIndex) {
      parts.push(text.slice(lastIndex, index));
    }
    parts.push(
      <mark key={partKey++} style={{ background: highlightBg, padding: 0, borderRadius: 2 }}>
        {text.slice(index, index + keyword.length)}
      </mark>,
    );
    lastIndex = index + keyword.length;
    index = lowerText.indexOf(lowerKeyword, lastIndex);
  }
  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex));
  }
  return parts.length > 0 ? <>{parts}</> : text;
}

export default function SettingsPage() {
  const { user } = useAuth();
  const { feishu_sync_enabled } = useFeishuFeatureFlag();
  const { isDark, toggleMode } = useThemeMode();
  const { token } = theme.useToken();
  const [searchTerm, setSearchTerm] = useState('');
  const cardRefs = useRef<Record<string, HTMLDivElement | null>>({});

  const userRole = user?.role || '';

  const visibleCards = useMemo(() => {
    return SETTINGS_CARDS.filter((card) => {
      if (!card.roles.includes(userRole)) return false;
      if (card.feishuOnly && !feishu_sync_enabled) return false;
      if (!searchTerm) return true;
      const term = searchTerm.toLowerCase();
      return (
        card.title.toLowerCase().includes(term) ||
        card.description.toLowerCase().includes(term) ||
        card.keywords.some((k) => k.toLowerCase().includes(term))
      );
    });
  }, [userRole, feishu_sync_enabled, searchTerm]);

  // Auto-scroll to first matching card on search
  useEffect(() => {
    if (searchTerm && visibleCards.length > 0) {
      const firstKey = visibleCards[0].key;
      const el = cardRefs.current[firstKey];
      if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }
    }
  }, [searchTerm, visibleCards]);

  const highlightBg = token.colorWarningBg;

  return (
    <div>
      <Title level={3}>系统设置</Title>
      <Input.Search
        placeholder="搜索设置项..."
        allowClear
        onChange={(e) => setSearchTerm(e.target.value)}
        style={{ maxWidth: 400, marginBottom: 24 }}
      />
      {visibleCards.length === 0 && searchTerm ? (
        <Empty
          description={
            <div>
              <div>未找到匹配的设置项</div>
              <Text type="secondary">请尝试其他关键词</Text>
            </div>
          }
        />
      ) : (
        <Row gutter={[24, 24]}>
          {visibleCards.map((card, idx) => (
            <Col xs={24} md={12} lg={8} key={card.key}>
              <div
                ref={(el) => {
                  cardRefs.current[card.key] = el;
                }}
              >
                <Card
                  title={highlightText(card.title, searchTerm, highlightBg)}
                  style={
                    idx === 0 && searchTerm
                      ? { boxShadow: `0 0 0 2px ${token.colorPrimary}` }
                      : undefined
                  }
                >
                  <p>{highlightText(card.description, searchTerm, highlightBg)}</p>
                  {card.key === 'theme' && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <SunOutlined />
                      <Switch checked={isDark} onChange={toggleMode} />
                      <MoonOutlined />
                      <Text type="secondary">
                        {isDark ? '暗黑模式' : '亮色模式'}
                      </Text>
                    </div>
                  )}
                  {card.linkTo && (
                    <Link to={card.linkTo} style={{ color: token.colorPrimary }}>
                      前往
                    </Link>
                  )}
                </Card>
              </div>
            </Col>
          ))}
        </Row>
      )}
    </div>
  );
}
