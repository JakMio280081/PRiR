import math
import os
import random
import time
from multiprocessing import Pool

LICZBA_MIAST = 30
ROZMIAR_POPULACJI = 300
LICZBA_POKOLEN = 100
ROZMIAR_TURNIEJU = 4
P_KRZYZOWANIA = 0.9
P_MUTACJI = 0.2
LICZBA_PROCESOW = min(4, os.cpu_count() or 1)

ODLEGLOSCI = None


def przygotuj_odleglosci():
    losowanie = random.Random(12345)
    miasta = [
        (losowanie.uniform(0, 1000), losowanie.uniform(0, 1000))
        for _ in range(LICZBA_MIAST)
    ]

    return [
        [
            math.dist(miasta[i], miasta[j])
            for j in range(LICZBA_MIAST)
        ]
        for i in range(LICZBA_MIAST)
    ]


def ustaw_odleglosci(odleglosci):
    global ODLEGLOSCI
    ODLEGLOSCI = odleglosci


def dlugosc_trasy(trasa):
    return sum(
        ODLEGLOSCI[trasa[i]][trasa[(i + 1) % len(trasa)]]
        for i in range(len(trasa))
    )


def turniej(populacja, oceny):
    kandydaci = random.sample(
        range(len(populacja)), ROZMIAR_TURNIEJU
    )
    return min(kandydaci, key=lambda i: oceny[i])


def krzyzowanie_ox(rodzic1, rodzic2, losowanie):
    a, b = sorted(losowanie.sample(range(LICZBA_MIAST), 2))
    dziecko = [-1] * LICZBA_MIAST
    dziecko[a:b + 1] = rodzic1[a:b + 1]

    zajete = set(dziecko[a:b + 1])

    wolne_geny = [
        miasto
        for miasto in rodzic2[b + 1:] + rodzic2[:b + 1]
        if miasto not in zajete
    ]

    pozycje = (
        list(range(b + 1, LICZBA_MIAST))
        + list(range(0, a))
    )

    for pozycja, miasto in zip(pozycje, wolne_geny):
        dziecko[pozycja] = miasto

    return dziecko


def mutacja(trasa, losowanie):
    i, j = losowanie.sample(range(LICZBA_MIAST), 2)
    trasa[i], trasa[j] = trasa[j], trasa[i]


def krzyzowanie_rownolegle(zadanie):
    rodzic1, rodzic2, ziarno = zadanie
    losowanie = random.Random(ziarno)

    if losowanie.random() < P_KRZYZOWANIA:
        return krzyzowanie_ox(rodzic1, rodzic2, losowanie)

    return rodzic1.copy()


def mutacja_rownolegla(zadanie):
    trasa, ziarno = zadanie
    losowanie = random.Random(ziarno)

    if losowanie.random() < P_MUTACJI:
        mutacja(trasa, losowanie)

    return trasa


def algorytm_genetyczny():
    random.seed(2026)
    odleglosci = przygotuj_odleglosci()

    populacja = [
        random.sample(range(LICZBA_MIAST), LICZBA_MIAST)
        for _ in range(ROZMIAR_POPULACJI)
    ]

    najlepsza_trasa = None
    najlepsza_odleglosc = float("inf")

    start = time.perf_counter()

    with Pool(
        processes=LICZBA_PROCESOW,
        initializer=ustaw_odleglosci,
        initargs=(odleglosci,)
    ) as pula:

        for pokolenie in range(LICZBA_POKOLEN + 1):

            # Rownolegla ocena
            oceny = pula.map(
                dlugosc_trasy, populacja, chunksize=25
            )

            indeks_najlepszego = min(
                range(ROZMIAR_POPULACJI),
                key=lambda i: oceny[i]
            )

            if oceny[indeks_najlepszego] < najlepsza_odleglosc:
                najlepsza_odleglosc = oceny[indeks_najlepszego]
                najlepsza_trasa = populacja[indeks_najlepszego].copy()

                trasa_tekst = ' -> '.join(
                    str(miasto + 1) for miasto in najlepsza_trasa
                )
                trasa_tekst += ' -> ' + str(najlepsza_trasa[0] + 1)

                print(f'ZMIANA! Pokolenie {pokolenie}: '
                      f'dlugosc = {najlepsza_odleglosc:.2f}')
                print(f'Trasa: {trasa_tekst}\n')

            if pokolenie % 25 == 0:
                print(
                    f"Pokolenie {pokolenie:3d}: "
                    f"najlepsza trasa = {najlepsza_odleglosc:.2f}"
                )

            if pokolenie == LICZBA_POKOLEN:
                break

            # najlepszy bez zmian
            elita = populacja[indeks_najlepszego].copy()

            # Wybor par 
            zadania_krzyzowania = []

            for _ in range(ROZMIAR_POPULACJI - 1):
                r1 = turniej(populacja, oceny)
                r2 = turniej(populacja, oceny)

                while r2 == r1:
                    r2 = turniej(populacja, oceny)

                zadania_krzyzowania.append(
                    (populacja[r1], populacja[r2], random.getrandbits(64))
                )

            # krzyzowanie 
            dzieci = pula.map(
                krzyzowanie_rownolegle, zadania_krzyzowania, chunksize=25
            )

            # mutacja 
            zadania_mutacji = [
                (dziecko, random.getrandbits(64))
                for dziecko in dzieci
            ]

            dzieci = pula.map(
                mutacja_rownolegla, zadania_mutacji, chunksize=25
            )

            populacja = [elita] + dzieci

    czas = time.perf_counter() - start

    print(f"\nNajlepsza dlugosc trasy: {najlepsza_odleglosc:.2f}")
    print(f"Czas wykonania: {czas:.3f} s")
    print("Najlepsza trasa:")
    print(
        " -> ".join(str(miasto + 1) for miasto in najlepsza_trasa)
        + " -> " + str(najlepsza_trasa[0] + 1)
    )


if __name__ == "__main__":
    print(f"Liczba miast: {LICZBA_MIAST}")
    print(f"Rozmiar populacji: {ROZMIAR_POPULACJI}")
    print(f"Liczba procesow: {LICZBA_PROCESOW}\n")
    algorytm_genetyczny()
