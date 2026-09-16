"""Génération de l'arrêté de décision PDF (Module 4 du CDCF)."""

import io

from django.core.files.base import ContentFile
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas


def generer_arrete_decision(decision):
    dossier = decision.audition.convocation.dossier
    conducteur = dossier.conducteur
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    largeur, hauteur = A4

    y = hauteur - 2 * cm
    p.setFont("Helvetica-Bold", 16)
    p.drawCentredString(largeur / 2, y, "RÉPUBLIQUE DU NIGER")
    y -= 0.7 * cm
    p.setFont("Helvetica", 11)
    p.drawCentredString(largeur / 2, y, "Ministère des Transports — Commission de Retrait de Permis")
    y -= 1.5 * cm

    p.setFont("Helvetica-Bold", 14)
    p.drawCentredString(largeur / 2, y, "ARRÊTÉ DE DÉCISION")
    y -= 1 * cm
    p.setFont("Helvetica", 10)
    p.drawCentredString(largeur / 2, y, f"Dossier n° {dossier.numero}")
    y -= 1.3 * cm

    p.setFont("Helvetica", 11)
    lignes = [
        f"Conducteur : {conducteur.prenom} {conducteur.nom} (Permis n° {conducteur.numero_permis})",
        f"Incident du {dossier.date_incident:%d/%m/%Y} à {dossier.ville}",
        "",
        f"Décision : {decision.get_type_decision_display()}",
    ]
    if decision.type_decision == "SUSPENSION" and decision.duree_suspension_mois:
        lignes.append(f"Durée de suspension : {decision.duree_suspension_mois} mois")
        if decision.date_fin_suspension:
            lignes.append(f"Date de fin de suspension : {decision.date_fin_suspension:%d/%m/%Y}")
    lignes += [
        "",
        "Motivation :",
        decision.motivation,
        "",
        f"Décidé le {decision.date_decision:%d/%m/%Y} par {decision.decide_par}",
        "",
        "Voies de recours : le conducteur dispose d'un délai de 15 jours pour introduire",
        "un recours auprès du tribunal compétent.",
    ]
    for ligne in lignes:
        for sous_ligne in [ligne[i:i + 95] for i in range(0, max(len(ligne), 1), 95)]:
            p.drawString(2 * cm, y, sous_ligne)
            y -= 0.6 * cm

    p.showPage()
    p.save()
    buffer.seek(0)
    return ContentFile(buffer.getvalue(), name=f"arrete_{dossier.numero}.pdf")
