# Exporteur d'opérations bancaires BoursoBank

Script python permettant d'exporter les opérations d'un compte BoursoBank dans un fichier `csv`.

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
BOURSOBANK_CLIENT_ID = '12345678'
BOURSOBANK_PASSWORD = '87654321'
BOURSOBANK_ACCOUNT_ID = '111c22222b55555a11111c66666b8888'
EXPORT_PATH = '~/exports_boursobank'
LOG_PATH = '/var/logs/boursobank-expoorter'
```

### Explication des variables d'environnement

-   **BOURSOBANK_CLIENT_ID** : Identifiant client BoursoBank. Utilisé pour la connexion à l'espace client.
-   **BOURSOBANK_PASSWORD** : Mot de passe utilisé pour la connexion à l'espace client.
-   **BOURSOBANK_ACCOUNT_ID** : Identifiant du compte qui contient les opérations à exporter.
-   **EXPORT_PATH** : Chemin vers le dossier qui contiendra les exports `csv`. Cela peut être un chemin absolu ou relatif. Ne pas inclure le nom du fichier, car celui-ci sera généré automatiquement en fonction des paramètres d'export spécifiés en argument.
    Si le chemin est vide (ou la variable non définie), alors les exports seront enregistrés dans le répertoire courant.
-   **LOG_PATH** : Chemin vers le dossier qui contiendra le fichier de logs `boursobank_exporter.log`.
    Si le chemin est vide (ou la variable non définie), alors le fichier de log sera créé dans le répertoire courant.

> [!Important]
> L'identifiant du compte pour la variable `BOURSOBANK_ACCOUNT_ID` n'est le numéro affiché sur l'espace client BoursoBank.
> Il s'agit d'un autre identifiant, qui peut être récupéré dans l'URL de la page du compte.
>
> Par exemple : https://clients.boursobank.com/compte/cav/111c22222b55555a11111c66666b8888/mouvements
>
> `111c22222b55555a11111c66666b8888` sera donc l'identifiant du compte à spécifier.

## Utilisation

Afin de réaliser un export en ligne de commande, le script `boursobank_exporter_cli.py` doit être exécuté avec au moins les deux arguments suivants :

-   `--from FROM_DATE` ou `-f FROM_DATE` : date au format `DD/MM/YYY` représentant la date de début des opérations à exporter.
-   `--to TO_DATE` ou `-t TO_DATE` : date au format `DD/MM/YYY` représentant la date de fin des opérations à exporter.

Les autres arguments peuvent être omis s'ils sont déjà présents dans le fichier d'environnement `.env`.

### Liste complète des arguments

La liste complète des arguments peut être obtenue en exécutant le script avec l'argument `-h` :

```
python .\src\boursobank_exporter_cli.py -h
```

Qui retournera ceci :

```
usage: boursobank_exporter_cli.py [-h] [--client-id CLIENT_ID] [--password PASSWORD] [--account-id ACCOUNT_ID] [--export-directory EXPORT_PATH]
                                  [--no-logs] [--from FROM_DATE] [--to TO_DATE]

options:
  -h, --help            show this help message and exit
  --client-id CLIENT_ID, -u CLIENT_ID
                        Numéro client BoursoBank
  --password PASSWORD, -p PASSWORD
                        Mot de passe BoursoBank
  --account-id ACCOUNT_ID, -a ACCOUNT_ID
                        Numéro de compte BoursoBank
  --export-directory EXPORT_PATH, -d EXPORT_PATH
                        Chemin vers le dossier dans lequel seront enregistrées les extractions
  --no-logs             Empêche le script d'enregistrer les logs sur le disque
  --from FROM_DATE, -f FROM_DATE
                        Date de début des transactions pour l'export
  --to TO_DATE, -t TO_DATE
                        Date de fin des transactions pour l'export
```

## Correspondance entre les arguments et les variables d'environnement

| Argument           | Variable              | Obligatoire ? |
| ------------------ | --------------------- | ------------- |
| --client-id        | BOURSOBANK_CLIENT_ID  | X             |
| --password         | BOURSOBANK_PASSWORD   | X             |
| --account-id       | BOURSOBANK_ACCOUNT_ID | X             |
| --export-directory | EXPORT_PATH           |               |
| --no-logs          | LOG_PATH              |               |
| --from             |                       | X             |
| --to               |                       | X             |

> [!NOTE]  
> Comme indiqué plus haut, les arguments obligatoires peuvent être omis si la variable d'environnement à laquelle ils sont associés est spécifiée.
