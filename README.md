# FlowPlus - Bosanski Realtime Prompt Replacer

## Opis
Alat za upravljanje promptima sa ključnim riječima koje se automatski zamjenjuju u realnom vremenu dok kucate u bilo kojoj aplikaciji.

## Funkcionalnosti
- Definisanje prompta sa ključnim riječima (npr. :prevedi, :sumiraj)
- Automatska zamjena ključnih riječi dok kucate u bilo kojoj aplikaciji
- Upravljanje promptima kroz web interfejs (FastAPI)
- Kompatibilnost sa Gemini AI modelima
- Mogućnost postavljanja varijabli okoline (API ključeva)
- Animirani loading ekran sa "Loading..." tekstom i tačkama pri pokretanju aplikacije
- Borderless prozor dizajn sa dugmićima za minimizaciju, maksimizaciju i zatvaranje

## Korištenje
1. Pokrenite aplikaciju: `python ui.py`
2. UI će se otvoriti u prozoru (backend na `http://127.0.0.1:8080`)
3. Dodajte svoje prompte sa ključnim riječima
4. Text replacer se automatski pokreće u pozadini

## Instalacija
```
uv pip install -r requirements.txt
```

## Pokretanje
```
python ui.py
```

## Konfiguracija
- Aplikacija koristi `.env` fajl za pohranu API ključeva i varijabli okoline
- Ako ne postoji `.env` fajl, biće automatski kreiran sa primjerima

## Napomene
- Aplikacija mora imati dozvole za praćenje tastature i simulaciju pritiska tipki
- Prilikom zamjene, originalni sadržaj clipboarda se čuva i vraća nakon zamjene
- Aplikacija koristi fajl prompts.json za čuvanje prompta između sesija
- Za najbolje iskustvo, koristite ključne riječi koje se neće pojaviti slučajno u normalnom tekstu
- Web interfejs koristi FastAPI umjesto Streamlita zbog problema sa kompilacijom u EXE