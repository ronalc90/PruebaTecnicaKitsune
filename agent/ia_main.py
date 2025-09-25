import os
from dotenv import load_dotenv
from openai import OpenAI

# Cargar variables desde el archivo .env
load_dotenv()

# Cliente de OpenAI usando tu variable personalizada
api_key = os.getenv("KEY_OPEN_IA")
if not api_key:
    raise ValueError("❌ No se encontró la variable KEY_OPEN_IA en el entorno")

client = OpenAI(api_key=api_key)

# URL base de tu API
API_BASE = "http://127.0.0.1:8000"

def agente_consulta(pregunta: str):
    """
    Agente que recibe consulta en lenguaje natural,
    la convierte en una llamada a la API y devuelve resultados resumidos.
    """
    # --- 1. Interpretar la intención con OpenAI ---
    system_prompt = """
    Eres un agente que traduce preguntas en lenguaje natural a llamadas REST.
    La API disponible tiene estos endpoints:
    - GET /records -> lista registros
    - GET /records/{id} -> consulta un registro por ID
    - GET /search?q=<palabra>&clasacc=<valor> -> búsqueda con filtros

    Responde SOLO con un JSON válido:
    {"endpoint": "...", "params": {...}, "needs_clarification": false, "clarification": ""}
    Si la consulta es ambigua y necesitas pedir más info, responde con:
    {"endpoint": null, "params": {}, "needs_clarification": true, "clarification": "texto de aclaración"}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",  # puedes ajustar
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": pregunta}
        ],
        temperature=0
    )

    content = response.choices[0].message.content.strip()
    try:
        api_call = eval(content)  # ⚠️ aquí parseamos, mejor usar json.loads
    except Exception as e:
        return f"Error interpretando intención: {content} ({e})"

    # --- 2. Si es ambigua, pedir aclaración ---
    if api_call.get("needs_clarification", False):
        return f"Necesito más información: {api_call.get('clarification')}"

    endpoint = api_call.get("endpoint")
    params = api_call.get("params", {})

    # --- 3. Ejecutar la llamada a la API ---
    try:
        url = f"{API_BASE}{endpoint}"
        r = requests.get(url, params=params)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        return f"Error al llamar API: {e}"

    # --- 4. Resumir con OpenAI los 5 primeros resultados ---
    resumen_prompt = f"""
    Resume claramente los siguientes resultados de accidentes (máximo 5 registros).
    Datos: {data}
    """
    resumen = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": "Eres un asistente que resume resultados."},
                  {"role": "user", "content": resumen_prompt}],
        temperature=0.3
    )

    return resumen.choices[0].message.content.strip()


# ==========================
# EJEMPLOS DE USO
# ==========================
if __name__ == "__main__":
    print(agente_consulta("Muéstrame los accidentes con peatones"))
    print(agente_consulta("Quiero ver el registro con id 10"))
    print(agente_consulta("Dame todos los registros"))
