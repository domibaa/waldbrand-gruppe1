# 1 Purpose and Patterns
Wir wollen einen Waldbrand modellieren, um herauszufinden wie sich ein Feuer ausbreitet.

Wir erwarten, dass es zu vielen kleinen Bränden kommt, aber nur selten zu einem großflächigen Brand.

Wie verändert sich die durchschnittliche Brandgröße, Clustergröße und Clusteranzahl bei unterschiedlichen Wahrscheinlichkeiten für Baumwachstum für einen Nadelwald und einen Mischwald?


# 2 Entities, State variables und Scales
Gitter mit Zellen

4 Zustände:
- EMPTY  (0) — leerer Boden
-TREE_A (1) — lebender Baum, Typ A (leicht entzündlich; p_spread_a = 1)
-FIRE   (2) — brennender Baum
-TREE_B (3) — lebender Baum, Typ B (feuerbeständiger; p_spread_b = 0,6)
 
100x100 Gitter mit abgeschlossenen Grenzen

Simulationsdauer: 1000 Ticks


# 3 Process Overview and Scheduling
Zellen ändern ihren Zustand
- Baum wächst mit Wahrscheinlichkeit p_growth
- Feuer entsteht mit Wahrscheinlichkeit p_lightning (=0,0001), nur wenn es einen Baum gibt
- wenn ein Nachbar (Moore-Nachbarschaft) brennt und es gibt einen Baum, dann brennt dieser Baum im nächsten Zeitschritt mit Wahrscheinlichkeit p_spread_a bzw. p_spread_b
- wenn Baum brennt ist die Zelle im nächsten Schritt leer

Zellen aktualisieren Zustand in jedem Zeitschritt synchron


# 4 Design Concepts
Basic Principles:
Self-Organised Criticality (Komplexität entsteht ohne zentrale Steuerung)
Emergence:
wenige Regeln für die Zellen -> entstehen viele kleine und wenig große Waldbrände
x Adaption, Objectives, Learning, Prediction:
Zellen treffen keine eigenen Entscheidungen, befolgen nur die Regeln
Sensing:
Zellen nehmen Zustand ihrer unmittelbaren Nachbarn wahr
Interaction:
direkte Beeinflussung der Nachbarn
Stochasticity:
Zufallsrate für Baumwachstum und Blitzeinschlag
x Collectives:
es gibt keine Gruppen von Agenten
Observation:
visuelle Darstellung der Zellen für jeden Zeitschritt
statistische Auswertung: durchschnittliche Brandgröße, Clustergröße, Clusteranzahl und Korrelation


# 5 Initialization 
10.000 Zellen
Baum mit Wahrscheinlichkeit p_tree_a und p_tree_b


# 6 Input Data
keine

# 7 Submodels
EMPTY → TREE_A oder TREE_B:
wenn die Zelle leer ist (grid == EMPTY), wächst mit einer Wahrscheinlichkeit von p_growth ein Baum von Typ A oder B

TREE_A -> FIRE: 
wenn es in der Zelle einen Baum (Typ A) gibt (grid == TREE_A) und einen brennenden Nachbarn hat ((burning_nb) > 0) & (rnd < p_spread_a) oder (rnd < p_lightning) => FIRE

TREE_B -> FIRE: 
wenn es in der Zelle einen Baum (Typ B) gibt (grid == TREE_B) und einen brennenden Nachbarn hat (burning_nb) > 0 & (rnd < p_spread_b) oder (rnd < p_lightning) => FIRE

FIRE -> EMPTY: 
wenn ein Baum brennt (grid == FIRE) => EMPTY
