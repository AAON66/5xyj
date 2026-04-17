import { useState, useMemo, useRef, useEffect, useCallback } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { Input, Card, Row, Col, Typography, Switch, Empty, Button, Tag, Modal, App, theme } from 'antd';
import { SunOutlined, MoonOutlined } from '@ant-design/icons';

import { useAuth } from '../hooks/useAuth';
import { useFeishuFeatureFlag } from '../hooks/useFeishuFeatureFlag';
import { useThemeMode } from '../theme/useThemeMode';
import { fetchBindAuthorizeUrl, unbindFeishu, feishuBindCallback } from '../services/feishu';
import type { ApiSuccessResponse } from '../services/api';
import { apiClient } from '../services/api';

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
    key: 'feishu-bind',
    title: '飞书账号绑定',
    description: '绑定或解绑飞书账号，绑定后可使用飞书快捷登录',
    keywords: ['飞书', '绑定', '账号', '解绑', 'feishu'],
    roles: ['admin', 'hr', 'employee'],
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

interface MeFeishuInfo {
  feishu_bound: boolean;
  feishu_display_name: string | null;
}

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
  const { message: messageApi } = App.useApp();
  const [searchTerm, setSearchTerm] = useState('');
  const cardRefs = useRef<Record<string, HTMLDivElement | null>>({});
  const [searchParams, setSearchParams] = useSearchParams();

  // Feishu bind state
  const [feishuBound, setFeishuBound] = useState(false);
  const [feishuDisplayName, setFeishuDisplayName] = useState<string | null>(null);
  const [bindLoading, setBindLoading] = useState(false);
  const bindCallbackProcessed = useRef(false);

  const userRole = user?.role || '';

  // Fetch feishu bind status from /auth/me
  const fetchFeishuStatus = useCallback(async () => {
    try {
      const response = await apiClient.get<ApiSuccessResponse<MeFeishuInfo>>('/auth/me');
      const data = response.data.data;
      setFeishuBound(!!data.feishu_bound);
      setFeishuDisplayName(data.feishu_display_name ?? null);
    } catch {
      // If the endpoint doesn't return these fields yet, leave defaults
    }
  }, []);

  useEffect(() => {
    void fetchFeishuStatus();
  }, [fetchFeishuStatus]);

  // Handle bind callback: check URL params for code + state + action=bind
  useEffect(() => {
    if (bindCallbackProcessed.current) return;
    const code = searchParams.get('code');
    const state = searchParams.get('state');
    const action = searchParams.get('action');
    if (code && state && action === 'bind') {
      bindCallbackProcessed.current = true;
      setBindLoading(true);
      feishuBindCallback(code, state)
        .then((result) => {
          setFeishuBound(true);
          setFeishuDisplayName(result.feishu_name);
          messageApi.success('飞书账号绑定成功');
          // Clean up URL params
          setSearchParams({}, { replace: true });
        })
        .catch(() => {
          messageApi.error('飞书账号绑定失败，请重试');
        })
        .finally(() => {
          setBindLoading(false);
        });
    }
  }, [searchParams, setSearchParams, messageApi]);

  // Handle bind click
  const handleBindFeishu = async () => {
    setBindLoading(true);
    try {
      const url = await fetchBindAuthorizeUrl();
      window.location.href = url;
    } catch {
      messageApi.error('获取飞书授权链接失败');
      setBindLoading(false);
    }
  };

  // Handle unbind click
  const handleUnbindFeishu = () => {
    Modal.confirm({
      title: '解绑飞书账号',
      content: '确定要解绑飞书账号吗？解绑后将无法使用飞书快捷登录。',
      okText: '确定解绑',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        setBindLoading(true);
        try {
          await unbindFeishu();
          setFeishuBound(false);
          setFeishuDisplayName(null);
          messageApi.success('已成功解绑飞书账号');
        } catch {
          messageApi.error('解绑失败，请重试');
        } finally {
          setBindLoading(false);
        }
      },
    });
  };

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

  const renderFeishuBindContent = () => {
    if (feishuBound) {
      return (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
          <Tag color="success">已绑定</Tag>
          {feishuDisplayName && <Text strong>{feishuDisplayName}</Text>}
          <Button
            type="text"
            danger
            size="small"
            loading={bindLoading}
            onClick={handleUnbindFeishu}
          >
            解绑
          </Button>
        </div>
      );
    }
    return (
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <Text type="secondary">未绑定飞书账号</Text>
        <Button
          type="primary"
          size="small"
          loading={bindLoading}
          onClick={handleBindFeishu}
        >
          绑定飞书
        </Button>
      </div>
    );
  };

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
                  {card.key === 'feishu-bind' && renderFeishuBindContent()}
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
