###
# @author William PENSEC
# @version 1.0
# @date 03/05/2019
# @description Ce code permet de gérer l'affichage d'un bandeau de LED en tenant compte du nombre de LED disponible.
#       On récupère les valeurs de position du TRAM de Brest via l'API mise à notre disposition.
#       Puis on allume la LED correspondante d'une certaine couleur
###

###
# Le code ci-dessous permet de récupérer en temps réel les données de position du tram de Brest.
# Ces données de position sont alors transformées pour afficher la position de la rame sur un bandeau de LEDs qui est disposé sur une maquette de Brest.
#   - Étape 1 : On exécute la requête sur l'API et on boucle tant qu'on a pas récupérer des valeurs correctes
#   - Étape 2 : On décode la chaine JSON reçue par la requête en la stockant dans une variable qui contiendra tout les noeuds de la chaîne
#   - Étape 3 : D'abord, il y a appel d'une fonction valmap() qui est une fonction reprise de la fonction map() d'Arduino et qui va calculer une valeur sur une plage à partir d'une autre plage de valeurs.
#               Cette fonction va donc calculer le numéro de la LED à allumer à partir de la position actuelle de la rame.
#               Enfin, cette valeur est stockée dans une liste déclarée au départ qui servira dans la dernière étape
#   - Étape 4 : Tout d'abord, on éteint chaque pixel du bandeau de LED afin de rafraichir les données.
#               Ensuite, on parcourt la première liste et on cherche à chaque fois dedans si une valeur est identique à une valeur contenue dans une des 2 autres listes :
#                   - si oui : on fait une synthèse additive des couleurs, par exemple Plouzané/Guipavas => Bleu + Vert donnera une LED cyan et on supprime la valeur dans la deuxième liste
#                   - si non : on affiche la couleur donnée à la ligne seulement
#               On remet à 0 les listes pour la prochaine itération.
#               Enfin, on affiche le bandeau tel qu'il est après la mise à jour. Puis on attend un certain nombre de secondes afin de retourner à l'étape 1
### 


### Import des librairies nécessaires ###
import json
import requests
from json.decoder import JSONDecoder
from json.decoder import JSONDecodeError
import time
from neopixel import *
import sys

### Paramétrage des variables ###
# Configuration du bandeau de LED : #
LED_COUNT       = 65			# Nombre de LED sur le bandeau
LED_PIN         = 18			# Pin GPIO connecté au bandeau
LED_FREQ_HZ     = 800000		# Fréquence du signal des LED en hertz
LED_DMA         = 10			# Utilisation du "Direct Memomy Access" pour générer un signal
LED_BRIGHTNESS  = 255		    # Luminosité : mettre à 0 pour sombre et 255 pour le plus lumineux
LED_INVERT      = False		    # True pour inverser le signal (quand vous utilisez un réhausseur de signal de 3.3V à 5V avec un transistor NPN)
LED_CHANNEL     = 0			    # Mettre à "1" pour les pin GPIO 13, 19, 41, 45 or 53

# Configuration des variables d'attente et position maximale : #
MAX_PLOUZANE    = 12300         # Valeur maximale de la position du tram sur la ligne "Porte de Plouzané"
MAX_GOUESNOU    = 12200         # Valeur maximale de la position du tram sur la ligne "Porte de Gouesnou"
MAX_GUIPAVAS    = 12400         # Valeur maximale de la position du tram sur la ligne "Porte de Guipavas"
DELAY_NR 		= 1.0			# Délai d'attente quand une requête échoue (en secondes)
DELAY_CE		= 5.0			# Délai d'attente lors d'une erreur de connexion au serveur http
DELAY			= 10.0			# Délai d'attente entre chaque mise à jour (en secondes)

### Fonction ###
# Fonction de calcul de la LED correspondante selon la position du tram sur la ligne, dérivée de la fonction map() Arduino
def valmap(value, istart, istop, vstart, vstop) :
    return int((value - istart) *  (istop - istart)/ (vstop - vstart) + vstart)

# Fonction prenant en paramètre le nom de la porte de direction, l'id du véhicule et la position courante afin de l'écrire dans un fichier
# Cette fonction n'est pas obligatoire d'utilisation mais s'avère pratique pour vérifier les valeurs car enregistre sous forme CSV les données
def writeFic(nomPorte, idVehicule, position) :
	fic = open("result.csv", "a")
	fic.write(nomPorte)
	fic.write(",")
	fic.write(idVehicule)
	fic.write(",")
	fic.write(position)
	fic.write("\n")
	fic.close()

### FONCTION PRINCIPALE ###
# Create NeoPixel object with appropriate configuration.
strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
# Initialize the library (must be called once before other functions).
strip.begin()

### Création de 3 listes pour chacune des portes ###
# Possibilité de mettre jusqu'à 20 valeurs dans chaque liste
listePlouzane = list(range(0,20))
listeGouesnou = list(range(0,20))
listeGuipavas = list(range(0,20))
#Initialisation à une liste vide au début du programme pour éviter des valeurs stockées en mémoire à cet endroit
del listePlouzane[:]
del listeGouesnou[:]
del listeGuipavas[:]

try :
    while True :
        ###### ====================== ETAPE 1 ====================== ######
        ### Récupération des données de localisation des trams pour Porte De Plouzané ###
        try :
            try :
                # On fait la requête sur l'API avec en paramètre: le format (json), le numéro de ligne (A pour le tram), la direction vers la Porte de Guipavas
                reponse = requests.get('https://applications002.brest-metropole.fr/WIPOD01/Transport/REST/getGeolocatedVehiclesPosition?format=json&route_id=A&trip_headsign=porte%20de%20plouzane')

                # Si la requête échoue, on retente jusqu'à réussir
                while len(reponse.text) == 0 or reponse.text == None :
                    reponse = requests.get('https://applications002.brest-metropole.fr/WIPOD01/Transport/REST/getGeolocatedVehiclesPosition?format=json&route_id=A&trip_headsign=porte%20de%20plouzane')
                    print("None guipavas")
                    time.sleep(DELAY_NR) # Attente entre chaque requête car sinon il peut y avoir des erreurs
            
            except requests.exceptions.ConnectionError :
                print("Erreur de Connexion Porte de Plouzané")
                #renewIP()
                time.sleep(DELAY_CE)
                continue
                    

        ###### ====================== ETAPE 2 ====================== ######
            # Décodage JSON de la chaine reçue via la requête
            obj_dict = JSONDecoder().decode(reponse.text)
            # Affichage simple avec la couleur de la LED correspondante
            print ("Porte de Plouzane (Bleu)")
            # Iterateur du nombre de rames en services sur la ligne
            i = 0
            while (len(obj_dict)) != i :
            ###### ====================== ETAPE 3 ====================== ###### 
                # On calcule la valeur de la LED selon le nombre de LED disponible et les valeurs minimales et maximales constatées de position
                val = valmap(int(obj_dict [i]['Pos']), 0, ((LED_COUNT - 1) - 8), 0, MAX_PLOUZANE)
                val = val - ((LED_COUNT - 1) - 8) # Les valeurs de Porte de PLouzané doivent être prises dans le sens inverse car la valeur "0" se trouve sur la porte de Gouesnou/Guipavas
                val = abs (val) # Depuis la valeur de LED transmise par la fonction, on retranche le nombre de LED et on prend la valeur absolue ensuite
                print(int(obj_dict [i]['Pos']), end='')
                print(" : ", end='')
                # Écriture sur le fichier
                # writeFic("Porte de Plouzané", obj_dict [i]['IdVehicle'], obj_dict [i]['Pos'])
                # On ajoute la valeur à la fin de la liste créée pour la porte de Plouzané
                if((val > 48) and  (obj_dict [i]['Cape'] > "225")) :
                    print(val)
                    listePlouzane.append(val) # Guipavas
                elif((val > 48) and  (obj_dict [i]['Cape'] <= "225")) :
                    print(val + 9)
                    listePlouzane.append(val + 8) # Gouesnou
                else :
                    print(val)
                    listePlouzane.append(val)
                i = i + 1
            print ()
        # Si la requête n'est pas du JSON on affiche un message d'erreur et on sort de la boucle
        except json.decoder.JSONDecodeError :
            print("\"reponse\" Plouzane n'est pas du json")
            # On affiche la valeur reçue pour debug
            print(reponse.text)
            break

        ###### ====================== ETAPE 1 ====================== ######
        ### Récupération des données de localisation des trams pour Porte De Gouesnou ###
        try :
            try :
                # On fait la requête sur l'API avec en paramètre: le format (json), le numéro de ligne (A pour le tram), la direction vers la Porte de Guipavas
                reponse = requests.get('https://applications002.brest-metropole.fr/WIPOD01/Transport/REST/getGeolocatedVehiclesPosition?format=json&route_id=A&trip_headsign=porte%20de%20gouesnou')

                # Si la requête échoue, on retente jusqu'à réussir
                while len(reponse.text) == 0 or reponse.text == None :
                    reponse = requests.get('https://applications002.brest-metropole.fr/WIPOD01/Transport/REST/getGeolocatedVehiclesPosition?format=json&route_id=A&trip_headsign=porte%20de%20gouesnou')
                    print("None guipavas")
                    time.sleep(DELAY_NR) # Attente entre chaque requête car sinon il peut y avoir des erreurs
            
            except requests.exceptions.ConnectionError :
                print("Erreur de Connexion Porte de Gouesnou")
                time.sleep(DELAY_CE)
                continue

        ###### ====================== ETAPE 2 ====================== ######   
            # Décodage JSON de la chaine reçue via la requête
            obj_dict = JSONDecoder().decode(reponse.text)
            # Affichage simple avec la couleur de la LED correspondante
            print ("Porte de Gouesnou (Rouge)")
            # Iterateur du nombre de rames en services sur la ligne
            i = 0
            while (len(obj_dict)) != i :
            ###### ====================== ETAPE 3 ====================== ######
                # On calcule la valeur de la LED selon le nombre de LED disponible et les valeurs minimales et maximales constatées de position
                val = valmap(int(obj_dict [i]['Pos']), 0, ((LED_COUNT - 1) - 8), 0, MAX_GOUESNOU)
                print(int(obj_dict [i]['Pos']), end='')
                print(" : ", end='')
                # Écriture sur le fichier
                #writeFic("Porte de Gouesnou", obj_dict [i]['IdVehicle'], obj_dict [i]['Pos'])
                # On ajoute la valeur à la fin de la liste créée pour la porte de Gouesnou
                if (val > 48) :
                    print(val + 9)
                    listeGouesnou.append(val + 9)
                else :
                    print(val)
                    listeGouesnou.append(val)
                i = i + 1
            print ()
        # Si la requête n'est pas du JSON on affiche un message d'erreur et on sort de la boucle
        except json.decoder.JSONDecodeError :
            print("\"reponse\" Gouesnou n'est pas du json")
            # On affiche la valeur reçue pour debug
            print(reponse.text)
            break

        ###### ====================== ETAPE 1 ====================== ######
        ### Récupération des données de localisation des trams pour Porte De Guipavas ###
        try :
            try :
                # On fait la requête sur l'API avec en paramètre: le format (json), le numéro de ligne (A pour le tram), la direction vers la Porte de Guipavas
                reponse = requests.get('https://applications002.brest-metropole.fr/WIPOD01/Transport/REST/getGeolocatedVehiclesPosition?format=json&route_id=A&trip_headsign=porte%20de%20guipavas')

                # Si la requête échoue, on retente jusqu'à réussir
                while len(reponse.text) == 0 or reponse.text == None :
                    reponse = requests.get('https://applications002.brest-metropole.fr/WIPOD01/Transport/REST/getGeolocatedVehiclesPosition?format=json&route_id=A&trip_headsign=porte%20de%20guipavas')
                    print("None guipavas")
                    time.sleep(DELAY_NR) # Attente entre chaque requête car sinon il peut y avoir des erreurs
            
            except requests.exceptions.ConnectionError :
                print("Erreur de connexion Porte de Guipavas")
                time.sleep(DELAY_CE)
                continue

        ###### ====================== ETAPE 2 ====================== ######
            # Décodage JSON de la chaine reçue via la requête
            obj_dict = JSONDecoder().decode(reponse.text)
            # Affichage simple avec la couleur de la LED correspondante
            print("Porte de Guipavas (Vert)")
            # Iterateur du nombre de rames en services sur la ligne
            i = 0
            while (len(obj_dict)) != i :
            ###### ====================== ETAPE 3 ====================== ######
                # On calcule la valeur de la LED selon le nombre de LED disponible et les valeurs minimales et maximales constatées de position
                val = valmap(int(obj_dict [i]['Pos']), 0, ((LED_COUNT - 1) - 8), 0, MAX_GUIPAVAS)
                print(int(obj_dict [i]['Pos']), end='')
                print(" : ", end='')
                print(val)
                # Écriture sur le fichier
                #writeFic("Porte de Guipavas", obj_dict [i]['IdVehicle'], obj_dict [i]['Pos'])
                # On ajoute la valeur à la fin de la liste créée pour la porte de Guipavas
                listeGuipavas.append(val)
                i = i + 1
        # Si la requête n'est pas du JSON on affiche un message d'erreur et on sort de la boucle
        except json.decoder.JSONDecodeError :
            print("\"reponse\" Guipavas n'est pas du json")
            # On affiche la valeur reçue pour debug
            print(reponse.text)
            break

        ###### ====================== ETAPE 4 ====================== ######
        # On éteint tous les pixels du bandeau afin de réactualiser les données visuelles
        iter = 0
        while iter != strip.numPixels() :
            strip.setPixelColor(iter , Color(0,0,0))
            strip.show()
            iter = iter + 1

        # Vérification pour chaque valeur d'une liste si cette même valeur est également présente dans une autre liste :
        # - si la valeur est présente dans une autre liste alors on opère une synthèse additive des couleurs pour allumer la LED correspondante sur une couleur mélangeant les 2 couleurs de bases
        #       on enlève également cette valeur de la liste dans laquelle elle se trouvait également pour éviter les doublons plus tard
        # - si la valeur n'est pas présente alors on allume la LED d'une couleur basique
        # Cas extrêmement rare => 3 trams différents au même arrêt; la couleur sera blanche mais normalement c'est impossible d'obtenir ce résultat
        for valeurListe in listePlouzane :
            if((valeurListe in listeGouesnou) > 0):
                strip.setPixelColor(valeurListe , Color(0,255,255)) # Plouzané/Gouesnou => Magenta
                if((valeurListe in listeGuipavas) > 0):
                    strip.setPixelColor(valeurListe , Color(255,255,255)) # Plouzané/Gouesnou/Guipavas => Blanc
                    listeGuipavas.remove(valeurListe)
                    print ("Superposition Porte de Plouzané/Gouesnou/Guipavas (Blanc)")
                listeGouesnou.remove(valeurListe)
                print ("Superposition Porte de Plouzané/Gouesnou (Magenta)")
            else :
                if((valeurListe in listeGuipavas) > 0):
                    strip.setPixelColor(valeurListe , Color(255,0,255)) # Plouzané/Guipavas => Cyan
                    listeGuipavas.remove(valeurListe)
                    print ("Superposition Porte de Plouzané/Guipavas (Cyan)")
                else :
                    strip.setPixelColor(valeurListe , Color(0,0,255)) # Plouzané => Bleu
            
        for valeurListe in listeGouesnou :
            if((valeurListe in listeGuipavas) > 0):
                strip.setPixelColor(valeurListe , Color(255,255,0)) # Gouesnou/Guipavas => Jaune
                listeGuipavas.remove(valeurListe)
                print ("Superposition Porte de Gouesnou/Guipavas (Jaune) ")
            else :
                strip.setPixelColor(valeurListe , Color(0,255,0)) # Gouesnou => Rouge
                
        for valeurListe in listeGuipavas :
            strip.setPixelColor(valeurListe , Color(255,0,0)) # Guipavas => Vert

        # Remise à 0 des listes pour la prochaine itération   
        del listePlouzane[:]
        del listeGouesnou[:]
        del listeGuipavas[:]

        # Actualisation du bandeau de LED
        strip.show()
        print()
        print ("-------------------------------------------------")
        print()
        # Attente de DELAY secondes entre chaque tour de boucle
        time.sleep(DELAY)

except KeyboardInterrupt :
    print("Programme interrompu")