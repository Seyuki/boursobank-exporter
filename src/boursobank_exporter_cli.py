import os, logging, argparse, re
from pathlib import Path
from dotenv import load_dotenv
from boursobank_exporter import BoursoBankExporter

# Chargement des variables d'environnement
load_dotenv()

# Arguments
parser = argparse.ArgumentParser()
parser.add_argument('--client-id',
                    '-u',
                    dest='client_id',
                    default=os.getenv("BOURSOBANK_CLIENT_ID"),
                    help="Numéro client BoursoBank")
parser.add_argument('--password',
                    '-p',
                    dest='password',
                    default=os.getenv("BOURSOBANK_PASSWORD"),
                    help="Mot de passe BoursoBank")
parser.add_argument('--accounts-id',
                    '-a',
                    dest='accounts_id',
                    default=os.getenv("BOURSOBANK_ACCOUNTS_ID"),
                    help="Numéros de comptes BoursoBank, séparés par des virgules")
parser.add_argument('--export-directory',
                    '-d',
                    dest='export_path',
                    default=os.getenv("EXPORT_PATH"),
                    help="Chemin vers le dossier dans lequel seront enregistrées les extractions")
parser.add_argument('--output',
                    '-o',
                    dest='output_type',
                    default=os.getenv("OUTPUT_TYPE"),
                    choices={"csv", "sqlite", "both"},
                    help="Type d'export souhaité, peut être 'csv', 'sqlite' ou 'both' pour les deux")
parser.add_argument('--sqlite-db',
                    '-db',
                    dest='db_path',
                    default=os.getenv("SQLITE_DB_PATH"),
                    help="Chemin vers la base de données SQLite")
parser.add_argument('--no-logs',
                    dest='no_logs',
                    action='store_true',
                    help="Empêche le script d'enregistrer les logs sur le disque")
parser.add_argument('--from',
                    '-f',
                    dest='from_date',
                    default=None,
                    help="Date de début des transactions pour l'export")
parser.add_argument('--to',
                    '-t',
                    dest='to_date',
                    default=None,
                    help="Date de fin des transactions pour l'export")
args = parser.parse_args()

# Logger
log_path: str = os.getenv("LOG_PATH") if os.getenv("LOG_PATH") is not None else ""
logger: logging.Logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
lf: logging.Formatter = logging.Formatter("[%(asctime)s][%(levelname)s](%(filename)s:%(lineno)s) %(message)s")

ch: logging.StreamHandler = logging.StreamHandler()
ch.setFormatter(lf)
ch.setLevel(logging.INFO)
logger.addHandler(ch)

if not args.no_logs:
    Path(log_path).mkdir(parents=True, exist_ok=True)
    fh: logging.FileHandler = logging.FileHandler(os.path.join(log_path, "boursobank_exporter.log"), encoding="utf-8")
    fh.setFormatter(lf)
    fh.setLevel(logging.INFO)
    logger.addHandler(fh)


def validate_args() -> bool:
    """Valide les arguments spécifiés.
    La majorité des arguments peuvent être remplacés par une variable d'environnement (fichier .env).

    Returns:
        bool: Indique si les arguments sont valides ou non.
    """
    if args.export_path is None:
        args.export_path = ""
    if args.output_type is None or args.output_type == "":
        args.output_type = "csv"

    if args.client_id is None:
        logger.error("L'identifiant client doit être spécifié.")
        return False
    elif not re.match(r"^\d+$", args.client_id):
        logger.error("L'identifiant client ne doit contenir que des chiffres.")
        return False
    elif args.password is None:
        logger.error("Le mot de passe doit être spécifié.")
        return False
    elif not re.match(r"^\d+$", args.password):
        logger.error("Le mot de passe ne doit contenir que des chiffres.")
        return False
    elif args.accounts_id is None:
        logger.error("Au moins un numéro de compte doit être spécifié.")
        return False
    elif not re.match(r"^[\da-zA-Z,]+$", args.accounts_id):
        logger.error("Les numéros de comptes ne doivent contenir que des chiffres et des lettres.")
        return False
    elif args.output_type.lower() not in ["csv", "sqlite", "both"]:
        logger.error("Le type d'export doit être 'csv', 'sqlite' ou 'both'.")
        return False
    elif args.from_date is None:
        logger.error("La date de début doit être spécifiée.")
        return False
    elif not re.match(r"^\d{2}\/\d{2}\/\d{4}$", args.from_date):
        logger.error("La date de début doit être au format DD/MM/YYYY.")
        return False
    elif args.to_date is None:
        logger.error("La date de fin doit être spécifiée.")
        return False
    elif not re.match(r"^\d{2}\/\d{2}\/\d{4}$", args.to_date):
        logger.error("La date de fin doit être au format DD/MM/YYYY.")
        return False
    
    return True


def main() -> None:
    """Fonction principale lors de l'exécution par ligne de commande
    """
    # Vérification des arguments
    if not validate_args():
        return
    
    # Liste des comptes
    id_comptes: list[str] = args.accounts_id.split(",")

    # Connexion
    bb_exporter: BoursoBankExporter = BoursoBankExporter()
    bb_exporter.login(args.client_id, args.password)

    # Export des opérations
    for id_compte in id_comptes:
        export: tuple[bytes, str, str] = bb_exporter.export_data(id_compte, args.from_date, args.to_date)

        if args.output_type.lower() in ["csv", "both"]:
            bb_exporter.write_to_csv(args.export_path, id_compte, export[0], export[1], export[2])
        if args.output_type.lower() in ["sqlite", "both"]:
            bb_exporter.write_to_sqlite(args.client_id, export[0], export[1], export[2], args.db_path)


if __name__ == "__main__":
    main()
