import { Tool, ToolRegistry, ToolPermission, PermissionLevel } from './types.js';
import { ToolResult } from './types.js';

export class BaseToolRegistry implements ToolRegistry {
  private tools: Map<string, Tool> = new Map();

  register(tool: Tool): void {
    this.tools.set(tool.name, tool);
  }

  get(name: string): Tool | undefined {
    return this.tools.get(name);
  }

  list(): Tool[] {
    return Array.from(this.tools.values());
  }

  checkPermission(tool: string, requiredLevel: PermissionLevel): boolean {
    const t = this.tools.get(tool);
    if (!t) return false;
    return this.hasPermissionLevel(t.permissionLevel, requiredLevel);
  }

  async execute(name: string, params: Record<string, unknown>): Promise<ToolResult> {
    const tool = this.tools.get(name);
    if (!tool) {
      return { success: false, error: `Tool '${name}' not found` };
    }
    try {
      return await tool.execute(params);
    } catch (error) {
      return { success: false, error: String(error) };
    }
  }

  private hasPermissionLevel(actual: PermissionLevel, required: PermissionLevel): boolean {
    const levels: PermissionLevel[] = ['read', 'write', 'exec', 'admin'];
    return levels.indexOf(actual) >= levels.indexOf(required);
  }
}

export const defaultToolRegistry = new BaseToolRegistry();
