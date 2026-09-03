from datetime import datetime, timedelta
from app.services.sla_service import sla_service

def test_sla_deadline_calculation():
    d_crit = sla_service.calculate_deadline("Critical")
    d_med = sla_service.calculate_deadline("Medium")
    assert d_crit < d_med

    past = datetime.utcnow() - timedelta(hours=1)
    future = datetime.utcnow() + timedelta(hours=1)
    assert sla_service.is_breached(past) is True
    assert sla_service.is_breached(future) is False
