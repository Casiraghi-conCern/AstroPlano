# variables to be shared across modules
#
real_daq =  False   # False  # per eseguirlo in simulazione mettere falso
real_sensors = False   # False # if you have no sensor set it False

if real_daq:    print('\n Acquisizione reale (non simulata)\n')
else:           print('\n ACQUISIZIONE SIMULATA !!!\n')

mydebug =   True  #False
STARTED =   0  #stato dell'acquisizione
READY   =   1
RUNNING   = 2

# questa classe serve solo a conservare dati comuni a grafica e acquisizione
class  astrodata():
    N_CHAN = 12      # n. canali WB
    N_SiPM = N_CHAN  # n. SiPM
    VERSIONE = 'Aprile 2022'
    # intervallo di tempo in secondi fra 2 correzioni di tensione per variazioni di T
    HV_correct_interval = 900

    Stato = STARTED
    MyGui = None
    guiActive = False  # per evitare di scrivere su finestra inesistente
    scroll    = None    # indirizzo dell'area di scroll della GUI
    link_plot = None

# valori default dei parametri
    configfilepath = "./"
    configfile     = 'AstroPlano.cfg'
    homedir   = './'    # path del logfile e dell'output file, devono coincidere
    log_file  = None
    logf      = None  # file pointer
    outfile   = None
    outfiledefault = 'AP_log_default'
    durata    = 2	    	# durata del run
    time_unit = 0  		    # 0 minuti,  1 ore
    monitpath = homedir     # path e filename del file usato per monitoring
    monitfile = outfiledefault
    MyPipeName  = "AstroPlanoPipe" # pipe per trasmettere comandi a WB
    stop_analisi= False  # per  arrestare lettura file monitoring


#   parametri WB
    leading   = 15  # valore ragionevole di default, uguale per tutti i canali
    trailing  = 25
    pedestal  = 0X3E00  # piedistalli, a priori tutti uguali
    gain      = 0  # 0 basso, 1 alto
    SiPM_HV   = [55.93, 55.9, 55.12, 55.0, 55.65, 55.35, 55.62, 55.84, 55.8, \
             55.61, 55.96, 55.87] # tensioni in Volt
#   tensioni corrette per la temperatura
    SiPM_HV_corr =[-1.0]*N_SiPM
    
# soglia iniziale e finale
    thr_start = [20., 20., 20., 20., 20., 20., 20., 20., 20., 20., 20., 20.]
    thr_stop  = [15., 15., 15., 15., 15., 15., 15., 15., 15., 15., 15., 15.]
	
# sensori  pressione, temperatura, umidita' relativa
    Temperature = None
    Pressure    = None
    RelHumid    = None 
    T_sensors   = [None]*4   #  i 4 sensori di temperatura
	
# Dati per correzioni temperatura    
    Treference = 20.0
    Tempco     = 54.0   # 54 mV/ C
    TempcoFlag = False  # falso -> no correzione
    
#parametri per connessione con WB, non toccare
    ip         = None   # indirizzo IP della WB,  qui 169.254.180.39
    port       = 22
    remoteuser = "root"
    keypath    = "/home/pi/.ssh/id_rsa"
    
    
# funzioni di uso comune

def cleanFilename(nome, ext):
    # se il nome contiene una estensione (.xyz) non faccio nulla, altrimenti 
    # aggiungo ext
    
    if '.' in nome[-4:-1]:  # c'e' un punto tra gli ultimi 4 caratteri?
        return nome         # c'e' una estensione, non faccio nulla
    elif '.' == nome[-1]:   # e' l'ultimo carattere
        return nome + ext
    else:
        return nome + '.' + ext   # aggiungo punto piu' estensione
    
if __name__ == '__main__':   
    nomeprova = cleanFilename('nomedelfile', 'bin')
    print ('%s \n'% nomeprova)
    
    nomeprova = cleanFilename('nomedelfile.', 'bin')
    print ('%s \n'% nomeprova)
    
    nomeprova = cleanFilename('nomedelfile.t', 'bin')
    print ('%s \n'% nomeprova)
   
