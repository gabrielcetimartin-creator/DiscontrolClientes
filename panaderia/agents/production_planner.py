"""
Agente: Production Planner — Panadería
Genera el plan de producción del día a partir de la previsión de demanda.

Input:  forecast del demand_forecaster, recetas.json, ingredientes.json
Output: plan de producción + lista de ingredientes necesarios + alertas de stock
"""
import json
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"


def load_json(filename):
    with open(DATA_DIR / filename, encoding="utf-8") as f:
        return json.load(f)


def calcular_ingredientes(forecast: dict, recetas: list, margen: float = 0.10) -> dict:
    """Calcula ingredientes totales necesarios añadiendo un margen de seguridad."""
    recetas_map = {r["producto_id"]: r["ingredientes"] for r in recetas}
    necesarios  = {}

    for producto_id, cantidad in forecast.items():
        cantidad_con_margen = cantidad * (1 + margen)
        ingredientes = recetas_map.get(producto_id, [])
        for ing in ingredientes:
            ing_id = ing["id"]
            necesarios[ing_id] = necesarios.get(ing_id, 0) + ing["cantidad"] * cantidad_con_margen

    return {k: round(v, 3) for k, v in necesarios.items()}


def verificar_stock(necesarios: dict, ingredientes: list) -> dict:
    """Compara stock disponible vs necesario. Devuelve alertas."""
    stock_map = {i["id"]: i for i in ingredientes}
    resultado = {}

    for ing_id, cantidad_necesaria in necesarios.items():
        ing = stock_map.get(ing_id)
        if not ing:
            continue
        stock      = ing["stock_actual"]
        minimo     = ing["stock_minimo"]
        diferencia = stock - cantidad_necesaria

        if diferencia < 0:
            estado = "🔴 INSUFICIENTE"
        elif stock <= minimo:
            estado = "🟡 STOCK BAJO"
        else:
            estado = "✅ OK"

        resultado[ing_id] = {
            "nombre":           ing["nombre"],
            "stock_actual":     stock,
            "stock_minimo":     minimo,
            "necesario":        cantidad_necesaria,
            "diferencia":       round(diferencia, 3),
            "unidad":           ing["unidad"],
            "estado":           estado,
            "proveedor":        ing.get("proveedor", "—"),
        }

    return resultado


def generar_lista_compra(verificacion: dict, ingredientes: list) -> list:
    """Genera lista de compra para ingredientes insuficientes o con stock bajo."""
    precio_map = {i["id"]: i.get("precio_kg", 0) for i in ingredientes}
    lista = []

    for ing_id, datos in verificacion.items():
        if datos["estado"] in ("🔴 INSUFICIENTE", "🟡 STOCK BAJO"):
            # Pedir suficiente para cubrir la necesidad + reponer al doble del mínimo
            cantidad_pedir = max(
                abs(datos["diferencia"]),
                datos["stock_minimo"] * 2 - datos["stock_actual"]
            )
            lista.append({
                "ingrediente":    datos["nombre"],
                "cantidad_pedir": round(cantidad_pedir, 2),
                "unidad":         datos["unidad"],
                "proveedor":      datos["proveedor"],
                "estado":         datos["estado"],
                "coste_estimado": round(cantidad_pedir * precio_map.get(ing_id, 0), 2),
            })

    return sorted(lista, key=lambda x: x["estado"])


def run(forecast_data: dict) -> dict:
    fecha    = forecast_data.get("fecha", "—")
    dia      = forecast_data.get("dia_semana", "—")
    forecast = forecast_data.get("forecast", {})

    recetas      = load_json("recetas.json")
    ingredientes = load_json("ingredientes.json")
    productos    = load_json("productos.json")
    prod_map     = {p["id"]: p["nombre"] for p in productos}

    print(f"\n🏭 Generando plan de producción para {fecha} ({dia})", flush=True)

    necesarios   = calcular_ingredientes(forecast, recetas)
    verificacion = verificar_stock(necesarios, ingredientes)
    lista_compra = generar_lista_compra(verificacion, ingredientes)

    # Plan de producción
    print("\n📋 PLAN DE PRODUCCIÓN:", flush=True)
    print(f"{'Producto':<30} {'Unidades':>10}", flush=True)
    print("─" * 42, flush=True)
    for pid, cant in forecast.items():
        print(f"  {prod_map.get(pid, pid):<28} {cant:>10} uds", flush=True)

    # Estado de ingredientes
    print("\n🧂 INGREDIENTES:", flush=True)
    for ing_id, datos in verificacion.items():
        print(f"  {datos['estado']} {datos['nombre']}: {datos['stock_actual']} {datos['unidad']} disponible, {datos['necesario']} {datos['unidad']} necesario", flush=True)

    # Lista de compra
    if lista_compra:
        print(f"\n🛒 LISTA DE COMPRA ({len(lista_compra)} items):", flush=True)
        coste_total = 0
        for item in lista_compra:
            print(f"  {item['estado']} {item['ingrediente']}: {item['cantidad_pedir']} {item['unidad']} — {item['proveedor']} (~{item['coste_estimado']}€)", flush=True)
            coste_total += item["coste_estimado"]
        print(f"\n  💶 Coste estimado total: {round(coste_total, 2)}€", flush=True)
    else:
        print("\n✅ Stock suficiente para toda la producción — no hay que comprar nada.", flush=True)

    return {
        "fecha":         fecha,
        "plan":          forecast,
        "ingredientes":  verificacion,
        "lista_compra":  lista_compra,
        "coste_compra":  round(sum(i["coste_estimado"] for i in lista_compra), 2),
    }


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    import demand_forecaster
    forecast_data = demand_forecaster.run()
    result = run(forecast_data)
    print("\n" + json.dumps(result, ensure_ascii=False, indent=2, default=str))
