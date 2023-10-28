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
import tkinter as tk 
root = tk.Tk()
#######################################################################################################
from matplotlib.backends.backend_pdf import PdfPages
from scipy import stats
from scipy.optimize import curve_fit
from scipy import asarray as ar,exp
from scipy import special as sp
import sys

import numpy as np
import pandas as pd

# stato di ritorno dalle funzioni
BAD = False
GOOD = True

# parametri da settare all'inizio

#inputPath = "../AstroPlano_sep21/"	#path input file
#inputFile = "AP_ven_cfg_old" 		# file corrotto (sipm>11)

inputPath = "./"		        # path input file
inputFile = "20231012-2104"
#inputFile = "20220517-1201"
#inputFile = "20220428-0940"   	    # input file name without AP and extension
#inputFile = "20220321-2128"   	    # input file name without extension
inputlog = "APlog" + inputFile + ".log"
outmonitor = "Monitor-AP" +  inputFile + ".pdf"

inputFile = "AP" + inputFile
print("Apro File: ", inputFile, " ", inputlog)
output_path = "./"		#idem for output
output_file = inputFile+ "provaPlot" + "_dst.txt"
output_log = inputFile+ "_WSVT.txt"

#numero di eventi da processare (-1 = tutti)
NEVMAX =  5000000   # 9999999    

# costanti che potremmo dover cambiare
time_win = 4000    # ns,  lunghezza max finestra temporale di un evento
rate_scan = 900     #intervallo di tempo su cui fare la media rate per scan temporale
MyDebug    = 0      # 0 no debug, 1 minimale, 2 esteso, 3 tutto
MyPlot     = 0
PlotMonitor = 0    # 0 no plot, 1 plot si
PlotStop = 0
AngPlot = 0         #0 no distrbuzione angolare, 1 set binari, 2 set alternativo
PlotFile    = 0     # 0 no plot, 1 plot su file
N_DUMP_FIRST_EVENTS = 4   # numero degli eventi iniziali che vengono stampati
N_PLOT_EVENTS = 5 # plotta evento desiderato

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

def myLinearRegression (x,y):
    # calcola il fit lineare al fronte di salita del trigger
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    if MyDebug>1: 
        print("\nslope: %8.2f    intercept: %11.2f, correl. %5.2f, errore_slope: %8.2f " % (
                       slope, intercept, r_value, std_err))
    return (slope, intercept, r_value, std_err)
    

def move_figure(position="top-right"):
    '''
    Move and resize a window to a set of standard positions on the screen.
    Possible positions are:
    top, bottom, left, right, top-left, top-right, bottom-left, bottom-right
    '''

    mgr = plt.get_current_fig_manager()
    #mgr.full_screen_toggle()  # primitive but works to get screen size
    #############################################################################################
    #Stefano: dovrebbe essere una versione più compatibile (Flavio verifica)
    #############################################################################################
    py = root.winfo_screenheight()
    px = root.winfo_screenwidth()
    print('Width: %i px, Height: %i px' % (px, py))
    d = 10  # width of the window border in pixels
    
    if position == "top":
        # x-top-left-corner, y-top-left-corner, x-width, y-width (in pixels)
        mgr.window.setGeometry=(d, 4*d, px - 2*d, int(py/2) - 4*d)
    elif position == "bottom":
        mgr.window.setGeometry=(d, py/2 + 5*d, px - 2*d, py/2 - 4*d)
    elif position == "left":
        mgr.window.setGeometry=(d, 4*d, px/2 - 2*d, py - 4*d)
    elif position == "right":
        mgr.window.setGeometry=(px/2 + d, 4*d, px/2 - 2*d, py - 4*d)
    elif position == "top-left":
        mgr.window.setGeometry=(d, 4*d, px/2 - 2*d, py/2 - 4*d)
    elif position == "top-right":
        mgr.window.setGeometry=(int(px/2) + d, 4*d, int(px/2) - 2*d, int(py/2) - 4*d)
    elif position == "bottom-left":
        mgr.window.setGeometry=(d, py/2 + 5*d, px/2 - 2*d, py/2 - 4*d)
    elif position == "bottom-right":
        mgr.window.setGeometry=(px/2 + d, int(py/2) + 5*d, int(px/2) - 2*d, int(py/2) - 4*d)
    ###############################################################################################
    '''//non funziona su farm infn
    #py = mgr.canvas.height()
    #px = mgr.canvas.width()
    if position == "top":
        # x-top-left-corner, y-top-left-corner, x-width, y-width (in pixels)
        mgr.window.setGeometry(d, 4*d, px - 2*d, int(py/2) - 4*d)
    elif position == "bottom":
        mgr.window.setGeometry(d, py/2 + 5*d, px - 2*d, py/2 - 4*d)
    elif position == "left":
        mgr.window.setGeometry(d, 4*d, px/2 - 2*d, py - 4*d)
    elif position == "right":
        mgr.window.setGeometry(px/2 + d, 4*d, px/2 - 2*d, py - 4*d)
    elif position == "top-left":
        mgr.window.setGeometry(d, 4*d, px/2 - 2*d, py/2 - 4*d)
    elif position == "top-right":
        mgr.window.setGeometry(int(px/2) + d, 4*d, int(px/2) - 2*d, int(py/2) - 4*d)
    elif position == "bottom-left":
        mgr.window.setGeometry(d, py/2 + 5*d, px/2 - 2*d, py/2 - 4*d)
    elif position == "bottom-right":
        mgr.window.setGeometry(px/2 + d, int(py/2) + 5*d, int(px/2) - 2*d, int(py/2) - 4*d)
    '''


class Trigger:
    # classe per trattare il segnale sel singolo SiPM
    def __init__(self):
        self.channel =None
        self.sequential = 0  # n. sequenziale all'interno dell'evento
        self.tempo   = [0,0,0,0]
        self.frag_flag =0
        self.fifofull  = 0
        self.carica_totale = 0
        self.nsamples = 0
        self.samples  = list()
        self.tpeak = None
        self.t50   = None
        self.intercept = None
        self.slope = None
        self.quality_flag = None
        self.Qcharge_flag = None
        self.shift = None
        self.peak_value = None
    
    def mydeepcopy(self):
        # copia un trigger completamente
        xx= Trigger()
        xx.channel = self.channel
        xx.sequential = self.sequential
        xx.tempo = self.tempo[:]
        xx.frag_flag = self.frag_flag
        xx.fifofull = self.fifofull
        xx.carica_totale = self.carica_totale
        xx.nsamples = self.nsamples
        xx.samples=self.samples[:]
        xx.tpeak = self.tpeak
        xx.intercept = self.intercept
        xx.slope = self.slope
        xx.t50 = self.t50
        xx.shift = self.shift
        xx.quality_flag = self.quality_flag
        xx.Qcharge_flag = self.Qcharge_flag
        xx.peak_value = self.peak_value
        return xx
        
        
    def LeggiHeader1(self):
        # legge  header 1 e lo ritorna, se EOF ritorna None
        key = 0X55AA
        head1 = MyData.f_in.read(4)
        self.f_in = MyData.f_in
        if head1 == b'':   # EOF reached
            return None
        ihead1= int.from_bytes(head1, byteorder='little')
        syncBytes = ihead1>>16
        if syncBytes == key: return ihead1
        # tento di ricuperare un file corrotto cercando la stringa 0x55AA
        print("\n\n Evento %d, Trigger anomalo: Header 1: %X" %(MyData.ntot_trigger, ihead1))
        print ("file corrotto ????")
        sys.exit('File corrotto ?')

        # c1=0
        # nerr=0
        # while c1 != key1:       #devo trovare 0x55
        #     c1=self.f_in.read(1)
        #     nerr = nerr +1
        #     if c1 != b'\x00': print('\n nerr=%d, c1= %X' %
        #                       (nerr, int.from_bytes(c1,byteorder='little')))
        #     if c1 != key1: continue
        #     c2=0                #trovato, adesso cerco 0xAA
        #     while c2 != key2:
        #         c2 = self.f_in.read(1)
        #         if c2 == key2:  #trovato 0x55, leggo gli altri 2 bytes e ritorno
        #             c3= self.f_in.read(1)
        #             c4= self.f_in.read(1)
        #             head1= int.from_bytes(c1,byteorder='little')
        #             head1 = head1<<8
        #             head1 = head1 | int.from_bytes(c2,byteorder='little')
        #             head1 = head1<<8
        #             head1 = head1 | int.from_bytes(c3,byteorder='little')
        #             head1 = head1<<8
        #             head1 = head1 | int.from_bytes(c4,byteorder='little')
        #             return head1
        #         elif c2 == key1:    # ho trovato 0Xaa, riprendo a cercare c2
        #             c1=c2
        #             continue
        #         else:       #esco dal loop piu' interno 
        #             break
        #     continue     # e continuo quello esterno
       
    def Check_charge(self):
        #Carica_ricalcolata =0
        #controlliamo che la carica fornita dalla Waveboard corrisponda a quella 
        # che possiamo calcolare noi facendo la somma dei singoli campionamenti
        Carica_ricalcolata = sum (self.samples)
        if self.carica_totale != Carica_ricalcolata:
            if MyDebug >0:
                print("\n N campioni: %d"% self.nsamples)
                print("\n\n ATTENZIONE Q sbagliata ?? Q waveboard: %d, Q ricalcolata: %d"% \
                  (self.carica_totale, Carica_ricalcolata))
                Qcharge_flag_port=1
                #self.Qcharge_flag=1
                #Qcharge_flag=1
            return BAD
            return (nstart, tpeak, const_frac, intercept, slope, quality_flag, Qcharge_flag, peak_value)
        else:
            Qcharge_flag_port=0
            #self.Qcharge_flag=0
            #Qcharge_flag=0
            return GOOD
            return (nstart, tpeak, const_frac, intercept, slope, quality_flag, Qcharge_flag, peak_value)
    def LeggiTrigger(self):
        # leggo header e lo ritorno in self, se EOF ritorno None, altrimenti 0
        self.tpeak= None    # in attesa di ricalcolarli
        self.t50=None
        
        ihead1 = self.LeggiHeader1()
        if ihead1 is None: return None
        
        self.channel = ihead1 & 15   # estraggo ultimi 4 bit
        if self.channel > (N_SIPM-1):
            print ("Canale anomalo: %d, riportato a valori decenti\n\n"% self.channel)
            # a volte capitava di trovare trigger>11, credo di avere risolto (mio bug)
            sys.exit('File corrotto ?')

        RankBoard = (ihead1>>4) % 32
    #   halfhead = (ihead1>>0) % 32
        if MyDebug>=2: print("\nHeader 1: %X, RankBoard: %X, canale: %X"% \
                           (ihead1, RankBoard, self.channel))
        self.samples =[]
            
        # header 2
        head2 = self.f_in.read(8)
        ihead2 = int.from_bytes(head2, byteorder='little')
        if MyDebug>=3: print("Header 2: %X"% ihead2 )
        decanno = ihead2>>60
        anno =    (ihead2>>56) % 16
        anno = decanno*10 + anno
        cengiorni = (ihead2>>54) % 4
        decgiorni = (ihead2>>50) % 16
        giorni = (ihead2>>46)% 16
        giorni = cengiorni*100+decgiorni*10+ giorni
        secondi = (ihead2>>29)  & 0x1FFFF
        us125 = (ihead2 >> 16)& 0X1FFF    
        ns = (ihead2 &0XFFFF) * SAMPLING_TIME   # tengo conto del clock a 250 MHz
        
        self.tempo[0]= anno
        self.tempo[1]= giorni 
        self.tempo[2]= secondi
        self.tempo[3]= us125*125000 + ns 

        #header 3
        head3 = self.f_in.read(4)
        ihead3 = int.from_bytes(head3, byteorder='little')
        if MyDebug>=3 : print("Header 3: %X"% ihead3 )     
        compr_flag = ihead3 >>31
        if compr_flag != 0:
            print("\n\n Attenzione flag di compressione attivo!! \n NON previsto !!")
            print ("\n Non so gestirlo, esco\n")
            sys.exit(('formato sconosciuto'))
                
        self.frag_flag = (ihead3>>30) & 0x01   #flag di frammentazione
        self.carica_totale = (ihead3>>8) & 0x3FFFFF 
        self.fifofull = (ihead3>>7) & 1
        self.nsamples =  ihead3 & 0X7F
        # if MyDebug>=1: 
        #     print("\nAnno: %d, giorno: %d, sec %d,  ns: %d, SiPM: %d, # campioni: %d, Q: %d" %
        #         (anno, giorni, secondi, ns, self.channel, self.nsamples,\
        #          self.carica_totale))
        
        if self.nsamples%2 != 0:  self.nsamples += 1    #se e' dispari
        else:  self.nsamples = self.nsamples
        for i in range(self.nsamples):
            samp = self.f_in.read(2)
            isamp = (int.from_bytes(samp, byteorder='little'))& 0X3FFF
            self.samples.append(isamp) 
            # if MyDebug>=2:
            #     print("Sample n. %d: %d ossia %X"% (i, isamp, isamp))
        rc = self.Check_charge()
        if rc== BAD:
            MyData.nWarning_charge += 1
        return  rc  # tutto bene



    def PrintTrigger(self):
        if MyDebug > 1:
            print ("\nTrigger n. %d"% self.sequential) 
            print(" SiPM: %d, Year: %d, Days: %d, secs: %d,  ns: %d"% \
                  (self.channel, self.tempo[0],self.tempo[1], self.tempo[2], self.tempo[3]) )
            print("Fragm flag: %d, Q tot: %d, Fifo full: %d, N. samples: %d"%(self.frag_flag, self.carica_totale, self.fifofull, self.nsamples), end="")
            try:    # definiti solo se gia' fatto fit al fronte di salita
                print ("\nt peak: %d ns, t (50%%):%5.1f ns \n" % (self.tpeak, self.t50) )
            except:
                pass
            
        if MyDebug>=2:
            npr=0
            for i in self.samples: 
                if npr%10 == 0: print(" ")  # 10 per riga
                print (" %d, "% i, end=" ")
                npr=npr+1
            print(" ")

            
            
    def TogliPed_trigger(self, baseline=5):
        # sottrae il piedistallo dai primi "baseline" punti 
        # se baseline == 0 non sottrae nulla
        nsa= self.nsamples # trigger  n. samples
        self.carica_totale = 0
        if baseline>0:
            if nsa<baseline:
                print ("\nTrigger troppo corto, non posso togliere il piedistallo")
                print ("\nn. samples= %d, baseline= %d "% (nsa, baseline))
                self.PrintTrigger()
                return
            # calcola il valore medio del piedistallo sui primi 'baseline' campioni
            pedmedio=0
            for p in range(baseline):
                pedmedio += self.samples[p]
            pedmedio= pedmedio /baseline
            # sottraiamolo
            for p in range (nsa):
                self.samples[p] -= pedmedio
                if self.samples[p]<0: self.samples[p]=0
                
        # carica totale
        self.carica_totale = sum (self.samples)
        
        # for p in range(nsa):
        #     self.carica_totale += self.samples[p]
            
        
    def findTime(self):
        # facciamo il fit del fronte di salita
        global MyPlot
        LOW_CUT = 0.2#ridotto intervallo di fit
        HIGH_CUT= 0.7
        LOW_TIME_SHIFT= 50#in nanosec
        LOW_TIME_CUT= 40#in nanosec
        HIGH_TIME_CUT= 80#in nanosec
        nsamp= self.nsamples
        samp = self.samples
        peak_value = max(samp)
        npeak = samp.index(peak_value)
        tpeak = npeak* SAMPLING_TIME
        shift=0
        #######
        #Faccio un controllo sui valori adiacenti
        #######
        if(abs(peak_value-samp[npeak-1]) < 0.05*peak_value): 
            peak_value=(peak_value+samp[npeak-1])/2
            tpeak = (2*npeak-1)/2* SAMPLING_TIME
        if((npeak+1)<(len(samp)-1)):    
          if(abs(peak_value-samp[npeak+1]) < 0.05*peak_value): 
              peak_value=(peak_value+samp[npeak+1])/2
              tpeak = (2*npeak+1)/2* SAMPLING_TIME
        if((npeak+1)<(len(samp)-1)):                  
          if(abs(peak_value-samp[npeak-1]) < 0.05*peak_value and abs(peak_value-samp[npeak+1]) < 0.05*peak_value ): 
              peak_value=(samp[npeak+1]+samp[npeak-1])/2
              tpeak = npeak* SAMPLING_TIME           
        ######
        #tpeak = npeak* SAMPLING_TIME
        nstart = 0
        nstop = npeak
        
    #verifico che se ci sono eventi che iniziano prima e li ritardo
        for index in range(0, npeak, 1):
            if (samp[index+1]-samp[index])>50 and (index*SAMPLING_TIME)<LOW_TIME_SHIFT: #continue
                shift= LOW_TIME_SHIFT - index*SAMPLING_TIME
                #print(index)
                #print(samp[index])
                #print(samp[index+1])
                break
            	# cerco t per cui il valore <= LOW_CUT * valore massimo partendo dal picco    
        for index in range(npeak, 0, -1):    
            if samp[index]> LOW_CUT*peak_value and index*SAMPLING_TIME>LOW_TIME_CUT: continue
            nstart = index
            break
        for index in range(nstart, nsamp):   # idem valore > HIGH_CUT * valore massimo
            if samp[index]<HIGH_CUT*peak_value and index*SAMPLING_TIME<HIGH_TIME_CUT: continue
            nstop=index
            break
        #print(shift)
        tpeak = tpeak + shift
        #fit del fronte di salita con retta, voglio migliorare timing
        const_frac = 0
        ##################################### 
        #Stefano:Provo a correggere il fit
        #####################################
        #nstart=nstart+1
        #nstop=nstop-1
        #####################################
        x= list(range(nstart*SAMPLING_TIME, (nstop+1)*SAMPLING_TIME, SAMPLING_TIME))
        y= samp[nstart: nstop+1]
        # devo avere almeno 2 punti per fare il fit
        if (nstop-nstart) >= 2:        # posso fare fit
           # if (nstart*SAMPLING_TIME>LOW_TIME_CUT && index*SAMPLING_TIME<HIGH_TIME_CUT)
            slope,intercept, correlazione, errore_slope = myLinearRegression(x, y)
            halfpeak= peak_value *0.50
            const_frac = (halfpeak - intercept )/slope + shift
        else:
            slope=-1        # no fit
            intercept=-1
            correlazione =0
            errore_slope = 999999
            
        quality_flag =0

        

        if correlazione<0.7 or slope <10:
            quality_flag =1  # normalmente la correlazione e' >0.8 e la pendenza>40
        # Calcolo del chi quadro, non usato
        # chi2=0
        # for ind in range(nstart, nstop+1):
        #     yfit = intercept + slope*x[ind-nstart]
        #     delta =(samp[ind]-yfit)
        #     chi2 = chi2 + delta**2 
    #        print ("x, samp y: %d %d  %d, chi2: %d"% ( x[ind-nstart], samp[ind], yfit, chi2))
    #    print("nstart nstop: %d  %d; chi2 %d"% (nstart, nstop,chi2))
    #    print ("t discrim. 50%%: %7.2f" % const_frac)
        # if Plot and (nstop-nstart>4) or slope==0:
            
    # se il fit e' cattivo vediamo com'e' il trigger        
        if MyPlot == 1 and (slope<10 or correlazione<0.7 or errore_slope>500):
            print("\n ATTENZIONE fit al leading edge cattivo")
            print ("correlazione %4.2f, errore %.1f, slope %.2f"% \
                (correlazione, errore_slope, slope))   
        return (nstart, tpeak, const_frac, intercept, slope, quality_flag, shift, peak_value)
     
        
     
    def PlotTrigger(self, nstart, npeak, intercept, slope, quality_flag, shift, peak_value):
        # grafica un trigger in funzione del tempo   
        global MyPlot
        tempi= list(range(0+shift, self.nsamples*SAMPLING_TIME+shift, SAMPLING_TIME))
        n0 = nstart
        n1= min (self.nsamples, npeak+1)
        if (quality_flag==0 or quality_flag==1): #faccio graficare solo eventi buoni
            gr=plt.subplot()#aggiunto per avere le griglie custom
            #fig = plt.figure()
            labelplot="Sipm_" + str(self.channel)
            plt.plot(tempi, self.samples, '--o', label=labelplot)
            yfit = [intercept + slope*xd for xd in tempi[n0:n1]]
            #plt.plot(tempi[n0:n1], yfit, 'r', label='fitted line')
            #######################################################################################
            #Stefano: aggiunte griglie custom
            #plt.grid(visible=True, which='both', axis='both')
            ###################################################################################
            # Change major ticks to show every 200 & 20.
            #plt.xaxis.grid(True, which='minor')
            gr.xaxis.set_major_locator(MultipleLocator(20))
            gr.yaxis.set_major_locator(MultipleLocator(10))

            # Change minor ticks to show every 50 and 5.(200/4=50)
            gr.xaxis.set_minor_locator(AutoMinorLocator(10))
            gr.yaxis.set_minor_locator(AutoMinorLocator(2))

            # Turn grid on for both major and minor ticks and style minor slightly
            # differently.
            plt.grid(which='major', color='#CCCCCC', linestyle='--')
            plt.grid(which='minor', color='#CCCCCC', linestyle=':')
            ######################################################################################
            plt.xlabel('ns')
            plt.legend()
            plt.title("Evt: %d, N. seq trg: %d, SiPM: %d" % \
                      (evento.nevt, self.sequential, self.channel))
            print("evento n: ", evento.nevt) 
            print("evento da mostrare: ", N_PLOT_EVENTS) 
           ## plt.gcf().number + 1
            
            if N_PLOT_EVENTS == (evento.nevt):
                
                '''with PdfPages('monitor.pdf') as pdf:
                    fig = plt.figure()
                    plt.savefig('monitor.pdf')'''
                plt.show()    
                move_figure()
                plt.pause(0.05)
                evento.PrintEvento()
                
                rc= input ("Batti 0 per continuare, 1 per smettere di plottare")
                try:   # cerco di recuperare input sbagliati senza abortire
                    rc=int(rc)
                except:
                    rc=0
                if rc == 1: MyPlot = 0
                if rc == 1: PlotFile = 0
                plt.close() #se sotto l'if mostra tutte le curve fino a N_PLOT_EVENTS, se fuori mostra solo N_PLOT_EVENTS    
                return rc
            #plt.close() #se sotto l'if mostra tutte le curve fino a N_PLOT_EVENTS, se fuori mostra solo N_PLOT_EVENTS    

        

class Evento:
    
    def __init__(self):
        self.nevt           = 0     # N. evento corrente
        self.ntrigger       = 0     # quanti trigger compongono l'evento
        self.scintil_active = [0]*N_SIPM   # per ogni SiPM attivo metto parola a 1
        self.trigger_list   = []

 
    def CreaEvento(self, last_trigger):
        # mette insieme i trigger se quasi contemporanei
        if last_trigger.frag_flag > 0 :       # fragmentation flag
            if MyDebug > 1:
                print("\n Trigger n. %d frammentato"% self.ntrigger)
                last_trigger.PrintTrigger()
    ###            self.PrintEvento()
            if self.ntrigger ==0 :
                print ("\n inizia evento con fragmentation flag ==1")
                print ("\n Errore interno o dei dati - esco \n")
                sys.exit('file corrotto ?')
    		# aggiungo questo trigger frammentato al precedente con stesso SiPM
            base_trigger_found= False
            for sipm in range(self.ntrigger):
                if last_trigger.channel == self.trigger_list[sipm].channel:  #il numero del SiPM deve essere uguale
                    # if MyDebug>1:
                    #     self.PrintTrigger(last_trigger)
                    #     if MyDebug>1:
                    #         self.PrintEvento()
                    base_trigger_found = True
                    self.trigger_list[sipm].nsamples += last_trigger.nsamples # aggiorno n. samples
                    self.trigger_list[sipm].samples.extend(last_trigger.samples) # e li copio in coda ai precedenti
                    if MyDebug>2:
                        print("\n dopo aggiunta")
                        self.PrintEvento()
                        print("\n\n\n")
                    break
   # ogni trigger frammentato deve avere un trigger precedente con lo stesso SiPM                
            if not base_trigger_found: 
                if MyDebug > 1:
                    print ("\n\n ATTENZIONE c'e' un trigger frammentato senza trigger di base !")
                    self.PrintEvento()
                    last_trigger.PrintTrigger()
                    # sys.exit()
                
            return 
        
        if  self.ntrigger==0: # se e' vuoto, puo' capitare solo all'inizio
            self.trigger_list= []
            self.trigger_list.append(last_trigger.mydeepcopy()) 
            self.ntrigger=1
            self.scintil_active=[0]*N_SIPM
            chan = self.trigger_list[0].channel
            self.scintil_active[chan] = 1   # registro il segnale sullo scintillatore
            return 

    	# controllo se questo trigger e' dentro la finestra temporale col primo
        ## ignoro i secondi e i giorni
        if abs(last_trigger.tempo[3]-self.trigger_list[0].tempo[3]) < time_win : 
            chan = last_trigger.channel
            last_trigger.sequential = self.ntrigger
            self.ntrigger   += 1
            self.trigger_list.append(last_trigger.mydeepcopy() )
            self.scintil_active[chan] += 1 # registro il segnale sullo scintillatore
            return   # ho aggiunto trigger
    		
        else: # ho completato un blocco dati simultanei
            self.nevt += 1
            #if PlotFile ==1: pdf = matplotlib.backends.backend_pdf.PdfPages("output_graph.pdf")
            for tt in self.trigger_list:
                # if tt.nsamples>126:
                #     print ("\n trigger lungo ", tt.nsamples)
                tt.TogliPed_trigger() 
                (nstart, tpeak, t50, intercept, slope, quality_flag, shift, peak_value) = tt.findTime()
                #aggiungo informazioni temporali (t picco e t fit per constant fraction)
                tt.tpeak = tpeak #+ shift
                tt.t50=t50 #+ shift
                tt.intercept=intercept ##da modificare
                tt.slope=slope
                tt.quality_flag = quality_flag
                tt.Qcharge_flag = Qcharge_flag_port
                tt.peak_value = peak_value
                npeak = int (tpeak / SAMPLING_TIME)
                if MyPlot ==1 or PlotFile==1: tt.PlotTrigger(nstart, npeak, intercept, slope, quality_flag, shift, peak_value)
                
                if tt.nsamples> 200: 
                    # tt.PlotTrigger(nstart, npeak, intercept, slope)
                    MyData.nWarning_leng +=1 # trigger molto lungo
            # contiamo il numero di eventi per vari numeri di trigger
            if evento.ntrigger==1: MyData.ntot_single  += 1
            if evento.ntrigger==2: MyData.ntot_coinc2  += 1
            if evento.ntrigger==3: MyData.ntot_coinc3  += 1
            if evento.ntrigger==4: MyData.ntot_coinc4  += 1
            if evento.ntrigger>=5: MyData.ntot_coinc5  += 1
            # contiamo quali scintillatori hanno dato segnale
            MyData.total_count_per_sipm = [MyData.total_count_per_sipm[i] + \
                        evento.scintil_active[i] for i in range(N_SIPM)]
            MyData.ntot_evt = evento.nevt     
            #if MyPlot ==1 or PlotFile==1 : pdf.close()
                
    
            if MyDebug >0 : self.PrintEvento()
            MyData.scrivi_evento(self)
            
    # mostriamo i primi eventi
            if (self.nevt < N_DUMP_FIRST_EVENTS) and (MyDebug ==0): self.PrintEvento()
    
            #azzero  l'evento appena scritto e inserisco il trigger appena letto
            self.scintil_active=[0]*N_SIPM
            self.trigger_list.clear()
            self.trigger_list = list() #pronti per il prossimo
            # metto il primo che ho trovato
            self.trigger_list.append(last_trigger.mydeepcopy() )
            chan = last_trigger.channel
            self.scintil_active[chan]=1 # registro il segnale sullo scintillatore
            self.ntrigger = 1
            



    def TogliPed(self, baseline):
        # # togli i primi valori dai dati (assumendoli costanti)
        # baseline  # n. punti utilizzati per calcolare piedistallo
        for tt in self.trigger_list:
            tt.TogliPed_trigger(baseline)


    def PrintEvento(self):
        if MyDebug > 1:
            print("\n ************ ev. %d "% self.nevt)
            print("Evento costituito dai seguenti %d trigger" % self.ntrigger)
            for tt in self.trigger_list:
                tt.PrintTrigger ()
            print("\nScintillatori attivi: ", end="")
            print([i for i in range(N_SIPM) if self.scintil_active[i] !=0])
            print("\n --- Fine evento -----------\n\n")
        

class AP_DataRead():
    # classe per aprire il file di input, leggerlo trigger dopo trigger
    # creare i singoli eventi e scriverli in output
        
    
    
    def __init__(self, NEVMAX):            
        # dati globali del file
        self.ntot_trigger = 0  # n. trigger letti
        self.fragmented   = 0 # N. trigger frammentati
        self.nWarning_leng    = 0  # trigger molto lunghi
        self.nWarning_charge  = 0  # trigger per cui la carica calcolata non coincide con quella fornita
        self.ntot_evt    = 0  # n. eventi letti
        self.ntot_single = 0 # eventi con un solo SiPM
        self.ntot_coinc2 = 0 # eventi con  2 SiPM
        self.ntot_coinc3 = 0 # eventi con  3 SiPM
        self.ntot_coinc4 = 0 # eventi con  4 SiPM
        self.ntot_coinc5 = 0 # eventi con almeno 5 SiPM
        self.total_count_per_sipm = [0]*N_SIPM  # conteggio totale dei trigger su ogni SiPM
        
        # file di input e output, N. eventi da analizzare
        self.f_in  = None # file di input da analizzare   (.bin)
        self.f_out = None # file di output in formato txt
        self.NEVMAX = NEVMAX # numero di eventi da processare
        
    def OpenInputFile(self, InputFile, InputLog):
        self.f_in = open(InputFile, "rb")
        #self.fl_in = open(InputLog, "rb")
        print('File di input %s aperto correttamente: '% InputFile)
        #print('File di input %s aperto correttamente: '% InputLog)
        
    def OpenOutputFile (self, OutputFile, OutputLog):
        self.f_out = open(OutputFile,'wt')
        #self.fl_out = open(OutputLog,'wt')
        print ('File di output %s aperto correttamente\n' % OutputFile)
        #print ('File di output %s aperto correttamente\n' % OutputLog)
        
    def CloseAllOutputFile (self):
        self.f_in.close()
        self.f_out.close()
        #self.fl_in.close()
        #self.fl_out.close()
        print ("\n File di input e output chiusi correttamente\n")
        
  
        
    
    
    
    
    def scrivi_evento(self, evento):
        global t_a_prev
        global t_g_prev
        global d_a
        global d_g
        self.f_out.write("%d  %d \n" % (evento.nevt, evento.ntrigger))
        for tt in evento.trigger_list:
            if(tt.tempo[1]==364): 
                
                t_a_prev=2
            if(tt.tempo[2]==86399): 
                
                t_g_prev=2
            if(t_a_prev==2 and tt.tempo[1]==0): 
                
                d_a=(d_a-1)+2 #incremento per tenere conto del reset dei secondi e gioni(?)
                
                t_a_prev=1
            if(t_g_prev==2 and tt.tempo[2]==0): 
                
                d_g=(d_g-1)+2 #incremento per tenere conto del reset dei secondi e gioni(?)
                
                t_g_prev=1           
            #print("%d %d %d %d %d %d %d %d \n" % (tt.tempo[0], tt.tempo[1], tt.tempo[2], t_a_prev, t_g_prev, t_s_prev, d_a, d_g))
            tt.tempo[0] = tt.tempo[0] + d_a-1
            tt.tempo[1] = tt.tempo[1] + d_g-1
            #print("%d %d %d %d %d %d %d %d \n" % (tt.tempo[0], tt.tempo[1], tt.tempo[2], t_a_prev, t_g_prev, t_s_prev, d_a, d_g))
            
            # sipm, secondi,  ns, Q tot, # campioni
            self.f_out.write("%d %d %d %d %d %d %d " % (tt.channel, \
                    tt.tempo[0], tt.tempo[1], tt.tempo[2], tt.tempo[3], \
                    tt.carica_totale, tt.nsamples))
            #print("QchargFlatPort= ", Qcharge_flag_port)
            #print("QchargFlat= ", self.Qcharge_flag)    
            # indice  picco , indice campionamento dal fit al 50%, flag di qualita'
            self.f_out.write("%d %5.1f %d %d %d %d \n" % (tt.tpeak, \
                   tt.t50, tt.quality_flag, tt.intercept, tt.slope, tt.peak_value))
            #t_a_prev = tt.tempo[0]
            #t_g_prev = tt.tempo[1] 
            #t_s_prev = tt.tempo[2]
            # print("Distribuzione dei conteggi per SiPM")
            # [print (" %5d" % nn, end="") for nn in range(N_SIPM)]
            # print("\n")
            # [print (" %5d" % nn, end="") for nn in MyData.total_count_per_sipm]
            # print("\n")
            

                

if __name__ == "__main__":
    # ------------------------------------------------------------------
    # main program
    print ("\nProgramma di conversione formato dati per AstroPlano.  V2.0")
    print ("Gennaio 2022   - Flavio Fontanelli \n")
    

    MyData = AP_DataRead(NEVMAX)
    filedati_in = inputPath+inputFile + '.bin'
    filelog_in = inputPath+inputlog
    MyData.OpenInputFile(filedati_in, filelog_in)
    
    filedati_out = output_path + output_file
    fileWSVT_out = output_path + output_log
    MyData.OpenOutputFile(filedati_out, fileWSVT_out)
    

    evento =Evento()
    last_trigger = Trigger()
 
    ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''    
    '''Leggo il file log per parametri run e WS '''
    ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    voltage=[[],[],[],[],[],[],[],[],[],[],[],[]]
    soglie=[[],[],[],[],[],[],[],[],[],[],[],[]]
    temperatura=[[],[],[],[]]
    tensione=[[],[],[],[]]
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
        if Testo.startswith("Tensioni V del Sistema"):
            Testo=log.readline()
            for i in range(4):
                tensione[i]=float(Testo.split()[i])     
                
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
    ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''    
    '''Leggo il file per produrre i plot di controllo '''
    ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    if PlotMonitor==1:
        prova4 = open(output_file, "r")
        #aprire nuovo file per dati temperatura e pressione (in progress)
        #Wstation = open(r"C:\Users\User\AP20220224-wsd.txt", "r")'''
        eventi=[''] #inseriamo un valore per far sì che il numero dell'evento coincida con
                    #l'indice inserito di sotto.
        rate=[0,0,0,0,0,0,0,0,0,0,0,0]
        rateLS=[0,0,0,0,0,0,0,0]            
         
        #check=True    #romosso perche mi sono accorto essere inutile

        #Trun = 6; # tempo run espresso in ore
        print("leggo il file Output", output_file)
        while True:            #sostituisco check con True
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

                riga_vect = riga.split()   #separa gli elementi di ogni trigger (n. SIM/
                                           #tempo in sec ecc...)

                for j in range(len(riga_vect)):     # sarà sempre 9
                    riga_vect[j] = float(riga_vect[j])    #creiamo la terza dimensione
            evento_n.append(riga_vect)   #creiamo la seconda dimensione
            
            eventi.append(evento_n)   #creiamo la prima dimensione   
        print("Ultimo evento n. ", n_trigger[0])   
        tempos =[[],[],[],[],[],[],[],[],[],[],[],[]]
        carica = [[],[],[],[],[],[],[],[],[],[],[],[]]
        carica_barra_L = [[],[],[],[],[]]
        tcf = [[],[],[],[],[],[],[],[],[],[],[],[]]
        last_event=len(eventi)-1        
        #Trun = eventi[last_event][0][1]-eventi[1][0][1]+(eventi[last_event][0][2]-eventi[1][0][2])/1e9
        #nuova definizione del formato dati che comprende anche anno e giorno
        Trun = (eventi[last_event][0][1]-eventi[1][0][1])*3.154e+7+(eventi[last_event][0][2]-eventi[1][0][2])*86400+eventi[last_event][0][3]-eventi[1][0][3]+(eventi[last_event][0][4]-eventi[1][0][4])/1e9
        '''
        if(eventi[last_event][0][1]<eventi[1][0][1]):#nel caso il contatore dei secondi si resetti durante il run
            for i in range(len(eventi)):
                j=i-1
                if(j!=-1):
                    if(eventi[i][0][1]==0 and eventi[j][0][1]>eventi[i][0][1]): Trun = eventi[j][0][1]-eventi[1][0][1]+eventi[last_event][0][1]+(eventi[j][0][2]-eventi[1][0][2]+eventi[last_event][0][2])/1e9
        '''       
        #print("Tempo totale Run: ", Trun)  
        for i in range (len(eventi)):
            for j in range (len(eventi[i])):
              if (eventi[i][j][9]!=1):
                channel = int(eventi[i][j][0])
                valore = rate[channel]
                #rate[channel] =  valore + 1/(Trun*60*60)
                t=eventi[i][j][3]*1e9+eventi[i][j][4]-(eventi[1][0][3]*1e9+eventi[1][0][4])
                tempos[channel].append(t)
                carica[channel].append(eventi[i][j][5]/10000)
      
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
        # XXXXXXXXXXXXXXXXXX #
           X              X           PIANO SUPERIORE
           X              X
        # XXXXXXXXXXXXXXXXXX #
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
        ##Set Binari
        if AngPlot==1:
            Ang=[0,42.3,59.9,67.8,73.0,76.5]        
            Ang_err=[12.8,6.35,3.0,1.8,1.1,0.7]
        ##Set Alternativo
        if AngPlot==2:
            Ang=[0,24.4,51.8,71.0,75.0,76.5]        
            Ang_err=[12.8,9.9,4.5,1.3,0.8,0.7]
        
        if AngPlot>0:
            for i in range (len(eventi)):
                for j in range(len(eventi[i])):
                    if (eventi[i][j][0] == 8 and eventi[i][j][7]!=1): # cerco primo canale corto
                        for l in range(len(eventi[i])):
                            if (l!=j and eventi[i][l][0] == 10 and eventi[i][l][7]!=1): countAng[0]=countAng[0]+1/Trun
                            if (l!=j and eventi[i][l][0] == 0 and eventi[i][l][7]!=1): countAng[1]=countAng[1]+1/Trun
                            if (l!=j and eventi[i][l][0] == 1 and eventi[i][l][7]!=1): countAng[2]=countAng[2]+1/Trun
                            if (l!=j and eventi[i][l][0] == 2 and eventi[i][l][7]!=1): countAng[3]=countAng[3]+1/Trun
                            if (l!=j and eventi[i][l][0] == 3 and eventi[i][l][7]!=1): countAng[4]=countAng[4]+1/Trun
                            if (l!=j and eventi[i][l][0] == 11 and eventi[i][l][7]!=1): countAng[5]=countAng[5]+1/Trun
                    if (eventi[i][j][0] == 9 and eventi[i][j][7]!=1): # cerco primo canale corto
                        for l in range(len(eventi[i])):
                            if (l!=j and eventi[i][l][0] == 10 and eventi[i][l][7]!=1): countAng[5]=countAng[5]+1/Trun
                            if (l!=j and eventi[i][l][0] == 0 and eventi[i][l][7]!=1): countAng[4]=countAng[4]+1/Trun
                            if (l!=j and eventi[i][l][0] == 1 and eventi[i][l][7]!=1): countAng[3]=countAng[3]+1/Trun
                            if (l!=j and eventi[i][l][0] == 2 and eventi[i][l][7]!=1): countAng[2]=countAng[2]+1/Trun
                            if (l!=j and eventi[i][l][0] == 3 and eventi[i][l][7]!=1): countAng[1]=countAng[1]+1/Trun
                            if (l!=j and eventi[i][l][0] == 11 and eventi[i][l][7]!=1): countAng[0]=countAng[0]+1/Trun                            
        
        
        
        '''Disegno i Grafici''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''' 
        file_uno = open("Rate.txt", "w")

        for j in range(8):
            for i in range(len(countLS_t[j])):
                tempoG[j].append(i*rate_scan)
                #if((countLS_t[j]-countLS[j])/countLS[j]>0 and (countLS_t[j]-countLS[j])/countLS[j]>0.1): countLS_t[j]=countLS[j]+countLS[j]*0.1
                #if((countLS_t[j]-countLS[j])/countLS[j]<0 and (countLS_t[j]-countLS[j])/countLS[j]<-0.1): countLS_t[j]=countLS[j]-countLS[j]*0.1
        with PdfPages(outmonitor) as pdf:
            fig = plt.figure(figsize=(15,7.5))
            for i in range(12):
                j=i+1
                plt.subplot(3, 4, j)
                n, bins, patches = plt.hist(carica[i], 100, range=[0, 20], density=False, facecolor='green', alpha=0.75)
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
                
                print("Valore medio coinc LS ", LS_string[i], " = ", round(statistics.mean(carica_barra_LS[i]),3), " +- ", round(statistics.stdev(carica_barra_LS[i]),3))
                file_uno.write("Valore medio Rate coinc LS %s = %.3f +- %.3f hz \n"% ( LS_string[i], round(statistics.mean(carica_barra_LS[i]),3),  round(statistics.stdev(carica_barra_LS[i]),3)))
                
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
                print("Rate coinc SS  ", SS_string[i], " = ", round(countSS[i],3), " +- ", round(math.sqrt(countSS[i]/Trun),3), " Hz")
                file_uno.write("Valore medio Rate coinc SS %s = %.3f +- %.3f hz \n"% ( SS_string[i], round(countSS[i],3),  round(math.sqrt(countSS[i]/Trun),3)))

            for i in range(2):    
                print("Rate coinc SSd ", SSd_string[i], " = ", round(countSSd[i],3), " +- ", round(math.sqrt(countSSd[i]/Trun),3), " Hz")
                file_uno.write("Valore medio Rate coinc SSd %s = %.3f +- %.3f hz \n"% ( SSd_string[i], round(countSSd[i],3),  round(math.sqrt(countSSd[i]/Trun),3)))
                
            for i in range(2):
                print("Rate coinc LL  ", LL_string[i], " = ", round(countLL[i],3), " +- ", round(math.sqrt(countLL[i]/Trun),3), " Hz")
                file_uno.write("Valore medio Rate coinc LL %s = %.3f +- %.3f hz \n"% ( LL_string[i], round(countLL[i],3),  round(math.sqrt(countLL[i]/Trun),3)))
                
            for i in range(2):
                print("Rate coinc LLd ", LLd_string[i], " = ", round(countLLd[i],3), " +- ", round(math.sqrt(countLLd[i]/Trun),3), " Hz")
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
            plt.errorbar(tempolog,deltaV[0], 0.054, linestyle='none',marker='.', label="DV sipm piano basso")
            plt.legend(loc='best', fontsize=11)
            #plt.title('DV sipm piano:  0')
            #plt.subplot(2, 2, 4)
            plt.errorbar(tempolog,deltaV[1], 0.054, linestyle='none',marker='.', label="DV sipm piano alto")
            plt.title('DV sipm piano')
            plt.legend(loc='best', fontsize=11)
            plt.ylabel("DeltaV(Volt)")
            plt.xlabel("Time(second)")               
            
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
                plt.ylim([0.2, 0.5])
                plt.axhline(y=countLS[i], color='r', linestyle='-')
                plt.axhline(y=countLS[i]+math.sqrt(countLS[i]/Trun), color='grey', linestyle='--')
                plt.axhline(y=countLS[i]-math.sqrt(countLS[i]/Trun), color='grey', linestyle='--')
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
            plt.errorbar(tempoG[0],countLL_t[0], countLL_t_err[0], marker='.', linestyle='none')
            plt.ylim([0.5, 0.9])
            plt.axhline(y=countLL[0], color='r', linestyle='-')
            plt.axhline(y=countLL[0]+math.sqrt(countLL[0]/Trun), color='grey', linestyle='--')
            plt.axhline(y=countLL[0]-math.sqrt(countLL[0]/Trun), color='grey', linestyle='--')            
            plt.title('Rate LL ' + LL_string[0])
            plt.ylabel("Rate(Hz)")
            plt.xlabel("Time(second)") 
            
            plt.subplot(2, 2, 2)
            plt.errorbar(tempoG[1],countLL_t[1], countLL_t_err[1], marker='.', linestyle='none')
            plt.ylim([0.5, 0.9])
            plt.axhline(y=countLL[1], color='r', linestyle='-')
            plt.axhline(y=countLL[1]+math.sqrt(countLL[1]/Trun), color='grey', linestyle='--')
            plt.axhline(y=countLL[1]-math.sqrt(countLL[1]/Trun), color='grey', linestyle='--')              
            plt.title('Rate LL ' + LL_string[1])
            plt.ylabel("Rate(Hz)")
            plt.xlabel("Time(second)") 
                      
            plt.subplot(2, 2, 3)
            plt.errorbar(tempoG[0],countSS_t[0], countSS_t_err[0], marker='.', linestyle='none')
            plt.ylim([0.1, 0.4])
            plt.axhline(y=countSS[0], color='r', linestyle='-')
            plt.axhline(y=countSS[0]+math.sqrt(countSS[0]/Trun), color='grey', linestyle='--')
            plt.axhline(y=countSS[0]-math.sqrt(countSS[0]/Trun), color='grey', linestyle='--')             
            plt.title('Rate SS ' + SS_string[0])
            plt.ylabel("Rate(Hz)")
            plt.xlabel("Time(second)") 
            
            plt.subplot(2, 2, 4)
            plt.errorbar(tempoG[1],countSS_t[1], countSS_t_err[1], marker='.', linestyle='none')
            plt.ylim([0.1, 0.4])
            plt.axhline(y=countSS[1], color='r', linestyle='-')
            plt.axhline(y=countSS[1]+math.sqrt(countSS[1]/Trun), color='grey', linestyle='--')
            plt.axhline(y=countSS[1]-math.sqrt(countSS[1]/Trun), color='grey', linestyle='--')              
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
                y = np.array(countAng)
                popt , pcov = curve_fit(cosq,x,y,p0=[2, 2])
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
                    countAng_err[i]=math.sqrt(countAng[i]*Trun)/Trun

                #plt.plot(x,y,label='data')
                plt.errorbar(Ang,countAng, countAng_err, Ang_err, marker='.', linestyle='none') 
                plt.plot(x,cosq(x,*popt),'ro:',label='fit') 
                               
                plt.title('Rate Angular Distribution')
                plt.ylabel("Rate(Hz)")
                plt.xlabel("Angle")             
                if(PlotStop==1): plt.show(block=True)
                fig.tight_layout()            
                pdf.savefig(fig) 
        
        plt.close()
    ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''    
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
