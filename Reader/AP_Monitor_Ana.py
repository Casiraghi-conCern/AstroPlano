# -*- coding: utf-8 -*-
"""
Created on 11 gennaio 2022
@author: F. Fontanelli

Classe per leggere il file di output (*.bin)

Formato dati in output:
1) numero sequenziale dell'evento e numero di trigger cioe' numero di SIPM che hanno dato segnale
per ogni trigger:
2) numero sipm, secondi,  nanosecondi, carica  totale (sottratto il piedistallo),
numero dei campioni, per il timing: indice  picco cioe' del massimo, 
indice campionamento dal fit al 50% cioe' costant fraction, 
flag di qualita' =0 e' ok, 1 no fit (per il momento se il fit da' risultati assurdi')
debug =0 niente, =1 dati fondamentali, =2 dettagli, 3 info debug

"""
import matplotlib.pyplot as plt
import math 
import statistics
import datetime
#import matplotlib.ticker as ticker
#from matplotlib import pyplot as plt
from matplotlib.ticker import (MultipleLocator, FormatStrFormatter,
                               AutoMinorLocator)
#######################################################################################################
#Stefano: libreria necessaria per fare grafico se non funziona mgr.canvas.height() e mgr.canvas.width()
#######################################################################################################

#######################################################################################################
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.mlab as mlab
from scipy import stats
from scipy.optimize import curve_fit
from scipy import asarray as ar,exp
from scipy import special as sp
from scipy.stats import moyal
import sys
#import ROOT

import numpy as np
#import pandas as pd


# parametri da settare all'inizio

#inputPath = "../AstroPlano_sep21/"	#path input file
#inputFile = "AP_ven_cfg_old" 		# file corrotto (sipm>11)

fileDate = input("Data acquisizione 'YYYYMMDD-HHMM' : ")
inputFile = "AP" + fileDate
inputPath = "./misure/" + inputFile + "/"     # path input file

#os.mkdir(inputPath + "output")

#inputFile = "20220517-1201"
#inputFile = "20220428-0940"   	    # input file name without AP and extension
#inputFile = "20220321-2128"   	    # input file name without extension
inputlog = "APlog" + fileDate + ".log"


print("Apro File: ", inputFile+".txt", " ", inputlog)
output_path = inputPath         	#idem for output
#output_path = inputPath + "output/"
output_file = inputFile+ "provaPlot" + "_dst.txt"
output_log = inputFile+ "_WSVT.txt"
output_root = inputFile+ "_tree.root"
outmonitor = output_path + "Monitor-AP" +  inputFile + ".pdf"


#numero di eventi da processare (-1 = tutti)
NEVMAX =  -1   # 9999999    

# costanti che potremmo dover cambiare
time_win = 400    # ns,  lunghezza max finestra temporale di un evento
rate_scan = 900     #intervallo di tempo su cui fare la media rate per scan temporale
MyDebug    = 0      # 0 no debug, 1 minimale, 2 esteso, 3 tutto
MyPlot     = 1
PlotMonitor = 1    # 0 no plot, 1 plot si
testsimp_s =0      #modilit� calibrazione sipm Angolari
PlotStop = 0
AngPlot = 0         #0 no distrbuzione angolare, 1 set binari, 2 set alternativo, 3 set ravvicinato sinistra (e 8-10 a sinistra), 4 come tre ma con 8 e 10 a destra 
Decadimento = 0
sciglass = 0

PlotFile    = 0     # 0 no plot, 1 plot su file
N_DUMP_FIRST_EVENTS = 4   # numero degli eventi iniziali che vengono stampati
N_PLOT_EVENTS = 20 # plotta evento desiderato

# altro non cambiare se non sai quello che fai
N_SIPM =12
SAMPLING_TIME =4  # 4 ns periodo di campionamento (f=250 MHz)
baseline =3 # numero dei campionamenti  iniziali da usare, mediando, come piedistallo
Qcharge_flag_port=0 
d_a=1.0
d_g=1.0
t_g_prev=1.0
t_a_prev=1.0
t_s_prev=1.0


plt.ion()

if PlotMonitor:
    import tkinter as tk 
    root = tk.Tk()

if __name__ == "__main__":
    # ------------------------------------------------------------------
    # main program
    print ("\nProgramma di conversione formato dati per AstroPlano.  V2.0")
    print ("Gennaio 2022   - Flavio Fontanelli \n")
    

    #MyData = AP_DataRead(NEVMAX)
    filedati_in = inputPath+inputFile + '.bin'
    filelog_in = inputPath+inputlog
    #MyData.OpenInputFile(filedati_in, filelog_in)
    
    filedati_out = output_path + output_file
    fileWSVT_out = output_path + output_log
    #MyData.OpenOutputFile(filedati_out, fileWSVT_out)
    

    #evento =Evento()
    #last_trigger = Trigger()
 
    ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''    
    '''Leggo il file log per parametri run e WS '''
    ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    voltage=[[],[],[],[],[],[],[],[],[],[],[],[]]
    soglie=[[],[],[],[],[],[],[],[],[],[],[],[]]
    tensione=[[],[],[],[]]
    temperatura=[[],[],[],[]]
    temp_media=[[],[]]
    deltaV=[[],[]]
    pressione=[]
    #tstartRun
    #datetime_orario = datetime.datetime.now()
    tempolog=[]
    log = open(filelog_in, 'r', encoding='utf-8')
    tcount=0
    
    while 1:
        Testo=log.readline()
        #print(Testo)
        if Testo=="":
            break
        if Testo==" ":
            continue
        if Testo=="\n":
            continue
        if Testo.startswith("Fine del run:"):
            break
        '''if Testo.startswith("StartRun:"):
            #leggo ora inizio run'''
            
        if Testo.startswith("Voltages"):
            #leggo tensioni iniziali
            Testo=log.readline()
            for i in range(12):
                voltage[i]=float(Testo.split()[i])
             #print(voltage)
        if Testo.startswith("Vbat"):
            #Testo=log.readline()
            for i in range(4):
                tensione[i].append(float(Testo.split()[i*3+1]))        
                
        if Testo.startswith("Start threshold"):
            #leggo Soglie
            Testo=log.readline()
            for i in range(12):
                soglie[i]=float(Testo.split()[i]) 
            #print(soglie)
        '''if Testo.startswith("Sensori T dei SiPM:"):
            #leggo temperature iniziali
            Testo=log.readline()
            for i in range(4):
                #print(Testo.split())
                temperatura[i].append(float(Testo.split()[i])) 
            #print(temperatura)  
        if Testo.startswith("Sensore temperatura n.:"):
            i = int(Testo.split()[3]) #leggo quarto valore della riga per avere il numero del sensore           
            temperatura[i].append(float(Testo.split()[5])) #leggo il sesto valore per avere al temperatura
        '''    
        if Testo.startswith("T2:"):
            #i = int(Testo.split()[3]) #leggo quarto valore della riga per avere il numero del sensore           
            temperatura[2].append(float(Testo.split()[1])) #leggo il secondo valore per avere al temperatura
            temperatura[3].append(float(Testo.split()[4]))
            deltaV[1].append(float(Testo.split()[14]))
        if Testo.startswith("T0:"):
            #i = int(Testo.split()[3]) #leggo quarto valore della riga per avere il numero del sensore           
            temperatura[0].append(float(Testo.split()[1])) #leggo il secondo valore per avere al temperatura
            temperatura[1].append(float(Testo.split()[4]))            
            
            #leggo temperatura durante run (prossimamente anche pressione)
        #if Testo.startswith("T media :"): #attenzione perchè potrebbe cambiare
            #leggo variazione tensione durante run 
            deltaV[0].append(float(Testo.split()[14]))
            
            for i in range(2):
                Testo=log.readline()
            #datetime_orario = datetime.datetime.strptime(Testo, '%a %b %d %H:%M:%S %Y\n')   
            # %a Giorno abbreviato, %b Mese abbreviato, %d Numero giorno, %H ore in 24-ore, %M minuti, %S secondi, %Y anno in 4 cifre 
            # oppure semplicemente %c
            
            if(tcount==0):
                datetime_orario = datetime.datetime.strptime(Testo, '%a %b %d %H:%M:%S %Y \n')
                print("Tempo inizio Run: ", datetime_orario)
            datetime_orario2 = datetime.datetime.strptime(Testo, '%a %b %d %H:%M:%S %Y \n')
            giorni=((datetime_orario2-datetime_orario).days)*24*60*60 #Converte i giorni in secondi
            delta=((datetime_orario2-datetime_orario).seconds) #converte la differenza di date in secondi
            tempolog.append(round(delta+giorni,2))
            tcount=tcount+1
            
        if Testo.startswith("Pressione:"):
            pressione.append(float(Testo.split()[1]))
    '''for i in range(4):
        print(temperatura[i])
    '''

   
    for t in range((len(tempolog))):
        temp_media[0].append(round((temperatura[0][t]+temperatura[1][t])/2,2))
        temp_media[1].append(round((temperatura[2][t]+temperatura[3][t])/2,2))
        
        #deltaV[0][t]=round(deltaV[0][t]/1000*temp_media[0][t],3)
        #deltaV[1][t]=round(deltaV[1][t]/1000*temp_media[1][t],3)
    if MyDebug > 1:        
        print(tempolog)
        print(temperatura[0])
        print(temperatura[1])
        print(temperatura[2])
        print(temperatura[3])
        print(tensione[0])
        print(tensione[1])
        print(tensione[2])
        print(tensione[3])
        print(temp_media[0])
        print(temp_media[1])
        print(deltaV[0])
        print(deltaV[1])
        #print(deltaV)
        #print(tempo)
    ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''   
    d_a=1
    d_g=1
    t_g_prev=1
    t_a_prev=1
    t_s_prev=1 
    '''
    while MyData.ntot_trigger <  NEVMAX  or NEVMAX <0:      
        # leggo i dati relativi al singolo trigger (un SIPM)
        rc =last_trigger.LeggiTrigger() 
        if rc == None: break  # fine dati (EOF)
        # if MyData.ntot_trigger==77:
        #     print ("trigger: %d"% MyData.ntot_trigger)
        #     last_trigger.PrintTrigger()
        if MyData.ntot_trigger % 10000 == 0: print ("Trigger n. %d"% MyData.ntot_trigger) 
        # if last_trigger.nsamples >126:
        #     print ("\n\n  -- trigger molto lungo %d   --\n\n"% last_trigger.nsamples)
    
        if MyDebug > 1: 
            last_trigger.PrintTrigger()
            
        if last_trigger.frag_flag==0: 
            MyData.ntot_trigger +=1 # contatore totale n. trigger
        else:
            MyData.fragmented += 1  # conteggio trigger frammentati
        evento.CreaEvento(last_trigger)


        # vars(evento.trigger_list[-1])
        # contiamo quali scintillatori hanno dato segnale
        # MyData.total_count_per_sipm = [MyData.total_count_per_sipm[i] + \
        #             evento.scintil_active[i] for i in range(N_SIPM)]
    # MyData.ntot_evt = evento.nevt     
     
    #fine del run
    MyData.CloseAllOutputFile ()
    '''
    ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''    
    '''Leggo il file per produrre i plot di controllo '''
    ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

    prova4 = open(output_path + output_file, "r")
    #aprire nuovo file per dati temperatura e pressione (in progress)
    #Wstation = open(r"C:\Users\User\AP20220224-wsd.txt", "r")'''
    eventi=[''] #inseriamo un valore per far sì che il numero dell'evento coincida con
                    #l'indice inserito di sotto.
    rate=[0,0,0,0,0,0,0,0,0,0,0,0]
    rateLS=[0,0,0,0,0,0,0,0]            
         
    #check=True    #romosso perche mi sono accorto essere inutile

    #Trun = 6; # tempo run espresso in ore
    print("leggo il file Output", output_file)
    iw=0
    while True:
        iw=iw+1;            #sostituisco check con True
        riga = prova4.readline()

        if riga == '':  # ho sostituito riga==False con riga=='' perchè            
            break       # a quanto pare è una stringa vuota e non una variabile booleana
        elif riga == '\n':
            continue
        # '''  #aggiungere una condizione per leggere la data che verra messa nel file  (probabilmente come primo dato)
        #   if riga == 'Tempo inizio Run:'
        #      testo = riga.split()
        #       tstart = datetime.datetime.strptime(testo, '%c\n')
          
        n_trigger = riga.split() #separa numero evento dal numero di trigger

        evento_n = []
        #print("evento n. ", n_trigger[0])
        for i in range(int(n_trigger[1])):
            riga = prova4.readline()
            #if i<10: print(riga)
            riga_vect = riga.split()   #separa gli elementi di ogni trigger (n. SIM/
                                           #tempo in sec ecc...)

            for j in range(len(riga_vect)):     # sarà sempre 9
                riga_vect[j] = float(riga_vect[j])    #creiamo la terza dimensione
            evento_n.append(riga_vect)   #creiamo la seconda dimensione
            #if i<10: print(riga_vect)
        eventi.append(evento_n)   #creiamo la prima dimensione   
        
        if(NEVMAX>0 and iw>NEVMAX):
          print("i= ", iw) 
          break        
    del evento_n      
    #print(eventi[1])
    print("Ultimo evento n. ", n_trigger[0])   
    tempos =[[],[],[],[],[],[],[],[],[],[],[],[]]
    carica = [[],[],[],[],[],[],[],[],[],[],[],[]]
    caricaO =[[]]
    carica_barra_L = [[],[],[],[],[]]
    tcf = [[],[],[],[],[],[],[],[],[],[],[],[]]
    last_event=len(eventi)-1        
    #Trun = eventi[last_event][0][1]-eventi[1][0][1]+(eventi[last_event][0][2]-eventi[1][0][2])/1e9
    #nuova definizione del formato dati che comprende anche anno e giorno
    print("Calcolo durata Run") 
    Trun = (eventi[last_event][0][1]-eventi[1][0][1])*3.154e+7+(eventi[last_event][0][2]-eventi[1][0][2])*86400+eventi[last_event][0][3]-eventi[1][0][3]+(eventi[last_event][0][4]-eventi[1][0][4])/1e9
    '''
        if(eventi[last_event][0][1]<eventi[1][0][1]):#nel caso il contatore dei secondi si resetti durante il run
            for i in range(len(eventi)):
                j=i-1
                if(j!=-1):
                    if(eventi[i][0][1]==0 and eventi[j][0][1]>eventi[i][0][1]): Trun = eventi[j][0][1]-eventi[1][0][1]+eventi[last_event][0][1]+(eventi[j][0][2]-eventi[1][0][2]+eventi[last_event][0][2])/1e9
    '''       
    #SGpe=[0.04,0.06,0.028,0.031,0.042,0.026,0.037,0.139,0.038,1,1,1]
    SGpe=[1,1,1,1,1,1,1,1,1,1,1,1]    
    #print("Tempo totale Run: ", Trun)  
    c=0;
    for i in range (len(eventi)):
        for j in range (len(eventi[i])):
          if (eventi[i][j][5]>0):
            channel = int(eventi[i][j][0])
            valore = rate[channel]
            #rate[channel] =  valore + 1/(Trun*60*60)
            #t=eventi[i][j][3]*1e9+eventi[i][j][4]-(eventi[1][0][3]*1e9+eventi[1][0][4])
            #tempos[channel].append(t)
            if(eventi[i][j][5]>1000 and sciglass==1): carica[channel].append(eventi[i][j][5]/10000/1.2/SGpe[channel])
            if(sciglass>1 ): carica[channel].append(eventi[i][j][5]/10000*1.1)            
            if(sciglass==0): 
              carica[channel].append(eventi[i][j][5]/10000)
              #if eventi[i][j][5] > 4 :
              if eventi[i][j][5] > 4 and eventi[i][j][6]>150:               
                #caricaO[channel].append(eventi[i][j][5])  
                c=c+1        
    print("eventi filtrati: ", c) 
    print("Disegno Multiplot carica singola")   
        #fig, ax = plt.subplots(nrows=3, ncols=4, figsize=(18, 5))
    ''' for i in range(4):
            plt.subplot(1, 2, 1)
            n, bins, patches = plt.hist(carica[i], 60, density=1, facecolor='green', alpha=0.75)
            ax[0,i].plot()
            #ax[0,i].hist(carica[i], 60, density=1, facecolor='green', alpha=0.75)
        for i in range(4):
            j=i+4
            n, bins, patches = plt.hist(carica[j], 60, density=1, facecolor='green', alpha=0.75)
            ax[1,i].plot()
            #ax[1,i].hist(carica[j], 60, density=1, facecolor='green', alpha=0.75) '''           
 
        
    if PlotMonitor==1:    
        #rate=[0,0,0,0,0,0,0,0,0,0,0,0]
        #rateLS=[0,0,0,0,0,0,0,0]   
        '''Calcolo Coincidenze LS'''
        print("calcolo coincidenze LS")
        caricaLS = [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]]
        #0-018,1-018,8-018, 0-019, 1-019, 9-019
        carica_barra_LS = [[],[],[],[],[],[],[],[],[],[]]
        carica_barra_LL = [[],[],[],[],[]]
        carica_barra_LLd = [[],[],[],[],[]]
        caricaSS = [[],[],[],[],[]]
        #8-8_10,10-8_10,9-9_11,11-9_11
        caricaSSd = [[],[],[],[],[]]
        tempoG=[[],[],[],[],[],[],[],[]]
        tempoGL=[[],[]]
        tempoGS=[[],[]]
        #8-8_11,11-8_11,9-9_10,10-9_10
        ind=0
        ind2=1 
        ind3=2
        indt=[rate_scan,rate_scan,rate_scan,rate_scan,rate_scan,rate_scan,rate_scan,rate_scan]
        indL=[rate_scan,rate_scan]
        indS=[rate_scan,rate_scan]
        tst=[0,0,0,0,0,0,0,0] 
        tstm=[0,0,0,0,0,0,0,0] 
        tstL=[0,0] 
        tstlm=[0,0] 
        tstS=[0,0] 
        tstsm=[0,0] 
        s3=0
        s2=0
        s4=0
        countLS=[0,0,0,0,0,0,0,0] 
        #"0_1c8", "0_1c9", "2_3c8","2_3c9", "4_5c10","4_5c11", "6_7c10", "6_7c11"
        countLS_t=[[],[],[],[],[],[],[],[]]
        countLS_t_err=[[],[],[],[],[],[],[],[]]
        countLL_t=[[],[]]
        countLL_t_err=[[],[]]
        countSS_t=[[],[]]
        countSS_t_err=[[],[]]
        countLL=[0,0]
        #0_1c4_5, 2_3c6_7
        countSS=[0,0]
        #8_10,9_11
        countLLd=[0,0]
        #0_1c6_7, 2_3c4_5
        countSSd=[0,0]
        #8_11,9_10
        for s in range(4):
            #print(s)
            s3=s2+1
            if (s==0):s3=0
            s2=s3+1
            c=0 
            c1=0
            
            
            for c in range(2):            
                if(s3<4): c1=8+c
                if(s3>3): c1=10+c
                s4=s3+c
                s5=s3+4
                s6=s2+4
                s7=s3+6
                s8=s2+6
                s9=s3+2
                s10=s2+2
                s11=s3+1
                for i in range (len(eventi)):
                    for j in range(len(eventi[i])):
                        if (eventi[i][j][0] == c1 and eventi[i][j][9]!=1): # cerco primo canale corto
                            for l in range(len(eventi[i])):
                                if(c==0):
                                    if (l!=j and eventi[i][l][0] == c1+2 and eventi[i][l][0]>7 and eventi[i][l][9]!=1):#coinc 8_10
                                    
                                        caricaSS[0].append(eventi[i][j][5]/10000)
                                        caricaSS[1].append(eventi[i][l][5]/10000)
                                        
                                        countSS[0]=countSS[0]+1/Trun
                                        if((eventi[i][j][3]-eventi[1][0][3])>indS[0]):
                                            indS[0]=indS[0]+rate_scan
                                            tstS[0]=countSS[0]*Trun/rate_scan-tstsm[0]
                                            countSS_t[0].append(tstS[0])
                                            countSS_t_err[0].append(math.sqrt(tstS[0]/rate_scan))
                                            tstsm[0]=countSS[0]*Trun/rate_scan                                        
                                    if (l!=j and eventi[i][l][0] == c1+3 and eventi[i][l][0]>7 and eventi[i][l][9]!=1):#coinc 8_11
                                        caricaSSd[0].append(eventi[i][j][5]/10000)
                                        caricaSSd[1].append(eventi[i][l][5]/10000)   
                                        countSSd[0]=countSSd[0]+1/Trun
                                if(c==1):
                                    if (l!=j and eventi[i][l][0] == c1+2 and eventi[i][l][0]>7 and eventi[i][l][9]!=1):#coinc 9_11
                                    
                                        caricaSS[2].append(eventi[i][j][5]/10000)
                                        caricaSS[3].append(eventi[i][l][5]/10000)
                                        countSS[1]=countSS[1]+1/Trun
                                        if((eventi[i][j][3]-eventi[1][0][3])>indS[1]):
                                            indS[1]=indS[1]+rate_scan
                                            tstS[1]=countSS[1]*Trun/rate_scan-tstsm[1]
                                            countSS_t[1].append(tstS[1])
                                            countSS_t_err[1].append(math.sqrt(tstS[1]/rate_scan))
                                            tstsm[1]=countSS[1]*Trun/rate_scan                                          
                                    if (l!=j and eventi[i][l][0] == c1+1 and eventi[i][l][0]>7 and eventi[i][l][9]!=1):#coinc 9_10
                                        caricaSSd[2].append(eventi[i][j][5]/10000)
                                        caricaSSd[3].append(eventi[i][l][5]/10000)   
                                        countSSd[1]=countSSd[1]+1/Trun                                       
                    if (len(eventi[i])>2): # cerco eventi con più di due sipm (coincidenza LS sono da almeno 3 e le LL almeno 4)
                        for j in range(len(eventi[i])):  # lunghezza evento
                            if (eventi[i][j][0] == s3 and eventi[i][j][9]!=1): # cerco primo canale lungo
                                for l in range(len(eventi[i])): 
                                    if (l!=j and eventi[i][l][0] == s2 and eventi[i][l][9]!=1): #cerco negli altri eventi quelli del canale consecutivo per coincidenza destra sinistra
                                        if(c==0): carica_barra_L[s].append(math.sqrt(eventi[i][j][5]/10000*eventi[i][l][5]/10000)) #carica barre lunghe
                                        for p in range(len(eventi[i])):
                                            #print(s3," ", s2, " ", s5," ", s6," ", s7, " ", s8, " ", s9, " ", s10, " ")
                                            if (p!=j and p!=l and eventi[i][p][0] == s5 and s5<8 and eventi[i][p][9]!=1):
                                                for h in range(len(eventi[i])):
                                                    if (h!=j and h!=l and eventi[i][h][0] == s6 and s6<8 and eventi[i][h][9]!=1):
                                                        if(c==0 and s3==0 and s5==4):
                                                            countLL[0]=countLL[0]+1/Trun
                                                            if((eventi[i][j][3]-eventi[1][0][3])>indL[0]):
                                                                indL[0]=indL[0]+rate_scan
                                                                tstL[0]=countLL[0]*Trun/rate_scan-tstlm[0]
                                                                countLL_t[0].append(tstL[0])
                                                                countLL_t_err[0].append(math.sqrt(tstL[0]/rate_scan))
                                                                tstlm[0]=countLL[0]*Trun/rate_scan                                                          
                                                        if(c==0 and s3==2 and s5==6):
                                                            countLL[1]=countLL[1]+1/Trun
                                                            if((eventi[i][j][3]-eventi[1][0][3])>indL[1]):
                                                                indL[1]=indL[1]+rate_scan
                                                                tstL[1]=countLL[1]*Trun/rate_scan-tstlm[1]
                                                                countLL_t[1].append(tstL[1])
                                                                countLL_t_err[1].append(math.sqrt(tstL[1]/rate_scan))
                                                                tstlm[1]=countLL[1]*Trun/rate_scan                                                            
                                                        if(c==0 and s3<4): carica_barra_LL[s3].append(math.sqrt(eventi[i][j][5]/10000*eventi[i][l][5]/10000))
                                                        if(c==0 and s3<4): carica_barra_LL[s11].append(math.sqrt(eventi[i][p][5]/10000*eventi[i][h][5]/10000))#carica barre LL
                                            if (p!=j and p!=l and eventi[i][p][0] == s7 and s7<8 or eventi[i][p][0] == s9 and s9<8 and s9>3 and eventi[i][p][9]!=1):
                                                for h in range(len(eventi[i])):
                                                    
                                                    if (h!=j and h!=l and eventi[i][h][0] == s8 and s8<8 or eventi[i][h][0] == s10 and s10<8 and s10>4 and eventi[i][h][9]!=1):
                                                        
                                                        if(c==0 and s3==0 and s7==6):countLLd[0]=countLLd[0]+1/Trun
                                                        if(c==0 and s3==2 and s9==4):countLLd[1]=countLLd[1]+1/Trun
                                                        if(c==0 and s3<4): carica_barra_LLd[s3].append(math.sqrt(eventi[i][j][5]/10000*eventi[i][l][5]/10000))
                                                        if(c==0 and s3<4): carica_barra_LLd[s11].append(math.sqrt(eventi[i][p][5]/10000*eventi[i][h][5]/10000))#carica barre LLd        
                                            if (p!=j and p!=l and eventi[i][p][0] == c1 and eventi[i][p][9]!=1): # cerco coincidenza con corto giusto
                                                caricaLS[ind].append(eventi[i][j][5]/10000)
                                                caricaLS[ind2].append(eventi[i][l][5]/10000)
                                                caricaLS[ind3].append(eventi[i][p][5]/10000) 
                                                carica_barra_LS[s4].append(math.sqrt(eventi[i][j][5]/10000*eventi[i][l][5]/10000)) #carica barre LS
                                                countLS[s4]=countLS[s4]+1/Trun
                                                if((eventi[i][j][3]-eventi[1][0][3])>indt[s4]):
                                                    indt[s4]=indt[s4]+rate_scan
                                                    tst[s4]=countLS[s4]*Trun/rate_scan-tstm[s4]
                                                    countLS_t[s4].append(tst[s4])
                                                    countLS_t_err[s4].append(math.sqrt(tst[s4]/rate_scan))
                                                    tstm[s4]=countLS[s4]*Trun/rate_scan
                                                '''for tin in range(int(Trun/300)):
                                                    indt=tin+300
                                                    tst[s4]=0
                                                    if((eventi[i][j][1]-eventi[1][0][1])<tin):
                                                        tst[s4]=tst[s4]+1/300
                                                        countLS_t[s4].append(tst[s4])'''
                                                         
                                                    
                                '''for l in range(len(eventi[i])): 
                                    if (l!=j and eventi[i][l][0] == 1): #cerco negli altri eventi quelli con canale 1 per coincidenza destra sinistra
                                        for p in range(len(eventi[i])):
                                            if (p!=j and p!=l and eventi[i][p][0] == 8): #cerco coincidenza con canale 8
                                                # if (eventi[i][0][0] == 1 or  eventi[i][1][0] == 1 or  eventi[i][2][0] == 1 or  eventi[i][3][0] == 1): 
                                                #  if (eventi[i][0][0] == 8 or  eventi[i][1][0] == 8 or  eventi[i][2][0] == 8 or  eventi[i][3][0] == 8):  
                                                rateLS[0] = rateLS[0]+1/(Trun*60*60)
                                                t0.append(eventi[i][j][6])
                                                c0.append(eventi[i][j][3]/1000)    '''
                

                ind=ind+3
                ind2=ind2+3
                ind3=ind3+3
        #print('Stampo vettore rate tempo: ') 
        #print(countLS_t)
        '''Calcolo coincidenze Angoli''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
        1 XXXXXXXXXXXXXXXXXX 0
           X              X           PIANO SUPERIORE
           X              X
        3 XXXXXXXXXXXXXXXXXX 2
           X              X
           8              9
       
        7 XXXXXXXXXXXXXXXXXX 6
           X  X  X  X  X  X           PIANO INFERIORE
           X  X  X  X  X  X
        5 XXXXXXXXXXXXXXXXXX 4
           X  X  X  X  X  X
           10 0b 1b 2b 3b 11
        '''
        countAng=[0,0,0,0,0,0] 
        countAng_err=[0,0,0,0,0,0]
        countSS_ref=[0,0]
        countSS_test=[0,0,0,0]
        #calib=[0.9990592306897463, 0.983787871943739, 0.65868146882135, 0.6839139183857759]#calibrazioni con treshold 15 mV
        calib=[1.0314053113413315, 1.0046311906735867, 0.6538601266444812, 0.6714588464092348]#calibrazioni con treshold 10 mV
        
        ##Set Binari
        if AngPlot==1:
            Ang=[0,42.3,59.9,67.8,73.0,76.5]        
            Ang_err=[12.8,6.35,3.0,1.8,1.1,0.7]
        ##Set Alternativo
        if AngPlot==2:
            Ang=[0,24.4,51.8,71.0,75.0,76.5]        
            Ang_err=[12.8,9.9,4.5,1.3,0.8,0.7]
        ##Set Ravvicinato
        if AngPlot>2:
            Ang=[0,24.4,42.3,51.8,59.9,76.5]        
            Ang_err=[12.8,9.9,6.35,4.5,3.0,0.7]            
        
        if AngPlot>0:
            print("calcolo Distribuzione angolare")
            for i in range (len(eventi)):
                for j in range(len(eventi[i])):
                    if AngPlot<3:
                        if (eventi[i][j][0] == 8 and eventi[i][j][9]!=1): # cerco primo canale corto
                            for l in range(len(eventi[i])):
                                if (l!=j and eventi[i][l][0] == 10 and eventi[i][l][9]!=1): countAng[0]=countAng[0]+1/Trun
                                if (l!=j and eventi[i][l][0] == 0 and eventi[i][l][9]!=1): countAng[1]=countAng[1]+1/Trun/calib[0]
                                if (l!=j and eventi[i][l][0] == 1 and eventi[i][l][9]!=1): countAng[2]=countAng[2]+1/Trun/calib[1]
                                if (l!=j and eventi[i][l][0] == 2 and eventi[i][l][9]!=1): countAng[3]=countAng[3]+1/Trun/calib[2]
                                if (l!=j and eventi[i][l][0] == 3 and eventi[i][l][9]!=1): countAng[4]=countAng[4]+1/Trun/calib[3]
                                if (l!=j and eventi[i][l][0] == 11 and eventi[i][l][9]!=1): countAng[5]=countAng[5]+1/Trun
                    if AngPlot==3:
                        if (eventi[i][j][0] == 8 and eventi[i][j][9]!=1): # cerco primo canale corto
                            for l in range(len(eventi[i])):
                                if (l!=j and eventi[i][l][0] == 10 and eventi[i][l][9]!=1): countAng[0]=countAng[0]+1/Trun
                                if (l!=j and eventi[i][l][0] == 0 and eventi[i][l][9]!=1): countAng[1]=countAng[1]+1/Trun/calib[0]
                                if (l!=j and eventi[i][l][0] == 1 and eventi[i][l][9]!=1): countAng[2]=countAng[2]+1/Trun/calib[1]
                                if (l!=j and eventi[i][l][0] == 2 and eventi[i][l][9]!=1): countAng[3]=countAng[3]+1/Trun/calib[2]
                                if (l!=j and eventi[i][l][0] == 3 and eventi[i][l][9]!=1): countAng[4]=countAng[4]+1/Trun/calib[3]
                                if (l!=j and eventi[i][l][0] == 11 and eventi[i][l][9]!=1): countAng[5]=countAng[5]+1/Trun  
                                '''                                          
                    if AngPlot==3:    
                        if (eventi[i][j][0] == 8 and eventi[i][j][9]!=1): # cerco primo canale corto
                            for l in range(len(eventi[i])):
                                if (l!=j and eventi[i][l][0] == 10 and eventi[i][l][9]!=1): countAng[0]=countAng[0]+1/Trun
                                if (l!=j and eventi[i][l][0] == 0 and eventi[i][l][9]!=1): countAng[4]=countAng[4]+1/Trun/calib[3]
                                if (l!=j and eventi[i][l][0] == 1 and eventi[i][l][9]!=1): countAng[3]=countAng[3]+1/Trun/calib[2]
                                if (l!=j and eventi[i][l][0] == 2 and eventi[i][l][9]!=1): countAng[2]=countAng[2]+1/Trun/calib[1]
                                if (l!=j and eventi[i][l][0] == 3 and eventi[i][l][9]!=1): countAng[1]=countAng[1]+1/Trun/calib[0]
                                if (l!=j and eventi[i][l][0] == 11 and eventi[i][l][9]!=1): countAng[5]=countAng[5]+1/Trun
                                '''
                    if AngPlot==4:    
                        if (eventi[i][j][0] == 9 and eventi[i][j][9]!=1): # cerco primo canale corto
                            for l in range(len(eventi[i])):
                                if (l!=j and eventi[i][l][0] == 10 and eventi[i][l][9]!=1): countAng[5]=countAng[5]+1/Trun
                                if (l!=j and eventi[i][l][0] == 0 and eventi[i][l][9]!=1): countAng[1]=countAng[1]+1/Trun/calib[0]
                                if (l!=j and eventi[i][l][0] == 1 and eventi[i][l][9]!=1): countAng[2]=countAng[2]+1/Trun/calib[1]
                                if (l!=j and eventi[i][l][0] == 2 and eventi[i][l][9]!=1): countAng[3]=countAng[3]+1/Trun/calib[2]
                                if (l!=j and eventi[i][l][0] == 3 and eventi[i][l][9]!=1): countAng[4]=countAng[4]+1/Trun/calib[3]
                                if (l!=j and eventi[i][l][0] == 11 and eventi[i][l][9]!=1): countAng[0]=countAng[0]+1/Trun                                
        if testsimp_s == 1 :
            print("calibrazione sipm misura angolare")
            for i in range (len(eventi)):
                for j in range(len(eventi[i])):
                    if (eventi[i][j][0] == 8 and eventi[i][j][9]!=1): # cerco primo canale corto
                        #print("trovato evento su sipm 8")
                        for l in range(len(eventi[i])):
                            if (l!=j and eventi[i][l][0] == 10 and eventi[i][l][9]!=1): countSS_ref[0]=countSS_ref[0]+1/Trun
                            if (l!=j and eventi[i][l][0] == 1 and eventi[i][l][9]!=1): countSS_test[1]=countSS_test[1]+1/Trun
                            if (l!=j and eventi[i][l][0] == 3 and eventi[i][l][9]!=1): countSS_test[3]=countSS_test[3]+1/Trun
                    if (eventi[i][j][0] == 9 and eventi[i][j][9]!=1): # cerco primo canale corto
                        #print("trovato evento su sipm 9")
                        for l in range(len(eventi[i])):
                            if (l!=j and eventi[i][l][0] == 11 and eventi[i][l][9]!=1): countSS_ref[1]=countSS_ref[1]+1/Trun
                            if (l!=j and eventi[i][l][0] == 0 and eventi[i][l][9]!=1): countSS_test[0]=countSS_test[0]+1/Trun
                            if (l!=j and eventi[i][l][0] == 2 and eventi[i][l][9]!=1): countSS_test[2]=countSS_test[2]+1/Trun
        
        ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    dec=0
    index=0
    refj=0
    refi=0
    time_dec=[]
    time_d_cal=0
    g=0
    
    if Decadimento>0:
        print("calcolo tempi decadimento")
        #print(eventi[62])
            
        for i in range (len(eventi)):
            #if(i<20):
            #print(i, j, refi, refj)
                #print(i, eventi[i])
            if (dec==0):
                for j in range(len(eventi[i])):
                    if ((eventi[i][j][0] == 1 or eventi[i][j][0] == 0) and eventi[i][j][9]!=1):
                        #for g in range(len(eventi[i])):
                         #   if (j!=g and eventi[i][g][0] == 0 and eventi[i][g][9]!=1):# cerco hit su primo piano
                                #print(i)
                        for l in range(len(eventi[i])):
                                if (l!=j and l!=g and (eventi[i][l][0] == 2 or eventi[i][l][0] == 3) and eventi[i][l][9]!=1): # cerco hit su secondo piano
                                    for h in range(len(eventi[i])):
                                        if (h!=j and h!=l and h!=g and (eventi[i][h][0] == 4 or eventi[i][h][0] == 5) and eventi[i][h][9]!=1): 
                                            dec=0 # cerco hit su terzo piano piano
                                            continue
                                        if (h!=j and h!=l and h!=g and eventi[i][h][0] != 4 and eventi[i][h][0] != 5 and eventi[i][h][9]!=1): 
                                            dec=1
                                            refj=l
                                            refi=i

                                        
            if(dec==1):                         
                for j in range(len(eventi[i])):
                    if (i!=refi  and (eventi[i][j][0] == 2 or eventi[i][j][0] == 3) and eventi[i][j][4]>eventi[refi][refj][4] and eventi[i][j][9]!=1): # cerco hit su secondo piano in evento sucessivo    
                        time_d_cal=((eventi[i][j][1]-eventi[refi][refj][1])*3.154e+7+(eventi[i][j][2]-eventi[refi][refj][2])*86400+eventi[i][j][3]-eventi[refi][refj][3]+(eventi[i][j][4]-eventi[refi][refj][4])/1e9)*1e3

                        for g in range(len(eventi[i])):
                            if (j!=g and eventi[i][g][0] != 5 or eventi[i][g][0] != 4 and eventi[i][g][9]!=1):# cerco hit su primo piano
                           
                                '''if(i<100):
                                print(i, j, refi, refj)
                                print(eventi[i][j])
                                print(eventi[refi][refj])
                                print(eventi[i][j][4], eventi[refi][refj][4])'''
                                
                                if (time_d_cal>0.004):
                                    time_dec.append(time_d_cal)
                                dec=0
                                index=index+1
                                refi=i
                                #print(time_dec)
                                continue
                            
        
    '''matrice''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''' 
               
    contRC=0
    #########################
    #        Plastica       #
    #########################
    #       #       #       #
    #       #       #       #
    #       #       #       #
    #########################
    #       #       #       #
    #       #       #       #
    #       #       #       #
    #########################
    #       #       #       #
    #       #       #       #
    #       #       #       #
    #########################
    #        Plastica       #
    #########################
    
    
    if sciglass==0:
        caricaCoin = [[],[],[],[],[],[],[],[],[],[],[],[]]
        caricaCoin3 = [[],[],[],[],[],[],[],[],[],[],[],[]]
        Coinc2 = [0,0,0,0,0,0,0,0,0,0,0,0]
        Coinc3 = [0,0,0,0,0,0,0,0,0,0,0,0]
        
        print("Glass Matrix analisys")
        #print(eventi[62])
            
        for i in range (len(eventi)):
            #if i<10: print(len(eventi[i]), i)
            countriemp = 0
            countriemp1 = 0
            
            countCoinc = 0
            countCoinc3 = 0
            #if(i<20):
            #print(i, j, refi, refj)
                #print(i, eventi[i])    
            for j in range(len(eventi[i])):
                #if (countriemp ==1): break
                if (eventi[i][j][0] == 9 or eventi[i][j][0] == 10 and eventi[i][j][9]!=1 and countriemp == 0 and countriemp1 == 0):#cerco un evento da una delle plastiche
                    for l in range(len(eventi[i])):
                       
                        if (l!=j and (eventi[i][l][0] != 9 or eventi[i][l][0] != 10) and eventi[i][l][9]!=1 and eventi[i][l][0] != eventi[i][j][0] and countriemp == 0 and countriemp1 == 0): #chiedo che non ci sia coincidenza barre plastica
                        
                        #if (l!=j and (eventi[i][l][0] == 9 or eventi[i][l][0] == 11) and eventi[i][l][9]!=1 and eventi[i][l][0] != eventi[i][j][0] and countriemp == 0 and countriemp1 == 0): #chiedo coincidenza barre plastica
                            for h in range(len(eventi[i])):
                                if (h!=j and h!=l and eventi[i][h][0] != 9 and eventi[i][h][0] != 10 and eventi[i][h][9]!=1): # chiedo coincidenza con un vetro o plastica corta
                                    if(countriemp == 0):# escludo coincidenze con se stessi
                                        channel1 = int(eventi[i][j][0])
                                        channel2 = int(eventi[i][l][0])
                                
                                        caricaCoin[channel1].append(eventi[i][j][5]/10000)
                                        caricaCoin[channel2].append(eventi[i][l][5]/10000)
                                        Coinc2[channel1]=Coinc2[channel1]+1
                                        Coinc2[channel2]=Coinc2[channel2]+1
                                    
                                    channel3 = int(eventi[i][h][0])
                                    if(eventi[i][h][5]>1000 and sciglass==1): caricaCoin[channel3].append(eventi[i][h][5]/10000/1.2/SGpe[channel3])
                                    if(sciglass>1): caricaCoin[channel3].append(eventi[i][h][5]/10000)
                                    Coinc2[channel3]=Coinc2[channel3]+1
                                    #print(countriemp, channel3, countCoinc)
                                    countriemp = 1
                                if (h!=j and h!=l and eventi[i][h][0] == 10 and eventi[i][h][9]!=1):  #chiedo coincidenza barretta corta
                                    for p in range(len(eventi[i])):
                                        if (p!=h and p!=j and p!=l and eventi[i][p][0] != 9 and eventi[i][p][0] != 10 and eventi[i][p][0] != 11 and eventi[i][p][9]!=1):
                                            #chiedo coincidenza con un vetro
                                            if(countriemp1 == 0):
                                                channel1 = int(eventi[i][j][0])
                                                channel2 = int(eventi[i][l][0])
                                                channel4 = int(eventi[i][h][0])
                                            
                                
                                                caricaCoin3[channel1].append(eventi[i][j][5]/10000)
                                                caricaCoin3[channel2].append(eventi[i][l][5]/10000)
                                                caricaCoin3[channel4].append(eventi[i][h][5]/10000)
                                                Coinc3[channel1]=Coinc3[channel1]+1
                                                Coinc3[channel2]=Coinc3[channel2]+1
                                                Coinc3[channel4]=Coinc3[channel4]+1
                                    
                                            channel3 = int(eventi[i][p][0])
                                            if(eventi[i][p][5]>1000 and sciglass==1): caricaCoin3[channel3].append(eventi[i][p][5]/10000/1.2/SGpe[channel3])
                                            if(sciglass>1): caricaCoin3[channel3].append(eventi[i][p][5]/10000)
                                            Coinc3[channel3]=Coinc3[channel3]+1
                                            countCoinc3=countCoinc3+1
                                            #print(countriemp, channel3, countCoinc)
                                            countriemp1 = 1
                                    
            #if(countCoinc>0): MultiCoin.append(countCoinc)
    #print(MultiCoin)
    ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    if sciglass==2:
        caricaCoin = [[],[],[],[],[],[],[],[],[],[],[],[]]
        caricaCoin3 = [[],[],[],[],[],[],[],[],[],[],[],[]]
        Coinc2 = [0,0,0,0,0,0,0,0,0,0,0,0]
        Coinc3 = [0,0,0,0,0,0,0,0,0,0,0,0]
        
        print("Glass Matrix analisys")
        #print(eventi[62])
            
        for i in range (len(eventi)):
            #if i<10: print(len(eventi[i]), i)
            countriemp = 0
            countriemp1 = 0
            
            countCoinc = 0
            countCoinc3 = 0
            #if(i<20):
            #print(i, j, refi, refj)
                #print(i, eventi[i])    
            for j in range(len(eventi[i])):
                if (eventi[i][j][0] == 0 or eventi[i][j][0] == 1  or eventi[i][j][0] == 2):
                    for l in range(len(eventi[i])):
                        if (l!=j and eventi[i][l][0] == 3 or eventi[i][l][0] == 4  or eventi[i][l][0] == 5):
                            for h in range(len(eventi[i])):
                                if (h!=j and h!=l and eventi[i][h][0] == 6 or eventi[i][h][0] == 7  or eventi[i][h][0] == 8): # chiedo coincidenza con un vetro o plastica corta
                                    channel1 = int(eventi[i][j][0])
                                    channel2 = int(eventi[i][l][0])
                                
                                    if(eventi[i][j][5]>1):caricaCoin[channel1].append(eventi[i][j][5]/10000)
                                    if(eventi[i][l][5]>1):caricaCoin[channel2].append(eventi[i][l][5]/10000)
                                    #Coinc2[channel1]=Coinc2[channel1]+1
                                    #Coinc2[channel2]=Coinc2[channel2]+1
                                    
                                    channel3 = int(eventi[i][h][0])
                                    if(eventi[i][h][5]>1):caricaCoin[channel3].append(eventi[i][h][5]/10000)
                          
    ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''        
    if sciglass==3:
        caricaCoin = [[],[],[],[],[],[],[],[],[],[],[],[]]
        caricaCoin3 = [[],[],[],[],[],[],[],[],[],[],[],[]]
        Coinc2 = [0,0,0,0,0,0,0,0,0,0,0,0]
        Coinc3 = [0,0,0,0,0,0,0,0,0,0,0,0]
        
        print("Glass Matrix analisys")
        #print(eventi[62])
        hc_sipm0=np.ROOT.TH1D("hc_sipm0-g9","hc_sipm0-g9",100,0,3);
        hc_sipm1=np.ROOT.TH1D("hc_sipm1-g10","hc_sipm1-g10",100,0,3);
        hc_sipm2=np.ROOT.TH1D("hc_sipm2-g11","hc_sipm2-g11",100,0,3);
        hc_sipm3=np.ROOT.TH1D("hc_sipm3-g13","hc_sipm3-g13",100,0,3);
        hc_sipm4=np.ROOT.TH1D("hc_sipm4-g14","hc_sipm4-g14",100,0,3);
        hc_sipm5=np.ROOT.TH1D("hc_sipm5-g15","hc_sipm5-g15",100,0,3);
        hc_sipm6=np.ROOT.TH1D("hc_sipm6-g16","hc_sipm6-g16",100,0,3);
        hc_sipm7=np.ROOT.TH1D("hc_sipm7-g18","hc_sipm7-g18",100,0,3);
        hc_sipm8=np.ROOT.TH1D("hc_sipm8-g19","hc_sipm8-g19",100,0,3);        
        for i in range (len(eventi)):
            #if i<10: print(len(eventi[i]), i)
            countriemp = 0
            countriemp1 = 0
            
            countCoinc = 0
            countCoinc3 = 0
            #if(i<20):
            #print(i, j, refi, refj)
                #print(i, eventi[i])
            for n in range (len(eventi[i])):
                if (eventi[i][n][0] == 9 or eventi[i][n][0] == 10 and eventi[i][n][9]!=1):#cerco un evento in plastica sopra
                    #for m in range (len(eventi[i])):
                        #if (m!=n and eventi[i][m][0] == 10 and eventi[i][m][9]!=1):#cerco un evento in plastica sopra

                            for j in range(len(eventi[i])):
                                if (j!=n and eventi[i][j][0] != 9 and eventi[i][j][0] != 10  and eventi[i][j][0] != 11):

                                                
                                    #if(eventi[i][j][5]>1):caricaCoin[channel1].append(eventi[i][j][5]/10000)
                                    #if(eventi[i][l][5]>1):caricaCoin[channel2].append(eventi[i][l][5]/10000)

                                                    
                                    channel3 = int(eventi[i][j][0])
                                    if(eventi[i][j][5]>2000):caricaCoin[channel3].append(eventi[i][j][5]/10000)
                                    if(eventi[i][j][5]>2000 and eventi[i][j][0] == 0): hc_sipm0.Fill(eventi[i][j][5]/10000)
                                    if(eventi[i][j][5]>2000 and eventi[i][j][0] == 1): hc_sipm1.Fill(eventi[i][j][5]/10000)
                                    if(eventi[i][j][5]>2000 and eventi[i][j][0] == 2): hc_sipm2.Fill(eventi[i][j][5]/10000)
                                    if(eventi[i][j][5]>2000 and eventi[i][j][0] == 3): hc_sipm3.Fill(eventi[i][j][5]/10000)
                                    if(eventi[i][j][5]>2000 and eventi[i][j][0] == 4): hc_sipm4.Fill(eventi[i][j][5]/10000)
                                    if(eventi[i][j][5]>2000 and eventi[i][j][0] == 5): hc_sipm5.Fill(eventi[i][j][5]/10000)
                                    if(eventi[i][j][5]>2000 and eventi[i][j][0] == 6): hc_sipm6.Fill(eventi[i][j][5]/10000)
                                    if(eventi[i][j][5]>2000 and eventi[i][j][0] == 7): hc_sipm7.Fill(eventi[i][j][5]/10000)
                                    if(eventi[i][j][5]>2000 and eventi[i][j][0] == 8): hc_sipm8.Fill(eventi[i][j][5]/10000)
    
    file_quatro = open(f"{output_path}dec.txt", "w")    
    '''Cancello vettori per liberare memoria'''
    print("Cancello vettori per liberare memoria")
    del eventi
    
    '''Disegno i Grafici''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''' 
    if PlotMonitor==1:    
        file_uno = open(f"{output_path}Rate.txt", "w")
        if testsimp_s == 1 : file_tre = open(f"{output_path}RateCalib.txt", "w")
        file_due = open(f"{output_path}Ang.txt", "w")
        
        for j in range(8):
            for i in range(len(countLS_t[j])):
                tempoG[j].append(i*rate_scan)
                #if((countLS_t[j]-countLS[j])/countLS[j]>0 and (countLS_t[j]-countLS[j])/countLS[j]>0.1): countLS_t[j]=countLS[j]+countLS[j]*0.1
                #if((countLS_t[j]-countLS[j])/countLS[j]<0 and (countLS_t[j]-countLS[j])/countLS[j]<-0.1): countLS_t[j]=countLS[j]-countLS[j]*0.1
        for j in range(2):
            for i in range(len(countLL_t[j])):
                tempoGL[j].append(i*rate_scan)
                #if((countLS_t[j]-countLS[j])/countLS[j]>0 and (countLS_t[j]-countLS[j])/countLS[j]>0.1): countLS_t[j]=countLS[j]+countLS[j]*0.1
                #if((countLS_t[j]-countLS[j])/countLS[j]<0 and (countLS_t[j]-countLS[j])/countLS[j]<-0.1): countLS_t[j]=countLS[j]-countLS[j]*0.1
        for j in range(2):
            for i in range(len(countSS_t[j])):
                tempoGS[j].append(i*rate_scan)
                #if((countLS_t[j]-countLS[j])/countLS[j]>0 and (countLS_t[j]-countLS[j])/countLS[j]>0.1): countLS_t[j]=countLS[j]+countLS[j]*0.1
                #if((countLS_t[j]-countLS[j])/countLS[j]<0 and (countLS_t[j]-countLS[j])/countLS[j]<-0.1): countLS_t[j]=countLS[j]-countLS[j]*0.1

        with PdfPages(outmonitor) as pdf:
            fig = plt.figure(figsize=(15,7.5))
            #for i in range(12):
            #j=i+1
            #plt.subplot(3, 4, j)   
       
            n, bins, patches = plt.hist(caricaO, 500, range=[0, 100000], density=False, facecolor='green', alpha=0.75)
            #plt.yscale("log")
            plt.title(r'Q SiPM %d' %(0))
            plt.xlabel("Charge(Arbitrary Unit)")
            plt.ylabel("Event(number)")                
                #ax[2,i].plot()     
            plt.suptitle(r'Plot carica singolo SiPM')
            fig.tight_layout()  
            #plt.show(block=True)          
            #if(PlotStop==1): plt.show(block=True)                   
            #L_string=["0_1", "2_3", "4_5", "6_7"]
            pdf.savefig(fig)
            
            fig = plt.figure(figsize=(15,7.5))
            for i in range(12):
                j=i+1
                plt.subplot(3, 4, j)   
       
                n, bins, patches = plt.hist(carica[i], 100, range=[0, 5], density=False, facecolor='green', alpha=0.75)
          
                plt.title(r'Q SiPM %d' %(i))
                plt.xlabel("Charge(Arbitrary Unit)")
                plt.ylabel("Event(number)")                
                #ax[2,i].plot()     
            plt.suptitle(r'Plot carica singolo SiPM')
            fig.tight_layout()            
            if(PlotStop==1): plt.show(block=True)                   
            L_string=["0_1", "2_3", "4_5", "6_7"]
            pdf.savefig(fig)
            
            fig = plt.figure(figsize=(15,7.5))
            for i in range(4):
                j=i+1
                plt.subplot(2, 2, j)
                n, bins, patches = plt.hist(carica_barra_L[i], 100, range=[0, 15], density=1, facecolor='green', alpha=0.75)
                #plt.figtext(1.0, 0.2, pd.DataFrame(carica_barra_L[i]).describe())
                plt.title('Q bar coinc' + L_string[i])
                plt.xlabel("Charge(Arbitrary Unit)")
                plt.ylabel("Event(number)")                   
                #ax[2,i].plot()     
            plt.suptitle(r'Plot Carica barre lunghe')  
            fig.tight_layout()            
            if(PlotStop==1): plt.show(block=True)
            pdf.savefig(fig, bbox_inches='tight')                
            LS_lrc_string=["0-0_1c8", "1-0_1c8","8-0_1c8", "0-0_1c9", "1-0_1c9", "9-0_1c9", "2-2_3c8", "3-2_3c8", "8-2_3c8","2-2_3c9","3-2_3c9","9-2_3c9", "4-4_5c10", "5-4_5c10", "10-4_5c10","4-4_5c11","5-4_5c11","11-4_5c11", "6-6_7c10", "7-6_7c10", "10-6_7c10", "6-6_7c11", "7-6_7c11", "11-6_7c11"]
            
            fig = plt.figure(figsize=(15,7.5))
            for i in range(24):
                j=i+1
                plt.subplot(4, 6, j)
                n, bins, patches = plt.hist(caricaLS[i], 100, range=[0, 15], density=1, facecolor='green', alpha=0.75)
                #plt.title(r'Q SiPM %d coinc %d' %(i))   
                #ax[2,i].plot()  
                plt.title('Q SiPM ' + LS_lrc_string[i])
                plt.xlabel("Charge(Arbitrary Unit)")
                plt.ylabel("Event(number)")                   
            plt.suptitle(r'Plot carica coinc LS')
            fig.tight_layout()            
            if(PlotStop==1): plt.show(block=True)    
            fig.tight_layout()            
            LS_string=["0_1c8", "0_1c9", "2_3c8","2_3c9", "4_5c10","4_5c11", "6_7c10", "6_7c11"]
            pdf.savefig(fig)            
            
            fig = plt.figure(figsize=(15,7.5))
            
            for i in range(8):
                j=i+1
                plt.subplot(2, 4, j)
                n, bins, patches = plt.hist(carica_barra_LS[i], 100, range=[0, 15], density=1, facecolor='green', alpha=0.75)
                plt.title('Q bar coinc' + LS_string[i])
                plt.xlabel("Charge(Arbitrary Unit)")
                plt.ylabel("Event(number)")                   
                print("Rate coinc LS ", LS_string[i], " = ", round(countLS[i],3), " +- ", round(math.sqrt(countLS[i]/Trun),3), " Hz")
                file_uno.write("Rate coinc LS %s = %.3f +- %.3f hz \n"% (LS_string[i], round(countLS[i],3), round(math.sqrt(countLS[i]/Trun),3)))
                
                #ax[2,i].plot()     
            plt.suptitle(r'Plot Carica barre LS')    
            if(PlotStop==1): plt.show(block=True)
            fig.tight_layout()            
            pdf.savefig(fig)            
            #LS_string=["0_1c8", "0_1c9", "2_3c8","2_3c9", "4_5c10","4_5c11", "6_7c10", "6_7c11"]
            
            fig = plt.figure(figsize=(15,7.5))
            for i in range(8):
                j=i+1
                #plt.subplot(2, 4, j)
                n, bins, patches = plt.hist(carica_barra_LS[i], 100, range=[0, 15], density=1, facecolor='green', alpha=0.75)
                #n, bins, patches = plt.hist(carica_barra_LS[i], 100, range=[0, 15], facecolor = "white", edgecolor=_get_lines.color_cycle, density=1, alpha=0.75, label=LS_string[i])
                #plt.title(r'Q SiPM %d coinc %d' %(i))   
                #ax[2,i].plot()
                
                ###print("Valore medio coinc LS ", LS_string[i], " = ", round(statistics.mean(carica_barra_LS[i]),3), " +- ", round(3*statistics.stdev(carica_barra_LS[i]),3))
                ###file_uno.write("Valore medio Rate coinc LS %s = %.3f +- %.3f hz \n"% ( LS_string[i], round(statistics.mean(carica_barra_LS[i]),3),  round(statistics.stdev(carica_barra_LS[i]),3)))
                
            plt.legend(loc='best', fontsize=11)
            plt.xlabel("Charge(Arbitrary Unit)")
            plt.ylabel("Event(number)")   
            plt.suptitle(r'Plot Carica barre LS sovrapposti')  
            if(PlotStop==1): plt.show(block=True)
            fig.tight_layout()            
            pdf.savefig(fig) 
            
            LL_b_string=["0_1-0_1c4_5","4_5-0_1c4_5","2_3-2_3c6_7","6_7-2_3c6_7"]
            LLd_b_string=["0_1-0_1c6_7","6_7-0_1c6_7","2_3-2_3c4_5","4_5-2_3c4_5"]
            LL_string=["0_1c4_5","2_3c6_7"]
            LLd_string=["0_1c6_7","2_3c4_5"]
            
            fig = plt.figure(figsize=(15,7.5))
            for i in range(4):
                j=i+1
                plt.subplot(2, 2, j)
                n, bins, patches = plt.hist(carica_barra_LL[i], 100, range=[0, 15], density=1, facecolor='green', alpha=0.75)
                plt.title('Q bar coinc' + LL_b_string[i]) 
                plt.xlabel("Charge(Arbitrary Unit)")
                plt.ylabel("Event(number)")                   
                #ax[2,i].plot()     
            plt.suptitle(r'Plot Carica barre LL')    
            if(PlotStop==1): plt.show(block=True)
            fig.tight_layout()            
            pdf.savefig(fig)
            
            fig = plt.figure(figsize=(15,7.5))
            for i in range(4):
                j=i+1
                plt.subplot(2, 2, j)
                n, bins, patches = plt.hist(carica_barra_LLd[i], 100, range=[0, 15], density=1, facecolor='green', alpha=0.75)
                plt.title('Q bar coinc' + LLd_b_string[i]) 
                plt.xlabel("Charge(Arbitrary Unit)")
                plt.ylabel("Event(number)")                   
                #ax[2,i].plot()     
            plt.suptitle(r'Plot Carica barre LLd')    
            if(PlotStop==1): plt.show(block=True)
            fig.tight_layout()            
            pdf.savefig(fig)
            
            SS_c_string=["8-8_10","10-8_10","9-9_11","11-9_11"]
            SS_string=["8_10","9_11"]
            SSd_string=["8_11","9_10"]
            for i in range(2):
                countSS[i]=countSS[i]/2
                countSSd[i]=countSSd[i]/2
                print("Rate coinc SS  ", SS_string[i], " = ", round(countSS[i],3), " +- ", round(3*math.sqrt(countSS[i]/Trun),3), " Hz")
                file_uno.write("Valore medio Rate coinc SS %s = %.3f +- %.3f hz \n"% ( SS_string[i], round(countSS[i],3),  round(math.sqrt(countSS[i]/Trun),3)))

            for i in range(2):    
                print("Rate coinc SSd ", SSd_string[i], " = ", round(countSSd[i],3), " +- ", round(3*math.sqrt(countSSd[i]/Trun),3), " Hz")
                file_uno.write("Valore medio Rate coinc SSd %s = %.3f +- %.3f hz \n"% ( SSd_string[i], round(countSSd[i],3),  round(math.sqrt(countSSd[i]/Trun),3)))
                
            for i in range(2):
                print("Rate coinc LL  ", LL_string[i], " = ", round(countLL[i],3), " +- ", round(3*math.sqrt(countLL[i]/Trun),3), " Hz")
                file_uno.write("Valore medio Rate coinc LL %s = %.3f +- %.3f hz \n"% ( LL_string[i], round(countLL[i],3),  round(math.sqrt(countLL[i]/Trun),3)))
                
            for i in range(2):
                print("Rate coinc LLd ", LLd_string[i], " = ", round(countLLd[i],3), " +- ", round(3*math.sqrt(countLLd[i]/Trun),3), " Hz")
                file_uno.write("Valore medio Rate coinc LLd %s = %.3f +- %.3f hz \n"% ( LLd_string[i], round(countLLd[i],3),  round(math.sqrt(countLLd[i]/Trun),3)))
                
            fig = plt.figure(figsize=(15,7.5))
            for i in range(4):
                if(i==0):j=1
                if(i==1):j=3
                if(i==2):j=2
                if(i==3):j=4
                plt.subplot(2, 2, j)
                n, bins, patches = plt.hist(caricaSS[i], 100, range=[0, 15], density=1, facecolor='green', alpha=0.75)
                plt.title('Q SiPM ' + SS_c_string[i]) 
                plt.xlabel("Charge(Arbitrary Unit)")
                plt.ylabel("Event(number)")   
                #ax[2,i].plot()     
            plt.suptitle(r'Plot Carica SS')    
            if(PlotStop==1): plt.show(block=True)
            fig.tight_layout()            
            pdf.savefig(fig)            
            SSd_c_string=["8-8_11","11-8_11","9-9_10", "10-9_10"]
            
            fig = plt.figure(figsize=(15,7.5))
            for i in range(4):
                if(i==0):j=1
                if(i==1):j=3
                if(i==2):j=2
                if(i==3):j=4
                plt.subplot(2, 2, j)
                n, bins, patches = plt.hist(caricaSSd[i], 100, range=[0, 15], density=1, facecolor='green', alpha=0.75)
                plt.title('Q SiPM ' + SSd_c_string[i]) 
                plt.xlabel("Charge(Arbitrary Unit)")
                plt.ylabel("Event(number)")                   
                #ax[2,i].plot()     
            plt.suptitle(r'Plot Carica SSd')    
            if(PlotStop==1): plt.show(block=True)
            fig.tight_layout()            
            pdf.savefig(fig)
            
            fig = plt.figure(figsize=(15,7.5))
            
       
            plt.subplot(2, 2, 1)
            plt.errorbar(tempolog,temp_media[0], 1, linestyle='none',marker='.', label="DV sipm piano basso")
            plt.legend(loc='best', fontsize=11)            
            #plt.title('T media Piano: 0')
            #plt.subplot(2, 2, 2)
            plt.errorbar(tempolog,temp_media[1], 1, linestyle='none',marker='.', label="T sipm piano alto")
            plt.title('T media')
            plt.legend(loc='best', fontsize=11)
            plt.ylabel("Temperature(°C)")
            plt.xlabel("Time(second)") 
            
            #plt.subplot(2, 2, 3)
            plt.subplot(2, 2, 2)
            plt.errorbar(tempolog,tensione[0], 0.0005, linestyle='none',marker='.', label="Vbat")
            plt.legend(loc='best', fontsize=11)
            #plt.title('DV sipm piano:  0')
            #plt.subplot(2, 2, 4)
            plt.errorbar(tempolog,tensione[1], 0.000125, linestyle='none',marker='.', label="Vrasp")
            plt.errorbar(tempolog,tensione[2], 0.000125, linestyle='none',marker='.', label="Vsens1")
            plt.errorbar(tempolog,tensione[3], 0.000250, linestyle='none',marker='.', label="Vsens2")
            plt.title('Tensioni di controllo (Vbat, Vrasp, Vsens)')
            plt.legend(loc='best', fontsize=11)
            plt.ylabel("Voltage(Volt)")
            plt.xlabel("Time(second)")      
            
            #sostituisco DV con il monitor tensioni
            '''
            #plt.subplot(2, 2, 3)
            plt.subplot(2, 2, 2)
            plt.errorbar(tempolog,deltaV[0], 0.054, linestyle='none',marker='.', label="DV sipm piano basso")
            plt.legend(loc='best', fontsize=11)
            #plt.title('DV sipm piano:  0')
            #plt.subplot(2, 2, 4)
            plt.errorbar(tempolog,deltaV[1], 0.054, linestyle='none',marker='.', label="DV sipm piano alto")
            plt.title('DV sipm piano')
            plt.legend(loc='best', fontsize=11)
            plt.ylabel("DeltaV(Volt)")
            plt.xlabel("Time(second)")               
            '''
            plt.subplot(2, 2, 3)
            plt.errorbar(tempolog,pressione, 1, linestyle='none',marker='.')
            plt.title('Pressione')
            plt.ylabel("Pressure(mbar)")
            plt.xlabel("Time(second)")               
            plt.suptitle(r'Parametri run nel tempo')    
            if(PlotStop==1): plt.show(block=True)
            fig.tight_layout()            
            pdf.savefig(fig)
            
            fig = plt.figure(figsize=(15,7.5))          
            for i in range(8):
                j=i+1
                plt.subplot(2, 4, j)
                plt.errorbar(tempoG[i],countLS_t[i], countLS_t_err[i], marker='.', linestyle='none')
                plt.ylim([0.1, 0.6])
                plt.axhline(y=countLS[i], color='r', linestyle='-')
                plt.axhline(y=countLS[i]+3*math.sqrt(countLS[i]/Trun), color='grey', linestyle='--')
                plt.axhline(y=countLS[i]-3*math.sqrt(countLS[i]/Trun), color='grey', linestyle='--')
                plt.title('Rate LS' + LS_string[i])
                #plt.text(500, .45, "Rate coinc LS ", LS_string[i], " = ", round(countLS[i],3), " +- ", round(math.sqrt(countLS[i]/Trun),3), " Hz")
            plt.suptitle(r'Plot Rate LS')
            plt.ylabel("Rate(Hz)")
            plt.xlabel("Time(second)")               
            if(PlotStop==1): plt.show(block=True)
            fig.tight_layout()            
            pdf.savefig(fig) 
            
            fig = plt.figure(figsize=(15,7.5)) 
            plt.subplot(2, 2, 1)
            plt.errorbar(tempoGL[0],countLL_t[0], countLL_t_err[0], marker='.', linestyle='none')
            plt.ylim([0.5, 1.5])
            plt.axhline(y=countLL[0], color='r', linestyle='-')
            plt.axhline(y=countLL[0]+3*math.sqrt(countLL[0]/Trun), color='grey', linestyle='--')
            plt.axhline(y=countLL[0]-3*math.sqrt(countLL[0]/Trun), color='grey', linestyle='--')            
            plt.title('Rate LL ' + LL_string[0])
            plt.ylabel("Rate(Hz)")
            plt.xlabel("Time(second)") 
            
            plt.subplot(2, 2, 2)
            plt.errorbar(tempoGL[1],countLL_t[1], countLL_t_err[1], marker='.', linestyle='none')
            plt.ylim([0.5, 1.5])
            plt.axhline(y=countLL[1], color='r', linestyle='-')
            plt.axhline(y=countLL[1]+3*math.sqrt(countLL[1]/Trun), color='grey', linestyle='--')
            plt.axhline(y=countLL[1]-3*math.sqrt(countLL[1]/Trun), color='grey', linestyle='--')              
            plt.title('Rate LL ' + LL_string[1])
            plt.ylabel("Rate(Hz)")
            plt.xlabel("Time(second)") 
                      
            plt.subplot(2, 2, 3)
            plt.errorbar(tempoGS[0],countSS_t[0], countSS_t_err[0], marker='.', linestyle='none')
            plt.ylim([0.1, 0.6])
            plt.axhline(y=countSS[0], color='r', linestyle='-')
            plt.axhline(y=countSS[0]+3*math.sqrt(countSS[0]/Trun), color='grey', linestyle='--')
            plt.axhline(y=countSS[0]-3*math.sqrt(countSS[0]/Trun), color='grey', linestyle='--')             
            plt.title('Rate SS ' + SS_string[0])
            plt.ylabel("Rate(Hz)")
            plt.xlabel("Time(second)") 
            
            plt.subplot(2, 2, 4)
            plt.errorbar(tempoGS[1],countSS_t[1], countSS_t_err[1], marker='.', linestyle='none')
            plt.ylim([0.1, 0.6])
            plt.axhline(y=countSS[1], color='r', linestyle='-')
            plt.axhline(y=countSS[1]+3*math.sqrt(countSS[1]/Trun), color='grey', linestyle='--')
            plt.axhline(y=countSS[1]-3*math.sqrt(countSS[1]/Trun), color='grey', linestyle='--')              
            plt.title('Rate SS ' + SS_string[1])
            plt.ylabel("Rate(Hz)")
            plt.xlabel("Time(second)") 
            
            plt.suptitle(r'Plot Rate LL - SS')    
            if(PlotStop==1): plt.show(block=True)
            fig.tight_layout()            
            pdf.savefig(fig) 
            
            if AngPlot>0:
                print("Disegno Distribuzione angolare")
                def cosq(x,a,x0):
                    #print("The variable, a is of type:", type(a))
                    #print("The variable, x0 is of type:", type(x0))
                    #print("The variable, x is of type:", type(x))
                    return a*(np.cos(np.pi*x/180*x0)**2)
                x = np.array(Ang)
                xf = np.arange(Ang[0],Ang[5])
                y = np.array(countAng)
                popt , pcov = curve_fit(cosq,x,y,bounds=((countAng[0]*0.95), [(countAng[0]*1.05), 1.5]))
                
                print(popt)
                '''
                print("The variable, popt is of type:", type(popt))
                print("The variable, pcov is of type:", type(pcov))
                
                print("The variable, Ang is of type:", type(Ang))
                print("The variable, countAng is of type:", type(countAng))
                print("The variable, countAng_err is of type:", type(countAng_err))
                print("The variable, Ang_err is of type:", type(Ang_err))
                '''
                fig = plt.figure(figsize=(15,7.5)) 
                for i in range(6):
                    countAng_err[i]=math.sqrt(countAng[i]/Trun)

                #plt.plot(x,y,label='data')
                plt.errorbar(Ang,countAng, countAng_err, Ang_err, marker='.', linestyle='none') 
                plt.plot(xf,cosq(xf,*popt),':',label='fit') 
                               
                plt.title('Rate Angular Distribution')
                plt.ylabel("Rate(Hz)")
                plt.xlabel("Angle")             
                if(PlotStop==1): plt.show(block=True)
                fig.tight_layout()            
                pdf.savefig(fig) 
                
                for i in range(6): 
                    file_due.write("%.3f %.3f %.3f %.3f \n"% (Ang[i], countAng[i], Ang_err[i], countAng_err[i]))

        
        print(countSS_test)
        print(countSS_ref)
        if testsimp_s == 1 :
          plt.close()
          ratioSS=[0,0,0,0]
          for i in range(2):
            ratioSS[i]=countSS_test[i]/countSS_ref[i]
            ratioSS[i+2]=countSS_test[i+2]/countSS_ref[i]
            file_tre.write("%.3f %.3f %.3f \n"% (countSS_ref[i], countSS_test[i],ratioSS[i]))
            file_tre.write("rate coinc 8_10 & %.3f %.3f %.3f %.3f \n"% (i*2, countSS_ref[i], countSS_test[i+2],ratioSS[i+2]))
            file_tre.write("rate coinc 9_11 & %.3f %.3f %.3f %.3f \n"% (i+1, countSS_ref[i], countSS_test[i+2],ratioSS[i+2]))
            
    if Decadimento>0:
        #print(time_dec)
        with PdfPages(outmonitor) as pdf:
            fig = plt.figure(figsize=(15,7.5))
            #fig = plt.figure(figsize=(15,7.5))
            #for i in range(8):
            #j=i+1
            #plt.subplot(2, 4, j)
            n, bins, patches = plt.hist(time_dec, 50, range=[0, 15], density=False, facecolor='blue', alpha=0.75)
            binscenters = np.array([(i*15/50) for i in range(50)])
            print(n,bins)
            for i in range(len(n)):
                file_quatro.write("%.3f %.3f %.3f %.3f \n"% (bins[i], n[i], 0.15, math.sqrt(bins[i])))
                
            #n, bins, patches = plt.hist(carica_barra_LS[i], 100, range=[0, 15], facecolor = "white", edgecolor=_get_lines.color_cycle, density=1, alpha=0.75, label=LS_string[i])
            #plt.title(r'Q SiPM %d coinc %d' %(i))   
            #ax[2,i].plot()
            #def exp(x,a,b,c):
            #    return  a * np.exp(b * x) + c
            #popte , pcove = curve_fit(exp,xdata=binscenters,ydata=n)       
            #print(popte)    
            #print("Valore medio coinc LS ", LS_string[i], " = ", round(statistics.mean(carica_barra_LS[i]),3), " +- ", round(statistics.stdev(carica_barra_LS[i]),3))
            #file_uno.write("Valore medio Rate coinc LS %s = %.3f +- %.3f hz \n"% ( LS_string[i], round(statistics.mean(carica_barra_LS[i]),3),  round(statistics.stdev(carica_barra_LS[i]),3)))
                    
            plt.legend(loc='best', fontsize=11)
            plt.xlabel("Decay time (mu_second)")
            plt.ylabel("Event(number)")   
            plt.suptitle(r'Plot tempo decadimento')  
            if(PlotStop==1): plt.show(block=True)
            fig.tight_layout()            
            pdf.savefig(fig)      
            
            
    if sciglass==1:
        with PdfPages(outmonitor) as pdf:
            fig = plt.figure(figsize=(15,7.5))
            #[0]*(exp(-0.5*(((x-[1])/[2])+exp(-((x-[1])/[2]))))/sqrt(2.*3.1415))
            for i in range(12):
                j=i+1
                mean, var = moyal.fit(carica[i])                
                plt.subplot(3, 4, j)   
                if i==1:
                  n, bins, patches = plt.hist(carica[i], 100, range=[6, 30], density=False, facecolor='green', alpha=0.75)
                if i==0 or 1<i<7 or i==8:                
                  n, bins, patches = plt.hist(carica[i], 50, range=[2, 16], density=False, facecolor='green', alpha=0.75)
                if i>8 and i <11:
                  n, bins, patches = plt.hist(carica[i], 50, range=[2, 16], density=False, facecolor='green', alpha=0.75)
                if i==11:
                  n, bins, patches = plt.hist(carica[i], 50, range=[2, 16], density=False, facecolor='green', alpha=0.75)    
                if i==7:
                  n, bins, patches = plt.hist(carica[i], 50, range=[2, 16], density=False, facecolor='green', alpha=0.75)  
                '''
                if(i==8):
                  mean, var = moyal.fit(carica[i])
                  plt.title(r'Q SiPM %d - Fit: mean=%.3f, var=%.3f' %(i,mean, var))  
                if(i!=8):plt.title(r'Q SiPM %d' %(i))'''
                y = moyal.pdf(bins, loc=mean, scale=1)
                #print(y)
                l = plt.plot(bins, y, 'r--', linewidth=2)
                
                plt.title(r'Q SiPM %d - Fit: mean=%.3f, var=%.3f' %(i,mean, var))
                plt.xlabel("PE")
                plt.ylabel("Event(number)")                
                #ax[2,i].plot()     
            plt.suptitle(r'Plot carica singolo SiPM')
            fig.tight_layout()            
            if(PlotStop==1): plt.show(block=True)                   
            L_string=["0_1", "2_3", "4_5", "6_7"]
            pdf.savefig(fig)
            
            fig = plt.figure(figsize=(15,7.5))
            '''def cosq(x,a,b,c):
                #print("The variable, a is of type:", type(a))
                #print("The variable, x0 is of type:", type(x0))
                #print("The variable, x is of type:", type(x))
                return a*(exp(-0.5*(((x-b)/c)+exp(-((x-b)/c))))/sqrt(2.*3.1415)'''

                        
            for i in range(12):
                j=i+1
                '''x = np.array(Ang)
                xf = np.arange(Ang[0],Ang[5])
                y = np.array(countAng)
                popt , pcov = curve_fit(cosq,x,y,bounds=((countAng[0]*0.95), [(countAng[0]*1.05), 1.5]))'''
                mean, var = moyal.fit(caricaCoin[i])
                plt.subplot(3, 4, j)   
                if i==1:
                  n, bins, patches = plt.hist(caricaCoin[i], 50, range=[0, 1], density=False, facecolor='green', alpha=0.75)
                if i==0 or 1<i<7 or i==8:             
                  n, bins, patches = plt.hist(caricaCoin[i], 50, range=[0, 1], density=False, facecolor='green', alpha=0.75)
                if i>8 and i <11:
                  n, bins, patches = plt.hist(caricaCoin[i], 50, range=[0, 1], density=False, facecolor='green', alpha=0.75)
                if i==11:
                  n, bins, patches = plt.hist(caricaCoin[i], 50, range=[0, 1], density=False, facecolor='green', alpha=0.75)    
                if i==7:
                  n, bins, patches = plt.hist(caricaCoin[i], 150, range=[0, 2.5], density=False, facecolor='green', alpha=0.75)  
                y = moyal.pdf(bins, loc=mean, scale=1)
                #print(y)
                l = plt.plot(bins, y, 'r--', linewidth=2)
                print("Coincidenze vetro canale ", i, " 2 barre plastica: ", Coinc2[i])
                plt.title(r'Q SiPM %d - Fit: mean=%.3f, var=%.3f' %(i,mean, var))
                plt.xlabel("PE")
                plt.ylabel("Event(number)")                
                #ax[2,i].plot()     
            plt.suptitle(r'Plot carica singolo SiPM in coincidenza con PlastScint')
            fig.tight_layout()            
            if(PlotStop==1): plt.show(block=True)                   
            L_string=["0_1", "2_3", "4_5", "6_7"]
            pdf.savefig(fig)
            
            fig = plt.figure(figsize=(15,7.5))
            
            for i in range(12):
                j=i+1
                '''x = np.array(Ang)
                xf = np.arange(Ang[0],Ang[5])
                y = np.array(countAng)
                popt , pcov = curve_fit(cosq,x,y,bounds=((countAng[0]*0.95), [(countAng[0]*1.05), 1.5]))'''
                mean, var = moyal.fit(caricaCoin3[i])
                plt.subplot(3, 4, j)
                if i==1:
                  n, bins, patches = plt.hist(caricaCoin3[i], 50, range=[2, 16], density=False, facecolor='green', alpha=0.75)
                if i==0 or 1<i<7 or i==8:             
                  n, bins, patches = plt.hist(caricaCoin3[i], 50, range=[2, 16], density=False, facecolor='green', alpha=0.75)
                if i>8 and i <11:
                  n, bins, patches = plt.hist(caricaCoin3[i], 50, range=[2, 16], density=False, facecolor='green', alpha=0.75)
                if i==11:
                  n, bins, patches = plt.hist(caricaCoin3[i], 50, range=[2, 16], density=False, facecolor='green', alpha=0.75)    
                if i==7:
                  n, bins, patches = plt.hist(caricaCoin3[i], 50, range=[2, 16], density=False, facecolor='green', alpha=0.75)  
                y = moyal.pdf(bins, loc=mean, scale=1)
                #print(y)
                l = plt.plot(bins, y, 'r--', linewidth=2)
                print("Coincidenze vetro canale ", i, " 3 barre plastica: ", Coinc3[i])

                plt.title(r'Q SiPM %d - Fit: mean=%.3f, var=%.3f' %(i,mean, var))
                plt.xlabel("Charge(Arbitrary Unit)")
                plt.ylabel("Event(number)")                
                #ax[2,i].plot()     
            plt.suptitle(r'Plot carica singolo SiPM in coincidenza con PlastScint')
            fig.tight_layout()            
            if(PlotStop==1): plt.show(block=True)                   
            L_string=["0_1", "2_3", "4_5", "6_7"]
            pdf.savefig(fig)
            
            fig = plt.figure(figsize=(15,7.5))
            
'''    if sciglass>1:
      with PdfPages(outmonitor) as pdf:
        fig = plt.figure(figsize=(15,7.5))
        for i in range(12):
            j=i+1
                               
            plt.subplot(3, 4, j)   
            if i<7 or i==8:             
              n, bins, patches = plt.hist(caricaCoin[i], 100, range=[0, 3], density=False, facecolor='green', alpha=0.75)
            if i>8 and i <11:
              n, bins, patches = plt.hist(caricaCoin[i], 700, range=[0, 35], density=False, facecolor='green', alpha=0.75)
            if i==11:
              n, bins, patches = plt.hist(caricaCoin[i], 400, range=[0, 20], density=False, facecolor='green', alpha=0.75)    
            if i==7:
              n, bins, patches = plt.hist(caricaCoin[i], 100, range=[0, 3], density=False, facecolor='green', alpha=0.75)  
            ''''''
                if(i==8):
                  mean, var = moyal.fit(carica[i])
                  plt.title(r'Q SiPM %d - Fit: mean=%.3f, var=%.3f' %(i,mean, var))  
                if(i!=8):plt.title(r'Q SiPM %d' %(i))''''''
                
                   
            #print(y)
            
            if not caricaCoin[i]:
              print("list channel ", i ," empty")
            else:
              mean, var = moyal.fit(caricaCoin[i])   
              #y = moyal.pdf(bins, loc=mean, scale=1)
              y = moyal.rvs(loc=0, scale=1, size=1, random_state=None)
              #l = plt.plot(bins, y, 'r--', linewidth=2)
              plt.title(r'Q SiPM %d - Fit: mean=%.3f, var=%.3f' %(i,mean, var))
              plt.xlabel("Charge")
              plt.ylabel("Event(number)")                
            #ax[2,i].plot()     
        plt.suptitle(r'Plot carica singolo SiPM')
        fig.tight_layout()            
                           
        L_string=["0_1", "2_3", "4_5", "6_7"]
        pdf.savefig(fig)
        #f = ROOT.TF1("f1", "sin(x)/x", 0., 10.)
        #f.Draw()
        outHistFile = ROOT.TFile(output_root, "RECREATE")
        Canvas = ROOT.TCanvas("cc","",10,10,800,600)
        Canvas.Divide(3,4)
        ROOT.gStyle.SetOptFit(1);
        
        Canvas.cd(1)
        hc_sipm0.Draw()
        hc_sipm0.Write()
        hc_sipm0.Fit("landau", "RL", "SAME", 0.4, 0.9) 
        hc_sipm0.Write()
        
        Canvas.cd(2)
        hc_sipm1.Draw()
        hc_sipm1.Write()
        hc_sipm1.Fit("landau", "RL", "SAME", 0.4, 0.9) 
        hc_sipm1.Write()
        
        Canvas.cd(3)
        hc_sipm2.Draw()
        hc_sipm2.Write()
        hc_sipm2.Fit("landau", "RL", "SAME", 0.4, 0.9) 
        hc_sipm2.Write()
        
        Canvas.cd(4)
        hc_sipm3.Draw()
        hc_sipm3.Write()
        hc_sipm3.Fit("landau", "RL", "SAME", 0.35, 0.9) 
        hc_sipm3.Write()
        
        Canvas.cd(5)
        hc_sipm4.Draw()
        hc_sipm4.Write()
        hc_sipm4.Fit("landau", "RL", "SAME", 0.4, 0.9) 
        hc_sipm4.Write()
        
        Canvas.cd(6)
        hc_sipm5.Draw()
        hc_sipm5.Write()
        hc_sipm5.Fit("landau", "RL", "SAME", 0.4, 0.9) 
        hc_sipm5.Write()
        
        Canvas.cd(7)
        hc_sipm6.Draw()
        hc_sipm6.Write()
        hc_sipm6.Fit("landau", "RL", "SAME", 0.4, 0.9) 
        hc_sipm6.Write()
        
        Canvas.cd(8)
        hc_sipm7.Draw()
        hc_sipm7.Write()
        hc_sipm7.Fit("landau", "RL", "SAME", 0.4, 0.9) 
        hc_sipm7.Write()
        
        Canvas.cd(9)
        hc_sipm8.Draw()
        hc_sipm8.Write()
        hc_sipm8.Fit("landau", "RL", "SAME", 0.4, 0.9) 
        hc_sipm8.Write()
        
        fig = plt.figure(figsize=(15,7.5))
        outHistFile.Close()
        if(PlotStop==1): plt.show(block=True)    ''''''
      
    if MyDebug>1:
        print ("\nFine del run      N. trigger analizzati: %d "%MyData.ntot_trigger)
        print ("N. trigger frammentati: %d "% MyData.fragmented)
        print ("\nN. trigger 'strani': %d"% MyData.nWarning_leng)
        print ("\nCarica anomala: %d"% MyData.nWarning_charge)
        print ("N. eventi: %d"% MyData.ntot_evt)
        print("N. eventi costituiti da 1 solo trigger %d" % MyData.ntot_single)
        print("N. eventi costituiti da 2 trigger %d" % MyData.ntot_coinc2)
        print("N. eventi costituiti da 3 trigger %d" % MyData.ntot_coinc3)
        print("N. eventi costituiti da 4 trigger %d" % MyData.ntot_coinc4)
        print("N. eventi costituiti da almeno 5 trigger %d" % MyData.ntot_coinc5)
        print("Distribuzione dei conteggi per SiPM")
        [print (" %5d" % nn, end="") for nn in range(N_SIPM)]
        print("\n")
        [print (" %5d" % nn, end="") for nn in MyData.total_count_per_sipm]
        print("\n")
    '''