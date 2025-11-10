"""
Modelos avanzados de Deep Learning con las últimas técnicas e innovaciones.
Incluye: Transformers, Attention Mechanisms, Ensemble Methods, etc.
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
import math
import logging

from app.ml.gpu_utils import get_device, to_device

logger = logging.getLogger(__name__)


class PositionalEncoding(nn.Module):
    """Encoding posicional para Transformers."""
    
    def __init__(self, d_model, max_len=5000, dropout=0.1):
        super(PositionalEncoding, self).__init__()
        self.dropout = nn.Dropout(p=dropout)
        
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0).transpose(0, 1)
        self.register_buffer('pe', pe)
        
    def forward(self, x):
        x = x + self.pe[:x.size(0), :]
        return self.dropout(x)


class TimeSeriesTransformer(nn.Module):
    """
    Transformer para series temporales con atención multi-head.
    Estado del arte en predicción de series temporales (2024-2025).
    """
    
    def __init__(self, input_size=10, d_model=128, nhead=8, num_layers=4, 
                 dim_feedforward=512, dropout=0.1, output_size=1):
        super(TimeSeriesTransformer, self).__init__()
        self.d_model = d_model
        
        # Embedding de entrada
        self.input_embedding = nn.Linear(input_size, d_model)
        self.pos_encoder = PositionalEncoding(d_model, dropout=dropout)
        
        # Transformer Encoder
        encoder_layers = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            activation='gelu',
            batch_first=True
        )
        self.transformer_encoder = nn.TransformerEncoder(encoder_layers, num_layers=num_layers)
        
        # Capa de salida
        self.fc = nn.Sequential(
            nn.Linear(d_model, dim_feedforward // 2),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(dim_feedforward // 2, output_size)
        )
        
    def forward(self, x):
        # x shape: (batch, seq_len, input_size)
        # Embedding
        x = self.input_embedding(x) * math.sqrt(self.d_model)
        x = x.transpose(0, 1)  # (seq_len, batch, d_model) para PositionalEncoding
        x = self.pos_encoder(x)
        x = x.transpose(0, 1)  # Volver a (batch, seq_len, d_model)
        
        # Transformer
        x = self.transformer_encoder(x)
        
        # Tomar la última salida (o promedio)
        x = x[:, -1, :]  # Última posición
        
        # Salida
        output = self.fc(x)
        return output


class AttentionLSTM(nn.Module):
    """
    LSTM con mecanismo de atención.
    Mejora la capacidad de enfocarse en partes relevantes de la secuencia.
    """
    
    def __init__(self, input_size=10, hidden_size=128, num_layers=2, 
                 output_size=1, dropout=0.2):
        super(AttentionLSTM, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers,
                           batch_first=True, dropout=dropout if num_layers > 1 else 0,
                           bidirectional=True)
        
        # Mecanismo de atención
        self.attention = nn.MultiheadAttention(
            embed_dim=hidden_size * 2,  # Bidirectional
            num_heads=8,
            dropout=dropout,
            batch_first=True
        )
        
        self.fc = nn.Sequential(
            nn.Linear(hidden_size * 2, hidden_size),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size, output_size)
        )
        
    def forward(self, x):
        # x shape: (batch, seq_len, input_size)
        lstm_out, (h_n, c_n) = self.lstm(x)
        # lstm_out shape: (batch, seq_len, hidden_size * 2)
        
        # Aplicar atención
        attn_out, attn_weights = self.attention(lstm_out, lstm_out, lstm_out)
        # attn_out shape: (batch, seq_len, hidden_size * 2)
        
        # Tomar la última salida con atención
        last_output = attn_out[:, -1, :]
        
        # Salida
        output = self.fc(last_output)
        return output, attn_weights


class ResidualLSTM(nn.Module):
    """
    LSTM con conexiones residuales.
    Facilita el entrenamiento de redes profundas.
    """
    
    def __init__(self, input_size=10, hidden_size=128, num_layers=3, 
                 output_size=1, dropout=0.2):
        super(ResidualLSTM, self).__init__()
        self.hidden_size = hidden_size
        
        # Primera capa LSTM
        self.lstm1 = nn.LSTM(input_size, hidden_size, 1, batch_first=True)
        
        # Capas LSTM adicionales con residuales
        self.lstm_layers = nn.ModuleList([
            nn.LSTM(hidden_size, hidden_size, 1, batch_first=True)
            for _ in range(num_layers - 1)
        ])
        
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(hidden_size, output_size)
        
    def forward(self, x):
        # Primera capa
        out, _ = self.lstm1(x)
        out = self.dropout(out)
        
        # Capas residuales
        for lstm_layer in self.lstm_layers:
            residual = out
            out, _ = lstm_layer(out)
            out = self.dropout(out)
            # Conexión residual (solo en la última dimensión)
            out = out + residual
        
        # Última salida
        last_output = out[:, -1, :]
        output = self.fc(last_output)
        return output


class HybridModel(nn.Module):
    """
    Modelo híbrido que combina CNN, LSTM y Transformer.
    Ensemble dentro de un solo modelo.
    """
    
    def __init__(self, input_size=10, hidden_size=128, output_size=1, dropout=0.2):
        super(HybridModel, self).__init__()
        
        # Branch CNN
        self.cnn_branch = nn.Sequential(
            nn.Conv1d(input_size, 64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.Conv1d(64, 128, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.AdaptiveAvgPool1d(1),
            nn.Flatten()
        )
        
        # Branch LSTM
        self.lstm_branch = nn.LSTM(input_size, hidden_size, 2, 
                                   batch_first=True, dropout=dropout)
        
        # Branch Transformer (simplificado)
        self.transformer_branch = TimeSeriesTransformer(
            input_size=input_size, d_model=hidden_size, nhead=4, 
            num_layers=2, dropout=dropout, output_size=hidden_size
        )
        
        # Fusion layer
        self.fusion = nn.Sequential(
            nn.Linear(128 + hidden_size + hidden_size, hidden_size * 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size * 2, output_size)
        )
        
    def forward(self, x):
        # x shape: (batch, seq_len, input_size)
        batch_size = x.size(0)
        
        # CNN branch
        x_cnn = x.transpose(1, 2)  # (batch, input_size, seq_len)
        cnn_out = self.cnn_branch(x_cnn)  # (batch, 128)
        
        # LSTM branch
        lstm_out, _ = self.lstm_branch(x)
        lstm_out = lstm_out[:, -1, :]  # (batch, hidden_size)
        
        # Transformer branch
        transformer_out = self.transformer_branch(x)  # (batch, hidden_size)
        
        # Fusion
        fused = torch.cat([cnn_out, lstm_out, transformer_out], dim=1)
        output = self.fusion(fused)
        
        return output


class ProfitAwareModel(nn.Module):
    """
    Modelo que predice directamente el profit esperado.
    Incluye métricas de riesgo en la predicción.
    """
    
    def __init__(self, input_size=10, hidden_size=128, num_layers=3, dropout=0.2):
        super(ProfitAwareModel, self).__init__()
        
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers,
                           batch_first=True, dropout=dropout if num_layers > 1 else 0)
        
        # Múltiples salidas: precio, profit, riesgo
        self.price_head = nn.Linear(hidden_size, 1)
        self.profit_head = nn.Linear(hidden_size, 1)
        self.risk_head = nn.Linear(hidden_size, 1)
        self.confidence_head = nn.Linear(hidden_size, 1)
        
        self.dropout = nn.Dropout(dropout)
        
    def forward(self, x):
        lstm_out, _ = self.lstm(x)
        last_output = lstm_out[:, -1, :]
        last_output = self.dropout(last_output)
        
        price = self.price_head(last_output)
        profit = self.profit_head(last_output)
        risk = torch.sigmoid(self.risk_head(last_output))  # 0-1
        confidence = torch.sigmoid(self.confidence_head(last_output))  # 0-1
        
        return {
            'price': price,
            'profit': profit,
            'risk': risk,
            'confidence': confidence
        }


def create_transformer_model(input_size=10, d_model=128, nhead=8, num_layers=4,
                            dim_feedforward=512, dropout=0.1, output_size=1):
    """Crear modelo Transformer."""
    model = TimeSeriesTransformer(
        input_size=input_size, d_model=d_model, nhead=nhead,
        num_layers=num_layers, dim_feedforward=dim_feedforward,
        dropout=dropout, output_size=output_size
    )
    device = get_device()
    model = to_device(model, device)
    logger.info(f"Transformer model created and moved to {device}")
    return model


def create_attention_lstm(input_size=10, hidden_size=128, num_layers=2,
                         output_size=1, dropout=0.2):
    """Crear LSTM con atención."""
    model = AttentionLSTM(
        input_size=input_size, hidden_size=hidden_size,
        num_layers=num_layers, output_size=output_size, dropout=dropout
    )
    device = get_device()
    model = to_device(model, device)
    logger.info(f"Attention LSTM created and moved to {device}")
    return model


def create_residual_lstm(input_size=10, hidden_size=128, num_layers=3,
                        output_size=1, dropout=0.2):
    """Crear LSTM residual."""
    model = ResidualLSTM(
        input_size=input_size, hidden_size=hidden_size,
        num_layers=num_layers, output_size=output_size, dropout=dropout
    )
    device = get_device()
    model = to_device(model, device)
    logger.info(f"Residual LSTM created and moved to {device}")
    return model


def create_hybrid_model(input_size=10, hidden_size=128, output_size=1, dropout=0.2):
    """Crear modelo híbrido."""
    model = HybridModel(
        input_size=input_size, hidden_size=hidden_size,
        output_size=output_size, dropout=dropout
    )
    device = get_device()
    model = to_device(model, device)
    logger.info(f"Hybrid model created and moved to {device}")
    return model


def create_profit_aware_model(input_size=10, hidden_size=128, num_layers=3, dropout=0.2):
    """Crear modelo que predice profit directamente."""
    model = ProfitAwareModel(
        input_size=input_size, hidden_size=hidden_size,
        num_layers=num_layers, dropout=dropout
    )
    device = get_device()
    model = to_device(model, device)
    logger.info(f"Profit-aware model created and moved to {device}")
    return model

