from fastapi import FastAPI
from app.database import Base, engine
from app.routes import payments
from fastapi.middleware.cors import CORSMiddleware

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(payments.router, tags=['Payments'], prefix="/api/payments")


@app.get("/api/healthchecker")
def root():
    return {"message": "Welcome to FastAPI with MongoDB Payments"}
