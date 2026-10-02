from prometheus_client import Counter, Gauge, Histogram

http_requests_total = Counter(
    'http_requests_total',
    'Общее количество HTTP-запросов',
    ['method', 'endpoint', 'status'],
)
http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'Время обработки запросов',
    ['method', 'endpoint'],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)

events_provider_requests_total = Counter(
    'events_provider_requests_total',
    'Количество запросов к Events Provider',
    ['endpoint', 'status'],
)
events_provider_request_duration_seconds = Histogram(
    'events_provider_request_duration_seconds',
    'Время ответа Events Provider',
    ['endpoint'],
)

tickets_created_total = Gauge(
    'tickets_created_total', 'Общее количество созданных билетов в БД'
)
tickets_cancelled_total = Gauge(
    'tickets_cancelled_total', 'Общее количество отменённых билетов в БД'
)
events_total = Gauge('events_total', 'Текущее количество событий в базе')

cache_hits_total = Counter('cache_hits_total', 'Попадания в кэш (seats)')
cache_misses_total = Counter('cache_misses_total', 'Промахи кэша (seats)')
