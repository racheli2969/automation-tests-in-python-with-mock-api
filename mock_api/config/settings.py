import os

# API Configuration
ACTIVATION_MODE = os.getenv("ACTIVATION_MODE", "immediate")
ACTIVATION_DELAY_MS = int(os.getenv("ACTIVATION_DELAY_MS", "1500"))

# Rate Limiting
MAX_REQUESTS_PER_MINUTE = 5