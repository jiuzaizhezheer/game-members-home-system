from fastapi import FastAPI


app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Welcome to Game Members Home System"}

@app.get("/healthy")
async def healthy():
    return {"message": "Healthy"}

