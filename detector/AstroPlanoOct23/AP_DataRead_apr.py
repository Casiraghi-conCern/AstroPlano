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
from scipy import stats
import sys

# stato di ritorno dalle funzioni
BAD = False
GOOD = True

# parametri da settare all'inizio

#inputPath = "../AstroPlano_sep21/"	#path input file
#inputFile = "AP_ven_cfg_old" 		# file corrotto (sipm>11)

inputPath = "../dati/"		        # path input file
inputFile = "HiG_Thr50_25" 		    # input file name without extension

output_path = "./"		#idem for output
output_file = inputFile+"prova" + "_dst.txt"

#numero di eventi da processare (-1 = tutti)
NEVMAX =  1000   # 9999999    

# costanti che potremmo dover cambiare
time_win = 400    # ns,  lunghezza max finestra temporale di un evento
MyDebug    = 0      # 0 no debug, 1 minimale, 2 esteso, 3 tutto
MyPlot     = 0      # 0 no plot, 1 plot si
N_DUMP_FIRST_EVENTS = 0   # numero degli eventi iniziali che vengono stampati

# altro non cambiare se non sai quello che fai
N_SIPM =12
SAMPLING_TIME =4  # 4 ns periodo di campionamento (f=250 MHz)
baseline =3 # numero dei campionamenti  iniziali da usare, mediando, come piedistallo
LeadingEdgeFit = True   #False  # per accelerare i test se non ti interessa il fit

plt.ion()

def myLinearRegression (x,y):
    # calcola il fit lineare al fronte di salita del trigger
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    if MyDebug>1: 
        print("\nslope: %8.2f    intercept: %11.2f, correl. %5.2f, errore slope: %8.2f " % (
                       slope, intercept, r_value, std_err))
    return (slope, intercept, r_value, std_err)
    

def move_figure(position="top-right"):
    '''
    Move and resize a window to a set of standard positions on the screen.
    Possible positions are:
    top, bottom, left, right, top-left, top-right, bottom-left, bottom-right
    '''

    mgr = plt.get_current_fig_manager()
    mgr.full_screen_toggle()  # primitive but works to get screen size
    py = mgr.canvas.height()
    px = mgr.canvas.width()

    d = 10  # width of the window border in pixels
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
        self.quality_flag = None
    
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
        xx.t50 = self.t50
        xx.quality_flag = self.quality_flag
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
            if MyDebug >1:
                print("\n N campioni: %d"% self.nsamples)
                print("\n\n ATTENZIONE Q sbagliata ?? Q waveboard: %d, Q ricalcolata: %d"% \
                  (self.carica_totale, Carica_ricalcolata))
            return BAD
        else:
            return GOOD
    
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
        return  rc   # tutto bene



    def PrintTrigger(self):
        print ("\nTrigger n. %d"% self.sequential) 
        print(" SiPM: %d, Year: %d, Days: %d, secs: %d,  ns: %d"% \
              (self.channel, self.tempo[0],self.tempo[1], self.tempo[2], self.tempo[3]) )
        print("Fragm flag: %d, Q tot: %d, Fifo full: %d, N. samples: %d"%(
              self.frag_flag, self.carica_totale, self.fifofull, self.nsamples), end="")
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

            
            
    def TogliPed_trigger(self, baseline=3):
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
        LOW_CUT = 0.10
        HIGH_CUT= 0.9
        
        nsamp= self.nsamples
        samp = self.samples
        peak_value = max(samp)
        npeak = samp.index(peak_value)
        tpeak = npeak* SAMPLING_TIME
        nstart = 0
        nstop = npeak
        
    	# cerco t per cui il valore <= LOW_CUT * valore massimo partendo dal picco
        for index in range(npeak, 0, -1):  
            if samp[index]> LOW_CUT*peak_value: continue
            nstart = index
            break
        for index in range(nstart, nsamp):   # idem valore > HIGH_CUT * valore massimo
            if samp[index]<HIGH_CUT*peak_value: continue
            nstop=index
            break
        
        #fit del fronte di salita con retta, voglio migliorare timing
        const_frac = 0
        x= list(range(nstart*SAMPLING_TIME, (nstop+1)*SAMPLING_TIME, SAMPLING_TIME))
        y= samp[nstart: nstop+1]
        # devo avere almeno 2 punti per fare il fit
        if (nstop-nstart) >= 2 and LeadingEdgeFit: # posso fare fit
            slope,intercept, correlazione, errore_slope = myLinearRegression(x, y)
            halfpeak= peak_value *0.50
            const_frac = (halfpeak - intercept )/slope
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
        return (nstart, tpeak, const_frac, intercept, slope, quality_flag)
     
        
     
    def PlotTrigger(self, nstart, npeak, intercept, slope):
        # grafica un trigger in funzione del tempo   
        global MyPlot
        tempi= list(range(0, self.nsamples*SAMPLING_TIME, SAMPLING_TIME))
        n0 = nstart
        n1= min (self.nsamples, npeak+1)

        plt.plot(tempi, self.samples, '.', label='original data')
        yfit = [intercept + slope*xd for xd in tempi[n0:n1]]
        plt.plot(tempi[n0:n1], yfit, 'r', label='fitted line')
        plt.grid(visible=True, which='both', axis='both')
        plt.xlabel('ns')
        # plt.legend()
        plt.title("Evt: %d, N. seq trg: %d, SiPM: %d" % \
                  (evento.nevt, self.sequential, self.channel))
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
        plt.close()
        return rc

class Evento:
    
    def __init__(self):
        self.nevt           = 0     # N. evento corrente
        self.ntrigger       = 0     # quanti trigger compongono l'evento
        self.scintil_active = [0]*N_SIPM   # per ogni SiPM attivo metto parola a 1
        self.trigger_list   = []

 
    def CreaEvento(self, last_trigger):
        # mette insieme i trigger se quasi contemporanei
        global MyDebug
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
                print ("\n\n ATTENZIONE c'e' un trigger frammentato senza trigger di base !")
                self.PrintEvento()
                last_trigger.PrintTrigger()
                MyDebug =1
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
            for tt in self.trigger_list:
                # if tt.nsamples>126:
                #     print ("\n trigger lungo ", tt.nsamples)
                tt.TogliPed_trigger() 
                (nstart, tpeak, t50, intercept, slope, quality_flag) = tt.findTime()
                #aggiungo informazioni temporali (t picco e t fit per constant fraction)
                tt.tpeak = tpeak
                tt.t50=t50
                tt.quality_flag = quality_flag
                npeak = int (tpeak / SAMPLING_TIME)
                if MyPlot ==1: tt.PlotTrigger(nstart, npeak, intercept, slope)
                if tt.nsamples> 200: 
                    # tt.PlotTrigger(nstart, npeak, intercept, slope)
                    MyData.nWarning_leng +=1 # trigger molto lungo
            # contiamo il numero di eventi per vari numeri di trigger
            if evento.ntrigger==1: MyData.ntot_single  += 1
            elif  evento.ntrigger==2: MyData.ntot_coinc2  += 1
            elif evento.ntrigger==3: MyData.ntot_coinc3  += 1
            elif evento.ntrigger==4: MyData.ntot_coinc4  += 1
            elif evento.ntrigger>=5: MyData.ntot_coinc5  += 1
            else: 
                print ("\n\nerrore interno conteggio trigger !!!\n\n")
                sys.exit()
                
            # contiamo quali scintillatori hanno dato segnale
            MyData.total_count_per_sipm = [MyData.total_count_per_sipm[i] + \
                        evento.scintil_active[i] for i in range(N_SIPM)]
            MyData.ntot_evt = evento.nevt     
    
            if MyDebug >0: 
                self.PrintEvento()
            MyData.scrivi_evento(self)
            
            # mostriamo i primi eventi
            if (self.nevt < N_DUMP_FIRST_EVENTS) and (MyDebug ==0): self.PrintEvento()
    
            #azzero  l'evento appena scritto e inserisco il trigger appena letto
            self.scintil_active=[0]*N_SIPM
            self.trigger_list.clear()
            self.trigger_list = list() #pronti per il prossimo
            # metto il primo che ho trovato
            last_trigger.sequential=0
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
        
    def OpenInputFile(self, InputFile):
        self.f_in = open(InputFile, "rb")
        print('File di input %s aperto correttamente: '% InputFile)
        
    def OpenOutputFile (self, OutputFile):
        self.f_out = open(OutputFile,'wt')
        print ('File di output %s aperto correttamente\n' % OutputFile)
    
    def CloseAllOutputFile (self):
        self.f_in.close()
        self.f_out.close()
        print ("\n File di input e output chiusi correttamente\n")
        
  
        
    
    
    
    
    def scrivi_evento(self, evento):
        self.f_out.write("%d  %d \n" % (evento.nevt, evento.ntrigger))
        for tt in evento.trigger_list:
            # sipm, secondi,  ns, Q tot, # campioni
            self.f_out.write("%d %d %d %d %d " % (tt.channel, \
                    tt.tempo[2], tt.tempo[3], \
                    tt.carica_totale, tt.nsamples))
                
            # indice  picco , indice campionamento dal fit al 50%, flag di qualita'
            self.f_out.write("%d %5.1f %d \n" % (tt.tpeak, \
                   tt.t50, tt.quality_flag))
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
    MyData.OpenInputFile(filedati_in)
    
    filedati_out = output_path + output_file
    MyData.OpenOutputFile(filedati_out)
    
    evento =Evento()
    last_trigger = Trigger()
    
    while MyData.ntot_trigger <  NEVMAX  or NEVMAX <0:      
        # leggo i dati relativi al singolo trigger (un SIPM)
        rc=last_trigger.LeggiTrigger() 
        if rc == None: break  # fine dati (EOF)
        if MyData.ntot_trigger % 10000 == 0: print ("Trigger n. %d"% MyData.ntot_trigger)   
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
