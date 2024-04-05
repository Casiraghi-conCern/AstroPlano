Content associated with AstroPlano.

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

AP_DataRead.py >>> .bin to .txt 

AP_Monitor_Ana.py >>> analisi dati file .txt

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Setup:
    al primo avvio assicurarsi di avere i due file .py 
    e il file requirements.txt 

    - aprire un terminale spostandosi nella cartella dove
        sono contenuti i file e eseguire il comando:
            >   pip install -r requirement.txt
        e attendere l'installazione delle librerie necesarie

    - creare manualmente una cartella chiamata "misure"
        (!ATTENZIONE A RISPETTARE MINUSCOLE E MAIUSCOLE!)

    - al suo interno di essa crearne una per ogni misura col nome
        "AP" seguito dalla data di avvio run nel formato "YYYYMMDD-HHMM"

        es. "AP20221103-1346" per una misura del 03/11/2022 ore 13:46

Avvio programmi:

    - ora è possibile avviare il primo programma e successivamente il secondo seguendo le istruzioni fornite all'avvio indicando a mano la data del run nel formato precedentemente indicato

    - i file generati dal programma saranno automaticamente generati ordinati nella cartella relativa a quella misura 
        "./misure/APYYYYMMDD-HHMM"
