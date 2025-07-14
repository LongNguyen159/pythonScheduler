from pydantic import BaseModel, Field, model_validator
from typing import List, Optional, Union, Dict, Any
from datetime import datetime
from enum import Enum

# ========== Enums ==========
class EndRepeatMode(str, Enum):
    NEVER = "never"
    ON_DATE = "on_date"
    AFTER_OCCURRENCES = "after_occurrences"

class Frequency(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"

class Weekday(str, Enum):
    MON = "mon"
    TUE = "tue"
    WED = "wed"
    THU = "thu"
    FRI = "fri"
    SAT = "sat"
    SUN = "sun"

class RepeatType(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    CUSTOM = "custom"

# ========== End Repeat ==========
class EndRepeatNever(BaseModel):
    mode: EndRepeatMode = EndRepeatMode.NEVER

class EndRepeatOnDate(BaseModel):
    mode: EndRepeatMode = EndRepeatMode.ON_DATE
    until: datetime

class EndRepeatAfterOccurrences(BaseModel):
    mode: EndRepeatMode = EndRepeatMode.AFTER_OCCURRENCES
    occurrences: int

EndRepeat = Union[EndRepeatNever, EndRepeatOnDate, EndRepeatAfterOccurrences]

# ========== Custom Repeats ==========
class CustomDaily(BaseModel):
    frequency: Frequency = Frequency.DAILY
    interval: int = Field(..., gt=0, description="Every X days")

class CustomWeekly(BaseModel):
    frequency: Frequency = Frequency.WEEKLY
    interval: int = Field(..., gt=0, description="Every X weeks")
    weekdays: List[Weekday]

class CustomMonthly(BaseModel):
    frequency: Frequency = Frequency.MONTHLY
    interval: int = Field(..., gt=0, description="Every X months")

CustomRepeat = Union[CustomDaily, CustomWeekly, CustomMonthly]

# ========== Repeat ==========
class RepeatSimple(BaseModel):
    type: RepeatType = RepeatType.DAILY

class RepeatCustom(BaseModel):
    type: RepeatType = RepeatType.CUSTOM
    custom: CustomRepeat

Repeat = Union[RepeatSimple, RepeatCustom]

# ========== Main Scheduler Payload ==========
class TaskSchedulePayload(BaseModel):
    task_id: str
    start_time: datetime
    is_repeat: bool = False
    repeat: Optional[Repeat] = None
    end_repeat: Optional[EndRepeat] = None
    args: Optional[List[Any]] = []
    kwargs: Optional[Dict[str, Any]] = {}

    @model_validator(mode="after")
    def validate_repeat_logic(self):
        is_repeat = self.is_repeat
        repeat = self.repeat
        end_repeat = self.end_repeat

        if is_repeat and not repeat:
            raise ValueError("`repeat` must be provided if `is_repeat` is True.")
        
        # if not is_repeat and repeat:
        #     raise ValueError("`repeat` must be omitted if `is_repeat` is False.")
        # if not is_repeat and end_repeat:
        #     raise ValueError("`end_repeat` must be omitted if `is_repeat` is False.")
        return self
