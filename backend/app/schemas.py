from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


# --- Task ---
class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    due_at: Optional[datetime] = None
    status: str = "pending"
    priority: str = "medium"


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_at: Optional[datetime] = None
    status: Optional[str] = None
    priority: Optional[str] = None


class TaskOut(TaskBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Calendar ---
class EventBase(BaseModel):
    title: str
    description: Optional[str] = None
    start_at: datetime
    end_at: Optional[datetime] = None
    all_day: bool = False


class EventCreate(EventBase):
    pass


class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    all_day: Optional[bool] = None


class EventOut(EventBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Note ---
class NoteBase(BaseModel):
    title: str
    body: str = ""
    tags: str = ""


class NoteCreate(NoteBase):
    pass


class NoteUpdate(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    tags: Optional[str] = None


class NoteOut(NoteBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Finance ---
class TransactionBase(BaseModel):
    amount: float
    currency: str = "CNY"
    category: str = "其他"
    note: Optional[str] = None
    occurred_at: datetime


class TransactionCreate(TransactionBase):
    pass


class TransactionUpdate(BaseModel):
    amount: Optional[float] = None
    currency: Optional[str] = None
    category: Optional[str] = None
    note: Optional[str] = None
    occurred_at: Optional[datetime] = None


class TransactionOut(TransactionBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Habit ---
class HabitBase(BaseModel):
    name: str
    description: Optional[str] = None
    frequency: str = "daily"


class HabitCreate(HabitBase):
    pass


class HabitUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    frequency: Optional[str] = None


class HabitOut(HabitBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class HabitLogCreate(BaseModel):
    logged_date: date = Field(default_factory=date.today)
    completed: bool = True


class HabitLogOut(BaseModel):
    id: int
    habit_id: int
    logged_date: date
    completed: bool

    model_config = {"from_attributes": True}


# --- Chat ---
class ChatRequest(BaseModel):
    message: str
    provider: Optional[str] = None
    model: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    provider: str
    model: str
    error: Optional[str] = None
