from flask import Blueprint, jsonify
from spectree import SpecTree, SecurityScheme
from flask_httpauth import HTTPTokenAuth
from pydantic import BaseModel, Field

from archilog.data import enregistrerParticipation, totalCagnotte, supprimerParticipation
from archilog.domain import (
    calculeQuiDoitAQui,
    validerCreationCagnotte,
    validerAjoutParticipation,
    CagnotteError,
)
from archilog.database import cagnotte_table, engine
from archilog.auth import getUtilisateur
from archilog.domain import hasherPassword

api = Blueprint("api", __name__)

api_spec = SpecTree(
    "flask",
    title="Archilog API",
    version="0.2",
    security_schemes=[
        SecurityScheme(
            name="bearer_token",
            data={"type": "http", "scheme": "bearer"}
        )
    ],
    security=[{"bearer_token": []}]
)

token_auth = HTTPTokenAuth(scheme="Bearer")


@token_auth.verify_token
def verify_token(token):
    """
    Le token est le login:passwordHash encodé simplement.
    Format attendu : "login:sha256hash"
    """
    try:
        login, password_hash = token.split(":", 1)
    except ValueError:
        return None

    utilisateur = getUtilisateur(login)
    if utilisateur and utilisateur.password == password_hash:
        return login
    return None

class cagnotteCreation(BaseModel):
    nomCagnotte: str = Field(min_length=5)
    montant: float = Field(gt=0)


class participationAjout(BaseModel):
    montant: float = Field(gt=0)


class cagnotteReponse(BaseModel):
    nomCagnotte: str
    total: float
    remboursements: list[str]


class participantReponse(BaseModel):
    login: str
    montant: float

@api.errorhandler(CagnotteError)
def handle_cagnotte_error(e):
    return jsonify({"erreur": str(e)}), 400


@api.errorhandler(401)
def handle_unauthorized(e):
    return jsonify({"erreur": "Token invalide ou manquant."}), 401


@api.errorhandler(404)
def handle_not_found(e):
    return jsonify({"erreur": "Ressource introuvable."}), 404

@api.get("/cagnottes")
@token_auth.login_required
@api_spec.validate(tags=["cagnottes"])
def listerCagnottes():
    """Récupère toutes les cagnottes."""
    stmt = (
        cagnotte_table.select()
        .with_only_columns(cagnotte_table.c.nomCagnotte)
        .distinct()
    )
    with engine.connect() as conn:
        cagnottes = conn.execute(stmt).fetchall()

    return jsonify([{"nomCagnotte": r.nomCagnotte} for r in cagnottes])


@api.post("/cagnottes")
@token_auth.login_required
@api_spec.validate(tags=["cagnottes"])
def creerCagnotte(json: cagnotteCreation):
    """Crée une nouvelle cagnotte."""
    login = token_auth.current_user()

    verif = cagnotte_table.select().where(cagnotte_table.c.nomCagnotte == json.nomCagnotte)
    with engine.connect() as conn:
        cagnotteExistante = conn.execute(verif).fetchone() is not None

    validerCreationCagnotte(json.nomCagnotte, json.montant, cagnotteExistante)

    stmt = cagnotte_table.insert().values(
        login=login,
        montant=json.montant,
        nomCagnotte=json.nomCagnotte
    )
    with engine.begin() as conn:
        conn.execute(stmt)

    return jsonify({"nomCagnotte": json.nomCagnotte, "montant": json.montant}), 201


@api.get("/cagnottes/<nom>")
@token_auth.login_required
@api_spec.validate(tags=["cagnottes"])
def voirCagnotte(nom: str):
    """Récupère le détail d'une cagnotte."""
    listParticipant = cagnotte_table.select().where(cagnotte_table.c.nomCagnotte == nom)
    total = totalCagnotte(nom)

    with engine.connect() as conn:
        participations = conn.execute(listParticipant).fetchall()

    if not participations:
        return jsonify({"erreur": "Cagnotte introuvable."}), 404

    remboursements = calculeQuiDoitAQui(participations, total)

    return jsonify({
        "nomCagnotte": nom,
        "total": total,
        "participants": [{"login": p.login, "montant": p.montant} for p in participations],
        "remboursements": remboursements,
    })


@api.post("/cagnottes/<nom>/participations")
@token_auth.login_required
@api_spec.validate(tags=["cagnottes"])
def ajouterParticipation(nom: str, json: participationAjout):
    """Ajoute une participation à une cagnotte."""
    login = token_auth.current_user()

    validerAjoutParticipation(json.montant)
    enregistrerParticipation(login, json.montant, nom)

    return jsonify({"login": login, "montant": json.montant, "nomCagnotte": nom}), 201


@api.delete("/cagnottes/<nom>/participations/<login>")
@token_auth.login_required
@api_spec.validate(tags=["cagnottes"])
def supprimerParticipation_(nom: str, login: str):
    """Supprime la participation d'un utilisateur dans une cagnotte."""
    supprimerParticipation(login, nom)

    total = totalCagnotte(nom)
    if total <= 0:
        supp = cagnotte_table.delete().where(cagnotte_table.c.nomCagnotte == nom)
        with engine.connect() as conn:
            conn.execute(supp)
            conn.commit()

    return jsonify({"message": f"Participation de {login} supprimée."}), 200