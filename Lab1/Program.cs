using System;
using System.Threading;
using System.Threading.Tasks;

namespace Kopalnia
{
    class Program
    {
        static int zloze = 2000;
        static int magazyn = 0;

        static SemaphoreSlim semaforZloze = new SemaphoreSlim(2, 2);
        static SemaphoreSlim semaforMagazyn = new SemaphoreSlim(1, 1);

        static object blokada = new object();
        static object blokadaKonsoli = new object();

        static bool koniec = false;

        static void Main(string[] args)
        {
            Console.Write("Podaj liczbę górników: ");
            int liczbaGornikow = int.Parse(Console.ReadLine());

            Console.Clear();
            Console.CursorVisible = false;

            Task[] zadania = new Task[liczbaGornikow];

            Task podglad = Task.Run(() => PokazStan());

            for (int i = 0; i < liczbaGornikow; i++)
            {
                int id = i + 1;
                zadania[i] = Task.Run(() => Gornik(id));
            }

            Task.WaitAll(zadania);

            koniec = true;
            podglad.Wait();

            lock (blokadaKonsoli)
            {
                Console.SetCursorPosition(0, liczbaGornikow + 4);
                Console.WriteLine("Koniec symulacji.");
                Console.CursorVisible = true;
            }
        }

        static void Status(int id, string tekst)
        {
            lock (blokadaKonsoli)
            {
                Console.SetCursorPosition(0, id + 2);
                Console.Write($"Górnik {id}: {tekst}".PadRight(60));
            }
        }

        static void PokazStan()
        {
            while (!koniec)
            {
                int stanZloza;
                int stanMagazynu;

                lock (blokada)
                {
                    stanZloza = zloze;
                    stanMagazynu = magazyn;
                }

                lock (blokadaKonsoli)
                {
                    Console.SetCursorPosition(0, 0);
                    Console.Write($"Stan złoża: {stanZloza} jednostek węgla".PadRight(60));

                    Console.SetCursorPosition(0, 1);
                    Console.Write($"Stan magazynu: {stanMagazynu} jednostek węgla".PadRight(60));
                }

                Thread.Sleep(100);
            }

            lock (blokadaKonsoli)
            {
                Console.SetCursorPosition(0, 0);
                Console.Write($"Stan złoża: {zloze} jednostek węgla".PadRight(60));

                Console.SetCursorPosition(0, 1);
                Console.Write($"Stan magazynu: {magazyn} jednostek węgla".PadRight(60));
            }
        }

        static void Gornik(int id)
        {
            while (true)
            {
                Status(id, "Czeka na dostęp do złoża...");

                semaforZloze.Wait();

                int wydobyto = 0;

                lock (blokada)
                {
                    if (zloze == 0)
                    {
                        semaforZloze.Release();
                        break;
                    }
                }

                Status(id, "Wydobywa węgiel...");

                for (int i = 0; i < 200; i++)
                {
                    lock (blokada)
                    {
                        if (zloze == 0)
                            break;

                        zloze--;
                        wydobyto++;
                    }

                    Thread.Sleep(10);
                }

                semaforZloze.Release();

                if (wydobyto == 0)
                    break;

                Status(id, $"Transportuje {wydobyto} jednostek do magazynu...");
                Thread.Sleep(10000);

                Status(id, "Czeka na rozładunek...");
                semaforMagazyn.Wait();

                Status(id, "Rozładowuje węgiel...");

                for (int i = 0; i < wydobyto; i++)
                {
                    Thread.Sleep(10);

                    lock (blokada)
                    {
                        magazyn++;
                    }
                }

                semaforMagazyn.Release();

                Status(id, "Wraca do kopalni...");
                Thread.Sleep(10000);
            }

            Status(id, "Zakończył pracę.");
        }
    }
}
