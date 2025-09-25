import os
import jwt
from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import FastAPI, Depends, HTTPException, Query, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

from etl import run_etl

load_dotenv()

DB_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGO = "HS256"

engine = create_engine(DB_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

app = FastAPI(title="Accidentes API", version="1.0")


# ---------- Auth util ----------
def create_jwt(subject: str, minutes: int = 60) -> str:
    now = datetime.utcnow()
    payload = {"sub": subject, "iat": now, "exp": now + timedelta(minutes=minutes)}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGO)

def require_jwt(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Token requerido")
    token = authorization.split(" ", 1)[1]
    try:
        jwt.decode(token, SECRET_KEY, algorithms=[ALGO])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")
    return True


# ---------- Schemas ----------
class Accidente(BaseModel):
    accidente_id: int
    id_entidad: int
    id_municipio: int
    fecha: datetime
    diasemana: Optional[str]
    urbana: Optional[str]
    suburbana: Optional[str]
    tipaccid: Optional[str]
    causaacci: Optional[str]
    sexo: Optional[str]
    aliento: Optional[str]
    cinturon: Optional[str]
    clasacc: Optional[str]
    estatus: Optional[str]

class SearchResponse(BaseModel):
    total: int
    items: List[Accidente]


# ---------- Endpoints ----------
@app.get("/auth/dev-token")
def dev_token():
    """Solo para pruebas locales. Quita en producción."""
    return {"token": create_jwt("etl_admin", minutes=120)}

@app.get("/records", response_model=SearchResponse)
def list_records(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    order: str = Query("fecha_desc", pattern="^(fecha_(asc|desc))$")
):
    order_sql = "fecha DESC" if order.endswith("desc") else "fecha ASC"
    with engine.connect() as conn:
        total = conn.execute(text("SELECT COUNT(*) FROM accidentes_100")).scalar_one()
        rows = conn.execute(text(f"""
            SELECT * FROM accidentes_100
            ORDER BY {order_sql}
            LIMIT :limit OFFSET :offset
        """), {"limit": limit, "offset": offset}).mappings().all()
        return {"total": total, "items": rows}

@app.get("/records/{accidente_id}", response_model=Accidente)
def get_record(accidente_id: int):
    with engine.connect() as conn:
        row = conn.execute(text("""
            SELECT * FROM accidentes_100 WHERE accidente_id = :id
        """), {"id": accidente_id}).mappings().first()
        if not row:
            raise HTTPException(status_code=404, detail="No encontrado")
        return row

@app.get("/search", response_model=SearchResponse)
def search(
    q: Optional[str] = Query(None, description="Palabra clave en tipo, causa, urbana, suburbana"),
    id_entidad: Optional[int] = None,
    id_municipio: Optional[int] = None,
    clasacc: Optional[str] = None,
    desde: Optional[datetime] = None,
    hasta: Optional[datetime] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    order: str = Query("fecha_desc", pattern="^(fecha_(asc|desc))$")
):
    clauses = ["1=1"]
    params = {}

    if q:
        clauses.append("(tipaccid ILIKE :q OR causaacci ILIKE :q OR urbana ILIKE :q OR suburbana ILIKE :q)")
        params["q"] = f"%{q}%"
    if id_entidad is not None:
        clauses.append("id_entidad = :id_entidad")
        params["id_entidad"] = id_entidad
    if id_municipio is not None:
        clauses.append("id_municipio = :id_municipio")
        params["id_municipio"] = id_municipio
    if clasacc:
        clauses.append("clasacc ILIKE :clasacc")
        params["clasacc"] = clasacc
    if desde:
        clauses.append("fecha >= :desde")
        params["desde"] = desde
    if hasta:
        clauses.append("fecha <= :hasta")
        params["hasta"] = hasta

    where_sql = " AND ".join(clauses)
    order_sql = "fecha DESC" if order.endswith("desc") else "fecha ASC"

    with engine.connect() as conn:
        total = conn.execute(text(f"SELECT COUNT(*) FROM accidentes_100 WHERE {where_sql}"), params).scalar_one()
        rows = conn.execute(text(f"""
            SELECT * FROM accidentes_100
            WHERE {where_sql}
            ORDER BY {order_sql}
            LIMIT :limit OFFSET :offset
        """), {**params, "limit": limit, "offset": offset}).mappings().all()
        return {"total": total, "items": rows}

@app.post("/admin/refresh-etl")
def refresh_etl(_: bool = Depends(require_jwt)):
    inserted = run_etl(sample_size=100)
    return JSONResponse({"status": "ok", "inserted": inserted})
