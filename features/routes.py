from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from features.scheduler import schedule_from_payload, scheduler
from features.schema import TaskSchedulePayload

# Initialize FastAPI app
app = FastAPI()

# Define Pydantic model for request payload
class ScheduleRequest(BaseModel):
    payload: TaskSchedulePayload

@app.post("/schedule")
def schedule_job(request: ScheduleRequest):
    try:
        job = schedule_from_payload(request.payload)
        return {"job_id": job.id, "name": job.name, "next_run_time": job.next_run_time}
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
        jobs = scheduler.get_jobs()
        return [{"job_id": job.id, "name": job.name, "next_run_time": job.next_run_time} for job in jobs]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
