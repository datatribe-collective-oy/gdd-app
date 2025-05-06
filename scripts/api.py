from fastapi import FastAPI, Response
from scripts.http_matrix import router as http_matrix_router
import uvicorn

app = FastAPI()


@app.get("/api/")
def read_root(response: Response):
    response.status_code
    return {"message": "API Root OK."}


@app.get("/api/gdd/")
def get_gdd(response: Response):
    response.status_code
    return {"message": "Get GDD."}


@app.get("/api/weather/")
def get_weather(response: Response):
    response.status_code
    return {"message": "Estimate Weather."}


# Include status test routes
app.include_router(http_matrix_router)

# Run API by uvicorn, local development.
if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)
