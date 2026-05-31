"""
Script de actualización de datos — Panadería
Permite actualizar stock, añadir ventas y gestionar ingredientes fácilmente.

Uso:
  python actualizar_datos.py stock harina_trigo 65
  python actualizar_datos.py venta 2026-06-01 pan_masa_madre 48
  python actualizar_datos.py ver-stock
  python actualizar_datos.py ver-ventas
"""
import json, sys
from pathlib import Path
from datetime import datetime

DATA_DIR = Path(__file__).parent / "data"


def load(f):
    with open(DATA_DIR / f, encoding="utf-8") as fh:
        return json.load(fh)


def save(f, data):
    with open(DATA_DIR / f, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
    print(f"✅ {f} actualizado.")


def actualizar_stock(ingrediente_id: str, nuevo_stock: float):
    ingredientes = load("ingredientes.json")
    for ing in ingredientes:
        if ing["id"] == ingrediente_id:
            viejo = ing["stock_actual"]
            ing["stock_actual"] = nuevo_stock
            save("ingredientes.json", ingredientes)
            print(f"   {ing['nombre']}: {viejo} → {nuevo_stock} {ing['unidad']}")
            return
    print(f"❌ Ingrediente '{ingrediente_id}' no encontrado.")
    print("   IDs disponibles:", ", ".join(i["id"] for i in ingredientes))


def añadir_venta(fecha: str, producto_id: str, cantidad: int):
    try:
        dt = datetime.strptime(fecha, "%Y-%m-%d")
    except ValueError:
        print("❌ Formato de fecha incorrecto. Usa: YYYY-MM-DD")
        return

    dias = ["lunes","martes","miercoles","jueves","viernes","sabado","domingo"]
    dia  = dias[dt.weekday()]

    ventas = load("ventas_historicas.json")
    ventas.append({
        "fecha":      fecha,
        "dia_semana": dia,
        "producto_id": producto_id,
        "cantidad":   cantidad,
    })
    save("ventas_historicas.json", ventas)
    print(f"   {fecha} ({dia}) — {producto_id}: {cantidad} uds añadidas.")


def ver_stock():
    ingredientes = load("ingredientes.json")
    print(f"\n{'Ingrediente':<30} {'Stock':>8} {'Mínimo':>8} {'Estado':>12}")
    print("─" * 62)
    for i in ingredientes:
        ratio  = i["stock_actual"] / i["stock_minimo"] if i["stock_minimo"] > 0 else 99
        estado = "🔴 CRÍTICO" if ratio < 1.0 else ("🟡 BAJO" if ratio < 1.5 else "✅ OK")
        print(f"  {i['nombre']:<28} {i['stock_actual']:>7} {i['unidad']:<2} {i['stock_minimo']:>6} {i['unidad']:<2}  {estado}")


def ver_ventas(ultimos_n: int = 10):
    ventas = load("ventas_historicas.json")
    productos = {p["id"]: p["nombre"] for p in load("productos.json")}
    ultimas = ventas[-ultimos_n:]
    print(f"\nÚltimas {len(ultimas)} entradas de ventas:")
    print(f"{'Fecha':<14} {'Día':<12} {'Producto':<30} {'Cant':>6}")
    print("─" * 66)
    for v in ultimas:
        nombre = productos.get(v["producto_id"], v["producto_id"])
        print(f"  {v['fecha']:<12} {v['dia_semana']:<12} {nombre:<28} {v['cantidad']:>6}")


if __name__ == "__main__":
    args = sys.argv[1:]

    if not args:
        print(__doc__)
        sys.exit(0)

    cmd = args[0]

    if cmd == "stock" and len(args) == 3:
        actualizar_stock(args[1], float(args[2]))

    elif cmd == "venta" and len(args) == 4:
        añadir_venta(args[1], args[2], int(args[3]))

    elif cmd == "ver-stock":
        ver_stock()

    elif cmd == "ver-ventas":
        n = int(args[1]) if len(args) > 1 else 10
        ver_ventas(n)

    else:
        print(__doc__)
