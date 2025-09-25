import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DATABASE_URL")
CSV_PATH = os.getenv("CSV_PATH", "./datos_accidentes.csv")

def run_etl(sample_size: int = 100, random_state: int = 42) -> int:
    # Leer CSV con codificación robusta
    try:
        df = pd.read_csv(CSV_PATH, encoding="utf-8")
    except UnicodeDecodeError:
        df = pd.read_csv(CSV_PATH, encoding="latin1")

    df.columns = df.columns.str.lower()

    # Fecha unificada
    df["fecha"] = pd.to_datetime(
        df[["anio","mes","id_dia","id_hora","id_minuto"]]
        .rename(columns={"anio":"year","mes":"month","id_dia":"day","id_hora":"hour","id_minuto":"minute"}),
        errors="coerce"
    )

    # Campos clave
    cols = ["id_entidad","id_municipio","fecha","diasemana","urbana","suburbana",
            "tipaccid","causaacci","sexo","aliento","cinturon","clasacc","estatus"]
    df = df[cols].drop_duplicates().dropna(subset=["fecha"])

    # Muestra de 100
    if len(df) >= sample_size:
        df = df.sample(n=sample_size, random_state=random_state).reset_index(drop=True)
    else:
        df = df.reset_index(drop=True)

    # Crear tabla destino con PK autoincremental
    engine = create_engine(DB_URL, pool_pre_ping=True)
    with engine.begin() as conn:
        conn.exec_driver_sql("""
        CREATE TABLE IF NOT EXISTS accidentes_100 (
          accidente_id SERIAL PRIMARY KEY,
          id_entidad   INT NOT NULL,
          id_municipio INT NOT NULL,
          fecha        TIMESTAMP NOT NULL,
          diasemana    VARCHAR(20),
          urbana       VARCHAR(60),
          suburbana    VARCHAR(60),
          tipaccid     VARCHAR(120),
          causaacci    VARCHAR(60),
          sexo         VARCHAR(20),
          aliento      VARCHAR(20),
          cinturon     VARCHAR(20),
          clasacc      VARCHAR(50),
          estatus      VARCHAR(30)
        );
        """)
        # Limpiar y recargar
        conn.execute(text("TRUNCATE accidentes_100 RESTART IDENTITY;"))
        df.to_sql("accidentes_100", conn, if_exists="append", index=False)
        inserted = conn.execute(text("SELECT COUNT(*) FROM accidentes_100;")).scalar_one()
        return int(inserted)
