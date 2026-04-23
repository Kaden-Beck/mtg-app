import strawberry
from strawberry.fastapi import GraphQLRouter
from app.graphql.resolvers.cards import CardsQuery
from app.graphql.resolvers.collection import CollectionQuery, CollectionMutation
from app.graphql.resolvers.converter import ConverterMutation
from app.graphql.resolvers.decks import DecksQuery, DecksMutation
from app.graphql.resolvers.prices import PricesQuery


@strawberry.type
class Query(CardsQuery, CollectionQuery, DecksQuery, PricesQuery):
    @strawberry.field
    def ping(self) -> str:
        return "pong"


@strawberry.type
class Mutation(CollectionMutation, ConverterMutation, DecksMutation):
    @strawberry.field
    def ping(self) -> str:
        return "pong"


schema = strawberry.Schema(query=Query, mutation=Mutation)
