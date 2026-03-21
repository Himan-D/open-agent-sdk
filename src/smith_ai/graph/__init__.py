"""Knowledge Graph Network - Graph-based knowledge representation for AGI agents.

This module implements a comprehensive knowledge graph with:

1. GRAPH STRUCTURE
   - Nodes: Entities, concepts, facts, agents, tools
   - Edges: Relationships with typed connections
   - Hyperedges: N-ary relationships
   - Attributes: Node and edge properties

2. GRAPH OPERATIONS
   - Traversal: BFS, DFS, bidirectional
   - Path finding: Shortest path, all paths
   - Subgraph extraction
   - Graph merging

3. QUERY ENGINE
   - Pattern matching
   - Graph queries (Cypher-like)
   - Similarity search
   - Neighborhood queries

4. INFERENCE ENGINE
   - Rule-based inference
   - Path traversal inference
   - Bayesian updates
   - Fuzzy matching

5. AGENT INTEGRATION
   - Memory as graph
   - Experience encoding
   - Knowledge sharing between agents
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import re
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Type, Union


# ============================================================================
# CORE TYPES
# ============================================================================

class NodeType(str, Enum):
    """Types of nodes in the knowledge graph."""
    ENTITY = "entity"              # Real-world entity
    CONCEPT = "concept"           # Abstract concept
    FACT = "fact"                # Factual statement
    AGENT = "agent"              # AI agent
    TOOL = "tool"                # Tool or capability
    TASK = "task"                # Task or goal
    MEMORY = "memory"            # Episodic memory
    RULE = "rule"                # Inference rule
    ACTION = "action"            # Action taken
    EVENT = "event"              # Event that occurred
    BELIEF = "belief"            # Agent belief
    VALUE = "value"              # Value or principle


class EdgeType(str, Enum):
    """Types of edges (relationships) in the knowledge graph."""
    IS_A = "is_a"                # Inheritance
    PART_OF = "part_of"          # Composition
    HAS_PROPERTY = "has_property" # Attribute
    CAUSES = "causes"            # Causation
    ENABLES = "enables"          # Capability
    DEPENDS_ON = "depends_on"    # Dependency
    RELATED_TO = "related_to"    # General relation
    SIMILAR_TO = "similar_to"    # Similarity
    BEFORE = "before"            # Temporal: A before B
    AFTER = "after"              # Temporal: A after B
    USES = "uses"                # Tool/knowledge usage
    ACHIEVES = "achieves"        # Goal achievement
    LEADS_TO = "leads_to"        # Sequence
    KNOWS = "knows"              # Knowledge relation
    BELIEVES = "believes"        # Belief relation
    LEARNED_FROM = "learned_from" # Learning relation


@dataclass
class Node:
    """A node in the knowledge graph."""
    id: str
    label: str
    node_type: NodeType
    properties: Dict[str, Any] = field(default_factory=dict)
    embeddings: Optional[List[float]] = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.id:
            self.id = hashlib.md5(f"{self.label}{self.node_type.value}{time.time()}".encode()).hexdigest()[:16]
    
    def add_property(self, key: str, value: Any) -> None:
        self.properties[key] = value
        self.updated_at = time.time()
    
    def get_property(self, key: str, default: Any = None) -> Any:
        return self.properties.get(key, default)
    
    def has_property(self, key: str) -> bool:
        return key in self.properties
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "type": self.node_type.value,
            "properties": self.properties,
            "confidence": self.confidence,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata,
        }


@dataclass
class Edge:
    """An edge (relationship) in the knowledge graph."""
    id: str
    source_id: str
    target_id: str
    edge_type: EdgeType
    weight: float = 1.0
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    confidence: float = 1.0
    bidirectional: bool = False
    
    def __post_init__(self):
        if not self.id:
            self.id = hashlib.md5(
                f"{self.source_id}{self.edge_type.value}{self.target_id}{time.time()}".encode()
            ).hexdigest()[:16]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "source": self.source_id,
            "target": self.target_id,
            "type": self.edge_type.value,
            "weight": self.weight,
            "properties": self.properties,
            "confidence": self.confidence,
            "bidirectional": self.bidirectional,
        }


@dataclass
class Path:
    """A path through the knowledge graph."""
    nodes: List[Node]
    edges: List[Edge]
    total_weight: float = 0.0
    
    def length(self) -> int:
        return len(self.nodes)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "nodes": [n.id for n in self.nodes],
            "edges": [e.id for e in self.edges],
            "length": self.length(),
            "total_weight": self.total_weight,
        }


# ============================================================================
# KNOWLEDGE GRAPH
# ============================================================================

class KnowledgeGraph:
    """A comprehensive knowledge graph for AGI agents.
    
    Features:
    - Multi-type nodes and edges
    - Graph traversal algorithms
    - Pattern matching and queries
    - Inference engine
    - Agent memory integration
    """
    
    def __init__(self, name: str = "default"):
        self.name = name
        self.nodes: Dict[str, Node] = {}
        self.edges: Dict[str, Edge] = {}
        
        # Indexes for fast lookup
        self._label_index: Dict[str, Set[str]] = defaultdict(set)
        self._type_index: Dict[NodeType, Set[str]] = defaultdict(set)
        self._edge_type_index: Dict[EdgeType, Set[str]] = defaultdict(set)
        self._outgoing: Dict[str, Set[str]] = defaultdict(set)  # node_id -> edge_ids
        self._incoming: Dict[str, Set[str]] = defaultdict(set)  # node_id -> edge_ids
        
        # Statistics
        self.stats = {
            "nodes_created": 0,
            "edges_created": 0,
            "queries_executed": 0,
            "inferences_made": 0,
        }
    
    # -------------------------------------------------------------------------
    # NODE OPERATIONS
    # -------------------------------------------------------------------------
    
    def add_node(
        self,
        label: str,
        node_type: NodeType,
        properties: Optional[Dict[str, Any]] = None,
        node_id: Optional[str] = None,
        confidence: float = 1.0,
    ) -> Node:
        """Add a node to the graph."""
        node = Node(
            id=node_id or "",
            label=label,
            node_type=node_type,
            properties=properties or {},
            confidence=confidence,
        )
        
        self.nodes[node.id] = node
        self._label_index[label].add(node.id)
        self._type_index[node_type].add(node.id)
        self.stats["nodes_created"] += 1
        
        return node
    
    def get_node(self, node_id: str) -> Optional[Node]:
        """Get a node by ID."""
        return self.nodes.get(node_id)
    
    def get_nodes_by_label(self, label: str) -> List[Node]:
        """Get all nodes with a specific label."""
        node_ids = self._label_index.get(label, set())
        return [self.nodes[nid] for nid in node_ids if nid in self.nodes]
    
    def get_nodes_by_type(self, node_type: NodeType) -> List[Node]:
        """Get all nodes of a specific type."""
        node_ids = self._type_index.get(node_type, set())
        return [self.nodes[nid] for nid in node_ids if nid in self.nodes]
    
    def update_node(self, node_id: str, properties: Dict[str, Any]) -> bool:
        """Update a node's properties."""
        node = self.nodes.get(node_id)
        if node:
            for key, value in properties.items():
                node.add_property(key, value)
            return True
        return False
    
    def delete_node(self, node_id: str) -> bool:
        """Delete a node and all its edges."""
        if node_id not in self.nodes:
            return False
        
        # Remove from indexes
        node = self.nodes[node_id]
        self._label_index[node.label].discard(node_id)
        self._type_index[node.node_type].discard(node_id)
        
        # Remove all edges
        edge_ids = list(self._outgoing.get(node_id, set())) + list(self._incoming.get(node_id, set()))
        for edge_id in edge_ids:
            self.delete_edge(edge_id)
        
        del self.nodes[node_id]
        return True
    
    # -------------------------------------------------------------------------
    # EDGE OPERATIONS
    # -------------------------------------------------------------------------
    
    def add_edge(
        self,
        source_id: str,
        target_id: str,
        edge_type: EdgeType,
        weight: float = 1.0,
        properties: Optional[Dict[str, Any]] = None,
        bidirectional: bool = False,
        edge_id: Optional[str] = None,
        confidence: float = 1.0,
    ) -> Optional[Edge]:
        """Add an edge to the graph."""
        if source_id not in self.nodes or target_id not in self.nodes:
            return None
        
        edge = Edge(
            id=edge_id or "",
            source_id=source_id,
            target_id=target_id,
            edge_type=edge_type,
            weight=weight,
            properties=properties or {},
            confidence=confidence,
            bidirectional=bidirectional,
        )
        
        self.edges[edge.id] = edge
        self._outgoing[source_id].add(edge.id)
        self._incoming[target_id].add(edge.id)
        self._edge_type_index[edge_type].add(edge.id)
        
        # Add reverse edge if bidirectional
        if bidirectional:
            reverse_edge = Edge(
                id="",
                source_id=target_id,
                target_id=source_id,
                edge_type=edge_type,
                weight=weight,
                properties=properties or {},
                confidence=confidence,
                bidirectional=False,
            )
            self.edges[reverse_edge.id] = reverse_edge
            self._outgoing[target_id].add(reverse_edge.id)
            self._incoming[source_id].add(reverse_edge.id)
        
        self.stats["edges_created"] += 1
        return edge
    
    def get_edge(self, edge_id: str) -> Optional[Edge]:
        """Get an edge by ID."""
        return self.edges.get(edge_id)
    
    def get_edges_by_type(self, edge_type: EdgeType) -> List[Edge]:
        """Get all edges of a specific type."""
        edge_ids = self._edge_type_index.get(edge_type, set())
        return [self.edges[eid] for eid in edge_ids if eid in self.edges]
    
    def delete_edge(self, edge_id: str) -> bool:
        """Delete an edge."""
        edge = self.edges.get(edge_id)
        if not edge:
            return False
        
        self._outgoing[edge.source_id].discard(edge_id)
        self._incoming[edge.target_id].discard(edge_id)
        self._edge_type_index[edge.edge_type].discard(edge_id)
        
        del self.edges[edge_id]
        return True
    
    def get_neighbors(self, node_id: str, edge_type: Optional[EdgeType] = None) -> List[Tuple[Node, Edge]]:
        """Get all neighboring nodes."""
        if node_id not in self.nodes:
            return []
        
        neighbors = []
        for edge_id in self._outgoing.get(node_id, set()):
            edge = self.edges.get(edge_id)
            if edge and (edge_type is None or edge.edge_type == edge_type):
                neighbor = self.nodes.get(edge.target_id)
                if neighbor:
                    neighbors.append((neighbor, edge))
        
        return neighbors
    
    # -------------------------------------------------------------------------
    # TRAVERSAL ALGORITHMS
    # -------------------------------------------------------------------------
    
    def bfs(
        self,
        start_id: str,
        max_depth: int = 5,
        edge_filter: Optional[Callable[[Edge], bool]] = None,
    ) -> List[Path]:
        """Breadth-first search from a starting node."""
        if start_id not in self.nodes:
            return []
        
        paths = []
        queue = deque([(start_id, [self.nodes[start_id]], [])])
        visited = {start_id}
        
        while queue:
            current_id, node_list, edge_list = queue.popleft()
            current_depth = len(node_list) - 1
            
            if current_depth >= max_depth:
                continue
            
            for neighbor, edge in self.get_neighbors(current_id):
                if neighbor.id not in visited:
                    if edge_filter is None or edge_filter(edge):
                        new_nodes = node_list + [neighbor]
                        new_edges = edge_list + [edge]
                        paths.append(Path(nodes=new_nodes, edges=new_edges, total_weight=sum(e.weight for e in new_edges)))
                        queue.append((neighbor.id, new_nodes, new_edges))
                        visited.add(neighbor.id)
        
        return paths
    
    def dfs(
        self,
        start_id: str,
        max_depth: int = 5,
        edge_filter: Optional[Callable[[Edge], bool]] = None,
    ) -> List[Path]:
        """Depth-first search from a starting node."""
        if start_id not in self.nodes:
            return []
        
        paths = []
        stack = [(start_id, [self.nodes[start_id]], [])]
        
        while stack:
            current_id, node_list, edge_list = stack.pop()
            current_depth = len(node_list) - 1
            
            if current_depth >= max_depth:
                continue
            
            for neighbor, edge in self.get_neighbors(current_id):
                if neighbor not in node_list:
                    if edge_filter is None or edge_filter(edge):
                        new_nodes = node_list + [neighbor]
                        new_edges = edge_list + [edge]
                        paths.append(Path(nodes=new_nodes, edges=new_edges, total_weight=sum(e.weight for e in new_edges)))
                        stack.append((neighbor.id, new_nodes, new_edges))
        
        return paths
    
    def shortest_path(self, start_id: str, end_id: str, max_depth: int = 10) -> Optional[Path]:
        """Find the shortest path between two nodes."""
        if start_id not in self.nodes or end_id not in self.nodes:
            return None
        
        if start_id == end_id:
            return Path(nodes=[self.nodes[start_id]], edges=[])
        
        queue = deque([(start_id, [self.nodes[start_id]], [])])
        visited = {start_id}
        
        while queue:
            current_id, node_list, edge_list = queue.popleft()
            current_depth = len(node_list) - 1
            
            if current_depth >= max_depth:
                continue
            
            for neighbor, edge in self.get_neighbors(current_id):
                if neighbor.id not in visited:
                    new_nodes = node_list + [neighbor]
                    new_edges = edge_list + [edge]
                    new_weight = sum(e.weight for e in new_edges)
                    
                    if neighbor.id == end_id:
                        return Path(nodes=new_nodes, edges=new_edges, total_weight=new_weight)
                    
                    queue.append((neighbor.id, new_nodes, new_edges))
                    visited.add(neighbor.id)
        
        return None
    
    def find_all_paths(self, start_id: str, end_id: str, max_depth: int = 5) -> List[Path]:
        """Find all paths between two nodes."""
        if start_id not in self.nodes or end_id not in self.nodes:
            return []
        
        paths = []
        stack = [(start_id, [self.nodes[start_id]], [])]
        
        while stack:
            current_id, node_list, edge_list = stack.pop()
            current_depth = len(node_list) - 1
            
            if current_depth >= max_depth:
                continue
            
            for neighbor, edge in self.get_neighbors(current_id):
                if neighbor not in node_list:
                    new_nodes = node_list + [neighbor]
                    new_edges = edge_list + [edge]
                    
                    if neighbor.id == end_id:
                        paths.append(Path(nodes=new_nodes, edges=new_edges, total_weight=sum(e.weight for e in new_edges)))
                    else:
                        stack.append((neighbor.id, new_nodes, new_edges))
        
        return paths
    
    # -------------------------------------------------------------------------
    # QUERY ENGINE
    # -------------------------------------------------------------------------
    
    def query(self, pattern: str) -> List[Tuple[Node, Edge, Node]]:
        """Query the graph with a simple pattern language.
        
        Pattern examples:
        - "Person -> KNOWS -> Person"
        - "Concept IS_A Entity"
        - "Tool USES Algorithm"
        """
        self.stats["queries_executed"] += 1
        
        results = []
        
        # Parse pattern
        parts = pattern.split("->")
        if len(parts) == 2:
            source_type, rest = parts[0].strip(), parts[1].strip()
            target_and_edge = rest.split("<-")
            
            if len(target_and_edge) == 2:
                target_type = target_and_edge[0].strip()
                edge_type_str = target_and_edge[1].strip()
            else:
                target_type = rest.split()[0] if " " in rest else rest
                edge_type_str = rest.split()[1] if " " in rest else "RELATED_TO"
            
            # Find edges
            for edge in self.edges.values():
                source = self.nodes.get(edge.source_id)
                target = self.nodes.get(edge.target_id)
                
                if source and target:
                    source_match = source_type == "*" or source.label == source_type or source.node_type.value == source_type
                    target_match = target_type == "*" or target.label == target_type or target.node_type.value == target_type
                    edge_match = edge_type_str == "*" or edge.edge_type.value == edge_type_str
                    
                    if source_match and target_match and edge_match:
                        results.append((source, edge, target))
        
        return results
    
    def find_similar(self, node_id: str, limit: int = 5) -> List[Tuple[Node, float]]:
        """Find similar nodes based on relationships."""
        if node_id not in self.nodes:
            return []
        
        source_node = self.nodes[node_id]
        similarity: Dict[str, float] = defaultdict(float)
        
        # Get neighbors' neighbors
        for neighbor, _ in self.get_neighbors(node_id):
            for n2, edge in self.get_neighbors(neighbor.id):
                if n2.id != node_id:
                    similarity[n2.id] += edge.weight * 0.5
            
            # Direct neighbor similarity
            similarity[neighbor.id] += 1.0
        
        # Sort by similarity
        sorted_nodes = sorted(similarity.items(), key=lambda x: x[1], reverse=True)[:limit]
        
        return [(self.nodes[nid], score) for nid, score in sorted_nodes if nid in self.nodes]
    
    def get_subgraph(self, node_ids: List[str], depth: int = 1) -> "KnowledgeGraph":
        """Extract a subgraph containing the given nodes."""
        subgraph = KnowledgeGraph(name=f"{self.name}_subgraph")
        
        # Add nodes
        for nid in node_ids:
            node = self.nodes.get(nid)
            if node:
                subgraph.add_node(
                    label=node.label,
                    node_type=node.node_type,
                    properties=node.properties.copy(),
                    node_id=node.id,
                    confidence=node.confidence,
                )
        
        # Add edges within the set
        for nid in node_ids:
            for neighbor, edge in self.get_neighbors(nid):
                if neighbor.id in node_ids:
                    subgraph.add_edge(
                        source_id=edge.source_id,
                        target_id=edge.target_id,
                        edge_type=edge.edge_type,
                        weight=edge.weight,
                        properties=edge.properties.copy(),
                        confidence=edge.confidence,
                    )
        
        return subgraph
    
    # -------------------------------------------------------------------------
    # INFERENCE ENGINE
    # -------------------------------------------------------------------------
    
    def infer_transitive(self, start_id: str, edge_type: EdgeType, max_depth: int = 5) -> Set[str]:
        """Infer all nodes reachable via transitive closure."""
        reachable = set()
        queue = deque([start_id])
        depth = {start_id: 0}
        
        while queue:
            current = queue.popleft()
            current_depth = depth[current]
            
            if current_depth >= max_depth:
                continue
            
            for neighbor, edge in self.get_neighbors(current, edge_type):
                if neighbor.id not in reachable:
                    reachable.add(neighbor.id)
                    queue.append(neighbor.id)
                    depth[neighbor.id] = current_depth + 1
        
        return reachable
    
    def infer_is_a_chain(self, node_id: str) -> List[Node]:
        """Get the IS_A inheritance chain for a node."""
        chain = []
        current_id = node_id
        
        for _ in range(20):  # Max depth
            node = self.nodes.get(current_id)
            if not node:
                break
            
            chain.append(node)
            
            # Find parent via IS_A
            parents = []
            for neighbor, edge in self.get_neighbors(current_id, EdgeType.IS_A):
                parents.append(neighbor)
            
            if not parents:
                break
            
            current_id = parents[0].id
        
        return chain
    
    def apply_rule(self, rule: Callable[[Node, Edge, Node], Optional[Tuple[Node, Edge, Node]]]) -> int:
        """Apply an inference rule to the graph."""
        inferences = 0
        
        for source in self.nodes.values():
            for neighbor, edge in self.get_neighbors(source.id):
                result = rule(source, edge, neighbor)
                if result:
                    new_source, new_edge, new_target = result
                    if self.add_edge(new_source.id, new_target.id, new_edge.edge_type, weight=new_edge.weight):
                        inferences += 1
                        self.stats["inferences_made"] += 1
        
        return inferences
    
    # -------------------------------------------------------------------------
    # AGENT MEMORY INTEGRATION
    # -------------------------------------------------------------------------
    
    def store_episode(self, agent_id: str, event: str, result: str, context: Dict[str, Any]) -> Node:
        """Store an episodic memory as a graph structure."""
        # Create event node
        event_node = self.add_node(
            label=event[:50],
            node_type=NodeType.MEMORY,
            properties={"event": event, "result": result, "context": json.dumps(context)},
        )
        
        # Create agent node if not exists
        agent_nodes = self.get_nodes_by_label(agent_id)
        if agent_nodes:
            agent_node = agent_nodes[0]
        else:
            agent_node = self.add_node(
                label=agent_id,
                node_type=NodeType.AGENT,
                properties={},
            )
        
        # Link agent to event
        self.add_edge(
            source_id=agent_node.id,
            target_id=event_node.id,
            edge_type=EdgeType.LEARNED_FROM,
        )
        
        return event_node
    
    def retrieve_episodes(self, agent_id: str, pattern: str, limit: int = 10) -> List[Node]:
        """Retrieve episodic memories for an agent."""
        agent_nodes = self.get_nodes_by_label(agent_id)
        if not agent_nodes:
            return []
        
        agent_node = agent_nodes[0]
        episodes = []
        
        for episode, _ in self.get_neighbors(agent_node.id, EdgeType.LEARNED_FROM):
            if pattern.lower() in episode.label.lower() or pattern.lower() in episode.get_property("event", "").lower():
                episodes.append(episode)
        
        return episodes[:limit]
    
    def share_knowledge(self, from_agent: str, to_agent: str, knowledge: str) -> bool:
        """Share knowledge between agents."""
        # Find or create knowledge node
        knowledge_nodes = self.get_nodes_by_label(knowledge)
        if knowledge_nodes:
            knowledge_node = knowledge_nodes[0]
        else:
            knowledge_node = self.add_node(
                label=knowledge,
                node_type=NodeType.CONCEPT,
                properties={},
            )
        
        # Create agent nodes
        from_nodes = self.get_nodes_by_label(from_agent)
        to_nodes = self.get_nodes_by_label(to_agent)
        
        from_node = from_nodes[0] if from_nodes else self.add_node(from_agent, NodeType.AGENT)
        to_node = to_nodes[0] if to_nodes else self.add_node(to_agent, NodeType.AGENT)
        
        # Link agents to knowledge
        self.add_edge(from_node.id, knowledge_node.id, EdgeType.KNOWS)
        self.add_edge(to_node.id, knowledge_node.id, EdgeType.KNOWS)
        
        return True
    
    # -------------------------------------------------------------------------
    # UTILITY METHODS
    # -------------------------------------------------------------------------
    
    def to_dict(self) -> Dict[str, Any]:
        """Export graph as dictionary."""
        return {
            "name": self.name,
            "nodes": [n.to_dict() for n in self.nodes.values()],
            "edges": [e.to_dict() for e in self.edges.values()],
            "stats": self.stats,
        }
    
    def summary(self) -> str:
        """Get a summary of the graph."""
        return (
            f"KnowledgeGraph '{self.name}': "
            f"{len(self.nodes)} nodes, {len(self.edges)} edges, "
            f"{self.stats['queries_executed']} queries, "
            f"{self.stats['inferences_made']} inferences"
        )
    
    def merge(self, other: "KnowledgeGraph") -> None:
        """Merge another graph into this one."""
        for node in other.nodes.values():
            if node.id not in self.nodes:
                self.add_node(
                    label=node.label,
                    node_type=node.node_type,
                    properties=node.properties.copy(),
                    node_id=node.id,
                    confidence=node.confidence,
                )
        
        for edge in other.edges.values():
            if edge.id not in self.edges:
                if edge.source_id in self.nodes and edge.target_id in self.nodes:
                    self.add_edge(
                        source_id=edge.source_id,
                        target_id=edge.target_id,
                        edge_type=edge.edge_type,
                        weight=edge.weight,
                        properties=edge.properties.copy(),
                        confidence=edge.confidence,
                    )


# ============================================================================
# GRAPH NETWORK - CONNECTED KNOWLEDGE GRAPHS
# ============================================================================

class GraphNetwork:
    """A network of interconnected knowledge graphs for multi-agent systems.
    
    This enables:
    - Distributed knowledge across agents
    - Knowledge sharing and transfer
    - Collaborative reasoning
    - Emergent understanding
    """
    
    def __init__(self, name: str = "global"):
        self.name = name
        self.graphs: Dict[str, KnowledgeGraph] = {}
        self.connections: Dict[Tuple[str, str], EdgeType] = {}  # (graph1, graph2) -> connection_type
        self.global_graph = KnowledgeGraph(name="global")
        
        # Agent registries
        self.agent_graphs: Dict[str, str] = {}  # agent_id -> graph_name
        self.graph_agents: Dict[str, List[str]] = defaultdict(list)  # graph_name -> agent_ids
    
    def create_graph(self, name: str) -> KnowledgeGraph:
        """Create a new knowledge graph in the network."""
        graph = KnowledgeGraph(name=name)
        self.graphs[name] = graph
        return graph
    
    def get_graph(self, name: str) -> Optional[KnowledgeGraph]:
        """Get a graph by name."""
        return self.graphs.get(name)
    
    def register_agent(self, agent_id: str, graph_name: Optional[str] = None) -> KnowledgeGraph:
        """Register an agent with its own knowledge graph."""
        if graph_name is None:
            graph_name = f"agent_{agent_id}"
        
        if graph_name not in self.graphs:
            self.create_graph(graph_name)
        
        self.agent_graphs[agent_id] = graph_name
        self.graph_agents[graph_name].append(agent_id)
        
        return self.graphs[graph_name]
    
    def get_agent_graph(self, agent_id: str) -> Optional[KnowledgeGraph]:
        """Get the knowledge graph for an agent."""
        graph_name = self.agent_graphs.get(agent_id)
        if graph_name:
            return self.graphs.get(graph_name)
        return None
    
    def connect_graphs(self, graph1_name: str, graph2_name: str, connection_type: EdgeType = EdgeType.RELATED_TO) -> bool:
        """Connect two knowledge graphs in the network."""
        if graph1_name in self.graphs and graph2_name in self.graphs:
            self.connections[(graph1_name, graph2_name)] = connection_type
            self.connections[(graph2_name, graph1_name)] = connection_type
            return True
        return False
    
    def share_between_agents(self, from_agent: str, to_agent: str, knowledge: str) -> bool:
        """Share knowledge from one agent's graph to another."""
        from_graph = self.get_agent_graph(from_agent)
        to_graph = self.get_agent_graph(to_agent)
        
        if from_graph and to_graph:
            return from_graph.share_knowledge(from_agent, to_agent, knowledge)
        
        return False
    
    def federated_query(self, agent_ids: List[str], pattern: str) -> List[Tuple[str, Node, Edge, Node]]:
        """Query across multiple agent graphs."""
        results = []
        
        for agent_id in agent_ids:
            graph = self.get_agent_graph(agent_id)
            if graph:
                query_results = graph.query(pattern)
                for source, edge, target in query_results:
                    results.append((agent_id, source, edge, target))
        
        return results
    
    def merge_to_global(self, graph_name: str) -> int:
        """Merge a graph into the global knowledge graph."""
        graph = self.graphs.get(graph_name)
        if graph:
            initial_count = len(self.global_graph.nodes)
            self.global_graph.merge(graph)
            return len(self.global_graph.nodes) - initial_count
        return 0
    
    def get_network_stats(self) -> Dict[str, Any]:
        """Get statistics about the network."""
        total_nodes = sum(len(g.nodes) for g in self.graphs.values())
        total_edges = sum(len(g.edges) for g in self.graphs.values())
        
        return {
            "name": self.name,
            "total_graphs": len(self.graphs),
            "total_nodes": total_nodes,
            "total_edges": total_edges,
            "registered_agents": len(self.agent_graphs),
            "connections": len(self.connections) // 2,  # Divided by 2 for bidirectional
            "global_nodes": len(self.global_graph.nodes),
        }


# ============================================================================
# KNOWLEDGE AGENT - AGENT WITH GRAPH-BASED MEMORY
# ============================================================================

class KnowledgeAgent:
    """An agent that uses a knowledge graph as its memory and reasoning engine.
    
    Features:
    - Knowledge graph as primary memory
    - Episodic memory storage
    - Relationship-based reasoning
    - Knowledge sharing with other agents
    - Path-finding for complex reasoning
    """
    
    def __init__(
        self,
        agent_id: str,
        role: str,
        goal: str,
        network: Optional[GraphNetwork] = None,
        verbose: bool = True,
    ):
        self.agent_id = agent_id
        self.role = role
        self.goal = goal
        self.verbose = verbose
        
        # Create or join network
        self.network = network or GraphNetwork(name=f"network_{agent_id}")
        
        # Register in network
        self.graph = self.network.register_agent(agent_id)
        
        # Add agent node
        self.node = self.graph.add_node(
            label=agent_id,
            node_type=NodeType.AGENT,
            properties={"role": role, "goal": goal},
        )
        
        # Add role and goal as nodes
        self.role_node = self.graph.add_node(label=role, node_type=NodeType.CONCEPT)
        self.goal_node = self.graph.add_node(label=goal, node_type=NodeType.TASK)
        
        self.graph.add_edge(self.node.id, self.role_node.id, EdgeType.IS_A)
        self.graph.add_edge(self.node.id, self.goal_node.id, EdgeType.ACHIEVES)
        
        # Reasoning state
        self.current_context: List[Node] = []
        self.reasoning_history: List[Path] = []
    
    def learn(self, concept: str, properties: Optional[Dict[str, Any]] = None, related_to: Optional[str] = None) -> Node:
        """Learn a new concept and connect it to existing knowledge."""
        if self.verbose:
            print(f"[{self.agent_id}] Learning: {concept}")
        
        node = self.graph.add_node(
            label=concept,
            node_type=NodeType.CONCEPT,
            properties=properties or {},
        )
        
        if related_to:
            related_nodes = self.graph.get_nodes_by_label(related_to)
            for rel_node in related_nodes:
                self.graph.add_edge(rel_node.id, node.id, EdgeType.RELATED_TO)
        
        # Connect to agent
        self.graph.add_edge(self.node.id, node.id, EdgeType.KNOWS)
        
        return node
    
    def remember(self, pattern: str, limit: int = 5) -> List[Node]:
        """Remember concepts matching a pattern."""
        if self.verbose:
            print(f"[{self.agent_id}] Remembering: {pattern}")
        
        nodes = self.graph.get_nodes_by_label(pattern)
        if nodes:
            return nodes[:limit]
        
        # Search in properties
        results = []
        for node in self.graph.nodes.values():
            if pattern.lower() in node.label.lower():
                results.append(node)
        
        return results[:limit]
    
    def relate(self, concept1: str, concept2: str, relationship: EdgeType, bidirectional: bool = True) -> bool:
        """Create a relationship between two concepts."""
        nodes1 = self.graph.get_nodes_by_label(concept1)
        nodes2 = self.graph.get_nodes_by_label(concept2)
        
        if nodes1 and nodes2:
            edge = self.graph.add_edge(
                source_id=nodes1[0].id,
                target_id=nodes2[0].id,
                edge_type=relationship,
                bidirectional=bidirectional,
            )
            
            if edge and self.verbose:
                print(f"[{self.agent_id}] Related: {concept1} --[{relationship.value}]--> {concept2}")
            
            return edge is not None
        
        return False
    
    def reason(self, from_concept: str, to_concept: str) -> Optional[Path]:
        """Find reasoning path between two concepts."""
        from_nodes = self.graph.get_nodes_by_label(from_concept)
        to_nodes = self.graph.get_nodes_by_label(to_concept)
        
        if from_nodes and to_nodes:
            if self.verbose:
                print(f"[{self.agent_id}] Reasoning: {from_concept} -> {to_concept}")
            
            path = self.graph.shortest_path(from_nodes[0].id, to_nodes[0].id)
            
            if path:
                self.reasoning_history.append(path)
                
                if self.verbose:
                    print(f"[{self.agent_id}] Found path: {' -> '.join(n.label for n in path.nodes)}")
            
            return path
        
        return None
    
    def infer(self, concept: str, relationship: EdgeType = EdgeType.IS_A) -> Set[Node]:
        """Infer all concepts related to this concept via a relationship."""
        nodes = self.graph.get_nodes_by_label(concept)
        
        if nodes:
            inferred = self.graph.infer_transitive(nodes[0].id, relationship)
            return {self.graph.nodes[nid] for nid in inferred if nid in self.graph.nodes}
        
        return set()
    
    def store_experience(self, event: str, result: str, context: Dict[str, Any]) -> Node:
        """Store an experience in episodic memory."""
        if self.verbose:
            print(f"[{self.agent_id}] Storing experience: {event[:30]}...")
        
        return self.graph.store_episode(self.agent_id, event, result, context)
    
    def recall_experiences(self, pattern: str, limit: int = 10) -> List[Node]:
        """Recall experiences matching a pattern."""
        return self.graph.retrieve_episodes(self.agent_id, pattern, limit)
    
    def share_knowledge(self, other_agent: str, knowledge: str) -> bool:
        """Share knowledge with another agent in the network."""
        if self.verbose:
            print(f"[{self.agent_id}] Sharing '{knowledge}' with {other_agent}")
        
        return self.network.share_between_agents(self.agent_id, other_agent, knowledge)
    
    def receive_knowledge(self) -> List[Node]:
        """Receive knowledge shared by other agents."""
        shared = []
        
        for agent_id, graph_name in self.network.agent_graphs.items():
            if agent_id != self.agent_id:
                graph = self.network.get_graph(graph_name)
                if graph:
                    for node in graph.nodes.values():
                        edges_from_agent = [e for e in graph.edges.values() if e.source_id == node.id]
                        if edges_from_agent and EdgeType.KNOWS in [e.edge_type for e in edges_from_agent]:
                            shared.append(node)
        
        return shared
    
    def think(self, query: str) -> Dict[str, Any]:
        """Think about a query using the knowledge graph."""
        if self.verbose:
            print(f"[{self.agent_id}] Thinking about: {query}")
        
        results = {
            "query": query,
            "learned": [],
            "remembered": [],
            "paths": [],
            "inferred": [],
        }
        
        # Learn if new
        if "explain" in query.lower() or "what is" in query.lower():
            concept = query.replace("explain", "").replace("what is", "").strip()
            if concept:
                node = self.learn(concept)
                results["learned"].append(node.to_dict())
        
        # Remember existing
        results["remembered"] = [n.to_dict() for n in self.remember(query)]
        
        # Find reasoning paths
        words = query.lower().split()
        for i, word in enumerate(words):
            if word in ["between", "from", "to"]:
                if i + 1 < len(words):
                    path = self.reason(words[i-1], words[i+1])
                    if path:
                        results["paths"].append(path.to_dict())
        
        # Infer related concepts
        for word in words:
            inferred = self.infer(word)
            results["inferred"].extend([n.to_dict() for n in inferred])
        
        return results
    
    def get_summary(self) -> str:
        """Get a summary of the agent's knowledge."""
        return (
            f"Agent '{self.agent_id}' ({self.role}):\n"
            f"  Knowledge graph: {len(self.graph.nodes)} nodes, {len(self.graph.edges)} edges\n"
            f"  Reasoning paths: {len(self.reasoning_history)}\n"
            f"  Goal: {self.goal}"
        )


# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================

def create_knowledge_graph(name: str = "default") -> KnowledgeGraph:
    """Create a new knowledge graph."""
    return KnowledgeGraph(name=name)


def create_graph_network(name: str = "global") -> GraphNetwork:
    """Create a new graph network."""
    return GraphNetwork(name=name)


def create_knowledge_agent(
    agent_id: str,
    role: str,
    goal: str,
    network: Optional[GraphNetwork] = None,
) -> KnowledgeAgent:
    """Create a knowledge-based agent."""
    return KnowledgeAgent(
        agent_id=agent_id,
        role=role,
        goal=goal,
        network=network,
    )


__all__ = [
    # Types
    "NodeType",
    "EdgeType",
    # Core
    "Node",
    "Edge",
    "Path",
    # Graphs
    "KnowledgeGraph",
    "GraphNetwork",
    "KnowledgeAgent",
    # Factories
    "create_knowledge_graph",
    "create_graph_network",
    "create_knowledge_agent",
]
