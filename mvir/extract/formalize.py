"""Formalization entrypoints for Phase 3 extraction.

Preprocess is lossless + offsets only; no semantic classification.
Phase 3 uses an LLM to produce MVIR semantics.
Providers must not modify MVIR schema.
"""

from __future__ import annotations

import json
import traceback
from copy import deepcopy
from pathlib import Path

from pydantic import ValidationError

from mvir.core.ast_normalize import normalize_expr_dict_relaxed
from mvir.core.models import MVIR, Warning
from mvir.extract.cache import ResponseCache
from mvir.extract.ast_repair import repair_expr
from mvir.extract.context import build_prompt_context
from mvir.extract.contract import validate_grounding_contract
from mvir.extract.normalize import normalize_llm_payload
from mvir.extract.prompts import build_mvir_prompt
from mvir.extract.provider_base import LLMProvider, Provider, ProviderError, ProviderResult
from mvir.extract.report import classify_exception
from mvir.extract.sanitize import sanitize_mvir_payload
from mvir.preprocess.context import build_preprocess_output
from mvir.repair.ast_sanitize import sanitize_expr_dict


def formalize(prompt_context: dict, provider: Provider) -> ProviderResult:
    """Formalize prompt context into MVIR using a provider."""

    raise NotImplementedError("Formalization not implemented.")


def try_repair_json_output(raw: str) -> str | None:
    """Try deterministic minimal repair of nearly-JSON LLM output."""

    repaired = raw.strip()

    if "```" in repaired:
        first = repaired.find("```")
        second = repaired.find("```", first + 3)
        if first != -1 and second != -1 and second > first:
            repaired = repaired[first + 3 : second].strip()

    first_brace = repaired.find("{")
    if first_brace != -1 and first_brace > 0:
        repaired = repaired[first_brace:]

    last_brace = repaired.rfind("}")
    if last_brace != -1 and last_brace < len(repaired) - 1:
        repaired = repaired[: last_brace + 1]

    if repaired.startswith("{") and repaired.endswith("}"):
        return repaired
    return None


def _build_validation_repair_prompt(
    *,
    problem_id: str,
    validation_error: ValidationError,
    previous_output: str,
) -> str:
    summary_lines = str(validation_error).splitlines()[:15]
    summary = "\n".join(summary_lines)
    return (
        "You output JSON but it failed MVIR validation.\n"
        "Fix the JSON to conform EXACTLY to MVIR v0.1.\n"
        "Do not change trace spans; keep trace identical.\n"
        "Do NOT change trace spans or span_ids; keep them identical.\n"
        "All trace references must be existing span_ids.\n\n"
        "Assumption.kind in {\"given\",\"derived\",\"wlog\"}\n"
        "Goal.kind in {\"prove\",\"find\",\"compute\",\"maximize\",\"minimize\",\"exists\",\"counterexample\"}\n"
        "Concept.role in {\"domain\",\"pattern\",\"candidate_tool\",\"definition\",\"representation_hint\"}\n\n"
        "Allowed values:\n"
        'Assumption.kind MUST be exactly one of: ["given","derived","wlog"]\n'
        'Goal.kind MUST be exactly one of: ["prove","find","compute","maximize","minimize","exists","counterexample"]\n'
        'Concept.role MUST be exactly one of: ["domain","pattern","candidate_tool","definition","representation_hint"]\n'
        'Entity.kind MUST be exactly one of: ["variable","constant","function","set","sequence","point","vector","object"]\n\n'
        "Exact AST rules:\n"
        'Symbol must be {"node":"Symbol","id":"x"} not name\n'
        "Gt/Ge/etc must use lhs/rhs (args only allowed in input but output must be lhs/rhs)\n"
        "Pow must be base/exp\n"
        "No extra null fields like id:null/value:null everywhere\n"
        "DO NOT output placeholder partial nodes like lhs:{\"node\":\"Symbol\"} (missing id) or rhs:{\"node\":\"Number\"} (missing value).\n"
        "Never output placeholder Expr nodes. If node==\"Sum\", you MUST provide var, from, to, body.\n"
        "Never include unrelated keys filled with null to satisfy schemas. Do not emit id/value/lhs/rhs/etc unless the node type requires it.\n"
        "AST node checklist (required fields):\n"
        "- Symbol: id\n"
        "- Number: value\n"
        "- Add/Mul: args (>=1)\n"
        "- Div: num, den\n"
        "- Pow: base, exp\n"
        "- Eq/Neq/Lt/Le/Gt/Ge/Divides: lhs, rhs\n"
        "- Sum: var, from, to, body\n"
        "- Call: fn, args\n"
        "If an assumption expression cannot be constructed with all required fields of its AST node, DO NOT insert placeholder null fields.\n"
        "Instead: remove that assumption and add warning:\n"
        "{\n"
        "  \"code\": \"invalid_assumption_expr_dropped\",\n"
        "  \"message\": \"...\",\n"
        "  \"trace\": [...],\n"
        "  \"details\": {\"reason\": \"...\", \"raw_expr\": {...}}\n"
        "}\n"
        "If a goal subexpression cannot be reconstructed safely, remove/replace that subexpression and add warning code=\"invalid_goal_expr_replaced\".\n"
        "If goal kind cannot stay valid, downgrade goal kind in degraded mode and add warning code=\"goal_kind_downgraded\".\n"
        "FORBIDDEN: id:null, value:null, args:null, lhs:null, rhs:null, base:null, exp:null, num:null, den:null, from:null, to:null, body:null.\n"
        "If a secondary task expression cannot be represented correctly with available AST nodes, DO NOT put it in assumptions.\n"
        "Instead: omit that assumption and add a warning with code=\"unparsed_math\" and trace=[span_id].\n"
        "Keep goal as primary; secondary tasks go into warning only.\n"
        "AST examples:\n"
        "Sum example: {\"node\":\"Sum\",\"var\":\"k\",\"from\":{\"node\":\"Number\",\"value\":1},\"to\":{\"node\":\"Symbol\",\"id\":\"n\"},\"body\":{\"node\":\"Symbol\",\"id\":\"k\"}}\n"
        "Div example: {\"node\":\"Div\",\"num\":{\"node\":\"Symbol\",\"id\":\"a\"},\"den\":{\"node\":\"Number\",\"value\":2}}\n"
        "Symbol example: {\"node\":\"Symbol\",\"id\":\"x\"} (never {\"node\":\"Symbol\",\"name\":\"x\"})\n"
        "Do not add fields not in the previous JSON unless required by schema.\n"
        "Required fields:\n"
        "Entity requires: id, kind, type\n"
        "Assumption requires: expr, kind\n"
        "Goal requires: kind, expr\n"
        "If goal.kind is \"find\", goal.target is required.\n"
        "If goal.target cannot be constructed safely, do NOT keep kind=\"find\".\n"
        "Downgrade to nearest valid kind among compute/prove/exists and add warning:\n"
        "{\n"
        "  \"code\": \"goal_kind_downgraded\",\n"
        "  \"message\": \"...\",\n"
        "  \"trace\": [...],\n"
        "  \"details\": {\"old_kind\": \"find\", \"reason\": \"...\"}\n"
        "}\n"
        "Concept requires: id, role\n"
        "Warning requires: code, message\n"
        "MVIR.trace must be non-empty\n"
        f"Problem ID: {problem_id}\n\n"
        "Validation errors (first lines):\n"
        f"{summary}\n\n"
        "Previous JSON output:\n"
        f"{previous_output}\n\n"
        "Return corrected JSON only."
    )


def formalize_text_to_mvir(
    text: str,
    provider: LLMProvider,
    *,
    problem_id: str = "unknown",
    temperature: float = 0.0,
    max_tokens: int = 2000,
    cache: ResponseCache | None = None,
    use_cache: bool = True,
    strict: bool = True,
    normalize: bool = False,
    repair: bool = True,
    debug_dir: str | None = None,
    degrade_on_validation_failure: bool = False,
    deterministic: bool = False,
) -> MVIR:
    """Run preprocess + prompt + provider completion and return MVIR."""

    preprocess_result = build_preprocess_output(text).to_dict()
    prompt_context = build_prompt_context(preprocess_result)
    prompt = build_mvir_prompt(prompt_context, problem_id=problem_id)
    provider_name = getattr(provider, "name", provider.__class__.__name__)
    model_name = getattr(provider, "model", None)
    debug_settings = {
        "provider": str(provider_name),
        "model": str(model_name) if model_name is not None else None,
        "schema_mode": getattr(provider, "format_mode", None),
        "fallback_mode": bool(getattr(provider, "allow_fallback", False)),
        "deterministic": deterministic,
        "temperature": temperature,
        "top_p": getattr(provider, "top_p", None),
    }

    response: str | None = None
    try:
        cache_key: str | None = None
        if cache is not None:
            cache_key = cache.make_key(
                provider_name=str(provider_name),
                model_name=str(model_name) if model_name is not None else None,
                temperature=temperature,
                max_tokens=max_tokens,
                prompt=prompt,
            )
            if use_cache:
                response = cache.get(cache_key)

        if response is None:
            try:
                response = provider.complete(
                    prompt, temperature=temperature, max_tokens=max_tokens
                )
            except Exception as exc:
                if isinstance(exc, ProviderError):
                    raise
                raise ValueError(f"Provider call failed: {exc}") from exc
            if cache is not None and cache_key is not None:
                cache.set(cache_key, response)

        try:
            payload = json.loads(response)
        except json.JSONDecodeError as exc:
            payload = None
            if repair:
                repaired = try_repair_json_output(response)
                if repaired is not None:
                    try:
                        payload = json.loads(repaired)
                    except json.JSONDecodeError:
                        payload = None
            if payload is None:
                head = response[:200]
                tail = response[-200:] if len(response) > 200 else response
                raise ValueError(
                    f"JSON parse failed: {exc}. head={head!r} tail={tail!r}"
                ) from exc

        if normalize or not strict:
            if isinstance(payload, dict):
                payload = normalize_llm_payload(payload)
        if isinstance(payload, dict):
            payload = sanitize_mvir_payload(payload)
            payload = _normalize_payload_expr_fields(
                payload,
                degrade_on_invalid_goal_expr=degrade_on_validation_failure,
            )

        try:
            mvir = MVIR.model_validate(payload)
        except ValidationError as exc:
            first_error = ValueError(f"MVIR validation failed: {exc}")
            _write_debug_bundle(
                debug_dir=debug_dir,
                problem_id=problem_id,
                source_text=text,
                preprocess_result=preprocess_result,
                prompt=prompt,
                raw_output=response,
                provider=provider,
                exc=first_error,
                settings=debug_settings,
            )

            if str(provider_name) == "openai":
                repair_prompt = _build_validation_repair_prompt(
                    problem_id=problem_id,
                    validation_error=exc,
                    previous_output=response,
                )
                try:
                    response = provider.complete(
                        repair_prompt, temperature=temperature, max_tokens=max_tokens
                    )
                except Exception as retry_exc:
                    if isinstance(retry_exc, ProviderError):
                        raise
                    raise ValueError(
                        f"Provider repair call failed: {retry_exc}"
                    ) from retry_exc

                try:
                    payload = json.loads(response)
                except json.JSONDecodeError as json_exc:
                    repaired = try_repair_json_output(response) if repair else None
                    if repaired is not None:
                        try:
                            payload = json.loads(repaired)
                        except json.JSONDecodeError:
                            payload = None
                    else:
                        payload = None
                    if payload is None:
                        raise ValueError(
                            f"JSON parse failed after repair retry: {json_exc}"
                        ) from json_exc

                if (normalize or not strict) and isinstance(payload, dict):
                    payload = normalize_llm_payload(payload)
                if isinstance(payload, dict):
                    payload = sanitize_mvir_payload(payload)
                    payload = _normalize_payload_expr_fields(
                        payload,
                        degrade_on_invalid_goal_expr=degrade_on_validation_failure,
                    )

                try:
                    mvir = MVIR.model_validate(payload)
                except ValidationError as retry_validation_exc:
                    if degrade_on_validation_failure and isinstance(payload, dict):
                        mvir = _recover_minimal_valid_mvir(
                            payload=payload,
                            problem_id=problem_id,
                            source_text=text,
                            reason=f"post_retry_validation_error: {retry_validation_exc}",
                        )
                    else:
                        raise ValueError(
                            f"MVIR validation failed after repair retry: {retry_validation_exc}"
                        ) from retry_validation_exc
            elif degrade_on_validation_failure and isinstance(payload, dict):
                mvir = _recover_minimal_valid_mvir(
                    payload=payload,
                    problem_id=problem_id,
                    source_text=text,
                    reason=f"validation_error: {exc}",
                )
            else:
                raise first_error from exc

        errors = validate_grounding_contract(mvir)
        if strict and errors:
            if degrade_on_validation_failure:
                mvir.warnings.append(
                    Warning(
                        code="grounding_contract_degraded",
                        message=(
                            "Grounding contract failed; retained degraded-but-valid MVIR."
                        ),
                        trace=["s0"],
                        details={"errors": errors},
                    )
                )
            else:
                raise ValueError("Grounding contract failed: " + "; ".join(errors))

        return mvir
    except Exception as exc:
        _write_debug_bundle(
            debug_dir=debug_dir,
            problem_id=problem_id,
            source_text=text,
            preprocess_result=preprocess_result,
            prompt=prompt,
            raw_output=response,
            provider=provider,
            exc=exc,
            settings=debug_settings,
        )
        raise


def _normalize_payload_expr_fields(
    payload: dict,
    *,
    degrade_on_invalid_goal_expr: bool = False,
) -> dict:
    """Normalize assumptions/goal expression dicts before MVIR validation."""

    span_texts = _span_text_map(payload)
    entities = payload.get("entities")
    if not isinstance(entities, list):
        entities = []

    warnings = payload.get("warnings")
    if not isinstance(warnings, list):
        warnings = []
        payload["warnings"] = warnings

    assumptions = payload.get("assumptions")
    if isinstance(assumptions, list):
        kept_assumptions: list[dict] = []
        for item in assumptions:
            if not isinstance(item, dict):
                continue
            expr = item.get("expr")
            if not isinstance(expr, dict):
                warnings.append(
                    {
                        "code": "invalid_assumption_expr_dropped",
                        "message": "dropped invalid expr subtree: non-object expression",
                        "trace": _trace_ids(item),
                        "details": {
                            "reason": "non_object_expr",
                            "raw_expr": deepcopy(expr),
                        },
                    }
                )
                continue
            raw_expr = deepcopy(expr)
            expr = normalize_expr_dict_relaxed(expr)
            if not isinstance(expr, dict):
                warnings.append(
                    {
                        "code": "invalid_assumption_expr_dropped",
                        "message": "dropped invalid expr subtree: normalization missing required fields",
                        "trace": _trace_ids(item),
                        "details": {
                            "reason": "normalize_missing_required_fields",
                            "raw_expr": raw_expr,
                        },
                    }
                )
                continue
            expr = repair_expr(
                expr,
                span_text=_first_trace_text(item, span_texts),
                entities=entities,
            )
            expr = sanitize_expr_dict(expr)
            if expr is None:
                warnings.append(
                    {
                        "code": "invalid_assumption_expr_dropped",
                        "message": "dropped invalid expr subtree: expression missing required AST fields",
                        "trace": _trace_ids(item),
                        "details": {
                            "reason": "incomplete_expr",
                            "raw_expr": raw_expr,
                        },
                    }
                )
                continue
            item["expr"] = expr
            kept_assumptions.append(item)
        payload["assumptions"] = kept_assumptions

    goal = payload.get("goal")
    if isinstance(goal, dict):
        raw_goal_expr = deepcopy(goal.get("expr"))
    else:
        raw_goal_expr = None

    if isinstance(goal, dict) and isinstance(goal.get("expr"), dict):
        normalized_expr = normalize_expr_dict_relaxed(goal["expr"])
        if isinstance(normalized_expr, dict):
            normalized_expr = repair_expr(
                normalized_expr,
                span_text=_first_trace_text(goal, span_texts),
                entities=entities,
            )
            sanitized_expr = sanitize_expr_dict(normalized_expr)
        else:
            sanitized_expr = None
        if sanitized_expr is not None:
            goal["expr"] = sanitized_expr
        else:
            _replace_invalid_goal_expr(payload, goal, raw_goal_expr)
    elif isinstance(goal, dict):
        _replace_invalid_goal_expr(payload, goal, raw_goal_expr)
    if isinstance(goal, dict) and isinstance(goal.get("target"), dict):
        raw_target = deepcopy(goal.get("target"))
        normalized_target = normalize_expr_dict_relaxed(goal["target"])
        sanitized_target = (
            sanitize_expr_dict(normalized_target)
            if isinstance(normalized_target, dict)
            else None
        )
        if sanitized_target is not None:
            goal["target"] = sanitized_target
        else:
            goal.pop("target", None)
            warnings.append(
                {
                    "code": "invalid_goal_target_expr_dropped",
                    "message": "dropped invalid expr subtree: goal.target missing required AST fields",
                    "trace": _trace_ids(goal),
                    "details": {
                        "reason": "goal_target_incomplete_expr",
                        "raw_expr": raw_target,
                    },
                }
            )

    _repair_find_goal_without_target(payload)

    return payload


def _replace_invalid_goal_expr(payload: dict, goal: dict, raw_goal_expr) -> None:
    warnings = payload.get("warnings")
    if not isinstance(warnings, list):
        warnings = []
        payload["warnings"] = warnings
    goal["kind"] = "prove"
    goal["expr"] = {"node": "Bool", "value": True}
    warnings.append(
        {
            "code": "invalid_goal_expr_replaced",
            "message": "dropped invalid expr subtree: goal.expr replaced with safe fallback Bool(true)",
            "trace": _trace_ids(goal),
            "details": {
                "reason": "goal_expr_not_parseable",
                "raw_expr": deepcopy(raw_goal_expr),
            },
        }
    )


def _recover_minimal_valid_mvir(
    *,
    payload: dict,
    problem_id: str,
    source_text: str,
    reason: str,
) -> MVIR:
    _ = payload
    full_len = len(source_text)
    fallback = {
        "meta": {
            "version": "0.1",
            "id": problem_id,
            "generator": "degraded-recovery",
        },
        "source": {"text": source_text},
        "entities": [],
        "assumptions": [],
        "goal": {
            "kind": "prove",
            "expr": {"node": "Bool", "value": True},
            "trace": ["s0"],
        },
        "concepts": [],
        "warnings": [
            {
                "code": "invalid_mvir_recovered",
                "message": "Recovered to minimal valid MVIR after validation failure.",
                "trace": ["s0"],
                "details": {"reason": reason},
            }
        ],
        "trace": [
            {"span_id": "s0", "start": 0, "end": full_len, "text": source_text},
            {"span_id": "s1", "start": 0, "end": full_len, "text": source_text},
        ],
    }

    return MVIR.model_validate(fallback)


def _repair_find_goal_without_target(payload: dict) -> None:
    goal = payload.get("goal")
    if not isinstance(goal, dict):
        return
    kind = goal.get("kind")
    if kind != "find":
        return
    target = goal.get("target")
    if isinstance(target, dict):
        return

    warnings = payload.get("warnings")
    if not isinstance(warnings, list):
        warnings = []
        payload["warnings"] = warnings

    downgraded = _choose_downgraded_goal_kind(payload, goal)
    goal["kind"] = downgraded
    goal.pop("target", None)
    warnings.append(
        {
            "code": "goal_kind_downgraded",
            "message": (
                "Downgraded goal kind from find because goal.target could not be extracted safely."
            ),
            "trace": _trace_ids(goal),
            "details": {
                "old_kind": "find",
                "new_kind": downgraded,
                "reason": "missing_or_invalid_target",
            },
        }
    )


def _choose_downgraded_goal_kind(payload: dict, goal: dict) -> str:
    source_text = ""
    source = payload.get("source")
    if isinstance(source, dict):
        text = source.get("text")
        if isinstance(text, str):
            source_text = text.lower()

    goal_text = ""
    span_map = _span_text_map(payload)
    trace = goal.get("trace")
    if isinstance(trace, list):
        parts: list[str] = []
        for item in trace:
            if isinstance(item, str):
                parts.append(span_map.get(item, ""))
        goal_text = " ".join(parts).lower()

    text = f"{goal_text} {source_text}".strip()
    if any(token in text for token in ("show that", "prove", "verify", "demonstrate")):
        return "prove"
    if any(token in text for token in ("there exists", "exists", "is there")):
        return "exists"
    return "compute"


def _span_text_map(payload: dict) -> dict[str, str]:
    out: dict[str, str] = {}
    trace = payload.get("trace")
    if not isinstance(trace, list):
        return out
    for span in trace:
        if not isinstance(span, dict):
            continue
        span_id = span.get("span_id")
        text = span.get("text")
        if isinstance(span_id, str) and span_id:
            out[span_id] = text if isinstance(text, str) else ""
    return out


def _first_trace_text(node: dict, span_texts: dict[str, str]) -> str:
    trace = node.get("trace")
    if not isinstance(trace, list) or not trace:
        return ""
    first = trace[0]
    if not isinstance(first, str):
        return ""
    return span_texts.get(first, "")


def _trace_ids(node: dict) -> list[str]:
    trace = node.get("trace")
    if not isinstance(trace, list):
        return []
    return [item for item in trace if isinstance(item, str)]


def _write_debug_bundle(
    *,
    debug_dir: str | None,
    problem_id: str,
    source_text: str,
    preprocess_result: dict,
    prompt: str,
    raw_output: str | None,
    provider: LLMProvider,
    exc: Exception,
    settings: dict | None = None,
) -> None:
    """Best-effort debug bundle writer; never raises."""

    if not debug_dir:
        return
    try:
        base = Path(debug_dir) / problem_id
        base.mkdir(parents=True, exist_ok=True)
        (base / "source.txt").write_text(source_text, encoding="utf-8")
        (base / "preprocess.json").write_text(
            json.dumps(preprocess_result, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        (base / "prompt.txt").write_text(prompt, encoding="utf-8")
        if raw_output is not None:
            (base / "raw_output.txt").write_text(raw_output, encoding="utf-8")
        request_json = getattr(provider, "last_request_json", None)
        if request_json is not None:
            (base / "request.json").write_text(
                json.dumps(request_json, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        response_json = getattr(provider, "last_response_json", None)
        if response_json is not None:
            (base / "response.json").write_text(
                json.dumps(response_json, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        if settings is not None:
            (base / "settings.json").write_text(
                json.dumps(settings, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        kind, message = classify_exception(exc)
        error_text = "\n".join(
            [
                f"kind: {kind.value}",
                f"message: {message}",
                f"exception: {exc!r}",
                "",
                "traceback:",
                traceback.format_exc(),
            ]
        )
        (base / "error.txt").write_text(error_text, encoding="utf-8")
    except Exception:
        return
