# Agentes de Inventario IA — Panadería

Sistema de gestión inteligente para panaderías. Predice demanda, planifica producción y alerta de stock bajo.

## Agentes

| Agente | Función |
|---|---|
| `ceo.py` | Orquesta el pipeline completo |
| `demand_forecaster.py` | Predice demanda del día siguiente con IA |
| `production_planner.py` | Genera plan de producción + lista de compra |
| `reorder_alert.py` | Monitoriza stock y genera alertas |

## Uso rápido

```bash
# Pipeline completo (para ejecutar cada mañana)
python ceo.py

# Solo revisar stock
python ceo.py --solo-stock

# Plan para una fecha concreta
python ceo.py --fecha 2026-06-05
```

## Requisitos

```bash
pip install anthropic
```

Añadir `ANTHROPIC_API_KEY` como variable de entorno para activar ajuste IA en la previsión.
Sin ella, funciona con previsión estadística pura.

## Datos (carpeta `data/`)

| Archivo | Contenido |
|---|---|
| `productos.json` | Catálogo de productos |
| `ingredientes.json` | Stock actual + mínimos + proveedores |
| `recetas.json` | Ingredientes por producto (cantidades) |
| `ventas_historicas.json` | Historial de ventas por día |

Actualizar `ingredientes.json` cada día con el stock real para que el sistema funcione correctamente.

## Flujo diario recomendado

1. **Cada mañana a las 6:00h** → ejecutar `python ceo.py`
2. Revisar el plan de producción y la lista de compra
3. Hacer pedidos a proveedores antes de las 10:00h si hay items críticos
4. Al final del día → actualizar `ventas_historicas.json` con las ventas reales
5. Actualizar `ingredientes.json` con el stock tras la jornada
