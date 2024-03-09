"""
    Programma di controllo per AstroPlano
    Giugno 2020,    agosto 2021, 
    dicembre 2021  Marzo 2022
    Flavio Fontanelli
"""

import time
import astrosettings as A_S 
import AstroSensori 
import AstroPlanoGui_class as gui
from sys import exit
from astro_detector_rp import astro_detector 
V_crit = A_S.astrodata.V_alarm  # tensione critica della batteria per avviare spegnimento controllato 


print ("\nProgramma di controllo per AstroPlano ")
print ("Versione %s Autore: Flavio Fontanelli\n"% A_S.astrodata.VERSIONE)

# creiamo il nome del file per il log del run
timestr = time.strftime("%Y%m%d-%H%M")
A_S.astrodata.log_file  =  A_S.astrodata.homedir +'APlog'+ timestr +'.log' 

#apro un file per scrivere info sulle attivita' in corso
print ("\nApro logfile: %s" % A_S.astrodata.log_file)
try: 
    A_S.astrodata.logf = open(A_S.astrodata.log_file, 'w') 
except:
    print ("il file di output esiste gia' (strano!), rinominalo!\n")
    exit()

    
# creo un nome per l'output file ragionevole e coerente col log file  
A_S.astrodata.outfiledefault = 'AP'+ timestr


if A_S.real_daq and A_S.real_sensors:
    # sensori temperatura e ambientale
    AstroSensori.APLsens()  
#    Tsens = AstroSensori.APLsens.Tsipm_sens(0)
#    print ("Sensore T #0: %5.2f "% Tsens)
    [print ("Sensore T[%d]: %5.2f "% (nn,AstroSensori.APLsens.Tsipm_sens(nn))) for nn in range(4)]
    (t,p,h)= AstroSensori.APLsens.Ambiente()
    print("Sensore ambientale: umid. rel.: {:.1f} %, P: {:.1f} hPa, T: {:.2f} C".format(h, p, t))
    print ("Tensione Batteria: %5.2f "% (AstroSensori.APLsens.V_values(0)))
    print ("Tensione Raspberry : %5.2f "% (AstroSensori.APLsens.V_values(1)))
    print ("Tensione Sensore 1: %5.2f "% (AstroSensori.APLsens.V_values(2)))
    print ("Tensione Sensore 2: %5.2f "% (AstroSensori.APLsens.V_values(3)))   
    if AstroSensori.APLsens.V_values(0) < V_crit: print ("\n***   Attenzione!!!  Batteria quasi Esaurita !!! Avviare acquisizione per iniziare spegnimento controllato ***\n")     
try:
    A_S.astrodata.MyGui= gui.AstroGui()
    A_S.astrodata.guiActive= True   # se gui non attiva scrivo i messaggi con print 
    A_S.astrodata.MyGui.after= None # per fare felice l'interprete
    if A_S.real_sensors:
		# ad intervalli regolari aggiorno sensore ambientale e temperature 
        # se il run e' in corso aggiornero' anche le tensioni dei SiPM
        A_S.astrodata.MyGui.root.after(A_S.astrodata.HV_correct_interval * 1000, \
					gui.Update_sens_HV, A_S.astrodata.MyGui)
    else:   # la chiamiamo spesso (50 s)  per farne il debug
        A_S.astrodata.MyGui.root.after(50000, gui.Update_sens_HV, A_S.astrodata.MyGui) 

    A_S.astrodata.MyGui.root.mainloop() 

finally:
    tempo= time.localtime(time.time())
    print("AstroPlano - fine dell'acquisizione: %s"% time.asctime(tempo))
    # cancelliamo l'aggiornamento delle temperature e tensioni
    # if A_S.astrodata.MyGui.after != None:
    try:
        A_S.astrodata.MyGui.root.after_cancel( A_S.astrodata.MyGui.after)
    except:
        pass
    A_S.guiActive= False
    astro_detector.EndRun()   # per essere sicuri che WB chiuda bene il processo
    AstroSensori.APLsens.chiudi()   # chiudiamo bus I2C
    exit()    # from sys
