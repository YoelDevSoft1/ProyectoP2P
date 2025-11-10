"""
Módulo de Machine Learning para predicciones.
Incluye modelos tradicionales (scikit-learn) y Deep Learning (PyTorch).
Incluye modelos avanzados con las últimas técnicas (Transformers, Attention, etc.).
"""
from app.ml.trainer import MLModelTrainer, MLPredictor
from app.ml.gpu_utils import get_device, to_device, get_gpu_info, optimize_model_for_inference

# Importar DL solo si PyTorch está disponible
try:
    from app.ml.dl_service import DLModelTrainer, DLPredictor
    DL_AVAILABLE = True
except ImportError:
    DL_AVAILABLE = False
    DLModelTrainer = None
    DLPredictor = None

# Importar modelos avanzados
try:
    from app.ml.advanced_dl_service import AdvancedDLTrainer
    from app.ml.feature_engineering import AdvancedFeatureEngineer
    from app.ml.profit_metrics import ProfitMetricsCalculator
    from app.ml.backtesting_service import BacktestingService
    ADVANCED_DL_AVAILABLE = True
except ImportError as e:
    ADVANCED_DL_AVAILABLE = False
    AdvancedDLTrainer = None
    AdvancedFeatureEngineer = None
    ProfitMetricsCalculator = None
    BacktestingService = None
    logger = __import__('logging').getLogger(__name__)
    logger.warning(f"Advanced DL modules not available: {e}")

__all__ = [
    "MLModelTrainer",
    "MLPredictor",
    "get_device",
    "to_device",
    "get_gpu_info",
    "optimize_model_for_inference",
]

if DL_AVAILABLE:
    __all__.extend(["DLModelTrainer", "DLPredictor"])

if ADVANCED_DL_AVAILABLE:
    __all__.extend([
        "AdvancedDLTrainer",
        "AdvancedFeatureEngineer",
        "ProfitMetricsCalculator",
        "BacktestingService"
    ])
