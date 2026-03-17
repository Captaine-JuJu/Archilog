def calculeQuiDoitAQui(participations, total):
    """
    recupère la liste de tous les participants avec leur montant dans la cagnotte et le montant total de la cagnotte et
    calcul la part que chaque participant doit payer pour équilibrer les dépenses puis répartit les dettes et les
    créances a chacun
    :param participations:
    :param total:
    :return: transaction
    """
    if not participations or total == 0:
        return []

    nbParticipants = len(participations)
    moyennePaiement = total/nbParticipants

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
            if montantAPayer <= 0:break
            if creance['remboursementAVenir'] <= 0:continue

            paye = min(montantAPayer, creance['remboursementAVenir'])

            transaction.append(f"{dette['nom']} doit donner {round(paye, 2)}€ à {creance['nom']}")

            montantAPayer -= paye
            creance['remboursementAVenir'] -= paye

    return transaction