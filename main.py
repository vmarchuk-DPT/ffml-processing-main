from fastapi import BackgroundTasks, FastAPI
from process import process
from mangum import Mangum

app = FastAPI()


#@app.get("/")
#async def start_processing(survey_version: int, background_tasks: BackgroundTasks):
#    background_tasks.add_task(process, survey_version)
#   return {"message": "Welcome to FFML"}


@app.get("/{survey_version}")
async def start_processing(survey_version: int, background_tasks: BackgroundTasks):
    background_tasks.add_task(process, survey_version)
    return {"message": "Processing started in background"}

# Add Mangum adapter to make FastAPI compatible with AWS Lambda
handler = Mangum(app)
