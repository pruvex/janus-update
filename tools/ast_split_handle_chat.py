"""
AST-based split of ChatOrchestrator.handle_chat_request into 5 phase bodies using ctx.workflow.

Run from repo root:
  python tools/ast_split_handle_chat.py

Rewrites backend/services/chat_orchestrator.py (backup recommended).
"""
from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import FrozenSet, List, Set

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "backend" / "services" / "chat_orchestrator.py"
STATE_PATH = ROOT / "backend" / "services" / "orchestrator" / "chat_request_workflow_state.py"

FILE_LINE_START = 1037
FILE_LINE_END = 3418

# Phase boundaries (1-based file line numbers, inclusive ranges for phases 1-5)
P1_END = 1107
P2_END = 1691
P3_END = 2453
P4_END = 2996

BLOCK = frozenset(
    {
        "self", "ctx", "wf", "request", "background_tasks", "True", "False", "None",
        "int", "str", "float", "bool", "dict", "list", "set", "tuple", "len", "isinstance",
        "getattr", "setattr", "hasattr", "super", "type", "print", "range", "enumerate",
        "zip", "map", "filter", "sorted", "min", "max", "sum", "abs", "round", "open",
        "bytes", "object", "property", "staticmethod", "classmethod", "Exception", "ValueError",
        "TypeError", "KeyError", "RuntimeError", "OSError", "IOError", "json", "re", "os",
        "time", "uuid", "asyncio", "logging", "keyring", "datetime", "schemas", "crud",
        "logger", "ChatOrchestrator", "tool_manager", "intent_classifier", "vision_service",
        "cost_service", "memory_manager", "memory_extractor", "llm_gateway", "image_manager",
        "SessionLocal", "HTTPException", "ValidationError", "desc", "text", "or_", "Document",
        "Memory", "Message", "ExtractedFact", "openai_profile", "gemini_profile",
        "UnifiedWebSearchRenderer", "apply_directives", "DIRECTIVES", "PromptDirective",
        "ExecutionResponse", "AuditContext", "OrchestratorExecutionEngine", "ToolExecutor",
        "Optional", "List", "Dict", "Any", "Tuple", "Union", "field", "dataclass",
    }
)


def collect_assigned_names_skip_nested_funcs(stmts: List[ast.stmt]) -> Set[str]:
    names: Set[str] = set()

    def walk_block(block: List[ast.stmt]) -> None:
        for st in block:
            walk_stmt(st)

    def walk_stmt(st: ast.stmt) -> None:
        if isinstance(st, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return
        if isinstance(st, ast.Assign):
            for t in st.targets:
                if isinstance(t, ast.Name):
                    names.add(t.id)
        elif isinstance(st, ast.AnnAssign) and isinstance(st.target, ast.Name):
            names.add(st.target.id)
        elif isinstance(st, ast.AugAssign) and isinstance(st.target, ast.Name):
            names.add(st.target.id)
        elif isinstance(st, ast.If):
            walk_block(st.body)
            walk_block(st.orelse)
        elif isinstance(st, (ast.For, ast.AsyncFor)):
            walk_block(st.body)
            walk_block(st.orelse)
        elif isinstance(st, ast.While):
            walk_block(st.body)
            walk_block(st.orelse)
        elif isinstance(st, ast.Try):
            walk_block(st.body)
            for h in st.handlers:
                walk_block(h.body)
            walk_block(st.orelse)
            walk_block(st.finalbody)
        elif isinstance(st, ast.With):
            for item in st.body:
                walk_stmt(item)
        elif isinstance(st, ast.Match):  # py3.10+
            for case in st.cases:
                walk_block(case.body)

    walk_block(stmts)
    return names


def collect_for_bind_names(tree: ast.AST) -> Set[str]:
    found: Set[str] = set()

    class V(ast.NodeVisitor):
        def visit_For(self, node: ast.For) -> None:
            self._pat(node.target)
            self.generic_visit(node)

        def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
            self._pat(node.target)
            self.generic_visit(node)

        def visit_comprehension(self, node: ast.comprehension) -> None:
            self._pat(node.target)
            self.generic_visit(node)

        def visit_With(self, node: ast.With) -> None:
            for it in node.items:
                if it.optional_vars:
                    self._pat(it.optional_vars)
            self.generic_visit(node)

        def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
            if node.name:
                if isinstance(node.name, str):
                    found.add(node.name)
                elif isinstance(node.name, ast.Name):
                    found.add(node.name.id)
            self.generic_visit(node)

        def _pat(self, t: ast.AST) -> None:
            if isinstance(t, ast.Name):
                found.add(t.id)
            elif isinstance(t, ast.Tuple) or isinstance(t, ast.List):
                for e in t.elts:
                    self._pat(e)

    V().visit(tree)
    return found


class WorkflowRename(ast.NodeTransformer):
    def __init__(self, allow: FrozenSet[str]) -> None:
        self.allow = allow
        self.func_depth = 0

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
        self.func_depth += 1
        node = self.generic_visit(node)
        self.func_depth -= 1
        return node

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AST:
        self.func_depth += 1
        node = self.generic_visit(node)
        self.func_depth -= 1
        return node

    def visit_Assign(self, node: ast.Assign) -> ast.Assign:
        if self.func_depth > 0:
            return self.generic_visit(node)
        new_targets = []
        for t in node.targets:
            if isinstance(t, ast.Name) and t.id in self.allow:
                new_targets.append(
                    ast.Attribute(value=ast.Name(id="wf", ctx=ast.Load()), attr=t.id, ctx=ast.Store())
                )
            else:
                new_targets.append(self.visit(t))
        return ast.Assign(targets=new_targets, value=self.visit(node.value), type_comment=node.type_comment)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> ast.AST:
        if self.func_depth > 0:
            return self.generic_visit(node)
        if isinstance(node.target, ast.Name) and node.target.id in self.allow:
            # wf.attr cannot be annotated in assignment form; drop annotation.
            val = self.visit(node.value) if node.value is not None else ast.Constant(value=None)
            return ast.Assign(
                targets=[
                    ast.Attribute(
                        value=ast.Name(id="wf", ctx=ast.Load()),
                        attr=node.target.id,
                        ctx=ast.Store(),
                    )
                ],
                value=val,
                type_comment=None,
            )
        return self.generic_visit(node)

    def visit_AugAssign(self, node: ast.AugAssign) -> ast.AugAssign:
        if self.func_depth > 0:
            return self.generic_visit(node)
        if isinstance(node.target, ast.Name) and node.target.id in self.allow:
            return ast.AugAssign(
                target=ast.Attribute(value=ast.Name(id="wf", ctx=ast.Load()), attr=node.target.id, ctx=ast.Store()),
                op=node.op,
                value=self.visit(node.value),
            )
        return self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> ast.AST:
        if self.func_depth > 0:
            return node
        if isinstance(node.ctx, ast.Load) and node.id in self.allow:
            return ast.Attribute(value=ast.Name(id="wf", ctx=ast.Load()), attr=node.id, ctx=ast.Load())
        return node


def wrap_body_as_async_func(inner_lines: List[str]) -> str:
    dedented = []
    for line in inner_lines:
        if line.startswith("        "):
            dedented.append("    " + line[8:])
        else:
            dedented.append(line)
    return "async def __phase__():\n" + "\n".join(dedented) + "\n"


def phase_for_line(file_line: int) -> int:
    if file_line <= P1_END:
        return 1
    if file_line <= P2_END:
        return 2
    if file_line <= P3_END:
        return 3
    if file_line <= P4_END:
        return 4
    return 5


def main() -> None:
    lines = PATH.read_text(encoding="utf-8").splitlines()
    body_lines = lines[FILE_LINE_START - 1 : FILE_LINE_END]
    src = wrap_body_as_async_func(body_lines)
    tree = ast.parse(src)

    outer = tree.body[0]
    assert isinstance(outer, ast.AsyncFunctionDef)
    stmts = outer.body

    top_assigned = collect_assigned_names_skip_nested_funcs(stmts)
    for_bound = collect_for_bind_names(tree)
    allow = frozenset(top_assigned - for_bound - BLOCK)

    inner_mod = ast.Module(body=list(stmts), type_ignores=[])
    renamed_inner = WorkflowRename(allow).visit(inner_mod)
    ast.fix_missing_locations(renamed_inner)
    new_stmts = renamed_inner.body

    # Replace _mark_retry_path calls -> ctx.workflow.mark_retry_path
    class FixRetry(ast.NodeTransformer):
        def visit_Call(self, node: ast.Call) -> ast.AST:
            self.generic_visit(node)
            if isinstance(node.func, ast.Name) and node.func.id == "_mark_retry_path":
                return ast.Call(
                    func=ast.Attribute(
                        value=ast.Attribute(value=ast.Name(id="ctx", ctx=ast.Load()), attr="workflow", ctx=ast.Load()),
                        attr="mark_retry_path",
                        ctx=ast.Load(),
                    ),
                    args=node.args,
                    keywords=node.keywords,
                )
            return node

    wrap_mod = ast.Module(body=new_stmts, type_ignores=[])
    FixRetry().visit(wrap_mod)
    ast.fix_missing_locations(wrap_mod)
    new_stmts = wrap_mod.body

    # Remove nested def _mark_retry_path
    filtered: List[ast.stmt] = []
    skip_until = None
    for i, st in enumerate(new_stmts):
        if skip_until is not None:
            if i < skip_until:
                continue
            skip_until = None
        if isinstance(st, ast.FunctionDef) and st.name == "_mark_retry_path":
            continue
        filtered.append(st)
    new_stmts = filtered

    # Group by phase
    phases: List[List[ast.stmt]] = [[] for _ in range(5)]
    for st in new_stmts:
        ln = getattr(st, "lineno", 2)
        file_line = FILE_LINE_START + (ln - 2)
        phases[phase_for_line(file_line) - 1].append(st)

    # Emit workflow state fields
    list_names = {
        "kpi_retry_paths",
        "relevant_skill_ids",
        "decision_tokens",
        "factcheck_tokens",
        "_shopping_intent_keywords_early",
        "_shopping_context_markers_early",
        "ollama_tool_triggers",
        "ollama_smalltalk_phrases",
        "image_intent_keywords",
        "local_business_keywords",
        "local_search_markers",
        "_personal_recall_keywords",
    }
    field_lines = []
    for n in sorted(allow):
        if n in list_names:
            field_lines.append(f"    {n}: List[Any] = field(default_factory=list)")
        else:
            field_lines.append(f"    {n}: Any = None")

    state_txt = (
        '"""Mutable workflow state for ChatOrchestrator.handle_chat_request (Phase 3 refactor)."""\n'
        "from __future__ import annotations\n\n"
        "from dataclasses import dataclass, field\n"
        "from typing import Any, List\n\n\n"
        "@dataclass\n"
        "class ChatRequestWorkflowState:\n"
        + "\n".join(field_lines)
        + "\n\n"
        "    def mark_retry_path(self, path: str) -> None:\n"
        '        normalized = str(path or "").strip()\n'
        "        if normalized and normalized not in self.kpi_retry_paths:\n"
        "            self.kpi_retry_paths.append(normalized)\n"
    )
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(state_txt, encoding="utf-8")

    def emit_stmts(sts: List[ast.stmt], indent: str) -> List[str]:
        src = ast.unparse(ast.Module(body=sts, type_ignores=[]))
        out = []
        for L in src.splitlines():
            out.append(indent + L)
        return out

    ind = "        "
    p1 = emit_stmts(phases[0], ind)
    p2 = emit_stmts(phases[1], ind)
    p3 = emit_stmts(phases[2], ind)
    p4 = emit_stmts(phases[3], ind)
    p5 = emit_stmts(phases[4], ind)

    # Post-fix: wf.kpi_retry_paths.append already correct; ast may emit ctx.workflow.mark_retry_path

    # Exclude the old `async def handle_chat_request` header line (file line FILE_LINE_START-1)
    pre = lines[: FILE_LINE_START - 2]

    # Insert imports + RequestContext before class ChatOrchestrator
    pre_text = "\n".join(pre)
    if "from dataclasses import dataclass" not in pre_text:
        pre_text = pre_text.replace(
            "from typing import Dict, Optional, List, Any, Tuple\n",
            "from typing import Dict, Optional, List, Any, Tuple\nfrom dataclasses import dataclass\n",
        )
    if "chat_request_workflow_state" not in pre_text:
        pre_text = pre_text.replace(
            "from backend.services.orchestrator.execution_engine import OrchestratorExecutionEngine\n",
            "from backend.services.orchestrator.execution_engine import OrchestratorExecutionEngine\n"
            "from backend.services.orchestrator.chat_request_workflow_state import ChatRequestWorkflowState\n",
        )
    pre = pre_text.splitlines()

    cls_i = next(i for i, L in enumerate(pre) if L.startswith("class ChatOrchestrator"))
    req_ctx = [
        "",
        "@dataclass",
        "class RequestContext:",
        '    """Per-request context for phased handle_chat_request."""',
        "    request: schemas.ChatRequest",
        "    background_tasks: Optional[Any] = None",
        "    identity_fact: Any = None",
        "    selected_slots: Optional[List[Any]] = None",
        '    memory_context_string: str = ""',
        '    formatted_fact_coupons: str = ""',
        "    workflow: Any = None",
        "",
    ]
    pre = pre[:cls_i] + req_ctx + pre[cls_i:]

    methods: List[str] = [
        "    def _classify_request(self, request: schemas.ChatRequest, background_tasks: Any = None) -> RequestContext:",
        "        ctx = RequestContext(request=request, background_tasks=background_tasks)",
        "        ctx.workflow = ChatRequestWorkflowState()",
        "        wf = ctx.workflow",
        "        request = ctx.request",
    ]
    methods += p1
    methods += ["        ctx.identity_fact = wf._identity", "        return ctx", ""]
    methods += [
        "    async def _try_early_exit(self, ctx: RequestContext) -> Optional[Dict]:",
        "        wf = ctx.workflow",
        "        request = ctx.request",
        "        background_tasks = ctx.background_tasks",
    ]
    methods += p2
    methods += ["        return None", ""]
    methods += [
        "    async def _build_memory_context(self, ctx: RequestContext) -> RequestContext:",
        "        wf = ctx.workflow",
        "        request = ctx.request",
        "        background_tasks = ctx.background_tasks",
    ]
    methods += p3
    methods += [
        "        ctx.memory_context_string = wf.memory_context_string",
        "        if getattr(wf, 'selected', None) is not None:",
        "            ctx.selected_slots = list(wf.selected)",
        "        ctx.formatted_fact_coupons = str(getattr(wf, '_formatted_coupons', '') or '')",
        "        return ctx",
        "",
    ]
    methods += [
        "    async def _execute_generation(self, ctx: RequestContext) -> RequestContext:",
        "        wf = ctx.workflow",
        "        request = ctx.request",
        "        background_tasks = ctx.background_tasks",
    ]
    methods += p4
    methods += ["        return ctx", ""]
    methods += [
        "    async def _finalize_response(self, ctx: RequestContext) -> Dict:",
        "        wf = ctx.workflow",
        "        request = ctx.request",
        "        background_tasks = ctx.background_tasks",
    ]
    methods += p5
    methods += [""]

    dispatcher = [
        "    async def handle_chat_request(self, request: schemas.ChatRequest, background_tasks: Any = None) -> Dict:",
        "        ctx = self._classify_request(request, background_tasks)",
        "        early = await self._try_early_exit(ctx)",
        "        if early is not None:",
        "            return early",
        "        ctx = await self._build_memory_context(ctx)",
        "        ctx = await self._execute_generation(ctx)",
        "        return await self._finalize_response(ctx)",
        "",
    ]

    new_lines = pre + methods + dispatcher + lines[FILE_LINE_END:]
    PATH.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    print("Wrote phases; allow size", len(allow))


if __name__ == "__main__":
    main()
