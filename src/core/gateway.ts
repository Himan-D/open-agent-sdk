import { EventEmitter } from 'events';
import { BaseAgent, AgentContext, AgentResponse } from './agent.js';
import { ToolRegistry } from './types.js';
import { Logger } from './logger.js';

export interface GatewayConfig {
  name: string;
  port?: number;
  enableWebSocket?: boolean;
  enableHTTP?: boolean;
}

export interface Session {
  id: string;
  agentId: string;
  userId?: string;
  channel?: string;
  createdAt: number;
  lastActivity: number;
  history: SessionMessage[];
}

export interface SessionMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
}

export interface InboundMessage {
  channel: string;
  accountId: string;
  userId?: string;
  content: string;
  metadata?: Record<string, unknown>;
}

export class Gateway extends EventEmitter {
  config: GatewayConfig;
  private agents: Map<string, BaseAgent> = new Map();
  private sessions: Map<string, Session> = new Map();
  private toolRegistry: ToolRegistry;
  private logger: Logger;

  constructor(config: GatewayConfig, toolRegistry: ToolRegistry) {
    super();
    this.config = config;
    this.toolRegistry = toolRegistry;
    this.logger = new Logger(`Gateway:${config.name}`);
  }

  registerAgent(agent: BaseAgent): void {
    this.agents.set(agent.config.id, agent);
    this.logger.info(`Agent registered: ${agent.config.name} (${agent.config.id})`);
  }

  getAgent(agentId: string): BaseAgent | undefined {
    return this.agents.get(agentId);
  }

  listAgents(): { id: string; name: string }[] {
    return Array.from(this.agents.values()).map(a => ({
      id: a.config.id,
      name: a.config.name
    }));
  }

  async createSession(agentId: string, userId?: string, channel?: string): Promise<Session> {
    const agent = this.agents.get(agentId);
    if (!agent) {
      throw new Error(`Agent '${agentId}' not found`);
    }

    const sessionId = `session_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`;
    const session: Session = {
      id: sessionId,
      agentId,
      userId,
      channel,
      createdAt: Date.now(),
      lastActivity: Date.now(),
      history: []
    };

    this.sessions.set(sessionId, session);
    await agent.initialize();
    this.logger.info(`Session created: ${sessionId} for agent ${agentId}`);
    return session;
  }

  async processMessage(sessionId: string, content: string): Promise<AgentResponse> {
    const session = this.sessions.get(sessionId);
    if (!session) {
      throw new Error(`Session '${sessionId}' not found`);
    }

    const agent = this.agents.get(session.agentId);
    if (!agent) {
      throw new Error(`Agent for session '${sessionId}' not found`);
    }

    const context: AgentContext = {
      sessionId,
      userId: session.userId,
      channel: session.channel
    };

    session.history.push({
      role: 'user',
      content,
      timestamp: Date.now()
    });

    this.logger.debug(`Processing message for session ${sessionId}`);
    const response = await agent.processMessage(content, context);

    session.history.push({
      role: 'assistant',
      content: response.message,
      timestamp: Date.now()
    });
    session.lastActivity = Date.now();

    return response;
  }

  getSession(sessionId: string): Session | undefined {
    return this.sessions.get(sessionId);
  }

  listSessions(): Session[] {
    return Array.from(this.sessions.values());
  }

  closeSession(sessionId: string): void {
    this.sessions.delete(sessionId);
    this.logger.info(`Session closed: ${sessionId}`);
  }
}

export function createSessionId(): string {
  return `session_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`;
}
