import click
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, Blueprint, session

from archilog.data import enregistrerParticipation, totalCagnotte, supprimerParticipation
from archilog.domain import calculeQuiDoitAQui
from archilog.database import cagnotte_table, engine, metadata

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

    # Cagnottes où l'utilisateur connecté a participé
    mesCagnottesStmt = (
        cagnotte_table.select()
        .with_only_columns(cagnotte_table.c.nomCagnotte)
        .where(cagnotte_table.c.login == utilisateur)
        .distinct()
    )

    # Toutes les cagnottes distinctes
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
    login = session["utilisateur"]  # ← depuis la session
    verif = cagnotte_table.select().where(cagnotte_table.c.nomCagnotte == nomCagnotte)
    with engine.connect() as conn:
        verification = conn.execute(verif).fetchone()
    if len(nomCagnotte) < 5:
        return redirect(url_for('web_ui.hello_world', code="2"))
    if verification:
        return redirect(url_for('web_ui.hello_world', code="4"))
    if montant <= "0" or montant is None:
        return redirect(url_for('web_ui.hello_world', code="3"))

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
    nom = session["utilisateur"]  # ← plus besoin du formulaire
    montant = float(request.form.get('montant', 0))
    nomCagnotte = request.form.get('nomCagnotte')
    if montant <= 0 or montant is None:
        return redirect(url_for('web_ui.voirCagnotte', nom=nomCagnotte, code=1))
    enregistrerParticipation(nom, montant, nomCagnotte)
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


@click.group()
def cli():
    pass

@cli.command()
def init_database():
    metadata.create_all(engine)

@cli.command()
@click.option("--nom-participant", prompt="Nom du participant ")
@click.option("--nom-cagnotte", prompt="Nom de la cagnotte ")
@click.option("--montant", prompt="Montant ")
def creationCagnotteCli(nom_participant, nom_cagnotte, montant):
    verif = cagnotte_table.select().where(cagnotte_table.c.nomCagnotte == nom_cagnotte)
    with engine.connect() as conn:
        verification = conn.execute(verif).one_or_none()

    if len(nom_participant) < 2:
        click.echo("Le nom du participant doit comprendre plus de deux caractères")
    elif len(nom_cagnotte) < 5:
        click.echo("Le nom de la cagnotte doit comprendre plus de 5 caractères")
    elif verification is not None:
        click.echo("Le nom de la cagnotte existe deja")
    elif montant <= "0" or montant is None:
        click.echo("Le montant doit être positif et non nul")
    else:
        stmt = cagnotte_table.insert().values(login=nom_participant, montant=montant, nomCagnotte=nom_cagnotte)
        with engine.begin() as conn:
            conn.execute(stmt)
            click.echo("Ajout réussi")


@cli.command()
@click.option("--nom-cagnotte", prompt="Nom de la cagnotte ")
def voirCagnotteCli(nom_cagnotte):
    exist = cagnotte_table.select().where(cagnotte_table.c.nomCagnotte == nom_cagnotte)
    with engine.connect() as conn:
        existant = conn.execute(exist).all()
    if not existant:
        click.echo("La cagnotte n'existe pas")
    else:
        click.echo("La cagnotte " + nom_cagnotte + " contient les transactions suivantes :")
        for i in existant:
            click.echo(f"{i.login} : {i.montant}")


@cli.command()
@click.option("--nom-participant", prompt="Nom du participant ")
@click.option("--nom-cagnotte", prompt="Nom de la cagnotte ")
@click.option("--nouveau-montant", prompt="Montant ")
def ajoutParticipationCli(nom_participant, nom_cagnotte, nouveau_montant):
    exist = cagnotte_table.select().where(cagnotte_table.c.nomCagnotte == nom_cagnotte)
    with engine.connect() as conn:
        existant = conn.execute(exist).all()
    if not existant:
        click.echo("La cagnotte n'existe pas")
    if int(nouveau_montant) <= 0 or nouveau_montant is None:
        click.echo("Le montant doit etre positif et non nul")
    if len(nom_participant) < 2:
        click.echo("Le login doit contenir au moins 3 caractères")
    enregistrerParticipation(nom_participant, nouveau_montant, nom_cagnotte)


@cli.command()
@click.option("--nom-participant", prompt="Nom du participant ")
@click.option("--nom-cagnotte", prompt="Nom de la cagnotte ")
def supprimerParticipationCli(nom_participant, nom_cagnotte):
    exist = cagnotte_table.select().where(
        cagnotte_table.c.nomCagnotte == nom_cagnotte and cagnotte_table.c.login == nom_participant
    )
    with engine.connect() as conn:
        existant = conn.execute(exist).all()
    if not existant:
        click.echo("Ce login n'existe pas dans la cagnotte, ou bien la cagnotte n'existe pas")
    supprimerParticipation(nom_participant, nom_cagnotte)
    click.echo("La participation de " + nom_participant + " à la cagnotte " + nom_cagnotte + " a bien été supprimée")
    if totalCagnotte(nom_cagnotte) == 0:
        supp = cagnotte_table.delete().where(cagnotte_table.c.nomCagnotte == nom_cagnotte)
        with engine.connect() as conn:
            conn.execute(supp)
            conn.commit()
        click.echo("La cagnotte a été supprimée")