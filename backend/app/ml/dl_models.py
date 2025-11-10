"""
Modelos de Deep Learning con PyTorch para predicción de precios y análisis de trading.
Usa CPU automáticamente (GPU si está disponible en el futuro).
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
import logging

from app.ml.gpu_utils import get_device, to_device

logger = logging.getLogger(__name__)


class LSTMModel(nn.Module):
    """
    Modelo LSTM para predicción de precios.
    """
    
    def __init__(self, input_size=10, hidden_size=64, num_layers=2, output_size=1, dropout=0.2):
        super(LSTMModel, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, 
                           batch_first=True, dropout=dropout if num_layers > 1 else 0)
        self.fc = nn.Linear(hidden_size, output_size)
        self.dropout = nn.Dropout(dropout)
        
    def forward(self, x):
        # x shape: (batch, seq_len, input_size)
        lstm_out, _ = self.lstm(x)
        # Tomar la última salida de la secuencia
        last_output = lstm_out[:, -1, :]
        last_output = self.dropout(last_output)
        output = self.fc(last_output)
        return output


class GRUModel(nn.Module):
    """
    Modelo GRU para predicción de spreads.
    """
    
    def __init__(self, input_size=10, hidden_size=64, num_layers=2, output_size=1, dropout=0.2):
        super(GRUModel, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        self.gru = nn.GRU(input_size, hidden_size, num_layers,
                         batch_first=True, dropout=dropout if num_layers > 1 else 0)
        self.fc = nn.Linear(hidden_size, output_size)
        self.dropout = nn.Dropout(dropout)
        
    def forward(self, x):
        # x shape: (batch, seq_len, input_size)
        gru_out, _ = self.gru(x)
        # Tomar la última salida de la secuencia
        last_output = gru_out[:, -1, :]
        last_output = self.dropout(last_output)
        output = self.fc(last_output)
        return output


class Autoencoder(nn.Module):
    """
    Autoencoder para detección de anomalías.
    """
    
    def __init__(self, input_size=10, encoding_dim=32, dropout=0.2):
        super(Autoencoder, self).__init__()
        
        # Encoder
        self.encoder = nn.Sequential(
            nn.Linear(input_size, 64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, encoding_dim),
            nn.ReLU()
        )
        
        # Decoder
        self.decoder = nn.Sequential(
            nn.Linear(encoding_dim, 64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, input_size),
            nn.Sigmoid()
        )
        
    def forward(self, x):
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        return decoded
    
    def encode(self, x):
        """Obtener representación codificada."""
        return self.encoder(x)


class CNNModel(nn.Module):
    """
    Modelo CNN para análisis de patrones en series temporales.
    """
    
    def __init__(self, input_channels=1, num_classes=2, dropout=0.2):
        super(CNNModel, self).__init__()
        
        self.conv1 = nn.Conv1d(input_channels, 32, kernel_size=3, padding=1)
        self.conv2 = nn.Conv1d(32, 64, kernel_size=3, padding=1)
        self.conv3 = nn.Conv1d(64, 128, kernel_size=3, padding=1)
        
        self.pool = nn.MaxPool1d(2)
        self.dropout = nn.Dropout(dropout)
        
        # Calcular tamaño después de convoluciones
        self.fc1 = nn.Linear(128 * 10, 128)  # Ajustar según tamaño de entrada
        self.fc2 = nn.Linear(128, num_classes)
        
    def forward(self, x):
        # x shape: (batch, channels, seq_len)
        x = F.relu(self.conv1(x))
        x = self.pool(x)
        x = F.relu(self.conv2(x))
        x = self.pool(x)
        x = F.relu(self.conv3(x))
        x = self.pool(x)
        
        # Flatten
        x = x.view(x.size(0), -1)
        x = self.dropout(x)
        x = F.relu(self.fc1(x))
        x = self.dropout(x)
        x = self.fc2(x)
        return x


def create_lstm_model(input_size=10, hidden_size=64, num_layers=2, output_size=1, dropout=0.2):
    """Crear modelo LSTM y moverlo al dispositivo."""
    model = LSTMModel(input_size, hidden_size, num_layers, output_size, dropout)
    device = get_device()
    model = to_device(model, device)
    logger.info(f"LSTM model created and moved to {device}")
    return model


def create_gru_model(input_size=10, hidden_size=64, num_layers=2, output_size=1, dropout=0.2):
    """Crear modelo GRU y moverlo al dispositivo."""
    model = GRUModel(input_size, hidden_size, num_layers, output_size, dropout)
    device = get_device()
    model = to_device(model, device)
    logger.info(f"GRU model created and moved to {device}")
    return model


def create_autoencoder(input_size=10, encoding_dim=32, dropout=0.2):
    """Crear autoencoder y moverlo al dispositivo."""
    model = Autoencoder(input_size, encoding_dim, dropout)
    device = get_device()
    model = to_device(model, device)
    logger.info(f"Autoencoder created and moved to {device}")
    return model


def create_cnn_model(input_channels=1, num_classes=2, dropout=0.2):
    """Crear modelo CNN y moverlo al dispositivo."""
    model = CNNModel(input_channels, num_classes, dropout)
    device = get_device()
    model = to_device(model, device)
    logger.info(f"CNN model created and moved to {device}")
    return model

