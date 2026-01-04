import sqlite3
import os

def migrate():
    # Paths compatible with both local dev (if running from backend dir) and Docker mount
    # In Docker, we are in /app, so backend/ is where files are.
    # But wait, local run is typically from root.
    # Docker mount is /app/backend.

    # Let's verify where we are.
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # Assuming this script is in backend/ folder.
    old_db = os.path.join(base_dir, "pump_curves.db")
    new_db = os.path.join(base_dir, "pump_curves_v2.db")

    # If using environment variable override
    if "SQLITE_DB_PATH" in os.environ:
         new_db = os.environ["SQLITE_DB_PATH"]

    print(f"Old DB Path: {old_db}")
    print(f"New DB Path: {new_db}")

    if not os.path.exists(old_db):
        print(f"No existing database {old_db} found. Skipping migration.")
        return

    if not os.path.exists(new_db):
        print(f"Target database {new_db} does not exist. Please run the app once to initialize schema.")
        return

    print(f"Migrating data from {old_db} to {new_db}...")

    conn_old = sqlite3.connect(old_db)
    conn_new = sqlite3.connect(new_db)

    conn_old.row_factory = sqlite3.Row

    try:
        cur_new = conn_new.cursor()

        # Get default org id
        cur_new.execute("SELECT id FROM organization LIMIT 1")
        row = cur_new.fetchone()
        if not row:
            print("No organization found in new DB. Skipping.")
            return
        default_org_id = row[0]

        # Migrate Pumps
        pumps = conn_old.execute("SELECT * FROM pump").fetchall()
        for pump in pumps:
            # Check if pump already exists
            exists = cur_new.execute("SELECT 1 FROM pump WHERE id = ?", (pump["id"],)).fetchone()
            if not exists:
                cur_new.execute(
                    "INSERT INTO pump (id, manufacturer, model, meta_data, created_at, updated_at, org_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (pump["id"], pump["manufacturer"], pump["model"], pump["meta_data"], pump["created_at"], pump["updated_at"], default_org_id)
                )

        # Migrate CurveSets
        # Assuming table name is curveset (SQLModel default)
        sets = conn_old.execute("SELECT * FROM curveset").fetchall()
        for s in sets:
             exists = cur_new.execute("SELECT 1 FROM curveset WHERE id = ?", (s["id"],)).fetchone()
             if not exists:
                 cur_new.execute(
                     "INSERT INTO curveset (id, name, pump_id, units, meta_data, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                     (s["id"], s["name"], s["pump_id"], s["units"], s["meta_data"], s["created_at"], s["updated_at"])
                 )

        # Migrate CurveSeries
        series = conn_old.execute("SELECT * FROM curveseries").fetchall()
        for s in series:
             exists = cur_new.execute("SELECT 1 FROM curveseries WHERE id = ?", (s["id"],)).fetchone()
             if not exists:
                 # Check if new columns exist in old db (they don't)
                 # New schema has fit/validation columns. We insert defaults (NULL/Empty)
                 cur_new.execute(
                     """INSERT INTO curveseries
                     (id, curve_set_id, type, validation_warnings, fit_model_type, fit_params, fit_quality, data_range)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                     (s["id"], s["curve_set_id"], s["type"], "[]", None, None, None, None)
                 )

        # Migrate CurvePoint
        points = conn_old.execute("SELECT * FROM curvepoint").fetchall()
        for p in points:
             exists = cur_new.execute("SELECT 1 FROM curvepoint WHERE id = ?", (p["id"],)).fetchone()
             if not exists:
                 cur_new.execute(
                     "INSERT INTO curvepoint (id, series_id, flow, value, sequence) VALUES (?, ?, ?, ?, ?)",
                     (p["id"], p["series_id"], p["flow"], p["value"], p["sequence"])
                 )

        conn_new.commit()
        print("Migration complete.")

    except Exception as e:
        print(f"Migration failed: {e}")
        conn_new.rollback()
    finally:
        conn_old.close()
        conn_new.close()

if __name__ == "__main__":
    migrate()
