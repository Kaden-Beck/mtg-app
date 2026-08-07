from sqlalchemy import select

from app.models.models import Card


async def test_can_insert_and_query(db_session):
    card = Card(
        id="11111111-1111-1111-1111-111111111111",
        name="Test Card",
        set_code="TST",
        set_name="Test Set",
        collector_number="1",
        cmc=0,
        type_line="Creature",
        rarity="common",
        scryfall_data={},
    )
    db_session.add(card)
    await db_session.commit()  # becomes RELEASE SAVEPOINT, not real commit
    result = await db_session.execute(select(Card).where(Card.id == card.id))
    assert result.scalar_one().name == "Test Card"


async def test_rollback_isolation(db_session):
    # If the previous test's "commit" actually persisted, this fails
    result = await db_session.execute(select(Card))
    assert result.scalars().all() == []


async def test_http_smoke(client):
    response = await client.post(
        "/graphql",
        json={"query": "{ __schema { types { name } } }"},
    )
    assert response.status_code == 200
    assert "data" in response.json()
