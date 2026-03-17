from flask import Flask, render_template, request, redirect, url_for

from src.archilog.data import enregistrerParticipation, totalCagnotte, supprimerParticipation
from src.archilog.domain import calculeQuiDoitAQui
from src.archilog.creation_table import users_table, engine

app = Flask(__name__)

@app.route("/")
def hello_world():
    tabl = users_table.select().with_only_columns(users_table.c.nomCagnotte).distinct()
    code = request.args.get('code')
    with engine.connect() as conn:
        result = conn.execute(tabl)
        print(result)

    print(request.form, flush=True)
    return render_template("home.html", result=result, code=code)

@app.route("/cagnotte/creationCagnotte", methods=["GET", "POST"])
def creationCagnotte():
    nomCagnotte = request.form.get('nomCagnotte')
    montant = request.form.get("montant")
    login = request.form.get("nom")
    verif = users_table.select().where(users_table.c.nomCagnotte == nomCagnotte)
    with engine.connect() as conn:
        verification = conn.execute(verif)
    if len(login) < 2:
        return redirect(url_for('hello_world', code="1"))
    if len(nomCagnotte) < 5:
        return redirect(url_for('hello_world', code="2"))
    if verification:
        return redirect(url_for('hello_world', code="4"))
    if montant <= "0" or montant is None:
        return redirect(url_for('hello_world', code="3"))

    stmt = users_table.insert().values(login=request.form.get('nom'), montant=request.form.get('montant'), nomCagnotte=request.form.get('nomCagnotte'))

    with engine.begin() as conn:
        result = conn.execute(stmt)
        print(result)
    return redirect(url_for('voirCagnotte', nom=nomCagnotte))


@app.route("/cagnotte/choix", methods=["GET", "POST"])
def cagnotteChoix():
    nomCagnotte = request.form.get("cagnotte")
    if nomCagnotte :
        return redirect(url_for('voirCagnotte', nom=nomCagnotte))
    return redirect(url_for('hello_world'))

@app.route("/cagnotte/voir/<nom>")
def voirCagnotte(nom):
    code = request.args.get('code')
    listParticipant = users_table.select().where(users_table.c.nomCagnotte == nom)
    total = totalCagnotte(nom)
    with engine.connect() as conn:
        participations = conn.execute(listParticipant).fetchall()
    remboursement = calculeQuiDoitAQui(participations, total)
    return render_template("cagnotte.html", nomAffichage=nom, participations=participations, total=total, remboursement=remboursement, error=code)

@app.route("/cagnotte/ajoutCagnotte", methods=["POST", "GET"])
def ajouterParticipation():
    nom = request.form.get('nom')
    montant = float(request.form.get('montant', 0))
    nomCagnotte = request.form.get('nomCagnotte')
    if montant <= 0 or montant is None:
        return redirect(url_for('voirCagnotte', nom=nomCagnotte, code=1))
    if len(nom) < 2:
        return redirect(url_for('voirCagnotte', nom=nomCagnotte, code=2))
    enregistrerParticipation(nom, montant, nomCagnotte)

    return redirect(url_for('voirCagnotte', nom=nomCagnotte))

@app.route("/cagnotte/supprimerCagnotte", methods=["GET", "POST"])
def retirerParticipation():

    loginSuppression = request.form.get('nom')
    nomCagnotte = request.form.get('nomCagnotte')

    supprimerParticipation(loginSuppression, nomCagnotte)

    total = totalCagnotte(nomCagnotte)
    if total <= 0:
        supp = users_table.delete().where(users_table.c.nomCagnotte == nomCagnotte)
        with engine.connect() as conn:
            conn.execute(supp)
            conn.commit()
        return redirect(url_for('hello_world'))
    return redirect(url_for('voirCagnotte', nom=nomCagnotte))