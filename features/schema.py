from pydantic import BaseModel, Field, model_validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

#region Enums
# ========== Enums ==========
class RepeatType(str, Enum):
    MINUTELY = "minutely"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"

class EndRepeatMode(str, Enum):
    NEVER = "never"
    ON_DATE = "on_date"

class Weekday(str, Enum):
    MON = "mon"
    TUE = "tue"
    WED = "wed"
    THU = "thu"
    FRI = "fri"
    SAT = "sat"
    SUN = "sun"

#endregion

#region Repeat
# ========== End Repeat ==========
class EndRepeat(BaseModel):
    mode: EndRepeatMode
    until: Optional[datetime] = None  # Only required if mode is ON_DATE

# ========== Repeat ==========
class Repeat(BaseModel):
    type: RepeatType
    frequency: Optional[int] = Field(None, gt=0, description="Every X units (optional, defaults to 1)")
    on_weekdays: Optional[List[Weekday]] = None  # For weekly repeats
    on_days: Optional[List[int]] = None  # For monthly repeats

#endregion


#region Payload
# ========== Main Scheduler Payload ==========
class TaskSchedulePayload(BaseModel):
    task_id: str
    start_time: datetime
    repeat: Optional[Repeat] = None  # Optional for one-time jobs
    end_repeat: Optional[EndRepeat] = None  # Optional for one-time jobs
    args: Optional[List[Any]] = []
    kwargs: Optional[Dict[str, Any]] = {}

    @model_validator(mode="after")
    def validate_repeat_logic(self):
        if self.repeat:
            if self.repeat.type == RepeatType.WEEKLY and self.repeat.on_weekdays is not None and not self.repeat.on_weekdays:
                raise ValueError("`on_weekdays` must not be empty if provided for `repeat.type` WEEKLY.")
            if self.repeat.type == RepeatType.MONTHLY and self.repeat.on_days is not None and not self.repeat.on_days:
                raise ValueError("`on_days` must not be empty if provided for `repeat.type` MONTHLY.")
        if self.end_repeat and self.end_repeat.mode == EndRepeatMode.ON_DATE and not self.end_repeat.until:
            raise ValueError("`until` must be provided if `end_repeat.mode` is ON_DATE.")
        return self
    


class JobResponse(BaseModel):
    id: str
    name: str
    func: str
    args: List[Any]
    kwargs: Dict[str, Any]
    coalesce: bool
    trigger: str
    executor: str
    misfire_grace_time: Optional[int] = None
    max_instances: int
    next_run_time: Optional[str] = None  # ISO format string or None
#endregion