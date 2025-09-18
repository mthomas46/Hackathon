"""Terminal Progress Visualizer - Rich Terminal UI for Simulation Execution.

This module provides a comprehensive terminal user interface for simulation execution
with progress bars, real-time status updates, interactive elements, and rich
visualization of simulation progress, document generation, and workflow execution.
"""

import sys
import os
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import threading
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Import from shared infrastructure
sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent / "services" / "shared"))

from simulation.infrastructure.logging import get_simulation_logger


class ProgressBarStyle(str, Enum):
    """Progress bar visual styles."""
    BLOCKS = "blocks"
    DOTS = "dots"
    LINES = "lines"
    ARROWS = "arrows"
    FILLED = "filled"


class StatusIndicator(str, Enum):
    """Status indicator types."""
    SPINNER = "spinner"
    PULSING = "pulsing"
    PROGRESS = "progress"
    CHECKMARK = "checkmark"
    CROSS = "cross"
    WARNING = "warning"


class ColorScheme(str, Enum):
    """Terminal color schemes."""
    DEFAULT = "default"
    DARK = "dark"
    LIGHT = "light"
    HIGH_CONTRAST = "high_contrast"
    MONOCHROME = "monochrome"


@dataclass
class ProgressItem:
    """Represents a single progress item."""
    id: str
    name: str
    status: str = "pending"
    progress: float = 0.0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    message: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    sub_items: List['ProgressItem'] = field(default_factory=list)


@dataclass
class TerminalUIState:
    """Current state of the terminal UI."""
    simulation_id: str
    overall_progress: float = 0.0
    current_phase: str = ""
    active_tasks: List[str] = field(default_factory=list)
    completed_tasks: List[str] = field(default_factory=list)
    failed_tasks: List[str] = field(default_factory=list)
    documents_generated: int = 0
    workflows_executed: int = 0
    start_time: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    last_update: Optional[datetime] = None
    progress_items: Dict[str, ProgressItem] = field(default_factory=dict)


class TerminalProgressVisualizer:
    """Rich terminal UI for simulation execution with progress bars and real-time updates."""

    def __init__(self,
                 simulation_id: str,
                 style: ProgressBarStyle = ProgressBarStyle.BLOCKS,
                 color_scheme: ColorScheme = ColorScheme.DEFAULT,
                 width: int = 80,
                 show_details: bool = True,
                 interactive: bool = True):
        """Initialize the terminal progress visualizer."""
        self.simulation_id = simulation_id
        self.style = style
        self.color_scheme = color_scheme
        self.width = width
        self.show_details = show_details
        self.interactive = interactive

        self.logger = get_simulation_logger()
        self.state = TerminalUIState(simulation_id=simulation_id)

        # UI control
        self._running = False
        self._last_display_time = 0
        self._display_interval = 0.5  # Update every 500ms
        self._spinner_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        self._spinner_index = 0

        # Threading for async updates
        self._update_thread: Optional[threading.Thread] = None
        self._update_queue: List[Dict[str, Any]] = []
        self._queue_lock = threading.Lock()

        # Color codes
        self._colors = self._get_color_codes()

    def start_simulation(self, estimated_duration_minutes: int = 60) -> None:
        """Start the simulation progress visualization."""
        self.state.start_time = datetime.now()
        self.state.estimated_completion = self.state.start_time + timedelta(minutes=estimated_duration_minutes)
        self._running = True

        self.logger.info(f"Starting terminal progress visualization for simulation {self.simulation_id}")

        # Initialize display
        self._clear_screen()
        self._display_header()
        self._display_initial_status()

        # Start update thread if interactive
        if self.interactive:
            self._update_thread = threading.Thread(target=self._update_loop, daemon=True)
            self._update_thread.start()

    def stop_simulation(self, success: bool = True) -> None:
        """Stop the simulation progress visualization."""
        self._running = False

        if self._update_thread and self._update_thread.is_alive():
            self._update_thread.join(timeout=1.0)

        # Final display
        self._clear_screen()
        self._display_final_summary(success)

        self.logger.info(f"Stopped terminal progress visualization for simulation {self.simulation_id}")

    def update_progress(self, progress_data: Dict[str, Any]) -> None:
        """Update the progress visualization with new data."""
        with self._queue_lock:
            self._update_queue.append(progress_data)

        # Immediate update if not interactive or if important event
        if not self.interactive or progress_data.get("immediate", False):
            self._process_updates()

    def _update_loop(self) -> None:
        """Background thread for updating the display."""
        while self._running:
            current_time = time.time()
            if current_time - self._last_display_time >= self._display_interval:
                self._process_updates()
                self._last_display_time = current_time
            time.sleep(0.1)

    def _process_updates(self) -> None:
        """Process queued updates and refresh display."""
        updates = []
        with self._queue_lock:
            updates = self._update_queue.copy()
            self._update_queue.clear()

        # Apply updates to state
        for update in updates:
            self._apply_update(update)

        # Refresh display
        if updates or time.time() - self._last_display_time >= self._display_interval:
            self._refresh_display()

    def _apply_update(self, update: Dict[str, Any]) -> None:
        """Apply a single update to the UI state."""
        update_type = update.get("type", "progress")

        if update_type == "simulation_started":
            self.state.current_phase = update.get("phase", "Planning")
            self._add_progress_item("simulation", "Simulation Execution", "running")

        elif update_type == "phase_completed":
            phase_name = update.get("phase_name", "Unknown")
            self._complete_progress_item(f"phase_{phase_name}")

        elif update_type == "document_generated":
            self.state.documents_generated += 1
            doc_title = update.get("document_title", "Document")
            doc_type = update.get("document_type", "Unknown")
            self._add_progress_item(f"doc_{self.state.documents_generated}",
                                  f"Generate {doc_title}", "completed")

        elif update_type == "workflow_executed":
            self.state.workflows_executed += 1
            workflow_name = update.get("workflow_name", "Workflow")
            success = update.get("success", True)
            status = "completed" if success else "failed"
            self._add_progress_item(f"workflow_{self.state.workflows_executed}",
                                  f"Execute {workflow_name}", status)

        elif update_type == "simulation_completed":
            self.state.overall_progress = 100.0
            self._complete_progress_item("simulation")

        elif update_type == "progress":
            self.state.overall_progress = update.get("progress_percentage", 0.0)
            self.state.current_phase = update.get("current_phase", self.state.current_phase)

        self.state.last_update = datetime.now()

    def _add_progress_item(self, item_id: str, name: str, status: str = "running") -> None:
        """Add a new progress item."""
        item = ProgressItem(
            id=item_id,
            name=name,
            status=status,
            start_time=datetime.now()
        )
        self.state.progress_items[item_id] = item

        if status == "running":
            self.state.active_tasks.append(item_id)
        elif status == "completed":
            self.state.completed_tasks.append(item_id)
        elif status == "failed":
            self.state.failed_tasks.append(item_id)

    def _complete_progress_item(self, item_id: str) -> None:
        """Mark a progress item as completed."""
        if item_id in self.state.progress_items:
            item = self.state.progress_items[item_id]
            item.status = "completed"
            item.end_time = datetime.now()
            item.progress = 100.0

            if item_id in self.state.active_tasks:
                self.state.active_tasks.remove(item_id)
            self.state.completed_tasks.append(item_id)

    def _refresh_display(self) -> None:
        """Refresh the entire terminal display."""
        if not self._running:
            return

        # Move cursor to top
        print("\033[H", end="")

        # Display components
        self._display_header()
        self._display_overall_progress()
        self._display_current_phase()
        self._display_active_tasks()
        self._display_recent_events()
        self._display_statistics()
        self._display_footer()

    def _display_header(self) -> None:
        """Display the header section."""
        title = f"🚀 Project Simulation Service - {self.simulation_id[:8]}"
        print(f"{self._color('cyan', 'bold')}{title.center(self.width)}{self._reset()}")
        print(f"{'─' * self.width}")

    def _display_overall_progress(self) -> None:
        """Display overall simulation progress."""
        progress = self.state.overall_progress
        bar = self._create_progress_bar(progress, 50)
        percent = f"{progress:5.1f}%"

        print(f"📊 Overall Progress: {bar} {percent}")

        if self.state.start_time:
            elapsed = datetime.now() - self.state.start_time
            elapsed_str = f"{elapsed.seconds // 60:02d}:{elapsed.seconds % 60:02d}"

            if self.state.estimated_completion:
                remaining = self.state.estimated_completion - datetime.now()
                if remaining.total_seconds() > 0:
                    remaining_str = f"{remaining.seconds // 60:02d}:{remaining.seconds % 60:02d}"
                    eta_str = f" (ETA: {remaining_str})"
                else:
                    eta_str = " (Overdue)"
            else:
                eta_str = ""

            print(f"⏱️  Elapsed: {elapsed_str}{eta_str}")

        print()

    def _display_current_phase(self) -> None:
        """Display current phase information."""
        if self.state.current_phase:
            spinner = self._get_spinner()
            phase = self.state.current_phase
            print(f"{spinner} Current Phase: {self._color('yellow', 'bold')}{phase}{self._reset()}")
        print()

    def _display_active_tasks(self) -> None:
        """Display currently active tasks."""
        if not self.state.active_tasks:
            return

        print(f"{self._color('blue', 'bold')}🔄 Active Tasks:{self._reset()}")
        for task_id in self.state.active_tasks[:5]:  # Show top 5
            if task_id in self.state.progress_items:
                item = self.state.progress_items[task_id]
                spinner = self._get_spinner()
                print(f"  {spinner} {item.name}")

        if len(self.state.active_tasks) > 5:
            print(f"  ... and {len(self.state.active_tasks) - 5} more")
        print()

    def _display_recent_events(self) -> None:
        """Display recent events."""
        recent_items = sorted(
            [item for item in self.state.progress_items.values() if item.end_time],
            key=lambda x: x.end_time or datetime.min,
            reverse=True
        )[:3]  # Last 3 completed items

        if recent_items:
            print(f"{self._color('green', 'bold')}✅ Recent Events:{self._reset()}")
            for item in recent_items:
                status_icon = "✅" if item.status == "completed" else "❌"
                print(f"  {status_icon} {item.name}")
            print()

    def _display_statistics(self) -> None:
        """Display simulation statistics."""
        if not self.show_details:
            return

        docs = self.state.documents_generated
        workflows = self.state.workflows_executed
        completed = len(self.state.completed_tasks)
        active = len(self.state.active_tasks)
        failed = len(self.state.failed_tasks)

        print(f"{self._color('magenta', 'bold')}📈 Statistics:{self._reset()}")
        print(f"  📄 Documents: {docs}")
        print(f"  ⚙️  Workflows: {workflows}")
        print(f"  ✅ Completed: {completed}")
        print(f"  🔄 Active: {active}")
        print(f"  ❌ Failed: {failed}")
        print()

    def _display_footer(self) -> None:
        """Display footer with controls."""
        if self.interactive:
            print(f"{'─' * self.width}")
            print("Press Ctrl+C to stop monitoring | Use WebSocket for detailed updates")
            print(f"Last update: {datetime.now().strftime('%H:%M:%S')}")

    def _display_initial_status(self) -> None:
        """Display initial status before starting."""
        print("🎯 Initializing simulation execution...")
        print("🔧 Setting up document generation pipeline...")
        print("📡 Establishing WebSocket connections...")
        print("📊 Preparing progress monitoring...")
        print()
        print("🚀 Starting simulation execution...")
        print()

    def _display_final_summary(self, success: bool) -> None:
        """Display final summary when simulation completes."""
        status_icon = "🎉" if success else "⚠️"
        status_text = "SUCCESS" if success else "COMPLETED WITH ISSUES"
        status_color = "green" if success else "yellow"

        print(f"\n{status_icon} Simulation {self._color(status_color, 'bold')}{status_text}{self._reset()}\n")

        if self.state.start_time:
            duration = datetime.now() - self.state.start_time
            duration_str = f"{duration.seconds // 60:02d}:{duration.seconds % 60:02d}"
            print(f"⏱️  Total Duration: {duration_str}")

        print(f"📄 Documents Generated: {self.state.documents_generated}")
        print(f"⚙️  Workflows Executed: {self.state.workflows_executed}")
        print(f"✅ Tasks Completed: {len(self.state.completed_tasks)}")

        if self.state.failed_tasks:
            print(f"❌ Tasks Failed: {len(self.state.failed_tasks)}")

        print(f"\n📊 Final Progress: {self.state.overall_progress:.1f}%")

        if success:
            print("\n🎯 Simulation completed successfully! Check the reports for detailed analysis.")
        else:
            print("\n⚠️  Simulation completed with some issues. Review the logs for details.")

    def _create_progress_bar(self, progress: float, width: int) -> str:
        """Create a visual progress bar."""
        filled = int(width * progress / 100)
        empty = width - filled

        if self.style == ProgressBarStyle.BLOCKS:
            bar_chars = "█" * filled + "░" * empty
        elif self.style == ProgressBarStyle.DOTS:
            bar_chars = "●" * filled + "○" * empty
        elif self.style == ProgressBarStyle.LINES:
            bar_chars = "━" * filled + "─" * empty
        elif self.style == ProgressBarStyle.ARROWS:
            bar_chars = "▶" * filled + "▷" * empty
        elif self.style == ProgressBarStyle.FILLED:
            bar_chars = "█" * filled + " " * empty
        else:
            bar_chars = "█" * filled + "░" * empty

        return f"[{bar_chars}]"

    def _get_spinner(self) -> str:
        """Get the current spinner character."""
        char = self._spinner_chars[self._spinner_index]
        self._spinner_index = (self._spinner_index + 1) % len(self._spinner_chars)
        return char

    def _clear_screen(self) -> None:
        """Clear the terminal screen."""
        if os.name == 'nt':  # Windows
            os.system('cls')
        else:  # Unix/Linux/Mac
            print("\033[2J\033[H", end="")

    def _color(self, color: str, style: str = "normal") -> str:
        """Get ANSI color code."""
        if self.color_scheme == ColorScheme.MONOCHROME:
            return ""

        color_code = self._colors.get(color, "")
        style_code = ""

        if style == "bold":
            style_code = "\033[1m"
        elif style == "dim":
            style_code = "\033[2m"
        elif style == "underline":
            style_code = "\033[4m"

        return f"{style_code}{color_code}"

    def _reset(self) -> str:
        """Reset ANSI colors."""
        if self.color_scheme == ColorScheme.MONOCHROME:
            return ""
        return "\033[0m"

    def _get_color_codes(self) -> Dict[str, str]:
        """Get ANSI color codes based on color scheme."""
        if self.color_scheme == ColorScheme.DARK:
            return {
                "black": "\033[30m",
                "red": "\033[31m",
                "green": "\033[32m",
                "yellow": "\033[33m",
                "blue": "\033[34m",
                "magenta": "\033[35m",
                "cyan": "\033[36m",
                "white": "\033[37m"
            }
        elif self.color_scheme == ColorScheme.LIGHT:
            return {
                "black": "\033[90m",
                "red": "\033[91m",
                "green": "\033[92m",
                "yellow": "\033[93m",
                "blue": "\033[94m",
                "magenta": "\033[95m",
                "cyan": "\033[96m",
                "white": "\033[97m"
            }
        elif self.color_scheme == ColorScheme.HIGH_CONTRAST:
            return {
                "black": "\033[40m\033[37m",
                "red": "\033[41m\033[37m",
                "green": "\033[42m\033[37m",
                "yellow": "\033[43m\033[30m",
                "blue": "\033[44m\033[37m",
                "magenta": "\033[45m\033[37m",
                "cyan": "\033[46m\033[30m",
                "white": "\033[47m\033[30m"
            }
        else:  # Default
            return {
                "black": "\033[30m",
                "red": "\033[31m",
                "green": "\033[32m",
                "yellow": "\033[33m",
                "blue": "\033[34m",
                "magenta": "\033[35m",
                "cyan": "\033[36m",
                "white": "\033[37m"
            }


class SimulationTerminalUI:
    """High-level interface for terminal UI during simulation execution."""

    def __init__(self, simulation_id: str):
        """Initialize the simulation terminal UI."""
        self.simulation_id = simulation_id
        self.visualizer = TerminalProgressVisualizer(
            simulation_id=simulation_id,
            style=ProgressBarStyle.BLOCKS,
            color_scheme=ColorScheme.DEFAULT,
            width=100,
            show_details=True,
            interactive=True
        )
        self.logger = get_simulation_logger()

    def start_monitoring(self, estimated_duration_minutes: int = 60) -> None:
        """Start monitoring the simulation execution."""
        try:
            self.visualizer.start_simulation(estimated_duration_minutes)
            self.logger.info(f"Started terminal monitoring for simulation {self.simulation_id}")
        except Exception as e:
            self.logger.error(f"Failed to start terminal monitoring: {e}")

    def stop_monitoring(self, success: bool = True) -> None:
        """Stop monitoring the simulation execution."""
        try:
            self.visualizer.stop_simulation(success)
            self.logger.info(f"Stopped terminal monitoring for simulation {self.simulation_id}")
        except Exception as e:
            self.logger.error(f"Failed to stop terminal monitoring: {e}")

    def update_from_event(self, event_data: Dict[str, Any]) -> None:
        """Update the UI based on simulation event data."""
        try:
            # Convert event data to UI update format
            update_data = {
                "type": event_data.get("event_type", "progress"),
                "immediate": event_data.get("event_type") in ["simulation_completed", "simulation_failed"],
                **event_data
            }

            self.visualizer.update_progress(update_data)
        except Exception as e:
            self.logger.error(f"Failed to update UI from event: {e}")

    def update_progress(self, progress_data: Dict[str, Any]) -> None:
        """Update the UI with progress information."""
        try:
            self.visualizer.update_progress(progress_data)
        except Exception as e:
            self.logger.error(f"Failed to update progress: {e}")


# Global terminal UI manager
_terminal_ui_manager: Dict[str, SimulationTerminalUI] = {}


def get_simulation_terminal_ui(simulation_id: str) -> SimulationTerminalUI:
    """Get or create a terminal UI instance for a simulation."""
    if simulation_id not in _terminal_ui_manager:
        _terminal_ui_manager[simulation_id] = SimulationTerminalUI(simulation_id)
    return _terminal_ui_manager[simulation_id]


def start_simulation_monitoring(simulation_id: str, estimated_duration_minutes: int = 60) -> None:
    """Start terminal monitoring for a simulation."""
    ui = get_simulation_terminal_ui(simulation_id)
    ui.start_monitoring(estimated_duration_minutes)


def stop_simulation_monitoring(simulation_id: str, success: bool = True) -> None:
    """Stop terminal monitoring for a simulation."""
    if simulation_id in _terminal_ui_manager:
        ui = _terminal_ui_manager[simulation_id]
        ui.stop_monitoring(success)
        del _terminal_ui_manager[simulation_id]


def update_simulation_ui(simulation_id: str, update_data: Dict[str, Any]) -> None:
    """Update the UI for a simulation."""
    if simulation_id in _terminal_ui_manager:
        ui = _terminal_ui_manager[simulation_id]
        ui.update_progress(update_data)


__all__ = [
    'TerminalProgressVisualizer',
    'SimulationTerminalUI',
    'ProgressBarStyle',
    'StatusIndicator',
    'ColorScheme',
    'get_simulation_terminal_ui',
    'start_simulation_monitoring',
    'stop_simulation_monitoring',
    'update_simulation_ui'
]
