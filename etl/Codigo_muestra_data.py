import pandas as pd
from sqlalchemy import create_engine

# --- 1. Cargar dataset con encoding correcto ---
file_path = "datos_accidentes.csv"

# Usa latin1 o cp1252 (Windows) si utf-8 falla
df = pd.read_csv(file_path, encoding="latin1")

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

connection_string = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(connection_string, echo=False)

with engine.connect() as conn:
    print("✅ Conexión a PostgreSQL establecida correctamente")

# --- 8. Crear tabla y cargar datos ---
table_name = "accidentes_100"
df_muestra.to_sql(table_name, engine, if_exists="replace", index=False)

print("✅ Dataset limpio con 100 registros cargado en PostgreSQL.")
