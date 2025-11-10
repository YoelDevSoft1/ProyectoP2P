"""
Servicio de Deep Learning para entrenamiento e inferencia.
Usa PyTorch con CPU (GPU si está disponible).
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

from app.ml.gpu_utils import get_device, to_device, optimize_model_for_inference
from app.ml.dl_models import create_lstm_model, create_gru_model, create_autoencoder

logger = logging.getLogger(__name__)


class TimeSeriesDataset(Dataset):
    """Dataset para series temporales."""
    
    def __init__(self, data: np.ndarray, targets: Optional[np.ndarray] = None, sequence_length: int = 10):
        self.data = data
        self.targets = targets
        self.sequence_length = sequence_length
        
    def __len__(self):
        return len(self.data) - self.sequence_length + 1
    
    def __getitem__(self, idx):
        sequence = self.data[idx:idx + self.sequence_length]
        if self.targets is not None:
            target = self.targets[idx + self.sequence_length - 1]
            return torch.FloatTensor(sequence), torch.FloatTensor([target])
        return torch.FloatTensor(sequence)


class DLModelTrainer:
    """Entrenador de modelos de Deep Learning."""
    
    def __init__(self, model_dir: Path = Path("ml_models/dl")):
        self.model_dir = model_dir
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.device = get_device()
        logger.info(f"DLModelTrainer initialized with device: {self.device}")
    
    def prepare_data(self, df: pd.DataFrame, target_col: str, 
                     feature_cols: List[str], sequence_length: int = 10,
                     train_ratio: float = 0.8) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Preparar datos para entrenamiento."""
        # Limpiar datos
        df = df.dropna()
        if len(df) < sequence_length + 1:
            raise ValueError(f"Not enough data. Need at least {sequence_length + 1} samples")
        
        # Normalizar features
        features = df[feature_cols].values
        targets = df[target_col].values
        
        # Crear secuencias
        X, y = [], []
        for i in range(len(features) - sequence_length + 1):
            X.append(features[i:i + sequence_length])
            y.append(targets[i + sequence_length - 1])
        
        X = np.array(X)
        y = np.array(y)
        
        # Dividir en train/test
        split_idx = int(len(X) * train_ratio)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        return X_train, X_test, y_train, y_test
    
    def train_price_predictor(self, data: pd.DataFrame, epochs: int = 50, 
                             batch_size: int = 32, learning_rate: float = 0.001) -> Dict:
        """Entrenar modelo LSTM para predicción de precios."""
        try:
            logger.info("Training price predictor LSTM model")
            
            # Preparar datos
            feature_cols = ['price', 'spread', 'volume', 'ma_5', 'ma_20', 
                           'volatility', 'price_change', 'hour', 'day_of_week', 'spread_ma']
            feature_cols = [col for col in feature_cols if col in data.columns]
            
            if 'price' not in data.columns:
                raise ValueError("'price' column not found in data")
            
            # Añadir columnas faltantes con valores por defecto
            for col in ['spread', 'volume', 'ma_5', 'ma_20', 'volatility', 
                       'price_change', 'hour', 'day_of_week', 'spread_ma']:
                if col not in data.columns:
                    data[col] = 0.0
            
            X_train, X_test, y_train, y_test = self.prepare_data(
                data, 'price', feature_cols, sequence_length=10
            )
            
            # Crear modelo
            model = create_lstm_model(
                input_size=len(feature_cols),
                hidden_size=64,
                num_layers=2,
                output_size=1,
                dropout=0.2
            )
            
            # Dataset y DataLoader
            train_dataset = TimeSeriesDataset(X_train, y_train, sequence_length=10)
            test_dataset = TimeSeriesDataset(X_test, y_test, sequence_length=10)
            train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
            test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)
            
            # Optimizador y loss
            criterion = nn.MSELoss()
            optimizer = optim.Adam(model.parameters(), lr=learning_rate)
            
            # Entrenamiento
            model.train()
            train_losses = []
            for epoch in range(epochs):
                epoch_loss = 0
                for batch_x, batch_y in train_loader:
                    batch_x = to_device(batch_x, self.device)
                    batch_y = to_device(batch_y, self.device)
                    
                    optimizer.zero_grad()
                    outputs = model(batch_x)
                    loss = criterion(outputs, batch_y)
                    loss.backward()
                    optimizer.step()
                    
                    epoch_loss += loss.item()
                
                avg_loss = epoch_loss / len(train_loader)
                train_losses.append(avg_loss)
                
                if (epoch + 1) % 10 == 0:
                    logger.info(f"Epoch {epoch + 1}/{epochs}, Loss: {avg_loss:.4f}")
            
            # Evaluación
            model.eval()
            test_loss = 0
            with torch.no_grad():
                for batch_x, batch_y in test_loader:
                    batch_x = to_device(batch_x, self.device)
                    batch_y = to_device(batch_y, self.device)
                    outputs = model(batch_x)
                    test_loss += criterion(outputs, batch_y).item()
            
            test_loss /= len(test_loader)
            
            # Guardar modelo
            model_path = self.model_dir / "price_predictor_lstm.pth"
            torch.save(model.state_dict(), model_path)
            
            # Optimizar para inferencia
            model = optimize_model_for_inference(model)
            
            logger.info(f"Price predictor trained. Test loss: {test_loss:.4f}")
            
            return {
                "status": "success",
                "test_loss": float(test_loss),
                "train_losses": train_losses,
                "model_path": str(model_path),
                "device": str(self.device)
            }
            
        except Exception as e:
            logger.error(f"Error training price predictor: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}
    
    def train_spread_predictor(self, data: pd.DataFrame, epochs: int = 50,
                              batch_size: int = 32, learning_rate: float = 0.001) -> Dict:
        """Entrenar modelo GRU para predicción de spreads."""
        try:
            logger.info("Training spread predictor GRU model")
            
            # Similar a train_price_predictor pero con GRU
            feature_cols = ['spread', 'volume', 'price', 'ma_5', 'ma_20',
                           'volatility', 'hour', 'day_of_week']
            feature_cols = [col for col in feature_cols if col in data.columns]
            
            if 'spread' not in data.columns:
                raise ValueError("'spread' column not found in data")
            
            # Añadir columnas faltantes
            for col in ['volume', 'price', 'ma_5', 'ma_20', 'volatility', 'hour', 'day_of_week']:
                if col not in data.columns:
                    data[col] = 0.0
            
            X_train, X_test, y_train, y_test = self.prepare_data(
                data, 'spread', feature_cols, sequence_length=10
            )
            
            # Crear modelo GRU
            model = create_gru_model(
                input_size=len(feature_cols),
                hidden_size=64,
                num_layers=2,
                output_size=1,
                dropout=0.2
            )
            
            # Dataset y DataLoader
            train_dataset = TimeSeriesDataset(X_train, y_train, sequence_length=10)
            test_dataset = TimeSeriesDataset(X_test, y_test, sequence_length=10)
            train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
            test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)
            
            # Optimizador y loss
            criterion = nn.MSELoss()
            optimizer = optim.Adam(model.parameters(), lr=learning_rate)
            
            # Entrenamiento
            model.train()
            train_losses = []
            for epoch in range(epochs):
                epoch_loss = 0
                for batch_x, batch_y in train_loader:
                    batch_x = to_device(batch_x, self.device)
                    batch_y = to_device(batch_y, self.device)
                    
                    optimizer.zero_grad()
                    outputs = model(batch_x)
                    loss = criterion(outputs, batch_y)
                    loss.backward()
                    optimizer.step()
                    
                    epoch_loss += loss.item()
                
                avg_loss = epoch_loss / len(train_loader)
                train_losses.append(avg_loss)
                
                if (epoch + 1) % 10 == 0:
                    logger.info(f"Epoch {epoch + 1}/{epochs}, Loss: {avg_loss:.4f}")
            
            # Evaluación
            model.eval()
            test_loss = 0
            with torch.no_grad():
                for batch_x, batch_y in test_loader:
                    batch_x = to_device(batch_x, self.device)
                    batch_y = to_device(batch_y, self.device)
                    outputs = model(batch_x)
                    test_loss += criterion(outputs, batch_y).item()
            
            test_loss /= len(test_loader)
            
            # Guardar modelo
            model_path = self.model_dir / "spread_predictor_gru.pth"
            torch.save(model.state_dict(), model_path)
            
            # Optimizar para inferencia
            model = optimize_model_for_inference(model)
            
            logger.info(f"Spread predictor trained. Test loss: {test_loss:.4f}")
            
            return {
                "status": "success",
                "test_loss": float(test_loss),
                "train_losses": train_losses,
                "model_path": str(model_path),
                "device": str(self.device)
            }
            
        except Exception as e:
            logger.error(f"Error training spread predictor: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}
    
    def train_anomaly_detector(self, data: pd.DataFrame, epochs: int = 50,
                              batch_size: int = 32, learning_rate: float = 0.001) -> Dict:
        """Entrenar autoencoder para detección de anomalías."""
        try:
            logger.info("Training anomaly detector autoencoder")
            
            feature_cols = ['price', 'spread', 'volume', 'ma_5', 'ma_20',
                           'volatility', 'price_change', 'hour', 'day_of_week', 'spread_ma']
            feature_cols = [col for col in feature_cols if col in data.columns]
            
            # Normalizar datos
            features = data[feature_cols].dropna().values
            if len(features) < 100:
                raise ValueError("Not enough data for training")
            
            # Normalizar
            from sklearn.preprocessing import MinMaxScaler
            scaler = MinMaxScaler()
            features_scaled = scaler.fit_transform(features)
            
            # Dividir datos
            split_idx = int(len(features_scaled) * 0.8)
            train_data = features_scaled[:split_idx]
            test_data = features_scaled[split_idx:]
            
            # Crear modelo
            model = create_autoencoder(
                input_size=len(feature_cols),
                encoding_dim=32,
                dropout=0.2
            )
            
            # Dataset y DataLoader
            train_dataset = torch.utils.data.TensorDataset(
                torch.FloatTensor(train_data)
            )
            train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
            
            # Optimizador y loss
            criterion = nn.MSELoss()
            optimizer = optim.Adam(model.parameters(), lr=learning_rate)
            
            # Entrenamiento
            model.train()
            train_losses = []
            for epoch in range(epochs):
                epoch_loss = 0
                for batch_x, in train_loader:
                    batch_x = to_device(batch_x, self.device)
                    
                    optimizer.zero_grad()
                    outputs = model(batch_x)
                    loss = criterion(outputs, batch_x)
                    loss.backward()
                    optimizer.step()
                    
                    epoch_loss += loss.item()
                
                avg_loss = epoch_loss / len(train_loader)
                train_losses.append(avg_loss)
                
                if (epoch + 1) % 10 == 0:
                    logger.info(f"Epoch {epoch + 1}/{epochs}, Loss: {avg_loss:.4f}")
            
            # Guardar modelo y scaler
            model_path = self.model_dir / "anomaly_detector_autoencoder.pth"
            scaler_path = self.model_dir / "anomaly_detector_scaler.pkl"
            torch.save(model.state_dict(), model_path)
            joblib.dump(scaler, scaler_path)
            
            # Optimizar para inferencia
            model = optimize_model_for_inference(model)
            
            logger.info(f"Anomaly detector trained. Final loss: {train_losses[-1]:.4f}")
            
            return {
                "status": "success",
                "final_loss": float(train_losses[-1]),
                "train_losses": train_losses,
                "model_path": str(model_path),
                "scaler_path": str(scaler_path),
                "device": str(self.device)
            }
            
        except Exception as e:
            logger.error(f"Error training anomaly detector: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}


class DLPredictor:
    """Predictor usando modelos de Deep Learning."""
    
    def __init__(self, model_dir: Path = Path("ml_models/dl")):
        self.model_dir = model_dir
        self.device = get_device()
        logger.info(f"DLPredictor initialized with device: {self.device}")
    
    def predict_price(self, sequence: np.ndarray, model_type: str = "lstm") -> Optional[float]:
        """Predecir precio usando modelo LSTM."""
        try:
            model_path = self.model_dir / "price_predictor_lstm.pth"
            if not model_path.exists():
                logger.warning("Price predictor model not found")
                return None
            
            # Cargar modelo
            from app.ml.dl_models import create_lstm_model
            model = create_lstm_model(input_size=sequence.shape[1], hidden_size=64, 
                                     num_layers=2, output_size=1)
            model.load_state_dict(torch.load(model_path, map_location=self.device))
            model.eval()
            model = optimize_model_for_inference(model)
            
            # Preparar entrada
            if len(sequence.shape) == 2:
                sequence = sequence.reshape(1, *sequence.shape)
            input_tensor = torch.FloatTensor(sequence)
            input_tensor = to_device(input_tensor, self.device)
            
            # Predicción
            with torch.no_grad():
                prediction = model(input_tensor)
                return float(prediction.cpu().numpy()[0][0])
                
        except Exception as e:
            logger.error(f"Error predicting price: {e}", exc_info=True)
            return None
    
    def detect_anomalies(self, data: np.ndarray, threshold: float = 0.1) -> List[bool]:
        """Detectar anomalías usando autoencoder."""
        try:
            model_path = self.model_dir / "anomaly_detector_autoencoder.pth"
            scaler_path = self.model_dir / "anomaly_detector_scaler.pkl"
            
            if not model_path.exists() or not scaler_path.exists():
                logger.warning("Anomaly detector model not found")
                return [False] * len(data)
            
            # Cargar modelo y scaler
            from app.ml.dl_models import create_autoencoder
            import joblib
            
            model = create_autoencoder(input_size=data.shape[1], encoding_dim=32)
            model.load_state_dict(torch.load(model_path, map_location=self.device))
            model.eval()
            model = optimize_model_for_inference(model)
            
            scaler = joblib.load(scaler_path)
            data_scaled = scaler.transform(data)
            
            # Predicción
            input_tensor = torch.FloatTensor(data_scaled)
            input_tensor = to_device(input_tensor, self.device)
            
            anomalies = []
            with torch.no_grad():
                reconstructed = model(input_tensor)
                reconstruction_error = torch.mean((input_tensor - reconstructed) ** 2, dim=1)
                anomalies = (reconstruction_error.cpu().numpy() > threshold).tolist()
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}", exc_info=True)
            return [False] * len(data)

