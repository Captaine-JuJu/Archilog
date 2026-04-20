from sqlalchemy import create_engine, MetaData, Column, Table, String, Double, Integer

from archilog.config import config

engine = create_engine(config.DATABASE_URL, echo=config.DEBUG)
metadata = MetaData()

cagnotte_table = Table(
    "participant",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("login", String, nullable=False),
    Column("montant", Double, nullable=False),
    Column("nomCagnotte", String, nullable=False),
)

utilisateur_table = Table(
    "utilisateur",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("login", String, nullable=False, unique=True),
    Column("password", String, nullable=False),
)
