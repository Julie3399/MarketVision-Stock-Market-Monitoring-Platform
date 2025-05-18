import React, { useState, useCallback } from 'react';
import { AutoComplete, Input, Spin, message } from 'antd';
import { PlusCircleOutlined, SearchOutlined } from '@ant-design/icons';
import { debounce } from 'lodash';
import type { SelectProps } from 'antd/es/select';

interface StockSearchProps {
  onSelect: (symbol: string) => void;
  style?: React.CSSProperties;
}

interface StockSuggestion {
  symbol: string;
  name: string;
  exchange: string;
  logo?: string;
}
// Use regular CSS classes and inline styles instead of styled-components
const styles = {
  suggestionItem: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '8px 12px',
  },
  stockInfo: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '4px',
  },
  ticker: {
    fontWeight: 600,
    color: '#1a1a1a',
  },
  companyName: {
    color: '#666',
    fontSize: '12px',
  },
  exchangeTag: {
    fontSize: '11px',
    padding: '2px 6px',
    borderRadius: '4px',
    backgroundColor: '#f0f0f0',
    color: '#666',
  },
  addButton: {
    cursor: 'pointer',
    transition: 'opacity 0.2s',
    opacity: 0.6,
    ':hover': {
      opacity: 1,
    },
  },
  rightSection: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
};

const formatCompanyName = (name: string, isMobile: boolean): string => {
  const maxLength = isMobile ? 20 : 35;
  return name.length > maxLength ? `${name.slice(0, maxLength-3)}...` : name;
};

export const StockSearch: React.FC<StockSearchProps> = ({ onSelect, style }) => {
  const [options, setOptions] = useState<SelectProps['options']>([]);
  const [loading, setLoading] = useState(false);
  const [searchCache] = useState<Map<string, StockSuggestion[]>>(new Map());

  const searchStocks = useCallback(
    debounce(async (query: string) => {
      if (!query) {
        setOptions([]);
        return;
      }

      try {
        setLoading(true);
        const url = `${process.env.REACT_APP_API_URL}/api/stock/search/${query}`;
        console.log('Searching at URL:', url);

        const response = await fetch(url, {
          method: 'GET',
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
          },
        });

        console.log('Response status:', response.status);

        if (!response.ok) {
          const errorText = await response.text();
          console.error('Error response:', errorText);
          throw new Error(`Search request failed: ${response.status} ${errorText}`);
        }

        const suggestions: StockSuggestion[] = await response.json();
        console.log('Search results:', suggestions);
        formatAndSetOptions(suggestions);
      } catch (error) {
        console.error('Failed to search stocks:', error);
        if (error instanceof TypeError && error.message === 'Failed to fetch') {
          message.error('Unable to connect to server, please ensure the backend service is running');
        } else {
          message.error('Search failed: ' + (error instanceof Error ? error.message : String(error)));
        }
        setOptions([]);
      } finally {
        setLoading(false);
      }
    }, 300),
    []
  );

  const formatAndSetOptions = (suggestions: StockSuggestion[]) => {
    const isMobile = window.innerWidth < 768;
    const formattedOptions = suggestions.map(item => ({
      value: item.symbol,
      label: (
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center', 
          padding: '8px 12px', 
          width: '100%' 
        }}>
          {/* Left content: stock code and company name (vertical layout) */}
          <div style={{ 
            display: 'flex', 
            flexDirection: 'column', 
            gap: '4px', 
            flex: 1, // Key: occupy remaining space
            overflow: 'hidden' // Prevent content overflow
          }}>
            <span style={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: '8px',
            minWidth: '120px', // Key: fixed minimum width
            marginLeft: '12px', // Keep spacing with left content
            flexShrink: 0 // Prevent compression
          }}>{item.symbol}</span>
            <span style={{ 
              color: '#666', 
              wordBreak: 'break-word' // Allow long names to wrap
            }}>
              {item.name}
            </span>
          </div>
  
          {/* Right content: exchange code and plus icon */}
          <div style={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: '8px',
            minWidth: '120px', // Key: fixed minimum width
            marginLeft: '12px', // Keep spacing with left content
            flexShrink: 0 // Prevent compression
          }}>
            <span style={{ fontSize: '12px', color: '#888' }}>
              {item.exchange}
            </span>
            <PlusCircleOutlined
              style={{ 
                cursor: 'pointer', 
                opacity: 0.6, 
                fontSize: '20px',
                flexShrink: 0 // Prevent icon compression
              }}
              onMouseEnter={(e) => (e.currentTarget.style.opacity = '1')}
              onMouseLeave={(e) => (e.currentTarget.style.opacity = '0.6')}
              onClick={(e) => {
                e.stopPropagation();
                handleAddStock(item.symbol);
              }}
            />
          </div>
        </div>
      ),
    }));
    setOptions(formattedOptions);
  };

  const handleAddStock = async (symbol: string) => {
    try {
      console.log('Starting to add stock:', symbol);
      
      // First check if the stock already exists in any group
      const watchlistResponse = await fetch(`${process.env.REACT_APP_API_URL}/api/watchlist`);
      if (!watchlistResponse.ok) {
        throw new Error('Failed to get watchlist');
      }
      const watchlistData = await watchlistResponse.json();
      
      // Check if stock exists in any group
      let existingGroup = null;
      Object.entries(watchlistData.groups).forEach(([groupName, group]: [string, any]) => {
        if (group.stocks.includes(symbol)) {
          existingGroup = groupName;
        }
      });
      
      if (existingGroup) {
        message.warning(`Stock ${symbol} already exists in group "${existingGroup}"`);
        return;
      }
      
      const requestBody = {
        symbol: symbol,
        group: 'Default Group'
      };
      
      console.log('Sending request body:', requestBody);
      
      const response = await fetch(`${process.env.REACT_APP_API_URL}/api/watchlist/add`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify(requestBody),
      });

      console.log('Add stock response status:', response.status);
      const data = await response.json();
      console.log('Add stock response data:', data);

      if (!response.ok) {
        if (data.detail) {
          throw new Error(Array.isArray(data.detail) ? data.detail[0].msg : data.detail);
        }
        throw new Error(data.error || 'Failed to add stock');
      }

      message.success(data.message || `Successfully added ${symbol} to watchlist`);
      onSelect(symbol);  // Notify parent component to update
    } catch (error) {
      console.error('Failed to add stock:', error);
      message.error(error instanceof Error ? error.message : 'Failed to add stock');
    }
  };

  return (
    <AutoComplete
      options={options}
      onSelect={onSelect}
      onSearch={searchStocks}
      notFoundContent={loading ? <Spin size="small" /> : "No matches found, try entering full code or company name"}
      style={style}
      dropdownMatchSelectWidth={false}
    >
      <Input
        placeholder="Search stock code or company name"
        prefix={<SearchOutlined style={{ color: '#bfbfbf' }} />}
        allowClear
      />
    </AutoComplete>
  );
};