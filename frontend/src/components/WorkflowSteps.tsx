import { Steps, Card } from 'antd';
import {
  UploadOutlined,
  DashboardOutlined,
  CheckCircleOutlined,
  ExportOutlined,
} from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAggregateSession } from '../hooks/useAggregateSession';
import type { AggregateSessionSnapshot } from '../services/aggregateSessionStore';

const WORKFLOW_STEPS = [
  { title: '\u4E0A\u4F20\u6587\u4EF6', path: '/aggregate', icon: <UploadOutlined /> },
  { title: '\u89E3\u6790\u5904\u7406', path: '/dashboard', icon: <DashboardOutlined /> },
  { title: '\u6821\u9A8C\u5339\u914D', path: '/results', icon: <CheckCircleOutlined /> },
  { title: '\u5BFC\u51FA\u7ED3\u679C', path: '/exports', icon: <ExportOutlined /> },
] as const;

type StepStatus = 'finish' | 'process' | 'error' | 'wait';

function getStepStatus(
  stepIndex: number,
  currentStepIndex: number,
  session: AggregateSessionSnapshot,
): StepStatus {
  if (stepIndex === currentStepIndex) return 'process';

  const { status, progress } = session;

  if (status === 'idle') return 'wait';

  const stage = progress?.stage ?? '';
  const PARSE_STAGES = ['social_import', 'housing_import', 'matching', 'validation', 'export'];
  const VALIDATE_STAGES = ['matching', 'validation', 'export'];

  if (status === 'failed' || status === 'cancelled') {
    if (stepIndex < currentStepIndex) return 'finish';
    return 'wait';
  }

  if (stepIndex === 0) {
    return (status === 'running' || status === 'completed') ? 'finish' : 'wait';
  }

  if (stepIndex === 1) {
    if (status === 'completed') return 'finish';
    if (status === 'running' && PARSE_STAGES.includes(stage)) return 'finish';
    return stepIndex < currentStepIndex ? 'finish' : 'wait';
  }

  if (stepIndex === 2) {
    if (status === 'completed') return 'finish';
    if (status === 'running' && VALIDATE_STAGES.includes(stage)) return 'finish';
    return stepIndex < currentStepIndex ? 'finish' : 'wait';
  }

  if (stepIndex === 3) {
    return status === 'completed' ? 'finish' : 'wait';
  }

  return 'wait';
}

export function WorkflowSteps() {
  const navigate = useNavigate();
  const location = useLocation();
  const session = useAggregateSession();

  const currentStepIndex = WORKFLOW_STEPS.findIndex(
    (step) => location.pathname === step.path,
  );

  return (
    <Card style={{ marginBottom: 16 }} styles={{ body: { padding: '12px 24px' } }}>
      <Steps
        size="small"
        current={currentStepIndex >= 0 ? currentStepIndex : 0}
        onChange={(stepIndex) => navigate(WORKFLOW_STEPS[stepIndex].path)}
        items={WORKFLOW_STEPS.map((step, index) => ({
          title: step.title,
          icon: step.icon,
          status: getStepStatus(index, currentStepIndex >= 0 ? currentStepIndex : 0, session),
        }))}
      />
    </Card>
  );
}
