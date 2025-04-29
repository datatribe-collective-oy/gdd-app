from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/")
def read_root():
    return ("Hello World")

# Run API by uvicorn, local development. 
if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)