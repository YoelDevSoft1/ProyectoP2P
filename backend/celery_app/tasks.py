"""
Tareas asíncronas de Celery.
"""
from celery_app.worker import celery_app
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import structlog
import asyncio
from typing import Callable, Any, List, Dict
from requests.exceptions import RequestException, Timeout, ConnectionError as RequestsConnectionError
from httpx import TimeoutException, ConnectError

from app.core.database import SessionLocal
from app.core.config import settings
from app.core.idempotency import idempotent_celery_task
from app.models.price_history import PriceHistory
from app.models.alert import Alert, AlertType, AlertPriority
from app.services.binance_service import BinanceService
from app.services.trm_service import TRMService

logger = structlog.get_logger()


def get_db():
    """Helper para obtener sesión de DB"""
    db = SessionLocal()
    try:
        return db
    finally:
        pass  # No cerramos aquí, se cierra en el finally del task


def run_async_task_safe(coro: Callable[..., Any], *args, **kwargs) -> Any:
    """
    Helper para ejecutar tareas asíncronas desde Celery de manera segura.
    Maneja correctamente el ciclo de vida del event loop y recursos.
    
    Cada worker de Celery necesita su propio event loop, y asyncio.run()
    crea uno nuevo y lo cierra correctamente al finalizar.
    """
    try:
        # Usar asyncio.run() que crea un nuevo event loop y lo cierra correctamente
        # Esto asegura que cada tarea tenga su propio loop limpio
        return asyncio.run(coro(*args, **kwargs))
    except RuntimeError as e:
        # Si ya hay un event loop corriendo (no debería pasar en Celery workers)
        # crear uno nuevo y ejecutar en él
        if "asyncio.run() cannot be called from a running event loop" in str(e):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(coro(*args, **kwargs))
            finally:
                loop.close()
        else:
            raise


@celery_app.task(
    name="celery_app.tasks.update_prices",
    autoretry_for=(
        RequestsConnectionError,
        RequestException,
        Timeout,
        TimeoutException,
        ConnectError,
        ConnectionError,
    ),
    retry_kwargs={'max_retries': 3, 'countdown': 5},
    retry_backoff=True,
    retry_backoff_max=60,
    retry_jitter=True,
    acks_late=True,
    reject_on_worker_lost=True,
)
def update_prices():
    """
    Actualizar precios de P2P y guardar en base de datos.

    Retry automático:
    - Máximo 3 reintentos
    - Espera inicial: 5 segundos
    - Backoff exponencial hasta 60 segundos
    - Jitter para evitar thundering herd
    """
    db = get_db()
    try:
        async def _update_prices_async():
            """Función async interna para manejar todas las llamadas async"""
            binance_service = BinanceService()
            trm_service = TRMService()
            try:
                results = []

                # Usar las propiedades que parsean correctamente desde variables de entorno
                # Asegurarse de que estamos obteniendo listas, no strings
                try:
                    assets_raw = settings.p2p_monitored_assets_list
                    fiats_raw = settings.p2p_monitored_fiats_list
                    
                    # Debug: verificar qué tipo de datos tenemos
                    logger.debug(
                        "Parsing monitored assets and fiats",
                        assets_raw_type=type(assets_raw).__name__,
                        fiats_raw_type=type(fiats_raw).__name__,
                        assets_raw_value=str(assets_raw)[:100],
                        fiats_raw_value=str(fiats_raw)[:100],
                        p2p_assets_str=settings.P2P_MONITORED_ASSETS,
                        p2p_fiats_str=settings.P2P_MONITORED_FIATS
                    )
                    
                    # Asegurarse de que son listas
                    if isinstance(assets_raw, str):
                        # Si es string, parsearlo manualmente
                        assets = [a.strip().upper() for a in assets_raw.split(",") if a.strip()]
                    elif isinstance(assets_raw, list):
                        assets = list(dict.fromkeys([str(a).strip().upper() for a in assets_raw if a]))
                    else:
                        assets = ["USDT"]
                    
                    if isinstance(fiats_raw, str):
                        # Si es string, parsearlo manualmente
                        fiats = [f.strip().upper() for f in fiats_raw.split(",") if f.strip()]
                    elif isinstance(fiats_raw, list):
                        fiats = list(dict.fromkeys([str(f).strip().upper() for f in fiats_raw if f]))
                    else:
                        fiats = ["COP", "VES"]
                    
                    # Filtrar valores vacíos
                    assets = [a for a in assets if a and len(a) > 0]
                    fiats = [f for f in fiats if f and len(f) > 0]
                    
                    if not assets:
                        assets = ["USDT"]
                    if not fiats:
                        fiats = ["COP", "VES"]
                        
                except Exception as e:
                    logger.error("Error parsing assets/fiats, using defaults", error=str(e))
                    assets = ["USDT"]
                    fiats = ["COP", "VES"]

                # Filtrar pares inválidos antes de procesarlos
                valid_pairs = []
                for asset in assets:
                    for fiat in fiats:
                        if binance_service.is_valid_pair(asset, fiat):
                            valid_pairs.append((asset, fiat))
                        else:
                            logger.debug(
                                "Skipping invalid pair in price update",
                                asset=asset,
                                fiat=fiat
                            )

                logger.info(
                    "Updating prices",
                    total_pairs=len(valid_pairs),
                    assets=assets,
                    fiats=fiats
                )

                trm_cache = None

                # Procesar pares en lotes para evitar rate limiting
                # Procesar máximo 8 pares a la vez (4 assets × 2 fiats o similar)
                batch_size = 8
                for i in range(0, len(valid_pairs), batch_size):
                    batch = valid_pairs[i:i + batch_size]
                    
                    # Procesar batch en paralelo pero con rate limiting incorporado
                    batch_tasks = []
                    for asset, fiat in batch:
                        batch_tasks.append(
                            binance_service.get_market_depth(
                                asset,
                                fiat,
                                rows=settings.P2P_ANALYSIS_ROWS,
                            )
                        )
                    
                    # Ejecutar batch con gather (rate limiting está en el servicio)
                    batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                    
                    # Procesar resultados del batch
                    for (asset, fiat), depth in zip(batch, batch_results):
                        if isinstance(depth, Exception):
                            logger.error(
                                "Error updating price for pair",
                                asset=asset,
                                fiat=fiat,
                                error=str(depth),
                                exc_info=True
                            )
                            results.append({"asset": asset, "fiat": fiat, "error": str(depth)})
                            continue
                        
                        # Verificar si hay error en la respuesta
                        if depth.get("error"):
                            logger.debug(
                                "Pair returned error",
                                asset=asset,
                                fiat=fiat,
                                error=depth.get("error")
                            )
                            continue
                        
                        best_buy = depth.get("best_buy")
                        best_sell = depth.get("best_sell")

                        if not (best_buy and best_sell):
                            logger.debug(
                                "Incomplete market depth (no data available)",
                                asset=asset,
                                fiat=fiat,
                            )
                            # No agregar a resultados si no hay datos
                            continue

                        trm = None
                        if fiat == "COP":
                            if trm_cache is None:
                                trm_cache = await trm_service.get_current_trm()
                            trm = trm_cache

                        results.append({
                            "asset": asset,
                            "fiat": fiat,
                            "best_buy": best_buy,
                            "best_sell": best_sell,
                            "depth": depth,
                            "trm": trm,
                        })
                    
                    # Pequeño delay entre batches para evitar rate limiting
                    if i + batch_size < len(valid_pairs):
                        await asyncio.sleep(0.5)  # 500ms entre batches

                return results
            finally:
                # Cerrar cliente HTTP dentro del mismo event loop
                await binance_service.aclose()
        
        # Ejecutar función async de manera segura
        results = run_async_task_safe(_update_prices_async)
        
        # Guardar resultados en base de datos
        for result in results:
            if "error" in result:
                continue

            fiat = result["fiat"]
            asset = result.get("asset", "USDT")
            best_buy = result["best_buy"]
            best_sell = result["best_sell"]
            depth = result["depth"]
            
            try:
                price_record = PriceHistory(
                    asset=asset,
                    fiat=fiat,
                    bid_price=best_buy["price"],
                    ask_price=best_sell["price"],
                    avg_price=(best_buy["price"] + best_sell["price"]) / 2,
                    spread=depth["spread_percent"],
                    source="binance_p2p",
                    trm_rate=result.get("trm")
                )

                db.add(price_record)
                db.commit()

                logger.info(
                    "Price updated",
                    asset=asset,
                    fiat=fiat,
                    bid=best_buy["price"],
                    ask=best_sell["price"]
                )
            except Exception as e:
                logger.error("Error saving price to database", fiat=fiat, error=str(e))
                db.rollback()

        updated_pairs = sorted({
            f"{result.get('asset', 'USDT')}/{result['fiat']}"
            for result in results
            if "error" not in result
        })

        return {"status": "success", "updated": updated_pairs}

    except Exception as e:
        logger.error("Error in update_prices task", error=str(e))
        db.rollback()
        return {"status": "error", "error": str(e)}
    finally:
        db.close()


@celery_app.task(
    name="celery_app.tasks.update_trm",
    autoretry_for=(
        RequestsConnectionError,
        RequestException,
        Timeout,
        TimeoutException,
        ConnectError,
        ConnectionError,
    ),
    retry_kwargs={'max_retries': 3, 'countdown': 10},
    retry_backoff=True,
    retry_backoff_max=120,
    retry_jitter=True,
    acks_late=True,
)
def update_trm():
    """
    Actualizar TRM desde la API del gobierno.

    Retry automático con backoff exponencial.
    """
    try:
        trm_service = TRMService()
        
        async def _update_trm_async():
            return await trm_service.get_current_trm()
        
        trm = run_async_task_safe(_update_trm_async)

        logger.info("TRM updated", value=trm)
        return {"status": "success", "trm": trm}

    except Exception as e:
        logger.error("Error updating TRM", error=str(e))
        return {"status": "error", "error": str(e)}


@celery_app.task(
    name="celery_app.tasks.analyze_spread_opportunities",
    autoretry_for=(
        RequestsConnectionError,
        RequestException,
        Timeout,
        TimeoutException,
        ConnectError,
        ConnectionError,
    ),
    retry_kwargs={'max_retries': 2, 'countdown': 15},
    retry_backoff=True,
    retry_backoff_max=60,
    retry_jitter=True,
    acks_late=True,
)
@idempotent_celery_task(ttl=55, key_prefix="spread_analysis")  # TTL < intervalo (60s)
def analyze_spread_opportunities():
    """
    Analizar spreads y detectar oportunidades de arbitraje.
    Crear alertas si se encuentran oportunidades.

    Retry automático con backoff (máx 2 reintentos para evitar duplicados).
    IDEMPOTENTE: TTL de 55 segundos previene ejecuciones duplicadas.
    """
    db = get_db()
    try:
        from app.services.notification_service import NotificationService

        async def _analyze_spread_async():
            """Función async interna para manejar todas las llamadas async"""
            binance_service = BinanceService()
            notif_service = NotificationService()
            
            try:
                results = []
                # Usar las propiedades que parsean correctamente desde variables de entorno
                # Asegurarse de que estamos obteniendo listas, no strings
                try:
                    assets_raw = settings.p2p_monitored_assets_list
                    fiats_raw = settings.p2p_monitored_fiats_list
                    
                    # Asegurarse de que son listas
                    if isinstance(assets_raw, str):
                        assets = [a.strip().upper() for a in assets_raw.split(",") if a.strip()]
                    elif isinstance(assets_raw, list):
                        assets = list(dict.fromkeys([str(a).strip().upper() for a in assets_raw if a]))
                    else:
                        assets = ["USDT"]
                    
                    if isinstance(fiats_raw, str):
                        fiats = [f.strip().upper() for f in fiats_raw.split(",") if f.strip()]
                    elif isinstance(fiats_raw, list):
                        fiats = list(dict.fromkeys([str(f).strip().upper() for f in fiats_raw if f]))
                    else:
                        fiats = ["COP", "VES"]
                    
                    # Filtrar valores vacíos
                    assets = [a for a in assets if a and len(a) > 0]
                    fiats = [f for f in fiats if f and len(f) > 0]
                    
                    if not assets:
                        assets = ["USDT"]
                    if not fiats:
                        fiats = ["COP", "VES"]
                except Exception as e:
                    logger.error("Error parsing assets/fiats in spread analysis, using defaults", error=str(e))
                    assets = ["USDT"]
                    fiats = ["COP", "VES"]

                def build_opportunities(depth: dict, asset_code: str, fiat_code: str) -> list:
                    """Derivar mejores spreads usando profundidad de mercado."""
                    buy_levels = depth.get("buy_depth") or []
                    sell_levels = depth.get("sell_depth") or []

                    raw_opportunities = []
                    max_levels = max(settings.P2P_TOP_SPREADS * 2, 3)

                    for buy in buy_levels[:max_levels]:
                        buy_price = buy.get("price")
                        if not buy_price or buy_price <= 0:
                            continue

                        for sell in sell_levels[:max_levels]:
                            sell_price = sell.get("price")
                            if not sell_price or sell_price <= 0:
                                continue

                            spread = ((sell_price - buy_price) / buy_price) * 100
                            if spread <= 0:
                                continue

                            raw_opportunities.append({
                                "asset": asset_code,
                                "fiat": fiat_code,
                                "spread": round(spread, 2),
                                "buy_price": round(buy_price, 2),
                                "sell_price": round(sell_price, 2),
                                "buy_available": round(buy.get("available", 0.0), 2),
                                "sell_available": round(sell.get("available", 0.0), 2),
                                "buy_merchant": buy.get("merchant"),
                                "sell_merchant": sell.get("merchant"),
                                "buy_payment_methods": buy.get("payment_methods", []),
                                "sell_payment_methods": sell.get("payment_methods", []),
                            })

                    raw_opportunities.sort(key=lambda item: item["spread"], reverse=True)

                    top_opportunities = []
                    seen_keys = set()
                    for opportunity in raw_opportunities:
                        dedupe_key = (
                            opportunity["buy_price"],
                            opportunity["sell_price"],
                            opportunity.get("buy_merchant"),
                            opportunity.get("sell_merchant"),
                        )
                        if dedupe_key in seen_keys:
                            continue
                        seen_keys.add(dedupe_key)
                        top_opportunities.append(opportunity)
                        if len(top_opportunities) >= settings.P2P_TOP_SPREADS:
                            break

                    return top_opportunities

                # Filtrar pares inválidos antes de procesarlos
                valid_pairs = []
                for asset in assets:
                    for fiat in fiats:
                        if binance_service.is_valid_pair(asset, fiat):
                            valid_pairs.append((asset, fiat))

                for asset, fiat in valid_pairs:
                    try:
                        depth = await binance_service.get_market_depth(
                            asset,
                            fiat,
                            rows=settings.P2P_ANALYSIS_ROWS,
                        )
                        
                        # Verificar si hay error en la respuesta
                        if depth.get("error"):
                            logger.debug(
                                "Pair returned error in spread analysis",
                                asset=asset,
                                fiat=fiat,
                                error=depth.get("error")
                            )
                            continue
                            
                    except Exception as exc:  # noqa: BLE001
                        logger.error(
                            "Error fetching depth for spread analysis",
                            asset=asset,
                            fiat=fiat,
                            error=str(exc),
                            exc_info=True
                        )
                        continue

                    opportunities = build_opportunities(depth, asset, fiat)

                    for idx, opportunity_data in enumerate(opportunities, start=1):
                        opportunity_data["rank"] = idx
                        spread = opportunity_data["spread"]
                        opportunity_data.setdefault("potential_profit_percent", spread)

                        results.append({
                            "asset": asset,
                            "fiat": fiat,
                            "spread": spread,
                            "depth": depth,
                            "opportunity_data": opportunity_data,
                        })

                        if spread >= settings.SPREAD_THRESHOLD:
                            try:
                                await notif_service.send_p2p_opportunity_alert(opportunity_data)
                                logger.info(
                                    "Spread opportunity notification sent",
                                    asset=asset,
                                    fiat=fiat,
                                    spread=spread,
                                    rank=idx,
                                )
                            except Exception as e:  # noqa: BLE001
                                logger.error(
                                    "Error sending notification",
                                    asset=asset,
                                    fiat=fiat,
                                    error=str(e),
                                )

                return results
            finally:
                # Cerrar cliente HTTP dentro del mismo event loop
                await binance_service.aclose()
                if 'notif_service' in locals():
                    try:
                        await notif_service.send_spread_digest(results)
                    except Exception as exc:  # noqa: BLE001
                        logger.error("Error sending spread digest", error=str(exc))

        # Ejecutar función async de manera segura
        results = run_async_task_safe(_analyze_spread_async)
        
        # Guardar alertas en base de datos
        for result in results:
            fiat = result["fiat"]
            asset = result.get("asset", "USDT")
            spread = result["spread"]
            opportunity_data = result.get("opportunity_data", {})

            buy_price = opportunity_data.get("buy_price")
            sell_price = opportunity_data.get("sell_price")
            buy_merchant = opportunity_data.get("buy_merchant") or "N/A"
            sell_merchant = opportunity_data.get("sell_merchant") or "N/A"

            try:
                alert = Alert(
                    alert_type=AlertType.SPREAD_OPPORTUNITY,
                    priority=AlertPriority.HIGH if spread >= 1.0 else AlertPriority.MEDIUM,
                    title=f"Oportunidad de spread en {asset}/{fiat}",
                    message=(
                        f"Spread de {spread}% detectado en {asset}/{fiat}. "
                        f"Compra: {buy_price} ({buy_merchant}) "
                        f"→ Venta: {sell_price} ({sell_merchant})."
                    ),
                    asset=asset,
                    fiat=fiat,
                    percentage=spread
                )
                db.add(alert)
            except Exception as e:
                logger.error("Error saving alert", fiat=fiat, asset=asset, error=str(e))

        db.commit()
        logger.info("Spread analysis completed")
        return {"status": "success"}

    except Exception as e:
        logger.error("Error analyzing spreads", error=str(e))
        db.rollback()
        return {"status": "error", "error": str(e)}
    finally:
        db.close()


@celery_app.task(
    name="celery_app.tasks.run_trading_bot",
    autoretry_for=(
        RequestsConnectionError,
        RequestException,
        Timeout,
        TimeoutException,
        ConnectError,
        ConnectionError,
    ),
    retry_kwargs={'max_retries': 1, 'countdown': 20},
    retry_backoff=False,  # No backoff para trading bot (tiempo crítico)
    acks_late=True,
    reject_on_worker_lost=True,
)
@idempotent_celery_task(ttl=55, key_prefix="trading_bot")  # TTL < intervalo (60s)
def run_trading_bot():
    """
    Ejecutar lógica del bot de trading.
    Solo ejecuta si está en modo automático o híbrido.

    Retry limitado (1 solo reintento) para evitar ejecuciones duplicadas.
    IDEMPOTENTE: CRÍTICO para prevenir trades duplicados (TTL 55s).
    """
    if settings.TRADING_MODE == "manual":
        logger.info("Trading bot skipped - manual mode enabled")
        return {"status": "skipped", "reason": "manual_mode"}

    try:
        from app.trading.bot import TradingBot

        async def _run_trading_bot_async():
            bot = TradingBot()
            return await bot.execute_trading_cycle()
        
        result = run_async_task_safe(_run_trading_bot_async)

        return result

    except Exception as e:
        logger.error("Error in trading bot", error=str(e))
        return {"status": "error", "error": str(e)}


@celery_app.task(
    name="celery_app.tasks.retrain_ml_model",
    autoretry_for=(ConnectionError,),
    retry_kwargs={'max_retries': 1, 'countdown': 300},  # 5 minutos de espera
    acks_late=True,
    time_limit=3600,  # 1 hora límite para ML training
    soft_time_limit=3300,  # 55 minutos soft limit
)
def retrain_ml_model():
    """
    Re-entrenar modelo de ML con datos recientes.

    Timeout extendido: 1 hora (tarea pesada).
    Retry limitado con 5 minutos de espera.
    """
    db = get_db()
    try:
        from app.ml.trainer import MLModelTrainer

        trainer = MLModelTrainer(db)
        result = trainer.train_model()

        logger.info("ML model retrained", metrics=result)
        return {"status": "success", "metrics": result}

    except Exception as e:
        logger.error("Error retraining ML model", error=str(e))
        return {"status": "error", "error": str(e)}
    finally:
        db.close()


@celery_app.task(
    name="celery_app.tasks.cleanup_old_data",
    bind=True,
    autoretry_for=(ConnectionError,),
    max_retries=2,
    retry_kwargs={'countdown': 60},  # 1 minuto de espera antes de reintentar
    acks_late=True,
    time_limit=600,  # 10 minutos (ajustado para ejecución cada 10 minutos)
    soft_time_limit=540  # 9 minutos
)
def cleanup_old_data():
    """
    Limpiar datos antiguos de la base de datos.
    - Mantener solo las 40 alertas más recientes (eliminar las demás)
    - Price history mayor a 90 días
    
    Esta tarea se ejecuta cada 10 minutos para mantener la base de datos limpia.

    Timeout: 10 minutos (ajustado para ejecución más frecuente).
    """
    db = get_db()
    max_alerts = 40
    try:
        # ============================================================
        # Limpiar alertas (mantener solo las 40 más recientes)
        # ============================================================
        total_alerts = db.query(Alert).count()
        deleted_alerts = 0
        alerts_kept = 0
        
        if total_alerts > max_alerts:
            # Obtener las N alertas más recientes (por created_at desc)
            recent_alerts = db.query(Alert.id).order_by(
                Alert.created_at.desc()
            ).limit(max_alerts).all()
            
            # Extraer los IDs de las alertas a mantener
            keep_ids = [alert.id for alert in recent_alerts]
            
            if keep_ids:
                # Eliminar todas las alertas excepto las N más recientes
                deleted_alerts = db.query(Alert).filter(
                    ~Alert.id.in_(keep_ids)
                ).delete(synchronize_session=False)
                alerts_kept = len(keep_ids)
                
                logger.info(
                    "Old alerts cleaned up",
                    deleted_alerts=deleted_alerts,
                    total_alerts_before=total_alerts,
                    alerts_kept=alerts_kept,
                    max_alerts=max_alerts
                )
        else:
            alerts_kept = total_alerts
            logger.info(
                "No alerts to clean up",
                total_alerts=total_alerts,
                max_alerts=max_alerts
            )
        
        # ============================================================
        # Eliminar price history antiguo (mayor a 90 días)
        # ============================================================
        cutoff_prices = datetime.utcnow() - timedelta(days=90)
        deleted_prices = db.query(PriceHistory).filter(
            PriceHistory.timestamp < cutoff_prices
        ).delete()

        # Commit de todas las operaciones
        db.commit()

        logger.info(
            "Old data cleaned up successfully",
            deleted_alerts=deleted_alerts,
            deleted_prices=deleted_prices,
            alerts_kept=alerts_kept,
            total_alerts_before=total_alerts
        )

        return {
            "status": "success",
            "deleted_alerts": deleted_alerts,
            "deleted_prices": deleted_prices,
            "alerts_kept": alerts_kept,
            "total_alerts_before": total_alerts,
            "message": f"Se eliminaron {deleted_alerts} alertas y {deleted_prices} registros de price history. Se mantuvieron {alerts_kept} alertas más recientes."
        }

    except Exception as e:
        logger.error("Error cleaning up old data", error=str(e), exc_info=True)
        db.rollback()
        return {"status": "error", "error": str(e)}
    finally:
        db.close()


@celery_app.task(
    name="celery_app.tasks.send_notification",
    autoretry_for=(
        RequestsConnectionError,
        RequestException,
        Timeout,
        TimeoutException,
        ConnectError,
        ConnectionError,
    ),
    retry_kwargs={'max_retries': 3, 'countdown': 30},
    retry_backoff=True,
    retry_backoff_max=300,  # Máx 5 minutos
    retry_jitter=True,
    acks_late=True,
)
def send_notification(title: str, message: str, priority: str = "medium"):
    """
    Enviar notificación por Telegram o email.

    Args:
        title: Título de la notificación
        message: Mensaje
        priority: low, medium, high, critical

    Retry automático agresivo (3 reintentos) para asegurar entrega.
    """
    if not settings.ENABLE_NOTIFICATIONS:
        return {"status": "skipped", "reason": "notifications_disabled"}

    try:
        from app.services.notification_service import NotificationService
        
        # Crear instancia del servicio
        notif_service = NotificationService()
        
        # Formatear mensaje con título
        formatted_message = f"*{title}*\n\n{message}"
        
        # Enviar por Telegram de forma asíncrona
        async def _send_async():
            return await notif_service.telegram_service.send_message(
                text=formatted_message,
                parse_mode="Markdown",
                priority=priority
            )
        
        # Ejecutar de forma segura en el event loop de Celery
        result = run_async_task_safe(_send_async)
        
        if result:
            logger.info("Notification sent", title=title, priority=priority)
            return {"status": "success", "method": "telegram"}
        else:
            logger.warning("Notification failed to send", title=title, priority=priority)
            return {"status": "error", "error": "Failed to send via Telegram"}

    except Exception as e:
        logger.error("Error sending notification", error=str(e), title=title)
        return {"status": "error", "error": str(e)}


@celery_app.task(
    name="celery_app.tasks.analyze_arbitrage",
    autoretry_for=(
        RequestsConnectionError,
        RequestException,
        Timeout,
        TimeoutException,
        ConnectError,
        ConnectionError,
    ),
    retry_kwargs={'max_retries': 2, 'countdown': 20},
    retry_backoff=True,
    retry_backoff_max=90,
    retry_jitter=True,
    acks_late=True,
)
@idempotent_celery_task(ttl=110, key_prefix="arbitrage_analysis")  # TTL < intervalo (120s)
def analyze_arbitrage():
    """
    Analizar oportunidades de arbitraje Spot-P2P.
    Enviar alertas si hay oportunidades rentables.

    Retry automático (máx 2 reintentos para evitar alertas duplicadas).
    IDEMPOTENTE: TTL de 110 segundos previene alertas duplicadas.
    """
    db = get_db()
    try:
        from app.services.arbitrage_service import ArbitrageService
        from app.services.notification_service import NotificationService

        async def _analyze_arbitrage_async() -> List[Dict[str, Any]]:
            """Función async interna para manejar todas las llamadas async"""
            from app.services.binance_service import BinanceService
            
            arb_service = ArbitrageService()
            notif_service = NotificationService()
            binance_service = BinanceService()  # Para validar pares

            # Usar las propiedades que parsean correctamente desde variables de entorno
            # Asegurarse de que estamos obteniendo listas, no strings
            try:
                assets_raw = settings.arbitrage_monitored_assets_list or settings.p2p_monitored_assets_list
                fiats_raw = settings.arbitrage_monitored_fiats_list or settings.p2p_monitored_fiats_list
                
                # Asegurarse de que son listas
                if isinstance(assets_raw, str):
                    assets = [a.strip().upper() for a in assets_raw.split(",") if a.strip()]
                elif isinstance(assets_raw, list):
                    assets = list(dict.fromkeys([str(a).strip().upper() for a in assets_raw if a]))
                else:
                    assets = ["USDT"]
                
                if isinstance(fiats_raw, str):
                    fiats = [f.strip().upper() for f in fiats_raw.split(",") if f.strip()]
                elif isinstance(fiats_raw, list):
                    fiats = list(dict.fromkeys([str(f).strip().upper() for f in fiats_raw if f]))
                else:
                    fiats = ["COP", "VES"]
                
                # Filtrar valores vacíos
                assets = [a for a in assets if a and len(a) > 0]
                fiats = [f for f in fiats if f and len(f) > 0]
                
                if not assets:
                    assets = ["USDT"]
                if not fiats:
                    fiats = ["COP", "VES"]
            except Exception as e:
                logger.error("Error parsing assets/fiats in arbitrage analysis, using defaults", error=str(e))
                assets = ["USDT"]
                fiats = ["COP", "VES"]

            # Filtrar pares inválidos antes de procesarlos
            valid_pairs = []
            for asset in assets:
                for fiat in fiats:
                    if binance_service.is_valid_pair(asset, fiat):
                        valid_pairs.append((asset, fiat))
                    else:
                        logger.debug(
                            "Skipping invalid pair in arbitrage task",
                            asset=asset,
                            fiat=fiat
                        )
            
            # Si no hay pares válidos, retornar vacío
            if not valid_pairs:
                logger.warning(
                    "No valid pairs found for arbitrage analysis",
                    assets=assets,
                    fiats=fiats
                )
                return []
            
            # Actualizar assets y fiats a solo los válidos
            assets = list(set(asset for asset, _ in valid_pairs))
            fiats = list(set(fiat for _, fiat in valid_pairs))

            top_limit = settings.ARBITRAGE_TOP_OPPORTUNITIES or 5
            
            try:
                await binance_service.aclose()
            except Exception:
                pass

            try:
                ranked = await arb_service.get_ranked_opportunities(
                    assets=assets,
                    fiats=fiats,
                    top_n=top_limit,
                    include_triangle=True,
                )
            finally:
                await arb_service.aclose()

            profitable = [
                {**opportunity, "rank": index}
                for index, opportunity in enumerate(
                    (
                        opp
                        for opp in ranked
                        if (opp.get("score") or 0) >= settings.ARBITRAGE_MIN_PROFIT
                    ),
                    start=1,
                )
            ]

            if profitable:
                try:
                    await notif_service.send_arbitrage_digest(profitable)
                except Exception as exc:  # noqa: BLE001
                    logger.error("Error sending arbitrage digest", error=str(exc))

            return profitable

        results = run_async_task_safe(_analyze_arbitrage_async)

        if not results:
            logger.info("Arbitrage analysis completed", opportunities=0)
            return {"status": "success", "opportunities": 0}

        def fmt_number(value: Any, decimals: int = 2) -> str:
            try:
                return f"{float(value):,.{decimals}f}"
            except (TypeError, ValueError):
                return f"{0:.{decimals}f}"

        def fmt_percent(value: Any) -> str:
            try:
                return f"{float(value):.2f}%"
            except (TypeError, ValueError):
                return "0.00%"

        saved = 0
        for opportunity in results:
            strategy = opportunity.get("strategy", "spot_to_p2p")
            label = opportunity.get("label", "")
            asset = opportunity.get("asset", "USDT")
            fiat = opportunity.get("fiat", "USD")
            score = opportunity.get("score", 0.0)
            details = opportunity.get("details", {})
            rank = opportunity.get("rank", 0)

            if strategy == "spot_to_p2p":
                message = (
                    f"{label} — Spot→P2P rank #{rank}. Profit neto {fmt_percent(score)}. "
                    f"Spot ${fmt_number(details.get('spot_price_usd'), 4)} | "
                    f"P2P {fmt_number(details.get('p2p_sell_price_fiat'))} {fiat}. "
                    f"Liquidez: {fmt_number(details.get('p2p_sell_available'))} {asset}."
                )
            elif strategy == "cross_currency":
                buy_quote = details.get("buy_quote", {})
                sell_quote = details.get("sell_quote", {})
                message = (
                    f"Ruta {label} rank #{rank}. Profit estimado {fmt_percent(score)}. "
                    f"Compra USDT en {details.get('fiat_from')} a {fmt_number(buy_quote.get('price'))} "
                    f"y vende en {details.get('fiat_to')} a {fmt_number(sell_quote.get('price'))}. "
                    f"Liquidez: {fmt_number(details.get('max_volume'))} {asset}."
                )
            elif strategy == "triangle_arbitrage":
                step1 = details.get("step_1", {})
                step2 = details.get("step_2", {})
                message = (
                    f"Ruta {label} rank #{rank}. ROI {fmt_percent(score)}. "
                    f"Paso 1: {step1.get('action')} @ {fmt_number(step1.get('price'))}. "
                    f"Paso 2: {step2.get('action')} @ {fmt_number(step2.get('price'))}."
                )
            else:
                message = f"{label} rank #{rank}. Profit estimado {fmt_percent(score)}."

            alert = Alert(
                alert_type=AlertType.ARBITRAGE,
                priority=AlertPriority.HIGH if score >= (settings.ARBITRAGE_MIN_PROFIT + 1) else AlertPriority.MEDIUM,
                title=f"Arbitraje {strategy.replace('_', ' ').title()} #{rank}",
                message=message,
                asset=asset,
                fiat=fiat,
                percentage=score,
            )

            db.add(alert)
            saved += 1

        db.commit()
        logger.info("Arbitrage analysis completed", opportunities=saved)
        return {"status": "success", "opportunities": saved}

    except Exception as e:
        logger.error("Error analyzing arbitrage", error=str(e))
        db.rollback()
        return {"status": "error", "error": str(e)}
    finally:
        db.close()
