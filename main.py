from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError

from database import create_db_and_tables, get_session
from models import User, Question, Answer
from datetime import datetime, timezone
from sqlalchemy import Column, JSON, Text


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(
    title="PeerBoard",
    description="Academic Questions and Answers Platform",
    lifespan=lifespan,
)


class UserCreate(BaseModel):
    name: str
    email: str


class QuestionCreate(BaseModel):
    title: str
    body: str
    course_code: str
    tags: list[str] = Field(default_factory=list)
    author_id: int


class AnswerCreate(BaseModel):
    body: str
    author_id: int


@app.post("/users", response_model=User, status_code=201)
def create_user(data: UserCreate, session: Session = Depends(get_session)):
    user = User(name=data.name, email=data.email)

    session.add(user)

    try:
        session.commit()
        session.refresh(user)
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=409, detail="Email already exists")

    return user


@app.post("/questions", response_model=Question, status_code=201)
def create_question(data: QuestionCreate, session: Session = Depends(get_session)):

    author = session.get(User, data.author_id)

    if not author:
        raise HTTPException(status_code=404, detail="Author not found")

    if not data.title.strip() or not data.body.strip():
        raise HTTPException(status_code=400, detail="Title and body cannot be empty")

    question = Question(**data.model_dump(), accepted_answer_id=None)

    session.add(question)
    session.commit()
    session.refresh(question)

    return question


@app.get("/questions", response_model=list[Question])
def list_questions(session: Session = Depends(get_session)):
    statement = select(Question)

    questions = session.exec(statement).all()

    return questions


@app.get("/questions/{question_id}", response_model=Question)
def get_question(question_id: int, session: Session = Depends(get_session)):

    question = session.get(Question, question_id)

    if not question:
        raise HTTPException(status_code=404, detail="Question not found!")

    return question


@app.delete("/questions/{question_id}")
def delete_question(question_id: int, session: Session = Depends(get_session)):
    question = session.get(Question, question_id)

    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    statement = select(Answer).where(Answer.question_id == question_id)

    answers = session.exec(statement).first()
    print(answers)

    if answers:
        raise HTTPException(
            status_code=400, detail="Cannot delete a question that has answers"
        )

    session.delete(question)
    session.commit()

    return {"message": "Question deleted"}


@app.put("/questions/{question_id}", response_model=Question)
def update_question(
    question_id: int, data: QuestionCreate, session: Session = Depends(get_session)
):
    question = session.get(Question, question_id)

    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    author = session.get(User, data.author_id)

    if not author:
        raise HTTPException(status_code=404, detail="Author not found")

    question.title = data.title
    question.body = data.body
    question.course_code = data.course_code
    question.tags = data.tags
    question.author_id = data.author_id

    question.updated_at = datetime.now(timezone.utc)

    session.add(question)
    session.commit()
    session.refresh(question)

    return question


@app.post("/questions/{question_id}/answers", response_model=Answer, status_code=201)
def create_answer(
    question_id: int, data: AnswerCreate, session: Session = Depends(get_session)
):

    author = session.get(User, data.author_id)

    if not author:
        raise HTTPException(status_code=404, detail="Author not found")

    question = session.get(Question, question_id)

    if not author:
        raise HTTPException(status_code=404, detail="Question not found")

    answer = Answer(author_id=author.id, body=data.body, question_id=question_id)

    session.add(answer)
    session.commit()
    session.refresh(answer)
    return answer


@app.get("/questions/{question_id}/answers" , response_model=list[Answer] )
def get_answers(question_id : int , session : Session = Depends(get_session)):

    answers = session.exec(select(Answer).where(Answer.question_id==question_id)).all()


    if not answers:
        raise HTTPException(
            status_code=404,
            detail="No answers found for this question."
        )
    
    return answers
