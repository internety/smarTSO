plik table-offki.sql zawiera definicję tabeli w lokalnym sql
ustawienia lokalnej bazy SQL w pliku dbinit.py
skrypt inline karmiący lokalną bazę: feed_local_mysql.py. użycie: mitmdump -s feed_local_mysql.py -p [PORT]
funkcja parseitem, do parsowania pola offer: parseitem.py

1. łapiemy dane handlu:
	- id
	- senderID
	- senderName
	- type
	- created    (czas msec since epoch od wysłania na handel)
	- offer
	- lotsRemaining
	- (wspólny) czas pobrania
   (przykłady pola offer:
	Bronze,10000|Granite,199|1
	ProductivityBuffLvl3,,0,0,25|Coin,280|1
	Adventure,TheBetrayedLittleTailor,5080572,0,1|Granite,12999|1
	CO,ILE|ZACO,ZAILE|TRANSZY)

2. dla każdego zestawu powyższych danych liczymy:
	- z offer:produkt oferowany, ilość oferowana, produkt żądany, ilość żądana, ilość wystawionych transz)
	- z created i czasu pobrania: wiek oferty w sekundach
	- z ilości wystawionych transz i lotsRemaining: ilość pozostałych transz
	- z pozostałych transz i z wieku oferty: średnia ilość sprzedaży na godzinę
	- ONEco_rowne_xzaco, Xco_rowne_ONEzaco: cena za sztuke, odwrotność ceny za sztukę (wartość "monety")

3. obliczone dane wraz z przechwyconymi wrzucamy do sql, tabela docelowa definiuje unikatowy łączony index 
   (id,senderID,lotsRemaining), wiersze dodajemy przez "INSERT IGNORE", potencjalne duplikaty są po cichu 
   ignorowane.



