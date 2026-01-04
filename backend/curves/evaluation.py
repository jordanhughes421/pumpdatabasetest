from typing import Dict, Any, Optional, List
import numpy as np
from backend.models import SeriesType

def evaluate_curve_at_point(
    fit_model_type: str,
    fit_params: Dict[str, Any],
    data_range: Dict[str, Any],
    flow: float,
    points: List[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Evaluates the curve at a given flow.
    """
    prediction = None
    warnings = []

    # Check extrapolation
    min_q = data_range.get("min_q", 0)
    max_q = data_range.get("max_q", 0)
    is_extrapolation = False

    if flow < min_q or flow > max_q:
        is_extrapolation = True
        warnings.append(f"Flow {flow} is outside data range [{min_q}, {max_q}]. Prediction is extrapolated.")

    if fit_model_type and fit_params:
        if fit_model_type.startswith("polynomial"):
            coeffs = fit_params.get("coeffs")
            if coeffs:
                p = np.poly1d(coeffs)
                prediction = float(p(flow))
        # Add other model types here if implemented

    # Fallback to linear interpolation if no fit or fit failed, provided we have raw points
    if prediction is None and points:
        # Sort points by flow just in case
        sorted_points = sorted(points, key=lambda x: x["flow"])
        qs = [p["flow"] for p in sorted_points]
        vs = [p["value"] for p in sorted_points]
        prediction = float(np.interp(flow, qs, vs)) # np.interp handles linear interpolation
        # Note: np.interp returns the boundary value for extrapolation (flat),
        # so it won't extrapolate linearly beyond the range.
        # If we really want linear extrapolation, we need a different function.
        # But for "fallback", flat or simple interp is okay.
        # If fit exists, we used that for extrapolation (polynomials extrapolate).
        # If no fit, maybe we shouldn't extrapolate?
        if is_extrapolation and prediction is None:
             # If np.interp clamped it, warn?
             pass

    return {
        "predicted_value": prediction,
        "is_extrapolation": is_extrapolation,
        "warnings": warnings
    }
