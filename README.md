# Bosanski Realtime Prompt Replacer

## Opis
Alat za upravljanje promptima sa ključnim riječima koje se automatski zamjenjuju u realnom vremenu dok kucate u bilo kojoj aplikaciji.

## Funkcionalnosti
- Definisanje prompta sa ključnim riječima (npr. :prevedi, :sumiraj)
- Automatska zamjena ključnih riječi dok kucate u bilo kojoj aplikaciji
- Upravljanje promptima kroz konzolni interfejs

## Korištenje
1. Pokrenite aplikaciju: `python realtime_prompt_replacer.py`
2. Dodajte svoje prompte sa ključnim riječima
3. Pokrenite "Start real-time replacement"
4. U bilo kojoj aplikaciji, kada ukucate definisanu ključnu riječ (npr. :testiramo) i pritisnete razmaknicu ili enter, 
   tekst će se automatski zamijeniti sa sadržajem prompta

## Instalacija
```
uv pip install pyautogui pynput pyperclip
```

## Pokretanje
```
python realtime_prompt_replacer.py
```

## Napomene
- Aplikacija mora imati dozvole za praćenje tastature i simulaciju pritiska tipki
- Prilikom zamjene, originalni sadržaj clipboarda se čuva i vraća nakon zamjene
- Aplikacija koristi fajl prompts.json za čuvanje prompta između sesija
- Za najbolje iskustvo, koristite ključne riječi koje se neće pojaviti slučajno u normalnom tekstu