"""Small GUI integration helpers shared by the packaged applications."""

from __future__ import annotations

import sys
import traceback
from typing import Type

from popfe_runtime import RuntimePaths


def write_exception_log(
    runtime: RuntimePaths,
    component: str,
    exception_type: Type[BaseException],
    exception: BaseException,
    traceback_object,
):
    """Persist one GUI callback failure and return its diagnostic log path."""
    log_path = runtime.new_log_path(component)
    with open(log_path, "w", encoding="utf-8") as log:
        log.write(f"POP-FE component: {component}\n")
        log.write(f"Platform: {runtime.platform}\n")
        log.write(f"Executable: {runtime.executable}\n\n")
        traceback.print_exception(
            exception_type,
            exception,
            traceback_object,
            file=log,
        )
    return log_path


def install_tk_error_handler(
    root,
    runtime: RuntimePaths,
    component: str,
    title: str,
) -> None:
    """Show an actionable dialog for exceptions raised by Tk callbacks."""
    def report_callback_exception(exception_type, exception, traceback_object):
        log_path = write_exception_log(
            runtime,
            component,
            exception_type,
            exception,
            traceback_object,
        )
        traceback.print_exception(
            exception_type,
            exception,
            traceback_object,
            file=sys.stderr,
        )
        from tkinter import messagebox

        messagebox.showerror(
            title,
            f"{exception}\n\nDiagnostic log: {log_path}",
            parent=root,
        )

    root.report_callback_exception = report_callback_exception
