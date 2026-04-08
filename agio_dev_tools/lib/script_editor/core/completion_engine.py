import traceback
from dataclasses import dataclass
from pathlib import Path
import jedi
import _pickle


@dataclass
class CompletionItem:
    name: str
    complete: str
    type: str = ""  # 'function', 'class', 'module', 'keyword', etc.
    signature: str = ""
    docstring: str = ""


class CompletionEngine:
    def __init__(self):
        self._script = None
        self._completions = []

    def get_completions(self, text: str, line: int, column: int) -> list[CompletionItem]:
        """
        Get completions for the given text at the specified position.

        Args:
            text: The full source text
            line: Line number (1-based from InputWidget)
            column: Column number (0-based)

        Returns:
            List of CompletionItem objects
        """
        try:
            # Use a temporary path to help Jedi resolve imports properly
            temp_path = Path("<input>")
            script = jedi.Script(text, path=temp_path)
            completions = script.complete(line, column)

            result = []
            for comp in completions:
                item = CompletionItem(
                    name=comp.name,
                    complete=comp.complete,
                    type=comp.type,
                )

                if comp.type == 'function':
                    try:
                        sigs = comp.get_signatures()
                        if sigs:
                            item.signature = sigs[0].to_string()
                    except Exception:
                        pass

                try:
                    doc = comp.docstring()
                    if doc:
                        item.docstring = doc
                except Exception:
                    pass

                result.append(item)

            return result
        except TypeError as e:
            # Jedi may raise TypeError when it encounters None values internally
            # (e.g., "TypeError: expected str, bytes or os.PathLike object, not NoneType")
            # This is a known Jedi issue, safely ignore it
            return []
        except _pickle.UnpicklingError:
            # Jedi subprocess pickle corruption can happen occasionally.
            # This is a known Jedi issue — silently recover with empty results.
            return []
        except Exception as e:
            # For other errors, log and return empty list
            traceback.print_exc()
            return []

    def should_trigger_completion(self, text: str, cursor_pos: int) -> bool:
        """
        Check if we should trigger autocompletion at this position.
        Triggers on alphanumeric characters and dots.
        """
        if cursor_pos <= 0 or cursor_pos > len(text):
            return False
        char_before = text[cursor_pos - 1]
        return char_before.isalnum() or char_before == '_'

    def get_context_completions(self, line_text: str, namespace: dict = None) -> tuple:
        """
        Get context-aware completions (e.g., for special environments).
        
        Returns:
            Tuple of (completions_list, extra_items_list)
        """
        # This can be extended for environment-specific completions
        return ([], [])
