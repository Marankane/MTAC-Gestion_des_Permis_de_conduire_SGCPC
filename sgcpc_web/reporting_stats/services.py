"""Calculs statistiques du Module 7 (CDCF section 3.7) : tableaux de bord,
taux de décisions, délais moyens, taux de présence, alertes."""

from datetime import timedelta

from django.db.models import Avg, Count, DurationField, ExpressionWrapper, F, Q
from django.db.models.functions import TruncMonth
from django.utils import timezone

from commissions.models import Convocation, SessionCommission, StatutConvocation
from decisions.models import Decision, TypeDecision
from dossiers.models import Dossier, StatutDossier


def confiscations_par_mois(nb_mois=12):
    """Nombre de dossiers saisis par mois, sur les N derniers mois."""
    depuis = timezone.now() - timedelta(days=30 * nb_mois)
    qs = (
        Dossier.objects.filter(date_saisie__gte=depuis)
        .annotate(mois=TruncMonth("date_saisie"))
        .values("mois")
        .annotate(total=Count("id"))
        .order_by("mois")
    )
    return [{"mois": row["mois"].strftime("%Y-%m"), "total": row["total"]} for row in qs]


def confiscations_par_region():
    """Nombre de dossiers par ville (proxy de région en l'absence de champ région dédié)."""
    qs = Dossier.objects.values("ville").annotate(total=Count("id")).order_by("-total")
    return [{"ville": row["ville"], "total": row["total"]} for row in qs]


def confiscations_par_type_incident():
    qs = Dossier.objects.values("type_incident").annotate(total=Count("id")).order_by("-total")
    libelles = dict(Dossier._meta.get_field("type_incident").choices)
    return [
        {"type": row["type_incident"], "libelle": libelles.get(row["type_incident"], row["type_incident"]), "total": row["total"]}
        for row in qs
    ]


def taux_decisions():
    """Répartition Relaxe / Suspension / Retrait définitif / Formation obligatoire."""
    total = Decision.objects.count()
    qs = Decision.objects.values("type_decision").annotate(total=Count("id")).order_by("-total")
    libelles = dict(TypeDecision.choices)
    resultats = []
    for row in qs:
        pourcentage = round((row["total"] / total) * 100, 1) if total else 0
        resultats.append(
            {
                "type": row["type_decision"],
                "libelle": libelles.get(row["type_decision"], row["type_decision"]),
                "total": row["total"],
                "pourcentage": pourcentage,
            }
        )
    return {"total": total, "repartition": resultats}


def delais_moyens_traitement():
    """Délai moyen (en jours) entre saisie et vérification, et entre saisie et décision."""
    duree_verif = ExpressionWrapper(
        F("date_verification") - F("date_saisie"), output_field=DurationField()
    )
    delai_verification = (
        Dossier.objects.filter(date_verification__isnull=False)
        .annotate(duree=duree_verif)
        .aggregate(moyenne=Avg("duree"))["moyenne"]
    )

    dossiers_decides = Dossier.objects.filter(statut__in=[StatutDossier.DECIDE, StatutDossier.CLOTURE])
    delais_decision = []
    for dossier in dossiers_decides.select_related():
        try:
            decision = dossier.convocation.audition.decision
            delais_decision.append((decision.date_decision - dossier.date_saisie).days)
        except Exception:
            continue
    moyenne_decision = round(sum(delais_decision) / len(delais_decision), 1) if delais_decision else None

    return {
        "delai_moyen_verification_jours": round(delai_verification.days, 1) if delai_verification else None,
        "delai_moyen_decision_jours": moyenne_decision,
        "nb_dossiers_decides_mesures": len(delais_decision),
    }


def taux_presence_commissions():
    total = Convocation.objects.count()
    presents = Convocation.objects.filter(statut=StatutConvocation.PRESENT).count()
    absents = Convocation.objects.filter(statut=StatutConvocation.ABSENT).count()
    taux = round((presents / total) * 100, 1) if total else 0
    return {"total_convocations": total, "presents": presents, "absents": absents, "taux_presence_pct": taux}


def alertes():
    """Dossiers en retard (> 30 jours sans décision) et commissions surbookées."""
    limite = timezone.now() - timedelta(days=30)
    dossiers_en_retard = Dossier.objects.filter(
        date_saisie__lt=limite
    ).exclude(statut__in=[StatutDossier.DECIDE, StatutDossier.CLOTURE, StatutDossier.REJETE])

    sessions_a_venir = SessionCommission.objects.filter(date_session__gte=timezone.now())
    sessions_surbookees = [s for s in sessions_a_venir if s.surbookee]

    return {
        "dossiers_en_retard": dossiers_en_retard.select_related("conducteur"),
        "nb_dossiers_en_retard": dossiers_en_retard.count(),
        "sessions_surbookees": sessions_surbookees,
        "nb_sessions_surbookees": len(sessions_surbookees),
    }


def resume_general():
    """Chiffres clés pour la page d'accueil du tableau de bord."""
    return {
        "total_dossiers": Dossier.objects.count(),
        "dossiers_en_cours": Dossier.objects.exclude(
            statut__in=[StatutDossier.CLOTURE, StatutDossier.REJETE]
        ).count(),
        "dossiers_clotures": Dossier.objects.filter(statut=StatutDossier.CLOTURE).count(),
        "total_decisions": Decision.objects.count(),
    }
