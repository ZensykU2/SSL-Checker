from fastapi import FastAPI
from app.core.init_app import init_app
from app.startup.lifespan import lifespan

app = FastAPI(lifespan=lifespan)

init_app(app)
