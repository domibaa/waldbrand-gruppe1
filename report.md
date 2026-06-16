# Wildfire Simulation: Einfluss von Baumwachstum und Waldzusammensetzung auf Branddynamiken

## Abstract

In diesem Projekt wird ein vereinfachtes Waldbrandmodell als zellulärer Automat auf einem 100×100-Raster umgesetzt. Untersucht wird, wie sich unterschiedliche Baumwachstumswahrscheinlichkeiten und Waldzusammensetzungen auf die Branddynamik auswirken. Dafür wird ein reiner Nadelwald mit einem Mischwald verglichen. Baumtyp A steht dabei für eine leicht entzündliche Baumart, Baumtyp B für eine feuerresistentere Baumart. Ausgewertet werden die mittlere Anzahl gleichzeitig brennender Zellen pro Tick, die mittlere Größe zusammenhängender Feuercluster und die mittlere Anzahl gleichzeitig aktiver Feuercluster. Die Ergebnisse zeigen, dass höheres Baumwachstum die Brandaktivität deutlich erhöht, während ein höherer Anteil feuerresistenter Bäume die Ausbreitung tendenziell abschwächt. Das Modell macht grundlegende Zusammenhänge zwischen Baumwachstum, Waldzusammensetzung und räumlicher Feuerausbreitung sichtbar, bleibt aber durch fehlende reale Faktoren wie Wind, Topografie und Feuchtigkeit stark vereinfacht.

## 1. Introduction
Waldbrände sind ein räumliches Ausbreitungsphänomen, bei dem lokale Prozesse zu großräumigen Mustern führen können. Ob ein Feuer klein bleibt oder sich über größere Flächen ausbreitet, hängt unter anderem davon ab, wie viel brennbares Material vorhanden ist, wie dieses räumlich verteilt ist und wie leicht benachbarte Bereiche entzündet werden können. In realen Ökosystemen spielen zusätzlich Faktoren wie Wind, Trockenheit, Topografie, Baumarten, Altersstruktur und menschliche Eingriffe eine Rolle. In einem vereinfachten Simulationsmodell können einzelne Einflussgrößen gezielt untersucht werden.

Ein geeigneter Ansatz dafür sind zelluläre Automaten. Dabei wird ein Raum in einzelne Zellen unterteilt, die jeweils einen bestimmten Zustand besitzen. Die Zustände ändern sich in diskreten Zeitschritten nach festgelegten Regeln. Jede Zelle reagiert nur auf ihren eigenen Zustand und auf den Zustand ihrer Nachbarschaft. Obwohl diese Regeln einfach sind, können auf Systemebene komplexe Muster entstehen, zum Beispiel viele kleine Feuer, größere zusammenhängende Feuerflächen oder mehrere gleichzeitig aktive Brandherde.

In diesem Projekt wird ein Waldbrandmodell auf einem zweidimensionalen Raster umgesetzt. Jede Zelle kann leer sein, einen Baum enthalten oder brennen. Zusätzlich wird zwischen zwei Baumtypen unterschieden. Baumtyp A steht für eine leicht entzündliche Baumart, zum Beispiel einen Nadelbaum. Baumtyp B steht für eine feuerresistentere Baumart, zum Beispiel einen Laubbaum. Dadurch kann ein reiner Nadelwald mit einem Mischwald verglichen werden. Die Feuerweitergabe erfolgt über die Moore-Nachbarschaft, also über die acht umliegenden Nachbarzellen einer Zelle. Zusätzlich können Bäume zufällig durch Blitzschlag entzündet werden, während leere Zellen mit einer bestimmten Wahrscheinlichkeit wieder zu Baumzellen werden.

Die zentrale Forschungsfrage lautet:

**Wie verändern sich die mittlere Anzahl gleichzeitig brennender Zellen, die mittlere Feuerclustergröße und die mittlere Anzahl gleichzeitig aktiver Feuercluster bei unterschiedlichen Wahrscheinlichkeiten für Baumwachstum in einem Nadelwald im Vergleich zu einem Mischwald?**

Die mittlere Anzahl gleichzeitig brennender Zellen (mean_fire) beschreibt, wie viele Zellen im Mittel pro Tick im Zustand FIRE sind. Die mittlere Feuerclustergröße (mean_cluster) beschreibt die durchschnittliche Größe zusammenhängender Gruppen brennender Zellen. Die Clusteranzahl (mean_n_clusters) gibt an, wie viele voneinander getrennte Feuercluster im Mittel gleichzeitig aktiv sind. Das Modell soll keine realen Waldbrände vorhersagen, sondern grundlegende Zusammenhänge zwischen Baumwachstum, Entzündungswahrscheinlichkeit, Waldzusammensetzung und räumlicher Feuerausbreitung sichtbar machen.

## 2. Method
Das Modell wurde als zellulärer Automat umgesetzt. Die Umgebung besteht aus einem zweidimensionalen Gitter mit 100 × 100 Zellen, also insgesamt 10.000 Zellen. Jede Zelle stellt eine kleine Fläche im Wald dar und kann sich in einem von vier Zuständen befinden: leerer Boden (EMPTY), Baum vom Typ A (TREE_A), Feuer (FIRE) oder Baum vom Typ B (TREE_B). Baumtyp A ist leicht entzündlich, während Baumtyp B feuerbeständiger ist. Die Simulation läuft über 1000 Zeitschritte. Die Grenzen des Gitters sind geschlossen, das heißt, Feuer kann nicht am Rand auf die gegenüberliegende Seite springen.

Zu Beginn wird das Gitter zufällig initialisiert. Für jede Zelle wird anhand vorgegebener Wahrscheinlichkeiten entschieden, ob sie leer bleibt, mit Baumtyp A besetzt wird oder mit Baumtyp B besetzt wird. Dies wird in der Funktion init_grid() umgesetzt:

```python
def init_grid(p_tree_a: float, p_tree_b: float) -> np.ndarray:
    p_empty = 1.0 - p_tree_a - p_tree_b
    return np.random.choice(
        [EMPTY, TREE_A, TREE_B],
        size=(N, N),
        p=[p_empty, p_tree_a, p_tree_b],
    )
```

Die Wahrscheinlichkeit für leere Zellen ergibt sich aus der Restwahrscheinlichkeit nach Abzug der Wahrscheinlichkeiten für Baumtyp A und Baumtyp B. Mit np.random.choice() wird anschließend für jede Zelle ein Anfangszustand ausgewählt. Dadurch können unterschiedliche Waldzusammensetzungen simuliert werden, zum Beispiel ein reiner Nadelwald oder ein Mischwald.
Die Zustandsänderungen erfolgen synchron. Das bedeutet, dass zuerst für alle Zellen auf Basis des aktuellen Gitters der nächste Zustand berechnet wird. Erst danach wird das gesamte Gitter aktualisiert. Dadurch reagieren Zellen nicht innerhalb desselben Ticks auf Zustände, die eigentlich erst im nächsten Tick gelten.

Die wichtigsten Prozesse im Modell sind Baumwachstum, Entzündung und Abbrennen. Eine leere Zelle kann mit der Wahrscheinlichkeit p_growth wieder zu einem Baum werden. Ob dabei Baumtyp A oder Baumtyp B wächst, richtet sich nach dem Verhältnis der Anfangsdichten p_init_a und p_init_b. Ein Baum kann entweder durch Blitzschlag mit der Wahrscheinlichkeit p_lightning oder durch benachbarte brennende Zellen Feuer fangen. Als Nachbarschaft wird die Moore-Nachbarschaft verwendet, also die acht umliegenden Zellen einschließlich diagonaler Nachbarn. Baumtyp A entzündet sich bei einem brennenden Nachbarn mit p_spread_a = 1.0, Baumtyp B mit p_spread_b = 0.6.

Die Entzündung wird für beide Baumtypen getrennt berechnet:

```python
fire_mask = (grid == FIRE).astype(int)
burning_nb = count_burning_neighbours(fire_mask)

ignites_a = (grid == TREE_A) & (
    ((burning_nb > 0) & (rnd < p_spread_a)) | (rnd < p_lightning)
)
new_grid[ignites_a] = FIRE

ignites_b = (grid == TREE_B) & (
    ((burning_nb > 0) & (rnd < p_spread_b)) | (rnd < p_lightning)
)
new_grid[ignites_b] = FIRE
```

Zuerst wird markiert, welche Zellen aktuell brennen. Danach wird berechnet, wie viele brennende Nachbarn jede Zelle besitzt. Anschließend wird geprüft, ob Baumtyp A oder Baumtyp B Feuer fängt. Der Unterschied zwischen den Baumtypen liegt in der Ausbreitungswahrscheinlichkeit. Brennende Zellen werden im nächsten Tick immer zu leerem Boden. Dadurch brennt ein Baum im Modell nur für einen Zeitschritt.
Die zentralen Parameter sind die Wachstumswahrscheinlichkeit p_growth, die Blitzwahrscheinlichkeit p_lightning, die Anfangsdichten p_init_a und p_init_b sowie die Ausbreitungswahrscheinlichkeiten p_spread_a und p_spread_b. Diese Parameter bilden ökologische Prozesse wie Nachwachsen, zufällige Entzündung und unterschiedliche Brennbarkeit stark vereinfacht ab.

Zur Auswertung werden in jedem Tick mehrere Messgrößen gespeichert: die Anzahl brennender Zellen, die Dichten von Baumtyp A und B, die mittlere Größe der Feuercluster und die Anzahl der Feuercluster. Ein Feuercluster ist eine zusammenhängende Gruppe brennender Zellen. Auch für die Clustererkennung wird die 8er-Nachbarschaft verwendet.

Für die technische Umsetzung wurden mehrere Python-Bibliotheken verwendet. numpy speichert das Raster als zweidimensionales Array und erzeugt Zufallszahlen für Wachstum, Blitzschlag und Feuerweitergabe. scipy.ndimage.label erkennt zusammenhängende Feuercluster. matplotlib dient zur Visualisierung der Simulation, der Zellzustände und der Zeitreihenplots. argparse ermöglicht die Steuerung der Parameter über die Kommandozeile, und itertools erzeugt die Parameterkombinationen für die Sweeps.

Das Modell enthält bewusste Vereinfachungen. Windrichtung, Topografie, Feuchtigkeit, Altersstruktur der Bäume und aktive Brandbekämpfung werden nicht berücksichtigt. Alle Zellen sind gleich groß und die Zeit läuft in festen diskreten Schritten ab. Dadurch eignet sich das Modell nicht für reale Vorhersagen, sondern für die Analyse grundlegender Ausbreitungsmuster.

## 3. Results

Für die Auswertung wurden mehrere Simulationsläufe und Parameter-Sweeps durchgeführt. Dabei wurden vor allem die Baumwachstumswahrscheinlichkeit und die Anfangsanteile der beiden Baumtypen variiert. Betrachtet wurden die mittlere Anzahl gleichzeitig brennender Zellen pro Tick (mean_fire), die mittlere Größe aktiver Feuercluster (mean_cluster) und die mittlere Anzahl gleichzeitig aktiver Feuercluster (mean_n_clusters). Zusätzlich wurden die mittleren Dichten von Baumtyp A und Baumtyp B ausgewertet.

mean_fire beschreibt nicht die gesamte abgebrannte Fläche über die komplette Simulation, sondern die mittlere Anzahl der Zellen, die gleichzeitig brennen. mean_n_clusters beschreibt nicht die Größe der Brände, sondern die mittlere Anzahl voneinander getrennter Feuercluster, die gleichzeitig aktiv sind. Ob diese Cluster groß oder klein sind, wird erst zusammen mit mean_cluster sichtbar.

### 3.1 Zeitliche Entwicklung im Nadelwald

Zuerst wurde ein reiner Nadelwald untersucht. Dabei wurde nur Baumtyp A verwendet. Baumtyp B kommt nicht vor. Baumtyp A besitzt mit p_spread_a = 1.0 eine hohe Entzündungswahrscheinlichkeit bei Kontakt mit einem brennenden Nachbarn.

![Zeitliche Entwicklung im Nadelwald](figures/nadelwald_timeseries.png)
 
**Abbildung 1:** Zeitliche Entwicklung eines reinen Nadelwaldes mit growth = 0.005, lightning = 0.0001, init_a = 0.6 und init_b = 0.0. Dargestellt sind die Anzahl brennender Zellen pro Tick, die Dichte von Baumtyp A, die Dichte von Baumtyp B, die mittlere Feuerclustergröße und die Anzahl gleichzeitig aktiver Feuercluster über 1000 Ticks.

In Abbildung 1 ist zu Beginn ein starker Ausschlag bei den brennenden Zellen sichtbar. Dieser Anfangseffekt entsteht durch die hohe Anfangsdichte. Da das Raster zu Beginn stark mit Baumtyp A besetzt ist, ist viel brennbares Material vorhanden. Sobald ein Feuer durch Blitzschlag entsteht, kann es sich schnell über benachbarte Baumzellen ausbreiten.

Nach diesem ersten starken Brand sinkt die Baumdichte deutlich ab, weil brennende Zellen im nächsten Tick zu leeren Zellen werden. Danach entwickelt sich ein dynamischer Verlauf aus Nachwachsen, erneuter Entzündung und Abbrennen. Die mittlere Anzahl gleichzeitig brennender Zellen liegt in diesem Beispiel bei etwa 39.7. Die mittlere Feuerclustergröße beträgt etwa 1.7, und die mittlere Anzahl gleichzeitig aktiver Feuercluster liegt bei etwa 21.6. Die Brandaktivität besteht damit im Mittel nicht aus einem einzigen großen Feuercluster, sondern aus mehreren räumlich getrennten Feuerstellen.

### 3.2 Zeitliche Entwicklung im Mischwald

Anschließend wurde ein Mischwald untersucht. Dabei wurden Baumtyp A und Baumtyp B mit gleicher Anfangswahrscheinlichkeit initialisiert. Baumtyp B entzündet sich bei einem brennenden Nachbarn nur mit p_spread_b = 0.6.
 
![Zeitliche Entwicklung im Mischwald](figures/mischwald_timeseries.png)

**Abbildung 2:** Zeitliche Entwicklung eines Mischwaldes mit growth = 0.005, lightning = 0.0001, init_a = 0.3 und init_b = 0.3. Dargestellt sind die Anzahl brennender Zellen pro Tick, die Dichte von Baumtyp A, die Dichte von Baumtyp B, die mittlere Feuerclustergröße und die Anzahl gleichzeitig aktiver Feuercluster über 1000 Ticks.

Auch im Mischwald tritt zu Beginn ein deutlicher Ausschlag bei den brennenden Zellen auf. Wie im Nadelwald ist dieser Anfangseffekt auf die hohe Anfangsdichte zurückzuführen. Nach dem ersten starken Brand sinken die Baumdichten und es entstehen im weiteren Verlauf wiederholt kleinere Feuer.
Im Vergleich zum reinen Nadelwald ist mean_fire im Mischwald mit etwa 37.5 etwas geringer. Die mittlere Dichte von Baumtyp A beträgt etwa 0.142, die von Baumtyp B etwa 0.176. Die mittlere Feuerclustergröße liegt bei etwa 1.6, die mittlere Anzahl gleichzeitig aktiver Feuercluster bei etwa 21.7. Der Unterschied ist in diesem einzelnen Vergleich nicht sehr groß, zeigt aber die erwartete Tendenz: Baumtyp B reduziert die Feuerweitergabe lokal, da er sich nur mit geringerer Wahrscheinlichkeit entzündet.

### 3.3 Einfluss des Baumwachstums im Nadelwald und Mischwald
Um den Einfluss des Baumwachstums zu untersuchen, wurden Growth-Sweeps für den Nadelwald und den Mischwald durchgeführt. Dabei wurde die Wachstumswahrscheinlichkeit von 0.002 bis 0.040 erhöht, während die übrigen Parameter konstant blieben.
 
![Terminalausgabe des Growth-Sweeps im Nadelwald](figures/growth_sweep_nadelwald.png)

**Abbildung 3:** Terminalausgabe des Growth-Sweeps im reinen Nadelwald mit init_a = 0.6 und init_b = 0.0.

![Terminalausgabe des Growth-Sweeps im Mischwald](figures/growth_sweep_mischwald.png)
 
**Abbildung 4:** Terminalausgabe des Growth-Sweeps im Mischwald mit init_a = 0.3 und init_b = 0.3.

Die Ergebnisse zeigen in beiden Waldtypen einen starken positiven Zusammenhang zwischen Wachstumswahrscheinlichkeit und Brandaktivität. Im Nadelwald steigt mean_fire von 18.91 bei growth = 0.002 auf 264.70 bei growth = 0.040. Im Mischwald steigt mean_fire im selben Bereich von 17.53 auf 244.29. Damit führt höheres Baumwachstum zu deutlich mehr gleichzeitig brennenden Zellen.

Auch die mittlere Feuerclustergröße nimmt zu. Im Nadelwald steigt mean_cluster von 1.44 auf 2.28, im Mischwald von 1.38 auf 1.92. Die mittlere Anzahl gleichzeitig aktiver Feuercluster steigt ebenfalls stark an: im Nadelwald von 10.23 auf 121.69, im Mischwald von 10.40 auf 126.78. Höheres Baumwachstum erzeugt also nicht nur mehr brennende Zellen, sondern auch mehr gleichzeitig aktive Feuercluster.

Die Pearson-Korrelation bestätigt diesen Zusammenhang. Zwischen growth und mean_fire ergibt sich in beiden Sweeps r = +0.9999. Zwischen growth und mean_cluster liegt die Korrelation im Nadelwald bei r = +0.8798 und im Mischwald bei r = +0.8197. Damit ist die Wachstumswahrscheinlichkeit in den untersuchten Simulationen der stärkste Einflussfaktor.

Im direkten Vergleich liegen die Werte des Mischwaldes bei gleicher Wachstumswahrscheinlichkeit meist etwas niedriger als im Nadelwald. Bei growth = 0.040 beträgt mean_fire im Nadelwald 264.70, im Mischwald 244.29. Auch die mittlere Feuerclustergröße ist im Nadelwald mit 2.28 höher als im Mischwald mit 1.92. Das deutet darauf hin, dass Baumtyp B die Feuerweitergabe abschwächt. Der Unterschied ist jedoch kleiner als der Effekt der Wachstumswahrscheinlichkeit selbst.

### 3.4 Einfluss der Waldzusammensetzung

Neben dem Baumwachstum wurde auch die Waldzusammensetzung untersucht. Dafür wurde ein Sweep über unterschiedliche Anfangsanteile von Baumtyp A und Baumtyp B durchgeführt.
 
![Terminalausgabe des Init-A- und Init-B-Sweeps](figures/init_ab_sweep_terminal.png)

**Abbildung 5:** Terminalausgabe des Sweeps über unterschiedliche Anfangsanteile von Baumtyp A und Baumtyp B bei growth = 0.010 und lightning = 0.0001.

Die Tabelle zeigt, dass ein höherer Anteil von Baumtyp B tendenziell mit einer geringeren mittleren Anzahl gleichzeitig brennender Zellen verbunden ist. Bei init_a = 0.60 und init_b = 0.00 liegt mean_fire bei 73.79. Bei init_a = 0.30 und init_b = 0.30 liegt mean_fire bei 68.10. Auch die mittlere Feuerclustergröße sinkt von etwa 1.92 auf etwa 1.74.

Die Pearson-Korrelation für den init_b-Sweep bestätigt diese Tendenz. Zwischen init_b und mean_fire ergibt sich eine negative Korrelation von r = -0.3768. Zwischen init_b und mean_cluster ergibt sich ebenfalls eine negative Korrelation von r = -0.4522. Ein höherer Anfangsanteil von Baumtyp B ist in den untersuchten Simulationen also mit geringerer momentaner Brandaktivität und kleineren Feuerclustern verbunden. Dieser Effekt ist jedoch deutlich schwächer als der Einfluss der Wachstumswahrscheinlichkeit.

### 3.5 Zusammenhang der Messgrößen

mean_fire, mean_cluster und mean_n_clusters beschreiben unterschiedliche Aspekte der Branddynamik. Eine hohe Anzahl brennender Zellen kann durch wenige größere Cluster oder durch viele kleine, getrennte Cluster entstehen. Deshalb zeigt mean_n_clusters nur, wie viele getrennte Feuerstellen gleichzeitig aktiv sind, nicht aber deren Größe. Erst zusammen mit mean_cluster lässt sich beurteilen, ob die Brandaktivität eher aus vielen kleinen oder aus größeren zusammenhängenden Feuerflächen besteht.

In den Sweeps steigen vor allem mean_fire und mean_n_clusters stark an, während mean_cluster schwächer zunimmt. Das deutet darauf hin, dass höheres Wachstum vor allem mehr gleichzeitig aktive Feuerstellen erzeugt und insgesamt mehr Zellen brennen lässt. Die Feuer verbinden sich aber nicht automatisch zu einem einzigen großen Brandcluster.

## 4. Discussion, Conclusion and Limitations

Die Ergebnisse zeigen, dass die Wachstumswahrscheinlichkeit einen sehr starken Einfluss auf die Branddynamik hat. Sowohl im Nadelwald als auch im Mischwald steigt mean_fire mit zunehmendem p_growth deutlich an. Da mean_fire die mittlere Anzahl gleichzeitig brennender Zellen pro Tick beschreibt, bedeutet dies, dass bei höherem Wachstum deutlich mehr Zellen gleichzeitig im Zustand FIRE sind. Die nahezu perfekte positive Korrelation zwischen growth und mean_fire zeigt, dass die Wachstumswahrscheinlichkeit in den untersuchten Simulationen der stärkste Einflussfaktor ist.

Auch die mittlere Feuerclustergröße und die Anzahl gleichzeitig aktiver Feuercluster nehmen mit höherem Wachstum zu. Der stärkste Effekt liegt jedoch nicht darin, dass sich immer ein einzelner großer Brand bildet, sondern darin, dass insgesamt mehr Zellen brennen und mehr getrennte Feuerstellen gleichzeitig aktiv sind. Die Brandaktivität wird dadurch intensiver und räumlich stärker verteilt.

Der Vergleich zwischen Nadelwald und Mischwald zeigt, dass die Waldzusammensetzung ebenfalls eine Rolle spielt. Im reinen Nadelwald besteht der Wald nur aus Baumtyp A, der sich bei Kontakt mit Feuer mit hoher Wahrscheinlichkeit entzündet. Im Mischwald kommt zusätzlich Baumtyp B vor, der sich bei brennenden Nachbarn nur mit geringerer Wahrscheinlichkeit entzündet. Dadurch wird die Weitergabe des Feuers lokal abgeschwächt. Die Ergebnisse zeigen deshalb im Mischwald tendenziell niedrigere Werte für mean_fire und mean_cluster als im Nadelwald.

Der Einfluss der Waldzusammensetzung ist jedoch schwächer als der Einfluss des Baumwachstums. Die Wachstumswahrscheinlichkeit bestimmt direkt, wie schnell nach einem Brand wieder neue Baumzellen entstehen und wie viel brennbares Material im Raster verfügbar ist. Der Baumtyp beeinflusst dagegen vor allem, wie wahrscheinlich die Feuerweitergabe von einer brennenden Zelle auf eine benachbarte Baumzelle ist. Dadurch wirkt der Mischwald abschwächend, verhindert Brände aber nicht vollständig.

Ein wichtiger Punkt für die Interpretation ist der starke Anfangseffekt in den Zeitreihen. Zu Beginn ist das Raster durch die gewählte Initialisierung bereits dicht bewachsen. Dadurch steht sofort viel brennbares Material zur Verfügung. Wenn ein Feuer entsteht, kann es sich in dieser Anfangsphase besonders schnell ausbreiten. Nach diesem ersten starken Brand sinkt die Baumdichte, und das System geht in einen dynamischeren Verlauf über, in dem Bäume nachwachsen und Feuer wiederholt neu entstehen. Da die Kennwerte über alle 1000 Ticks gemittelt werden, kann dieser Anfangseffekt die Mittelwerte beeinflussen.

Die Forschungsfrage lässt sich damit folgendermaßen beantworten: Eine höhere Wachstumswahrscheinlichkeit führt im Modell zu einer deutlich höheren mittleren Anzahl gleichzeitig brennender Zellen, zu größeren Feuerclustern und zu mehr gleichzeitig aktiven Feuerclustern. Der Mischwald reduziert die momentane Brandaktivität und die mittlere Feuerclustergröße tendenziell im Vergleich zum reinen Nadelwald. Der stärkste untersuchte Einflussfaktor ist jedoch das Baumwachstum, da es direkt bestimmt, wie viel Brennstoff im Raster verfügbar ist.

Das Modell liefert keine realistische Vorhersage echter Waldbrände. Dafür ist es zu stark vereinfacht. Reale Waldbrände werden unter anderem von Windrichtung, Windgeschwindigkeit, Temperatur, Luftfeuchtigkeit, Bodenfeuchte, Hangneigung, Topografie, Jahreszeiten, menschlichen Eingriffen und der genauen Vegetationsstruktur beeinflusst. Diese Faktoren werden im Modell nicht berücksichtigt. Auch die Darstellung der Baumarten ist stark vereinfacht, da es nur zwei Baumtypen gibt, die sich ausschließlich durch ihre Entzündungswahrscheinlichkeit unterscheiden.

Eine weitere Einschränkung betrifft die zeitliche Darstellung des Feuers. Eine brennende Zelle bleibt im Modell nur für einen Zeitschritt im Zustand FIRE und wird danach sofort zu leerem Boden. Dadurch werden Brenndauer, Brandintensität und Nachglimmen stark vereinfacht. Auch die regelmäßige Rasterstruktur und die geschlossenen Grenzen stellen eine Vereinfachung gegenüber realen Landschaften dar. Das Modell eignet sich daher vor allem, um qualitative Zusammenhänge zwischen Baumwachstum, Waldzusammensetzung und räumlicher Feuerausbreitung zu analysieren.

##  5. References

[1] Biodiv im Wald. (2020). Waldbrand: Neue Gefahr für die heimischen Waldökosysteme?
https://biodiv-im-wald.online/waldbrand-neue-gefahr-fur-die-heimischen-waldokosysteme
[2] Dingeldein, L. (2020). A Cellular Automata Based Forest-Fire Model. Institut für Theoretische Physik, Goethe University Frankfurt.
https://itp.uni-frankfurt.de/~gros/StudentProjects/Projects_2020/projekt_lars_dingeldein/

## Appendix A: ODD