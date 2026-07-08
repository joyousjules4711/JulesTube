from fastapi import FastAPI

app = FastAPI(
    title="JulesTube",
    description="Your couch. Your music. Your rules.",
    version="Prelude"
)


@app.get("/")
def home():
    return {
        "app": "JulesTube",
        "version": "Prelude",
        "message": "Welcome, Jules! Raphael: prepare for music!🎵"
    }