import { Tool, ToolResult } from './types.js';

export interface AgentConfig {
  id: string;
  name: string;
  description?: string;
  model: string;
  systemPrompt?: string;
  tools?: string[];
  maxIterations?: number;
  timeout?: number;
}

export interface AgentContext {
  sessionId: string;
  userId?: string;
  channel?: string;
  metadata?: Record<string, unknown>;
}

export interface AgentMessage {
  role: 'user' | 'assistant' | 'system' | 'tool';
  content: string;
  name?: string;
  toolCallId?: string;
}

export interface AgentResponse {
  message: string;
  toolCalls?: ToolCall[];
  done: boolean;
  metadata?: Record<string, unknown>;
}

export interface ToolCall {
  id: string;
  name: string;
  params: Record<string, unknown>;
}

export interface BaseAgent {
  config: AgentConfig;
  initialize(): Promise<void>;
  processMessage(message: string, context?: AgentContext): Promise<AgentResponse>;
  getMemory(): AgentMemory;
  addToolCallResult(result: ToolResult): void;
}

export interface AgentMemory {
  shortTerm: AgentMessage[];
  longTerm: MemoryEntry[];
  addToShortTerm(message: AgentMessage): void;
  addToLongTerm(entry: MemoryEntry): void;
  getRecentShortTerm(count: number): AgentMessage[];
  searchLongTerm(query: string): MemoryEntry[];
  compact(): void;
}

export interface MemoryEntry {
  id: string;
  content: string;
  timestamp: number;
  type: 'fact' | 'preference' | 'conversation' | 'task';
  metadata?: Record<string, unknown>;
}
