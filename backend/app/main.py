from fastapi import FastAPI


app = FastAPI(
    title="社保表格聚合工具",
    version="0.1.0",
    summary="基础项目骨架",
)


@app.get("/health", tags=["system"])
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}

