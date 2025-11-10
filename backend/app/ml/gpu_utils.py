"""
Utilidades para detectar y usar GPU Intel Arc A750.
Detecta automáticamente si hay GPU disponible y configura PyTorch en consecuencia.
"""
import logging
import os

logger = logging.getLogger(__name__)

# Variables globales para estado de GPU
GPU_AVAILABLE = False
GPU_DEVICE = None
GPU_COUNT = 0
GPU_NAMES = []

try:
    import torch
    
    # Intentar importar Intel Extension
    try:
        import intel_extension_for_pytorch as ipex
        INTEL_EXTENSION_AVAILABLE = True
        logger.info("Intel Extension for PyTorch disponible")
    except ImportError:
        INTEL_EXTENSION_AVAILABLE = False
        logger.warning("Intel Extension for PyTorch no disponible - usando PyTorch estándar")
    except Exception as e:
        INTEL_EXTENSION_AVAILABLE = False
        logger.warning(f"Error al importar Intel Extension: {e} - usando PyTorch estándar")
    
    # Verificar si hay soporte XPU (GPU Intel)
    if INTEL_EXTENSION_AVAILABLE and hasattr(torch, 'xpu'):
        try:
            if torch.xpu.is_available():
                GPU_AVAILABLE = True
                GPU_COUNT = torch.xpu.device_count()
                GPU_DEVICE = torch.device('xpu:0')
                GPU_NAMES = [torch.xpu.get_device_name(i) for i in range(GPU_COUNT)]
                logger.info(f"✅ GPU Intel Arc disponible: {GPU_NAMES}")
                logger.info(f"   Dispositivos: {GPU_COUNT}")
            else:
                logger.info("GPU Intel Arc no disponible - usando CPU")
        except Exception as e:
            logger.warning(f"Error al verificar GPU: {e} - usando CPU")
    else:
        logger.info("Soporte XPU no disponible - usando CPU")
    
    # Configurar dispositivo por defecto
    if GPU_AVAILABLE:
        DEVICE = GPU_DEVICE
        logger.info(f"Usando dispositivo: {DEVICE}")
    else:
        DEVICE = torch.device('cpu')
        logger.info("Usando dispositivo: CPU")
        
except ImportError:
    logger.error("PyTorch no está instalado")
    INTEL_EXTENSION_AVAILABLE = False
    GPU_AVAILABLE = False
    DEVICE = None
except Exception as e:
    logger.error(f"Error al inicializar GPU: {e}")
    INTEL_EXTENSION_AVAILABLE = False
    GPU_AVAILABLE = False
    DEVICE = None


def get_device():
    """
    Obtiene el dispositivo disponible (GPU o CPU).
    
    Returns:
        torch.device: Dispositivo a usar
    """
    return DEVICE if DEVICE is not None else torch.device('cpu')


def to_device(tensor_or_model, device=None):
    """
    Mueve un tensor o modelo al dispositivo especificado.
    
    Args:
        tensor_or_model: Tensor o modelo de PyTorch
        device: Dispositivo (None = auto-detectar)
        
    Returns:
        Tensor o modelo en el dispositivo
    """
    if device is None:
        device = get_device()
    
    try:
        return tensor_or_model.to(device)
    except Exception as e:
        logger.warning(f"Error al mover a dispositivo {device}: {e} - usando CPU")
        return tensor_or_model.to('cpu')


def get_gpu_info():
    """
    Obtiene información sobre la GPU disponible.
    
    Returns:
        dict: Información de la GPU
    """
    info = {
        "available": GPU_AVAILABLE,
        "device": str(DEVICE) if DEVICE else "cpu",
        "count": GPU_COUNT,
        "names": GPU_NAMES,
        "intel_extension": INTEL_EXTENSION_AVAILABLE,
    }
    
    if GPU_AVAILABLE:
        try:
            import torch
            # Obtener memoria GPU
            if hasattr(torch.xpu, 'get_device_properties'):
                props = torch.xpu.get_device_properties(0)
                info["memory_total"] = getattr(props, 'total_memory', 'N/A')
        except Exception as e:
            logger.warning(f"Error al obtener información de GPU: {e}")
    
    return info


def optimize_model_for_inference(model):
    """
    Optimiza un modelo para inferencia usando Intel Extension si está disponible.
    
    Args:
        model: Modelo de PyTorch
        
    Returns:
        Modelo optimizado
    """
    if not INTEL_EXTENSION_AVAILABLE:
        return model
    
    try:
        import intel_extension_for_pytorch as ipex
        
        # Optimizar modelo para inferencia
        if GPU_AVAILABLE:
            # Optimizar para GPU
            model = ipex.optimize(model, device='xpu')
            logger.info("Modelo optimizado para GPU Intel Arc")
        else:
            # Optimizar para CPU
            model = ipex.optimize(model, device='cpu')
            logger.info("Modelo optimizado para CPU con Intel Extension")
        
        return model
    except Exception as e:
        logger.warning(f"Error al optimizar modelo: {e} - usando modelo estándar")
        return model


def print_gpu_status():
    """Imprime el estado actual de la GPU."""
    info = get_gpu_info()
    
    print("=" * 50)
    print("Estado de GPU Intel Arc A750")
    print("=" * 50)
    print(f"GPU Disponible: {'✅ Sí' if info['available'] else '❌ No'}")
    print(f"Dispositivo: {info['device']}")
    print(f"Intel Extension: {'✅ Instalado' if info['intel_extension'] else '❌ No instalado'}")
    
    if info['available']:
        print(f"Dispositivos GPU: {info['count']}")
        for i, name in enumerate(info['names']):
            print(f"  - GPU {i}: {name}")
    else:
        print("Modo: CPU (funciona perfectamente)")
    print("=" * 50)


if __name__ == "__main__":
    # Ejecutar para verificar estado
    print_gpu_status()

