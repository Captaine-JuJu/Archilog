from flask import Blueprint, render_template, request, redirect, url_for, session

from archilog.auth import getUtilisateur, inscrireUtilisateur
from archilog.domain import validerInscription, validerConnexion, AuthError

auth_ui = Blueprint("auth_ui", __name__)


@auth_ui.route("/inscription", methods=["GET", "POST"])
def inscription():
    if request.method == "GET":
        return render_template("inscription.html")

    login = request.form.get("login", "").strip()
    password = request.form.get("password", "")
    confirmation = request.form.get("confirmation", "")

    loginExistant = getUtilisateur(login) is not None

    try:
        validerInscription(login, password, confirmation, loginExistant)
    except AuthError as e:
        return render_template("inscription.html", erreur=str(e))

    inscrireUtilisateur(login, password)
    session["utilisateur"] = login
    return redirect(url_for("web_ui.hello_world"))


@auth_ui.route("/connexion", methods=["GET", "POST"])
def connexion():
    if request.method == "GET":
        return render_template("connexion.html")

    login = request.form.get("login", "").strip()
    password = request.form.get("password", "")

    utilisateur = getUtilisateur(login)

    try:
        validerConnexion(utilisateur, password)
    except AuthError as e:
        return render_template("connexion.html", erreur=str(e))

    session["utilisateur"] = login
    return redirect(url_for("web_ui.hello_world"))


@auth_ui.route("/deconnexion")
def deconnexion():
    session.pop("utilisateur", None)
    return redirect(url_for("auth_ui.connexion"))