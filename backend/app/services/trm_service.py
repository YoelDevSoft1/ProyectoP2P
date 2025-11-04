"""
Servicio para obtener la Tasa Representativa del Mercado (TRM) de Colombia.
"""
import httpx
from datetime import datetime, timedelta
from typing import Optional, Dict
import structlog

from app.core.config import settings

logger = structlog.get_logger()


class TRMService:
    """
    Servicio para obtener TRM desde la API del gobierno colombiano.
    API oficial: https://www.datos.gov.co/
    """

    def __init__(self):
        self.api_url = settings.TRM_API_URL
        self.cache = {}
        self.cache_expiry = None

    async def get_current_trm(self) -> float:
        """
        Obtener TRM actual.

        Returns:
            Valor de TRM (COP por USD)
        """
        # Verificar cache
        if self.cache_expiry and datetime.utcnow() < self.cache_expiry:
            if "current" in self.cache:
                return self.cache["current"]

        try:
            async with httpx.AsyncClient() as client:
                # La API de datos.gov.co usa formato YYYY-MM-DD
                today = datetime.utcnow().strftime("%Y-%m-%d")

                # Query para obtener TRM de hoy
                response = await client.get(
                    self.api_url,
                    params={
                        "$where": f"vigenciadesde='{today}'",
                        "$limit": 1,
                        "$order": "vigenciadesde DESC"
                    },
                    timeout=10.0
                )

                response.raise_for_status()
                data = response.json()

                if data and len(data) > 0:
                    trm_value = float(data[0].get("valor", 0))

                    # Guardar en cache por 5 minutos
                    self.cache["current"] = trm_value
                    self.cache_expiry = datetime.utcnow() + timedelta(
                        seconds=settings.TRM_UPDATE_INTERVAL
                    )

                    logger.info("TRM fetched successfully", trm=trm_value, date=today)
                    return trm_value
                else:
                    # Si no hay datos de hoy, buscar el más reciente
                    return await self._get_latest_trm()

        except Exception as e:
            logger.error("Error fetching TRM", error=str(e))
            # Retornar valor de cache si existe
            if "current" in self.cache:
                logger.warning("Using cached TRM due to API error")
                return self.cache["current"]
            # Valor por defecto (aproximado)
            return 4000.0

    async def _get_latest_trm(self) -> float:
        """
        Obtener el TRM más reciente disponible.

        Returns:
            Valor de TRM más reciente
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.api_url,
                    params={
                        "$limit": 1,
                        "$order": "vigenciadesde DESC"
                    },
                    timeout=10.0
                )

                response.raise_for_status()
                data = response.json()

                if data and len(data) > 0:
                    trm_value = float(data[0].get("valor", 0))
                    vigencia = data[0].get("vigenciadesde", "")

                    logger.info("Latest TRM fetched", trm=trm_value, date=vigencia)
                    return trm_value

        except Exception as e:
            logger.error("Error fetching latest TRM", error=str(e))

        return 4000.0  # Valor por defecto

    async def get_trm_history(self, days: int = 30) -> list:
        """
        Obtener historial de TRM.

        Args:
            days: Número de días hacia atrás

        Returns:
            Lista de registros de TRM
        """
        try:
            async with httpx.AsyncClient() as client:
                end_date = datetime.utcnow()
                start_date = end_date - timedelta(days=days)

                response = await client.get(
                    self.api_url,
                    params={
                        "$where": f"vigenciadesde>='{start_date.strftime('%Y-%m-%d')}' AND vigenciadesde<='{end_date.strftime('%Y-%m-%d')}'",
                        "$order": "vigenciadesde ASC",
                        "$limit": days
                    },
                    timeout=15.0
                )

                response.raise_for_status()
                data = response.json()

                history = []
                for record in data:
                    history.append({
                        "date": record.get("vigenciadesde", ""),
                        "value": float(record.get("valor", 0))
                    })

                return history

        except Exception as e:
            logger.error("Error fetching TRM history", error=str(e))
            return []

    async def get_trm_with_history(self, history_days: int = 7) -> Dict:
        """
        Obtener TRM actual con historial.

        Args:
            history_days: Días de historial

        Returns:
            Dict con TRM actual y historial
        """
        current_trm = await self.get_current_trm()
        history = await self.get_trm_history(history_days)

        # Calcular cambio porcentual
        percentage_change = 0
        if history and len(history) > 0:
            first_value = history[0]["value"]
            if first_value > 0:
                percentage_change = ((current_trm - first_value) / first_value) * 100

        return {
            "current": current_trm,
            "currency": "COP/USD",
            "last_updated": datetime.utcnow().isoformat(),
            "change_percentage": round(percentage_change, 2),
            "history": history
        }

    async def get_usd_cop_rate(self) -> float:
        """
        Alias de get_current_trm para compatibilidad.

        Returns:
            Tasa USD a COP
        """
        return await self.get_current_trm()
