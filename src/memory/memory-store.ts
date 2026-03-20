import { MemoryEntry } from '../core/agent.js';
import { Logger } from '../core/logger.js';
import fs from 'fs/promises';
import path from 'path';

export interface MemoryConfig {
  storagePath?: string;
  maxShortTerm?: number;
  maxLongTerm?: number;
  enablePersistence?: boolean;
}

export class MemoryStore {
  private shortTerm: MemoryEntry[] = [];
  private longTerm: MemoryEntry[] = [];
  private config: Required<MemoryConfig>;
  private logger: Logger;
  private agentId: string;

  constructor(agentId: string, config: MemoryConfig = {}) {
    this.agentId = agentId;
    this.config = {
      storagePath: config.storagePath || `./memory/${agentId}`,
      maxShortTerm: config.maxShortTerm || 100,
      maxLongTerm: config.maxLongTerm || 1000,
      enablePersistence: config.enablePersistence ?? true
    };
    this.logger = new Logger(`Memory:${agentId}`);
  }

  async initialize(): Promise<void> {
    if (this.config.enablePersistence) {
      try {
        await fs.mkdir(this.config.storagePath, { recursive: true });
        await this.load();
      } catch (error) {
        this.logger.warn('Failed to initialize memory storage', error);
      }
    }
  }

  addShortTerm(entry: Omit<MemoryEntry, 'id'>): string {
    const id = `st_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`;
    const fullEntry: MemoryEntry = { ...entry, id };
    this.shortTerm.push(fullEntry);

    if (this.shortTerm.length > this.config.maxShortTerm) {
      this.promoteOldestToLongTerm();
    }

    this.persist();
    return id;
  }

  addLongTerm(entry: Omit<MemoryEntry, 'id'>): string {
    const id = `lt_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`;
    const fullEntry: MemoryEntry = { ...entry, id };
    this.longTerm.push(fullEntry);

    if (this.longTerm.length > this.config.maxLongTerm) {
      this.pruneOldLongTerm();
    }

    this.persist();
    return id;
  }

  getShortTerm(count?: number): MemoryEntry[] {
    if (count) {
      return this.shortTerm.slice(-count);
    }
    return [...this.shortTerm];
  }

  getLongTerm(count?: number): MemoryEntry[] {
    if (count) {
      return this.longTerm.slice(-count);
    }
    return [...this.longTerm];
  }

  search(query: string): MemoryEntry[] {
    const lowerQuery = query.toLowerCase();
    const results: MemoryEntry[] = [];

    for (const entry of this.shortTerm) {
      if (entry.content.toLowerCase().includes(lowerQuery)) {
        results.push(entry);
      }
    }

    for (const entry of this.longTerm) {
      if (entry.content.toLowerCase().includes(lowerQuery)) {
        results.push(entry);
      }
    }

    return results;
  }

  searchByType(type: MemoryEntry['type']): MemoryEntry[] {
    const results: MemoryEntry[] = [];

    for (const entry of this.shortTerm) {
      if (entry.type === type) {
        results.push(entry);
      }
    }

    for (const entry of this.longTerm) {
      if (entry.type === type) {
        results.push(entry);
      }
    }

    return results;
  }

  delete(id: string): boolean {
    let index = this.shortTerm.findIndex(e => e.id === id);
    if (index !== -1) {
      this.shortTerm.splice(index, 1);
      this.persist();
      return true;
    }

    index = this.longTerm.findIndex(e => e.id === id);
    if (index !== -1) {
      this.longTerm.splice(index, 1);
      this.persist();
      return true;
    }

    return false;
  }

  clear(): void {
    this.shortTerm = [];
    this.longTerm = [];
    this.persist();
  }

  private promoteOldestToLongTerm(): void {
    if (this.shortTerm.length > 0) {
      const oldest = this.shortTerm.shift();
      if (oldest) {
        this.addLongTerm({
          ...oldest,
          type: 'conversation'
        });
      }
    }
  }

  private pruneOldLongTerm(): void {
    const toRemove = this.longTerm.length - this.config.maxLongTerm + 100;
    if (toRemove > 0) {
      this.longTerm.splice(0, toRemove);
    }
  }

  private async persist(): Promise<void> {
    if (!this.config.enablePersistence) return;

    try {
      const data = {
        shortTerm: this.shortTerm,
        longTerm: this.longTerm,
        updatedAt: Date.now()
      };
      await fs.writeFile(
        path.join(this.config.storagePath, 'memory.json'),
        JSON.stringify(data, null, 2)
      );
    } catch (error) {
      this.logger.error('Failed to persist memory', error);
    }
  }

  private async load(): Promise<void> {
    try {
      const filePath = path.join(this.config.storagePath, 'memory.json');
      const data = await fs.readFile(filePath, 'utf-8');
      const parsed = JSON.parse(data);
      this.shortTerm = parsed.shortTerm || [];
      this.longTerm = parsed.longTerm || [];
    } catch {
      this.logger.debug('No existing memory file found');
    }
  }

  getStats(): { shortTermCount: number; longTermCount: number } {
    return {
      shortTermCount: this.shortTerm.length,
      longTermCount: this.longTerm.length
    };
  }
}
