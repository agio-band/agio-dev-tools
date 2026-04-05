from dataclasses import dataclass
import jedi


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
            script = jedi.Script(text, path=None)
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
        except Exception as e:
            print(e)
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
