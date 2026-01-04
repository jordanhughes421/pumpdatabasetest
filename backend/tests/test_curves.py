import pytest
from backend.curves.validation import validate_points
from backend.curves.fitting import fit_curve
from backend.curves.evaluation import evaluate_curve_at_point
from backend.models import SeriesType

def test_validation_non_numeric():
    points = [{"flow": "a", "value": 10}]
    res = validate_points(SeriesType.head, points)
    assert len(res.blocking_errors) > 0
    assert res.blocking_errors[0]["code"] == "NON_NUMERIC"

def test_validation_too_few_points():
    points = [{"flow": 10, "value": 10}]
    res = validate_points(SeriesType.head, points)
    assert len(res.blocking_errors) > 0
    assert res.blocking_errors[0]["code"] == "TOO_FEW_POINTS"

def test_validation_negative_flow():
    points = [{"flow": -10, "value": 10}, {"flow": 10, "value": 10}]
    res = validate_points(SeriesType.head, points)
    assert len(res.blocking_errors) > 0
    assert res.blocking_errors[0]["code"] == "NEGATIVE_FLOW"

def test_validation_duplicates_and_sorting():
    points = [
        {"flow": 20, "value": 20},
        {"flow": 10, "value": 10},
        {"flow": 10, "value": 12}
    ]
    res = validate_points(SeriesType.head, points)
    assert not res.blocking_errors
    assert len(res.normalized_points) == 2
    assert res.normalized_points[0]["flow"] == 10
    assert res.normalized_points[0]["value"] == 11 # Average
    assert len(res.warnings) > 0
    assert res.warnings[0]["code"] == "DUPLICATE_FLOW"

def test_validation_efficiency():
    points = [
        {"flow": 10, "value": 110},
        {"flow": 20, "value": 80}
    ]
    res = validate_points(SeriesType.efficiency, points)
    assert len(res.warnings) > 0
    assert res.warnings[0]["code"] == "EFF_GT_100"

def test_fitting_head_polynomial():
    # y = x^2
    points = [
        {"flow": 0, "value": 0},
        {"flow": 1, "value": 1},
        {"flow": 2, "value": 4},
        {"flow": 3, "value": 9}
    ]
    type, params, qual, range = fit_curve(SeriesType.head, points)
    assert type == "polynomial_2"
    assert "coeffs" in params
    # x^2 coeffs should be close to [1, 0, 0]
    coeffs = params["coeffs"]
    assert abs(coeffs[0] - 1.0) < 1e-5
    assert qual["r2"] > 0.99

def test_evaluation():
    points = [
        {"flow": 0, "value": 0},
        {"flow": 2, "value": 4}
    ]
    # Linear interpolation check
    res = evaluate_curve_at_point(None, None, {"min_q": 0, "max_q": 2}, 1.0, points)
    assert res["predicted_value"] == 2.0
    assert not res["is_extrapolation"]

    # Extrapolation check
    res = evaluate_curve_at_point(None, None, {"min_q": 0, "max_q": 2}, 3.0, points)
    assert res["is_extrapolation"]
    assert len(res["warnings"]) > 0

    # Polynomial evaluation
    params = {"coeffs": [1, 0, 0]} # x^2
    res = evaluate_curve_at_point("polynomial_2", params, {"min_q": 0, "max_q": 10}, 3.0, points)
    assert abs(res["predicted_value"] - 9.0) < 1e-5
