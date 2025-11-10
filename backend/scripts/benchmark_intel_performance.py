"""
Script de benchmarking para comparar rendimiento con y sin Intel Extension.
Mide tiempo de entrenamiento y predicción de modelos de Deep Learning.
"""
import time
import torch
import numpy as np
import pandas as pd
from pathlib import Path
import logging
import sys

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.ml.gpu_utils import get_device, get_gpu_info, to_device
from app.ml.dl_models import create_lstm_model
from app.ml.advanced_models import create_transformer_model
from torch.utils.data import DataLoader, TensorDataset

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_synthetic_data(n_samples=1000, sequence_length=20, n_features=10):
    """Genera datos sintéticos para testing."""
    # Generar secuencias temporales sintéticas
    sequences = np.random.randn(n_samples, sequence_length, n_features).astype(np.float32)
    targets = np.random.randn(n_samples, 1).astype(np.float32)
    return sequences, targets


def benchmark_training(model, train_loader, device, epochs=10):
    """Mide el tiempo de entrenamiento de un modelo."""
    model = to_device(model, device)
    criterion = torch.nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    
    model.train()
    start_time = time.time()
    
    for epoch in range(epochs):
        epoch_loss = 0
        for batch_sequences, batch_targets in train_loader:
            batch_sequences = to_device(batch_sequences, device)
            batch_targets = to_device(batch_targets, device)
            
            optimizer.zero_grad()
            outputs = model(batch_sequences)
            loss = criterion(outputs, batch_targets)
            loss.backward()
            optimizer.step()
            
            epoch_loss += loss.item()
        
        if (epoch + 1) % 5 == 0:
            logger.info(f"Epoch {epoch + 1}/{epochs}, Loss: {epoch_loss / len(train_loader):.4f}")
    
    end_time = time.time()
    training_time = end_time - start_time
    
    return training_time, epoch_loss / len(train_loader)


def benchmark_inference(model, test_loader, device, n_iterations=100):
    """Mide el tiempo de inferencia de un modelo."""
    model = to_device(model, device)
    model.eval()
    
    times = []
    
    with torch.no_grad():
        for i in range(n_iterations):
            # Obtener un batch de prueba
            batch_sequences, _ = next(iter(test_loader))
            batch_sequences = to_device(batch_sequences, device)
            
            start_time = time.time()
            outputs = model(batch_sequences)
            end_time = time.time()
            
            # Sincronizar si es GPU
            if device.type != 'cpu':
                torch.xpu.synchronize() if hasattr(torch, 'xpu') else torch.cuda.synchronize()
            
            inference_time = (end_time - start_time) * 1000  # Convertir a ms
            times.append(inference_time)
    
    avg_time = np.mean(times)
    std_time = np.std(times)
    min_time = np.min(times)
    max_time = np.max(times)
    
    return avg_time, std_time, min_time, max_time


def benchmark_matrix_operations(device, n_iterations=100):
    """Mide el rendimiento de operaciones de matriz."""
    device_obj = get_device() if device is None else torch.device(device)
    
    times = []
    
    for i in range(n_iterations):
        # Crear matrices grandes
        a = torch.randn(1000, 1000, device=device_obj)
        b = torch.randn(1000, 1000, device=device_obj)
        
        start_time = time.time()
        c = torch.matmul(a, b)
        
        # Sincronizar si es GPU
        if device_obj.type != 'cpu':
            torch.xpu.synchronize() if hasattr(torch, 'xpu') else torch.cuda.synchronize()
        
        end_time = time.time()
        times.append((end_time - start_time) * 1000)  # ms
    
    avg_time = np.mean(times)
    return avg_time


def run_benchmark():
    """Ejecuta el benchmark completo."""
    print("=" * 80)
    print("🚀 BENCHMARK DE RENDIMIENTO: Intel Extension vs PyTorch Estándar")
    print("=" * 80)
    
    # Información del dispositivo
    gpu_info = get_gpu_info()
    device = get_device()
    
    print(f"\n📊 Información del Dispositivo:")
    print(f"   - Dispositivo: {device}")
    print(f"   - GPU Disponible: {'✅ Sí' if gpu_info['available'] else '❌ No'}")
    print(f"   - Intel Extension: {'✅ Instalado' if gpu_info.get('intel_extension', False) else '❌ No instalado'}")
    if gpu_info['available']:
        print(f"   - GPU: {gpu_info.get('names', ['Unknown'])[0]}")
    print()
    
    # Verificar Intel Extension
    try:
        import intel_extension_for_pytorch as ipex
        intel_extension_available = True
        print(f"✅ Intel Extension for PyTorch: {ipex.__version__}")
    except ImportError:
        intel_extension_available = False
        print("⚠️  Intel Extension for PyTorch no está instalado")
    print()
    
    # Generar datos de prueba
    print("📦 Generando datos de prueba...")
    n_samples = 500
    sequence_length = 20
    n_features = 10
    sequences, targets = generate_synthetic_data(n_samples, sequence_length, n_features)
    
    # Convertir a tensores
    sequences_tensor = torch.FloatTensor(sequences)
    targets_tensor = torch.FloatTensor(targets)
    
    # Crear dataloaders
    train_dataset = TensorDataset(sequences_tensor, targets_tensor)
    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
    test_loader = DataLoader(train_dataset, batch_size=32, shuffle=False)
    
    results = {}
    
    # Benchmark 1: Entrenamiento LSTM
    print("\n" + "=" * 80)
    print("📊 Benchmark 1: Entrenamiento LSTM")
    print("=" * 80)
    
    try:
        model_lstm = create_lstm_model(
            input_size=n_features,
            hidden_size=64,
            num_layers=2,
            output_size=1
        )
        
        training_time, final_loss = benchmark_training(model_lstm, train_loader, device, epochs=10)
        results['lstm_training'] = training_time
        
        print(f"✅ Entrenamiento LSTM completado:")
        print(f"   - Tiempo: {training_time:.2f} segundos")
        print(f"   - Loss final: {final_loss:.4f}")
        
    except Exception as e:
        print(f"❌ Error en entrenamiento LSTM: {e}")
        results['lstm_training'] = None
    
    # Benchmark 2: Inferencia LSTM
    print("\n" + "=" * 80)
    print("📊 Benchmark 2: Inferencia LSTM")
    print("=" * 80)
    
    try:
        model_lstm = create_lstm_model(
            input_size=n_features,
            hidden_size=64,
            num_layers=2,
            output_size=1
        )
        
        avg_time, std_time, min_time, max_time = benchmark_inference(
            model_lstm, test_loader, device, n_iterations=100
        )
        results['lstm_inference'] = avg_time
        
        print(f"✅ Inferencia LSTM completada:")
        print(f"   - Tiempo promedio: {avg_time:.2f} ms")
        print(f"   - Desviación estándar: {std_time:.2f} ms")
        print(f"   - Mínimo: {min_time:.2f} ms")
        print(f"   - Máximo: {max_time:.2f} ms")
        
    except Exception as e:
        print(f"❌ Error en inferencia LSTM: {e}")
        results['lstm_inference'] = None
    
    # Benchmark 3: Operaciones de Matriz
    print("\n" + "=" * 80)
    print("📊 Benchmark 3: Operaciones de Matriz")
    print("=" * 80)
    
    try:
        matrix_time = benchmark_matrix_operations(device, n_iterations=100)
        results['matrix_operations'] = matrix_time
        
        print(f"✅ Operaciones de matriz completadas:")
        print(f"   - Tiempo promedio (matmul 1000x1000): {matrix_time:.2f} ms")
        
    except Exception as e:
        print(f"❌ Error en operaciones de matriz: {e}")
        results['matrix_operations'] = None
    
    # Benchmark 4: Transformer (si está disponible)
    print("\n" + "=" * 80)
    print("📊 Benchmark 4: Entrenamiento Transformer")
    print("=" * 80)
    
    try:
        model_transformer = create_transformer_model(
            input_size=n_features,
            d_model=64,
            nhead=4,
            num_layers=2,
            dim_feedforward=256,
            dropout=0.1,
            seq_len=sequence_length
        )
        
        training_time, final_loss = benchmark_training(model_transformer, train_loader, device, epochs=5)
        results['transformer_training'] = training_time
        
        print(f"✅ Entrenamiento Transformer completado:")
        print(f"   - Tiempo: {training_time:.2f} segundos")
        print(f"   - Loss final: {final_loss:.4f}")
        
    except Exception as e:
        print(f"❌ Error en entrenamiento Transformer: {e}")
        results['transformer_training'] = None
    
    # Resumen de resultados
    print("\n" + "=" * 80)
    print("📊 RESUMEN DE RESULTADOS")
    print("=" * 80)
    
    print(f"\n🔧 Configuración:")
    print(f"   - Dispositivo: {device}")
    print(f"   - Intel Extension: {'✅ Disponible' if intel_extension_available else '❌ No disponible'}")
    print(f"   - GPU: {'✅ Disponible' if gpu_info['available'] else '❌ No disponible'}")
    
    print(f"\n⏱️  Tiempos de Ejecución:")
    if results.get('lstm_training'):
        print(f"   - Entrenamiento LSTM: {results['lstm_training']:.2f} segundos")
    if results.get('lstm_inference'):
        print(f"   - Inferencia LSTM: {results['lstm_inference']:.2f} ms")
    if results.get('matrix_operations'):
        print(f"   - Operaciones de matriz: {results['matrix_operations']:.2f} ms")
    if results.get('transformer_training'):
        print(f"   - Entrenamiento Transformer: {results['transformer_training']:.2f} segundos")
    
    print("\n" + "=" * 80)
    print("✅ Benchmark completado!")
    print("=" * 80)
    
    return results


if __name__ == "__main__":
    try:
        results = run_benchmark()
    except KeyboardInterrupt:
        print("\n\n⚠️  Benchmark interrumpido por el usuario")
    except Exception as e:
        logger.error(f"Error en benchmark: {e}", exc_info=True)
        print(f"\n❌ Error en benchmark: {e}")

