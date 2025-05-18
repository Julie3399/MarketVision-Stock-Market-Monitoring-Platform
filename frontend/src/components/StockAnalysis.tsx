import React, { useState } from 'react';
import { Card, Descriptions, Tag, Space, Spin, Button, DatePicker, Modal, message, Tooltip } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined, HistoryOutlined, StockOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import utc from 'dayjs/plugin/utc';
import timezone from 'dayjs/plugin/timezone';
import type { RangePickerProps } from 'antd/es/date-picker';

// Add dayjs plugins
dayjs.extend(utc);
dayjs.extend(timezone);

interface AnalysisProps {
  symbol: string;
}

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8002';

// Define signal explanations mapping
const SIGNAL_EXPLANATIONS: { [key: string]: string } = {
  "MACD Golden Cross": "MACD line crosses above signal line, indicating potential upward trend, a buy signal.",
  "MACD Death Cross": "MACD line crosses below signal line, indicating potential downward trend, a sell signal.",
  "RSI Overbought": "Relative Strength Index (RSI) above 70, indicating market may be overheated and price may fall.",
  "RSI Oversold": "Relative Strength Index (RSI) below 30, indicating market may have bottomed and price may rebound.",
  "KDJ Golden Cross": "In KDJ indicator, K line crosses above D line, indicating potential uptrend, a buy signal.",
  "KDJ Death Cross": "In KDJ indicator, K line crosses below D line, indicating potential downtrend, a sell signal.",
  "Upper Band Breakout": "Price breaks above Bollinger Band, indicating strong uptrend but possible pullback.",
  "Lower Band Breakout": "Price breaks below Bollinger Band, indicating clear downtrend but possible rebound.",
  "Volume Breakout": "Current volume significantly higher than average, indicating increased market activity.",
  "Volume Weakness": "Volume below average level, indicating decreased market participation."
};

interface Analysis {
  price: number;
  change: number;
  volume: number;
  volatility_alert: string;
  money_flow: string;
  technical_signals: string[];
  volume_alert: string;
  date: string;
  error?: string;  // Optional error property
}

type AnalysisResponse = Analysis | { error: string };

interface BackTestPrediction {
  signal: string;
  prediction: string;
  correct: boolean;
}

interface BackTestResults {
  date: string;
  price: number;
  change: number;
  volume: number;
  volatility_alert?: string;
  money_flow?: string;
  technical_signals?: string[];
  volume_alert?: string;
  next_day?: {
    date: string;
    price: number;
    change: number;
  };
  predictions_verified?: BackTestPrediction[];
  accuracy?: number;
}

const StockAnalysis: React.FC<AnalysisProps> = ({ symbol }) => {
  const [analysis, setAnalysis] = React.useState<AnalysisResponse | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [backTestResults, setBackTestResults] = useState<BackTestResults | null>(null);
  const [isBackTesting, setIsBackTesting] = useState(false);
  const [isBackTestModalVisible, setIsBackTestModalVisible] = useState(false);
  const [backTestDate, setBackTestDate] = useState<dayjs.Dayjs | null>(null);
  const [selectedSignal, setSelectedSignal] = useState<string | null>(null);

  React.useEffect(() => {
    const fetchAnalysis = async () => {
      try {
        setLoading(true);
        const response = await fetch(`${API_URL}/api/stock/analysis/${symbol}`);
        const data = await response.json();
        setAnalysis(data);
      } catch (error) {
        console.error('Failed to fetch analysis data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchAnalysis();
  }, [symbol]);

  const runBackTest = async () => {
    if (!backTestDate) {
      return;
    }
    
    // Ensure selected date is in the past
    if (backTestDate.isAfter(dayjs())) {
      message.error('Cannot select future dates');
      return;
    }
    
    // Get data for selected date
    const endDate = backTestDate.format('YYYY-MM-DD');
    const startDate = backTestDate.clone().subtract(60, 'day').format('YYYY-MM-DD');
    
    try {
      setIsBackTesting(true);
      const url = `${API_URL}/api/stock/backtest/${symbol}?start_date=${startDate}&end_date=${endDate}`;
      console.log('Requesting backtest:', url);
      
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          'Origin': window.location.origin
        },
        credentials: 'omit'  // Don't send cookies
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('Response error:', response.status, errorText);
        throw new Error(`Request failed: ${response.status} ${errorText}`);
      }
      
      const data = await response.json();
      console.log('Backtest results:', data);
      
      if (data.error) {
        message.error(data.error);
        return;
      }
      
      setBackTestResults(data);
      message.success('Backtest analysis completed');
    } catch (error) {
      console.error('Backtest analysis failed:', error);
      message.error(error instanceof Error ? error.message : 'Backtest analysis failed, please try again later');
    } finally {
      setIsBackTesting(false);
      setIsBackTestModalVisible(false);
    }
  };

  const handleBackTest = async () => {
    await runBackTest();
  };

  const handleDateChange = (date: dayjs.Dayjs | null) => {
    setBackTestDate(date);
  };

  const handleSignalClick = (signal: string) => {
    // Modify handler to match partial signal text
    let matchedSignal = signal;
    if (signal.startsWith('RSI Overbought') || signal.startsWith('RSI Oversold')) {
      matchedSignal = signal.split(' (')[0];
    }
    setSelectedSignal(matchedSignal);
  };

  // Add function to get US Eastern time
  const getUsEasternTime = () => {
    return dayjs().tz('America/New_York').format('YYYY-MM-DD HH:mm:ss');
  };

  if (loading) {
    return <Spin />;
  }

  // Use type guard to check for errors
  if (!analysis || 'error' in analysis) {
    return <div>Unable to fetch analysis data</div>;
  }

  return (
    <div style={{ height: '100%' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
        <div style={{ textAlign: 'left' }}>
          <h3 style={{ margin: 0, marginBottom: '4px', textAlign: 'left' }}>{symbol} Analysis Report</h3>
          <div style={{ color: '#666', fontSize: '12px', textAlign: 'left' }}>
            As of {getUsEasternTime()} EST
          </div>
        </div>
        <Space>
          <Button 
            type="link" 
            icon={<StockOutlined />}
            href={`https://www.bing.com/search?q=${symbol}+stock+site:msn.com/en-us/money/stockdetails`}
            target="_blank"
            style={{ padding: '4px 8px' }}
          >
            MSN
          </Button>
          <Button 
            type="link" 
            icon={<StockOutlined />}
            href={`https://finance.yahoo.com/quote/${symbol}`}
            target="_blank"
            style={{ padding: '4px 8px' }}
          >
            Yahoo
          </Button>
          <Button 
            type="primary" 
            icon={<HistoryOutlined />} 
            onClick={() => setIsBackTestModalVisible(true)}
          >
            Backtest Analysis
          </Button>
        </Space>
      </div>
      <Descriptions column={1} size="small">
        <Descriptions.Item label="Current Price">
          ${analysis.price.toFixed(2)}
          <Tag color={analysis.change >= 0 ? 'green' : 'red'} style={{ marginLeft: 8 }}>
            {analysis.change >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
            {Math.abs(analysis.change).toFixed(2)}%
          </Tag>
        </Descriptions.Item>
        <Descriptions.Item label="Volume">
          {analysis.volume.toFixed(1)}M
        </Descriptions.Item>
        <Descriptions.Item label="Volatility Alert">
          <Tag color={analysis.volatility_alert.includes('Alert') ? 'red' : 'green'}>
            {analysis.volatility_alert}
          </Tag>
        </Descriptions.Item>
        <Descriptions.Item label="Money Flow">
          <Tag color={
            analysis.money_flow.includes('Inflow') ? 'green' : 
            analysis.money_flow.includes('Outflow') ? 'red' : 'blue'
          }>
            {analysis.money_flow}
          </Tag>
        </Descriptions.Item>
      </Descriptions>

      <div style={{ marginTop: 16 }}>
        <h4>Technical Signals</h4>
        <Space direction="vertical" style={{ width: '100%' }}>
          {analysis.technical_signals.map((signal: string, index: number) => (
            <Tag
              key={index}
              color={signal.includes('Golden Cross') || signal.includes('Oversold') ? 'green' : 
                     signal.includes('Death Cross') || signal.includes('Overbought') ? 'red' : 'blue'}
              style={{ cursor: 'pointer' }}
              onClick={() => handleSignalClick(signal)}
            >
              {signal}
            </Tag>
          ))}
        </Space>
      </div>

      <div style={{ marginTop: 16 }}>
        <h4>Volume Analysis</h4>
        <Tag color={
          analysis.volume_alert.includes('Breakout') ? 'red' :
          analysis.volume_alert.includes('Low') ? 'orange' : 'green'
        }>
          {analysis.volume_alert}
        </Tag>
      </div>
      <Modal
        title="Select Backtest Date"
        open={isBackTestModalVisible}
        onOk={handleBackTest}
        onCancel={() => setIsBackTestModalVisible(false)}
        okButtonProps={{ disabled: !backTestDate }}
      >
        <DatePicker
          style={{ width: '100%' }}
          onChange={handleDateChange}
          value={backTestDate}
          disabledDate={current => {
            // Disable today and future dates
            return current && current > dayjs().endOf('day');
          }}
          allowClear={true}
          placeholder="Select trading day to analyze"
          presets={[
            { label: 'Last Month End', value: dayjs().subtract(1, 'month').endOf('month') },
            { label: '3 Months Ago', value: dayjs().subtract(3, 'month').endOf('month') },
          ]}
        />
        <div style={{ marginTop: 8, fontSize: 12, color: '#666' }}>
          After selecting a date, the system will analyze market signals for that day and verify predictions using the next trading day's data
        </div>
      </Modal>

      {isBackTesting && (
        <div style={{ marginTop: 16, textAlign: 'center' }}>
          <Spin tip="Backtesting in progress..." />
        </div>
      )}

      {backTestResults && !isBackTesting && (
        <Card 
          title={`${backTestResults.date} Analysis Report Backtest`} 
          style={{ marginTop: 24, backgroundColor: '#fafafa' }}
          bordered={false}
        >
          <Descriptions column={1} size="small">
            <Descriptions.Item label="Day Price">
              ${backTestResults.price?.toFixed(2)}
              <Tag color={backTestResults.change >= 0 ? 'green' : 'red'} style={{ marginLeft: 8 }}>
                {backTestResults.change >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
                {Math.abs(backTestResults.change || 0).toFixed(2)}%
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="Volume">
              {backTestResults.volume?.toFixed(1)}M
            </Descriptions.Item>
            {backTestResults.volatility_alert && (
              <Descriptions.Item label="Volatility Alert">
                <Tag color={backTestResults.volatility_alert?.includes('Alert') ? 'red' : 'green'}>
                  {backTestResults.volatility_alert}
                </Tag>
              </Descriptions.Item>
            )}
            {backTestResults.money_flow && (
              <Descriptions.Item label="Money Flow">
                <Tag color={
                  backTestResults.money_flow?.includes('Inflow') ? 'green' : 
                  backTestResults.money_flow?.includes('Outflow') ? 'red' : 'blue'
                }>
                  {backTestResults.money_flow}
                </Tag>
              </Descriptions.Item>
            )}
          </Descriptions>

          {backTestResults.technical_signals && (
            <div style={{ marginTop: 16 }}>
              <h4>Technical Signals</h4>
              <Space direction="vertical" style={{ width: '100%' }}>
                {backTestResults.technical_signals.map((signal: string, index: number) => (
                  <Tag 
                    key={index} 
                    color={
                      signal?.includes('Golden Cross') || signal?.includes('Oversold') ? 'green' : 
                      signal?.includes('Death Cross') || signal?.includes('Overbought') ? 'red' : 'blue'
                    } 
                    style={{ margin: '4px 0', cursor: 'pointer' }}
                    onClick={() => handleSignalClick(signal)}
                  >
                    {signal}
                  </Tag>
                ))}
              </Space>
            </div>
          )}

          {backTestResults.volume_alert && (
            <div style={{ marginTop: 16 }}>
              <h4>Volume Analysis</h4>
              <Tag color={
                backTestResults.volume_alert?.includes('Breakout') ? 'red' :
                backTestResults.volume_alert?.includes('Low') ? 'orange' : 'green'
              }>
                {backTestResults.volume_alert}
              </Tag>
            </div>
          )}

          {backTestResults.next_day && (
            <div style={{ marginTop: 16 }}>
              <h4>Prediction Verification</h4>
              <Descriptions column={1} size="small">
                <Descriptions.Item label="Next Day Actual">
                  ${backTestResults.next_day.price?.toFixed(2)}
                  <Tag color={backTestResults.next_day.change >= 0 ? 'green' : 'red'} style={{ marginLeft: 8 }}>
                    {backTestResults.next_day.change >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
                    {Math.abs(backTestResults.next_day.change || 0).toFixed(2)}%
                  </Tag>
                </Descriptions.Item>
              </Descriptions>
              
              {backTestResults.predictions_verified && (
                <Space direction="vertical" style={{ width: '100%', marginTop: 8 }}>
                  {backTestResults.predictions_verified.map((prediction: any, index: number) => (
                    <div key={index} style={{ 
                      padding: '8px', 
                      backgroundColor: 'white', 
                      borderRadius: '6px',
                      marginBottom: '4px'
                    }}>
                      <Space>
                        <span>{prediction.signal}</span>
                        <Tag color="blue">Prediction: {prediction.prediction}</Tag>
                        <Tag color={prediction.correct ? 'green' : 'red'}>
                          {prediction.correct ? 'Correct' : 'Incorrect'}
                        </Tag>
                      </Space>
                    </div>
                  ))}
                </Space>
              )}

              {backTestResults.accuracy !== null && backTestResults.accuracy !== undefined && (
                <div style={{ marginTop: 8 }}>
                  <Tag color={backTestResults.accuracy >= 60 ? 'green' : 'red'}>
                    Prediction Accuracy: {backTestResults.accuracy.toFixed(1)}%
                  </Tag>
                </div>
              )}
            </div>
          )}
        </Card>
      )}

      <Modal
        title="Technical Indicator Explanation"
        open={!!selectedSignal}
        onCancel={() => setSelectedSignal(null)}
        footer={null}
      >
        {selectedSignal && (
          <div>
            <h3>{selectedSignal}</h3>
            <p>{SIGNAL_EXPLANATIONS[selectedSignal]}</p>
            <div style={{ marginTop: 16 }}>
              <h4>How to Use This Signal:</h4>
              <ul>
                <li>Signal Meaning: {SIGNAL_EXPLANATIONS[selectedSignal]}</li>
                <li>Suggested Action: {
                  selectedSignal.includes('Golden Cross') || selectedSignal.includes('Oversold') ? 
                    'Consider buying or holding' : 
                    selectedSignal.includes('Death Cross') || selectedSignal.includes('Overbought') ?
                    'Consider selling or waiting' : 'Monitor market changes closely'
                }</li>
                <li>Note: Technical indicators are for reference only, please combine with fundamentals and market conditions</li>
              </ul>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default StockAnalysis;
