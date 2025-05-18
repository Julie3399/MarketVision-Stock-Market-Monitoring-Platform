import React from 'react';
import { Button, Tooltip } from 'antd';
import { UndoOutlined } from '@ant-design/icons';

interface FolderOperationsProps {
  onUndo: () => void;
  style?: React.CSSProperties;
}

export const FolderOperations: React.FC<FolderOperationsProps> = ({ onUndo, style }) => {
  return (
    <Tooltip title="Undo last equity distribution or financing operation">
      <Button
        type="link"
        icon={<UndoOutlined />}
        size="middle"
        onClick={onUndo}
        style={{
          padding: '4px 8px',
          color: '#1890ff',
          ...style
        }}
      />
    </Tooltip>
  );
};
