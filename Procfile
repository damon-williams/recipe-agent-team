web: gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 4 --worker-class gthread --timeout 120 --keep-alive 5 --preload web_app:app

# Key changes:
# --worker-class gthread  ← CRITICAL: Enables threading support
# --threads 4            ← Allows 4 concurrent threads per worker  
# --workers 1            ← Single worker to avoid queue conflicts
# --preload              ← Loads app before forking (preserves threads)
# --keep-alive 5         ← Keeps connections alive
# --timeout 120          ← Longer timeout for recipe generation