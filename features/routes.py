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
        job = scheduler_service.schedule_job(request, task_to_execute_callback=test)
        if not job:
            raise HTTPException(status_code=400, detail="Failed to schedule job.")
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
        job: Job | None = scheduler_service.scheduler.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found.")
        
        return {
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.delete("/remove-all-jobs")
def remove_all_jobs():
    try:
        return scheduler_service.remove_all_jobs()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))