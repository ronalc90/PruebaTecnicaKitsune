import pandas as pd
from sqlalchemy import create_engine, text

# --- 1. Cargar dataset ---
file_path = "../Dataset/datos_accidentes.csv"
df = pd.read_csv(file_path, encoding="latin1")  # evita errores de codificación

# --- 2. Normalizar nombres de columnas ---
df.columns = df.columns.str.lower()

# --- 3. Crear columna fecha unificada ---
df["fecha"] = pd.to_datetime(
    df[["anio", "mes", "id_dia", "id_hora", "id_minuto"]]
    .rename(columns={
        "anio": "year",
        "mes": "month",
        "id_dia": "day",
        "id_hora": "hour",
        "id_minuto": "minute"
    }),
    errors="coerce"
)

# --- 4. Selección de campos clave ---
df_reducido = df[[
    "id_entidad", "id_municipio", "fecha", "diasemana",
    "urbana", "suburbana", "tipaccid", "causaacci",
    "sexo", "aliento", "cinturon", "clasacc", "estatus"
]].copy()

# --- 5. Limpieza ---
df_reducido = df_reducido.drop_duplicates()
df_reducido = df_reducido.dropna(subset=["fecha"])

# --- 6. Tomar 100 registros representativos ---
df_muestra = df_reducido.sample(n=100, random_state=42).reset_index(drop=True)

# --- 7. Conexión a PostgreSQL ---
DB_USER = "postgres"
DB_PASS = "1234"
DB_HOST = "localhost"
DB_PORT = "5433"
DB_NAME = "accidentes_db"

engine = create_engine(f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

table_name = "accidentes_100"

# --- 8. Crear tabla manualmente con accidente_id ---
with engine.begin() as conn:
    conn.execute(text(f"DROP TABLE IF EXISTS {table_name} CASCADE;"))
    conn.execute(text(f"""
        CREATE TABLE {table_name} (
            accidente_id SERIAL PRIMARY KEY,
            id_entidad   INT NOT NULL,
            id_municipio INT NOT NULL,
            fecha        TIMESTAMP NOT NULL,
            diasemana    VARCHAR(20),
            urbana       VARCHAR(120),
            suburbana    VARCHAR(120),
            tipaccid     VARCHAR(200),
            causaacci    VARCHAR(120),
            sexo         VARCHAR(20),
            aliento      VARCHAR(20),
            cinturon     VARCHAR(20),
            clasacc      VARCHAR(50),
            estatus      VARCHAR(50)
        );
    """))

# --- 9. Insertar los datos (sin accidente_id, lo genera PostgreSQL) ---
df_muestra.to_sql(table_name, engine, if_exists="append", index=False)

print("✅ Tabla recreada y dataset de 100 registros cargado en PostgreSQL con accidente_id autoincremental.")
