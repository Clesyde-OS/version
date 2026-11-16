# Clesyde/Lyvo : validation DEV et promotion BETA, 16 novembre 2026

Résultat : PASS pour la qualification de la seule BOX DEV ARM64. Les mêmes images signées sont proposées pour DEV et BETA, sans reconstruction ni écrasement de tag historique. STABLE reste identique.

| Composant | Version fonctionnelle | Paquet immuable |
| --- | --- | --- |
| Core | 2026.11.1 | 2026.11.1.4 |
| Frontend | 20261028.5 | wheel 3clesyde3 |
| Supervisor | 2026.11.0 | 2026.11.0.6 |

Les images natives ARM64/AMD64 ont passé leurs contrôles, démarrages et redémarrages HTTP. Core : 11 101 tests passés, 1 ignoré, 176 snapshots, 42 tests SDK, 6 scénarios de cycle de vie et tous les contrôles de qualité/Pylint. Frontend : compilation unique, mêmes octets dans les deux images, 19 scénarios Store/Marketplace. Sept signatures de construction/source et tous les blobs/digests OCI ont été vérifiés. Les PR amont restent distinctes de cette qualification ; leurs attentes OEM, chemins volontairement désactivés et services externes ne constituent pas une CI amont globalement verte.

Sur la box DEV : les deux images, commits et digests correspondent aux artefacts signés ; 15513 fichiers du Frontend, SDK et composant Lyvo ont été comparés. Cloud chargé, six fichiers d'identité/certificats inchangés, URL externe persistée et active conforme à l'adresse attribuée, contenu Frontend exact reçu en HTTPS avec validation TLS. Redémarrage Core et redémarrage réel de la box observés, mêmes artefacts après redémarrage, SQLite intègre au schéma 53 sans migration effectuée.

MQTT local : connexion, SUBACK, PUBACK et écho QoS1 non conservé sur un sujet de diagnostic unique passent. Cloud : deux lectures du shadow config traitées par le client existant, aucun desired modifié ; six séries collectées par minute et 1 lot(s) confirmé(s) après publication MQTT. Aucun échec de lecture/publication ; file SQLite vide après livraison ; niveaux de journalisation rétablis. Douze cas isolés sur le matériel ARM64 passent (lecteurs, horloge, persistance/reprise, QoS1, profils, callback de certificat attendu), avec transport simulé et sans rotation volontaire de certificat.

Store : les seize extensions installées restent rattachées, versions et préférences de mise à jour inchangées. UI réelle vérifiée ; Marketplace distinct du Store Clesyde, avertissements/consentement conservés et traductions corrigées. Les guides techniques officiels sont rétablis. Le SDK 0.1.21.dev2, SniTun 0.47.0, port 8123 et endpoint AWS Lyvo de production restent conservés.

Sauvegarde complète fraîche 36bd3682 : 3 012 fichiers restaurés à l'identique hors box, SQLite intègre et données Cloud présentes. Runtime précédent et Frontend2 conservés, retour arrière préparé ; aucun rollback réel n'a été appliqué pour ce test. Les clés, tokens, certificats de box, noms de tunnel et sauvegardes restent privés dans Work.

Limites : AMD64 est validé nativement en CI, sans box AMD64 physique disponible. Les essais KNX/Z-Wave des suites et imports natifs ne valent pas une validation complète sur chaque matériel radio. L'erreur cloudflared et les préférences d'extensions relevées avant essai restent des éléments de l'état initial. Aucune box cliente/showroom n'a été connectée ou déployée. La promotion du catalogue ne force pas le retour arrière d'une box déjà mise à jour.

Les références complètes et preuves sont dans manifest.json, signatures/ et proofs/. La phase DEV a été activée par PR9 ; cette phase ne modifie que les trois valeurs BETA après validation, DEV et STABLE restant inchangés.
