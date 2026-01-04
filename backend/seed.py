from sqlmodel import Session, select
from backend.database import engine, create_db_and_tables
from backend.models import Pump, CurveSet, CurveSeries, CurvePoint, SeriesType

def seed():
    create_db_and_tables()
    with Session(engine) as session:
        # Check if exists
        existing = session.exec(select(Pump)).first()
        if existing:
            print("Database already seeded.")
            return

        print("Seeding database...")

        # Create Pump
        pump = Pump(manufacturer="Acme Pumps", model="X-2000", meta_data={"impeller": "10.5 in", "rpm": 1750})
        session.add(pump)
        session.commit()
        session.refresh(pump)

        # Create Curve Set
        curve_set = CurveSet(
            name="1750 RPM, Max Impeller",
            pump_id=pump.id,
            units={"flow": "gpm", "head": "ft", "efficiency": "%", "power": "hp"},
            meta_data={"test_date": "2023-10-27"}
        )
        session.add(curve_set)
        session.commit()
        session.refresh(curve_set)

        # Create Series
        # Head vs Flow
        head_series = CurveSeries(curve_set_id=curve_set.id, type=SeriesType.head)
        session.add(head_series)
        session.commit()
        session.refresh(head_series)

        head_points = [
            (0, 100), (100, 98), (200, 95), (300, 90), (400, 82), (500, 70), (600, 55)
        ]
        for seq, (f, v) in enumerate(head_points):
            session.add(CurvePoint(series_id=head_series.id, flow=f, value=v, sequence=seq))

        # Efficiency vs Flow
        eff_series = CurveSeries(curve_set_id=curve_set.id, type=SeriesType.efficiency)
        session.add(eff_series)
        session.commit()
        session.refresh(eff_series)

        eff_points = [
            (0, 0), (100, 40), (200, 65), (300, 78), (400, 82), (500, 75), (600, 60)
        ]
        for seq, (f, v) in enumerate(eff_points):
            session.add(CurvePoint(series_id=eff_series.id, flow=f, value=v, sequence=seq))

        # Power vs Flow
        pwr_series = CurveSeries(curve_set_id=curve_set.id, type=SeriesType.power)
        session.add(pwr_series)
        session.commit()
        session.refresh(pwr_series)

        pwr_points = [
            (0, 5), (100, 8), (200, 12), (300, 15), (400, 18), (500, 20), (600, 21)
        ]
        for seq, (f, v) in enumerate(pwr_points):
            session.add(CurvePoint(series_id=pwr_series.id, flow=f, value=v, sequence=seq))

        session.commit()
        print("Seeding complete.")

if __name__ == "__main__":
    seed()
