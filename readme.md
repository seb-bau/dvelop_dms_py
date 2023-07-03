# d.velop DMS Python Wrapper
## (Bisher) Umgesetzte Funktionen
* Recherche mit Filtermöglichkeit Kategorie und Eigenschaft
* Download des Dokumenten-Blobs
* Auflösung von Eigenschaften oder Kateogorie-Keys zu Anzeigenamen
## Beispiele
### Objekt initialisieren
```
from dvelopdmspy.dvelopdmspy import DvelopDmsPy

dvelop = DvelopDmsPy(hostname="instanz.d-velop.cloud", api_key="API-KEY")
```

### Dokumentenrecherche
Im Beispiel: Es werden alle Dokumente aufgelistet, die in der Kategorie "Beschwerde" oder "Schriftverkehr" abgelegt  
wurden, die Eigenschaft "Dokumenten-Status" den Wert "neu" hat und "Zuständigkeit" den Wert "Mustermann Max" hat

```
# Mehrere Eigenschaften und Kategorien können verkettet werden, in dem die Variable angehängt wird
sprops = dvelop.add_property("Zuständigkeit", "Mustermann Max")
sprops = dvelop.add_property("Dokumenten-Status", "Neu", sprops)

scats = dvelop.add_category("Beschwerde")
scats = dvelop.add_category("Schriftverkehr", scats)

# Recherche durchführen, Limit ist optional
docs = dvelop.get_documents(properties=sprops, categories=scats, limit=100)

# Alle Dok-IDs ausgeben, die gefunden wurden:
for doc in docs:
    print(doc.id_)
```

### Datei des Dokumentes herunterladen
```
dest_file = "C:\\temp\\ausgabe.pdf"
dvelop.download_doc_blob("DOK-ID", dest_file)
```

### Anzeigenamen der Kategorie eines recherchierten Dokumentes anzeigen
```
doc = dvelop.get_documents(doc_id="DOC-ID")
cat_displ_name = dvelop.key_to_display_name(doc[0].sourcecategories)
print(f"Die Kategorie von Dokument {doc[0].id_} lautet {cat_displ_name}.")
```