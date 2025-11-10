"""
Entrenador de modelos de Machine Learning.

Este módulo entrena modelos para predecir:
1. Mejores momentos para operar
2. Tendencias de precios
3. Probabilidad de éxito de operaciones
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, mean_squared_error
import joblib
import structlog
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from app.core.config import settings
from app.models.price_history import PriceHistory
from app.models.trade import Trade, TradeStatus

logger = structlog.get_logger()


class MLModelTrainer:
    """
    Entrenador de modelos ML para trading.
    """

    def __init__(self, db_session):
        self.db = db_session
        self.model_dir = Path("ml_models")
        self.model_dir.mkdir(exist_ok=True)

    def train_model(self) -> dict:
        """
        Entrenar modelo completo.

        Returns:
            Métricas del modelo entrenado
        """
        logger.info("Starting ML model training")

        # 1. Obtener datos
        data = self._prepare_training_data()

        if len(data) < settings.ML_MIN_DATA_POINTS:
            logger.warning(
                "Insufficient data for training",
                available=len(data),
                required=settings.ML_MIN_DATA_POINTS
            )
            return {"status": "skipped", "reason": "insufficient_data"}

        # 2. Entrenar modelo de predicción de precios
        price_metrics = self._train_price_prediction(data)

        # 3. Entrenar modelo de clasificación de oportunidades
        opportunity_metrics = self._train_opportunity_classifier(data)

        metrics = {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "data_points": len(data),
            "price_model": price_metrics,
            "opportunity_model": opportunity_metrics
        }

        logger.info("ML model training completed", metrics=metrics)
        return metrics

    def _prepare_training_data(self) -> pd.DataFrame:
        """
        Preparar datos de entrenamiento desde la base de datos.

        Returns:
            DataFrame con features y labels
        """
        # Obtener historial de precios
        since = datetime.utcnow() - timedelta(days=30)

        prices = self.db.query(PriceHistory).filter(
            PriceHistory.timestamp >= since
        ).order_by(PriceHistory.timestamp.asc()).all()

        if not prices:
            return pd.DataFrame()

        # Convertir a DataFrame
        data = []
        for p in prices:
            data.append({
                "timestamp": p.timestamp,
                "asset": p.asset,
                "fiat": p.fiat,
                "bid_price": p.bid_price,
                "ask_price": p.ask_price,
                "avg_price": p.avg_price,
                "spread": p.spread,
                "trm_rate": p.trm_rate or 0
            })

        df = pd.DataFrame(data)

        if df.empty:
            return df

        # Feature engineering
        df = self._create_features(df)

        return df

    def _create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Crear features para ML.

        Args:
            df: DataFrame original

        Returns:
            DataFrame con features adicionales
        """
        # Convertir timestamp a features temporales
        df["hour"] = pd.to_datetime(df["timestamp"]).dt.hour
        df["day_of_week"] = pd.to_datetime(df["timestamp"]).dt.dayofweek
        df["day_of_month"] = pd.to_datetime(df["timestamp"]).dt.day

        # Calcular estadísticas móviles por fiat
        for fiat in df["fiat"].unique():
            mask = df["fiat"] == fiat

            # Moving averages
            df.loc[mask, "ma_5"] = df.loc[mask, "avg_price"].rolling(window=5, min_periods=1).mean()
            df.loc[mask, "ma_20"] = df.loc[mask, "avg_price"].rolling(window=20, min_periods=1).mean()

            # Volatilidad
            df.loc[mask, "volatility"] = df.loc[mask, "avg_price"].rolling(window=10, min_periods=1).std()

            # Price change
            df.loc[mask, "price_change"] = df.loc[mask, "avg_price"].pct_change()

            # Spread moving average
            df.loc[mask, "spread_ma"] = df.loc[mask, "spread"].rolling(window=10, min_periods=1).mean()

        # Rellenar NaN
        df = df.fillna(method="bfill").fillna(0)

        return df

    def _train_price_prediction(self, data: pd.DataFrame) -> dict:
        """
        Entrenar modelo de predicción de precios.

        Args:
            data: Datos de entrenamiento

        Returns:
            Métricas del modelo
        """
        if data.empty:
            return {"status": "skipped"}

        try:
            # Preparar features y target
            feature_cols = ["hour", "day_of_week", "spread", "ma_5", "ma_20", "volatility", "price_change"]

            # Asegurar que todas las columnas existen
            for col in feature_cols:
                if col not in data.columns:
                    logger.warning(f"Feature {col} not found, skipping price prediction")
                    return {"status": "skipped", "reason": "missing_features"}

            X = data[feature_cols]

            # Target: precio futuro (siguiente período)
            y = data["avg_price"].shift(-1).fillna(method="ffill")

            # Split
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )

            # Entrenar modelo
            model = GradientBoostingRegressor(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=3,
                random_state=42
            )

            model.fit(X_train, y_train)

            # Evaluar
            y_pred = model.predict(X_test)
            mse = mean_squared_error(y_test, y_pred)
            rmse = np.sqrt(mse)

            # Guardar modelo
            model_path = self.model_dir / "price_prediction.pkl"
            joblib.dump(model, model_path)

            logger.info("Price prediction model trained", rmse=rmse)

            return {
                "status": "success",
                "rmse": float(rmse),
                "model_path": str(model_path)
            }

        except Exception as e:
            logger.error("Error training price prediction model", error=str(e))
            return {"status": "error", "error": str(e)}

    def _train_opportunity_classifier(self, data: pd.DataFrame) -> dict:
        """
        Entrenar clasificador de oportunidades.

        Args:
            data: Datos de entrenamiento

        Returns:
            Métricas del modelo
        """
        if data.empty:
            return {"status": "skipped"}

        try:
            # Preparar features
            feature_cols = ["hour", "day_of_week", "spread", "ma_5", "ma_20", "volatility", "spread_ma"]

            for col in feature_cols:
                if col not in data.columns:
                    logger.warning(f"Feature {col} not found, skipping opportunity classifier")
                    return {"status": "skipped", "reason": "missing_features"}

            X = data[feature_cols]

            # Target: si el spread es mayor al threshold (oportunidad)
            y = (data["spread"] >= settings.SPREAD_THRESHOLD).astype(int)

            # Split
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )

            # Entrenar
            model = RandomForestClassifier(
                n_estimators=100,
                max_depth=5,
                random_state=42
            )

            model.fit(X_train, y_train)

            # Evaluar
            y_pred = model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)

            # Feature importance
            importance = dict(zip(feature_cols, model.feature_importances_))

            # Guardar modelo
            model_path = self.model_dir / "opportunity_classifier.pkl"
            joblib.dump(model, model_path)

            logger.info("Opportunity classifier trained", accuracy=accuracy)

            return {
                "status": "success",
                "accuracy": float(accuracy),
                "feature_importance": {k: float(v) for k, v in importance.items()},
                "model_path": str(model_path)
            }

        except Exception as e:
            logger.error("Error training opportunity classifier", error=str(e))
            return {"status": "error", "error": str(e)}


class MLPredictor:
    """
    Predictor usando modelos entrenados.
    """

    def __init__(self):
        self.model_dir = Path("ml_models")

    def predict_price(self, features: dict) -> Optional[float]:
        """
        Predecir precio futuro.

        Args:
            features: Dict con features

        Returns:
            Precio predicho o None
        """
        try:
            model_path = self.model_dir / "price_prediction.pkl"
            if not model_path.exists():
                return None

            model = joblib.load(model_path)

            # Preparar features en el orden correcto
            feature_cols = ["hour", "day_of_week", "spread", "ma_5", "ma_20", "volatility", "price_change"]
            X = [[features.get(col, 0) for col in feature_cols]]

            prediction = model.predict(X)[0]
            return float(prediction)

        except Exception as e:
            logger.error("Error predicting price", error=str(e))
            return None

    def predict_opportunity(self, features: dict) -> Optional[float]:
        """
        Predecir probabilidad de oportunidad.

        Args:
            features: Dict con features

        Returns:
            Probabilidad (0-1) o None
        """
        try:
            model_path = self.model_dir / "opportunity_classifier.pkl"
            if not model_path.exists():
                return None

            model = joblib.load(model_path)

            feature_cols = ["hour", "day_of_week", "spread", "ma_5", "ma_20", "volatility", "spread_ma"]
            X = [[features.get(col, 0) for col in feature_cols]]

            probability = model.predict_proba(X)[0][1]
            return float(probability)

        except Exception as e:
            logger.error("Error predicting opportunity", error=str(e))
            return None
