"""Script simple para probar rendimiento."""
import torch
import sys
import time
import numpy as np
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.ml.gpu_utils import get_device, get_gpu_info

print("=" * 80)
print("🚀 TEST DE RENDIMIENTO: Intel Extension vs PyTorch Estándar")
print("=" * 80)
print()

# Información del dispositivo
gpu_info = get_gpu_info()
device = get_device()

print(f"📊 Información del Dispositivo:")
print(f"   - PyTorch version: {torch.__version__}")
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

# Test 1: Operaciones de matriz
print("=" * 80)
print("📊 Test 1: Operaciones de Matriz (Matrix Multiplication)")
print("=" * 80)

try:
    # Crear matrices grandes
    size = 1000
    a = torch.randn(size, size, device=device)
    b = torch.randn(size, size, device=device)
    
    # Warmup
    for _ in range(10):
        _ = torch.matmul(a, b)
    
    # Medir tiempo
    n_iterations = 100
    times = []
    
    for i in range(n_iterations):
        start_time = time.time()
        c = torch.matmul(a, b)
        
        # Sincronizar si es GPU
        if device.type != 'cpu':
            if hasattr(torch, 'xpu'):
                torch.xpu.synchronize()
            elif hasattr(torch, 'cuda'):
                torch.cuda.synchronize()
        
        end_time = time.time()
        times.append((end_time - start_time) * 1000)  # ms
    
    avg_time = np.mean(times)
    std_time = np.std(times)
    
    print(f"✅ Operaciones de matriz completadas:")
    print(f"   - Tamaño de matriz: {size}x{size}")
    print(f"   - Iteraciones: {n_iterations}")
    print(f"   - Tiempo promedio: {avg_time:.2f} ms")
    print(f"   - Desviación estándar: {std_time:.2f} ms")
    print(f"   - Operaciones/segundo: {1000/avg_time:.2f}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

# Test 2: Operaciones LSTM simples
print()
print("=" * 80)
print("📊 Test 2: Operaciones LSTM")
print("=" * 80)

try:
    from app.ml.dl_models import create_lstm_model
    
    # Crear modelo LSTM
    model = create_lstm_model(input_size=10, hidden_size=64, num_layers=2, output_size=1)
    model = model.to(device)
    model.eval()
    
    # Crear datos de prueba
    batch_size = 32
    sequence_length = 20
    n_features = 10
    test_data = torch.randn(batch_size, sequence_length, n_features, device=device)
    
    # Warmup
    for _ in range(10):
        with torch.no_grad():
            _ = model(test_data)
    
    # Medir tiempo de inferencia
    n_iterations = 100
    times = []
    
    for i in range(n_iterations):
        start_time = time.time()
        with torch.no_grad():
            output = model(test_data)
        
        # Sincronizar si es GPU
        if device.type != 'cpu':
            if hasattr(torch, 'xpu'):
                torch.xpu.synchronize()
            elif hasattr(torch, 'cuda'):
                torch.cuda.synchronize()
        
        end_time = time.time()
        times.append((end_time - start_time) * 1000)  # ms
    
    avg_time = np.mean(times)
    std_time = np.std(times)
    
    print(f"✅ Inferencia LSTM completada:")
    print(f"   - Batch size: {batch_size}")
    print(f"   - Sequence length: {sequence_length}")
    print(f"   - Features: {n_features}")
    print(f"   - Iteraciones: {n_iterations}")
    print(f"   - Tiempo promedio: {avg_time:.2f} ms")
    print(f"   - Desviación estándar: {std_time:.2f} ms")
    print(f"   - Predicciones/segundo: {1000/avg_time:.2f}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Entrenamiento simple
print()
print("=" * 80)
print("📊 Test 3: Entrenamiento LSTM (mini-batch)")
print("=" * 80)

try:
    from app.ml.dl_models import create_lstm_model
    
    # Crear modelo LSTM
    model = create_lstm_model(input_size=10, hidden_size=64, num_layers=2, output_size=1)
    model = model.to(device)
    model.train()
    
    # Crear datos de entrenamiento
    batch_size = 32
    sequence_length = 20
    n_features = 10
    train_data = torch.randn(batch_size, sequence_length, n_features, device=device)
    train_targets = torch.randn(batch_size, 1, device=device)
    
    # Optimizador y loss
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    criterion = torch.nn.MSELoss()
    
    # Warmup
    for _ in range(5):
        optimizer.zero_grad()
        output = model(train_data)
        loss = criterion(output, train_targets)
        loss.backward()
        optimizer.step()
    
    # Medir tiempo de entrenamiento
    n_epochs = 50
    start_time = time.time()
    
    for epoch in range(n_epochs):
        optimizer.zero_grad()
        output = model(train_data)
        loss = criterion(output, train_targets)
        loss.backward()
        optimizer.step()
    
    # Sincronizar si es GPU
    if device.type != 'cpu':
        if hasattr(torch, 'xpu'):
            torch.xpu.synchronize()
        elif hasattr(torch, 'cuda'):
            torch.cuda.synchronize()
    
    end_time = time.time()
    training_time = end_time - start_time
    final_loss = loss.item()
    
    print(f"✅ Entrenamiento LSTM completado:")
    print(f"   - Epochs: {n_epochs}")
    print(f"   - Batch size: {batch_size}")
    print(f"   - Tiempo total: {training_time:.2f} segundos")
    print(f"   - Tiempo por epoch: {training_time/n_epochs*1000:.2f} ms")
    print(f"   - Loss final: {final_loss:.4f}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

# Resumen
print()
print("=" * 80)
print("📊 RESUMEN")
print("=" * 80)
print(f"✅ Tests completados con dispositivo: {device}")
print(f"✅ Intel Extension: {'Disponible' if intel_extension_available else 'No disponible'}")
print(f"✅ GPU: {'Disponible' if gpu_info['available'] else 'No disponible'}")
print()
print("=" * 80)

