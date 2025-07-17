from fastapi import FastAPI, HTTPException
from features.scheduler import SchedulerService
from features.schema import TaskExecutionSettings
from typing import List
from apscheduler.job import Job
# Initialize FastAPI app
app = FastAPI()
scheduler_service = SchedulerService()

'''
    TODO: Optional 'expert mode': Accept in a CRON string to schedule jobs.
'''

def test():
    print("Test job executed successfully!")
    return "Test successful!"

@app.post("/schedule")
def schedule_job(request: TaskExecutionSettings):
    try:
        job = scheduler_service.schedule_job(request, callback=test)
        return job
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/cancel/{job_id}")
def cancel_job(job_id: str):
    try:
        return scheduler_service.cancel_job(job_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/jobs")
def list_jobs():
    try:
        return scheduler_service.get_all_jobs()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    

@app.get("/job/{job_id}")
def get_job(job_id: str):
    try:
       job = scheduler_service.get_job_by_id(job_id)
       return job
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.delete("/remove-all-jobs")
def remove_all_jobs():
    try:
        return scheduler_service.remove_all_jobs()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))