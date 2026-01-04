import numpy as np
from scipy.interpolate import UnivariateSpline
from typing import List, Dict, Any, Optional, Tuple
from backend.models import SeriesType

def fit_curve(series_type: SeriesType, points: List[Dict[str, float]]) -> Tuple[str, Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    """
    Fits a curve to the points.
    Returns:
        fit_model_type: str
        fit_params: dict
        fit_quality: dict
        data_range: dict
    """
    if not points or len(points) < 2:
        return None, None, None, None

    flows = np.array([p["flow"] for p in points])
    values = np.array([p["value"] for p in points])

    min_q = float(np.min(flows))
    max_q = float(np.max(flows))
    data_range = {"min_q": min_q, "max_q": max_q}

    fit_model_type = "unknown"
    fit_params = {}
    fit_quality = {}

    if series_type == SeriesType.head:
        # Polynomial regression degree 2
        # Use numpy.polyfit
        # H = a*Q^2 + b*Q + c
        try:
            coeffs = np.polyfit(flows, values, 2)
            # coeffs is [a, b, c] for a*x^2 + b*x + c
            fit_model_type = "polynomial_2"
            fit_params = {
                "coeffs": coeffs.tolist() # [a, b, c]
            }

            # Calculate R^2 or RMSE
            p = np.poly1d(coeffs)
            y_pred = p(flows)
            residuals = values - y_pred
            rmse = float(np.sqrt(np.mean(residuals**2)))
            ss_res = np.sum(residuals**2)
            ss_tot = np.sum((values - np.mean(values))**2)
            r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

            fit_quality = {
                "rmse": rmse,
                "r2": float(r2)
            }
        except Exception as e:
            fit_model_type = "failed"
            fit_quality = {"error": str(e)}

    elif series_type == SeriesType.efficiency or series_type == SeriesType.power:
        # Univariate Spline with smoothing
        # "smooth curve with a single peak preference" for eff
        # "monotonic-ish smoothing" for power

        # We can use UnivariateSpline. It allows setting a smoothing factor s.
        # If we don't provide s, it uses len(w).
        # Let's try a default smoothing strategy.
        try:
            # Sort just in case (though validation ensures sorted)
            # UnivariateSpline requires strictly increasing x
            # Deduplication should have handled equal x.

            # To store spline, we need knots (t), coeffs (c), degree (k)
            # UnivariateSpline defaults to k=3

            # Simple heuristic for s: len(points) if noisy?
            # Let's try s=None (default) first, which might be interpolating if no weights.
            # We want smoothing. s controls the smoothness.
            # s = number of points?

            spl = UnivariateSpline(flows, values, k=3, s=len(flows)) # Just a guess for s

            # If s is too large, it might be too smooth (flat). If too small, too wiggly.
            # Let's try to find a good s? Or just use a fixed small s or leave it to scipy defaults which usually interpolate.
            # Requirement: "Auto-fit a smooth curve".
            # For efficiency, we expect a hump.
            # For power, we expect monotonic increase usually.

            # For robustness, let's use a lower order polynomial (3 or 4) for Efficiency/Power if points are few,
            # or Spline if many.
            # Actually, the prompt says "recommended fits... Efficiency: smooth curve... Power: monotonic-ish".

            # Let's stick to polynomial degree 3 for efficiency and power for simplicity and robustness against wild oscillations of splines.
            # Unless the user really wants splines.
            # "Head vs Flow: polynomial regression... Efficiency... smooth curve... Power... monotonic-ish"

            # Let's try Polynomial degree 3 for all others for now as a baseline robust fit.
            # It handles single peak (efficiency) and monotonic (power) reasonably well for pump curves.

            coeffs = np.polyfit(flows, values, 3)
            fit_model_type = "polynomial_3"
            fit_params = {
                "coeffs": coeffs.tolist()
            }
             # Calculate R^2 or RMSE
            p = np.poly1d(coeffs)
            y_pred = p(flows)
            residuals = values - y_pred
            rmse = float(np.sqrt(np.mean(residuals**2)))
            ss_res = np.sum(residuals**2)
            ss_tot = np.sum((values - np.mean(values))**2)
            r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

            fit_quality = {
                "rmse": rmse,
                "r2": float(r2)
            }

        except Exception as e:
            fit_model_type = "failed"
            fit_quality = {"error": str(e)}

    return fit_model_type, fit_params, fit_quality, data_range
