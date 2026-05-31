"""
CEO — Sistema de Gestión Inteligente de Panadería
Orquesta el pipeline completo:
  1. Demand Forecaster  → predice demanda del día siguiente
  2. Production Planner → genera plan de producción + lista de compra
  3. Reorder Alert      → revisa el estado general del stock

Uso:
  python ceo.py                    → pipeline completo para mañana
  python ceo.py --solo-stock       → solo alerta de stock
  python ceo.py --fecha 2026-06-05 → plan para fecha concreta
"""
import sys, json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

import demand_forecaster
import production_planner
import reorder_alert


def separador(titulo: str):
    print(f"\n{'━' * 55}", flush=True)
    print(f"  {titulo}", flush=True)
    print(f"{'━' * 55}", flush=True)


def run(fecha: datetime = None, solo_stock: bool = False):
    print("\n🥖 SISTEMA DE GESTIÓN — PANADERÍA", flush=True)
    print(f"   {datetime.now().strftime('%d/%m/%Y %H:%M')}", flush=True)

    # ── PASO 1: Alerta de stock actual ────────────────────────
    separador("PASO 1 · Estado del inventario")
    alerta = reorder_alert.run()

    if alerta["criticos"] > 0:
        print(f"\n⚠️  HAY {alerta['criticos']} INGREDIENTE(S) EN ESTADO CRÍTICO", flush=True)

    if solo_stock:
        return {"alerta": alerta}

    # ── PASO 2: Previsión de demanda ──────────────────────────
    separador("PASO 2 · Previsión de demanda")
    forecast_data = demand_forecaster.run(fecha)

    # ── PASO 3: Plan de producción ────────────────────────────
    separador("PASO 3 · Plan de producción")
    plan = production_planner.run(forecast_data)

    # ── RESUMEN FINAL ─────────────────────────────────────────
    separador("RESUMEN EJECUTIVO")
    fecha_str = forecast_data.get("fecha", "—")
    dia_str   = forecast_data.get("dia_semana", "—")
    total_uds = sum(forecast_data.get("forecast", {}).values())

    print(f"  📅 Fecha:              {fecha_str} ({dia_str})", flush=True)
    print(f"  🍞 Unidades a producir: {total_uds}", flush=True)
    print(f"  🔴 Ingredientes críticos: {alerta['criticos']}", flush=True)
    print(f"  🟡 Stock bajo:            {alerta['bajos']}", flush=True)
    print(f"  🛒 Items a comprar:       {len(plan.get('lista_compra', []))}", flush=True)
    print(f"  💶 Coste estimado compra: {plan.get('coste_compra', 0)}€", flush=True)

    if plan.get("lista_compra"):
        print("\n  ⚡ ACCIÓN REQUERIDA: Realizar pedido a proveedores antes de las 10:00h", flush=True)
    else:
        print("\n  ✅ Sin acciones pendientes — todo listo para producción", flush=True)

    return {
        "alerta":   alerta,
        "forecast": forecast_data,
        "plan":     plan,
    }


if __name__ == "__main__":
    solo_stock = "--solo-stock" in sys.argv
    fecha      = None

    if "--fecha" in sys.argv:
        idx = sys.argv.index("--fecha")
        try:
            fecha = datetime.strptime(sys.argv[idx + 1], "%Y-%m-%d")
        except (IndexError, ValueError):
            print("Uso: python ceo.py --fecha YYYY-MM-DD")
            sys.exit(1)

    result = run(fecha=fecha, solo_stock=solo_stock)
