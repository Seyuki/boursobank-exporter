import os, re, io, logging, requests, csv, sqlite3
from bs4 import BeautifulSoup
from pathlib import Path

logger: logging.Logger = logging.getLogger()

class BoursoBankExporter:
    """Représente une instance d'exporteur BoursoBank.
    """
    def __create_session(self) -> None:
        """Création de la session, afin de récupérer les cookies et token nécessaires à la connexion et à l'export.
        """
        # Récupération du cookie "__brs_mit"
        logger.debug("Récupération du cookie '__brs_mit'")
        content: str = self.__http_session.get("https://clients.boursobank.com/connexion/").text
        __brs_mit: str = content[content.find("__brs_mit=")+10:content.find(";")]
        self.__http_session.cookies.set("__brs_mit", __brs_mit, domain=".clients.boursobank.com")

        # Récupération du "token"
        logger.debug("Récupération du token de formulaire")
        response: requests.Response = self.__http_session.get("https://clients.boursobank.com/connexion/")
        soup: BeautifulSoup = BeautifulSoup(response.text, "html.parser")
        self.__form_token = soup.find("input", {"name": "form[_token]"})["value"]

    
    def __load_digits_mapping(self) -> None:
        """Récupère le mapping entre les chiffres du mot de passe avec les codes du clavier virtuel aléatoire.
        """
        logger.debug("Récupération de la correspondance entre les chiffres du mot de passe avec les touches du clavier virtuel")
        response: requests.Response = self.__http_session.get("https://clients.boursobank.com/connexion/clavier-virtuel?_hinclude=1")
        soup: BeautifulSoup = BeautifulSoup(response.text, "html.parser")
        
        for button in soup.find_all("button", class_="sasmap__key"):
            img: str = button.find("img", class_="sasmap__img")["src"]
            digit: int = self.__IMG_LEN_TO_DIGIT[len(img)]
            self.__digits_mapping[str(digit)] = button["data-matrix-key"]

        # Récupération du Random Matrix Challenge
        logger.debug("Récupération du challenge aléatoire pour la matrice du clavier virtuelle")
        self.__matrix_random_challenge: str = re.search(r"\$\(\"\[data-matrix-random-challenge\]\"\)\.val\(\"([^\"]*)\"\)", response.text).group(1)


    def __init__(self) -> None:
        """Constructeur de la classe BoursoBankExporter.
        """
        logger.info("Initialisation de l'exporteur")
        self.__IMG_LEN_TO_DIGIT: dict[int, int] = {
                419  : 0,
                259  : 1,
                1131 : 2,
                979  : 3,
                763  : 4,
                839  : 5,
                1075 : 6,
                1359 : 7,
                1023 : 8,
                1047 : 9,
        }
        self.__http_session: requests.Session = requests.Session()
        self.__form_token: str = None
        self.__matrix_random_challenge: str = None
        self.__digits_mapping: dict[str, str] = {}
        self.__is_logged: bool = False

        # Création de la session
        self.__create_session()

        # Mapping des digits pour le clavier du mot de passe
        self.__load_digits_mapping()

    
    def __get_encoded_password(self, password: str) -> str:
        """Transforme le mot de passe en chaine de caractère encodée, en fonction du clavier virtuel aléatoire.

        Args:
            password (str): Mot de passe en clair.

        Returns:
            str: Mot de passe encodé.
        """
        logger.debug("Transformation du mot de passe avec la matrice aléatoire du clavier virtuelle")

        encoded_password_arr: list[str] = []
        for c in password:
            encoded_password_arr.append(self.__digits_mapping[c])

        return "|".join(encoded_password_arr)

    
    def login(self, client: str, password: str) -> None:
        """Connexion à BoursoBank avec les identifiants spécifiés.

        Args:
            client (str): Identifiant client.
            password (str): Mot de passe.
        """
        logger.info("Connexion à BoursoBank")

        # Récupération du mot de passe encodé avec le clavier aléatoire
        encoded_password: str = self.__get_encoded_password(password)
        
        # Création de la requête de login
        fields: tuple[str, tuple[str, str]] = (
            ('form[clientNumber]', (None,  client)),
            ('form[password]', (None,  encoded_password)),
            ('form[ajx]', (None,  1)),
            ('form[platformAuthenticatorAvailable]', (None,  "-1")),
            ('form[passwordAck]', (None,  "{}")),
            ('form[fakePassword]', (None,  "••••••••")),
            ('form[_token]', (None,  self.__form_token)),
            ('form[matrixRandomChallenge]', (None,  self.__matrix_random_challenge))
        )

        # Connexion
        response: requests.Response = self.__http_session.post("https://clients.boursobank.com/connexion/saisie-mot-de-passe", files=fields)
        
        if response.status_code == 200:
            self.__is_logged = True


    def export_data(self, account_id: str, from_date: str, to_date: str) -> tuple[bytes, str, str]:
        """Retourne les transactions entre les dates spécifiées, pour le compte spécifié.

        Args:
            account_id (str): Numéro de compte à exporter.
            from_date (str): Date de début des transactions (DD/MM/YYYY).
            to_date (str): Date de fin des transactions (DD/MM/YYYY).

        Returns:
            bytes: Export des transactions au format binaire.
        """
        logger.info(f"Export des données du {from_date} au {to_date} pour le compte {account_id}")

        # Vérification de la connexion
        if not self.__is_logged:
            logger.error("Veuillez d'abord vous connecter")
            return None

        # Vérification du format des dates
        pattern: re.Pattern = re.compile(r"^\d{2}\/\d{2}\/\d{4}$")
        if not pattern.match(from_date) or not pattern.match(to_date):
            logger.error("Les dates doivent être au format DD/MM/YYYY")
            return None

        # Requête
        params: dict[str, str] = {
            "movementSearch[selectedAccounts][]": account_id,
            "movementSearch[fromDate]": from_date,
            "movementSearch[toDate]": to_date,
            "movementSearch[format]": "CSV",
            "movementSearch[filteredBy]": "filteredByCategory",
            "movementSearch[catergory]": "",
            "movementSearch[operationTypes]": "",
            "movementSearch[myBudgetPage]": 1,
            "movementSearch[submit]": ""
        }

        response: requests.Response = self.__http_session.get("https://clients.boursobank.com/budget/exporter-mouvements", params=params)
        return response.content, from_date, to_date
    

    def write_to_csv(self, folder: str, account_id: str, data: bytes, from_date: str, to_date: str) -> str:
        """Enregistre l'export binaire dans un fichier csv sur le disque, dans le dossier spécifié.

        Args:
            folder (str): Chemin vers le dossier dans lequel le fichier csv sera créé.
            account_id (str): Identifiant du compte BoursoBank.
            data (bytes): Export des transactions au format binaire.
            from_date (str): Date de début des transactions (DD/MM/YYYY).
            to_date (str): Date de fin des transactions (DD/MM/YYYY).

        Returns:
            str: Chemin vers le fichier csv créé.
        """
        # Création du dossier d'export s'il n'existe pas
        Path(folder).mkdir(parents=True, exist_ok=True)

        # Nom de l'export
        export_file: str = account_id
        export_file += "_"
        export_file += from_date[6:] + from_date[3:5] + from_date[0:2]
        export_file += "-"
        export_file += to_date[6:] + to_date[3:5] + to_date[0:2]
        export_file = os.path.join(folder, f"{export_file}.csv")

        # Ecriture du fichier
        with open(export_file, "wb") as f:
            f.write(data)

        logger.info(f"Fichier enregistré : {export_file}")

        return export_file
    

    def __init_db(self, client_id: str, db_path: str) -> list[str]:
        """Crée la base de donnée et la table si elles n'existent pas déjà.

        Args:
            client_id (str): Identifiant client, pour nommer la table.
            db_path (str): Chemin vers la base de données.

        Returns:
            list[str]: Liste complète des champs de la table.
        """
        logger.debug("Initialisation de la base de données")

        # Création des dossiers s'ils n'existent pas
        parent_path: str = os.path.dirname(db_path)
        if parent_path != "":
            Path(parent_path).mkdir(parents=True, exist_ok=True)

        # Champs de la table
        fields: list[tuple[str, str, bool]] = [
            ("dateOp", "TEXT"),
            ("dateVal", "TEXT"),
            ("label", "TEXT"),
            ("category", "TEXT"),
            ("categoryParent", "TEXT"),
            ("supplierFound", "TEXT"),
            ("amount", "REAL"),
            ("comment", "TEXT"),
            ("accountNum", "TEXT"),
            ("accountLabel", "TEXT"),
            ("accountbalance", "REAL")
        ]
        fields_for_create: list[str] = []
        fields_for_query: list[str] = []
        for field in fields:
            fields_for_create.append(f"{field[0]} {field[1]}")
            fields_for_query.append(field[0])

        # Création de la table si elle n'existe pas
        req: str = f"CREATE TABLE IF NOT EXISTS client_{client_id} ({",".join(fields_for_create)});"
        con: sqlite3.Connection = sqlite3.connect(db_path)
        cur: sqlite3.Cursor = con.cursor()
        cur.execute(req)
        con.commit()
        con.close()

        return fields_for_query
    

    def __remove_same_period(self, client_id: str, from_date: str, to_date: str, db_path: str) -> None:
        """Supprime les opérations sur la même période que celle demandée, afin d'éviter d'avoir des opérations en doublon.

        Args:
            client_id (str): Identifiant client, pour identifier la table.
            from_date (str): Date de début des transactions (DD/MM/YYYY).
            to_date (str): Date de fin des transactions (DD/MM/YYYY).
            db_path (str): Chemin vers la base de données.
        """
        logger.info("Suppression des opérations sur la même période pour éviter les doublons")

        from_date = from_date[6:] + "-" + from_date[3:5] + "-" + from_date[0:2]
        to_date = to_date[6:] + "-" + to_date[3:5] + "-" + to_date[0:2]

        con: sqlite3.Connection = sqlite3.connect(db_path)
        cur: sqlite3.Cursor = con.cursor()
        cur.execute(f"DELETE FROM client_{client_id} WHERE dateOp >= '{from_date}' AND dateOp <= '{to_date}';")
        con.commit()
        con.close()


    def write_to_sqlite(self, client_id: str, data: bytes, from_date: str, to_date: str, db_path: str = "boursobank_exports.db") -> None:
        """Insert les opérations exportées dans une base de données SQLite.

        Args:
            client_id (str): Identifiant client.
            data (bytes): Export des transactions au format binaire.
            from_date (str): Date de début des transactions (DD/MM/YYYY).
            to_date (str): Date de fin des transactions (DD/MM/YYYY).
            db_path (str, optional): Chemin vers la base de données SQLite. Defaults to "boursobank_exports.db".
        """
        # Base de données SQLite
        if db_path is None or db_path == "":
            db_path = "boursobank_exports.db"

        # Initialisation de la DB
        fields = self.__init_db(client_id, db_path)

        # Suppression des anciennes opérations sur la même période
        self.__remove_same_period(client_id, from_date, to_date, db_path)

        # Décodage des données
        io_data: io.StringIO = io.StringIO(data.decode("utf-8-sig"))
        dict_reader: csv.DictReader = csv.DictReader(io_data, delimiter=";")

        rows: list[dict[str, any]] = [] 
        for row in dict_reader:
            if row["amount"] is not None and row["amount"] != "":
                row["amount"] = float(row["amount"].replace(" ", "").replace(",", "."))
            else:
                row["amount"] = None
            if row["accountbalance"] is not None and row["accountbalance"] != "":
                row["accountbalance"] = float(row["accountbalance"].replace(" ", "").replace(",", "."))
            else:
                row["accountbalance"] = None
            rows.append(row)
        
        # Insertion des données
        logger.info(f"Insertion des données dans la base SQLite, table 'client_{client_id}'")
        fields = [f":{field}" for field in fields]
        req: str = f"INSERT INTO client_{client_id} VALUES ({",".join(fields)});"

        con: sqlite3.Connection = sqlite3.connect(db_path)
        cur: sqlite3.Cursor = con.cursor()
        cur.executemany(req, tuple(rows))
        con.commit()
        con.close()
