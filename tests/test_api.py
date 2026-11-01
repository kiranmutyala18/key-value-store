from api import Metrics


def test_metrics_expose_request_counter() -> None:
    metrics = Metrics()
    metrics.record("set")

    assert 'kv_requests_total{operation="set"} 1' in metrics.prometheus()
