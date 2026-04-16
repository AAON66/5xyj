import { List, Modal, Typography } from 'antd';
import type { Candidate } from '../services/feishu';

const { Text } = Typography;

export interface CandidateSelectModalProps {
  open: boolean;
  candidates: Candidate[];
  feishuName: string;
  loading: boolean;
  onSelect: (employeeMasterId: string) => void;
  onCancel: () => void;
}

export function CandidateSelectModal({
  open,
  candidates,
  feishuName,
  loading,
  onSelect,
  onCancel,
}: CandidateSelectModalProps) {
  return (
    <Modal
      title="选择您的身份"
      open={open}
      onCancel={onCancel}
      footer={null}
      maskClosable={!loading}
      closable={!loading}
    >
      <Text style={{ display: 'block', marginBottom: 16 }}>
        系统发现多个与「{feishuName}」同名的员工，请选择您的身份以完成绑定：
      </Text>
      <List
        dataSource={candidates}
        renderItem={(item) => (
          <List.Item
            style={{ cursor: loading ? 'not-allowed' : 'pointer' }}
            onClick={() => {
              if (!loading) {
                onSelect(item.employee_master_id);
              }
            }}
          >
            <List.Item.Meta
              title={item.person_name}
              description={`${item.department} | 工号 ${item.employee_id_masked}`}
            />
          </List.Item>
        )}
      />
    </Modal>
  );
}
