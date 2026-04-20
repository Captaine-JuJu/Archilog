from functools import wraps
from flask import render_template, request, redirect, url_for, Blueprint, session

from archilog.data import enregistrerParticipation, totalCagnotte, supprimerParticipation
from archilog.domain import calculeQuiDoitAQui, validerCreationCagnotte, validerAjoutParticipation, CagnotteError
from archilog.database import cagnotte_table, engine


web_ui = Blueprint("web_ui", __name__)


def login_required(f):
    """Décorateur qui redirige vers la connexion si l'utilisateur n'est pas connecté."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "utilisateur" not in session:
            return redirect(url_for("auth_ui.connexion"))
        return f(*args, **kwargs)
    return decorated_function


@web_ui.route("/")
@login_required
def hello_world():
    utilisateur = session["utilisateur"]
    code = request.args.get('code')

    mesCagnottesStmt = (
        cagnotte_table.select()
        .with_only_columns(cagnotte_table.c.nomCagnotte)
        .where(cagnotte_table.c.login == utilisateur)
        .distinct()
    )
    toutesCagnottesStmt = (
        cagnotte_table.select()
        .with_only_columns(cagnotte_table.c.nomCagnotte)
        .distinct()
    )

    with engine.connect() as conn:
        mesCagnottes = conn.execute(mesCagnottesStmt).fetchall()
        toutesCagnottes = conn.execute(toutesCagnottesStmt).fetchall()

    nomsMesCagnottes = {r.nomCagnotte for r in mesCagnottes}
    autresCagnottes = [r for r in toutesCagnottes if r.nomCagnotte not in nomsMesCagnottes]

    return render_template(
        "home.html",
        mesCagnottes=mesCagnottes,
        autresCagnottes=autresCagnottes,
        code=code,
        utilisateur=utilisateur
    )


@web_ui.route("/cagnotte/creationCagnotte", methods=["GET", "POST"])
@login_required
def creationCagnotte():
    nomCagnotte = request.form.get('nomCagnotte')
    montant = request.form.get("montant")
    login = session["utilisateur"]

    verif = cagnotte_table.select().where(cagnotte_table.c.nomCagnotte == nomCagnotte)
    with engine.connect() as conn:
        cagnotteExistante = conn.execute(verif).fetchone() is not None

    try:
        validerCreationCagnotte(nomCagnotte, montant, cagnotteExistante)
    except CagnotteError as e:
        return render_template(
            "home.html",
            erreur=str(e),
            mesCagnottes=[],
            autresCagnottes=[],
            utilisateur=login
        )

    stmt = cagnotte_table.insert().values(login=login, montant=montant, nomCagnotte=nomCagnotte)
    with engine.begin() as conn:
        conn.execute(stmt)
    return redirect(url_for('web_ui.voirCagnotte', nom=nomCagnotte))


@web_ui.route("/cagnotte/choix", methods=["GET", "POST"])
@login_required
def cagnotteChoix():
    nomCagnotte = request.form.get("cagnotte")
    if nomCagnotte:
        return redirect(url_for('web_ui.voirCagnotte', nom=nomCagnotte))
    return redirect(url_for('web_ui.hello_world'))


@web_ui.route("/cagnotte/voir/<nom>")
@login_required
def voirCagnotte(nom):
    code = request.args.get('code')
    listParticipant = cagnotte_table.select().where(cagnotte_table.c.nomCagnotte == nom)
    total = totalCagnotte(nom)
    with engine.connect() as conn:
        participations = conn.execute(listParticipant).fetchall()
    remboursement = calculeQuiDoitAQui(participations, total)
    return render_template(
        "cagnotte.html",
        nomAffichage=nom,
        participations=participations,
        total=total,
        remboursement=remboursement,
        error=code,
        utilisateur=session["utilisateur"]
    )


@web_ui.route("/cagnotte/ajoutCagnotte", methods=["POST", "GET"])
@login_required
def ajouterParticipation():
    nom = session["utilisateur"]
    montant = request.form.get('montant')
    nomCagnotte = request.form.get('nomCagnotte')

    try:
        validerAjoutParticipation(montant)
    except CagnotteError as e:
        return render_template(
            "cagnotte.html",
            nomAffichage=nomCagnotte,
            erreur=str(e),
            participations=[],
            total=0,
            remboursement=[],
            utilisateur=nom
        )

    enregistrerParticipation(nom, float(montant), nomCagnotte)
    return redirect(url_for('web_ui.voirCagnotte', nom=nomCagnotte))


@web_ui.route("/cagnotte/supprimerCagnotte", methods=["GET", "POST"])
@login_required
def retirerParticipation():
    loginSuppression = request.form.get('nom')
    nomCagnotte = request.form.get('nomCagnotte')

    supprimerParticipation(loginSuppression, nomCagnotte)

    total = totalCagnotte(nomCagnotte)
    if total <= 0:
        supp = cagnotte_table.delete().where(cagnotte_table.c.nomCagnotte == nomCagnotte)
        with engine.connect() as conn:
            conn.execute(supp)
            conn.commit()
        return redirect(url_for('web_ui.hello_world'))
    return redirect(url_for('web_ui.voirCagnotte', nom=nomCagnotte))