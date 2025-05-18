import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Select, Spin, message, Layout, Menu, Input, Button, Modal, Form, Dropdown, Space, notification, Badge, AutoComplete, DatePicker, Tree, Tooltip } from 'antd';
import { PlusOutlined, DeleteOutlined, FolderOutlined, MoreOutlined, AlertOutlined, StockOutlined, ExpandOutlined, CompressOutlined, EditOutlined, ReloadOutlined } from '@ant-design/icons';
import { AdvancedRealTimeChart } from 'react-ts-tradingview-widgets';
import type { CardProps } from 'antd';
import StockAnalysis from './StockAnalysis';
import dayjs from 'dayjs';
import type { RangePickerProps } from 'antd/es/date-picker';
import type { DataNode, TreeProps, EventDataNode } from 'antd/es/tree';
import type { Key } from 'rc-tree/lib/interface';
import type { MenuProps } from 'antd';
import { StockSearch } from './StockSearch';

const { Sider, Content } = Layout;
const { Search, TextArea } = Input;

interface StockCardProps {
  symbol: string;
  timeframe: "1" | "3" | "5" | "15" | "30" | "60" | "120" | "180" | "240" | "D" | "W" | "BACKTEST";
  backTestRange?: [dayjs.Dayjs | null, dayjs.Dayjs | null];
}

interface StockGroup {
  description: string;
  stocks: string[];
  subGroups?: { [key: string]: StockGroup };  // Add sub-folders
}

interface GroupData {
  [key: string]: StockGroup;
}

interface AlertData {
  type: string;
  message: string;
  value: number;
  threshold: number;
}

// 添加 WatchlistData 接口
interface WatchlistData {
  groups: {
    [key: string]: StockGroup;
  };
}

const timeframeOptions = [
  { label: 'History', options: [
    { value: "D", label: 'Daily' },
    { value: "W", label: 'Weekly' }
  ]},
];

const StockCard: React.FC<StockCardProps> = ({ symbol, timeframe, backTestRange }) => {
  const [note, setNote] = useState<string>("");
  const [isEditingNote, setIsEditingNote] = useState(false);
  const [editedNote, setEditedNote] = useState<string>("");
  const noteEditorRef = React.useRef<HTMLDivElement>(null);
  const analysisColRef = React.useRef<HTMLDivElement>(null);

  // Function to calculate editor window position
  const calculateEditorPosition = () => {
    if (analysisColRef.current) {
      const rect = analysisColRef.current.getBoundingClientRect();
      return {
        top: rect.top - 210, // 20px above analysis report
        left: rect.left,
      };
    }
    return null;
  };

  // Handle clicks outside the editor
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (noteEditorRef.current && !noteEditorRef.current.contains(event.target as Node)) {
        setIsEditingNote(true);  
      }
    };

    if (isEditingNote) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isEditingNote]);

  // Fetch note
  useEffect(() => {
    const fetchNote = async () => {
      try {
        const response = await fetch(`${process.env.REACT_APP_API_URL}/api/stock/note/${symbol}`);
        if (response.ok) {
          const data = await response.json();
          setNote(data.note);
        }
      } catch (error) {
        console.error('Failed to fetch note:', error);
      }
    };
    fetchNote();
  }, [symbol]);

  // Update note
  const updateNote = async (newNote: string) => {
    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL}/api/stock/note`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          symbol,
          note: newNote,
        }),
      });

      if (response.ok) {
        setNote(newNote);
        message.success('Note updated');
      } else {
        message.error('Failed to update note');
      }
    } catch (error) {
      console.error('Failed to update note:', error);
      message.error('Failed to update note');
    }
  };

  // Handle note edit
  const handleNoteEdit = () => {
    setEditedNote(note);
    setIsEditingNote(true);
  };

  // Handle note save
  const handleNoteSave = () => {
    updateNote(editedNote);
    setIsEditingNote(false);
  };

  // Function to auto adjust height
  const autoAdjustHeight = (element: HTMLTextAreaElement) => {
    element.style.height = 'auto';
    element.style.height = `${element.scrollHeight}px`;
  };

  const getChartRange = () => {
    if (timeframe === "BACKTEST" && backTestRange && backTestRange[0] && backTestRange[1]) {
      const diffDays = backTestRange[1].diff(backTestRange[0], 'day');
      if (diffDays <= 30) return "1M";
      if (diffDays <= 90) return "3M";
      if (diffDays <= 180) return "6M";
      return "12M";
    }
    return timeframe === "D" ? "12M" : 
           timeframe === "W" ? "60M" : "1D";
  };

  // Calculate start and end time
  const getFromTo = () => {
    if (timeframe === "BACKTEST" && backTestRange && backTestRange[0] && backTestRange[1]) {
      return {
        from: backTestRange[0].format('YYYY-MM-DD'),
        to: backTestRange[1].format('YYYY-MM-DD')
      };
    }
    return undefined;
  };

  const dateRange = getFromTo();

  return (
    <Card 
      title={
        <div style={{ 
          display: 'flex', 
          alignItems: 'center', 
          position: 'relative',
          justifyContent: 'center',
          minHeight: '32px'
        }}>
          <span style={{ 
            position: 'absolute',
            left: '50%',
            transform: 'translateX(-50%)',
            fontWeight: 500
          }}>{symbol}</span>
          <div style={{ position: 'absolute', right: 0 }}>
            {isEditingNote ? (
              <div 
                ref={noteEditorRef}
                style={{ 
                  position: 'fixed',
                  zIndex: 1000,
                  background: 'white',
                  padding: '16px',
                  borderRadius: '8px',
                  boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
                  width: '400px',
                  maxWidth: '90vw',
                  transition: 'all 0.3s ease',
                  border: '1px solid #f0f0f0',
                  ...(calculateEditorPosition() || {})
                }}
              >
                <div style={{ 
                  marginBottom: '12px', 
                  fontWeight: 500,
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px'
                }}>
                  <span>Edit Note</span>
                  <span style={{ 
                    color: '#1890ff', 
                    backgroundColor: '#e6f7ff', 
                    padding: '2px 8px', 
                    borderRadius: '4px',
                    fontSize: '14px'
                  }}>
                    {symbol}
                  </span>
                </div>
                <TextArea
                  value={editedNote}
                  onChange={(e) => {
                    setEditedNote(e.target.value);
                    // Auto adjust height
                    const textarea = e.target as HTMLTextAreaElement;
                    textarea.style.height = 'auto';
                    textarea.style.height = `${textarea.scrollHeight}px`;
                  }}
                  placeholder="Enter note here..."
                  autoFocus
                  autoSize={{ minRows: 3 }}
                  style={{ 
                    resize: 'none',
                    border: '1px solid #d9d9d9',
                    borderRadius: '4px',
                    width: '100%',
                    fontSize: '14px',
                    lineHeight: '1.6',
                    padding: '8px 12px',
                    maxHeight: '60vh',
                    overflowY: 'auto'
                  }}
                />
                <div style={{ 
                  marginTop: '12px',
                  display: 'flex',
                  justifyContent: 'flex-end',
                  gap: '8px'
                }}>
                  <Button onClick={() => setIsEditingNote(false)}>
                    Cancel
                  </Button>
                  <Button type="primary" onClick={handleNoteSave}>
                    Save
                  </Button>
                </div>
              </div>
            ) : (
              <Tooltip title={note || 'Click to add note'} placement="topRight">
                <div
                  onClick={handleNoteEdit}
                  style={{
                    cursor: 'pointer',
                    color: '#666',
                    fontSize: '14px',
                    maxWidth: 500,
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                    textAlign: 'right'
                  }}
                >
                  {note ? note.split('\n')[0].slice(0, 30) + (note.split('\n')[0].length > 30 ? '...' : '') : '+ Add Note'}
                </div>
              </Tooltip>
            )}
          </div>
        </div>
      }
      style={{ marginBottom: 16 }}
      bodyStyle={{ padding: '12px' }}
    >
      <Row gutter={16}>
        <Col span={16}>
          <div style={{ height: 400 }}>
            <AdvancedRealTimeChart
              symbol={symbol}
              interval={timeframe === "BACKTEST" ? "D" : timeframe}
              theme="light"
              width="100%"
              height={400}
              allow_symbol_change={true}
              hide_side_toolbar={false}
              range={getChartRange()}
              timezone="America/New_York"
            />
          </div>
        </Col>
        <Col span={8} ref={analysisColRef} style={{ maxHeight: 400, overflowY: 'auto' }}>
          <StockAnalysis symbol={symbol} />
        </Col>
      </Row>
    </Card>
  );
};
const StockDashboard: React.FC = () => {
  const [watchlist, setWatchlist] = useState<WatchlistData>({ groups: {} });
  const [loading, setLoading] = useState(true);
  const [selectedStock, setSelectedStock] = useState<string | null>(null);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [form] = Form.useForm();
  const [expandedKeys, setExpandedKeys] = useState<string[]>([]);
  const [timeframe, setTimeframe] = useState<StockCardProps['timeframe']>("D");
  const [selectedKeys, setSelectedKeys] = useState<Key[]>([]);

  // Add ref mapping to store references to each stock card
  const stockRefs = React.useRef<{ [key: string]: HTMLDivElement | null }>({});

  // Function to scroll to specified stock
  const scrollToStock = (symbol: string) => {
    const element = stockRefs.current[symbol];
    if (element) {
      element.scrollIntoView({ 
        behavior: 'smooth',
        block: 'start'
      });
    }
  };

  // Get watchlist
  const fetchWatchlist = async () => {
    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL}/api/watchlist`);
      if (!response.ok) {
        throw new Error('Failed to fetch watchlist');
      }
      const data = await response.json();
      
      // Completely replace existing watchlist state
      setWatchlist({ groups: data.groups || {} });
      
      // Clear stockRefs
      stockRefs.current = {};
      
      // Clear selection state
      setSelectedStock(null);
      setSelectedKeys([]);
      
      // Expand all groups by default
      setExpandedKeys(getAllFolderKeys(data.groups));
    } catch (error) {
      console.error('Failed to fetch watchlist:', error);
      message.error('Failed to fetch watchlist');
    } finally {
      setLoading(false);
    }
  };

  React.useEffect(() => {
    fetchWatchlist();
  }, []);

  // Get all unique stocks
  const getAllStocks = () => {
    const allStocks = new Set<string>();
    
    const addStocksFromGroup = (group: StockGroup) => {
      // Add stocks from current group
      group.stocks.forEach(stock => allStocks.add(stock));
      
      // Recursively process subgroups
      if (group.subGroups) {
        Object.values(group.subGroups).forEach(subGroup => {
          addStocksFromGroup(subGroup);
        });
      }
    };
    
    Object.values(watchlist.groups).forEach(group => {
      addStocksFromGroup(group);
    });
    
    return Array.from(allStocks);
  };

  // Get grouped stocks
  const getGroupedStocks = () => {
    const groupedStocks = new Set<string>();
    
    const addStocksFromGroup = (group: StockGroup) => {
      // Add stocks from current group
      group.stocks.forEach(stock => groupedStocks.add(stock));
      
      // Recursively process subgroups
      if (group.subGroups) {
        Object.values(group.subGroups).forEach(subGroup => {
          addStocksFromGroup(subGroup);
        });
      }
    };
    
    Object.entries(watchlist.groups).forEach(([groupName, group]) => {
      if (groupName !== "Default Group") {
        addStocksFromGroup(group);
      }
    });
    
    return groupedStocks;
  };

  // Get ungrouped stocks
  const getUngroupedStocks = () => {
    const allStocks = getAllStocks();
    const groupedStocks = getGroupedStocks();
    return allStocks.filter(stock => !groupedStocks.has(stock));
  };

  // Handle stock deletion
  const handleDeleteStock = async (groupName: string, symbol: string) => {
    try {
      const response = await fetch(
        `${process.env.REACT_APP_API_URL}/api/watchlist/${encodeURIComponent(groupName)}/${encodeURIComponent(symbol)}`,
        {
          method: 'DELETE',
        }
      );
  
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to delete stock');
      }
  
      await fetchWatchlist();
      message.success('Successfully deleted');
    } catch (error) {
      console.error('Failed to delete stock:', error);
      message.error(error instanceof Error ? error.message : 'Failed to delete stock');
    }
  };

  // Handle drop events
  const onDrop: TreeProps['onDrop'] = async (info) => {
    const dropKey = info.node.key as string;
    const dragKey = info.dragNode.key as string;
    const dropPos = info.node.pos.split('-');
    const dropPosition = info.dropPosition - Number(dropPos[dropPos.length - 1]);
    
    // Handle folder drag and drop
    if (dragKey.startsWith('folder-')) {
        const sourceFolder = dragKey.replace('folder-', '');
        const targetFolder = dropKey.replace(/^(folder|stock)-/, '');
        
        // If reordering (placing before or after another folder)
        if (dropPosition === -1 || dropPosition === 1) {
            try {
                const response = await fetch(`${process.env.REACT_APP_API_URL}/api/groups/reorder`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        source_group: sourceFolder,
                        target_group: targetFolder,
                        position: dropPosition === -1 ? 'before' : 'after'
                    }),
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.error || 'Failed to reorder');
                }

                const data = await response.json();
                setWatchlist({ groups: data.groups });
                message.success('Successfully reordered');
            } catch (error) {
                console.error('Failed to reorder:', error);
                message.error(error instanceof Error ? error.message : 'Failed to reorder');
            }
            return;
        }
        
        // If moving into another folder
        try {
            const response = await fetch(`${process.env.REACT_APP_API_URL}/api/groups/move`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    source_group: sourceFolder,
                    target_group: dropPosition === 0 ? targetFolder : ''
                }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to move folder');
            }

            const data = await response.json();
            setWatchlist({ groups: data.groups });
            message.success('Successfully moved');
        } catch (error) {
            console.error('Failed to move folder:', error);
            message.error(error instanceof Error ? error.message : 'Failed to move folder');
        }
        return;
    }
    
    // Handle stock drag and drop
    if (dragKey.startsWith('stock-')) {
      const symbol = dragKey.replace('stock-', '');
      let fromGroup = '';
      let toGroup = '';

      // Determine source group
      for (const [groupName, group] of Object.entries(watchlist.groups)) {
        if (group.stocks.includes(symbol)) {
          fromGroup = groupName;
          break;
        }
      }

      // Determine target position and group
      if (dropKey.startsWith('folder-')) {
        // If dragged onto a folder, move to that folder
        toGroup = dropKey.replace('folder-', '');
      } else if (dropKey.startsWith('stock-')) {
        // If dragged onto another stock, could be reordering or moving to another group
        const targetSymbol = dropKey.replace('stock-', '');
        
        // Find target stock's group
        for (const [groupName, group] of Object.entries(watchlist.groups)) {
          if (group.stocks.includes(targetSymbol)) {
            toGroup = groupName;
            break;
          }
        }

        // If within same group, reorder
        if (fromGroup === toGroup) {
          try {
            // Build complete group path
            let fullGroupPath = '';
            for (const [groupName, group] of Object.entries(watchlist.groups)) {
              if (group.stocks.includes(targetSymbol)) {
                fullGroupPath = groupName;
                break;
              }
              if (group.subGroups) {
                for (const [subGroupName, subGroup] of Object.entries(group.subGroups)) {
                  if (subGroup.stocks.includes(targetSymbol)) {
                    fullGroupPath = `${groupName}/${subGroupName}`;
                    break;
                  }
                }
                if (fullGroupPath) break;
              }
            }

            const response = await fetch(`${process.env.REACT_APP_API_URL}/api/watchlist/reorder`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({
                group: fullGroupPath,
                source_symbol: symbol,
                target_symbol: targetSymbol,
                position: dropPosition === -1 ? 'before' : 'after'
              }),
            });

            if (!response.ok) {
              const errorData = await response.json();
              throw new Error(errorData.error || 'Failed to reorder');
            }

            const data = await response.json();
            setWatchlist({ groups: data.groups });
            message.success('Successfully reordered');
            return;
          } catch (error) {
            console.error('Failed to reorder:', error);
            message.error(error instanceof Error ? error.message : 'Failed to reorder');
            return;
          }
        }
      } else {
        // If dragged to ungrouped area
        toGroup = 'Default Group';
      }

      // If source and target groups are the same, don't move
      if (fromGroup === toGroup) {
        return;
      }

      try {
        // Get stocks to move
        let stocksToMove: string[] = [];
        if (selectedKeys.length > 1 && selectedKeys.includes(dragKey)) {
          // If multiple items selected including dragged item, move all selected stocks
          stocksToMove = selectedKeys
            .filter(key => typeof key === 'string' && key.startsWith('stock-'))
            .map(key => (key as string).replace('stock-', ''));
        } else {
          // Otherwise only move dragged stock
          stocksToMove = [symbol];
        }

        // Move each stock sequentially
        for (const stockSymbol of stocksToMove) {
          console.log(`Moving stock ${stockSymbol} from ${fromGroup} to ${toGroup}`);
          const response = await fetch(`${process.env.REACT_APP_API_URL}/api/watchlist/move`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              symbol: stockSymbol,
              from_group: fromGroup,
              to_group: toGroup,
            }),
          });

          if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to move stock');
          }
        }

        // Update state immediately after successful move
        setWatchlist(prevState => {
          const newState = {
            groups: { ...prevState.groups }
          };

          // Remove stocks from source group
          if (newState.groups[fromGroup]) {
            newState.groups[fromGroup] = {
              ...newState.groups[fromGroup],
              stocks: newState.groups[fromGroup].stocks.filter(s => !stocksToMove.includes(s))
            };
          }

          // Add to target group
          if (newState.groups[toGroup]) {
            newState.groups[toGroup] = {
              ...newState.groups[toGroup],
              stocks: [...newState.groups[toGroup].stocks, ...stocksToMove]
            };
          }

          return newState;
        });

        message.success(`Successfully moved ${stocksToMove.length} stocks to ${toGroup}`);
        setSelectedKeys([]); // Clear selection state
      } catch (error) {
        console.error('Failed to move stocks:', error);
        message.error(error instanceof Error ? error.message : 'Failed to move stocks');
      }
    }
  };

  // Create new folder
  const handleAddFolder = async (values: { name: string; description: string }) => {
    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL}/api/groups`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: values.name,
          description: values.description,
        }),
      });

      if (!response.ok) throw new Error('Failed to create group');

      await fetchWatchlist();
      setIsModalVisible(false);
      form.resetFields();
      message.success('Group created successfully');
    } catch (error) {
      console.error('Failed to create group:', error);
      message.error('Failed to create group');
    }
  };

  // Modify Tree onSelect handler
  const handleTreeSelect = (selectedKeys: Key[]) => {
    const key = selectedKeys[0] as string;
    if (key?.startsWith('stock-')) {
      const symbol = key.replace('stock-', '');
      setSelectedStock(symbol);
      scrollToStock(symbol);
    }
  };

  // Add handleExpand function
  const handleExpand = (
    expandedKeys: Key[],
    info: {
      node: EventDataNode<DataNode>;
      expanded: boolean;
      nativeEvent: MouseEvent;
    }
  ) => {
    setExpandedKeys(expandedKeys.map(key => String(key)));
  };

  // Modify folder deletion handler
  const handleDeleteFolder = async (groupPath: string) => {
    try {
      const response = await fetch(
        `${process.env.REACT_APP_API_URL}/api/groups/${encodeURIComponent(groupPath)}`, 
        {
          method: 'DELETE',
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to delete folder');
      }

      await fetchWatchlist();
      message.success('Successfully deleted');
    } catch (error) {
      console.error('Failed to delete folder:', error);
      message.error(error instanceof Error ? error.message : 'Failed to delete folder');
    }
  };

  // Modify handleRenameFolder function
  const handleRenameFolder = async (groupPath: string, newName: string) => {
    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL}/api/groups/rename`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          old_path: encodeURIComponent(groupPath),  // Encode special characters in path
          new_name: newName,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to rename folder');
      }

      await fetchWatchlist();
      message.success('Successfully renamed');
    } catch (error) {
      console.error('Failed to rename folder:', error);
      message.error(error instanceof Error ? error.message : 'Failed to rename folder');
    }
  };

  // Modify generateTreeData function
  const generateTreeData = (group: StockGroup, groupPath: string): DataNode => {
    const stockNodes: DataNode[] = group.stocks.map((stock: string) => ({
      title: (
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <StockOutlined />
            <span>{stock}</span>
          </div>
          <Dropdown
            menu={{
              items: [
                {
                  key: 'delete',
                  icon: <DeleteOutlined />,
                  label: 'Delete',
                  onClick: () => handleDeleteStock(groupPath, stock)
                }
              ]
            }}
            trigger={['click']}
          >
            <MoreOutlined
              onClick={(e: React.MouseEvent) => e.stopPropagation()}
              style={{ cursor: 'pointer' }}
            />
          </Dropdown>
        </div>
      ),
      key: `stock-${stock}`,
      isLeaf: true,
    }));

    // Create subfolder nodes
    const subGroupNodes: DataNode[] = group.subGroups ? 
      Object.entries(group.subGroups).map(([subName, subGroup]) =>
        generateTreeData(subGroup, `${groupPath}/${subName}`)
      ) : [];

    // Return current folder node
    return {
      title: (
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <FolderOutlined />
            <span>{groupPath.split('/').pop()}</span>
          </div>
          <Dropdown
            menu={{
              items: [
                {
                  key: 'rename',
                  icon: <EditOutlined />,
                  label: 'Rename',
                  onClick: () => {
                    const currentName = groupPath.split('/').pop() || '';
                    let inputRef: any = null;

                    Modal.confirm({
                      title: 'Rename Folder',
                      icon: <EditOutlined />,
                      content: (
                        <Input 
                          placeholder="Enter new name"
                          defaultValue={currentName}
                          ref={node => {
                            if (node) {
                              inputRef = node;
                              setTimeout(() => node.select(), 100);
                            }
                          }}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') {
                              const value = inputRef.input.value.trim();
                              if (value) {
                                handleRenameFolder(groupPath, value);
                                Modal.destroyAll();
                              }
                            }
                          }}
                        />
                      ),
                      async onOk() {
                        const value = inputRef.input.value.trim();
                        if (value) {
                          await handleRenameFolder(groupPath, value);
                        }
                      },
                      okButtonProps: {
                        disabled: false
                      }
                    });
                  }
                },
                {
                  key: 'delete',
                  icon: <DeleteOutlined />,
                  label: 'Delete Folder',
                  onClick: () => {
                    Modal.confirm({
                      title: 'Confirm Delete',
                      content: 'After deleting the folder, stocks within it will be moved to the default group. Are you sure you want to delete?',
                      onOk: () => handleDeleteFolder(groupPath),
                    });
                  }
                }
              ]
            }}
            trigger={['click']}
          >
            <MoreOutlined
              onClick={(e: React.MouseEvent) => e.stopPropagation()}
              style={{ cursor: 'pointer' }}
            />
          </Dropdown>
        </div>
      ),
      key: `folder-${groupPath}`,
      children: [...stockNodes, ...subGroupNodes],
      selectable: false
    };
  };

  // Modify treeData generation
  const treeData: DataNode[] = [
    // Ungrouped stocks
    ...getUngroupedStocks().map((stock: string): DataNode => ({
      title: (
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <StockOutlined />
            <span>{stock}</span>
          </div>
          <Dropdown
            menu={{
              items: [
                {
                  key: 'delete',
                  icon: <DeleteOutlined />,
                  label: 'Delete',
                  onClick: () => handleDeleteStock('Default Group', stock)
                }
              ]
            }}
            trigger={['click']}
          >
            <MoreOutlined
              onClick={(e: React.MouseEvent) => e.stopPropagation()}
              style={{ cursor: 'pointer' }}
            />
          </Dropdown>
        </div>
      ),
      key: `stock-${stock}`,
      isLeaf: true,
    })),
    // Grouped stocks and subgroups
    ...Object.entries(watchlist.groups)
      .filter(([groupName]) => groupName !== "Default Group")
      .map(([groupName, group]) => generateTreeData(group, groupName))
  ];

  // Add function to get all folder keys
  const getAllFolderKeys = (groups: GroupData): string[] => {
    const keys: string[] = [];
    
    const addFolderKeys = (groupPath: string, group: StockGroup) => {
      keys.push(`folder-${groupPath}`);
      if (group.subGroups) {
        Object.entries(group.subGroups).forEach(([subName, subGroup]) => {
          addFolderKeys(`${groupPath}/${subName}`, subGroup);
        });
      }
    };

    Object.entries(groups)
      .filter(([groupName]) => groupName !== "Default Group")
      .forEach(([groupName, group]) => {
        addFolderKeys(groupName, group);
      });

    return keys;
  };

  // Add handler for expanding/collapsing all folders
  const handleExpandAll = (expand: boolean) => {
    if (expand) {
      // Expand all folders
      const allKeys = getAllFolderKeys(watchlist.groups);
      setExpandedKeys(allKeys);
    } else {
      // Collapse all folders
      setExpandedKeys([]);
    }
  };

  // Add directory refresh function
  const handleRefreshDirectory = async () => {
    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL}/api/watchlist`);
      if (!response.ok) {
        throw new Error('Failed to get watchlist');
      }
      const data = await response.json();
      setWatchlist({ groups: data.groups || {} });
      message.success('Directory refreshed successfully');
    } catch (error) {
      console.error('Failed to refresh directory:', error);
      message.error('Failed to refresh directory');
    }
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider width={300} theme="light" style={{ padding: '16px' }}>
        <div style={{ marginBottom: '16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <StockSearch 
            onSelect={(symbol) => {
              setSelectedStock(symbol);
              fetchWatchlist();  // Refresh watchlist
            }} 
            style={{ width: '100%' }}
          />
          
          <div style={{ display: 'flex', gap: '8px' }}>
            <Button 
              type="primary" 
              icon={<PlusOutlined />}
              onClick={() => setIsModalVisible(true)}
              style={{ flex: 1 }}
            >
              New Folder
            </Button>
            <Tooltip title="Refresh Directory" placement="bottom">
              <Button
                icon={<ReloadOutlined />}
                onClick={handleRefreshDirectory}
              />
            </Tooltip>
            <Tooltip 
              title={expandedKeys.length === 0 ? "Expand All Folders" : "Collapse All Folders"}
              placement="bottom"
            >
              <Button
                onClick={() => handleExpandAll(expandedKeys.length === 0)}
                icon={expandedKeys.length === 0 ? <ExpandOutlined /> : <CompressOutlined />}
              />
            </Tooltip>
          </div>
        </div>
        
        {loading ? (
          <Spin />
        ) : (
          <Tree
            treeData={treeData}
            expandedKeys={expandedKeys}
            selectedKeys={selectedKeys}
            onExpand={handleExpand}
            onSelect={(keys) => {
              const validKeys = keys.filter(key => 
                typeof key === 'string' && key.startsWith('stock-')
              );
              setSelectedKeys(validKeys);
              
              if (validKeys.length === 1) {
                const symbol = (validKeys[0] as string).replace('stock-', '');
                setSelectedStock(symbol);
                scrollToStock(symbol);
              }
            }}
            draggable
            onDrop={onDrop}
            showIcon
          />
        )}
        <Modal
          title="New Folder"
          open={isModalVisible}
          onCancel={() => setIsModalVisible(false)}
          onOk={() => form.submit()}
        >
          <Form form={form} onFinish={handleAddFolder}>
            <Form.Item
              name="name"
              label="Name"
              rules={[{ required: true, message: 'Please enter folder name' }]}
            >
              <Input />
            </Form.Item>
            <Form.Item
              name="description"
              label="Description"
            >
              <Input />
            </Form.Item>
          </Form>
        </Modal>
      </Sider>

      <Content style={{ padding: '24px', overflowY: 'auto' }}>
        <div style={{ marginBottom: '16px' }}>
          <Select
            style={{ width: 120 }}
            value={timeframe}
            onChange={setTimeframe}
            options={timeframeOptions}
          />
        </div>
        
        {/* Render ungrouped stocks */}
        {getUngroupedStocks().length > 0 && (
          <div>
            <h2 style={{ margin: '16px 0' }}>Ungrouped Stocks</h2>
            {getUngroupedStocks().map(symbol => (
              <div 
                key={symbol}
                ref={(el: HTMLDivElement | null) => {
                  stockRefs.current[symbol] = el;
                  return undefined;
                }}
                id={`stock-${symbol}`}
              >
                <StockCard
                  symbol={symbol}
                  timeframe={timeframe}
                />
              </div>
            ))}
          </div>
        )}
        
        {/* Render grouped and sub-grouped stocks */}
        {Object.entries(watchlist.groups)
          .filter(([groupName]) => groupName !== "Default Group")
          .map(([groupName, group]) => {
            const renderStockGroup = (stocks: string[], indent: number = 0) => (
              <>
                {stocks.map(symbol => (
                  <div 
                    key={symbol}
                    ref={(el: HTMLDivElement | null) => {
                      stockRefs.current[symbol] = el;
                      return undefined;
                    }}
                    id={`stock-${symbol}`}
                    style={{ marginLeft: `${indent}px` }}
                  >
                    <StockCard
                      symbol={symbol}
                      timeframe={timeframe}
                    />
                  </div>
                ))}
              </>
            );

            return (
              <div key={groupName}>
                <h2 style={{ margin: '16px 0' }}>{groupName}</h2>
                {/* Render current group stocks */}
                {renderStockGroup(group.stocks)}
                
                {/* Render subgroup stocks */}
                {group.subGroups && Object.entries(group.subGroups).map(([subGroupName, subGroup]) => (
                  <div key={`${groupName}-${subGroupName}`}>
                    <h3 style={{ margin: '16px 0', paddingLeft: '20px' }}>{subGroupName}</h3>
                    {renderStockGroup(subGroup.stocks, 20)}
                  </div>
                ))}
              </div>
            );
          })}
      </Content>
    </Layout>
  );
};

export default StockDashboard;
