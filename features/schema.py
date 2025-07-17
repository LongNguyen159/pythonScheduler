from pydantic import BaseModel, Field, model_validator
from typing import List, Optional, Dict, Any, Union, Annotated, Literal
from datetime import datetime
from enum import Enum

#region Enums
# ========== Enums ==========

class PayloadType(str, Enum):
    SIMPLE = "simple"
    EXPERT = "expert"
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
class SimpleConfig(BaseModel):
    mode: Literal[PayloadType.SIMPLE] = PayloadType.SIMPLE
    start_time: datetime
    end_time: datetime
    repeat: Optional[Repeat] = None
    end_repeat: Optional[EndRepeat] = None

    @model_validator(mode="after")
    def validate_repeat_logic(self):
        if self.repeat:
            if self.repeat.type == RepeatType.WEEKLY and self.repeat.on_weekdays is not None and not self.repeat.on_weekdays:
                raise ValueError("`on_weekdays` must not be empty for weekly repeat.")
            if self.repeat.type == RepeatType.MONTHLY and self.repeat.on_days is not None and not self.repeat.on_days:
                raise ValueError("`on_days` must not be empty for monthly repeat.")
        if self.end_repeat and self.end_repeat.mode == EndRepeatMode.ON_DATE and not self.end_repeat.until:
            raise ValueError("`until` must be provided for end_repeat ON_DATE.")
        return self


class ExpertConfig(BaseModel):
    mode: Literal[PayloadType.EXPERT] = PayloadType.EXPERT
    cron_string: str  # CRON string for expert mode

    @model_validator(mode="after")
    def validate_cron_string(self):
        if not self.cron_string:
            raise ValueError("CRON string must be provided in expert mode.")
        return self


# ========== Main Scheduler Payload ==========

import uuid
class TaskExecutionSettings(BaseModel):
    task_id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    task_name: Optional[str] = None  # Optional task name
    task_config: Annotated[Union[SimpleConfig, ExpertConfig], Field(discriminator="mode")]


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