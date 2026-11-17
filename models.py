from datetime import datetime, timezone
from sqlalchemy import Column, JSON, Text
from sqlmodel import SQLModel, Field


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    email: str = Field(index=True, unique=True)
    role: str = "student"


class Question(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str
    body: str = Field(sa_column=Column(Text))
    course_code: str
    tags: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    author_id: int = Field(foreign_key="user.id")

    accepted_answer_id: int | None = Field(default=None, foreign_key="answer.id")

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Answer(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    question_id: int = Field(foreign_key="question.id")
    author_id: int = Field(foreign_key="user.id")

    body: str = Field(sa_column=Column(Text))

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
