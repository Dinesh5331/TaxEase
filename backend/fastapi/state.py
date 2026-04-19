# Global application state — populated during FastAPI lifespan startup
# Stored here to avoid circular imports between app.py and routers
app_state: dict = {}
