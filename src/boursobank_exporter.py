import os, re, logging, requests
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
        logger.info(f"Export des données du {from_date} au {to_date}")

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
    

    def save_data(self, folder: str, data: bytes, from_date: str, to_date: str) -> str:
        """Enregistre l'export binaire dans un fichier csv sur le disque, dans le dossier spécifié.

        Args:
            folder (str): Chemin vers le dossier dans lequel le fichier csv sera créé.
            data (bytes): Export des transactions au format binaire.

        Returns:
            str: Chemin vers le fichier csv créé.
        """
        # Création du dossier d'export s'il n'existe pas
        Path(folder).mkdir(parents=True, exist_ok=True)

        # Nom de l'export
        export_file: str = "boursobank_export_"
        export_file += from_date[6:] + from_date[3:5] + from_date[0:2]
        export_file += "-"
        export_file += to_date[6:] + to_date[3:5] + to_date[0:2]
        export_file = os.path.join(folder, f"{export_file}.csv")

        # Ecriture du fichier
        with open(export_file, "wb") as f:
            f.write(data)

        logger.info(f"Fichier enregistré : {export_file}")

        return export_file
