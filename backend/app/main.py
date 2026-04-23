# from typing import AsyncGenerator

from fastapi import Depends, FastAPI
from sqlalchemy.ext.asyncio import AsyncSession
from strawberry.fastapi import GraphQLRouter

from app.db import get_db
from app.graphql.schema import schema

async def get_context(db: AsyncSession = Depends(get_db)):
    return {"db": db}

app = FastAPI(title="MTG App API")

graphql_app = GraphQLRouter(schema, context_getter=get_context)

app.include_router(graphql_app, prefix="/graphql")

@app.get("/health")
def health():
    return {"status": "ok"}