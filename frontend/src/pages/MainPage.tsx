import React, { useState, useEffect } from 'react';
import { StockDebugInfo } from '../components/StockDebugInfo';
import { FolderOperations } from '../components/FolderOperations';
import { message, Button, Input } from 'antd';

interface WatchlistItem {
  symbol: string;
  group: string;
  subgroup?: string;
}

interface GroupedStocks {
  [key: string]: {
    [key: string]: string[];
  };
}

interface FolderState {
  expanded: boolean;
  stocks: string[];
}

interface FolderHistory {
  timestamp: number;
  groupName: string;
  previousState: FolderState;
}

interface FolderOperation {
  type: 'ADD' | 'DELETE' | 'MOVE';
  timestamp: number;
  data: {
    symbol: string;
    fromGroup?: string;
    toGroup?: string;
  };
}
export const MainPage: React.FC = () => {
  const [loadedStocks, setLoadedStocks] = useState<string[]>([]);
  const [groupedStocks, setGroupedStocks] = useState<GroupedStocks>({});
  const [folderHistory, setFolderHistory] = useState<FolderHistory[]>([]);
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set());
  const [operationHistory, setOperationHistory] = useState<FolderOperation[]>([]);

  useEffect(() => {
    const fetchWatchlist = async () => {
      try {
        const response = await fetch(`${process.env.REACT_APP_API_URL}/api/watchlist`, {
          credentials: 'include'
        });
        
        if (!response.ok) {
          throw new Error('Failed to get watchlist');
        }
        
        const data: WatchlistItem[] = await response.json();
        console.log('Watchlist data:', data);

        // Process all stocks (ungrouped)
        setLoadedStocks(data.map(item => item.symbol));

        // Process grouped stocks
        const grouped: GroupedStocks = {};
        data.forEach(item => {
          const group = item.group || 'Default Group';
          const subgroup = item.subgroup || 'Default Subgroup';
          
          if (!grouped[group]) {
            grouped[group] = {};
          }
          if (!grouped[group][subgroup]) {
            grouped[group][subgroup] = [];
          }
          
          grouped[group][subgroup].push(item.symbol);
        });

        setGroupedStocks(grouped);
        console.log('Grouped stocks:', grouped);

      } catch (error) {
        console.error('Failed to load watchlist:', error);
        message.error('Failed to load watchlist');
      }
    };

    fetchWatchlist();
  }, []);

  // Debug function to print all group information
  const printGroupStructure = () => {
    Object.entries(groupedStocks).forEach(([group, subgroups]) => {
      console.log(`Group: ${group}`);
      Object.entries(subgroups).forEach(([subgroup, stocks]) => {
        console.log(`  Subgroup: ${subgroup}`);
        console.log(`    Stocks: ${stocks.join(', ')}`);
      });
    });
  };

  useEffect(() => {
    printGroupStructure();
  }, [groupedStocks]);

  const handleFolderToggle = (groupName: string, isExpanded: boolean) => {
    // Save current state to history
    const currentState: FolderState = {
      expanded: !isExpanded,
      stocks: groupedStocks[groupName]?.['Default Subgroup'] || []
    };

    setFolderHistory(prev => [...prev, {
      timestamp: Date.now(),
      groupName,
      previousState: currentState
    }]);

    // Update expanded state
    setExpandedFolders(prev => {
      const newSet = new Set(prev);
      if (isExpanded) {
        newSet.delete(groupName);
      } else {
        newSet.add(groupName);
      }
      return newSet;
    });
  };

  const handleUndo = () => {
    if (operationHistory.length === 0) {
      message.info('No operations to undo');
      return;
    }

    const lastOperation = operationHistory[operationHistory.length - 1];
    try {
      // Execute undo based on operation type
      switch (lastOperation.type) {
        case 'ADD':
          // Undo add operation
          fetch(`${process.env.REACT_APP_API_URL}/api/watchlist/remove`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            credentials: 'include',
            body: JSON.stringify({
              symbol: lastOperation.data.symbol,
              group: lastOperation.data.toGroup
            }),
          });
          break;
        case 'DELETE':
          // Undo delete operation
          fetch(`${process.env.REACT_APP_API_URL}/api/watchlist/add`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            credentials: 'include',
            body: JSON.stringify({
              symbol: lastOperation.data.symbol,
              group: lastOperation.data.fromGroup
            }),
          });
          break;
        // Can add handling for other operation types
      }

      // Remove the operation from history
      setOperationHistory(prev => prev.slice(0, -1));
      message.success('Last operation undone');
    } catch (error) {
      console.error('Failed to undo operation:', error);
      message.error('Failed to undo operation');
    }
  };

  const renderFolderStructure = () => {
    return (
      <div>
        <div style={{ 
          display: 'flex', 
          alignItems: 'center', 
          marginBottom: '16px',
          gap: '8px'
        }}>
          <Input.Search placeholder="Search stocks" style={{ width: '200px' }} />
          <Button>+ New Folder</Button>
          <FolderOperations 
            onUndo={handleUndo}
            style={{ marginLeft: 'auto' }}
          />
        </div>

        {/* Folder List */}
        {Object.entries(groupedStocks).map(([groupName, subgroups]) => (
          <div key={groupName} style={{ marginBottom: '8px' }}>
            <div 
              style={{ 
                display: 'flex', 
                alignItems: 'center',
                cursor: 'pointer',
                padding: '4px',
                backgroundColor: '#f5f5f5',
                borderRadius: '4px'
              }}
            >
              <span 
                style={{ width: '20px', textAlign: 'center' }}
                onClick={() => handleFolderToggle(groupName, expandedFolders.has(groupName))}
              >
                {expandedFolders.has(groupName) ? '▼' : '▶'}
              </span>
              <span style={{ marginLeft: '8px' }}>{groupName}</span>
            </div>
            {expandedFolders.has(groupName) && (
              <div style={{ 
                marginLeft: '20px',
                marginTop: '4px',
                padding: '4px',
                backgroundColor: '#fafafa',
                borderRadius: '4px'
              }}>
                {subgroups['Default Subgroup']?.map(stock => (
                  <div key={stock} style={{ padding: '4px 8px' }}>{stock}</div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    );
  };

  return (
    <div style={{ padding: '20px' }}>
      {renderFolderStructure()}
      <StockDebugInfo stocks={loadedStocks} />
    </div>
  );
};
