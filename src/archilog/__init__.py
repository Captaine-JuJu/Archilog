import click

from archilog.creation_table import metadata, engine


@click.command()
def init_database():
    metadata.create_all(engine)
