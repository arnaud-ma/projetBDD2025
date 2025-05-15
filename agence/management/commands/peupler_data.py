import django
from django.core.management import BaseCommand
from django.db import transaction
from faker import Faker

import agence.models as ag

TZINFO = django.utils.timezone.get_current_timezone()


class Command(BaseCommand):
    help = "Peuple la base de données avec des données fictives"

    def add_arguments(self, parser):
        parser.add_argument(
            "--n",
            type=int,
            default=100,
            help="Nombre d'entrées à générer",
        )
        parser.add_argument(
            "--locale",
            type=str,
            default="fr_FR",
            help="Locale pour Faker (ex: fr_FR, en_US)",
        )
        parser.add_argument(
            "--seed",
            type=int,
            default=None,
            help="Graine pour Faker. Permet de reproduire les mêmes données à chaque exécution.",
        )

    def handle(self, *args, **options):
        N, locale, seed = options["n"], options["locale"], options["seed"]
        fake = Faker(locale)
        if seed is not None:
            fake.seed_instance(seed)

        communes = [
            ag.Commune(
                code_insee=fake.unique.postcode(),
                nom=fake.unique.city(),
                code_postal=fake.unique.postcode(),
            )
            for _ in range(N)
        ]

        voies = [
            ag.Voie(nom=fake.unique.street_name(), commune=fake.random.choice(communes))
            for _ in range(N)
        ]

        adresses = []
        for _ in range(N):
            adresse = ag.Adresse(
                id_ban=fake.unique.uuid4(),
                voie=fake.random.choice(voies),
                numero=fake.building_number(),
                # complement=fake.secondary_address() # TODO
                longitude=float(fake.longitude()),
                latitude=float(fake.latitude()),
            )
            adresse.label = adresse.create_label()
            adresses.append(adresse)

        nb_agences = fake.random.randint(1, N // 10)
        agences = [
            ag.Agence(
                nom=fake.company(),
                adresse=fake.random.choice(adresses),
                telephone=fake.phone_number(),
            )
            for _ in range(nb_agences)
        ]

        infos_biens = [
            ag.InfosBien(
                nb_chambres=fake.random_int(min=1, max=5),
                nb_salles_bain=fake.random_int(min=1, max=3),
                nb_garages=fake.random_int(min=0, max=2),
                nb_cuisines=fake.random_int(min=1, max=2),
                nb_wc=fake.random_int(min=1, max=3),
                surface_habitable=fake.random_int(min=30, max=200),
                surface_terrain=fake.random_int(min=50, max=1000),
                lieu=fake.random.choice(adresses),
                description=fake.paragraph(nb_sentences=3, variable_nb_sentences=True),
                prix=fake.random.randint(100000, 1000000) + round(fake.random.uniform(0, 1), 2),
            )
            for _ in range(N)
        ]

        utilisateurs = [
            ag.Utilisateur(
                nom=fake.last_name(),
                prenom=fake.first_name(),
                telephone=fake.phone_number(),
                email=fake.unique.email(),
            )
            for _ in range(N)
        ]

        nb_vendeurs = fake.random.randint(1, N // 2)
        vendeurs = [
            ag.Vendeur(utilisateur=u) for u in fake.random.sample(utilisateurs, k=nb_vendeurs)
        ]

        nb_agents = fake.random.randint(N // 4, N // 2)
        agents = [
            ag.Agent(
                utilisateur=u,
                agence=fake.random.choice(agences),
            )
            for u in fake.random.sample(utilisateurs, k=nb_agents)
        ]

        etats = [etat.value for etat in ag.Bien.Etat]
        biens = [
            ag.Bien(
                etat=fake.random.choice(etats),
                infos_bien=fake.random.choice(infos_biens),
                agent=fake.random.choice(agents),
                vendeur=fake.random.choice(vendeurs),
            )
            for _ in range(N)
        ]

        nb_acheteurs = fake.random.randint(N // 4, N)
        acheteurs = [
            ag.Acheteur(
                utilisateur=u,
                critere_recherche=fake.random.choice(infos_biens),
            )
            for u in fake.random.sample(utilisateurs, k=nb_acheteurs)
        ]

        etapes = [etape.value for etape in ag.FaitAchat.EtapeAchat]
        fait_achats = [
            ag.FaitAchat(
                bien=fake.random.choice(biens),
                acheteur=fake.random.choice(acheteurs),
                etape_achat=fake.random.choice(etapes),
            )
            for _ in range(N)
        ]

        rdvs = [
            ag.RendezVous(
                fait_achat=fake.random.choice(fait_achats),
                objet=fake.sentence(nb_words=6, variable_nb_words=True),
                commentaire=fake.paragraph(nb_sentences=10, variable_nb_sentences=True),
                date=fake.date_time_this_year(tzinfo=TZINFO),
                lieu=fake.random.choice(adresses),
            )
            for _ in range(N)
        ]

        messages = [
            ag.Message(
                fait_achat=fake.random.choice(fait_achats),
                contenu=fake.paragraph(nb_sentences=20, variable_nb_sentences=True),
                auteur=fake.random.choice(utilisateurs),
                date=fake.date_time_this_year(tzinfo=TZINFO),
            )
            for _ in range(N)
        ]

        with transaction.atomic():
            ag.Commune.objects.bulk_create(communes)
            ag.Voie.objects.bulk_create(voies)
            ag.Adresse.objects.bulk_create(adresses)
            ag.Agence.objects.bulk_create(agences)
            ag.InfosBien.objects.bulk_create(infos_biens)
            ag.Utilisateur.objects.bulk_create(utilisateurs)
            ag.Vendeur.objects.bulk_create(vendeurs)
            ag.Agent.objects.bulk_create(agents)
            ag.Bien.objects.bulk_create(biens)
            ag.Acheteur.objects.bulk_create(acheteurs)
            ag.FaitAchat.objects.bulk_create(fait_achats)
            ag.RendezVous.objects.bulk_create(rdvs)
            ag.Message.objects.bulk_create(messages)

        self.stdout.write(
            self.style.SUCCESS(f"Successfully populated the database with {N} records.")
        )
