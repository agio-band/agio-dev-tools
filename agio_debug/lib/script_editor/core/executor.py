"""Code execution engine with stdout/stderr capture."""

import sys
import io
import traceback
from contextlib import redirect_stdout
from typing import Any, Dict, Optional
from PySide6.QtCore import QObject, Signal


class ExecutionResult:
    """Holds the result of a code execution."""
    def __init__(self):
        self.stdout = ""
        self.stderr = ""
        self.exception = None
        self.has_result = False
        self.result = None


class CodeExecutor(QObject):
    """Executes Python code with captured output and namespace management."""

    stdout_signal = Signal(str)
    stderr_signal = Signal(str)
    execution_finished_signal = Signal()

    def __init__(self):
        super().__init__()
        self._namespace: Dict[str, Any] = {"__name__": "__main__"}

    def get_namespace(self) -> Dict[str, Any]:
        """Get the execution namespace."""
        return self._namespace

    def update_namespace(self, updates: Dict[str, Any]) -> None:
        """Update the execution namespace with new variables."""
        self._namespace.update(updates)

    def clear_namespace(self) -> None:
        """Clear the execution namespace (except __name__)."""
        self._namespace = {"__name__": "__main__"}

    def execute(self, code: str) -> ExecutionResult:
        """Execute code string and return ExecutionResult."""
        # Replace Qt paragraph separators with newlines
        code = code.replace('\u2029', '\n')
        
        result = ExecutionResult()
        stdout_buffer = io.StringIO()
        stderr_buffer = io.StringIO()

        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = stdout_buffer
        sys.stderr = stderr_buffer

        try:
            code_stripped = code.strip()
            
            # Try eval first for single expressions
            try:
                result_value = eval(code_stripped, self._namespace, self._namespace)
                if result_value is not None:
                    stdout_buffer.write(repr(result_value) + '\n')
                    result.has_result = True
                    result.result = result_value
            except SyntaxError:
                # Fall back to exec for statements
                exec(code, self._namespace, self._namespace)
        except Exception as e:
            result.exception = e
            tb_lines = traceback.format_exc().split('\n')
            # Remove internal frames
            filtered = [line for line in tb_lines 
                       if not ('script_editor' in line and '<string>' in line)]
            stderr_buffer.write('\n'.join(filtered))
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

        result.stdout = stdout_buffer.getvalue()
        result.stderr = stderr_buffer.getvalue()
        
        # Emit collected output
        if result.stdout.strip():
            self.stdout_signal.emit(result.stdout.rstrip('\n'))
        if result.stderr.strip():
            self.stderr_signal.emit(result.stderr.rstrip('\n'))

        self.execution_finished_signal.emit()
        return result

    def execute_selected(self, code: str) -> ExecutionResult:
        """Execute selected code (alias for execute)."""
        return self.execute(code)
