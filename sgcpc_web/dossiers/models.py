import uuid
from datetime import date

from django.conf import settings
from django.db import models
from django.urls import reverse


def generer_numero_dossier():
    """Génère un numéro unique du type Niger-2026-000123."""
    annee = date.today().year
    dernier = Dossier.objects.filter(numero__startswith=f"Niger-{annee}-").order_by("-numero").first()
    if dernier:
        seq = int(dernier.numero.split("-")[-1]) + 1
    else:
        seq = 1
    return f"Niger-{annee}-{seq:06d}"


class TypeIncident(models.TextChoices):
    CORPOREL = "CORPOREL", "Accident corporel"
    MATERIEL = "MATERIEL", "Accident matériel"
    DELIT_FUITE = "DELIT_FUITE", "Délit de fuite"
    AUTRE = "AUTRE", "Autre infraction grave"


class TypeVehicule(models.TextChoices):
    VOITURE = "VOITURE", "Voiture"
    CAMION = "CAMION", "Camion"
    MOTO = "MOTO", "Moto"
    AUTRE = "AUTRE", "Autre"


class TypePermis(models.TextChoices):
    A = "A", "A"
    BC = "BC", "BC"
    D = "D", "D"
    E = "E", "E"
    F = "F", "F"


class StatutPermis(models.TextChoices):
    ACTIF = "ACTIF", "Actif"
    SUSPENDU = "SUSPENDU", "Suspendu"
    EXPIRE = "EXPIRE", "Expire"
    RETIRE = "RETIRE", "Retiré"


class StatutDossier(models.TextChoices):
    SAISI = "SAISI", "Saisi (en attente de vérification)"
    COMPLEMENT_DEMANDE = "COMPLEMENT_DEMANDE", "Complément demandé"
    VERIFIE = "VERIFIE", "Vérifié / transmis à la commission"
    REJETE = "REJETE", "Rejeté"
    PROGRAMME = "PROGRAMME", "Programmé en commission"
    DECIDE = "DECIDE", "Décision rendue"
    CLOTURE = "CLOTURE", "Clôturé / archivé"


class Conducteur(models.Model):
    code_qr = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    date_naissance = models.DateField()
    lieu_naissance = models.CharField(max_length=150, blank=True)
    numero_permis = models.CharField(max_length=50)
    mention_permis = models.CharField(max_length=100, default="Nationale")
    type_permis = models.CharField(max_length=2, choices=TypePermis.choices, default=TypePermis.A)
    statut_permis = models.CharField(max_length=10, choices=StatutPermis.choices, default=StatutPermis.ACTIF)
    date_delivrance = models.DateField(null=True, blank=True)
    date_expiration = models.DateField(null=True, blank=True)
    date_suspension = models.DateField(null=True, blank=True)
    telephone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    adresse = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = "Conducteur"
        verbose_name_plural = "Conducteurs"
        constraints = [
            models.UniqueConstraint(
                fields=["numero_permis", "mention_permis"],
                name="unique_numero_mention_permis",
            )
        ]

    def __str__(self):
        return f"{self.prenom} {self.nom} (Permis {self.numero_permis}, {self.mention_permis})"


class Vehicule(models.Model):
    marque = models.CharField(max_length=100)
    modele = models.CharField(max_length=100)
    plaque = models.CharField(max_length=30)
    type_vehicule = models.CharField(max_length=20, choices=TypeVehicule.choices)

    def __str__(self):
        return f"{self.marque} {self.modele} - {self.plaque}"


class Dossier(models.Model):
    """Dossier de confiscation de permis — pièce centrale du workflow (Modules 1-7)."""

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    numero = models.CharField(max_length=30, unique=True, blank=True)

    # Saisie initiale (Module 1)
    agent_saisisseur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="dossiers_saisis"
    )
    date_incident = models.DateTimeField()
    ville = models.CharField(max_length=100)
    quartier = models.CharField(max_length=100, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    type_incident = models.CharField(max_length=20, choices=TypeIncident.choices)

    vehicule = models.ForeignKey(Vehicule, on_delete=models.PROTECT, related_name="dossiers")
    conducteur = models.ForeignKey(Conducteur, on_delete=models.PROTECT, related_name="dossiers")

    vitesse_excessive = models.BooleanField(default=False)
    alcool = models.BooleanField(default=False)
    stupefiants = models.BooleanField(default=False)
    feu_rouge = models.BooleanField(default=False)
    autres_circonstances = models.TextField(blank=True)

    nombre_blesses = models.PositiveIntegerField(default=0)
    nombre_deces = models.PositiveIntegerField(default=0)
    gravite = models.CharField(max_length=50, blank=True)

    date_saisie = models.DateTimeField(auto_now_add=True)
    date_derniere_modif = models.DateTimeField(auto_now=True)
    modification_validee_hierarchie = models.BooleanField(default=True)

    statut = models.CharField(max_length=25, choices=StatutDossier.choices, default=StatutDossier.SAISI)

    # Vérification (Module 2)
    verificateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="dossiers_verifies",
    )
    date_verification = models.DateTimeField(null=True, blank=True)
    motif_rejet = models.TextField(blank=True)

    class Meta:
        verbose_name = "Dossier de confiscation"
        verbose_name_plural = "Dossiers de confiscation"
        ordering = ["-date_saisie"]

    def save(self, *args, **kwargs):
        if not self.numero:
            self.numero = generer_numero_dossier()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.numero} - {self.conducteur}"

    def get_absolute_url(self):
        return reverse("dossiers:detail", kwargs={"pk": self.pk})

    @property
    def modifiable_librement(self):
        """Un dossier ne peut être modifié librement que dans les 24h après saisie."""
        from django.utils import timezone

        return (timezone.now() - self.date_saisie).total_seconds() < 24 * 3600

    @property
    def en_retard(self):
        """Dossier en retard : plus de 30 jours sans décision."""
        from django.utils import timezone

        if self.statut in (StatutDossier.DECIDE, StatutDossier.CLOTURE, StatutDossier.REJETE):
            return False
        return (timezone.now() - self.date_saisie).days > 30


def chemin_upload_piece(instance, filename):
    return f"dossiers/{instance.dossier.numero}/{instance.type_piece}_{filename}"


class TypePiece(models.TextChoices):
    PERMIS = "PERMIS", "Photo du permis confisqué"
    CARTE_GRISE = "CARTE_GRISE", "Photo de la carte grise"
    PV_ACCIDENT = "PV_ACCIDENT", "PV d'accident"
    CONSTAT_MEDICAL = "CONSTAT_MEDICAL", "Constatations médicales"
    AUTRE = "AUTRE", "Autre pièce"


class PieceJointe(models.Model):
    dossier = models.ForeignKey(Dossier, on_delete=models.CASCADE, related_name="pieces")
    type_piece = models.CharField(max_length=20, choices=TypePiece.choices)
    fichier = models.FileField(upload_to=chemin_upload_piece)
    uploade_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Pièce jointe"
        verbose_name_plural = "Pièces jointes"

    def __str__(self):
        return f"{self.get_type_piece_display()} - {self.dossier.numero}"


class HistoriqueDossier(models.Model):
    """Traçabilité : qui a fait quoi, quand, sur chaque dossier."""

    dossier = models.ForeignKey(Dossier, on_delete=models.CASCADE, related_name="historique")
    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=255)
    date_action = models.DateTimeField(auto_now_add=True)
    details = models.TextField(blank=True)

    class Meta:
        verbose_name = "Historique du dossier"
        verbose_name_plural = "Historiques des dossiers"
        ordering = ["-date_action"]

    def __str__(self):
        return f"{self.dossier.numero} - {self.action} ({self.date_action:%d/%m/%Y %H:%M})"
