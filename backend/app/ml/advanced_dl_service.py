"""
Servicio Avanzado de Deep Learning con las últimas técnicas.
Incluye: Transformers, Attention, Ensemble, Feature Engineering, Profit Metrics.
"""
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import numpy as np
import pandas as pd
from pathlib import Path
import logging
from typing import Optional, Dict, List, Tuple
import joblib
from sklearn.preprocessing import MinMaxScaler, StandardScaler
from sklearn.model_selection import TimeSeriesSplit
import warnings

# Suprimir advertencias de NumPy sobre valores infinitos
warnings.filterwarnings('ignore', category=RuntimeWarning)

from app.ml.gpu_utils import get_device, to_device, optimize_model_for_inference
from app.ml.advanced_models import (
    create_transformer_model, create_attention_lstm, create_residual_lstm,
    create_hybrid_model, create_profit_aware_model
)
from app.ml.feature_engineering import AdvancedFeatureEngineer
from app.ml.profit_metrics import ProfitMetricsCalculator

logger = logging.getLogger(__name__)


class AdvancedTimeSeriesDataset(Dataset):
    """Dataset avanzado para series temporales con múltiples features."""
    
    def __init__(self, sequences: np.ndarray, targets: Optional[np.ndarray] = None):
        """
        Args:
            sequences: Array de forma (n_samples, sequence_length, n_features) - secuencias ya creadas
            targets: Array de forma (n_samples,) - targets ya alineados con las secuencias
        """
        self.sequences = sequences
        self.targets = targets
        
    def __len__(self):
        return len(self.sequences)
    
    def __getitem__(self, idx):
        sequence = self.sequences[idx]
        if self.targets is not None:
            target = self.targets[idx]
            return torch.FloatTensor(sequence), torch.FloatTensor([target])
        return torch.FloatTensor(sequence)


class AdvancedDLTrainer:
    """Entrenador avanzado de modelos de Deep Learning."""
    
    def __init__(self, model_dir: Path = Path("ml_models/dl_advanced")):
        self.model_dir = model_dir
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.device = get_device()
        self.feature_engineer = AdvancedFeatureEngineer()
        self.profit_calculator = ProfitMetricsCalculator()
        logger.info(f"AdvancedDLTrainer initialized with device: {self.device}")
    
    def prepare_advanced_data(self, df: pd.DataFrame, target_col: str,
                             sequence_length: int = 20,
                             train_ratio: float = 0.8,
                             val_ratio: float = 0.1) -> Tuple:
        """Preparar datos con features avanzadas."""
        # Crear features avanzadas
        df = self.feature_engineer.create_all_features(df)
        
        # Obtener lista de features
        feature_cols = self.feature_engineer.get_feature_list(include_profit=False)
        feature_cols = [col for col in feature_cols if col in df.columns]
        
        # Limpiar datos: eliminar infinitos y valores muy grandes
        df = df.replace([np.inf, -np.inf], np.nan)
        df = df.dropna()
        
        # Limpiar valores extremos de manera más conservadora
        for col in feature_cols:
            if col in df.columns:
                # Usar percentiles para detectar outliers
                q01 = df[col].quantile(0.01)
                q99 = df[col].quantile(0.99)
                iqr = q99 - q01
                
                # Si hay valores extremos, usar un rango más conservador
                if iqr > 0:
                    lower_bound = q01 - 3 * iqr
                    upper_bound = q99 + 3 * iqr
                    df[col] = df[col].clip(lower=lower_bound, upper=upper_bound)
                
                # Asegurar que no haya valores infinitos
                df[col] = df[col].replace([np.inf, -np.inf], np.nan)
        
        if len(df) < sequence_length + 1:
            raise ValueError(f"Not enough data. Need at least {sequence_length + 1} samples")
        
        # Normalizar features
        scaler = StandardScaler()
        features = df[feature_cols].values
        
        # Verificar que no haya infinitos antes de escalar
        if np.isinf(features).any() or np.isnan(features).any():
            logger.warning("Found inf or nan values in features, replacing with 0")
            features = np.nan_to_num(features, nan=0.0, posinf=0.0, neginf=0.0)
        
        features_scaled = scaler.fit_transform(features)
        
        # Verificar que el escalado no haya creado infinitos
        if np.isinf(features_scaled).any() or np.isnan(features_scaled).any():
            logger.warning("Found inf or nan values after scaling, replacing with 0")
            features_scaled = np.nan_to_num(features_scaled, nan=0.0, posinf=0.0, neginf=0.0)
        
        # Targets - normalizar con StandardScaler para evitar valores extremos
        targets = df[target_col].values.copy()
        
        # Reemplazar infinitos y NaN
        targets = np.nan_to_num(targets, nan=0.0, posinf=0.0, neginf=0.0)
        
        # Normalizar targets también para entrenamiento estable
        target_scaler = StandardScaler()
        targets_scaled = target_scaler.fit_transform(targets.reshape(-1, 1)).flatten()
        
        # Guardar información de escalado para desnormalizar después
        target_scaling_info = {
            'scaler': target_scaler,
            'target_mean': float(target_scaler.mean_[0]),
            'target_std': float(target_scaler.scale_[0]),
            'use_scaling': True
        }
        
        logger.info(f"Targets normalizados: mean={target_scaling_info['target_mean']:.2f}, std={target_scaling_info['target_std']:.2f}")
        
        # Crear secuencias
        X, y = [], []
        for i in range(len(features_scaled) - sequence_length + 1):
            X.append(features_scaled[i:i + sequence_length])
            y.append(targets_scaled[i + sequence_length - 1])
        
        X = np.array(X)
        y = np.array(y)
        
        # Verificar dimensiones
        if len(X) == 0:
            raise ValueError("No se pudieron crear secuencias. Datos insuficientes.")
        
        logger.info(f"Secuencias creadas: {len(X)} muestras, forma X: {X.shape}, forma y: {y.shape}")
        
        # Dividir en train/val/test
        n_train = int(len(X) * train_ratio)
        n_val = int(len(X) * val_ratio)
        
        X_train = X[:n_train]
        X_val = X[n_train:n_train + n_val]
        X_test = X[n_train + n_val:]
        
        y_train = y[:n_train]
        y_val = y[n_train:n_train + n_val]
        y_test = y[n_train + n_val:]
        
        return (X_train, X_val, X_test, y_train, y_val, y_test, 
                scaler, feature_cols, target_scaling_info)
    
    def train_transformer_model(self, data: pd.DataFrame, epochs: int = 100,
                               batch_size: int = 32, learning_rate: float = 0.0001,
                               target_col: str = 'price') -> Dict:
        """Entrenar modelo Transformer avanzado."""
        try:
            logger.info("Training advanced Transformer model")
            
            # Preparar datos
            X_train, X_val, X_test, y_train, y_val, y_test, scaler, feature_cols, target_scaling_info = \
                self.prepare_advanced_data(data, target_col, sequence_length=20)
            
            input_size = len(feature_cols)
            
            # Crear modelo
            model = create_transformer_model(
                input_size=input_size,
                d_model=128,
                nhead=8,
                num_layers=4,
                dim_feedforward=512,
                dropout=0.1,
                output_size=1
            )
            
            # Dataset y DataLoader - las secuencias ya están creadas
            train_dataset = AdvancedTimeSeriesDataset(X_train, y_train)
            val_dataset = AdvancedTimeSeriesDataset(X_val, y_val)
            test_dataset = AdvancedTimeSeriesDataset(X_test, y_test)
            
            train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
            val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
            test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)
            
            # Optimizador y loss
            criterion = nn.MSELoss()
            optimizer = optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=0.01)
            scheduler = optim.lr_scheduler.ReduceLROnPlateau(
                optimizer, mode='min', factor=0.5, patience=10, verbose=True
            )
            
            # Early stopping
            best_val_loss = float('inf')
            patience = 20
            patience_counter = 0
            
            # Entrenamiento
            train_losses = []
            val_losses = []
            
            for epoch in range(epochs):
                # Train
                model.train()
                epoch_train_loss = 0
                for batch_x, batch_y in train_loader:
                    batch_x = to_device(batch_x, self.device)
                    batch_y = to_device(batch_y, self.device)
                    
                    optimizer.zero_grad()
                    outputs = model(batch_x)
                    loss = criterion(outputs, batch_y)
                    loss.backward()
                    torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
                    optimizer.step()
                    
                    epoch_train_loss += loss.item()
                
                avg_train_loss = epoch_train_loss / len(train_loader)
                train_losses.append(avg_train_loss)
                
                # Validation
                model.eval()
                epoch_val_loss = 0
                with torch.no_grad():
                    for batch_x, batch_y in val_loader:
                        batch_x = to_device(batch_x, self.device)
                        batch_y = to_device(batch_y, self.device)
                        outputs = model(batch_x)
                        loss = criterion(outputs, batch_y)
                        epoch_val_loss += loss.item()
                
                avg_val_loss = epoch_val_loss / len(val_loader)
                val_losses.append(avg_val_loss)
                
                # Scheduler
                scheduler.step(avg_val_loss)
                
                # Early stopping
                if avg_val_loss < best_val_loss:
                    best_val_loss = avg_val_loss
                    patience_counter = 0
                    # Guardar mejor modelo
                    best_model_state = model.state_dict().copy()
                else:
                    patience_counter += 1
                
                if (epoch + 1) % 10 == 0:
                    logger.info(f"Epoch {epoch + 1}/{epochs}, Train Loss: {avg_train_loss:.4f}, "
                              f"Val Loss: {avg_val_loss:.4f}")
                
                if patience_counter >= patience:
                    logger.info(f"Early stopping at epoch {epoch + 1}")
                    break
            
            # Cargar mejor modelo
            model.load_state_dict(best_model_state)
            
            # Evaluación en test
            model.eval()
            test_loss = 0
            test_predictions = []
            test_targets = []
            
            with torch.no_grad():
                for batch_x, batch_y in test_loader:
                    batch_x = to_device(batch_x, self.device)
                    batch_y = to_device(batch_y, self.device)
                    outputs = model(batch_x)
                    loss = criterion(outputs, batch_y)
                    test_loss += loss.item()
                    test_predictions.extend(outputs.cpu().numpy())
                    test_targets.extend(batch_y.cpu().numpy())
            
            test_loss /= len(test_loader)
            test_predictions_scaled = np.array(test_predictions).flatten()
            test_targets_scaled = np.array(test_targets).flatten()
            
            # Desnormalizar predicciones y targets para métricas
            if target_scaling_info and target_scaling_info.get('use_scaling', False):
                target_scaler = target_scaling_info['scaler']
                test_predictions_original = target_scaler.inverse_transform(test_predictions_scaled.reshape(-1, 1)).flatten()
                test_targets_original = target_scaler.inverse_transform(test_targets_scaled.reshape(-1, 1)).flatten()
            else:
                test_predictions_original = test_predictions_scaled
                test_targets_original = test_targets_scaled
            
            # Calcular métricas de profit con valores originales
            test_prices = pd.Series(test_targets_original)
            test_pred_prices = pd.Series(test_predictions_original)
            
            # Calcular returns solo si hay suficientes datos
            if len(test_prices) > 1:
                test_returns = test_prices.pct_change().dropna()
                if len(test_returns) > 0:
                    profit_metrics = self.profit_calculator.calculate_all_metrics(
                        prices=test_prices,
                        returns=test_returns,
                        period='daily'
                    )
                else:
                    profit_metrics = {}
            else:
                profit_metrics = {}
            
            # Guardar modelo, scaler e información de escalado
            model_path = self.model_dir / "transformer_advanced.pth"
            scaler_path = self.model_dir / "transformer_scaler.pkl"
            torch.save(model.state_dict(), model_path)
            joblib.dump(scaler, scaler_path)
            joblib.dump(feature_cols, self.model_dir / "transformer_features.pkl")
            joblib.dump(target_scaling_info, self.model_dir / "transformer_target_scaling.pkl")
            
            # Optimizar para inferencia
            model = optimize_model_for_inference(model)
            
            logger.info(f"Transformer model trained. Test loss: {test_loss:.4f}")
            logger.info(f"Profit metrics: {profit_metrics}")
            
            return {
                "status": "success",
                "model": "transformer",
                "test_loss": float(test_loss),
                "train_losses": train_losses,
                "val_losses": val_losses,
                "profit_metrics": profit_metrics,
                "model_path": str(model_path),
                "scaler_path": str(scaler_path),
                "device": str(self.device),
                "best_epoch": epoch - patience_counter + 1
            }
            
        except Exception as e:
            logger.error(f"Error training transformer model: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}
    
    def train_profit_aware_model(self, data: pd.DataFrame, epochs: int = 100,
                                batch_size: int = 32, learning_rate: float = 0.001,
                                target_col: str = 'price') -> Dict:
        """Entrenar modelo que predice profit directamente."""
        try:
            logger.info("Training profit-aware model")
            
            # Preparar datos
            X_train, X_val, X_test, y_train, y_val, y_test, scaler, feature_cols, target_scaling_info = \
                self.prepare_advanced_data(data, target_col, sequence_length=20)
            
            input_size = len(feature_cols)
            
            # Crear modelo
            model = create_profit_aware_model(
                input_size=input_size,
                hidden_size=128,
                num_layers=3,
                dropout=0.2
            )
            
            # Dataset - las secuencias ya están creadas
            train_dataset = AdvancedTimeSeriesDataset(X_train, y_train)
            val_dataset = AdvancedTimeSeriesDataset(X_val, y_val)
            test_dataset = AdvancedTimeSeriesDataset(X_test, y_test)
            
            train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
            val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
            test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)
            
            # Optimizador y loss
            price_criterion = nn.MSELoss()
            profit_criterion = nn.MSELoss()
            risk_criterion = nn.BCELoss()
            confidence_criterion = nn.BCELoss()
            
            optimizer = optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=0.01)
            
            # Entrenamiento
            train_losses = []
            
            for epoch in range(epochs):
                model.train()
                epoch_loss = 0
                
                for batch_x, batch_y in train_loader:
                    batch_x = to_device(batch_x, self.device)
                    batch_y = to_device(batch_y, self.device)
                    
                    optimizer.zero_grad()
                    outputs = model(batch_x)
                    
                    # Loss combinado
                    price_loss = price_criterion(outputs['price'], batch_y)
                    # Profit loss (usar diferencia)
                    profit_target = batch_y - batch_y.mean()  # Normalizar
                    profit_loss = profit_criterion(outputs['profit'], profit_target)
                    
                    # Loss total
                    loss = price_loss + 0.5 * profit_loss
                    loss.backward()
                    torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
                    optimizer.step()
                    
                    epoch_loss += loss.item()
                
                avg_loss = epoch_loss / len(train_loader)
                train_losses.append(avg_loss)
                
                if (epoch + 1) % 10 == 0:
                    logger.info(f"Epoch {epoch + 1}/{epochs}, Loss: {avg_loss:.4f}")
            
            # Guardar modelo
            model_path = self.model_dir / "profit_aware_model.pth"
            torch.save(model.state_dict(), model_path)
            joblib.dump(scaler, self.model_dir / "profit_aware_scaler.pkl")
            joblib.dump(feature_cols, self.model_dir / "profit_aware_features.pkl")
            joblib.dump(target_scaling_info, self.model_dir / "profit_aware_target_scaling.pkl")
            
            logger.info(f"Profit-aware model trained")
            
            return {
                "status": "success",
                "model": "profit_aware",
                "train_losses": train_losses,
                "model_path": str(model_path),
                "device": str(self.device)
            }
            
        except Exception as e:
            logger.error(f"Error training profit-aware model: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}
    
    def train_ensemble_model(self, data: pd.DataFrame, epochs: int = 50,
                           batch_size: int = 32, learning_rate: float = 0.001,
                           target_col: str = 'price') -> Dict:
        """Entrenar ensemble de múltiples modelos."""
        try:
            logger.info("Training ensemble of models")
            
            # Preparar datos
            X_train, X_val, X_test, y_train, y_val, y_test, scaler, feature_cols, target_scaling_info = \
                self.prepare_advanced_data(data, target_col, sequence_length=20)
            
            input_size = len(feature_cols)
            
            # Crear múltiples modelos
            seq_len = X_train.shape[1]  # Longitud de secuencia
            models = {
                'transformer': create_transformer_model(
                    input_size=input_size, 
                    d_model=128, 
                    nhead=8, 
                    num_layers=4, 
                    dim_feedforward=512,
                    dropout=0.1, 
                    output_size=1
                ),
                'attention_lstm': create_attention_lstm(
                    input_size=input_size, 
                    hidden_size=128, 
                    num_layers=2, 
                    output_size=1, 
                    dropout=0.2
                ),
                'residual_lstm': create_residual_lstm(
                    input_size=input_size, 
                    hidden_size=128, 
                    num_layers=3, 
                    output_size=1, 
                    dropout=0.2
                ),
                'hybrid': create_hybrid_model(
                    input_size=input_size, 
                    hidden_size=128, 
                    output_size=1, 
                    dropout=0.2
                )
            }
            
            # Entrenar cada modelo - las secuencias ya están creadas
            train_dataset = AdvancedTimeSeriesDataset(X_train, y_train)
            val_dataset = AdvancedTimeSeriesDataset(X_val, y_val)
            train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
            val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
            
            trained_models = {}
            model_weights = {}
            
            for name, model in models.items():
                logger.info(f"Training {name}...")
                criterion = nn.MSELoss()
                optimizer = optim.Adam(model.parameters(), lr=learning_rate)
                
                best_val_loss = float('inf')
                patience = 15
                patience_counter = 0
                
                for epoch in range(epochs):
                    # Train
                    model.train()
                    for batch_x, batch_y in train_loader:
                        batch_x = to_device(batch_x, self.device)
                        batch_y = to_device(batch_y, self.device)
                        optimizer.zero_grad()
                        if name == 'attention_lstm':
                            outputs, _ = model(batch_x)
                        else:
                            outputs = model(batch_x)
                        loss = criterion(outputs, batch_y)
                        loss.backward()
                        optimizer.step()
                    
                    # Validate
                    model.eval()
                    val_loss = 0
                    with torch.no_grad():
                        for batch_x, batch_y in val_loader:
                            batch_x = to_device(batch_x, self.device)
                            batch_y = to_device(batch_y, self.device)
                            try:
                                if name == 'attention_lstm':
                                    outputs, _ = model(batch_x)
                                else:
                                    outputs = model(batch_x)
                                loss = criterion(outputs, batch_y)
                                val_loss += loss.item()
                            except Exception as e:
                                logger.warning(f"Error validating {name}: {e}")
                                continue
                    
                    avg_val_loss = val_loss / len(val_loader)
                    
                    if avg_val_loss < best_val_loss:
                        best_val_loss = avg_val_loss
                        patience_counter = 0
                        best_model_state = model.state_dict().copy()
                    else:
                        patience_counter += 1
                    
                    if patience_counter >= patience:
                        break
                
                model.load_state_dict(best_model_state)
                trained_models[name] = model
                model_weights[name] = 1.0 / best_val_loss  # Peso inverso a loss
                
                logger.info(f"{name} trained. Best val loss: {best_val_loss:.4f}")
            
            # Normalizar pesos
            total_weight = sum(model_weights.values())
            model_weights = {k: v / total_weight for k, v in model_weights.items()}
            
            # Guardar modelos y pesos
            for name, model in trained_models.items():
                torch.save(model.state_dict(), self.model_dir / f"ensemble_{name}.pth")
            
            joblib.dump(model_weights, self.model_dir / "ensemble_weights.pkl")
            joblib.dump(scaler, self.model_dir / "ensemble_scaler.pkl")
            joblib.dump(feature_cols, self.model_dir / "ensemble_features.pkl")
            joblib.dump(target_scaling_info, self.model_dir / "ensemble_target_scaling.pkl")
            
            logger.info(f"Ensemble trained. Weights: {model_weights}")
            
            return {
                "status": "success",
                "model": "ensemble",
                "models": list(trained_models.keys()),
                "weights": model_weights,
                "model_dir": str(self.model_dir),
                "device": str(self.device)
            }
            
        except Exception as e:
            logger.error(f"Error training ensemble: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}

