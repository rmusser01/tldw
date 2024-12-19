from fastapi import FastAPI

app = FastAPI(title="TLDW API", version="1.0.0")

@app.get("/")
async def root():
    return {"message": "Welcome to the tldw API"}
