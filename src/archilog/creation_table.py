from sqlalchemy import create_engine, MetaData, Column, Uuid, Table, String, Double, Integer

engine = create_engine("sqlite:///database.db", echo=True)
metadata = MetaData()
users_table = Table(
    "participant",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("login", String, nullable=False),
    Column("montant", Double, nullable=False),
    Column("nomCagnotte", String, nullable=False),
)

metadata.create_all(engine)
