from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from routers import news
from routers import users
from routers import favorite
from routers import history
from utils.exception_handlers import register_exception_handlers

app=FastAPI()

register_exception_handlers(app)

origins=[
    "http://localhost",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # 允许的源
    allow_credentials=True, # 允许携带cookie
    allow_methods=["*"],    # 允许的请求方法
    allow_headers=["*"],    # 允许的请求头
)

@app.get('/')
async def root():
    return {"message":"Hello World"}

app.include_router(news.router)
app.include_router(users.router)
app.include_router(favorite.router)
app.include_router(history.router)
