"""Post-validation enrichment for MVIR math surface spans."""

from __future__ import annotations

from copy import deepcopy

from mvir.latex.surface import parse_surface


def _default_warning_trace(mvir: dict) -> list[str]:
    trace = mvir.get("trace")
    if isinstance(trace, list) and trace:
        first = trace[0]
        if isinstance(first, dict):
            span_id = first.get("span_id")
            if isinstance(span_id, str) and span_id:
                return [span_id]
    return []


def _append_warning(mvir: dict, *, code: str, message: str, details: dict | None = None) -> None:
    warnings = mvir.get("warnings")
    if not isinstance(warnings, list):
        warnings = []
        mvir["warnings"] = warnings
    warning = {
        "code": code,
        "message": message,
        "trace": _default_warning_trace(mvir),
    }
    if details is not None:
        warning["details"] = details
    warnings.append(warning)


def enrich_mvir_with_math_surface(mvir: dict, prompt_context: dict) -> dict:
    """Attach source.math_surface entries derived from prompt_context math candidates."""

    out = deepcopy(mvir)
    try:
        source = out.get("source")
        if not isinstance(source, dict):
            raise ValueError("mvir.source must be an object")

        math_candidates = prompt_context.get("math_candidates", [])
        if not isinstance(math_candidates, list):
            math_candidates = []

        parsed_spans: list[dict] = []
        for idx, span in enumerate(math_candidates):
            if not isinstance(span, dict):
                continue
            span_id = span.get("span_id")
            start = span.get("start")
            end = span.get("end")
            text = span.get("text")
            if not isinstance(span_id, str) or not isinstance(start, int) or not isinstance(end, int):
                continue
            if not isinstance(text, str):
                text = ""

            result = parse_surface(text)
            parsed_spans.append(
                {
                    "span_id": span_id,
                    "start": start,
                    "end": end,
                    "raw_latex": result.raw_latex,
                    "tokens": sorted(result.tokens),
                    "sexpr": result.sexpr,
                    "status": result.status,
                    "warnings": list(result.warnings),
                    "_idx": idx,
                }
            )

        parsed_spans = sorted(parsed_spans, key=lambda item: (item["span_id"], item["_idx"]))
        for item in parsed_spans:
            item.pop("_idx", None)
        source["math_surface"] = parsed_spans
    except Exception as exc:  # noqa: BLE001 - enrichment must never break output flow
        _append_warning(
            out,
            code="math_surface_enrichment_failed",
            message="Failed to enrich source.math_surface; kept MVIR without enrichment.",
            details={"reason": str(exc)},
        )
    return out

