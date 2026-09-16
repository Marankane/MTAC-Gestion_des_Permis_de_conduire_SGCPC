"""Génération du bordereau de transmission (PDF) et du QR code de vérification (Module 1 du CDCF)."""

import io

import qrcode
from django.core.files.base import ContentFile
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas


def generer_qrcode_dossier(dossier):
    """Retourne un ContentFile PNG du QR code pointant vers l'UUID de vérification du dossier."""
    url_verification = f"/dossiers/verifier/{dossier.uuid}/"
    img = qrcode.make(url_verification)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return ContentFile(buffer.getvalue(), name=f"qr_{dossier.numero}.png")


def generer_bordereau_pdf(dossier):
    """Génère le bordereau de transmission PDF (Police/Gendarmerie -> Administration)."""
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    largeur, hauteur = A4

    y = hauteur - 2 * cm
    p.setFont("Helvetica-Bold", 16)
    p.drawCentredString(largeur / 2, y, "RÉPUBLIQUE DU NIGER")
    y -= 0.7 * cm
    p.setFont("Helvetica", 11)
    p.drawCentredString(largeur / 2, y, "Ministère des Transports — Direction de la Sécurité Routière")
    y -= 1.2 * cm
    p.setFont("Helvetica-Bold", 14)
    p.drawCentredString(largeur / 2, y, "BORDEREAU DE TRANSMISSION DE PERMIS CONFISQUÉ")
    y -= 1.5 * cm

    p.setFont("Helvetica-Bold", 11)
    p.drawString(2 * cm, y, f"Numéro de dossier : {dossier.numero}")
    y -= 1 * cm

    p.setFont("Helvetica", 10)
    lignes = [
        f"Date et heure de l'incident : {dossier.date_incident:%d/%m/%Y %H:%M}",
        f"Lieu : {dossier.ville} {dossier.quartier}",
        f"Type d'incident : {dossier.get_type_incident_display()}",
        "",
        f"Conducteur : {dossier.conducteur.prenom} {dossier.conducteur.nom}",
        f"N° Permis : {dossier.conducteur.numero_permis}",
        f"Téléphone : {dossier.conducteur.telephone}",
        "",
        f"Véhicule : {dossier.vehicule.marque} {dossier.vehicule.modele} ({dossier.vehicule.plaque})",
        "",
        f"Blessés : {dossier.nombre_blesses}    Décès : {dossier.nombre_deces}",
        "",
        f"Agent saisisseur : {dossier.agent_saisisseur.get_full_name() or dossier.agent_saisisseur.username}",
        f"Date de saisie : {dossier.date_saisie:%d/%m/%Y %H:%M}",
    ]
    for ligne in lignes:
        p.drawString(2 * cm, y, ligne)
        y -= 0.6 * cm

    # QR code
    qr_content = generer_qrcode_dossier(dossier)
    from reportlab.lib.utils import ImageReader

    qr_img = ImageReader(io.BytesIO(qr_content.read()))
    p.drawImage(qr_img, largeur - 5 * cm, 2 * cm, width=3 * cm, height=3 * cm)
    p.setFont("Helvetica", 8)
    p.drawString(largeur - 5 * cm, 1.7 * cm, "Scanner pour vérifier le dossier")

    y -= 1.5 * cm
    p.line(2 * cm, y, 9 * cm, y)
    p.drawString(2 * cm, y - 0.5 * cm, "Signature de l'agent")
    p.line(largeur - 9 * cm, y, largeur - 2 * cm, y)
    p.drawString(largeur - 9 * cm, y - 0.5 * cm, "Signature du conducteur")

    p.showPage()
    p.save()
    buffer.seek(0)
    return ContentFile(buffer.getvalue(), name=f"bordereau_{dossier.numero}.pdf")
