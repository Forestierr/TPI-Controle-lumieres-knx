# Caméra #

## Dossiers ##

### test ###

Dossier contenant un fichier de test d'OpenCV.
> cd test
> 
> python main.py

### Detection_Porte ###

**door_select.py** fichier utilisé pour sélectionner la position des portes.

**door_detect.py** fichier utilisé pour détecter les porte avec le template matching.

### Detection_Personne ##

**personne_detect.py** fichier utilisé pour détecter des personnes en mouvement (avec backgroundSubtractorKNN).

**personne_tracking.py** fichier utilisé pour calculer l'angle de déplacement d'une personne.

### Detection_Entry ###

**entry_detect.py** fichier utiliser pour détecter les entrées. Ce fichier utilise la detection des portes et des 
personnes.

### Detection_Personne_2 ###

Ce dossier contient le fichier de détection réaliser pour l'amélioration du système.
La détection se fait donc par le dessu de la porte ou par le côté.

**personne_detect.py** fichier utilisé pour détecter des personnes en mouvement (avec backgroundSubtractorMOG2).

### Detection_Entry_2 ###

Ce dossier contient le fichier de détection réaliser pour l'amélioration du système.
Il fonctionne avec **Detection_Personne_2**.

**entry_detect_2.py** fichier utiliser pour détecter les entrées. Ce fichier utilise la detection des portes et des
personnes.

---

Robin Forestier