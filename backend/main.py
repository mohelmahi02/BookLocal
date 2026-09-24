from fastapi import FastAPI

app = FastAPI(title="BookLocal API")

@app.get("/")
def root():
    return {"status": "BookLocal API is running"}

@app.get("/health")
def health():
    return {"status": "ok"}
