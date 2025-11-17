"""
Dependency Visualizer - Generate dependency graphs and analysis reports

This module provides tools to visualize and analyze code dependencies:
- Parse Python files to extract imports
- Build dependency graphs
- Detect circular dependencies
- Generate visual diagrams (Mermaid, DOT)
- Calculate coupling metrics
- Identify refactoring priorities

Usage:
    visualizer = DependencyVisualizer()
    
    # Analyze a directory
    visualizer.analyze_directory("backend/")
    
    # Check for circular dependencies
    circles = visualizer.find_circular_dependencies()
    print(f"Found {len(circles)} circular dependencies")
    
    # Generate Mermaid diagram
    diagram = visualizer.generate_mermaid_diagram()
    
    # Calculate coupling
    coupling = visualizer.calculate_coupling()
"""

import ast
import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Tuple


@dataclass
class DependencyNode:
    """
    Represents a module in the dependency graph
    
    Attributes:
        name: Module name (e.g., "backend.indicators.rsi")
        file_path: Absolute path to file
        imports: Modules this module imports
        imported_by: Modules that import this module
        external_imports: External dependencies (pandas, numpy, etc.)
    """
    name: str
    file_path: str
    imports: Set[str] = field(default_factory=set)
    imported_by: Set[str] = field(default_factory=set)
    external_imports: Set[str] = field(default_factory=set)
    
    def get_coupling_in(self) -> int:
        """Number of modules that depend on this module"""
        return len(self.imported_by)
    
    def get_coupling_out(self) -> int:
        """Number of modules this module depends on"""
        return len(self.imports)
    
    def get_total_coupling(self) -> int:
        """Total coupling (in + out)"""
        return self.get_coupling_in() + self.get_coupling_out()


class DependencyVisualizer:
    """
    Visualize and analyze code dependencies
    
    Example:
        visualizer = DependencyVisualizer()
        
        # Analyze directory
        visualizer.analyze_directory("backend/")
        
        # Find circular dependencies
        circles = visualizer.find_circular_dependencies()
        for circle in circles:
            print(" -> ".join(circle))
        
        # Calculate metrics
        coupling = visualizer.calculate_coupling()
        print(f"Average coupling: {coupling:.2f}")
        
        # Generate diagram
        mermaid = visualizer.generate_mermaid_diagram()
        with open("dependencies.md", "w") as f:
            f.write("```mermaid\\n")
            f.write(mermaid)
            f.write("\\n```")
    """
    
    def __init__(self):
        self.nodes: Dict[str, DependencyNode] = {}
        self.root_path: Optional[Path] = None
    
    def analyze_directory(self, directory: str, package_name: str = ""):
        """
        Analyze all Python files in a directory
        
        Args:
            directory: Directory to analyze
            package_name: Package name prefix (e.g., "backend")
        """
        self.root_path = Path(directory).resolve()
        
        for py_file in self.root_path.rglob("*.py"):
            if "__pycache__" in str(py_file) or "venv" in str(py_file):
                continue
            
            module_name = self._get_module_name(py_file, package_name)
            self._analyze_file(py_file, module_name)
    
    def _get_module_name(self, file_path: Path, package_name: str) -> str:
        """Convert file path to module name"""
        rel_path = file_path.relative_to(self.root_path)
        parts = list(rel_path.parts[:-1]) + [rel_path.stem]
        
        # Remove __init__
        if parts[-1] == "__init__":
            parts = parts[:-1]
        
        module = ".".join(parts)
        if package_name:
            module = f"{package_name}.{module}" if module else package_name
        
        return module
    
    def _analyze_file(self, file_path: Path, module_name: str):
        """Analyze a single Python file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            node = DependencyNode(
                name=module_name,
                file_path=str(file_path)
            )
            
            for item in ast.walk(tree):
                if isinstance(item, ast.Import):
                    for alias in item.names:
                        self._add_import(node, alias.name)
                
                elif isinstance(item, ast.ImportFrom):
                    if item.module:
                        self._add_import(node, item.module)
            
            self.nodes[module_name] = node
        
        except Exception:
            # Skip files that can't be parsed
            pass
    
    def _add_import(self, node: DependencyNode, import_name: str):
        """Add an import to a node"""
        # Check if it's an internal import
        if self.root_path:
            # Internal imports start with package name
            is_internal = any(
                import_name.startswith(n.split('.')[0])
                for n in self.nodes.keys()
            )
            
            if is_internal:
                node.imports.add(import_name)
            else:
                node.external_imports.add(import_name.split('.')[0])
        else:
            node.imports.add(import_name)
    
    def build_dependency_graph(self):
        """Build reverse dependencies (imported_by)"""
        for node in self.nodes.values():
            for imported in node.imports:
                # Find matching modules (handle partial imports)
                for module_name, module_node in self.nodes.items():
                    if imported.startswith(module_name):
                        module_node.imported_by.add(node.name)
    
    def find_circular_dependencies(self) -> List[List[str]]:
        """
        Find all circular dependencies using DFS
        
        Returns:
            List of circular dependency chains
        """
        self.build_dependency_graph()
        
        circles = []
        visited = set()
        rec_stack = set()
        path = []
        
        def dfs(node_name: str) -> bool:
            """DFS to detect cycles"""
            visited.add(node_name)
            rec_stack.add(node_name)
            path.append(node_name)
            
            if node_name in self.nodes:
                for neighbor in self.nodes[node_name].imports:
                    # Find matching node
                    neighbor_node = None
                    for n in self.nodes.keys():
                        if neighbor.startswith(n):
                            neighbor_node = n
                            break
                    
                    if neighbor_node is None:
                        continue
                    
                    if neighbor_node not in visited:
                        if dfs(neighbor_node):
                            return True
                    elif neighbor_node in rec_stack:
                        # Found cycle
                        cycle_start = path.index(neighbor_node)
                        cycle = path[cycle_start:] + [neighbor_node]
                        if cycle not in circles and list(reversed(cycle)) not in circles:
                            circles.append(cycle)
            
            path.pop()
            rec_stack.remove(node_name)
            return False
        
        for node_name in self.nodes:
            if node_name not in visited:
                dfs(node_name)
        
        return circles
    
    def calculate_coupling(self) -> float:
        """
        Calculate average coupling across all modules
        
        Returns:
            Average coupling value (0-1, lower is better)
        """
        if not self.nodes:
            return 0.0
        
        total_coupling = sum(node.get_total_coupling() for node in self.nodes.values())
        max_possible = len(self.nodes) * (len(self.nodes) - 1)
        
        if max_possible == 0:
            return 0.0
        
        return total_coupling / max_possible
    
    def get_most_coupled_modules(self, top_n: int = 10) -> List[Tuple[str, int]]:
        """
        Get most coupled modules
        
        Args:
            top_n: Number of modules to return
        
        Returns:
            List of (module_name, coupling) tuples
        """
        modules = [
            (node.name, node.get_total_coupling())
            for node in self.nodes.values()
        ]
        return sorted(modules, key=lambda x: x[1], reverse=True)[:top_n]
    
    def generate_mermaid_diagram(self, max_nodes: int = 20) -> str:
        """
        Generate Mermaid diagram
        
        Args:
            max_nodes: Maximum nodes to include (to avoid huge diagrams)
        
        Returns:
            Mermaid diagram string
        """
        self.build_dependency_graph()
        
        # Get most connected nodes
        top_nodes = [name for name, _ in self.get_most_coupled_modules(max_nodes)]
        
        lines = ["graph TD"]
        
        # Add nodes
        node_ids = {}
        for i, node_name in enumerate(top_nodes):
            node_id = f"N{i}"
            node_ids[node_name] = node_id
            # Shorten name for display
            display_name = node_name.split('.')[-1]
            lines.append(f"    {node_id}[{display_name}]")
        
        # Add edges
        for node_name in top_nodes:
            if node_name not in self.nodes:
                continue
            
            node = self.nodes[node_name]
            for imported in node.imports:
                # Find matching node in top_nodes
                for target in top_nodes:
                    if imported.startswith(target) and target in node_ids:
                        lines.append(f"    {node_ids[node_name]} --> {node_ids[target]}")
        
        return "\n".join(lines)
    
    def generate_dot_diagram(self, max_nodes: int = 20) -> str:
        """
        Generate Graphviz DOT diagram
        
        Args:
            max_nodes: Maximum nodes to include
        
        Returns:
            DOT diagram string
        """
        self.build_dependency_graph()
        
        top_nodes = [name for name, _ in self.get_most_coupled_modules(max_nodes)]
        
        lines = ["digraph dependencies {"]
        lines.append("    rankdir=LR;")
        lines.append("    node [shape=box];")
        lines.append("")
        
        # Add nodes
        for node_name in top_nodes:
            display_name = node_name.split('.')[-1]
            lines.append(f'    "{node_name}" [label="{display_name}"];')
        
        lines.append("")
        
        # Add edges
        for node_name in top_nodes:
            if node_name not in self.nodes:
                continue
            
            node = self.nodes[node_name]
            for imported in node.imports:
                for target in top_nodes:
                    if imported.startswith(target):
                        lines.append(f'    "{node_name}" -> "{target}";')
        
        lines.append("}")
        return "\n".join(lines)
    
    def generate_report(self) -> str:
        """
        Generate dependency analysis report
        
        Returns:
            Formatted text report
        """
        self.build_dependency_graph()
        circles = self.find_circular_dependencies()
        coupling = self.calculate_coupling()
        top_coupled = self.get_most_coupled_modules(10)
        
        lines = []
        lines.append("=" * 80)
        lines.append("DEPENDENCY ANALYSIS REPORT")
        lines.append("=" * 80)
        lines.append("")
        
        # Summary
        lines.append("SUMMARY:")
        lines.append("-" * 80)
        lines.append(f"Total Modules: {len(self.nodes)}")
        lines.append(f"Circular Dependencies: {len(circles)}")
        lines.append(f"Average Coupling: {coupling:.3f}")
        lines.append("")
        
        # Circular dependencies
        if circles:
            lines.append("CIRCULAR DEPENDENCIES:")
            lines.append("-" * 80)
            for i, circle in enumerate(circles, 1):
                lines.append(f"{i}. {' -> '.join(circle)}")
            lines.append("")
        
        # Most coupled modules
        lines.append("MOST COUPLED MODULES:")
        lines.append("-" * 80)
        for name, coupling_value in top_coupled:
            node = self.nodes[name]
            lines.append(f"{name}")
            lines.append(f"  Imports: {node.get_coupling_out()}")
            lines.append(f"  Imported by: {node.get_coupling_in()}")
            lines.append(f"  Total coupling: {coupling_value}")
            lines.append("")
        
        # External dependencies
        external_deps = set()
        for node in self.nodes.values():
            external_deps.update(node.external_imports)
        
        if external_deps:
            lines.append("EXTERNAL DEPENDENCIES:")
            lines.append("-" * 80)
            for dep in sorted(external_deps):
                count = sum(1 for n in self.nodes.values() if dep in n.external_imports)
                lines.append(f"{dep} (used by {count} modules)")
            lines.append("")
        
        lines.append("=" * 80)
        return "\n".join(lines)


def visualize_dependencies(directory: str, package_name: str = "") -> DependencyVisualizer:
    """
    Analyze dependencies in a directory
    
    Args:
        directory: Directory to analyze
        package_name: Package name prefix
    
    Returns:
        DependencyVisualizer instance
    """
    visualizer = DependencyVisualizer()
    visualizer.analyze_directory(directory, package_name)
    return visualizer


def generate_dependency_report(directory: str, package_name: str = "") -> str:
    """
    Generate dependency report for a directory
    
    Args:
        directory: Directory to analyze
        package_name: Package name prefix
    
    Returns:
        Formatted report string
    """
    visualizer = visualize_dependencies(directory, package_name)
    return visualizer.generate_report()


def check_circular_dependencies(directory: str, package_name: str = "") -> List[List[str]]:
    """
    Check for circular dependencies
    
    Args:
        directory: Directory to analyze
        package_name: Package name prefix
    
    Returns:
        List of circular dependency chains
    """
    visualizer = visualize_dependencies(directory, package_name)
    return visualizer.find_circular_dependencies()
