from fastapi import FastAPI

app = FastAPI(
    title="Double-Entry Financial Ledger API",
    description="Atomic, immutable financial ledger service.",
    version="0.1.0",
)


@app.get("/")
def health_check():
    return "Hello WOrld!"
    return {"status": "active", "system": "double-entry-ledger"}
