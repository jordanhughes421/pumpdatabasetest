# Frontend Verification Instructions

To verify the new "Curve Validation + Auto-Fit" features manually:

1.  **Start the Application**:
    *   Run `docker-compose up --build`.
    *   Open `http://localhost:3000`.

2.  **Navigate to Curve Edit Page**:
    *   Create a Pump (if none exists).
    *   Create a Curve Set.
    *   Click on the Curve Set to view details.

3.  **Verify Data Entry Validation**:
    *   In the "Edit Curve Data" text area:
        *   Type garbage (e.g., `abc def`). Verify a "NON_NUMERIC" blocking error appears.
        *   Type negative flow (e.g., `-10 100`). Verify "NEGATIVE_FLOW" error.
        *   Type duplicate flow (e.g., `100 90` and `100 85`). Verify a warning appears (not blocking).
        *   Type valid data (e.g., `0 100`, `100 90`, `200 70`). Verify "valid points found" message appears and errors disappear.

4.  **Verify Saving and Fitting**:
    *   With valid data, click "Save Series".
    *   Verify the chart updates.
    *   Verify the "Existing Series" list shows the new series with "Fit: polynomial_x" (or similar) and R² value.
    *   Toggle "Show Fitted Curves" and "Show Raw Points" checkboxes to ensure they work.

5.  **Verify Duty Point Evaluation**:
    *   In the "Duty Point Evaluation" panel (below the chart):
        *   Enter a Flow value within the range (e.g., `100`). Click Evaluate. Verify Predicted Head is shown.
        *   Enter a Target Head (e.g., `90`). Click Evaluate. Verify Residual and Pass/Fail status.
        *   Enter a Flow value outside the range (e.g., `1000`). Click Evaluate. Verify "Extrapolation detected" warning.

6.  **Verify Other Curve Types**:
    *   Select "Efficiency" or "Power" from dropdown.
    *   Enter data (Efficiency: `0 0`, `100 80`, `200 70`). Note: Efficiency > 100 should warn.
    *   Save and verify they are plotted on secondary axes (Eff right, Power right).
