# Exporteur d'opérations bancaires BoursoBank

Script python permettant d'exporter les opérations d'un compte BoursoBank (ou plusieurs) dans un fichier `csv`, une base de données `sqlite`, et/ou une base de données `PostgreSQL`.

## Installation des dépendances

Le script repose sur certains packages python qui peuvent être facilement installés via le fichier `requirements.txt`, avec pip :

```
pip install -r requirements.txt
```

## Configuration

Des informations sont obligatoires au bon fonctionnement du script, notamment l'identifiant client et le mot de passe de connexion à BoursoBank.

Ces informations peuvent être directement passées en argument du script (voir ci-dessous) ou être renseignées dans un fichier d'environnement `.env`.

### Exemple de fichier .env

```
BOURSOBANK_CLIENT_ID   = '12345678'
BOURSOBANK_PASSWORD    = '87654321'
BOURSOBANK_ACCOUNTS_ID = '111c22222b55555a11111c66666b8888'
LOG_PATH               = '/var/logs/boursobank-exporter'
OUTPUT_TYPE            = 'csv,sqlite,postgresql'
EXPORT_PATH            = '~/exports_boursobank'
SQLITE_DB_PATH         = 'exports_boursobank.db'
POSTGRESQL_CONN_STRING = 'postgresql://user:password@localhost:5432/dbname'
```

### Explication des variables d'environnement

-   **BOURSOBANK_CLIENT_ID** : Identifiant client BoursoBank. Utilisé pour la connexion à l'espace client.
-   **BOURSOBANK_PASSWORD** : Mot de passe utilisé pour la connexion à l'espace client.
-   **BOURSOBANK_ACCOUNTS_ID** : Identifiant des comptes qui contiennent les opérations à exporter.
    Plusieurs comptes peuvent être spécifiés, dans ce cas, ils doivent être séparés par une virgule.
-   **LOG_PATH** : Chemin vers le dossier qui contiendra le fichier de logs `boursobank_exporter.log`.
    Si le chemin est vide (ou la variable non définie), alors le fichier de log sera créé dans le répertoire courant.
-   **OUTPUT_TYPE** : Type d'exports souhaité. Les valeurs possibles sont : `csv`, `sqlite` ou `postgresql`. Il est également possible de spécifier plusieurs types, en les séparant par une virgule, exemple : `csv,sqlite` pour obtenir des exports en csv et dans la base SQLite.
-   **EXPORT_PATH** : Chemin vers le dossier qui contiendra les exports `csv`. Cela peut être un chemin absolu ou relatif. Ne pas inclure le nom du fichier, car celui-ci sera généré automatiquement en fonction des paramètres d'export spécifiés en argument.
    Si le chemin est vide (ou la variable non définie), alors les exports seront enregistrés dans le répertoire courant.
-   **SQLITE_DB_PATH** : Chemin vers la base de données `sqlite` dans laquelle seront enregistrées les opérations. N'est pris en compte que si le type d'export est `sqlite` ou `both`.
-   **POSTGRESQL_CONN_STRING** : Chaîne de connexion à la base de données PostgreSQL (au format `postgresql://`)

> [!Important]
> L'identifiant du compte pour la variable `BOURSOBANK_ACCOUNTS_ID` n'est pas le numéro affiché sur l'espace client BoursoBank.
> Il s'agit d'un autre identifiant, qui peut être récupéré dans l'URL de la page du compte.
>
> Par exemple : https://clients.boursobank.com/compte/cav/111c22222b55555a11111c66666b8888/mouvements
>
> `111c22222b55555a11111c66666b8888` sera donc l'identifiant du compte à spécifier.

> [!NOTE]  
> Pour un export SQLite ou PostgreSQL, la base contiendra une table dont le nom correspond à `client_[identifiant client]`. Les exports seront ajoutés à cette table sans écraser les précédents.
> Si la période de l'export englobe ou chevauche une période précédemment extraite, les données de cette périodes seront d'abord supprimées afin d'éviter des doublons d'opérations.

## Utilisation

Afin de réaliser un export en ligne de commande, le script `boursobank_exporter_cli.py` peut être exécuté avec les deux arguments suivants :

-   `--from FROM_DATE` ou `-f FROM_DATE` : date au format `DD/MM/YYY` représentant la date de début des opérations à exporter.
-   `--to TO_DATE` ou `-t TO_DATE` : date au format `DD/MM/YYY` représentant la date de fin des opérations à exporter.

Exemple :

```
python .\src\boursobank_exporter_cli.py -f "01/01/2024" -t "31/12/2024"
```

Il est possible de ne pas spécifier les dates, ou de n'en spécifier qu'une des deux. Dans ce cas, la valeur des dates non spécifiées sera automatiquement déduite par le script :

-   **Début (--from)** : Si le chemin vers la base `sqlite` est spécifié (dans le fichier `.env` ou en argument), le script récupérera la date la plus récente des opérations déjà exportées pour le compte en question. Si le chemin vers la base `sqlite` n'est pas spécifié ou aucune donnée n'a été trouvée pour le compte, alors la date correspondra à la date d'il y a 30 jours.
-   **Fin (--to)** : Date du jour.

Les autres arguments obligatoires peuvent être omis s'ils sont déjà présents dans le fichier d'environnement `.env`. (Voir plus bas pour la correspondance entre les arguments et les variables d'environnement.)

### Liste complète des arguments

La liste complète des arguments peut être obtenue en exécutant le script avec l'argument `-h` :

```
python .\src\boursobank_exporter_cli.py -h
```

Qui retournera ceci :

```
usage: boursobank_exporter_cli.py [-h] [--client-id CLIENT_ID] [--password PASSWORD] [--accounts-id ACCOUNTS_ID] [--export-directory EXPORT_PATH]
                                  [--output OUTPUT_TYPE] [--sqlite-db DB_PATH] [--postgresql-uri POSTGRESQL_URI] [--no-logs] [--from FROM_DATE]
                                  [--to TO_DATE]

options:
  -h, --help            show this help message and exit
  --client-id CLIENT_ID, -u CLIENT_ID
                        Numéro client BoursoBank
  --password PASSWORD, -p PASSWORD
                        Mot de passe BoursoBank
  --accounts-id ACCOUNTS_ID, -a ACCOUNTS_ID
                        Numéros de comptes BoursoBank, séparés par des virgules
  --export-directory EXPORT_PATH, -d EXPORT_PATH
                        Chemin vers le dossier dans lequel seront enregistrées les extractions
  --output OUTPUT_TYPE, -o OUTPUT_TYPE
                        Type d'export souhaité, peut être 'csv', 'sqlite' ou 'postgresql', ou une combinaison de ces 3 valeurs séparées par une virgule
  --sqlite-db DB_PATH, -db DB_PATH
                        Chemin vers la base de données SQLite
  --postgresql-uri POSTGRESQL_URI, -pg POSTGRESQL_URI
                        Chaine de connexion à la base PostgreSQL
  --no-logs             Empêche le script d'enregistrer les logs sur le disque
  --from FROM_DATE, -f FROM_DATE
                        Date de début des transactions pour l'export
  --to TO_DATE, -t TO_DATE
                        Date de fin des transactions pour l'export
```

## Correspondance entre les arguments et les variables d'environnement

| Argument           | Variable               | Obligatoire ?            | Par défaut                                                                 |
| ------------------ | ---------------------- | ------------------------ | -------------------------------------------------------------------------- |
| --client-id        | BOURSOBANK_CLIENT_ID   | X                        |                                                                            |
| --password         | BOURSOBANK_PASSWORD    | X                        |                                                                            |
| --accounts-id      | BOURSOBANK_ACCOUNTS_ID | X                        |                                                                            |
| --export-directory | EXPORT_PATH            |                          | .\                                                                         |
| --output           | OUTPUT_TYPE            |                          | csv                                                                        |
| --sqlite-db        | SQLITE_DB_PATH         |                          | .\boursobank_exports.db                                                    |
| --postgresql-uri   | POSTGRESQL_CONN_STRING | X (si export PostgreSQL) |                                                                            |
| --no-logs          |                        |                          | False                                                                      |
| --from             |                        |                          | Date dernière opération exportée pour le compte, ou date d'il y a 30 jours |
| --to               |                        |                          | Date du jour                                                               |

> [!NOTE]  
> Comme indiqué plus haut, les arguments obligatoires peuvent être omis si la variable d'environnement à laquelle ils sont associés est spécifiée.
