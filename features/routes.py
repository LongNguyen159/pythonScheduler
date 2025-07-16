from fastapi import FastAPI, HTTPException
from features.scheduler import scheduler, run_scheduler
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
def cancel_job(job_id: str):
    try:
        job = scheduler.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        scheduler.remove_job(job_id)
        return {"message": f"Job {job_id} canceled successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/jobs")
def list_jobs():
    try:
        jobs: List[Job] = scheduler.get_jobs()
        jobs_list = [
            {
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
            for job in jobs
        ]
        return jobs_list
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
@app.delete("/remove-all-jobs")
def remove_all_jobs():
    try:
        scheduler.remove_all_jobs()
        return {"message": "All jobs removed successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))