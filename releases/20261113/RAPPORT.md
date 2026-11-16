# Livraison Clesyde/Lyvo : ouverture DEV, 16 novembre 2026

Les quatre images natives Core/Supervisor sont construites, testées, signées et publiées sous de nouveaux tags immuables. Ce changement ouvre uniquement DEV pour la validation de la box autorisée. BETA et STABLE restent identiques octet pour octet. Aucune image n'est reconstruite lors de la publication.

| Composant | Base fonctionnelle | Paquet immuable |
| --- | --- | --- |
| Core | 2026.11.1 | 2026.11.1.4 |
| Frontend | 20261028.5 | wheel 3clesyde3 |
| Supervisor | 2026.11.0 | 2026.11.0.6 |

Core : 11 101 tests passés, 1 ignoré, 176 snapshots, 42 tests du SDK, 6 scénarios de démarrage/nettoyage, quatre lots complets Pylint et tous les contrôles de qualité passent. Le Frontend partagé a passé 19 scénarios Store/Marketplace et conserve les avertissements, le consentement et les notices. Les images ARM64 et AMD64 ont passé les démarrages/redémarrages HTTP natifs ; chaque archive, blob OCI, digest et signature a été vérifié. Le même wheel Frontend, SHA256 `578b94541a29aa49eb3c6c7b4226279962fb3d034309113aa26d007f6edc810a`, est utilisé sur les deux architectures.

Les correctifs couvrent les erreurs de provisionnement sans secrets, le cycle de vie Cloud, le rechargement du tunnel, le callback de certificat attendu, l'URL externe persistée, les guides techniques officiels, les icônes, les traductions Marketplace et la visibilité du Store selon le vrai canal. Le SDK reste 0.1.21.dev2, SniTun 0.47.0, le port 8123 et l'API AWS Lyvo de production sont conservés. Marketplace HA et Store Clesyde restent distincts.

La sauvegarde complète du 16 novembre `36bd3682` a été restaurée en isolation : 3012 fichiers identiques, SQLite intègre, schéma 53, identité et données Cloud présentes. Les originaux et le runtime précédent sont conservés en privé hors box. Aucun certificat, clé, token ou configuration privée n'est dans ce dépôt.

La qualification réelle des nouveaux artefacts sur la seule BOX DEV est encore en attente. Le Supervisor installé ignore une version explicite hors mode de développement et utilise la version du catalogue : l'ouverture DEV précède donc normalement l'installation. Aucun mode de sécurité ni contrôle de version n'est contourné. BETA ne sera ouvert qu'après validation de la box. Aucun accès ni déploiement sur une box cliente ou showroom.

La CI native de livraison est verte ; les PR amont conservent des attentes OEM/chemins désactivés et des services externes hors de cette qualification. Ce rapport ne déclare pas la CI amont globalement verte. ARM64 doit encore être validé sur la box ; AMD64 a une validation native CI, sans machine physique disponible. Les tests radio réels restent dépendants du matériel ; les suites KNX/Z-Wave/MQTT et les imports natifs passent.

Les signatures publiques de construction, les digests et les preuves sont dans `manifest.json`, `signatures/` et `proofs/`. Les sauvegardes privées restent dans Work. Les tags historiques 2026.10.4, 2026.11.1 et 2026.11.0 ont été conservés.
