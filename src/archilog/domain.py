import hashlib


class CagnotteError(Exception):
    """Exception métier pour les erreurs de cagnotte."""
    pass


class AuthError(Exception):
    """Exception métier pour les erreurs d'authentification."""
    pass


# --- Auth ---

def hasherPassword(password):
    """
    Retourne le hash SHA-256 du mot de passe.
    :param password: mot de passe en clair
    :return: hash hexadécimal
    """
    return hashlib.sha256(password.encode()).hexdigest()


def validerInscription(login, password, confirmation, loginExistant):
    """
    Valide les données d'inscription.
    Lève AuthError si les données sont invalides.
    :param login: login choisi
    :param password: mot de passe
    :param confirmation: confirmation du mot de passe
    :param loginExistant: True si le login est déjà pris
    """
    if len(login) < 2:
        raise AuthError("Le login doit contenir au moins 2 caractères.")
    if len(password) < 6:
        raise AuthError("Le mot de passe doit contenir au moins 6 caractères.")
    if password != confirmation:
        raise AuthError("Les mots de passe ne correspondent pas.")
    if loginExistant:
        raise AuthError("Ce login est déjà utilisé.")


def validerConnexion(utilisateur, password):
    """
    Vérifie que le mot de passe correspond à l'utilisateur trouvé en base.
    Lève AuthError si les identifiants sont incorrects.
    :param utilisateur: ligne retournée par la base, ou None
    :param password: mot de passe en clair saisi
    """
    if utilisateur is None or utilisateur.password != hasherPassword(password):
        raise AuthError("Login ou mot de passe incorrect.")


# --- Cagnotte ---

def validerCreationCagnotte(nomCagnotte, montant, cagnotteExistante):
    """
    Valide les données de création d'une cagnotte.
    Lève CagnotteError si les données sont invalides.
    :param nomCagnotte: nom de la cagnotte
    :param montant: montant initial
    :param cagnotteExistante: True si une cagnotte avec ce nom existe déjà
    """
    if len(nomCagnotte) < 5:
        raise CagnotteError("Le nom de la cagnotte doit contenir au moins 5 caractères.")
    if cagnotteExistante:
        raise CagnotteError("Cette cagnotte existe déjà.")
    if montant is None or float(montant) <= 0:
        raise CagnotteError("Le montant doit être positif et non nul.")


def validerAjoutParticipation(montant):
    """
    Valide les données d'ajout d'une participation.
    Lève CagnotteError si les données sont invalides.
    :param montant: montant à ajouter
    """
    if montant is None or float(montant) <= 0:
        raise CagnotteError("Le montant doit être positif et non nul.")


def calculeQuiDoitAQui(participations, total):
    """
    Recupère la liste de tous les participants avec leur montant dans la cagnotte et le montant total de la cagnotte et
    calcul la part que chaque participant doit payer pour équilibrer les dépenses puis répartit les dettes et les
    créances a chacun.
    :param participations:
    :param total:
    :return: transaction
    """
    if not participations or total == 0:
        return []

    nbParticipants = len(participations)
    moyennePaiement = total / nbParticipants

    balances = []
    for participant in participations:
        balances.append({
            'nom': participant.login,
            'montant': participant.montant - moyennePaiement,
        })

    endetter = [{'nom': b['nom'], 'montantAPayer': abs(b['montant'])} for b in balances if b['montant'] < 0]
    creancier = [{'nom': b['nom'], 'remboursementAVenir': b['montant']} for b in balances if b['montant'] > 0]

    transaction = []

    for dette in endetter:
        montantAPayer = dette['montantAPayer']
        for creance in creancier:
            if montantAPayer <= 0:
                break
            if creance['remboursementAVenir'] <= 0:
                continue
            paye = min(montantAPayer, creance['remboursementAVenir'])
            transaction.append(f"{dette['nom']} doit donner {round(paye, 2)}€ à {creance['nom']}")
            montantAPayer -= paye
            creance['remboursementAVenir'] -= paye

    return transaction