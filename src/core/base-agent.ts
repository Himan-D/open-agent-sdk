import { BaseAgent, AgentConfig, AgentContext, AgentResponse, AgentMessage, AgentMemory, MemoryEntry, ToolCall } from './agent.js';
import { ToolRegistry, ToolResult } from './types.js';

export abstract class AbstractAgent implements BaseAgent {
  config: AgentConfig;
  protected memory: AgentMemoryImpl;
  protected toolRegistry: ToolRegistry;
  protected toolCallResults: ToolResult[] = [];
  protected iterationCount = 0;

  constructor(config: AgentConfig, toolRegistry: ToolRegistry) {
    this.config = config;
    this.toolRegistry = toolRegistry;
    this.memory = new AgentMemoryImpl();
  }

  async initialize(): Promise<void> {
    this.iterationCount = 0;
    this.toolCallResults = [];
  }

  abstract processMessage(message: string, context?: AgentContext): Promise<AgentResponse>;

  getMemory(): AgentMemory {
    return this.memory;
  }

  addToolCallResult(result: ToolResult): void {
    this.toolCallResults.push(result);
  }

  protected async executeToolCalls(toolCalls: ToolCall[]): Promise<ToolResult[]> {
    const results: ToolResult[] = [];
    for (const call of toolCalls) {
      const result = await this.toolRegistry.execute(call.name, call.params);
      results.push(result);
    }
    return results;
  }

  protected shouldContinue(iterations: number): boolean {
    const maxIterations = this.config.maxIterations || 10;
    return iterations < maxIterations;
  }

  protected buildSystemPrompt(): string {
    const parts: string[] = [];

    if (this.config.systemPrompt) {
      parts.push(this.config.systemPrompt);
    }

    parts.push(`You are ${this.config.name}.`);
    if (this.config.description) {
      parts.push(this.config.description);
    }

    const tools = this.toolRegistry.list();
    if (tools.length > 0) {
      parts.push('\n## Available Tools');
      for (const tool of tools) {
        parts.push(`- **${tool.name}**: ${tool.description}`);
      }
    }

    return parts.join('\n');
  }
}

class AgentMemoryImpl implements AgentMemory {
  shortTerm: AgentMessage[] = [];
  longTerm: MemoryEntry[] = [];

  addToShortTerm(message: AgentMessage): void {
    this.shortTerm.push(message);
    if (this.shortTerm.length > 100) {
      this.compact();
    }
  }

  addToLongTerm(entry: MemoryEntry): void {
    this.longTerm.push(entry);
  }

  getRecentShortTerm(count: number): AgentMessage[] {
    return this.shortTerm.slice(-count);
  }

  searchLongTerm(query: string): MemoryEntry[] {
    const lowerQuery = query.toLowerCase();
    return this.longTerm.filter(entry =>
      entry.content.toLowerCase().includes(lowerQuery)
    );
  }

  compact(): void {
    if (this.shortTerm.length > 50) {
      const toKeep = this.shortTerm.slice(-50);
      const summary: AgentMessage = {
        role: 'system',
        content: `[Previous ${this.shortTerm.length - 50} messages compacted]`
      };
      this.shortTerm = [summary, ...toKeep];
    }
  }
}

export function createToolCallId(): string {
  return `call_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`;
}
