#!/usr/bin/env python3
"""
Sistema de Monitoreo Automático
Rastrea oportunidades y genera logs para validación sin gastar dinero
"""

import requests
import json
from datetime import datetime
import os
from pathlib import Path

# Configuración
API_BASE = "http://localhost:8000"
VALIDATION_DIR = Path(__file__).parent

def get_timestamp():
    """Retorna timestamp formateado"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def get_date():
    """Retorna fecha actual"""
    return datetime.now().strftime("%Y-%m-%d")

def log_opportunity(data):
    """Guarda oportunidad detectada en archivo JSON"""
    opportunities_dir = VALIDATION_DIR / "opportunities"
    opportunities_dir.mkdir(exist_ok=True)

    filename = opportunities_dir / f"opportunities_{get_date()}.jsonl"

    with open(filename, 'a', encoding='utf-8') as f:
        f.write(json.dumps(data, ensure_ascii=False) + '\n')

    print(f"[OK] Oportunidad guardada en {filename}")

def log_prediction(data):
    """Guarda predicción ML en archivo JSON"""
    predictions_dir = VALIDATION_DIR / "predictions"
    predictions_dir.mkdir(exist_ok=True)

    filename = predictions_dir / f"predictions_{get_date()}.jsonl"

    with open(filename, 'a', encoding='utf-8') as f:
        f.write(json.dumps(data, ensure_ascii=False) + '\n')

    print(f"[OK] Prediccion guardada en {filename}")

def check_dashboard():
    """Revisa dashboard y extrae métricas clave"""
    try:
        resp = requests.get(f"{API_BASE}/api/v1/analytics/dashboard", timeout=10)
        resp.raise_for_status()
        data = resp.json()

        log_entry = {
            'timestamp': get_timestamp(),
            'date': get_date(),
            'today': data.get('today', {}),
            'week': data.get('week', {}),
            'alerts': data.get('alerts', {}),
            'latest_trade': data.get('latest_trade', {})
        }

        print(f"\nDashboard actualizado:")
        print(f"   Hoy: {data['today']['total_trades']} trades, ${data['today']['total_profit']:.2f} profit")
        print(f"   Semana: {data['week']['total_trades']} trades, ${data['week']['total_profit']:.2f} profit")
        print(f"   Alertas no leidas: {data['alerts']['unread']}")

        return log_entry

    except Exception as e:
        print(f"[ERROR] Error obteniendo dashboard: {e}")
        return None

def check_arbitrage_opportunities():
    """Busca oportunidades de arbitraje"""
    try:
        # Intentar obtener análisis avanzado de arbitraje
        resp = requests.get(f"{API_BASE}/api/v1/advanced-arbitrage/opportunities", timeout=10)

        if resp.status_code == 200:
            data = resp.json()
            opportunities = data.get('opportunities', [])

            if opportunities:
                print(f"\n{len(opportunities)} oportunidades de arbitraje detectadas:")

                for i, opp in enumerate(opportunities[:5], 1):  # Mostrar solo las 5 mejores
                    log_opportunity({
                        'timestamp': get_timestamp(),
                        'date': get_date(),
                        'opportunity': opp,
                        'manual_verification': {
                            'verified': None,
                            'notes': 'Pendiente verificacion manual'
                        }
                    })

                    print(f"   {i}. Tipo: {opp.get('type', 'N/A')}")
                    print(f"      Profit potencial: {opp.get('profit_percentage', 0):.2f}%")

                return opportunities
            else:
                print("\n[AVISO] No hay oportunidades de arbitraje en este momento")
                return []
        else:
            print(f"\n[AVISO] Endpoint de arbitraje no disponible (HTTP {resp.status_code})")
            return []

    except Exception as e:
        print(f"[ERROR] Error buscando oportunidades: {e}")
        return []

def check_ml_predictions():
    """Intenta obtener predicciones ML"""
    pairs = ['USDT_COP', 'USDT_VES']

    print(f"\nBuscando predicciones ML...")

    for pair in pairs:
        try:
            resp = requests.get(f"{API_BASE}/api/v1/analytics/ml/predict-spread?pair={pair}", timeout=10)

            if resp.status_code == 200:
                data = resp.json()

                prediction = {
                    'timestamp': get_timestamp(),
                    'date': get_date(),
                    'pair': pair,
                    'prediction': data,
                    'actual_24h_later': {
                        'price': None,
                        'spread': None,
                        'accuracy': None,
                        'notes': 'Verificar en 24 horas'
                    }
                }

                log_prediction(prediction)

                print(f"   [OK] {pair}: Prediccion obtenida")

            else:
                print(f"   [AVISO] {pair}: No disponible")

        except Exception as e:
            print(f"   [ERROR] {pair}: Error - {e}")

def generate_daily_summary():
    """Genera resumen del día"""
    summary_file = VALIDATION_DIR / "daily_logs" / f"summary_{get_date()}.md"
    summary_file.parent.mkdir(exist_ok=True)

    dashboard = check_dashboard()

    if not dashboard:
        return

    summary = f"""# Resumen del Día - {get_date()}

## 📊 Métricas del Sistema

### Hoy
- **Trades**: {dashboard['today'].get('total_trades', 0)}
- **Completados**: {dashboard['today'].get('completed_trades', 0)}
- **Profit Total**: ${dashboard['today'].get('total_profit', 0):.2f}
- **Profit Promedio**: ${dashboard['today'].get('average_profit', 0):.2f}

### Esta Semana
- **Trades**: {dashboard['week'].get('total_trades', 0)}
- **Profit Total**: ${dashboard['week'].get('total_profit', 0):.2f}
- **Profit Promedio**: ${dashboard['week'].get('average_profit', 0):.2f}

### Alertas
- **No leídas**: {dashboard['alerts'].get('unread', 0)}

### Último Trade
- **ID**: {dashboard['latest_trade'].get('id', 'N/A')}
- **Tipo**: {dashboard['latest_trade'].get('type', 'N/A')}
- **Status**: {dashboard['latest_trade'].get('status', 'N/A')}
- **Moneda**: {dashboard['latest_trade'].get('fiat', 'N/A')}
- **Monto**: ${dashboard['latest_trade'].get('amount', 0):.2f}

---

## 🎯 Oportunidades Detectadas

*Revisar archivo: `opportunities/opportunities_{get_date()}.jsonl`*

## 🤖 Predicciones ML

*Revisar archivo: `predictions/predictions_{get_date()}.jsonl`*

---

## ✅ Tareas Pendientes

- [ ] Verificar manualmente oportunidades del día
- [ ] Comparar predicciones ML de ayer vs precio real
- [ ] Actualizar Google Sheets
- [ ] Screenshots del dashboard

---

**Generado**: {get_timestamp()}
"""

    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(summary)

    print(f"\nResumen guardado en: {summary_file}")

def main():
    """Función principal de monitoreo"""
    print("="*60)
    print(f"MONITOREO DEL SISTEMA - {get_timestamp()}")
    print("="*60)

    # 1. Revisar dashboard
    check_dashboard()

    # 2. Buscar oportunidades de arbitraje
    check_arbitrage_opportunities()

    # 3. Obtener predicciones ML
    check_ml_predictions()

    # 4. Generar resumen diario
    generate_daily_summary()

    print("\n" + "="*60)
    print("MONITOREO COMPLETADO")
    print("="*60)

    print("\nProximos pasos:")
    print("   1. Revisar archivos generados en /validacion/")
    print("   2. Verificar manualmente oportunidades en Binance")
    print("   3. Actualizar Google Sheets con resultados")
    print("   4. Tomar screenshots del dashboard")

if __name__ == "__main__":
    main()
