from fastapi import FastAPI, HTTPException
from features.scheduler import run_scheduler, cancel_job, get_all_jobs, remove_all_jobs
from features.schema import TaskSchedulePayload
from typing import List
from apscheduler.job import Job
# Initialize FastAPI app
app = FastAPI()

# Define Pydantic model for request payload

@app.post("/schedule")
def schedule_job(request: TaskSchedulePayload):
    try:
        job = run_scheduler(request)
        job_details = {
            "id": job.id,
            "name": job.name,
            "func": str(job.func),
            "args": job.args,
            "kwargs": job.kwargs,
            "coalesce": job.coalesce,
            "trigger": str(job.trigger),
            "executor": job.executor,
            "misfire_grace_time": job.misfire_grace_time,
            "max_instances": job.max_instances,
            "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None
        }
        return job_details
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/cancel/{job_id}")
def cancel_job_api(job_id: str):
    try:
        return cancel_job(job_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/jobs")
def list_jobs():
    try:
        return get_all_jobs()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    

@app.delete("/remove-all-jobs")
def remove_all_jobs_api():
    try:
        return remove_all_jobs()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))