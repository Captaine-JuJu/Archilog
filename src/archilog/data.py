from sqlalchemy import func, update, and_

from src.archilog.creation_table import  engine, users_table

def enregistrerParticipation(nom, montantAjoute, nomCagnotte):
    """
    ajoute à la base de donnée une nouvelle dépense lié à la cagnotte mise en paramètre
    :param nom:
    :param montant_ajoute:
    :param nomCagnotte:
    """
    verifMontant = users_table.select().where(
        and_(users_table.c.login == nom, users_table.c.nomCagnotte == nomCagnotte)
    )

    with engine.connect() as conn:
        resultat = conn.execute(verifMontant).fetchone()

        if resultat:
            nouveauMontant = float(resultat.montant) + float(montantAjoute)
            stmt = update(users_table).where(
                and_(users_table.c.login == nom, users_table.c.nomCagnotte == nomCagnotte)
            ).values(montant=nouveauMontant)
        else:
            stmt = users_table.insert().values(
                login=nom, montant=montantAjoute, nomCagnotte=nomCagnotte
            )

        conn.execute(stmt)
        conn.commit()

def totalCagnotte(nomCagnotte):
    """
    recupère le nom d'une cagnotte et fait la somme de tous les montants de ses participants. Elle retourne ladite somme
    :arg: nomCagnotte
    :return: result
    """

    stmt = users_table.select().with_only_columns(func.sum(users_table.c.montant)).where(users_table.c.nomCagnotte == nomCagnotte)

    with engine.connect() as conn:
        result = conn.execute(stmt).scalar()

    return result if result is not None else 0



def supprimerParticipation(nom, nomCagnotte):
    """
    La fonction supprime dans la base de donnée toutes les lignes possédant le nom et le nomCagnotte mis en paramètre
    :arg nom
    :arg nomCagnotte
    """

    if nom:
        stmt = users_table.delete().where(
            and_(
                users_table.c.nomCagnotte == nomCagnotte,
                users_table.c.login == nom
            )
        )
        with engine.connect() as conn:
            conn.execute(stmt)
            conn.commit()