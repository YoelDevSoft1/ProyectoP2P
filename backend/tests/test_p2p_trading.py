import pytest

from app.services.p2p_trading_service import P2PTradingService


class DummySession:
    def __init__(self):
        self.trades = []
        self.closed = False

    def add(self, trade):
        trade.id = len(self.trades) + 1
        self.trades.append(trade)

    def commit(self):
        return True

    def refresh(self, trade):
        return trade

    def rollback(self):
        return True

    def close(self):
        self.closed = True


@pytest.fixture(autouse=True)
def stub_browser(monkeypatch):
    class FakeBrowserAutomationService:
        def __init__(self):
            self.create_response = {"success": True, "order_id": "order-1"}
            self.orders = [{"order_id": "order-1"}]

        async def initialize(self):
            return True

        async def login(self, *args, **kwargs):
            return True

        async def create_p2p_order(self, **kwargs):
            return dict(self.create_response)

        async def cancel_p2p_order(self, order_id):
            return {"success": True, "order_id": order_id}

        async def get_p2p_orders(self):
            return list(self.orders)

        async def close(self):
            return True

    stub = FakeBrowserAutomationService()
    monkeypatch.setattr(
        "app.services.p2p_trading_service.BrowserAutomationService",
        lambda: stub,
    )
    return stub


@pytest.mark.asyncio
async def test_execute_trade_success(stub_browser):
    session = DummySession()
    service = P2PTradingService(db_session=session)

    result = await service.execute_trade(
        asset="USDT",
        fiat="COP",
        trade_type="BUY",
        amount=100,
        price=4000,
        payment_methods=["Nequi"],
    )

    assert result["success"] is True
    assert result["order_id"] == "order-1"
    await service.close()


@pytest.mark.asyncio
async def test_execute_trade_failure(stub_browser):
    stub_browser.create_response = {"success": False, "error": "failure"}
    session = DummySession()
    service = P2PTradingService(db_session=session)

    result = await service.execute_trade(
        asset="USDT",
        fiat="COP",
        trade_type="SELL",
        amount=50,
        price=4100,
        payment_methods=["Nequi"],
    )

    assert result["success"] is False
    assert "failure" in result["error"]
    await service.close()


@pytest.mark.asyncio
async def test_get_orders(stub_browser):
    session = DummySession()
    service = P2PTradingService(db_session=session)

    orders = await service.get_active_orders()
    assert orders == [{"order_id": "order-1"}]
    await service.close()
