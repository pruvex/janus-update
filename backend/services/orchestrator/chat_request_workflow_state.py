"""Mutable workflow state for :meth:`ChatOrchestrator.handle_chat_request` (phase pipeline).

Attributes mirror legacy ``wf.*`` assignments across the orchestrator and related
modules. Intent- and skill-related fields use concrete ``bool`` / ``list[str]`` types
where the refactor touched them (e.g. ``relevant_skill_ids``, ``is_shopping_intent``,
``is_meta_agent_run``).

Other fields use ``Optional[...]``, ``dict``, or ``Any`` depending on how heterogeneous
runtime values are (vision payloads, tool-loop results, ORM rows).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from re import Match, Pattern
from typing import Any, Callable, Dict, List, Optional

from backend.services.memory_identity import IdentitySlot
from backend.services.orchestrator.intent_engine import IntentDetectionResult
from backend.services.orchestrator.schemas import AuditContext, ExecutionResponse, OrchestratorContext


@dataclass
class ChatRequestWorkflowState:
    _GERMAN_DAYS: List[str] = field(default_factory=list)
    _active_directive_names: Any = None
    _active_directives: Any = None
    _anchor: Any = None
    _anti_confusion: Any = None
    _before: Any = None
    _budget_raw: Any = None
    _budget_re_match: Optional[Match[str]] = None
    _clock_line: Any = None
    _day_name: Any = None
    _detected_budget: Optional[float] = None
    _fact_coupons: Any = None
    _formatted_coupons: Any = None
    _has_negative_preferences: Any = None
    _id_directive: Any = None
    _id_tag: Any = None
    _identity: Optional[IdentitySlot] = None
    _identity_from_current_msg: bool = False
    _is_gpt: bool = False
    _is_name_recall: bool = False
    _is_personal_recall: bool = False
    _is_plain_chat: bool = False
    _is_small_model: bool = False
    _memory_ratio: Any = None
    _memory_recall_block: Any = None
    _model_lower: Any = None
    _name_recall_re: Optional[Pattern[str]] = None
    _normalize_tool_args_fn: Optional[Callable[..., Any]] = None
    _now_local: Any = None
    _osh: Any = None
    _realtime_name: Any = None
    _sd: Any = None
    _skill_directive_parts: List[str] = field(default_factory=list)
    _websearch_skills: Any = None
    action_guidance: Any = None
    active_personality: Any = None
    agent_execution: Any = None
    agent_flow_error: Any = None
    agent_response_payload: Any = None
    aggregated_cost: Dict[str, Any] = field(default_factory=dict)
    aggregated_usage: Dict[str, Any] = field(default_factory=dict)
    all_dynamic_skills: Any = None
    api_key: Optional[str] = None
    audit_context_to_save: Optional[AuditContext] = None
    audit_data: Any = None
    audit_target_filename: Any = None
    bald_required: bool = False
    base: Any = None
    base64_image: Any = None
    base_system_prompt: Any = None
    blocked_arguments: Dict[str, Any] = field(default_factory=dict)
    blocked_skill_id: Any = None
    budget: Any = None
    bypass_policy_this_turn: bool = False
    candidate_url: Any = None
    calendar_context_string: str = ""
    calendar_proactive_guidance: str = ""
    calendar_snapshot: Any = None
    capability_groups: Dict[str, Any] = field(default_factory=dict)
    capability_guidance: Any = None
    chat_row: Any = None  # Chat ORM row
    chat_title: Any = None
    chat_title_l: Any = None
    chosen_model: Any = None
    citation_guidance: Any = None
    clean_comp: Any = None
    clean_text: Any = None
    cleaned_fact_block: Any = None
    cleaned_sentences: List[str] = field(default_factory=list)
    clip_verified: Any = None
    cloud_description: Any = None
    cloud_task: Any = None
    cloud_vision_result: Dict[str, Any] = field(default_factory=dict)
    cmd: Any = None
    config: Dict[str, Any] = field(default_factory=dict)
    content: Any = None
    content_json: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    critical_keys: Any = None
    current_limit: int = 0
    data: Dict[str, Any] = field(default_factory=dict)
    decision_response_text: Any = None
    decision_silent: Any = None
    decision_tokens: List[str] = field(default_factory=list)
    dedup: List[str] = field(default_factory=list)
    dialog_mode: Any = None
    direct_dispatch_handled: bool = False
    direct_dispatch_image_url: Optional[str] = None
    direct_pdf_execution: Any = None  # ExecutionResponse-like from meta PDF path
    disable_tools: bool = False
    display_text: Any = None
    dynamic_skills: Any = None
    engine_status: Any = None
    err_msg: Any = None
    event: Any = None
    event_data: Dict[str, Any] = field(default_factory=dict)
    exclusion_terms: Any = None
    execution_for_api: Optional[ExecutionResponse] = None
    execution_for_persist: Optional[ExecutionResponse] = None
    executor: Any = None
    fact_count: int = 0
    factcheck_modifications_detected: Optional[bool] = None
    factcheck_prompt_pending: bool = False
    factcheck_tokens: List[str] = field(default_factory=list)
    facts: Dict[str, Any] = field(default_factory=dict)
    fallback_agent_text: Any = None
    fallback_summary: Any = None
    final_facts: Dict[str, Any] = field(default_factory=dict)
    final_image_url: Any = None
    final_markdown: Any = None
    final_system_prompt: Any = None
    final_text: Any = None
    final_text_lower: Any = None
    final_text_to_generate: Any = None
    final_ui_command: Any = None
    fname: Any = None
    font_fallback_notice: Any = None
    footwear_exclusion: bool = False
    gate_prompt: Any = None
    gateway_kwargs: Dict[str, Any] = field(default_factory=dict)
    gemini_stream_raw_model_parts: List[Any] = field(default_factory=list)
    intent_detection_result: Optional[IntentDetectionResult] = None
    grant_payload: Any = None
    grant_results: Any = None
    hair_conflict_tokens: Any = None
    has_audit: bool = False
    has_image: bool = False
    has_tool_trigger: bool = False
    high_output_required: bool = False
    history_limit: int = 0
    image_data: Any = None
    image_intent_keywords: List[str] = field(default_factory=list)
    image_key: Any = None
    image_name_hint: Any = None
    image_name_hint_l: Any = None
    image_pdf_flow_guidance: Any = None
    is_audit_decision: bool = False
    is_audit_request: bool = False
    is_basic_conversation: bool = False
    is_eval_reporting: bool = False
    is_factcheck_decision: bool = False
    is_factcheck_no: bool = False
    is_factcheck_yes: bool = False
    is_first_meeting: bool = False
    is_identity_turn: bool = False
    is_large_ollama_model: bool = False
    is_local_business_intent: bool = False
    is_local_planner_early_exit: bool = False
    is_menu_selection: bool = False
    is_meta_agent_candidate: bool = False
    is_meta_agent_run: bool = False
    is_multitask_image_pdf: bool = False
    is_numeric_decision: bool = False
    is_ollama_provider: bool = False
    is_ollama_vague_smalltalk: bool = False
    is_personal_recall: bool = False
    is_policy_question: bool = False
    is_policy_response: bool = False
    is_pure_json: bool = False
    is_realtime_search_query: bool = False
    is_shopping_intent: bool = False
    is_shopping_intent_early: bool = False
    is_video_intent: bool = False
    is_simple_document_check_prompt: bool = False
    is_small: bool = False
    is_smalltalk_turn: bool = False
    is_storybook_macro: bool = False
    is_waiting_for_consent: bool = False
    json_match: Any = None
    json_path: Any = None
    json_str: Any = None
    k: Any = None
    kpi_error_code: Any = None
    kpi_phase1_research_ms: Optional[float] = None
    kpi_phase1_started_at: Optional[float] = None
    kpi_phase2_pdf_ms: Optional[float] = None
    kpi_phase2_started_at: Optional[float] = None
    kpi_retry_paths: List[str] = field(default_factory=list)
    kpi_success: bool = False
    last_model_message: Any = None
    last_model_text: Any = None
    latest_ui_command: Any = None
    lean_tool_call_examples: Any = None
    learned_name: Any = None
    lines: List[str] = field(default_factory=list)
    literal_blacklist: Any = None
    literal_block: Any = None
    literal_lines: List[str] = field(default_factory=list)
    llm_input: Dict[str, Any] = field(default_factory=dict)
    llm_output_lower: Any = None
    llm_payload: Any = None
    local_task: Any = None
    markdown_image_match: Any = None
    match: Any = None
    maturity_entries: Any = None
    max_tokens: int = 0
    memory_context_string: Any = None
    messages: List[Dict[str, Any]] = field(default_factory=list)
    meta_fast_path: Any = None
    meta_profile: Any = None
    missing_literals: List[str] = field(default_factory=list)
    missing_required_terms: List[str] = field(default_factory=list)
    missing_terms: List[str] = field(default_factory=list)
    model: Any = None
    model_limit: int = 0
    model_name_lower: Any = None
    mods: Any = None
    modal_request: Any = None
    normalized_exclusions: Any = None
    orchestrator_context: Optional[OrchestratorContext] = None
    original_cost: Optional[float] = None
    original_document_name: Any = None
    original_filename: Any = None
    parity_dir: Any = None
    parsed: Dict[str, Any] = field(default_factory=dict)
    payload: Dict[str, Any] = field(default_factory=dict)
    pdf_only_skill: Any = None
    pdf_requested: bool = False
    phase1_context: Any = None
    phase1_execution: Any = None
    phase2_execution: Any = None
    phase2_prompt: Any = None
    placeholder_md_pattern: Any = None
    planner_prefers_agent: bool = False
    plugin_gate_debug: Any = None
    policy_injection_message: Any = None
    policy_pending_data: Dict[str, Any] = field(default_factory=dict)
    proactive_guidance: Any = None
    profile_to_save: Any = None
    provider: Any = None
    question_line: Any = None
    question_present: bool = False
    raw_data: Any = None
    raw_text: Any = None
    recherche_domains: Any = None
    relevant_facts: Any = None
    relevant_skill_ids: List[str] = field(default_factory=list)
    rendered_websearch: Any = None
    reporter_fact_source: Any = None
    reporter_facts: Any = None
    request_provider: Any = None
    request_started_at: Optional[float] = None
    request_trace_id: Any = None
    requested_pdf_filename: Any = None
    required_terms_by_image: Dict[str, List[str]] = field(default_factory=dict)
    required_verified_terms: Any = None
    research_guidance: Any = None
    response: Dict[str, Any] = field(default_factory=dict)
    response_text: Any = None
    result: Any = None
    resume_payload: Any = None
    resume_results: Any = None
    run_tool_loop_result: Any = None
    saved_traits: Any = None
    search_costs: Dict[str, Any] = field(default_factory=dict)
    seen: Any = None
    selected: Any = None
    sentence_l: Any = None
    sentences: List[str] = field(default_factory=list)
    shoe_sentence: Any = None
    skip_fact_extraction: bool = False
    skip_llm_generation: bool = False
    slots: Any = None
    small_talk_guard: Any = None
    small_talk_prefix: Any = None
    status_persisted: bool = False
    suggestion_mode: int = 1
    stripped_input: Any = None
    summary_text: Any = None
    system_prompt: Any = None
    system_prompt_for_llm: Any = None
    tags_to_save: Any = None
    target_name: Any = None
    term_lower: Any = None
    term_s: Any = None
    timestamp: Optional[int] = None
    tool_protocol_guidance: Any = None
    tool_results: Any = None
    tool_retry_guidance: Any = None
    tools_override: Any = None
    total_search_cost: Optional[float] = None
    ui_guidance: Any = None
    use_agent_factory: bool = False
    user_prompt_lower: str = ""
    user_selected_model: Any = None
    user_text: str = ""
    user_text_clean: str = ""
    user_text_for_prompt: Any = None
    user_text_lower: str = ""
    v_profile: Any = None
    value_clean: Any = None
    value_lower: Any = None
    verified_block: Any = None
    verified_lines: List[str] = field(default_factory=list)
    verified_terms: Any = None
    vision_data: Optional[Dict[str, Any]] = None
    vision_mode: Any = None
    vision_result: Optional[Dict[str, Any]] = None
    visual_profile_str: Any = None

    def mark_retry_path(self, path: str) -> None:
        """Append a KPI retry-path label if not already present (deduplicated)."""
        normalized = str(path or "").strip()
        if normalized and normalized not in self.kpi_retry_paths:
            self.kpi_retry_paths.append(normalized)
