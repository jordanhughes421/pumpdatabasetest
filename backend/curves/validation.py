from typing import List, Dict, Any, Tuple
from pydantic import BaseModel
from backend.models import SeriesType

class ValidationResult(BaseModel):
    blocking_errors: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]
    normalized_points: List[Dict[str, Any]]

def validate_points(series_type: SeriesType, points: List[Dict[str, Any]]) -> ValidationResult:
    blocking_errors = []
    warnings = []
    normalized_points = []

    # 1. Basic validation and cleaning
    clean_points = []
    for i, pt in enumerate(points):
        flow = pt.get("flow")
        value = pt.get("value")

        # Non-numeric check
        if not isinstance(flow, (int, float)) or not isinstance(value, (int, float)):
             blocking_errors.append({
                 "code": "NON_NUMERIC",
                 "message": f"Point at index {i} has non-numeric values.",
                 "severity": "error",
                 "indices": [i]
             })
             continue

        # Negative flow check
        if flow < 0:
             blocking_errors.append({
                 "code": "NEGATIVE_FLOW",
                 "message": f"Point at index {i} has negative flow.",
                 "severity": "error",
                 "indices": [i]
             })
             continue

        clean_points.append({"flow": float(flow), "value": float(value), "original_index": i})

    if blocking_errors:
        return ValidationResult(blocking_errors=blocking_errors, warnings=warnings, normalized_points=[])

    if len(clean_points) < 2:
        blocking_errors.append({
            "code": "TOO_FEW_POINTS",
            "message": "At least 2 points are required.",
            "severity": "error"
        })
        return ValidationResult(blocking_errors=blocking_errors, warnings=warnings, normalized_points=[])

    # 2. Sorting
    # Sort by flow
    clean_points.sort(key=lambda x: x["flow"])

    # Check if reordering happened (not strictly necessary to warn, but good to know)
    # The prompt says "Sort by Flow increasing for storage/plotting (report if re-ordered)"
    # but "normalized_points" handles the sorted version. Maybe just sorting is enough.

    # 3. Duplicate Flow check and Deduplication
    unique_points = []
    if clean_points:
        current_flow = clean_points[0]["flow"]
        current_group = [clean_points[0]]

        for pt in clean_points[1:]:
            if abs(pt["flow"] - current_flow) < 1e-9: # Float equality check
                current_group.append(pt)
            else:
                # Process group
                if len(current_group) > 1:
                    warnings.append({
                        "code": "DUPLICATE_FLOW",
                        "message": f"Duplicate flow values found at flow={current_flow}. Averaging values.",
                        "severity": "warning",
                        "indices": [p["original_index"] for p in current_group]
                    })
                    # Strategy: Average
                    avg_val = sum(p["value"] for p in current_group) / len(current_group)
                    unique_points.append({"flow": current_flow, "value": avg_val})
                else:
                    unique_points.append({"flow": current_group[0]["flow"], "value": current_group[0]["value"]})

                current_flow = pt["flow"]
                current_group = [pt]

        # Last group
        if len(current_group) > 1:
            warnings.append({
                "code": "DUPLICATE_FLOW",
                "message": f"Duplicate flow values found at flow={current_flow}. Averaging values.",
                "severity": "warning",
                "indices": [p["original_index"] for p in current_group]
            })
            avg_val = sum(p["value"] for p in current_group) / len(current_group)
            unique_points.append({"flow": current_flow, "value": avg_val})
        else:
            unique_points.append({"flow": current_group[0]["flow"], "value": current_group[0]["value"]})

    normalized_points = unique_points

    # 4. Type specific checks
    flows = [p["flow"] for p in normalized_points]
    values = [p["value"] for p in normalized_points]

    if series_type == SeriesType.efficiency:
        # Efficiency > 100
        indices_gt_100 = [i for i, v in enumerate(values) if v > 100]
        if indices_gt_100:
             warnings.append({
                 "code": "EFF_GT_100",
                 "message": "Efficiency values > 100% detected.",
                 "severity": "warning", # Prompt says "warning or error (justify and document)". Defaulting to warning as user might mean >1 or weird units.
                 "indices": indices_gt_100
             })
        # Efficiency < 0
        indices_lt_0 = [i for i, v in enumerate(values) if v < 0]
        if indices_lt_0:
             blocking_errors.append({
                 "code": "EFF_LT_0",
                 "message": "Efficiency values < 0% detected.",
                 "severity": "error",
                 "indices": indices_lt_0
             })

    elif series_type == SeriesType.head:
         # Negative Head
        indices_lt_0 = [i for i, v in enumerate(values) if v < 0]
        if indices_lt_0:
             warnings.append({
                 "code": "NEGATIVE_HEAD",
                 "message": "Negative head values detected.",
                 "severity": "warning",
                 "indices": indices_lt_0
             })

    elif series_type == SeriesType.power:
        # Power strongly decreasing?
        # Simple check: if power drops significantly while flow increases, might be wrong.
        # But power can drop at end of curve for some pumps (overloading vs non-overloading).
        # Let's check for "wild oscillations" or generally decreasing trend if that's what "strongly decreasing" means.
        # "Power strongly decreasing with Flow across most of range -> warning"
        # Let's check correlation? Or just start vs end.
        if len(values) > 2:
            # Check if slope is generally negative
            # Linear regression slope
            import numpy as np
            if len(values) > 0:
                slope, _ = np.polyfit(flows, values, 1)
                if slope < -0.1: # Arbitrary threshold, "strongly decreasing"
                     warnings.append({
                         "code": "POWER_DECREASING",
                         "message": "Power appears to decrease with flow. Check if units are correct.",
                         "severity": "warning"
                     })

    # Missing coverage
    if flows:
        min_q, max_q = min(flows), max(flows)
        if max_q > 0 and (max_q - min_q) / max_q < 0.1: # Covers less than 10% of range from 0 to max? Or just narrow range relative to absolute values?
            # "max/min < 1.1" -> max < 1.1 * min. This implies narrow relative range.
            if min_q > 0 and max_q / min_q < 1.1:
                warnings.append({
                    "code": "NARROW_RANGE",
                    "message": "Data covers a very narrow flow range.",
                    "severity": "warning"
                })

    return ValidationResult(
        blocking_errors=blocking_errors,
        warnings=warnings,
        normalized_points=normalized_points
    )
