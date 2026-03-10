from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers.fluids import router as fluids_router

from backend.routers.flow_orifice import router as flow_orifice_router
from backend.routers.straight_through import router as straight_through_router

app = FastAPI(title="ccp-backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(fluids_router)
app.include_router(flow_orifice_router)
app.include_router(straight_through_router)


@app.get("/")
def root():
    return {"status": "ok"}
