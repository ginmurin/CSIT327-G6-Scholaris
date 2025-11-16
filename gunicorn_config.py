# Gunicorn configuration file
import multiprocessing

# Worker timeout - increased to allow for AI API calls
timeout = 120  # 2 minutes (default is 30 seconds)

# Number of worker processes
workers = multiprocessing.cpu_count() * 2 + 1

# Worker class
worker_class = 'sync'

# Maximum requests a worker will process before restarting
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'

# Keep-alive connections
keepalive = 5
