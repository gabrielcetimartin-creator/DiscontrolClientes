"""
Agente: Demand Forecaster — Panadería
Predice la demanda del día siguiente usando historial de ventas + IA.

Input:  ventas_historicas.json, productos.json, fecha objetivo
Output: { producto_id: cantidad_prevista, ... }
"""
import json, os, sys
from pathlib import Path
from datetime import datetime, timedelta

DATA_DIR = Path(__file__).parent / "data"


def load_json(filename):
    with open(DATA_DIR / filename, encoding="utf-8") as f:
        return json.load(f)


def get_dia_semana(fecha: datetime) -> str:
    nombres = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]
    return nombres[fecha.weekday()]


def ventas_por_dia(ventas: list, dia_semana: str) -> dict:
    totales = {}
    conteos = {}
    for v in ventas:
        if v["dia_semana"] == dia_semana:
            pid = v["producto_id"]
            totales[pid] = totales.get(pid, 0) + v["cantidad"]
            conteos[pid] = conteos.get(pid, 0) + 1
    return {pid: round(totales[pid] / conteos[pid]) for pid in totales}


def forecast_con_ia(fecha: datetime, media_dia: dict, productos: list) -> dict:
    """
    Usa Claude para ajustar la previsión según contexto (festivos, temporada, tendencias).
    Requiere ANTHROPIC_API_KEY en el entorno.
    """
    try:
        import anthropic
    except ImportError:
        print("⚠️  anthropic no instalado — usando previsión estadística pura", flush=True)
        return media_dia

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("⚠️  ANTHROPIC_API_KEY no configurada — usando previsión estadística pura", flush=True)
        return media_dia

    client = anthropic.Anthropic(api_key=api_key)

    productos_map = {p["id"]: p["nombre"] for p in productos}
    historico_str = "\n".join(
        f"  - {productos_map.get(pid, pid)}: media {cant} unidades"
        for pid, cant in media_dia.items()
    )

    prompt = f"""Eres el sistema de previsión de demanda de una panadería artesanal.

Fecha de mañana: {fecha.strftime('%A %d de %B de %Y')} ({get_dia_semana(fecha)})

Ventas medias para este día de la semana (basado en historial):
{historico_str}

Analiza si hay factores que justifiquen ajustar estas cantidades:
- ¿Es víspera de festivo o fin de semana largo?
- ¿Hay alguna festividad local relevante?
- ¿Es temporada alta (verano, Navidad, Semana Santa)?
- ¿Otros factores estacionales?

Responde SOLO con un JSON válido con las cantidades ajustadas. Ejemplo:
{{"pan_masa_madre": 45, "baguette": 40, "croissant": 28, "pan_sin_gluten": 7, "napolitana": 20}}

Si no hay razón para ajustar, devuelve las mismas cantidades. Redondea siempre al entero más cercano."""

    try:
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}]
        )
        text = msg.content[0].text.strip()
        # Extraer JSON de la respuesta
        import re
        m = re.search(r'\{[^}]+\}', text, re.DOTALL)
        if m:
            return json.loads(m.group())
    except Exception as e:
        print(f"⚠️  Error en IA: {e} — usando previsión estadística", flush=True)

    return media_dia


def run(fecha_objetivo: datetime = None) -> dict:
    if fecha_objetivo is None:
        fecha_objetivo = datetime.now() + timedelta(days=1)

    productos  = load_json("productos.json")
    ventas     = load_json("ventas_historicas.json")
    dia        = get_dia_semana(fecha_objetivo)

    print(f"📅 Previendo demanda para: {fecha_objetivo.strftime('%d/%m/%Y')} ({dia})", flush=True)

    media_dia = ventas_por_dia(ventas, dia)
    if not media_dia:
        # Sin historial para ese día: usar media global
        todos_dias = {}
        conteos    = {}
        for v in ventas:
            pid = v["producto_id"]
            todos_dias[pid] = todos_dias.get(pid, 0) + v["cantidad"]
            conteos[pid]    = conteos.get(pid, 0) + 1
        media_dia = {pid: round(todos_dias[pid] / conteos[pid]) for pid in todos_dias}
        print("⚠️  Sin historial para este día — usando media global", flush=True)

    print(f"📊 Media histórica ({dia}):", flush=True)
    for pid, cant in media_dia.items():
        print(f"   {pid}: {cant} uds", flush=True)

    forecast = forecast_con_ia(fecha_objetivo, media_dia, productos)

    print("\n🤖 Previsión final (con ajuste IA):", flush=True)
    for pid, cant in forecast.items():
        diff = cant - media_dia.get(pid, cant)
        signo = f"+{diff}" if diff > 0 else str(diff)
        print(f"   {pid}: {cant} uds  ({signo} vs media)", flush=True)

    return {"fecha": fecha_objetivo.strftime("%Y-%m-%d"), "dia_semana": dia, "forecast": forecast}


if __name__ == "__main__":
    result = run()
    print("\n" + json.dumps(result, ensure_ascii=False, indent=2))
