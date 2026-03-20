export interface Tool {
  name: string;
  description: string;
  parameters: Record<string, unknown>;
  execute: (params: Record<string, unknown>) => Promise<ToolResult>;
  permissionLevel: PermissionLevel;
}

export interface ToolResult {
  success: boolean;
  output?: string;
  error?: string;
}

export type PermissionLevel = 'read' | 'write' | 'exec' | 'admin';

export interface ToolPermission {
  tool: string;
  level: PermissionLevel;
}

export interface ToolRegistry {
  register(tool: Tool): void;
  get(name: string): Tool | undefined;
  list(): Tool[];
  checkPermission(tool: string, requiredLevel: PermissionLevel): boolean;
}
