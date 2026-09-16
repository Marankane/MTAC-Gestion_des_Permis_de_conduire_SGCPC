"""Génération de la lettre de convocation PDF (Module 3 du CDCF)."""

import io

from django.core.files.base import ContentFile
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas


def generer_lettre_convocation(convocation):
    dossier = convocation.dossier
    session = convocation.session
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

    p.setFont("Helvetica-Bold", 13)
    p.drawString(2 * cm, y, "LETTRE DE CONVOCATION")
    y -= 1.2 * cm

    p.setFont("Helvetica", 11)
    conducteur = dossier.conducteur
    lignes = [
        f"Objet : Convocation devant la commission de retrait de permis — Dossier {dossier.numero}",
        "",
        f"Monsieur/Madame {conducteur.prenom} {conducteur.nom},",
        "",
        "Vous êtes convoqué(e) à comparaître devant la commission de retrait de permis",
        f"le {session.date_session:%d/%m/%Y à %H:%M}, à l'adresse suivante :",
        f"    {session.lieu}",
        "",
        f"Cette convocation fait suite à l'incident du {dossier.date_incident:%d/%m/%Y} survenu à {dossier.ville}.",
        "",
        "Votre présence est obligatoire. En cas d'absence non justifiée, la commission",
        "pourra statuer sur votre dossier en votre absence.",
        "",
        "Veuillez vous munir de votre pièce d'identité et de tout document utile à votre défense.",
    ]
    for ligne in lignes:
        p.drawString(2 * cm, y, ligne)
        y -= 0.65 * cm

    y -= 1 * cm
    p.setFont("Helvetica-Oblique", 10)
    p.drawString(2 * cm, y, "Le Président de la Commission")

    p.showPage()
    p.save()
    buffer.seek(0)
    return ContentFile(buffer.getvalue(), name=f"convocation_{dossier.numero}.pdf")
