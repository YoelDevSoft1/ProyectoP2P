"""
Script para entrenar modelos avanzados de ML con datos históricos.
Usa datos de la BD como fuente principal, con opción de Yahoo Finance.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

from app.core.database import SessionLocal
from app.models.price_history import PriceHistory
from app.ml.advanced_dl_service import AdvancedDLTrainer
from app.services.yahoo_finance_service import YahooFinanceService

def get_data_from_db(min_days: int = 200) -> pd.DataFrame:
    """Obtener datos históricos de la base de datos."""
    db = SessionLocal()
    try:
        # Obtener datos de los últimos N días
        cutoff_date = datetime.utcnow() - timedelta(days=min_days * 2)
        price_history = db.query(PriceHistory).filter(
            PriceHistory.timestamp >= cutoff_date
        ).order_by(PriceHistory.timestamp).all()
        
        if len(price_history) < min_days:
            print(f"⚠️  Solo {len(price_history)} registros en BD (se necesitan {min_days})")
            # Usar todos los datos disponibles
            price_history = db.query(PriceHistory).order_by(PriceHistory.timestamp).all()
        
        if len(price_history) == 0:
            raise ValueError("No hay datos en la base de datos")
        
        # Convertir a DataFrame
        data = pd.DataFrame([
            {
                "price": ph.price,
                "spread": ph.spread or 0,
                "volume": ph.volume or 0,
                "timestamp": ph.timestamp,
            }
            for ph in price_history
        ])
        
        print(f"✅ Obtenidos {len(data)} registros de la BD")
        return data
        
    finally:
        db.close()

def get_data_from_yahoo(symbol: str = "BTC-USD", period: str = "1y", 
                        interval: str = "1d") -> pd.DataFrame:
    """Obtener datos históricos de Yahoo Finance."""
    try:
        print(f"📊 Intentando obtener datos de Yahoo Finance para {symbol}...")
        yahoo_service = YahooFinanceService()
        
        # Determinar tipo de símbolo
        if "=X" in symbol or "/" in symbol:
            # Forex
            if "=X" in symbol:
                from_curr = symbol.split("=")[0][:3]
                to_curr = symbol.split("=")[0][3:]
            else:
                parts = symbol.split("/")
                from_curr = parts[0]
                to_curr = parts[1]
            data = yahoo_service.get_forex_data(from_curr, to_curr, period=period, interval=interval)
        else:
            # Crypto o Stock
            if "-" in symbol:
                data = yahoo_service.get_crypto_data(symbol, period=period, interval=interval, max_retries=3)
            else:
                data = yahoo_service.get_stock_data(symbol, period=period, interval=interval)
        
        if data is None or data.empty:
            raise ValueError(f"No se pudieron obtener datos de Yahoo Finance para {symbol}")
        
        # Preparar datos
        data = yahoo_service.prepare_data_for_training(data, target_col="close")
        print(f"✅ Obtenidos {len(data)} registros de Yahoo Finance")
        return data
        
    except Exception as e:
        print(f"❌ Error obteniendo datos de Yahoo Finance: {e}")
        raise

def train_transformer_model(data: pd.DataFrame, epochs: int = 50, 
                           batch_size: int = 32, learning_rate: float = 0.0001):
    """Entrenar modelo Transformer."""
    print("\n" + "="*60)
    print("🚀 Entrenando modelo Transformer...")
    print("="*60)
    
    trainer = AdvancedDLTrainer()
    result = trainer.train_transformer_model(
        data=data,
        epochs=epochs,
        batch_size=batch_size,
        learning_rate=learning_rate,
        target_col='price'
    )
    
    if result.get("status") == "success":
        print(f"✅ Modelo Transformer entrenado exitosamente!")
        print(f"   Test Loss: {result.get('test_loss', 'N/A'):.4f}")
        print(f"   Best Epoch: {result.get('best_epoch', 'N/A')}")
        if 'profit_metrics' in result:
            metrics = result['profit_metrics']
            print(f"   Sharpe Ratio: {metrics.get('sharpe_ratio', 'N/A'):.2f}")
    else:
        print(f"❌ Error entrenando modelo: {result.get('error', 'Unknown error')}")
    
    return result

def train_ensemble_model(data: pd.DataFrame, epochs: int = 30, 
                        batch_size: int = 32, learning_rate: float = 0.001):
    """Entrenar ensemble de modelos."""
    print("\n" + "="*60)
    print("🚀 Entrenando Ensemble de Modelos...")
    print("="*60)
    
    trainer = AdvancedDLTrainer()
    result = trainer.train_ensemble_model(
        data=data,
        epochs=epochs,
        batch_size=batch_size,
        learning_rate=learning_rate,
        target_col='price'
    )
    
    if result.get("status") == "success":
        print(f"✅ Ensemble entrenado exitosamente!")
        print(f"   Modelos: {', '.join(result.get('models', []))}")
        print(f"   Pesos: {result.get('weights', {})}")
    else:
        print(f"❌ Error entrenando ensemble: {result.get('error', 'Unknown error')}")
    
    return result

def main():
    """Función principal."""
    print("="*60)
    print("🎯 Entrenamiento de Modelos Avanzados de ML")
    print("="*60)
    
    # Configuración
    use_yahoo = False  # Cambiar a True para usar Yahoo Finance
    symbol = "BTC-USD"
    period = "1y"
    interval = "1d"
    epochs_transformer = 50
    epochs_ensemble = 30
    batch_size = 32
    
    try:
        # Obtener datos
        if use_yahoo:
            try:
                data = get_data_from_yahoo(symbol=symbol, period=period, interval=interval)
                data_source = "Yahoo Finance"
            except Exception as e:
                print(f"⚠️  Fallback a datos de BD: {e}")
                data = get_data_from_db(min_days=200)
                data_source = "Base de Datos"
        else:
            data = get_data_from_db(min_days=200)
            data_source = "Base de Datos"
        
        print(f"\n📊 Fuente de datos: {data_source}")
        print(f"   Registros: {len(data)}")
        print(f"   Período: {data['timestamp'].min()} - {data['timestamp'].max()}")
        
        if len(data) < 200:
            print(f"⚠️  Advertencia: Solo {len(data)} registros (se recomiendan al menos 200)")
        
        # Entrenar modelos
        print("\n" + "="*60)
        print("🎯 ¿Qué modelo deseas entrenar?")
        print("="*60)
        print("1. Transformer (Recomendado)")
        print("2. Ensemble (Máxima Robustez)")
        print("3. Ambos")
        
        choice = input("\nSelecciona opción (1/2/3): ").strip()
        
        if choice == "1" or choice == "3":
            train_transformer_model(data, epochs=epochs_transformer, 
                                  batch_size=batch_size, learning_rate=0.0001)
        
        if choice == "2" or choice == "3":
            train_ensemble_model(data, epochs=epochs_ensemble, 
                               batch_size=batch_size, learning_rate=0.001)
        
        print("\n" + "="*60)
        print("✅ Entrenamiento completado!")
        print("="*60)
        print("\n📁 Modelos guardados en: ml_models/dl_advanced/")
        print("🚀 Puedes usar los modelos para predicciones ahora")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())

