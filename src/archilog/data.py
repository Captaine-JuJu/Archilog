from sqlalchemy import func, update, and_

from archilog.database import  engine, cagnotte_table

def enregistrerParticipation(nom, montantAjoute, nomCagnotte):
    """
    ajoute à la base de donnée une nouvelle dépense lié à la cagnotte mise en paramètre
    :param nom:
    :param montant_ajoute:
    :param nomCagnotte:
    """
    verifMontant = cagnotte_table.select().where(
        and_(cagnotte_table.c.login == nom, cagnotte_table.c.nomCagnotte == nomCagnotte)
    )

    with engine.connect() as conn:
        resultat = conn.execute(verifMontant).fetchone()

        if resultat:
            nouveauMontant = float(resultat.montant) + float(montantAjoute)
            stmt = update(cagnotte_table).where(
                and_(cagnotte_table.c.login == nom, cagnotte_table.c.nomCagnotte == nomCagnotte)
            ).values(montant=nouveauMontant)
        else:
            stmt = cagnotte_table.insert().values(
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

    stmt = cagnotte_table.select().with_only_columns(func.sum(cagnotte_table.c.montant)).where(cagnotte_table.c.nomCagnotte == nomCagnotte)

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
        stmt = cagnotte_table.delete().where(
            and_(
                cagnotte_table.c.nomCagnotte == nomCagnotte,
                cagnotte_table.c.login == nom
            )
        )
        with engine.connect() as conn:
            conn.execute(stmt)
            conn.commit()