"""
Memory Monitor - Tracks memory usage and helps detect memory leaks.

This module provides utilities for monitoring application memory usage,
tracking object counts, and detecting potential memory leaks.
"""
import gc
import logging
try:
    import psutil  # type: ignore
    _HAS_PSUTIL = True
except Exception:  # pragma: no cover - optional dependency
    psutil = None  # type: ignore
    _HAS_PSUTIL = False
import os
import sys
import tracemalloc
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, field

logger = logging.getLogger('Core.MemoryMonitor')


@dataclass
class MemorySnapshot:
    """Represents a memory usage snapshot."""
    timestamp: datetime
    process_memory_mb: float
    python_objects: int
    qt_widgets: int
    loaded_modules: int
    script_modules: int
    menu_actions: int
    menu_items: int
    garbage_collector_stats: Dict[str, int] = field(default_factory=dict)


class MemoryMonitor:
    """Monitor application memory usage and detect potential leaks."""
    
    def __init__(self, enable_tracemalloc: bool = False):
        """
        Initialize the memory monitor.
        
        Args:
            enable_tracemalloc: Enable Python's tracemalloc for detailed tracking
        """
        # psutil is optional; degrade gracefully if unavailable
        self.process = psutil.Process(os.getpid()) if _HAS_PSUTIL else None
        self.snapshots: List[MemorySnapshot] = []
        self.baseline_snapshot: Optional[MemorySnapshot] = None
        self.tracemalloc_enabled = enable_tracemalloc
        
        if enable_tracemalloc:
            tracemalloc.start()
            logger.info("Memory tracing enabled with tracemalloc")
        
        logger.info("MemoryMonitor initialized")
    
    def take_snapshot(self, label: str = "") -> MemorySnapshot:
        """
        Take a memory usage snapshot.
        
        Args:
            label: Optional label for the snapshot
            
        Returns:
            MemorySnapshot object with current memory stats
        """
        # Get process memory
        if self.process is not None:
            try:
                memory_info = self.process.memory_info()
                process_memory_mb = memory_info.rss / 1024 / 1024
            except Exception:
                process_memory_mb = 0.0
        else:
            # Fallback when psutil is not installed
            process_memory_mb = 0.0
        
        # Count Python objects
        gc.collect()  # Force collection before counting
        python_objects = len(gc.get_objects())
        
        # Count Qt widgets (if PyQt6 is available)
        qt_widgets = self._count_qt_widgets()
        
        # Count loaded modules
        loaded_modules = len(sys.modules)
        
        # Count script-specific modules
        script_modules = sum(1 for name in sys.modules.keys() 
                            if 'script' in name.lower() or name.startswith('__main__'))
        
        # Count menu items (approximate)
        menu_actions, menu_items = self._count_menu_objects()
        
        # Get garbage collector statistics
        gc_stats = {
            f"generation_{i}": stat['collected'] 
            for i, stat in enumerate(gc.get_stats())
        }
        
        snapshot = MemorySnapshot(
            timestamp=datetime.now(),
            process_memory_mb=process_memory_mb,
            python_objects=python_objects,
            qt_widgets=qt_widgets,
            loaded_modules=loaded_modules,
            script_modules=script_modules,
            menu_actions=menu_actions,
            menu_items=menu_items,
            garbage_collector_stats=gc_stats
        )
        
        self.snapshots.append(snapshot)
        
        if label:
            logger.info(f"Memory snapshot '{label}': {process_memory_mb:.2f} MB, "
                       f"{python_objects} objects, {qt_widgets} widgets")
        
        return snapshot
    
    def set_baseline(self) -> MemorySnapshot:
        """Set the current memory state as baseline for comparisons."""
        self.baseline_snapshot = self.take_snapshot("Baseline")
        logger.info(f"Baseline set: {self.baseline_snapshot.process_memory_mb:.2f} MB")
        return self.baseline_snapshot
    
    def compare_to_baseline(self) -> Dict[str, Any]:
        """
        Compare current memory usage to baseline.
        
        Returns:
            Dictionary with memory differences
        """
        if not self.baseline_snapshot:
            logger.warning("No baseline set, taking baseline now")
            self.set_baseline()
            return {}
        
        current = self.take_snapshot()
        
        comparison = {
            'memory_change_mb': current.process_memory_mb - self.baseline_snapshot.process_memory_mb,
            'objects_change': current.python_objects - self.baseline_snapshot.python_objects,
            'widgets_change': current.qt_widgets - self.baseline_snapshot.qt_widgets,
            'modules_change': current.loaded_modules - self.baseline_snapshot.loaded_modules,
            'script_modules_change': current.script_modules - self.baseline_snapshot.script_modules,
            'menu_actions_change': current.menu_actions - self.baseline_snapshot.menu_actions,
            'current_memory_mb': current.process_memory_mb,
            'baseline_memory_mb': self.baseline_snapshot.process_memory_mb
        }
        
        # Log significant changes
        if abs(comparison['memory_change_mb']) > 10:
            logger.warning(f"Significant memory change: {comparison['memory_change_mb']:.2f} MB")
        
        if comparison['objects_change'] > 10000:
            logger.warning(f"Large object count increase: {comparison['objects_change']}")
        
        return comparison
    
    def get_top_memory_consumers(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get top memory consuming objects (requires tracemalloc).
        
        Args:
            limit: Number of top consumers to return
            
        Returns:
            List of top memory consumers
        """
        if not self.tracemalloc_enabled:
            logger.warning("tracemalloc not enabled, cannot get top consumers")
            return []
        
        snapshot = tracemalloc.take_snapshot()
        top_stats = snapshot.statistics('lineno')[:limit]
        
        consumers = []
        for stat in top_stats:
            consumers.append({
                'file': stat.traceback.format()[0] if stat.traceback else 'Unknown',
                'size_mb': stat.size / 1024 / 1024,
                'count': stat.count
            })
        
        return consumers
    
    def detect_potential_leaks(self, threshold_mb: float = 50) -> Dict[str, Any]:
        """
        Analyze snapshots to detect potential memory leaks.
        
        Args:
            threshold_mb: Memory growth threshold to flag as potential leak
            
        Returns:
            Dictionary with leak detection results
        """
        if len(self.snapshots) < 2:
            return {'detected': False, 'reason': 'Insufficient snapshots'}
        
        # Check memory growth over time
        first_snapshot = self.snapshots[0]
        last_snapshot = self.snapshots[-1]
        
        memory_growth = last_snapshot.process_memory_mb - first_snapshot.process_memory_mb
        object_growth = last_snapshot.python_objects - first_snapshot.python_objects
        module_growth = last_snapshot.script_modules - first_snapshot.script_modules
        
        potential_leak = memory_growth > threshold_mb
        
        result = {
            'detected': potential_leak,
            'memory_growth_mb': memory_growth,
            'object_growth': object_growth,
            'module_growth': module_growth,
            'snapshots_analyzed': len(self.snapshots),
            'time_span_minutes': (last_snapshot.timestamp - first_snapshot.timestamp).total_seconds() / 60
        }
        
        if potential_leak:
            logger.warning(f"Potential memory leak detected: {memory_growth:.2f} MB growth")
            
            # Try to identify the source
            if module_growth > 10:
                result['likely_cause'] = 'Module cache growth'
            elif object_growth > 50000:
                result['likely_cause'] = 'Object accumulation'
            else:
                result['likely_cause'] = 'Unknown'
        
        return result
    
    def force_cleanup(self) -> Dict[str, int]:
        """
        Force aggressive memory cleanup.
        
        Returns:
            Dictionary with cleanup statistics
        """
        logger.info("Forcing aggressive memory cleanup...")
        
        # Clear method caches
        for module in sys.modules.values():
            if hasattr(module, '__dict__'):
                for obj in module.__dict__.values():
                    if hasattr(obj, 'cache_clear'):
                        obj.cache_clear()
        
        # Force garbage collection
        collected = []
        for i in range(3):
            collected.append(gc.collect(i))
        
        stats = {
            'gen0_collected': collected[0] if len(collected) > 0 else 0,
            'gen1_collected': collected[1] if len(collected) > 1 else 0,
            'gen2_collected': collected[2] if len(collected) > 2 else 0,
            'total_collected': sum(collected)
        }
        
        logger.info(f"Cleanup complete: {stats['total_collected']} objects collected")
        
        return stats
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of memory monitoring results.
        
        Returns:
            Dictionary with memory monitoring summary
        """
        if not self.snapshots:
            return {'error': 'No snapshots available'}
        
        current = self.snapshots[-1]
        
        summary = {
            'current_memory_mb': current.process_memory_mb,
            'python_objects': current.python_objects,
            'qt_widgets': current.qt_widgets,
            'loaded_modules': current.loaded_modules,
            'script_modules': current.script_modules,
            'menu_objects': current.menu_actions + current.menu_items,
            'snapshots_taken': len(self.snapshots)
        }
        
        if self.baseline_snapshot:
            summary['baseline_memory_mb'] = self.baseline_snapshot.process_memory_mb
            summary['memory_growth_mb'] = current.process_memory_mb - self.baseline_snapshot.process_memory_mb
        
        # Add leak detection
        leak_info = self.detect_potential_leaks()
        summary['potential_leak'] = leak_info.get('detected', False)
        
        return summary
    
    def _count_qt_widgets(self) -> int:
        """Count PyQt6 widgets in memory."""
        try:
            from PyQt6.QtWidgets import QWidget
            qt_widgets = sum(1 for obj in gc.get_objects() 
                           if isinstance(obj, QWidget))
            return qt_widgets
        except ImportError:
            return 0
    
    def _count_menu_objects(self) -> tuple:
        """Count menu-related objects."""
        try:
            from PyQt6.QtGui import QAction
            from PyQt6.QtWidgets import QMenu
            
            actions = sum(1 for obj in gc.get_objects() 
                         if isinstance(obj, QAction))
            menus = sum(1 for obj in gc.get_objects() 
                       if isinstance(obj, QMenu))
            
            return actions, menus
        except ImportError:
            return 0, 0
    
    def cleanup(self):
        """Clean up the memory monitor."""
        if self.tracemalloc_enabled:
            tracemalloc.stop()
        
        self.snapshots.clear()
        logger.info("MemoryMonitor cleaned up")


# Singleton instance
_monitor_instance: Optional[MemoryMonitor] = None


def get_memory_monitor() -> MemoryMonitor:
    """Get the singleton memory monitor instance."""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = MemoryMonitor()
    return _monitor_instance
