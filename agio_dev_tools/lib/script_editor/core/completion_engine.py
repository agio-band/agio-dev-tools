"""Jedi-based completion engine.

Runs in the CompletionWorker thread only. Optimized for the interactive
editor: no docstrings (they are the slowest part of jedi completions),
signatures for callables only, results capped.
"""

import logging

from dataclasses import dataclass

import jedi

logger = logging.getLogger(__name__)

MAX_COMPLETIONS = 100
# completion types for which we fetch a signature for the tooltip
SIGNATURE_TYPES = {'function', 'method', 'class'}


@dataclass
class CompletionItem:
    name: str
    complete: str
    type: str = ""  # 'function', 'class', 'module', 'keyword', etc.
    signature: str = ""
    docstring: str = ""


class CompletionEngine:
    def get_completions(self, text: str, line: int, column: int) -> list:
        """
        Get completions for the given source text at the given position.

        Args:
            text: The full source text
            line: Line number (1-based)
            column: Column number (0-based, position after the typed prefix)

        Returns:
            List of CompletionItem objects (empty list on any failure —
            completion is a nice-to-have, errors must not surface in the UI)
        """
        try:
            script = jedi.Script(code=text)
            completions = script.complete(line, column)

            result = []
            for comp in completions[:MAX_COMPLETIONS]:
                item = CompletionItem(
                    name=comp.name,
                    complete=comp.complete,
                    type=comp.type or "",
                )
                if comp.type in SIGNATURE_TYPES:
                    try:
                        sigs = comp.get_signatures()
                        if sigs:
                            item.signature = sigs[0].to_string()
                    except Exception:
                        pass
                result.append(item)
            return result
        except Exception as e:
            # jedi can raise on odd input (e.g. during incremental typing);
            # log quietly and return nothing instead of spamming the console
            logger.debug("jedi completion failed at line=%s column=%s: %s", line, column, e)
            return []
