"""
app.py -- Dịch vụ mô hình FastAPI (nội dung 10; hợp đồng docs/api_contract.md). Viết 21/10/2026.
Chỉ là lớp HTTP mỏng quanh core.RecommenderCore: kiểm tham số, đổi lỗi sang định dạng chung, đo thời gian xử lý.

Thư mục embedding đọc từ biến môi trường CAMERA_EMB_DIR (run_service.py đặt), thiết bị từ CAMERA_DEVICE (mặc định cpu).
"""

import logging
import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from core import ApiError, RecommenderCore

CONTRACT_VERSION = "1.0"
STATE = {}


@asynccontextmanager
async def lifespan(app):
    log = logging.getLogger("uvicorn.error").info           # ra màn hình và log của run_service.py
    STATE["core"] = RecommenderCore(os.environ["CAMERA_EMB_DIR"], device=os.environ.get("CAMERA_DEVICE", "cpu"),
                                    log=log)
    yield
    STATE.clear()


app = FastAPI(title="camera-store model service", version=CONTRACT_VERSION, lifespan=lifespan)


def _err(status, code, message, details=None):
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message,
                                                               "details": details or {}}})


@app.exception_handler(ApiError)
async def api_error(_, e: ApiError):
    return _err(e.status, e.code, e.message, e.details)


@app.exception_handler(RequestValidationError)
async def validation_error(_, e: RequestValidationError):
    return _err(422, "INVALID_PARAM", "Tham số không hợp lệ.",
                {"errors": [{"loc": list(x["loc"]), "msg": x["msg"]} for x in e.errors()]})


@app.exception_handler(StarletteHTTPException)
async def http_error(_, e: StarletteHTTPException):
    return _err(e.status_code, "NOT_FOUND" if e.status_code == 404 else "HTTP_ERROR", str(e.detail))


@app.exception_handler(Exception)
async def internal_error(_, e: Exception):
    return _err(500, "INTERNAL_ERROR", f"{type(e).__name__}: {e}")


@app.middleware("http")
async def timing(request: Request, call_next):
    t = time.perf_counter()
    resp = await call_next(request)
    resp.headers["X-Process-Time-Ms"] = f"{(time.perf_counter() - t) * 1000:.3f}"
    return resp


@app.get("/health")
def health():
    return {**STATE["core"].health(), "contract_version": CONTRACT_VERSION}


@app.get("/recommend")
def recommend(user_id: int = Query(...), k: int = Query(10, ge=1, le=50),
              exclude: str = Query("train", pattern="^(train|train_val)$")):
    return STATE["core"].recommend(user_id, k, exclude)


@app.get("/items/{item_id}")
def item(item_id: int):
    return STATE["core"].item_info(item_id)


@app.get("/users/{user_id}/bodies")
def user_bodies(user_id: int):
    return STATE["core"].user_bodies(user_id)


@app.get("/compat")
def compat(body_id: int = Query(...), lens_id: int = Query(...)):
    return STATE["core"].compat(body_id, lens_id)
