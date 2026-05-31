"""
Agente: Reorder Alert — Panadería
Monitoriza el stock independientemente del pipeline diario.
Genera alertas cuando un ingrediente baja del mínimo configurado.

Se puede ejecutar en cualquier momento para revisar el estado del almacén.
"""
import json
from pathlib import Path
from datetime import datetime

DATA_DIR = Path(__file__).parent / "data"


def load_json(filename):
    with open(DATA_DIR / filename, encoding="utf-8") as f:
        return json.load(f)


def analizar_stock(ingredientes: list) -> dict:
    criticos  = []
    bajos     = []
    correctos = []

    for ing in ingredientes:
        stock   = ing["stock_actual"]
        minimo  = ing["stock_minimo"]
        ratio   = stock / minimo if minimo > 0 else 99

        if ratio < 1.0:
            criticos.append(ing)
        elif ratio < 1.5:
            bajos.append(ing)
        else:
            correctos.append(ing)

    return {"criticos": criticos, "bajos": bajos, "correctos": correctos}


def generar_informe(analisis: dict) -> str:
    ahora    = datetime.now().strftime("%d/%m/%Y %H:%M")
    criticos = analisis["criticos"]
    bajos    = analisis["bajos"]
    correctos= analisis["correctos"]

    lineas = [
        f"🔔 ALERTA DE INVENTARIO — {ahora}",
        "=" * 50,
        "",
    ]

    if criticos:
        lineas.append(f"🔴 STOCK CRÍTICO ({len(criticos)} ingredientes):")
        for i in criticos:
            falta = i["stock_minimo"] - i["stock_actual"]
            lineas.append(f"   • {i['nombre']}: {i['stock_actual']} {i['unidad']} (mínimo: {i['stock_minimo']}) — FALTAN {round(falta,2)} {i['unidad']}")
            lineas.append(f"     → Proveedor: {i.get('proveedor','—')}")
        lineas.append("")

    if bajos:
        lineas.append(f"🟡 STOCK BAJO ({len(bajos)} ingredientes):")
        for i in bajos:
            lineas.append(f"   • {i['nombre']}: {i['stock_actual']} {i['unidad']} (mínimo: {i['stock_minimo']})")
            lineas.append(f"     → Proveedor: {i.get('proveedor','—')}")
        lineas.append("")

    if correctos:
        lineas.append(f"✅ STOCK OK ({len(correctos)} ingredientes):")
        for i in correctos:
            lineas.append(f"   • {i['nombre']}: {i['stock_actual']} {i['unidad']}")
        lineas.append("")

    if not criticos and not bajos:
        lineas.append("✅ Todo el inventario está por encima del mínimo. No se requiere acción.")

    return "\n".join(lineas)


def run() -> dict:
    ingredientes = load_json("ingredientes.json")
    analisis     = analizar_stock(ingredientes)
    informe      = generar_informe(analisis)

    print(informe, flush=True)

    return {
        "timestamp":      datetime.now().isoformat(),
        "criticos":       len(analisis["criticos"]),
        "bajos":          len(analisis["bajos"]),
        "correctos":      len(analisis["correctos"]),
        "ingredientes":   analisis,
        "informe":        informe,
    }


if __name__ == "__main__":
    result = run()
