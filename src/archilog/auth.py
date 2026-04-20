from archilog.database import engine, utilisateur_table
from archilog.domain import hasherPassword


def getUtilisateur(login):
    """
    Récupère un utilisateur en base par son login.
    Retourne la ligne ou None.
    :param login: login de l'utilisateur
    """
    stmt = utilisateur_table.select().where(utilisateur_table.c.login == login)
    with engine.connect() as conn:
        return conn.execute(stmt).fetchone()


def inscrireUtilisateur(login, password):
    """
    Insère un nouvel utilisateur en base avec son mot de passe hashé.
    :param login: login de l'utilisateur
    :param password: mot de passe en clair
    """
    passwordHash = hasherPassword(password)
    stmt = utilisateur_table.insert().values(login=login, password=passwordHash)
    with engine.begin() as conn:
        conn.execute(stmt)