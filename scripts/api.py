from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/")
def read_root():
    return ("Hello World")

@app.get("/api/gdd/")
def get_gdd():
    return {"message": "Get GDD"}

@app.get("/api/weather/")
def get_weather():
    return {"message": "Estimate Weather"}

# Run API by uvicorn, local development. 
if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)