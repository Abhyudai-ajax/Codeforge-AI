"""Input-aware code analysis used when no AI model is configured or reachable.

Everything here is derived from the submitted text itself: syntax errors come from
the real parser/compiler, structure and complexity from the Python AST (or a
lightweight scan for brace languages), and issues from concrete patterns found in
the code. Nothing is canned, so the answer always matches what the user wrote.
"""

from __future__ import annotations

import ast
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

LANGUAGE_LABELS = {
    "python": "Python",
    "javascript": "JavaScript",
    "c": "C",
    "cpp": "C++",
    "java": "Java",
}

_SHADOWED_BUILTINS = {
    "list", "dict", "set", "str", "int", "float", "sum", "max", "min", "len",
    "input", "id", "type", "map", "filter", "range", "sorted", "object", "next", "iter",
}  # fmt: skip

_TAG_HINTS = {
    "arrays": "Walk the array once and keep a running summary (best so far, running sum, "
    "last index seen). Ask what you need to remember about the prefix to answer for "
    "the current element in O(1).",
    "hashing": "Trade memory for time: store what you've already seen in a hash map/set so each "
    "lookup is O(1) instead of re-scanning the input.",
    "two pointers": "Sort (if order doesn't matter) and move two indices toward each other, "
    "deciding which pointer to advance from the comparison at each step.",
    "sliding window": "Grow the window with the right pointer and shrink it from the left only "
    "when it becomes invalid; track window contents in a counter/map.",
    "strings": "Think in terms of character counts or two indices over the string; most string "
    "problems avoid building new strings inside a loop.",
    "stack": "Process elements left to right and keep a stack of 'unresolved' items; each new "
    "element resolves (pops) the ones it answers.",
    "queue": "Model the order of processing explicitly with a FIFO queue; two stacks can "
    "simulate a queue with amortised O(1) operations.",
    "design": "Pick data structures so every operation is O(1): a hash map for lookup plus a "
    "linked list (or ordered dict) for recency/order.",
    "linked list": "Use pointer manipulation with a dummy head, or fast/slow pointers to find "
    "the middle or detect cycles without extra memory.",
    "binary search": "Identify the monotonic property: a condition that is false then true across "
    "the search space, and binary search on where it flips.",
    "heaps": "Keep a heap of size k: push each element and pop when it exceeds k, giving "
    "O(n log k) instead of sorting everything.",
    "prefix sum": "Precompute prefix sums so any subarray sum is prefix[j] - prefix[i]; a hash "
    "map of prefix sums seen so far finds matching subarrays in one pass.",
    "trees": "Write a recursive function that returns what the parent needs from each subtree "
    "(height, found node, best path) and combine children's answers.",
    "graphs": "Build an adjacency list first, then use BFS/DFS with a visited set; for shortest "
    "weighted paths use Dijkstra with a min-heap.",
    "greedy": "Find the locally optimal choice that never needs undoing (often after sorting) "
    "and argue why taking it is always safe.",
    "sorting": "Sort first; once ordered, neighbours carry the information you need and a single "
    "pass usually finishes the job.",
    "backtracking": "Build the answer one choice at a time, recurse, then undo the choice; prune "
    "branches that can no longer lead to a valid answer.",
    "dynamic programming": "Define dp[i] in words (the answer for the first i items / ending at i), "
    "write the recurrence from smaller states, then fill the table in order.",
    "bit manipulation": "XOR cancels equal values (a ^ a = 0); masks with & and shifts test "
    "individual bits in O(1).",
}


@dataclass
class Finding:
    line: int | None
    message: str
    severity: str = "warning"  # "error" | "warning" | "suggestion"

    def render(self) -> str:
        where = f"Line {self.line}: " if self.line else ""
        return f"- {where}{self.message}"


@dataclass
class FunctionInfo:
    name: str
    params: list[str]
    start: int
    end: int
    loop_depth: int = 0
    loops: int = 0
    recursive: bool = False
    memoized: bool = False
    has_docstring: bool = False
    returns_value: bool = False
    calls: list[str] = field(default_factory=list)
    annotations: dict[str, str] = field(default_factory=dict)
    return_annotation: str | None = None
    raises: list[str] = field(default_factory=list)


@dataclass
class Analysis:
    language: str | None
    lines: int
    syntax_errors: list[Finding] = field(default_factory=list)
    compiler_warnings: list[Finding] = field(default_factory=list)
    issues: list[Finding] = field(default_factory=list)
    suggestions: list[Finding] = field(default_factory=list)
    functions: list[FunctionInfo] = field(default_factory=list)
    classes: list[str] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)
    data_structures: list[str] = field(default_factory=list)
    reads_input: bool = False
    prints_output: bool = False
    max_loop_depth: int = 0
    sorts: bool = False
    todos: list[int] = field(default_factory=list)
    entry_point: str | None = None
    checked_syntax: bool = True

    @property
    def label(self) -> str:
        return LANGUAGE_LABELS.get(self.language or "", "Unknown")


# --------------------------------------------------------------------------- public


def analyze(mode: str, content: str, context: str | None = None) -> str:
    """Return a markdown answer for one AI-assistant mode, based only on the input."""
    content = content or ""
    context = context or ""
    if mode == "hint":
        return _hint(content, context)
    if mode in {"interview", "roadmap"}:
        return _progress_summary(mode, content)

    language = detect_language(content)
    if language is None:
        return _not_code(mode, content)

    analysis = _analyze(language, content)
    renderer = {
        "explain": _explain,
        "review": _review,
        "debug": _debug,
        "tests": _tests,
        "docs": _docs,
    }[mode]
    return renderer(analysis, content, context)


def detect_language(code: str) -> str | None:
    text = code.strip()
    if not text:
        return None
    if re.search(r"#include\s*[<\"]", text):
        cpp = r"\b(std::|using\s+namespace|cout|cin|vector\s*<|class\s+\w+|template\s*<)"
        return "cpp" if re.search(cpp, text) else "c"
    if re.search(
        r"\bpublic\s+(static\s+)?(final\s+)?(class|void|int|String)\b|System\.out\.", text
    ):
        return "java"
    if re.search(
        r"\b(const|let|var)\s+\w+\s*=|=>|console\.log|\bfunction\b\s*\w*\s*\(|require\(", text
    ):
        return "javascript"
    python_markers = (
        r"^\s*(def|class)\s+\w+|^\s*(import|from)\s+\w+|\bprint\s*\(|"
        r"^\s*(for|while|if|elif|else|try|except|with)\b.*:\s*$|^\s*\w+\s*=\s*.+$|"
        r"^\s*return\b"
    )
    if re.search(python_markers, text, re.MULTILINE):
        return "python"
    if re.search(r"\b(int|void|char|double|float|long)\s+\w+\s*\(.*\)\s*\{", text):
        return "c"
    return None


# ------------------------------------------------------------------------- analysis


def _analyze(language: str, code: str) -> Analysis:
    analysis = Analysis(language=language, lines=len(code.splitlines()))
    analysis.todos = [
        number
        for number, line in enumerate(code.splitlines(), start=1)
        if re.search(r"\b(TODO|FIXME)\b", line)
    ]
    if language == "python":
        _analyze_python(analysis, code)
    else:
        _analyze_braces(analysis, code)
        _compile_check(analysis, code)
    return analysis


def _analyze_python(analysis: Analysis, code: str) -> None:
    try:
        tree = ast.parse(code, filename="<submitted code>")
    except SyntaxError as exc:
        analysis.syntax_errors.append(
            Finding(exc.lineno, _python_syntax_message(exc, code), "error")
        )
        # Still give a rough outline so explain/docs have something to say.
        _analyze_braces(analysis, code)
        return

    lines = code.splitlines()
    top_level_calls: set[str] = set()
    all_calls: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = _call_name(node.func)
            if name:
                all_calls.add(name)
            if name in {"input", "sys.stdin.read", "sys.stdin.readline", "sys.stdin.readlines"}:
                analysis.reads_input = True
            if name in {"print", "sys.stdout.write"}:
                analysis.prints_output = True
            if name in {"sorted"} or (name and name.endswith(".sort")):
                analysis.sorts = True
            for structure, label in (
                ("dict", "dictionary"),
                ("set", "set"),
                ("deque", "deque"),
                ("collections.deque", "deque"),
                ("Counter", "Counter"),
                ("collections.Counter", "Counter"),
                ("defaultdict", "defaultdict"),
                ("collections.defaultdict", "defaultdict"),
                ("heapq.heappush", "heap"),
                ("heappush", "heap"),
                ("bisect.bisect_left", "binary search (bisect)"),
            ):
                if name == structure and label not in analysis.data_structures:
                    analysis.data_structures.append(label)
        elif isinstance(node, ast.Dict) and "dictionary" not in analysis.data_structures:
            analysis.data_structures.append("dictionary")
        elif isinstance(node, ast.Set) and "set" not in analysis.data_structures:
            analysis.data_structures.append("set")
        elif isinstance(node, ast.Attribute) and _call_name(node) in {"sys.stdin"}:
            analysis.reads_input = True
        elif isinstance(node, ast.Import):
            analysis.imports += [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            analysis.imports.append(node.module or ".")
        elif isinstance(node, ast.ClassDef):
            analysis.classes.append(node.name)

    for statement in tree.body:
        for node in ast.walk(statement):
            if isinstance(node, ast.Call) and not isinstance(
                statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
            ):
                name = _call_name(node.func)
                if name:
                    top_level_calls.add(name)

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            analysis.functions.append(_function_info(node))

    analysis.max_loop_depth = _loop_depth(tree)
    if "main" in top_level_calls:
        analysis.entry_point = "main"

    _python_issues(analysis, tree, lines, top_level_calls, all_calls)


def _python_syntax_message(exc: SyntaxError, code: str) -> str:
    message = exc.msg
    # Take the line from the submission: exc.text can be read from an unrelated
    # file on disk that happens to share the reported filename.
    code_lines = code.splitlines()
    if exc.lineno and 0 < exc.lineno <= len(code_lines):
        source = code_lines[exc.lineno - 1]
        caret = " " * max((exc.offset or 1) - 1, 0) + "^"
        return f"**{type(exc).__name__}: {message}**\n\n  ```\n  {source}\n  {caret}\n  ```"
    return f"**{type(exc).__name__}: {message}**"


def _function_info(node: ast.FunctionDef | ast.AsyncFunctionDef) -> FunctionInfo:
    params = [arg.arg for arg in node.args.args if arg.arg not in {"self", "cls"}]
    info = FunctionInfo(
        name=node.name,
        params=params,
        start=node.lineno,
        end=getattr(node, "end_lineno", node.lineno) or node.lineno,
        has_docstring=ast.get_docstring(node) is not None,
        loop_depth=_loop_depth(node),
        loops=sum(isinstance(n, (ast.For, ast.While)) for n in ast.walk(node)),
        annotations={
            arg.arg: ast.unparse(arg.annotation) for arg in node.args.args if arg.annotation
        },
        return_annotation=ast.unparse(node.returns) if node.returns else None,
        memoized=any(
            (_call_name(d) or _call_name(getattr(d, "func", d)) or "").split(".")[-1]
            in {"lru_cache", "cache"}
            for d in node.decorator_list
        ),
    )
    calls: list[str] = []
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            name = _call_name(child.func)
            if name == node.name:
                info.recursive = True
            elif name and name not in calls:
                calls.append(name)
        elif isinstance(child, ast.Return) and child.value is not None:
            info.returns_value = True
        elif isinstance(child, ast.Raise) and child.exc is not None:
            raised = _call_name(getattr(child.exc, "func", child.exc))
            if raised and raised not in info.raises:
                info.raises.append(raised)
    info.calls = calls
    return info


def _python_issues(
    analysis: Analysis,
    tree: ast.Module,
    lines: list[str],
    top_level_calls: set[str],
    all_calls: set[str],
) -> None:
    issues, suggestions = analysis.issues, analysis.suggestions
    defined = {f.name for f in analysis.functions}

    has_top_level_work = any(
        not isinstance(
            s,
            (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Import, ast.ImportFrom),
        )
        and not (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant))
        for s in tree.body
    )
    if defined and not has_top_level_work:
        never_called = sorted(defined - all_calls)
        if never_called:
            issues.append(
                Finding(
                    None,
                    f"Nothing runs: `{never_called[0]}()` is defined but never called, so the "
                    "program exits without doing anything. Call it at the bottom of the file.",
                )
            )

    if analysis.reads_input and not analysis.prints_output:
        issues.append(
            Finding(
                None,
                "The program reads input but never prints anything, so the judge will see "
                "empty output.",
            )
        )

    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler) and node.type is None:
            issues.append(
                Finding(
                    node.lineno,
                    "Bare `except:` also swallows KeyboardInterrupt and hides real bugs; catch "
                    "a specific exception.",
                )
            )
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for default in node.args.defaults + node.args.kw_defaults:
                if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                    issues.append(
                        Finding(
                            node.lineno,
                            f"`{node.name}` uses a mutable default argument; it is shared "
                            "across calls. Use `None` and create it inside the function.",
                        )
                    )
            for arg in node.args.args:
                if arg.arg in _SHADOWED_BUILTINS:
                    suggestions.append(
                        Finding(
                            node.lineno,
                            f"Parameter `{arg.arg}` shadows the built-in `{arg.arg}()`.",
                            "suggestion",
                        )
                    )
            _unused_variables(node, issues)
            info = next(f for f in analysis.functions if f.name == node.name)
            if info.recursive and not any(isinstance(n, ast.If) for n in ast.walk(node)):
                issues.append(
                    Finding(
                        node.lineno,
                        f"`{node.name}` calls itself with no `if` guarding a base case, which "
                        "will hit RecursionError.",
                    )
                )
            if info.recursive and not info.memoized and _calls_self_twice(node):
                suggestions.append(
                    Finding(
                        node.lineno,
                        f"`{node.name}` recurses more than once per call; without memoization "
                        "(`@functools.cache`) this is exponential time.",
                        "suggestion",
                    )
                )
            if len(lines) and info.end - info.start > 40:
                suggestions.append(
                    Finding(
                        node.lineno,
                        f"`{node.name}` is {info.end - info.start + 1} lines long; consider "
                        "splitting it into smaller helpers.",
                        "suggestion",
                    )
                )
        elif isinstance(node, ast.Compare):
            for op, right in zip(node.ops, node.comparators, strict=False):
                if isinstance(op, (ast.Eq, ast.NotEq)) and _is_none(right):
                    suggestions.append(
                        Finding(node.lineno, "Compare with `is None` instead of `== None`.")
                    )
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in _SHADOWED_BUILTINS:
                    issues.append(
                        Finding(
                            node.lineno,
                            f"Assigning to `{target.id}` shadows the built-in "
                            f"`{target.id}()`; any later call to it will fail.",
                        )
                    )
            value = node.value
            if isinstance(value, ast.Call) and (_call_name(value.func) or "").endswith(".sort"):
                issues.append(
                    Finding(
                        node.lineno,
                        "`list.sort()` sorts in place and returns `None`; use `sorted(...)` "
                        "if you need the result.",
                    )
                )
        elif isinstance(node, ast.Subscript):
            index = node.slice
            if isinstance(index, ast.BinOp) and isinstance(index.op, ast.Div):
                issues.append(
                    Finding(
                        node.lineno,
                        "Index uses `/`, which produces a float and raises TypeError; use "
                        "`//` for integer division.",
                    )
                )
        elif isinstance(node, ast.While) and _is_true(node.test):
            if not any(isinstance(n, (ast.Break, ast.Return, ast.Raise)) for n in ast.walk(node)):
                issues.append(
                    Finding(node.lineno, "`while True` has no `break`/`return`: infinite loop.")
                )
        elif isinstance(node, ast.For) and _is_range_len(node.iter):
            suggestions.append(
                Finding(
                    node.lineno,
                    "`for i in range(len(x))` reads more clearly as `for i, item in "
                    "enumerate(x)`.",
                    "suggestion",
                )
            )
        if isinstance(node, (ast.For, ast.While)):
            for inner in ast.walk(node):
                if inner is node or not isinstance(inner, ast.Call):
                    continue
                name = _call_name(inner.func) or ""
                if name.endswith(".pop") and inner.args and _is_zero(inner.args[0]):
                    suggestions.append(
                        Finding(
                            inner.lineno,
                            "`pop(0)` inside a loop is O(n) each time; use "
                            "`collections.deque.popleft()`.",
                            "suggestion",
                        )
                    )
                elif name.endswith(".insert") and inner.args and _is_zero(inner.args[0]):
                    suggestions.append(
                        Finding(
                            inner.lineno,
                            "`insert(0, x)` inside a loop is O(n) each time; use a deque.",
                            "suggestion",
                        )
                    )

    # Whole-program findings (no line) first, then in source order.
    issues.sort(key=lambda f: f.line or 0)
    suggestions.sort(key=lambda f: f.line or 0)


def _unused_variables(node: ast.FunctionDef | ast.AsyncFunctionDef, issues: list[Finding]) -> None:
    stored: dict[str, int] = {}
    loaded: set[str] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Name):
            if isinstance(child.ctx, ast.Store):
                stored.setdefault(child.id, child.lineno)
            else:
                loaded.add(child.id)
    for name, line in stored.items():
        if name not in loaded and not name.startswith("_"):
            issues.append(
                Finding(
                    line,
                    f"`{name}` is assigned but never used — usually a sign the logic that "
                    "should use it is missing.",
                )
            )


def _analyze_braces(analysis: Analysis, code: str) -> None:
    """Rough structure for C-family/JS code (and Python that failed to parse)."""
    language = analysis.language
    if language == "javascript":
        pattern = r"function\s+(\w+)\s*\(([^)]*)\)|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\(?([^)=]*)\)?\s*=>"
    elif language == "python":
        pattern = r"^\s*def\s+(\w+)\s*\(([^)]*)\)"
    else:
        pattern = r"^[ \t]*(?:[\w<>\[\],:*&]+[ \t]+)+[*&]?(\w+)[ \t]*\(([^;{}]*)\)[ \t]*(?:const[ \t]*)?\{"
    keywords = {"if", "for", "while", "switch", "return", "else"}
    for match in re.finditer(pattern, code, re.MULTILINE):
        groups = [g for g in match.groups()]
        name = groups[0] or (groups[2] if len(groups) > 2 else None)
        raw_params = groups[1] if groups[0] else (groups[3] if len(groups) > 3 else "")
        if not name or name in keywords:
            continue
        params = [_param_name(p) for p in (raw_params or "").split(",") if p.strip()]
        start = code.count("\n", 0, match.start()) + 1
        analysis.functions.append(
            FunctionInfo(name=name, params=[p for p in params if p], start=start, end=start)
        )
    analysis.reads_input = bool(
        re.search(r"\b(scanf|cin\s*>>|getline|Scanner|BufferedReader|readFileSync|input\()", code)
    )
    analysis.prints_output = bool(
        re.search(r"\b(printf|puts|cout\s*<<|System\.out|console\.log|print\()", code)
    )
    analysis.sorts = bool(re.search(r"\b(sort|qsort|Arrays\.sort|Collections\.sort)\s*\(", code))
    for needle, label in (
        (r"\b(unordered_map|map<|HashMap|Map\(|new Map|dict\()", "hash map"),
        (r"\b(unordered_set|set<|HashSet|new Set|set\()", "set"),
        (r"\b(priority_queue|PriorityQueue|heapq)", "heap"),
        (r"\b(stack<|Stack<|Deque<|ArrayDeque)", "stack/deque"),
        (r"\b(queue<|Queue<|LinkedList<)", "queue"),
        (r"\b(vector<|ArrayList<|\[\])", "dynamic array"),
    ):
        if re.search(needle, code):
            analysis.data_structures.append(label)

    depth = 0
    stack: list[bool] = []
    pending_loop = False
    for token in re.finditer(r"\b(for|while)\b|[{}]", _strip_strings_and_comments(code)):
        text = token.group(0)
        if text in {"for", "while"}:
            pending_loop = True
        elif text == "{":
            stack.append(pending_loop)
            pending_loop = False
            depth = max(depth, sum(stack))
        elif stack:
            stack.pop()
    if language != "python":
        analysis.max_loop_depth = depth
    else:
        indents = [
            len(line) - len(line.lstrip())
            for line in code.splitlines()
            if re.match(r"\s*(for|while)\b", line)
        ]
        analysis.max_loop_depth = len(set(indents))
    if re.search(r"\bmain\s*\(", code):
        analysis.entry_point = "main"


def _compile_check(analysis: Analysis, code: str) -> None:
    """Run the real compiler/parser in syntax-only mode; never executes the code."""
    language = analysis.language
    if language == "javascript":
        tool, filename, argv = "node", "main.js", ["node", "--check", "main.js"]
    elif language == "c":
        tool, filename = "gcc", "main.c"
        argv = ["gcc", "-fsyntax-only", "-Wall", "-Wextra", "-std=c17", "main.c"]
    elif language == "cpp":
        tool, filename = "g++", "main.cpp"
        argv = ["g++", "-fsyntax-only", "-Wall", "-Wextra", "-std=c++17", "main.cpp"]
    elif language == "java":
        match = re.search(r"public\s+(?:final\s+)?class\s+(\w+)", code)
        class_name = match.group(1) if match else "Main"
        tool, filename = "javac", f"{class_name}.java"
        argv = ["javac", "-Xlint:all", "-d", "out", filename]
    else:
        return
    if not shutil.which(tool):
        analysis.checked_syntax = False
        return

    with tempfile.TemporaryDirectory(prefix="codeforge-ai-") as directory:
        Path(directory, filename).write_text(code, encoding="utf-8")
        Path(directory, "out").mkdir()
        try:
            completed = subprocess.run(
                argv, cwd=directory, capture_output=True, text=True, timeout=15, check=False
            )
        except (subprocess.TimeoutExpired, OSError):
            analysis.checked_syntax = False
            return
    output = (completed.stderr or "") + (completed.stdout or "")
    errors, warnings = _parse_diagnostics(output, filename)
    if completed.returncode != 0 and not errors:
        errors = [Finding(None, f"```\n{output.strip()[:1500]}\n```", "error")]
    analysis.syntax_errors += errors
    analysis.compiler_warnings += warnings


def _parse_diagnostics(output: str, filename: str) -> tuple[list[Finding], list[Finding]]:
    errors: list[Finding] = []
    warnings: list[Finding] = []
    lines = output.splitlines()
    pattern = re.compile(
        rf"^{re.escape(filename)}:(\d+)(?::\d+)?:\s*(fatal error|error|warning)?:?\s*(.*)$"
    )
    for index, line in enumerate(lines):
        match = pattern.match(line)
        if not match:
            if line.startswith("SyntaxError") and not errors:  # node --check
                snippet = "\n".join(lines[max(index - 3, 0) : index]).strip()
                line_no = re.search(r":(\d+)", lines[0]) if lines else None
                errors.append(
                    Finding(
                        int(line_no.group(1)) if line_no else None,
                        f"**{line}**\n\n  ```\n{_indent(snippet)}\n  ```",
                        "error",
                    )
                )
            continue
        number, kind, message = int(match.group(1)), match.group(2) or "error", match.group(3)
        excerpt = [
            text
            for text in lines[index + 1 : index + 3]
            if text.strip() and not pattern.match(text)
        ]
        detail = f"**{message.strip()}**"
        if excerpt:
            detail += f"\n\n  ```\n{_indent(chr(10).join(excerpt))}\n  ```"
        (warnings if kind == "warning" else errors).append(
            Finding(number, detail, "warning" if kind == "warning" else "error")
        )
    return errors[:8], warnings[:8]


# ---------------------------------------------------------------------------- modes

OFFLINE_NOTE = (
    "\n\n---\n_Offline analysis generated from your code (no AI model is configured). "
    "Set `OPENAI_API_KEY` in `.env` for full AI answers._"
)


def _not_code(mode: str, content: str) -> str:
    action = {
        "explain": "explain",
        "review": "review",
        "debug": "debug",
        "tests": "write tests for",
        "docs": "document",
    }.get(mode, "analyse")
    if not content.strip():
        return "Paste some code in the **Code** box first." + OFFLINE_NOTE
    preview = content.strip().splitlines()[0][:80]
    return (
        "### That doesn't look like code\n\n"
        f"I received: `{preview}`\n\n"
        f"To {action} something, paste a code snippet in **Python, JavaScript, C, C++ or "
        "Java**. Offline analysis can only read source code; free-form questions need an AI "
        "model to be configured." + OFFLINE_NOTE
    )


def _header(analysis: Analysis) -> str:
    parts = [f"**Language:** {analysis.label}", f"{analysis.lines} lines"]
    if analysis.functions:
        parts.append(f"{len(analysis.functions)} function(s)")
    if analysis.classes:
        parts.append(f"{len(analysis.classes)} class(es)")
    return " · ".join(parts)


def _syntax_section(analysis: Analysis) -> str:
    if not analysis.syntax_errors:
        return ""
    body = "\n".join(f.render() for f in analysis.syntax_errors)
    return (
        f"#### ❌ Syntax / compile errors\nThe code will not run until these are fixed.\n\n{body}\n"
    )


def _complexity(analysis: Analysis) -> str:
    depth = analysis.max_loop_depth
    notes = []
    for f in analysis.functions:
        if f.recursive and f.memoized:
            notes.append(f"`{f.name}` is memoized recursion: (number of states) × (work per state).")
        elif f.recursive:
            notes.append(
                f"`{f.name}` is recursive: linear if it recurses once per call, exponential if "
                "it branches without memoization."
            )
    recursion = (" " + " ".join(notes)) if notes else ""
    terms = {0: "O(1) or O(n) (no explicit loops)", 1: "O(n)", 2: "O(n²)", 3: "O(n³)"}
    estimate = terms.get(depth, f"O(n^{depth})")
    if analysis.sorts and depth <= 1:
        estimate = "O(n log n) (dominated by sorting)"
    reason = f"deepest loop nesting is {depth}" if depth else "no nested loops"
    return f"About **{estimate}** time — {reason}.{recursion}"


def _describe_function(info: FunctionInfo) -> str:
    params = ", ".join(f"`{p}`" for p in info.params) or "no parameters"
    bits = [f"takes {params}"]
    if info.loops:
        nested = f", nested {info.loop_depth} deep" if info.loop_depth > 1 else ""
        bits.append(f"runs {info.loops} loop(s){nested}")
    if info.recursive:
        bits.append("calls itself recursively" + (" (memoized)" if info.memoized else ""))
    useful_calls = [c for c in info.calls if c not in {"print", "len", "range", "int", "str"}]
    if useful_calls:
        bits.append("uses " + ", ".join(f"`{c}()`" for c in useful_calls[:5]))
    bits.append("returns a value" if info.returns_value else "returns nothing")
    where = f"line {info.start}" if info.start == info.end else f"lines {info.start}–{info.end}"
    return f"- **`{info.name}()`** ({where}): " + ", ".join(bits) + "."


def _explain(analysis: Analysis, code: str, context: str) -> str:
    out = ["### Code explanation", _header(analysis), ""]
    syntax = _syntax_section(analysis)
    if syntax:
        out += [syntax]
    overview = []
    if analysis.reads_input:
        overview.append("reads its input from standard input")
    if analysis.data_structures:
        overview.append("builds " + ", ".join(analysis.data_structures))
    if analysis.sorts:
        overview.append("sorts data")
    if analysis.prints_output:
        overview.append("prints the result")
    if overview:
        out.append("**Overview:** The program " + ", ".join(overview) + ".")
    if analysis.imports:
        out.append("**Imports:** " + ", ".join(f"`{i}`" for i in analysis.imports))
    if analysis.functions:
        out += ["", "**Functions**", *(_describe_function(f) for f in analysis.functions)]
    if analysis.entry_point:
        out.append(f"\nExecution starts by calling `{analysis.entry_point}()`.")
    out += ["", f"**Complexity:** {_complexity(analysis)}"]
    if analysis.todos:
        lines = ", ".join(map(str, analysis.todos))
        out.append(f"\n**Unfinished:** TODO/FIXME left on line(s) {lines}.")
    if context.strip():
        out.append(f"\n_Context noted:_ {context.strip()[:200]}")
    return "\n".join(out) + OFFLINE_NOTE


def _review(analysis: Analysis, code: str, context: str) -> str:
    out = ["### Code review", _header(analysis), ""]
    syntax = _syntax_section(analysis)
    if syntax:
        out.append(syntax)
    if analysis.issues:
        out += ["#### ⚠️ Problems", *(f.render() for f in analysis.issues), ""]
    if analysis.compiler_warnings:
        out += ["#### Compiler warnings", *(f.render() for f in analysis.compiler_warnings), ""]
    suggestions = list(analysis.suggestions)
    undocumented = [f.name for f in analysis.functions if not f.has_docstring and f.name != "main"]
    if analysis.language == "python" and undocumented and not analysis.syntax_errors:
        names = ", ".join(f"`{n}`" for n in undocumented[:4])
        suggestions.append(Finding(None, f"Add docstrings to {names}.", "suggestion"))
    unannotated = [
        f.name
        for f in analysis.functions
        if analysis.language == "python" and f.params and not f.annotations
    ]
    if unannotated and not analysis.syntax_errors:
        names = ", ".join(f"`{n}`" for n in unannotated[:4])
        suggestions.append(
            Finding(None, f"Add type hints to the parameters of {names}.", "suggestion")
        )
    if analysis.todos:
        suggestions.append(
            Finding(analysis.todos[0], "TODO left in the code — the logic is unfinished.")
        )
    if suggestions:
        out += ["#### 💡 Suggestions", *(f.render() for f in suggestions), ""]
    if not (analysis.syntax_errors or analysis.issues or analysis.compiler_warnings or suggestions):
        out.append("✅ No problems found by static checks.")
    out += ["", f"**Complexity:** {_complexity(analysis)}"]
    problems = (
        len(analysis.syntax_errors) * 3
        + len(analysis.issues) * 2
        + len(analysis.compiler_warnings)
        + len(suggestions)
    )
    out.append(f"**Score:** {max(1, 10 - problems)}/10 (based on the findings above)")
    return "\n".join(out) + OFFLINE_NOTE


def _debug(analysis: Analysis, code: str, context: str) -> str:
    out = ["### Debug analysis", _header(analysis), ""]
    syntax = _syntax_section(analysis)
    if syntax:
        out.append(syntax)
        out.append("Fix the error above first — it stops the program before any line runs.")
        return "\n".join(out) + OFFLINE_NOTE
    if analysis.issues:
        out += ["#### Likely bugs", *(f.render() for f in analysis.issues), ""]
    if analysis.compiler_warnings:
        out += ["#### Compiler warnings", *(f.render() for f in analysis.compiler_warnings), ""]
    if analysis.todos:
        out.append(
            f"- Line {analysis.todos[0]}: a TODO is still in place, so that part of the logic "
            "is missing."
        )
    if not (analysis.issues or analysis.compiler_warnings or analysis.todos):
        checked = "compiles" if analysis.checked_syntax else "has no obvious structural problems"
        out.append(
            f"✅ The code {checked} and no common bug patterns were found. If it still gives "
            "wrong answers, run it on the smallest failing input and print intermediate "
            "values; check off-by-one loop bounds and empty-input handling."
        )
    if context.strip():
        out.append(f"\n_Context noted:_ {context.strip()[:200]}")
    return "\n".join(out) + OFFLINE_NOTE


def _tests(analysis: Analysis, code: str, context: str) -> str:
    out = ["### Generated tests", _header(analysis), ""]
    syntax = _syntax_section(analysis)
    if syntax:
        out += [syntax, "Tests below assume the errors above are fixed.", ""]
    targets = [f for f in analysis.functions if f.params and f.name not in {"main"}]
    if analysis.language == "python" and targets:
        module_hint = "solution"
        test_lines = [
            "```python",
            "import pytest",
            "",
            f"from {module_hint} import " + ", ".join(f.name for f in targets),
            "",
        ]
        for f in targets:
            args = ", ".join(_example_value(p, f.annotations.get(p)) for p in f.params)
            empty_args = ", ".join(_edge_value(p, f.annotations.get(p)) for p in f.params)
            test_lines += [
                f"def test_{f.name}_typical_case():",
                f"    assert {f.name}({args}) == ...  # TODO: expected result",
                "",
                f"def test_{f.name}_edge_case():",
                f"    assert {f.name}({empty_args}) == ...  # empty / zero input",
                "",
            ]
            if f.raises:
                test_lines += [
                    f"def test_{f.name}_raises():",
                    f"    with pytest.raises({f.raises[0]}):",
                    f"        {f.name}({empty_args})",
                    "",
                ]
        test_lines.append("```")
        out += test_lines
        out.append("Save your code as `solution.py` and run `pytest`.")
    else:
        run = {
            "python": "python solution.py",
            "javascript": "node solution.js",
            "c": "./solution",
            "cpp": "./solution",
            "java": "java Main",
        }[analysis.language or "python"]
        out += [
            "This program reads standard input, so test it end-to-end with input/output pairs:",
            "",
            "```python",
            "import subprocess",
            "import pytest",
            "",
            "CASES = [",
            '    ("<typical input>\\n", "<expected output>\\n"),',
            '    ("<smallest input, e.g. n = 1>\\n", "<expected>\\n"),',
            '    ("<edge case: duplicates / negatives / maximum size>\\n", "<expected>\\n"),',
            "]",
            "",
            '@pytest.mark.parametrize("stdin, expected", CASES)',
            "def test_program(stdin, expected):",
            f"    result = subprocess.run({run.split()!r}, input=stdin,",
            "                            capture_output=True, text=True, timeout=5)",
            "    assert result.stdout.split() == expected.split()",
            "```",
        ]
    edge_cases = ["smallest valid input (n = 0 or 1)", "all elements equal", "negative numbers"]
    if analysis.sorts:
        edge_cases.append("input that is already sorted / reverse sorted")
    if analysis.max_loop_depth >= 2:
        edge_cases.append("maximum input size, to catch the O(n²) loop timing out")
    out += ["", "**Edge cases worth covering:** " + "; ".join(edge_cases) + "."]
    return "\n".join(out) + OFFLINE_NOTE


def _docs(analysis: Analysis, code: str, context: str) -> str:
    out = ["### Documentation", _header(analysis), ""]
    if analysis.syntax_errors:
        out += [_syntax_section(analysis)]
    purpose = []
    if analysis.reads_input:
        purpose.append("reads input from stdin")
    if analysis.prints_output:
        purpose.append("writes results to stdout")
    out.append(
        "#### Overview\n"
        + (
            f"A {analysis.label} program that " + " and ".join(purpose) + "."
            if purpose
            else f"A {analysis.label} module."
        )
    )
    if analysis.imports:
        out.append("**Dependencies:** " + ", ".join(f"`{i}`" for i in analysis.imports))
    for f in analysis.functions:
        signature = ", ".join(
            f"{p}: {f.annotations[p]}" if p in f.annotations else p for p in f.params
        )
        returns = f" -> {f.return_annotation}" if f.return_annotation else ""
        out += ["", f"#### `{f.name}({signature}){returns}`", f"{_humanize(f.name)}."]
        if f.params:
            out.append("**Parameters**")
            out += [
                f"- `{p}`"
                + (f" (*{f.annotations[p]}*)" if p in f.annotations else "")
                + f": {_humanize(p).lower()}."
                for p in f.params
            ]
        if f.returns_value or f.return_annotation not in {None, "None"}:
            out.append(
                "**Returns:** "
                + (f"`{f.return_annotation}`" if f.return_annotation else "the computed result")
            )
        if f.raises:
            out.append("**Raises:** " + ", ".join(f"`{r}`" for r in f.raises))
        if f.loops or f.recursive:
            out.append(
                f"**Complexity:** {'recursive' if f.recursive else f'{f.loops} loop(s)'}, "
                f"loop nesting depth {f.loop_depth}."
            )
    if not analysis.functions:
        out.append("\nNo functions found — the code runs top to bottom as a script.")
    return "\n".join(out) + OFFLINE_NOTE


def _hint(content: str, context: str) -> str:
    tags = re.search(r"^Tags:\s*(.+)$", context, re.MULTILINE)
    title = re.search(r"^Problem:\s*(.+?)\s*\(", context, re.MULTILINE)
    tag_names = [t.strip().lower() for t in tags.group(1).split(",")] if tags else []
    out = ["### Hint" + (f" for {title.group(1)}" if title else "")]
    hints = [_TAG_HINTS[t] for t in tag_names if t in _TAG_HINTS]
    if hints:
        out.append(f"**Topic:** {', '.join(tag_names)}\n")
        out += [f"- {h}" for h in hints]
    language = detect_language(content)
    if language:
        analysis = _analyze(language, content)
        notes = []
        if analysis.syntax_errors:
            first = analysis.syntax_errors[0]
            notes.append(f"Your code has a syntax error on line {first.line}; fix that first.")
        if analysis.todos and not analysis.issues:
            notes.append(
                "Start by parsing the input into variables, then build the answer step by step."
            )
        if analysis.max_loop_depth >= 2:
            notes.append(
                f"Your current approach nests loops {analysis.max_loop_depth} deep "
                f"({_complexity(analysis)}); the hint above is how to remove a level of nesting."
            )
        notes += [f.message for f in analysis.issues[:2]]
        if notes:
            out += ["", "**About your code**", *(f"- {n}" for n in notes)]
    if len(out) == 1:
        out.append(
            "Restate the problem in terms of input size: what is the slowest acceptable "
            "complexity? Then pick the data structure that makes the repeated operation cheap."
        )
    return "\n".join(out) + OFFLINE_NOTE


def _progress_summary(mode: str, content: str) -> str:
    title = "Interview feedback" if mode == "interview" else "Roadmap suggestions"
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    out = [f"### {title}"]
    if not lines:
        out.append("Not enough information yet — complete a few questions/problems first.")
    else:
        out.append("Based on the information provided:")
        out += [f"- {line[:200]}" for line in lines[:8]]
    return "\n".join(out) + OFFLINE_NOTE


# -------------------------------------------------------------------------- helpers


def _call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _call_name(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    return None


def _loop_depth(node: ast.AST, current: int = 0) -> int:
    deepest = current
    for child in ast.iter_child_nodes(node):
        is_loop = isinstance(child, (ast.For, ast.While, ast.comprehension))
        deepest = max(deepest, _loop_depth(child, current + 1 if is_loop else current))
    return deepest


def _calls_self_twice(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    return (
        sum(isinstance(c, ast.Call) and _call_name(c.func) == node.name for c in ast.walk(node))
        >= 2
    )


def _is_none(node: ast.AST) -> bool:
    return isinstance(node, ast.Constant) and node.value is None


def _is_true(node: ast.AST) -> bool:
    return isinstance(node, ast.Constant) and node.value is True


def _is_zero(node: ast.AST) -> bool:
    return isinstance(node, ast.Constant) and node.value == 0


def _is_range_len(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Call)
        and _call_name(node.func) == "range"
        and len(node.args) == 1
        and isinstance(node.args[0], ast.Call)
        and _call_name(node.args[0].func) == "len"
    )


def _param_name(raw: str) -> str:
    raw = raw.split("=")[0].strip()
    tokens = re.findall(r"\w+", raw)
    return tokens[-1] if tokens else ""


def _strip_strings_and_comments(code: str) -> str:
    code = re.sub(r"//[^\n]*|/\*.*?\*/", "", code, flags=re.DOTALL)
    return re.sub(r"\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*'", '""', code)


def _humanize(name: str) -> str:
    words = re.sub(r"([a-z])([A-Z])", r"\1 \2", name).replace("_", " ").strip()
    return words[:1].upper() + words[1:] if words else name


def _indent(text: str) -> str:
    return "\n".join(f"  {line}" for line in text.splitlines())


def _example_value(name: str, annotation: str | None) -> str:
    hint = (annotation or name).lower()
    if any(k in hint for k in ("dict", "map", "graph", "seen", "memo", "cache")):
        return "{1: [2], 2: []}"
    if any(k in hint for k in ("list", "nums", "arr", "items", "values", "[")):
        return "[2, 7, 11, 15]"
    if hint in {"s", "t"} or any(k in hint for k in ("str", "text", "word", "name")):
        return '"example"'
    return "3"


def _edge_value(name: str, annotation: str | None) -> str:
    example = _example_value(name, annotation)
    return {"[2, 7, 11, 15]": "[]", '"example"': '""', "{1: [2], 2: []}": "{}"}.get(example, "0")
