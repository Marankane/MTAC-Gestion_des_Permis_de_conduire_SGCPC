import csv
import io
import json

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

from dossiers.models import Dossier

from . import services


@login_required
def tableau_de_bord(request):
    decisions = services.taux_decisions()
    contexte = {
        "resume": services.resume_general(),
        "par_mois": services.confiscations_par_mois(),
        "par_region": services.confiscations_par_region(),
        "par_type": services.confiscations_par_type_incident(),
        "decisions": decisions,
        "delais": services.delais_moyens_traitement(),
        "presence": services.taux_presence_commissions(),
        "alertes": services.alertes(),
        # Versions JSON pour les graphiques Chart.js (json.dumps produit du JSON
        # valide ; le rendu direct d'une liste Python via |safe ne l'est pas).
        "par_mois_json": json.dumps(services.confiscations_par_mois()),
        "par_region_json": json.dumps(services.confiscations_par_region()),
        "par_type_json": json.dumps(services.confiscations_par_type_incident()),
        "decisions_json": json.dumps(decisions["repartition"]),
    }
    return render(request, "reporting_stats/dashboard.html", contexte)


@login_required
def export_csv(request):
    """Export CSV de tous les dossiers, pour analyse externe (CDCF 3.7)."""
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="dossiers_sgcpc.csv"'
    # BOM UTF-8 : nécessaire pour qu'Excel sous Windows détecte correctement
    # l'encodage et affiche les accents sans les corrompre.
    response.write("\ufeff")

    writer = csv.writer(response)
    writer.writerow(
        [
            "Numéro", "Date incident", "Ville", "Type incident", "Statut",
            "Conducteur", "N° Permis", "Véhicule", "Plaque",
            "Blessés", "Décès", "Date de saisie",
        ]
    )
    dossiers = Dossier.objects.select_related("conducteur", "vehicule").order_by("-date_saisie")
    for d in dossiers:
        writer.writerow(
            [
                d.numero, d.date_incident.strftime("%d/%m/%Y %H:%M"), d.ville,
                d.get_type_incident_display(), d.get_statut_display(),
                f"{d.conducteur.prenom} {d.conducteur.nom}", d.conducteur.numero_permis,
                f"{d.vehicule.marque} {d.vehicule.modele}", d.vehicule.plaque,
                d.nombre_blesses, d.nombre_deces, d.date_saisie.strftime("%d/%m/%Y %H:%M"),
            ]
        )
    return response


@login_required
def export_pdf(request):
    """Rapport officiel PDF de synthèse (CDCF 3.7 : rapports Ministère/Conseil des Ministres)."""
    resume = services.resume_general()
    decisions = services.taux_decisions()
    delais = services.delais_moyens_traitement()
    presence = services.taux_presence_commissions()
    alertes = services.alertes()

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
    p.drawCentredString(largeur / 2, y, "RAPPORT DE SYNTHÈSE — SGCPC")
    y -= 0.6 * cm
    p.setFont("Helvetica", 9)
    from django.utils import timezone as tz

    p.drawCentredString(largeur / 2, y, f"Généré le {tz.now():%d/%m/%Y à %H:%M}")
    y -= 1.3 * cm

    def section(titre):
        nonlocal y
        p.setFont("Helvetica-Bold", 12)
        p.drawString(2 * cm, y, titre)
        y -= 0.7 * cm
        p.setFont("Helvetica", 10)

    def ligne(texte):
        nonlocal y
        p.drawString(2.3 * cm, y, texte)
        y -= 0.55 * cm

    section("1. Chiffres clés")
    ligne(f"Total des dossiers : {resume['total_dossiers']}")
    ligne(f"Dossiers en cours : {resume['dossiers_en_cours']}")
    ligne(f"Dossiers clôturés : {resume['dossiers_clotures']}")
    ligne(f"Total des décisions rendues : {resume['total_decisions']}")
    y -= 0.4 * cm

    section("2. Répartition des décisions")
    for item in decisions["repartition"]:
        ligne(f"{item['libelle']} : {item['total']} ({item['pourcentage']}%)")
    y -= 0.4 * cm

    section("3. Délais moyens de traitement")
    verif = delais["delai_moyen_verification_jours"]
    dec = delais["delai_moyen_decision_jours"]
    ligne(f"Saisie -> Vérification : {verif if verif is not None else 'N/A'} jour(s)")
    ligne(f"Saisie -> Décision : {dec if dec is not None else 'N/A'} jour(s)")
    y -= 0.4 * cm

    section("4. Présence aux commissions")
    ligne(f"Taux de présence : {presence['taux_presence_pct']}% ({presence['presents']}/{presence['total_convocations']})")
    y -= 0.4 * cm

    section("5. Alertes")
    ligne(f"Dossiers en retard (> 30 jours) : {alertes['nb_dossiers_en_retard']}")
    ligne(f"Sessions de commission surbookées : {alertes['nb_sessions_surbookees']}")

    p.showPage()
    p.save()
    buffer.seek(0)

    response = HttpResponse(buffer.read(), content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="rapport_sgcpc.pdf"'
    return response


@login_required
def alertes_view(request):
    contexte = services.alertes()
    return render(request, "reporting_stats/alertes.html", contexte)
