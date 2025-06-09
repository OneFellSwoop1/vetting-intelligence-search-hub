import React, { useState, useMemo } from 'react';
import { 
  BarChart3, 
  PieChart, 
  TrendingUp, 
  DollarSign, 
  Calendar,
  Filter,
  Download,
  Share2,
  Maximize2
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart as RechartsPieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  Area,
  AreaChart
} from 'recharts';

interface SearchResult {
  title: string;
  description: string;
  amount?: string | number;
  date?: string;
  source: string;
  vendor?: string;
  agency?: string;
  url?: string;
  record_type?: string;
  client_count?: number;
  registration_count?: number;
  year?: string;
}

interface AnalyticsDashboardProps {
  results: SearchResult[];
  totalHits: Record<string, number>;
  query: string;
}

const sourceColors = {
  senate_lda: '#EF4444',
  checkbook: '#10B981', 
  dbnyc: '#3B82F6',
  nys_ethics: '#F59E0B',
  nyc_lobbyist: '#F97316'
};

const AnalyticsDashboard: React.FC<AnalyticsDashboardProps> = ({ 
  results, 
  totalHits, 
  query 
}) => {
  const [activeChart, setActiveChart] = useState<'source' | 'timeline' | 'amount'>('source');
  const [timeRange, setTimeRange] = useState<'1y' | '2y' | 'all'>('1y');

  // Process data for visualizations
  const analyticsData = useMemo(() => {
    // Source distribution
    const sourceData = Object.entries(totalHits).map(([source, count]) => ({
      name: source.replace('_', ' ').toUpperCase(),
      value: count,
      color: sourceColors[source as keyof typeof sourceColors] || '#6B7280',
      source
    }));

    // Timeline data
    const timelineData = results.reduce((acc, result) => {
      if (result.date) {
        const date = new Date(result.date);
        const year = date.getFullYear();
        const month = `${year}-${String(date.getMonth() + 1).padStart(2, '0')}`;
        
        if (!acc[month]) {
          acc[month] = { month, count: 0, amount: 0 };
        }
        acc[month].count += 1;
        
        if (result.amount) {
          const numAmount = typeof result.amount === 'number' 
            ? result.amount 
            : parseFloat(result.amount.toString().replace(/[$,]/g, ''));
          if (!isNaN(numAmount)) {
            acc[month].amount += numAmount;
          }
        }
      }
      return acc;
    }, {} as Record<string, { month: string; count: number; amount: number }>);

    const sortedTimelineData = Object.values(timelineData)
      .sort((a, b) => a.month.localeCompare(b.month))
      .slice(-12); // Last 12 months

    // Amount distribution
    const amountRanges = [
      { range: '$0-$10K', min: 0, max: 10000, count: 0 },
      { range: '$10K-$100K', min: 10000, max: 100000, count: 0 },
      { range: '$100K-$1M', min: 100000, max: 1000000, count: 0 },
      { range: '$1M+', min: 1000000, max: Infinity, count: 0 }
    ];

    results.forEach(result => {
      if (result.amount) {
        const numAmount = typeof result.amount === 'number' 
          ? result.amount 
          : parseFloat(result.amount.toString().replace(/[$,]/g, ''));
        
        if (!isNaN(numAmount)) {
          const range = amountRanges.find(r => numAmount >= r.min && numAmount < r.max);
          if (range) range.count += 1;
        }
      }
    });

    const amountData = amountRanges.filter(r => r.count > 0);

    // Summary metrics
    const totalResults = results.length;
    const totalAmount = results.reduce((sum, result) => {
      if (result.amount) {
        const numAmount = typeof result.amount === 'number' 
          ? result.amount 
          : parseFloat(result.amount.toString().replace(/[$,]/g, ''));
        return sum + (isNaN(numAmount) ? 0 : numAmount);
      }
      return sum;
    }, 0);

    const averageAmount = totalResults > 0 ? totalAmount / totalResults : 0;
    const sourcesCount = Object.keys(totalHits).length;

    return {
      sourceData,
      timelineData: sortedTimelineData,
      amountData,
      metrics: {
        totalResults,
        totalAmount,
        averageAmount,
        sourcesCount
      }
    };
  }, [results, totalHits]);

  const formatCurrency = (value: number) => {
    if (value >= 1000000) {
      return `$${(value / 1000000).toFixed(1)}M`;
    } else if (value >= 1000) {
      return `$${(value / 1000).toFixed(0)}K`;
    } else {
      return `$${value.toLocaleString()}`;
    }
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-medium text-gray-900">{label}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {entry.name}: {entry.name === 'amount' ? formatCurrency(entry.value) : entry.value}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Analytics Dashboard</h2>
          <p className="text-gray-600">Analysis for "{query}" search results</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm">
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
          <Button variant="outline" size="sm">
            <Share2 className="w-4 h-4 mr-2" />
            Share
          </Button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Results</p>
                <p className="text-2xl font-bold text-gray-900">
                  {analyticsData.metrics.totalResults.toLocaleString()}
                </p>
              </div>
              <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                <BarChart3 className="w-4 h-4 text-blue-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Value</p>
                <p className="text-2xl font-bold text-gray-900">
                  {formatCurrency(analyticsData.metrics.totalAmount)}
                </p>
              </div>
              <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
                <DollarSign className="w-4 h-4 text-green-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Average Value</p>
                <p className="text-2xl font-bold text-gray-900">
                  {formatCurrency(analyticsData.metrics.averageAmount)}
                </p>
              </div>
              <div className="w-8 h-8 bg-orange-100 rounded-lg flex items-center justify-center">
                <TrendingUp className="w-4 h-4 text-orange-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Data Sources</p>
                <p className="text-2xl font-bold text-gray-900">
                  {analyticsData.metrics.sourcesCount}
                </p>
              </div>
              <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center">
                <PieChart className="w-4 h-4 text-purple-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Chart Navigation */}
      <div className="flex gap-2">
        <Button
          variant={activeChart === 'source' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setActiveChart('source')}
        >
          Source Distribution
        </Button>
        <Button
          variant={activeChart === 'timeline' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setActiveChart('timeline')}
        >
          Timeline Analysis
        </Button>
        <Button
          variant={activeChart === 'amount' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setActiveChart('amount')}
        >
          Amount Distribution
        </Button>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Chart */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              {activeChart === 'source' && 'Results by Data Source'}
              {activeChart === 'timeline' && 'Timeline Analysis'}
              {activeChart === 'amount' && 'Amount Distribution'}
              <Button variant="ghost" size="sm">
                <Maximize2 className="w-4 h-4" />
              </Button>
            </CardTitle>
          </CardHeader>
          <CardContent className="p-6">
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                {activeChart === 'source' && (
                  <BarChart data={analyticsData.sourceData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip content={<CustomTooltip />} />
                    <Bar dataKey="value" fill="#3B82F6" />
                  </BarChart>
                )}
                
                {activeChart === 'timeline' && (
                  <AreaChart data={analyticsData.timelineData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" />
                    <YAxis />
                    <Tooltip content={<CustomTooltip />} />
                    <Area type="monotone" dataKey="count" stackId="1" stroke="#3B82F6" fill="#3B82F6" fillOpacity={0.6} />
                  </AreaChart>
                )}
                
                {activeChart === 'amount' && (
                  <BarChart data={analyticsData.amountData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="range" />
                    <YAxis />
                    <Tooltip content={<CustomTooltip />} />
                    <Bar dataKey="count" fill="#10B981" />
                  </BarChart>
                )}
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Source Breakdown */}
        <Card>
          <CardHeader>
            <CardTitle>Source Breakdown</CardTitle>
          </CardHeader>
          <CardContent className="p-6">
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <RechartsPieChart>
                  <Pie
                    data={analyticsData.sourceData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {analyticsData.sourceData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </RechartsPieChart>
              </ResponsiveContainer>
            </div>
            
            {/* Legend */}
            <div className="mt-4 space-y-2">
              {analyticsData.sourceData.map((item, index) => (
                <div key={index} className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2">
                    <div 
                      className="w-3 h-3 rounded-full" 
                      style={{ backgroundColor: item.color }}
                    />
                    <span className="text-gray-700">{item.name}</span>
                  </div>
                  <span className="font-medium text-gray-900">{item.value}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default AnalyticsDashboard; 