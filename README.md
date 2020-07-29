# Mirai-playschool

## Enoncé
L’objectif du TB consiste à fournir un bac à sable de laboratoires pour les cours SLO, AST et EHK qui doit permettre aux étudiants de mieux comprendre la mise en œuvre de cyber-attaques avancées (APT).

Il a fallu dans un premier temps analyser le code source de [Mirai](https://github.com/jgamblin/Mirai-Source-Code).

Il faudra ensuite épurer ce code source afin de créer un thingbot interne. Il faudra que cet environnement soit monitorable et permette d'utiliser de façon sécurisée un botnet.

L'idée finale est de créer un jeu où des points seront accordés à des élèves ayant effectués une action. Les actions permettant d'obtenir des points sont les suivants :
- Scanner le réseau et découvrir un hôte
- Se connecter sûr un hôte découvert
- L'infecter en exécutant un fichier non-désiré
- Effectuer une attaque sur une cible

Vous retrouverez plus d'informations sur la façon d'installer le réseau, comment prendre en main le code permettant de créer un thingbot et comment lancer une partie dans le [Wiki](https://github.com/panticne/mirai-playschool/wiki) de ce repo.
