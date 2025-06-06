'use client';

import React from 'react';
import InteractiveBarChart from './InteractiveBarChart';
import TimelineChart from './TimelineChart';
import NetworkDiagram from './NetworkDiagram';

export {
  InteractiveBarChart,
  TimelineChart,
  NetworkDiagram
};

export interface ChartData {
  id: string;
  name: string;
  value: number;
  category?: string;
  date?: string;
  source?: string;
  metadata?: Record<string, any>;
}

export interface TimelineData {
  id: string;
  date: string;
  title: string;
  description: string;
  amount?: number;
  source: string;
  type: string;
  metadata?: Record<string, any>;
}

export interface NetworkNode {
  id: string;
  label: string;
  type: 'company' | 'agency' | 'person' | 'contract' | 'lobbyist';
  size?: number;
  color?: string;
  metadata?: Record<string, any>;
}

export interface NetworkEdge {
  id: string;
  from: string;
  to: string;
  label?: string;
  weight?: number;
  type?: string;
  metadata?: Record<string, any>;
}

export interface NetworkData {
  nodes: NetworkNode[];
  edges: NetworkEdge[];
}

export default function InteractiveCharts() {
  return null; // This is just an export module
} 