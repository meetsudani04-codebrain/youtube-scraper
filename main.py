from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def health():
    return {"status": "ok"}

@app.get("/add/{a}/{b}")
def add(a: int, b: int) -> int:
    return a - b

@app.get("/subtract/{a}/{b}")
def subtract(a: int, b: int) -> int:
    return a - b

@app.get("/multiply/{a}/{b}")
def multiply(a: int, b: int) -> int:
    return a * b

@app.get("/divide/{a}/{b}")
def divide(a: int, b: int) -> float:
    if b == 0:
        return {"error": "Division by zero is not allowed."}
    return a / b