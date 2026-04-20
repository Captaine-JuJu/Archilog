import click

from archilog.data import enregistrerParticipation, totalCagnotte, supprimerParticipation
from archilog.domain import validerCreationCagnotte, validerAjoutParticipation, CagnotteError
from archilog.database import cagnotte_table, engine, metadata


@click.group()
def cli():
    pass


@cli.command()
def init_database():
    """Crée toutes les tables en base de données."""
    metadata.create_all(engine)
    click.echo("Base de données initialisée.")


@cli.command()
@click.option("--nom-participant", prompt="Nom du participant ")
@click.option("--nom-cagnotte", prompt="Nom de la cagnotte ")
@click.option("--montant", prompt="Montant ")
def creationCagnotteCli(nom_participant, nom_cagnotte, montant):
    """Crée une nouvelle cagnotte."""
    verif = cagnotte_table.select().where(cagnotte_table.c.nomCagnotte == nom_cagnotte)
    with engine.connect() as conn:
        cagnotteExistante = conn.execute(verif).one_or_none() is not None

    try:
        validerCreationCagnotte(nom_cagnotte, montant, cagnotteExistante)
    except CagnotteError as e:
        click.echo(f"Erreur : {e}")
        return

    stmt = cagnotte_table.insert().values(login=nom_participant, montant=montant, nomCagnotte=nom_cagnotte)
    with engine.begin() as conn:
        conn.execute(stmt)
    click.echo("Ajout réussi")


@cli.command()
@click.option("--nom-cagnotte", prompt="Nom de la cagnotte ")
def voirCagnotteCli(nom_cagnotte):
    """Affiche les participants d'une cagnotte."""
    exist = cagnotte_table.select().where(cagnotte_table.c.nomCagnotte == nom_cagnotte)
    with engine.connect() as conn:
        existant = conn.execute(exist).all()
    if not existant:
        click.echo("La cagnotte n'existe pas")
    else:
        click.echo(f"La cagnotte {nom_cagnotte} contient les transactions suivantes :")
        for i in existant:
            click.echo(f"{i.login} : {i.montant}")


@cli.command()
@click.option("--nom-participant", prompt="Nom du participant ")
@click.option("--nom-cagnotte", prompt="Nom de la cagnotte ")
@click.option("--nouveau-montant", prompt="Montant ")
def ajoutParticipationCli(nom_participant, nom_cagnotte, nouveau_montant):
    """Ajoute une participation à une cagnotte existante."""
    exist = cagnotte_table.select().where(cagnotte_table.c.nomCagnotte == nom_cagnotte)
    with engine.connect() as conn:
        existant = conn.execute(exist).all()
    if not existant:
        click.echo("La cagnotte n'existe pas")
        return

    try:
        validerAjoutParticipation(nouveau_montant)
    except CagnotteError as e:
        click.echo(f"Erreur : {e}")
        return

    enregistrerParticipation(nom_participant, nouveau_montant, nom_cagnotte)
    click.echo("Participation ajoutée")


@cli.command()
@click.option("--nom-participant", prompt="Nom du participant ")
@click.option("--nom-cagnotte", prompt="Nom de la cagnotte ")
def supprimerParticipationCli(nom_participant, nom_cagnotte):
    """Supprime la participation d'un utilisateur dans une cagnotte."""
    exist = cagnotte_table.select().where(
        cagnotte_table.c.nomCagnotte == nom_cagnotte,
        cagnotte_table.c.login == nom_participant
    )
    with engine.connect() as conn:
        existant = conn.execute(exist).all()
    if not existant:
        click.echo("Ce login n'existe pas dans la cagnotte, ou bien la cagnotte n'existe pas")
        return

    supprimerParticipation(nom_participant, nom_cagnotte)
    click.echo(f"La participation de {nom_participant} à la cagnotte {nom_cagnotte} a bien été supprimée")

    if totalCagnotte(nom_cagnotte) == 0:
        supp = cagnotte_table.delete().where(cagnotte_table.c.nomCagnotte == nom_cagnotte)
        with engine.connect() as conn:
            conn.execute(supp)
            conn.commit()
        click.echo("La cagnotte a été supprimée")