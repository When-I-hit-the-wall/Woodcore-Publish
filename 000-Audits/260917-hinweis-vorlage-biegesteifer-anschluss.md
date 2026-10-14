# Hinweis an die verantwortliche Person der Vorlage «rigid connection»

**Vorlage:** `«rigid connection» template` (Excel-Tools, «go life» 24.02.2022)
**Blatt:** «Biegesteifer Anschluss», Spalte AH (Zeilen 8 bis 107) und Zelle C50 — Winkel zwischen Kraft- und Faserrichtung beim massgebenden Verbinder
**Gefunden:** periodisches Audit des Projekts «Statischer Rapport», 16.09.2026 (Befund AUD-2-4)
**Datum dieses Hinweises:** 17.09.2026

## Was nicht stimmt

Der Kraft-Faser-Winkel wird aus dem **Betrag** der Kraftrichtung berechnet. Danach wird α abgezogen:

| Zelle | Formel heute |
|---|---|
| AH*n* | `=IF(AA n+AB n=0,90,ABS(ATAN((Y n+Z n)/(AA n+AB n))*180/PI()))` |
| C50 | `=ABS(INDEX(AH8:AH107,MATCH($C49,$AC8:$AC107,0))-C12)` |

`ABS(ATAN(…))` verliert das Vorzeichen der Kraftrichtung. Für α = 0 ist das ohne Folgen. Für α ≠ 0 und eine Kraft, die zur anderen Seite der Faser geneigt ist, liefert C50 einen falschen Winkel.

## Beispiel

α = 30° (C12), F_Ed,x = 10 kN, F_Ed,y = 10 kN nach unten, M_Ed = 0:

- Vorlage, C50: **15°**
- Geometrie, am Raster der Vorlage selbst gemessen: **75°**
- Unabhängige Berechnung des Projekts: 75°

Das Audit hat 29 Fälle verglichen. Von den 10 Fällen mit α ≠ 0 zeigen 6 diese Abweichung. Die 4 übrigen haben α = 90°, eine Kraft parallel zu einer Achse oder eine Kraft, die zur Faserseite geneigt ist.

Keine Formel der Vorlage liest C50 weiter. Wer den Winkel aber für die Lochleibungsfestigkeit f_h,α,k übernimmt, zum Beispiel in die Vorlage «Stabdübel- und Schraubverbindungen», rechnet mit einem falschen Winkel. Ein zu kleiner Winkel ergibt dort eine zu hohe Festigkeit.

## Vorschlag

Den Winkel mit Vorzeichen berechnen und erst danach auf 0° bis 90° zurückführen, zum Beispiel:

- AH*n*: `=DEGREES(ATAN2(AA n+AB n, Y n+Z n))` (ATAN2 nimmt in Excel zuerst x, dann y; die Reihenfolge ist an die Achsen des Blatts anzupassen)
- C50: den Winkel zwischen der Kraftrichtung und der Faserrichtung α auf 0° bis 90° falten, z. B. `=MIN(MOD(ABS(… - C12),180), 180-MOD(ABS(… - C12),180))`

Die genaue Formel hängt davon ab, wie das Blatt Y/Z und AA/AB orientiert. Sie sollte mit dem Beispiel oben geprüft werden (Soll: 75°).

## Nebenbei gefunden (AUD-2-10)

C18 `=(C13-2*C16)/(C17-1)` teilt durch null, wenn die Gruppe nur eine Reihe hat (C17 = 1). Das ganze Blatt zeigt dann `#DIV/0!`, zum Beispiel bei 1 × 4 oder 1 × 1 Verbindungsmitteln.

Im Projekt ist nichts zu ändern. Es berechnet diesen Winkel selbst (`calc/domains/connection.py`, `grain_angle`) und benutzt die Vorlage nicht.
