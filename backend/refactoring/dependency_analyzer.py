"""
Dependency Analyzer

Part 5B: Deterministic Refactoring Blueprint Engine (DRBE)
Analyzes code dependencies to determine safe migration order.
"""

import ast
import os
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, field
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class DependencyGraph:
    """
    Graph representing module dependencies
    
    Attributes:
        modules: Set of all module names
        dependencies: Dict mapping module to its dependencies
        dependents: Dict mapping module to modules that depend on it
        circular: List of circular dependency chains
    """
    modules: Set[str] = field(default_factory=set)
    dependencies: Dict[str, Set[str]] = field(default_factory=dict)
    dependents: Dict[str, Set[str]] = field(default_factory=dict)
    circular: List[List[str]] = field(default_factory=list)
    
    def add_dependency(self, module: str, depends_on: str) -> None:
        """Add a dependency relationship"""
        self.modules.add(module)
        self.modules.add(depends_on)
        
        if module not in self.dependencies:
            self.dependencies[module] = set()
        self.dependencies[module].add(depends_on)
        
        if depends_on not in self.dependents:
            self.dependents[depends_on] = set()
        self.dependents[depends_on].add(module)
    
    def get_dependencies(self, module: str) -> Set[str]:
        """Get direct dependencies of a module"""
        return self.dependencies.get(module, set())
    
    def get_dependents(self, module: str) -> Set[str]:
        """Get modules that depend on this module"""
        return self.dependents.get(module, set())
    
    def get_all_dependencies(self, module: str, visited: Optional[Set[str]] = None) -> Set[str]:
        """Get all transitive dependencies of a module"""
        if visited is None:
            visited = set()
        
        if module in visited:
            return set()
        
        visited.add(module)
        all_deps = set(self.dependencies.get(module, set()))
        
        for dep in list(all_deps):
            all_deps.update(self.get_all_dependencies(dep, visited))
        
        return all_deps
    
    def has_circular_dependency(self, module: str) -> bool:
        """Check if module is part of any circular dependency"""
        return any(module in chain for chain in self.circular)
    
    def __str__(self) -> str:
        """Human-readable summary"""
        lines = [
            f"Dependency Graph:",
            f"  Modules: {len(self.modules)}",
            f"  Dependencies: {sum(len(deps) for deps in self.dependencies.values())}",
            f"  Circular chains: {len(self.circular)}"
        ]
        
        if self.circular:
            lines.append("\n  Circular dependencies:")
            for i, chain in enumerate(self.circular, 1):
                lines.append(f"    {i}. {' -> '.join(chain)}")
        
        return "\n".join(lines)


def analyze_dependencies(root_path: str, package_name: str = "backend") -> DependencyGraph:
    """
    Analyze Python file dependencies in a directory
    
    Args:
        root_path: Root directory to analyze
        package_name: Package name prefix (default: "backend")
    
    Returns:
        DependencyGraph with dependency relationships
    
    Usage:
        graph = analyze_dependencies('backend/', 'backend')
        print(f"Found {len(graph.modules)} modules")
        
        # Find what depends on indicators.base
        dependents = graph.get_dependents('backend.indicators.base')
        print(f"Modules depending on base: {dependents}")
    """
    graph = DependencyGraph()
    root = Path(root_path)
    
    # Find all Python files
    python_files = []
    for path in root.rglob("*.py"):
        if "__pycache__" not in str(path) and "venv" not in str(path):
            python_files.append(path)
    
    # Parse each file and extract imports
    for file_path in python_files:
        try:
            # Convert file path to module name
            relative_path = file_path.relative_to(root.parent)
            module_name = str(relative_path.with_suffix('')).replace(os.sep, '.')
            
            # Parse file
            with open(file_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read(), filename=str(file_path))
            
            # Extract imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.startswith(package_name):
                            graph.add_dependency(module_name, alias.name)
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module and node.module.startswith(package_name):
                        graph.add_dependency(module_name, node.module)
        
        except Exception as e:
            logger.warning(f"Could not parse {file_path}: {e}")
    
    # Detect circular dependencies
    graph.circular = find_circular_dependencies(graph)
    
    return graph


def find_circular_dependencies(graph: DependencyGraph) -> List[List[str]]:
    """
    Find all circular dependency chains using DFS
    
    Args:
        graph: DependencyGraph to analyze
    
    Returns:
        List of circular dependency chains
    
    Usage:
        graph = analyze_dependencies('backend/')
        circular = find_circular_dependencies(graph)
        
        if circular:
            print("Found circular dependencies:")
            for chain in circular:
                print(f"  {' -> '.join(chain)}")
    """
    circular_chains = []
    visited = set()
    rec_stack = set()
    
    def dfs(module: str, path: List[str]) -> None:
        """Depth-first search to find cycles"""
        if module in rec_stack:
            # Found a cycle
            cycle_start = path.index(module)
            cycle = path[cycle_start:] + [module]
            
            # Normalize cycle (smallest element first)
            min_idx = cycle.index(min(cycle[:-1]))
            normalized = cycle[min_idx:-1] + cycle[:min_idx] + [cycle[min_idx]]
            
            # Add if not already found
            if normalized not in circular_chains:
                circular_chains.append(normalized)
            return
        
        if module in visited:
            return
        
        visited.add(module)
        rec_stack.add(module)
        path.append(module)
        
        # Visit dependencies
        for dep in graph.get_dependencies(module):
            dfs(dep, path[:])
        
        rec_stack.remove(module)
    
    # Check all modules
    for module in graph.modules:
        if module not in visited:
            dfs(module, [])
    
    return circular_chains


def get_migration_order(graph: DependencyGraph, modules: List[str] = None) -> List[str]:
    """
    Get safe migration order using topological sort
    
    Args:
        graph: DependencyGraph to analyze
        modules: Specific modules to order (default: all modules)
    
    Returns:
        List of modules in safe migration order (dependencies first)
    
    Raises:
        ValueError: If circular dependencies prevent ordering
    
    Usage:
        graph = analyze_dependencies('backend/')
        
        # Get order for all modules
        order = get_migration_order(graph)
        print("Migration order:", order)
        
        # Get order for specific modules
        indicator_modules = [m for m in graph.modules if 'indicators' in m]
        order = get_migration_order(graph, indicator_modules)
    """
    if modules is None:
        modules = list(graph.modules)
    
    # Check for circular dependencies in subset
    subset_graph = DependencyGraph()
    module_set = set(modules)
    
    for module in modules:
        for dep in graph.get_dependencies(module):
            if dep in module_set:
                subset_graph.add_dependency(module, dep)
    
    circular = find_circular_dependencies(subset_graph)
    if circular:
        raise ValueError(
            f"Cannot determine migration order: circular dependencies found\n"
            f"Chains: {circular}"
        )
    
    # Topological sort using Kahn's algorithm
    in_degree = {m: 0 for m in modules}
    
    for module in modules:
        for dep in graph.get_dependencies(module):
            if dep in module_set:
                in_degree[module] += 1
    
    # Queue of modules with no dependencies
    queue = [m for m in modules if in_degree[m] == 0]
    result = []
    
    while queue:
        # Sort for deterministic order
        queue.sort()
        module = queue.pop(0)
        result.append(module)
        
        # Reduce in-degree for dependents
        for dependent in graph.get_dependents(module):
            if dependent in module_set:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)
    
    if len(result) != len(modules):
        # Should not happen if circular check passed
        missing = set(modules) - set(result)
        raise ValueError(f"Could not order all modules: {missing}")
    
    return result


def suggest_refactoring_order(root_path: str) -> List[Tuple[str, str]]:
    """
    Suggest refactoring order with reasons
    
    Args:
        root_path: Root directory to analyze
    
    Returns:
        List of (module, reason) tuples in suggested order
    
    Usage:
        suggestions = suggest_refactoring_order('backend/')
        
        for i, (module, reason) in enumerate(suggestions, 1):
            print(f"{i}. {module}")
            print(f"   Reason: {reason}")
    """
    graph = analyze_dependencies(root_path)
    
    # Calculate metrics for each module
    module_metrics = {}
    for module in graph.modules:
        deps_count = len(graph.get_dependencies(module))
        dependents_count = len(graph.get_dependents(module))
        is_circular = graph.has_circular_dependency(module)
        
        module_metrics[module] = {
            'deps': deps_count,
            'dependents': dependents_count,
            'circular': is_circular
        }
    
    # Prioritize modules
    suggestions = []
    
    # 1. Fix circular dependencies first
    circular_modules = [m for m in graph.modules if graph.has_circular_dependency(m)]
    if circular_modules:
        for module in sorted(circular_modules):
            suggestions.append((
                module,
                f"Part of circular dependency (fix required)"
            ))
    
    # 2. Base modules with many dependents (high impact)
    base_modules = [
        m for m in graph.modules 
        if module_metrics[m]['dependents'] > 5 
        and not graph.has_circular_dependency(m)
    ]
    for module in sorted(base_modules, key=lambda m: -module_metrics[m]['dependents']):
        suggestions.append((
            module,
            f"Base module with {module_metrics[module]['dependents']} dependents (high impact)"
        ))
    
    # 3. Leaf modules with no dependents (safe to refactor)
    leaf_modules = [
        m for m in graph.modules
        if module_metrics[m]['dependents'] == 0
        and not graph.has_circular_dependency(m)
    ]
    for module in sorted(leaf_modules):
        suggestions.append((
            module,
            f"Leaf module with no dependents (safe, low risk)"
        ))
    
    # 4. Remaining modules
    remaining = set(graph.modules) - set(m for m, _ in suggestions)
    for module in sorted(remaining):
        suggestions.append((
            module,
            f"Standard module ({module_metrics[module]['deps']} deps, "
            f"{module_metrics[module]['dependents']} dependents)"
        ))
    
    return suggestions


def visualize_dependencies(graph: DependencyGraph, output_format: str = "mermaid") -> str:
    """
    Generate dependency visualization
    
    Args:
        graph: DependencyGraph to visualize
        output_format: "mermaid" or "dot"
    
    Returns:
        Visualization markup string
    
    Usage:
        graph = analyze_dependencies('backend/')
        mermaid = visualize_dependencies(graph, "mermaid")
        
        # Save to file for rendering
        with open('dependencies.mmd', 'w') as f:
            f.write(mermaid)
    """
    if output_format == "mermaid":
        lines = ["graph TD"]
        
        # Add nodes and edges
        for module in sorted(graph.modules):
            safe_name = module.replace('.', '_')
            
            for dep in sorted(graph.get_dependencies(module)):
                dep_safe = dep.replace('.', '_')
                
                # Highlight circular dependencies
                if any(module in chain and dep in chain for chain in graph.circular):
                    lines.append(f"    {safe_name}[{module}] -->|CIRCULAR| {dep_safe}[{dep}]")
                    lines.append(f"    style {safe_name} fill:#ff9999")
                    lines.append(f"    style {dep_safe} fill:#ff9999")
                else:
                    lines.append(f"    {safe_name}[{module}] --> {dep_safe}[{dep}]")
        
        return "\n".join(lines)
    
    elif output_format == "dot":
        lines = ["digraph dependencies {"]
        lines.append("    rankdir=LR;")
        
        for module in sorted(graph.modules):
            for dep in sorted(graph.get_dependencies(module)):
                is_circular = any(
                    module in chain and dep in chain 
                    for chain in graph.circular
                )
                
                if is_circular:
                    lines.append(f'    "{module}" -> "{dep}" [color=red,penwidth=2];')
                else:
                    lines.append(f'    "{module}" -> "{dep}";')
        
        lines.append("}")
        return "\n".join(lines)
    
    else:
        raise ValueError(f"Unknown format: {output_format}")
