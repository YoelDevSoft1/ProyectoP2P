"""
Advanced ML Service - Machine Learning para predicción y optimización de trading

Modelos implementados:
1. Predicción de spread futuro
2. Clasificación de oportunidades de arbitraje
3. Predicción de timing óptimo
4. Predicción de liquidez
5. Detección de anomalías en precios
6. Forecasting de volatilidad
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor, RandomForestClassifier, IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import joblib
import os
import logging

logger = logging.getLogger(__name__)


class AdvancedMLService:
    """Servicio de Machine Learning avanzado para trading P2P"""

    def __init__(self):
        self.models_dir = "ml_models"
        os.makedirs(self.models_dir, exist_ok=True)

        # Modelos
        self.spread_predictor = None
        self.opportunity_classifier = None
        self.timing_predictor = None
        self.anomaly_detector = None

        # Scalers
        self.spread_scaler = StandardScaler()
        self.opportunity_scaler = StandardScaler()

        # Cargar modelos si existen
        self._load_models()

    def _load_models(self):
        """Carga modelos pre-entrenados si existen"""
        try:
            spread_path = os.path.join(self.models_dir, "spread_predictor.pkl")
            opportunity_path = os.path.join(self.models_dir, "opportunity_classifier.pkl")

            if os.path.exists(spread_path):
                self.spread_predictor = joblib.load(spread_path)
                logger.info("Spread predictor model loaded")

            if os.path.exists(opportunity_path):
                self.opportunity_classifier = joblib.load(opportunity_path)
                logger.info("Opportunity classifier model loaded")

        except Exception as e:
            logger.error(f"Error loading models: {str(e)}")

    def _save_model(self, model, name: str):
        """Guarda un modelo entrenado"""
        try:
            path = os.path.join(self.models_dir, f"{name}.pkl")
            joblib.dump(model, path)
            logger.info(f"Model {name} saved successfully")
        except Exception as e:
            logger.error(f"Error saving model {name}: {str(e)}")

    def train_spread_predictor(self, historical_data: List[Dict]) -> Dict:
        """
        Entrena modelo para predecir spread futuro

        Features:
        - Spread actual
        - Volumen bid/ask
        - Time of day
        - Day of week
        - Volatilidad reciente
        - Momentum
        """

        if len(historical_data) < 100:
            return {
                "success": False,
                "error": "Insufficient data for training (minimum 100 samples)"
            }

        try:
            # Preparar features y targets
            X, y = self._prepare_spread_features(historical_data)

            # Split train/test
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )

            # Escalar features
            X_train_scaled = self.spread_scaler.fit_transform(X_train)
            X_test_scaled = self.spread_scaler.transform(X_test)

            # Entrenar modelo
            self.spread_predictor = GradientBoostingRegressor(
                n_estimators=200,
                max_depth=5,
                learning_rate=0.1,
                subsample=0.8,
                random_state=42
            )

            self.spread_predictor.fit(X_train_scaled, y_train)

            # Evaluar
            train_score = self.spread_predictor.score(X_train_scaled, y_train)
            test_score = self.spread_predictor.score(X_test_scaled, y_test)

            # Guardar modelo
            self._save_model(self.spread_predictor, "spread_predictor")
            self._save_model(self.spread_scaler, "spread_scaler")

            return {
                "success": True,
                "model": "Gradient Boosting Regressor",
                "train_score": train_score,
                "test_score": test_score,
                "samples": len(historical_data),
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error training spread predictor: {str(e)}")
            return {"success": False, "error": str(e)}

    def _prepare_spread_features(self, data: List[Dict]) -> Tuple[np.ndarray, np.ndarray]:
        """Prepara features para predicción de spread"""

        features = []
        targets = []

        for i in range(len(data) - 1):  # -1 porque necesitamos el siguiente para target
            current = data[i]
            next_sample = data[i + 1]

            # Features
            feature_vector = [
                current.get("spread", 0),
                current.get("bid_volume", 0),
                current.get("ask_volume", 0),
                current.get("bid_ask_ratio", 1),
                current.get("volatility", 0),
                current.get("momentum", 0),
                self._get_hour_of_day(current.get("timestamp")),
                self._get_day_of_week(current.get("timestamp")),
                current.get("num_orders_bid", 0),
                current.get("num_orders_ask", 0),
            ]

            # Target: spread en el siguiente timeframe
            target = next_sample.get("spread", 0)

            features.append(feature_vector)
            targets.append(target)

        return np.array(features), np.array(targets)

    def predict_future_spread(self, current_market_data: Dict, horizon_minutes: int = 10) -> Dict:
        """
        Predice el spread futuro basado en condiciones actuales

        Args:
            current_market_data: Datos actuales del mercado
            horizon_minutes: Horizonte de predicción en minutos
        """

        if self.spread_predictor is None:
            return {
                "success": False,
                "error": "Spread predictor model not trained yet"
            }

        try:
            # Preparar features del estado actual
            features = np.array([[
                current_market_data.get("current_spread", 0),
                current_market_data.get("bid_volume", 0),
                current_market_data.get("ask_volume", 0),
                current_market_data.get("bid_ask_ratio", 1),
                current_market_data.get("volatility", 0),
                current_market_data.get("momentum", 0),
                self._get_hour_of_day(datetime.utcnow()),
                self._get_day_of_week(datetime.utcnow()),
                current_market_data.get("num_orders_bid", 0),
                current_market_data.get("num_orders_ask", 0),
            ]])

            # Escalar
            features_scaled = self.spread_scaler.transform(features)

            # Predecir
            predicted_spread = self.spread_predictor.predict(features_scaled)[0]

            # Calcular confidence basado en varianza del ensemble
            # Para GradientBoosting, usamos las predicciones de cada stage
            confidence = self._calculate_prediction_confidence(
                current_market_data.get("current_spread", 0),
                predicted_spread
            )

            return {
                "success": True,
                "current_spread": current_market_data.get("current_spread", 0),
                "predicted_spread": predicted_spread,
                "spread_change": predicted_spread - current_market_data.get("current_spread", 0),
                "spread_change_percentage": (
                    (predicted_spread - current_market_data.get("current_spread", 0)) /
                    current_market_data.get("current_spread", 1) * 100
                ),
                "confidence": confidence,
                "horizon_minutes": horizon_minutes,
                "recommendation": self._generate_spread_recommendation(
                    current_market_data.get("current_spread", 0),
                    predicted_spread
                ),
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error predicting spread: {str(e)}")
            return {"success": False, "error": str(e)}

    def train_opportunity_classifier(self, historical_opportunities: List[Dict]) -> Dict:
        """
        Entrena clasificador para determinar calidad de oportunidades

        Clasifica oportunidades en:
        - EXCELLENT (alta probabilidad de éxito y ROI alto)
        - GOOD (buena probabilidad de éxito)
        - MODERATE (ROI moderado o riesgo moderado)
        - POOR (baja probabilidad de éxito)

        Features:
        - ROI esperado
        - Spread
        - Liquidez disponible
        - Volatilidad
        - Market quality
        """

        if len(historical_opportunities) < 50:
            return {
                "success": False,
                "error": "Insufficient data for training (minimum 50 samples)"
            }

        try:
            # Preparar features y labels
            X, y = self._prepare_opportunity_features(historical_opportunities)

            # Split
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )

            # Escalar
            X_train_scaled = self.opportunity_scaler.fit_transform(X_train)
            X_test_scaled = self.opportunity_scaler.transform(X_test)

            # Entrenar Random Forest Classifier
            self.opportunity_classifier = RandomForestClassifier(
                n_estimators=200,
                max_depth=10,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                class_weight='balanced'
            )

            self.opportunity_classifier.fit(X_train_scaled, y_train)

            # Evaluar
            train_accuracy = self.opportunity_classifier.score(X_train_scaled, y_train)
            test_accuracy = self.opportunity_classifier.score(X_test_scaled, y_test)

            # Feature importance
            feature_names = [
                "roi", "spread", "liquidity", "volatility", "market_quality",
                "execution_time", "slippage", "volume_ratio"
            ]
            feature_importance = dict(zip(
                feature_names,
                self.opportunity_classifier.feature_importances_
            ))

            # Guardar modelo
            self._save_model(self.opportunity_classifier, "opportunity_classifier")
            self._save_model(self.opportunity_scaler, "opportunity_scaler")

            return {
                "success": True,
                "model": "Random Forest Classifier",
                "train_accuracy": train_accuracy,
                "test_accuracy": test_accuracy,
                "samples": len(historical_opportunities),
                "feature_importance": feature_importance,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error training opportunity classifier: {str(e)}")
            return {"success": False, "error": str(e)}

    def _prepare_opportunity_features(
        self,
        opportunities: List[Dict]
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Prepara features para clasificación de oportunidades"""

        features = []
        labels = []

        for opp in opportunities:
            feature_vector = [
                opp.get("roi", 0),
                opp.get("spread", 0),
                opp.get("liquidity", 0),
                opp.get("volatility", 0),
                opp.get("market_quality_score", 0),
                opp.get("estimated_execution_time", 0),
                opp.get("estimated_slippage", 0),
                opp.get("volume_ratio", 1),
            ]

            # Label basado en resultado real
            label = self._classify_opportunity_label(opp)

            features.append(feature_vector)
            labels.append(label)

        return np.array(features), np.array(labels)

    def _classify_opportunity_label(self, opportunity: Dict) -> int:
        """
        Clasifica una oportunidad en una de 4 categorías

        0 = POOR
        1 = MODERATE
        2 = GOOD
        3 = EXCELLENT
        """

        roi = opportunity.get("roi", 0)
        success = opportunity.get("executed_successfully", True)
        actual_profit = opportunity.get("actual_profit", roi)

        if not success or actual_profit < 0:
            return 0  # POOR

        if actual_profit >= 5.0:
            return 3  # EXCELLENT
        elif actual_profit >= 3.0:
            return 2  # GOOD
        elif actual_profit >= 1.0:
            return 1  # MODERATE
        else:
            return 0  # POOR

    def classify_opportunity(self, opportunity_data: Dict) -> Dict:
        """
        Clasifica una oportunidad de trading en tiempo real

        Retorna probabilidad de cada clase y recomendación
        """

        if self.opportunity_classifier is None:
            # Si no hay modelo entrenado, usar heurística simple
            return self._classify_opportunity_heuristic(opportunity_data)

        try:
            # Preparar features
            features = np.array([[
                opportunity_data.get("roi", 0),
                opportunity_data.get("spread", 0),
                opportunity_data.get("liquidity", 0),
                opportunity_data.get("volatility", 0),
                opportunity_data.get("market_quality_score", 0),
                opportunity_data.get("estimated_execution_time", 0),
                opportunity_data.get("estimated_slippage", 0),
                opportunity_data.get("volume_ratio", 1),
            ]])

            # Escalar
            features_scaled = self.opportunity_scaler.transform(features)

            # Predecir
            prediction = self.opportunity_classifier.predict(features_scaled)[0]
            probabilities = self.opportunity_classifier.predict_proba(features_scaled)[0]

            class_names = ["POOR", "MODERATE", "GOOD", "EXCELLENT"]
            predicted_class = class_names[prediction]

            # Probabilidades por clase
            class_probabilities = {
                class_names[i]: float(prob) for i, prob in enumerate(probabilities)
            }

            return {
                "success": True,
                "classification": predicted_class,
                "confidence": float(max(probabilities)),
                "probabilities": class_probabilities,
                "recommendation": self._generate_classification_recommendation(
                    predicted_class,
                    max(probabilities)
                ),
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error classifying opportunity: {str(e)}")
            return {"success": False, "error": str(e)}

    def _classify_opportunity_heuristic(self, opportunity_data: Dict) -> Dict:
        """Clasificación heurística cuando no hay modelo entrenado"""

        roi = opportunity_data.get("roi", 0)
        liquidity = opportunity_data.get("liquidity", 0)
        market_quality = opportunity_data.get("market_quality_score", 0)

        # Reglas simples
        if roi >= 5.0 and liquidity > 5000 and market_quality >= 70:
            classification = "EXCELLENT"
            confidence = 0.85
        elif roi >= 3.0 and liquidity > 2000 and market_quality >= 50:
            classification = "GOOD"
            confidence = 0.75
        elif roi >= 1.0 and liquidity > 500:
            classification = "MODERATE"
            confidence = 0.65
        else:
            classification = "POOR"
            confidence = 0.60

        return {
            "success": True,
            "classification": classification,
            "confidence": confidence,
            "method": "heuristic",
            "recommendation": self._generate_classification_recommendation(
                classification,
                confidence
            ),
            "timestamp": datetime.utcnow().isoformat(),
        }

    def detect_price_anomalies(self, price_history: List[Dict]) -> Dict:
        """
        Detecta anomalías en series de precios usando Isolation Forest

        Útil para identificar:
        - Flash crashes
        - Pump and dumps
        - Errores de precio
        - Manipulación
        """

        if len(price_history) < 50:
            return {
                "success": False,
                "error": "Insufficient price history (minimum 50 samples)"
            }

        try:
            # Preparar features
            features = []
            for price_point in price_history:
                features.append([
                    price_point.get("price", 0),
                    price_point.get("volume", 0),
                    price_point.get("spread", 0),
                    price_point.get("price_change_pct", 0),
                ])

            X = np.array(features)

            # Entrenar Isolation Forest
            anomaly_detector = IsolationForest(
                contamination=0.1,  # 10% esperado de anomalías
                random_state=42
            )

            predictions = anomaly_detector.fit_predict(X)
            anomaly_scores = anomaly_detector.score_samples(X)

            # Identificar anomalías (prediction = -1)
            anomalies = []
            for i, (pred, score) in enumerate(zip(predictions, anomaly_scores)):
                if pred == -1:
                    anomalies.append({
                        "index": i,
                        "timestamp": price_history[i].get("timestamp"),
                        "price": price_history[i].get("price"),
                        "anomaly_score": float(score),
                        "severity": self._classify_anomaly_severity(score)
                    })

            return {
                "success": True,
                "total_samples": len(price_history),
                "anomalies_detected": len(anomalies),
                "anomaly_rate": len(anomalies) / len(price_history) * 100,
                "anomalies": anomalies[-10:],  # Últimas 10 anomalías
                "interpretation": self._interpret_anomalies(len(anomalies), len(price_history)),
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error detecting anomalies: {str(e)}")
            return {"success": False, "error": str(e)}

    def predict_optimal_timing(self, market_conditions: Dict) -> Dict:
        """
        Predice el timing óptimo para ejecutar una operación

        Considera:
        - Spread previsto
        - Liquidez esperada
        - Volatilidad
        - Patrones históricos por hora del día
        """

        try:
            current_hour = datetime.utcnow().hour
            current_spread = market_conditions.get("current_spread", 0)

            # Analizar próximas 6 horas
            timing_scores = []

            for hour_offset in range(0, 6):
                future_hour = (current_hour + hour_offset) % 24

                # Score basado en patrones históricos
                hour_score = self._get_hour_quality_score(future_hour)

                # Ajustar por condiciones actuales
                liquidity_score = min(100, market_conditions.get("liquidity", 0) / 100)
                volatility_penalty = market_conditions.get("volatility", 0) * 10

                total_score = hour_score + liquidity_score - volatility_penalty

                timing_scores.append({
                    "hour_offset": hour_offset,
                    "hour_utc": future_hour,
                    "score": total_score,
                    "recommendation": "OPTIMAL" if total_score >= 80 else (
                        "GOOD" if total_score >= 60 else "AVOID"
                    )
                })

            # Ordenar por score
            timing_scores.sort(key=lambda x: x["score"], reverse=True)

            best_timing = timing_scores[0]

            return {
                "success": True,
                "current_hour_utc": current_hour,
                "best_timing": best_timing,
                "all_timings": timing_scores,
                "recommendation": self._generate_timing_recommendation(best_timing),
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error predicting optimal timing: {str(e)}")
            return {"success": False, "error": str(e)}

    # Helper methods

    def _get_hour_of_day(self, timestamp) -> int:
        """Extrae hora del día (0-23)"""
        if isinstance(timestamp, str):
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        elif isinstance(timestamp, datetime):
            dt = timestamp
        else:
            dt = datetime.utcnow()
        return dt.hour

    def _get_day_of_week(self, timestamp) -> int:
        """Extrae día de la semana (0-6)"""
        if isinstance(timestamp, str):
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        elif isinstance(timestamp, datetime):
            dt = timestamp
        else:
            dt = datetime.utcnow()
        return dt.weekday()

    def _calculate_prediction_confidence(
        self,
        current_value: float,
        predicted_value: float
    ) -> float:
        """Calcula confidence de predicción basado en desviación"""

        deviation = abs(predicted_value - current_value) / max(current_value, 0.01)

        if deviation < 0.1:
            return 0.95
        elif deviation < 0.25:
            return 0.85
        elif deviation < 0.5:
            return 0.70
        else:
            return 0.50

    def _generate_spread_recommendation(
        self,
        current_spread: float,
        predicted_spread: float
    ) -> str:
        """Genera recomendación basada en predicción de spread"""

        change = predicted_spread - current_spread

        if change < -0.3:
            return "ESPERAR - El spread probablemente se reducirá pronto"
        elif change > 0.3:
            return "EJECUTAR AHORA - El spread podría aumentar"
        else:
            return "NEUTRAL - No se espera cambio significativo en el spread"

    def _generate_classification_recommendation(
        self,
        classification: str,
        confidence: float
    ) -> str:
        """Genera recomendación basada en clasificación"""

        if classification == "EXCELLENT" and confidence > 0.8:
            return "🚀 EJECUTAR INMEDIATAMENTE - Oportunidad excelente con alta confidence"
        elif classification == "GOOD" and confidence > 0.7:
            return "✅ EJECUTAR - Buena oportunidad"
        elif classification == "MODERATE":
            return "⚠️ EVALUAR - Oportunidad moderada, verificar condiciones"
        else:
            return "❌ EVITAR - Baja probabilidad de éxito"

    def _classify_anomaly_severity(self, anomaly_score: float) -> str:
        """Clasifica severidad de anomalía"""
        if anomaly_score < -0.5:
            return "CRITICAL"
        elif anomaly_score < -0.3:
            return "HIGH"
        elif anomaly_score < -0.1:
            return "MEDIUM"
        else:
            return "LOW"

    def _interpret_anomalies(self, num_anomalies: int, total_samples: int) -> str:
        """Interpreta cantidad de anomalías detectadas"""

        rate = num_anomalies / total_samples * 100

        if rate > 20:
            return "Alta tasa de anomalías - Mercado muy volátil o datos inconsistentes"
        elif rate > 10:
            return "Tasa moderada de anomalías - Volatilidad normal del mercado"
        elif rate > 5:
            return "Baja tasa de anomalías - Mercado relativamente estable"
        else:
            return "Muy pocas anomalías - Mercado estable y predecible"

    def _get_hour_quality_score(self, hour: int) -> float:
        """
        Score de calidad por hora del día basado en patrones típicos

        Horarios típicos de alta liquidez:
        - 14:00-22:00 UTC (horario de América Latina)
        """

        # Horario prime: 14:00 - 22:00 UTC
        if 14 <= hour <= 22:
            return 90
        # Horario bueno: 12:00-14:00, 22:00-00:00
        elif 12 <= hour < 14 or 22 < hour <= 24:
            return 70
        # Horario bajo: madrugada
        else:
            return 40

    def _generate_timing_recommendation(self, best_timing: Dict) -> str:
        """Genera recomendación de timing"""

        hour_offset = best_timing["hour_offset"]
        score = best_timing["score"]

        if hour_offset == 0 and score >= 70:
            return "EJECUTAR AHORA - Condiciones actuales son óptimas"
        elif hour_offset <= 1 and score >= 80:
            return f"ESPERAR {hour_offset} HORA(S) - Mejores condiciones pronto"
        elif score >= 60:
            return f"CONSIDERAR ESPERAR - Mejores condiciones en ~{hour_offset} horas"
        else:
            return "EVITAR - Condiciones subóptimas en horizonte visible"
