# 1 Puspose and Patterns
Wir wollen einen Waldbrand modellieren, um herauszufinden wie sich ein Feuer ausbreitet.

Wir erwarten, dass es zu vielen kleinen Bränden kommt, aber nur selten zu einem großflächigen Brand.


# 2 Entities, State variables und Scales
Gitter mit Zellen
3 Zustände:
- Baum 
- Feuer 
- leer

1 m^2 Zellen
10.000 Zellen

Simulationsdauer: - (bis ein Muster zu erkennen ist)
Zeitschritt Dauer: 1s (oder kürzer)


# 3 Process Overview and Scheduling
Zellen ändern ihren Zustand
- Baum wächst mit Wahrscheinlichkeit p
- Feuer entsteht mit Wahrscheinlichkeit f; f << p, nur wenn es einen Baum gibt
- wenn ein Nachbar brennt und es gibt einen Baum, dann brennt dieser Baum im nächsten Zeitschritt (Zustand = Feuer)
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
Zufallsrate für Baumwachstum und Blitzeinschlag (=Feuer)
x Collectives:
es gibt keine Gruppen von Agenten
Observation:
visuelle Darstellung der Zellen für jeden Zeitschritt


# 5 Initialization 
10.000 Zellen (Größe von 1 m^2)
Baum mit Wahrscheinlichkeit -

# 6 Input Data
keine

# 7 Submodels
Blitz: wenn es in der Zelle einen Baum gibt, dann mit Wahrscheinlichkeit f Feuer
Baumwachstum: wenn Zelle leer, dann mit Wahrscheinlichkeit p Baum
Feuerausbreitung: wenn es in der Zelle einen Baum gibt und mind. ein Nachbar brennt, dann Feuer
Brand: wenn Zelle = Feuer, dann Zelle im nächsten Zeitsschritt leer



