from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Server running"}

def main():
    import uvicorn
    uvicorn.run("server.app:app", host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()
