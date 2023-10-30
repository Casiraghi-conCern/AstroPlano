# -*- coding: utf-8 -*-
"""
Created on Jul 2020
@author: F. Fontanelli

mappa scintillatori:
    3 XXXXXXXXXXXXXXXX 2
       X            X           PIANO SUPERIORE
       X            X
    1 XXXXXXXXXXXXXXXX 0
       X            X
       8            9
       
    7 XXXXXXXXXXXXXXXX 6
       X            X           PIANO INFERIORE
       X            X
    5 XXXXXXXXXXXXXXXX 4
       X            X
       10           11
"""
import copy
from time import sleep
#from  numpy import arange
import astrosettings  as A_S
import AstroPlanoGui_class
import astro_hist as hi

f=None
ntot=0 # n. totale di trigger acquisiti
channel=-1 # il SiPM attivo
conteggio_scintillatori =[0]*A_S.astrodata.N_CHAN
cum_scint=[0]*A_S.astrodata.N_SiPM # conteggi totali di ogni SiPM 
N_COINC=15
coincidenze = [0]*N_COINC
soglia_amp = 300  # da vedere, soglia su ampiezza minima, uguale su tutti i canali
soglia_q = 20000  # da vedere, soglia su carica minima, uguale su tutti i canali

time_win = 100 # ns*4 , larghezza della coincidenza
debug = 0  # 0 no debug, 1 minimale, 2 esteso, 3 tutto

class Trigger(object):
    channel=None
    anno=None
    giorni=None
    secondi=None
    startTime=None
    comprFlag=None
    fragFlag=None
    fifoFull=None
    totalCharge=None
    pedmedio=None
    nSamples=None
    samples=[]
		
    def __init__(self):
        self.channel     = None
        self.anno        = None
        self.giorni      = None
        self.secondi     = None
        self.startTime   = None
        self.comprFlag   = None
        self.fragFlag    = None
        self.fifoFull    = None
        self.totalCharge =  0
        self.pedmedio    =  0
        self.nSamples    = None
        self.samples     = []

# ma serve ?
    def addTrigger(self, ch, anno, giorni, secondi, st, comprFlag, fragFlag, 
                   fifoFull, totQ, NSa, samp):
        self.channel     = ch
        self.anno        = anno
        self.giorni      = giorni
        self.secondi     = secondi
        self.startTime   = st
        self.comprFlag   = comprFlag
        self.fragFlag    = fragFlag
        self.fifoFull    = fifoFull
        self.totalCharge = totQ
        self.nSamples    = NSa
        self.samples     = samp.copy()
			
    def printTrigger(self, debug=0):
        print("Trigger ch. %d, ns: %d, Q: %d, n. samples: %d \n"%
				  (self.channel, self.startTime, self.totalCharge, self.nSamples))
        if debug>0:
                print("samples:")
                npr=0
                for i in self.samples:
                    if npr%10 == 0: print("\n")
                    print ("%7.1f " % i, end=" ")
                    npr=npr+1
                print("\n")
				
	# controllo che la carica fornita da WB sia uguale alla somma dei sample,
	#   cosi'sembra essere, per cui ho commentato
	#    print ("Carica totale da WB: %d" % trig[7])
	#    myQ=0
	#    for q in trig[10]:
	#        myQ= myQ+ q
	#    print("\n carica sommata %d"% myQ)
		
    def sottraiPedTrigger(self):
    # calcola il piedistallo medio sui primi campionamenti e lo sottrae a tutti
        baseline =10
        ns = self.nSamples
        if ns<baseline:
            print ("\n Trigger troppo corto, non posso togliere il piedistallo")
            print ("\nns= %d, baseline= %d "% (ns, baseline))
            self.printTrigger()
            return
        self.pedmedio = 0
        for p in range(baseline):
            self.pedmedio= self.pedmedio+self.samples[p]
        self.pedmedio /= baseline
        
#oltre a sottrarre il piedistallo, aggiorna la carica totale  
        self.totalCharge = 0.
        for p in range (ns):
            # qui usa reduce FFX
            self.totalCharge += self.samples[p]
            self.samples[p] -= self.pedmedio
            if self.samples[p]<0: self.samples[p]=0.

    def leggiTrigger(self, f, debug=0):
    # leggo header, problema e' True finche' non sono riuscito a leggerlo
    # ritorna None se sono alla fine del file, altrimenti il numero del SiPM
        problema = True
        while problema:
            ihead1 = self.leggiHeader1(f)
            if ihead1 == None: return None  # EOF 
            problema = False       #ok, ho letto la prima DWORD del data frame: header1    
            #self.channel = ihead1 % 15
            self.channel = ((ihead1>>0) & 0xF)
            Board = (ihead1>>4) % 32
            if debug>=2: print("\nHeader 1: %X, Board: %X, canale: %X"% (ihead1, Board, channel))
            self.samples =[]
    
        else:           
            if debug>=2: 
                print("\nsync byte OK, Header 1: %X, Board: %X, canale: %d"% \
                      (ihead1, Board, channel))
            # header 2
            head2 = f.read(8)
            ihead2 = int.from_bytes(head2, byteorder='little')
            if debug>=2: print("Header 2: %X"% ihead2 )
            decanno = ihead2>>60
            anno =    (ihead2>>56) % 16
            self.anno = decanno*10 + anno
            
            cengiorni = (ihead2>>54) % 4
            decgiorni = (ihead2>>50) % 16
            giorni = (ihead2>>46)% 16
            self.giorni = cengiorni*100+decgiorni*10+ giorni
            
            self.secondi = (ihead2>>29)  & 0x1FFFF
            us125 = (ihead2 >> 16)& 0X1FFF    
            usec = us125 *125     #  forse per 125000 ?? da capire
            ns = ihead2 &0XFFFF
#            self.startTime= usec*1000 + ns
            self.startTime = ns
            if debug>=1: print("\nAnno: %d, giorno: %d, secondi: %d, ns: %d" %
                    (self.anno, self.giorni, self.secondi, self.startTime))
            # header 3
            head3 = f.read(4)
            ihead3 = int.from_bytes(head3, byteorder='little')
            if debug>=2 : print("Header 3: %X"% ihead3 )     
            self.comprFlag = ihead3 >>31
            if self.comprFlag!= 0:
                print("\n\n Attenzione flag di compressione attivo!! \n NON previsto !!")
                print ("\n Non so gestirlo, esco\n")
                exit()
                
            self.fragFlag = (ihead3>>30) & 0x01
            self.totalCharge = (ihead3>>8) & 0x3FFFFF
            self.fifoFull = (ihead3>>7)& 1
            nsamp = ihead3 & 0X7F
            if debug>= 2: 
                print("\nFlag compr: %1d, flag framment: %1d, carica totale %d, flag FIFO pieno: %1d" %
                    (self.comprFlag, self.fragFlag, self.totalCharge, self.fifoFull))
                print("\nN. campioni per questo evento: %d "% nsamp)
            if (nsamp%2 != 0):  self.nSamples=nsamp+1    #se e' dispari
            else:  self.nSamples = nsamp
    
            for i in range(self.nSamples):
                samp = f.read(2)
                isamp = (int.from_bytes(samp, byteorder='little'))& 0X3FFF
                self.samples.append(isamp) 
                if debug>=3:
                    print("Sample n. %d: %d ossia %X"% (i, isamp, isamp))
            if debug >= 1: 
               self.printTrigger(debug)
            return self.channel


    def leggiHeader1(self, f):
        key1=b'\xAA'
        key2=b'\x55'
        head1 = f.read(4)
    
        if head1 == b'':   # EOF reached
            return None
        ihead1= int.from_bytes(head1, byteorder='little')
        syncBytes = ihead1>>16
        if syncBytes == 0X55AA: return ihead1
        # tento di ricuperare un file corrotto cercando la stringa 0x55AA
        # funzionalita' da controllare se dovesse succedere
        print(" Evento %d, Trigger anomalo: Header 1: %X" %(ntot, ihead1))
        c1=0
        nerr=0
        while c1 != key1:       #devo trovare 0x55
            c1=f.read(1)
            nerr = nerr +1
            if c1 != b'\x00': print('\n nerr=%d, c1= %X' %
                              (nerr, int.from_bytes(c1,byteorder='little')))
            if c1 != key1: continue
            c2=0                #trovato, adesso cerco 0xAA
            while c2 != key2:
                c2 = f.read(1)
                if c2 == key2:  #trovato 0x55, leggo gli altri 2 bytes e ritorno
                    c3=f.read(1)
                    c4= f.read(1)
                    head1= int.from_bytes(c1,byteorder='little')
                    head1 = head1<<8
                    head1 = head1 | int.from_bytes(c2,byteorder='little')
                    head1 = head1<<8
                    head1 = head1 | int.from_bytes(c3,byteorder='little')
                    head1 = head1<<8
                    head1 = head1 | int.from_bytes(c4,byteorder='little')
                    return head1
                elif c2 == key1:    # ho trovato 0Xaa, riprendo a cercare c2
                    c1=c2
                    continue
                else:       #esco dal loop piu' interno 
                    break
                continue     # e continuo quello esterno
     
    
                


#  classe evento
class AstroPlanoEvento(object):
    def __init__(self):
        self.nTrigger = 0
# per ogni SiPM attivo metto  a 1 l'elemento corrispondente
        self.scintilActive = [0]*A_S.astrodata.N_SiPM     
        self.trigs   = []      # lista di Trigger
    
    def clearEvent(self):
        self.nTrigger = 0
        self.scintilActive = [0]*A_S.astrodata.N_SiPM     
        self.trigs   = []      # lista di Trigger
        
    
    def printEvento(self, debug=0):
        print("\n ************")
        print("Evento costituito da %d trigger" % self.nTrigger)
        print("Scintillatori attivi: ", end="")
        print([i for i in range(A_S.astrodata.N_SiPM) if self.scintilActive[i] !=0])
        for tr in self.trigs:
            tr.printTrigger(debug)
			
			
    def sottraiPedEv(self, debug=False):
# sottrae il piedistallo a tutti i trigger dell'evento
        for tt in range(self.nTrigger):
            self.trigs[tt].sottraiPedTrigger()

	
    def addTriggerToEvent(self, lastTrigger, debug=0):
# aggiunge i trigger all'evento se sono circa simultanei, ritorna il numero dei trigger
# ritorna -1 se l'evento e' completo e non e' stato possibile aggiungere un altro trigger        
        if lastTrigger.fragFlag  >0 :       # fragmentation flag
            if debug>0:
                print("\n Trigger n. %d frammentato"% lastTrigger.channel)
                lastTrigger.PrintTrigger(debug)
                self.PrintEvento(debug)
            if self.nTrigger ==0 :
                print ("\n inizia evento con fragmentation flag ==1")
                print ("\n Errore interno o dei dati - esco \n")
                exit() #magari potremmo provare a ignorarlo e vedere cosa succede
                # per ora non e' mai capitato
            for sipm in range(self.nTrigger):
                if lastTrigger.channel == self.trigs[sipm].channel:  #il numero del SiPM deve essere uguale
    # controllo che in effetti il pezzo di trigger sia +/- contemporaneo al candidato
                    if abs(lastTrigger.startTime - self.trigs[sipm].startTime)> time_win:
                        print ('\n Evento frammentato con tempi molto diversi, sospetto !!\n')
                        
                    self.trigs[sipm].nSamples += lastTrigger.nSamples
                    self.trigs[sipm].samples.extend(lastTrigger.samples)
                    if debug>1:
                        print("\n dopo l'aggiunta del frammento: ")
                        self.printEvento(debug)
                        print("\n\n\n")
                    break
            return self.nTrigger
        
        ch = lastTrigger.channel
        if ch >11:
            debug=1
            print ("\n trigger impossibile  "+str(ch))
            lastTrigger.printTrigger(1)
            self.printEvento(1)
        
        cum_scint[ch] += 1  # se non e' frammento devo sicuramente incrementare
        if  self.nTrigger==0: # se e' vuota    
            self.trigs.append( copy.deepcopy(lastTrigger) )
            self.nTrigger=1
            self.scintilActive=[0]*A_S.astrodata.N_SiPM
            self.scintilActive[ch]=1        # registro il segnale sullo scintillatore
            return 1
        
        if abs(lastTrigger.startTime-self.trigs[0].startTime) < time_win:
            self.trigs.append( copy.deepcopy(lastTrigger))
            self.nTrigger += 1
            self.scintilActive[ch] += 1 # registro il segnale sullo scintillatore
            return  self.nTrigger
        else: # ho trovato un blocco dati simultanei
            if debug>=1: self.printEvento(debug)
            #riempiamo il vettore con i SiPM con segnale
#            for i in self.trigs:
#                nc = i.channel
#                self.scintilActive[nc] +=1
# toglie il piedistallo a tutti i  trigger                
            self.sottraiPedEv()
            return -1            
                 
                
    def analizza(self, debug=0):
        if debug>=2:
            print ('\n\nTrigger evento: ')
            for i in range(A_S.astrodata.N_SiPM):
                print ('%6d '%i,end='')
            print('\n')
            for i in range(A_S.astrodata.N_SiPM):
                print ('%6d '%self.scintilActive[i],end='')
    
        if (self.scintilActive[0]==1) & (self.scintilActive[1]==1): coincidenze[0] += 1
        if (self.scintilActive[2]==1) & (self.scintilActive[3]==1): coincidenze[1] += 1
        if (self.scintilActive[4]==1) & (self.scintilActive[5]==1): coincidenze[2] += 1
        if (self.scintilActive[6]==1) & (self.scintilActive[7]==1): coincidenze[3] += 1
        #coincidenze doppie lunghe
        if ((self.scintilActive[0]==1) | (self.scintilActive[1]==1)) &  \
           ((self.scintilActive[4]==1) | (self.scintilActive[5]==1)):
                coincidenze[4] += 1
    
        if ((self.scintilActive[2]==1) | (self.scintilActive[3]==1)) &  \
           ((self.scintilActive[6]==1) | (self.scintilActive[7]==1)):
                coincidenze[5] += 1
    
        if ((self.scintilActive[2]==1) | (self.scintilActive[3]==1)) &  \
           ((self.scintilActive[4]==1) | (self.scintilActive[5]==1)):
                coincidenze[6] += 1
    
        if ((self.scintilActive[0]==1) | (self.scintilActive[1]==1)) &  \
           ((self.scintilActive[6]==1) | (self.scintilActive[7]==1)):
               coincidenze[7] += 1
    #coincidenze doppie corte
        if ((self.scintilActive[8]==1) & (self.scintilActive[10]==1)):
               coincidenze[8] += 1
               
        if ((self.scintilActive[9]==1) & (self.scintilActive[11]==1)):
               coincidenze[9] += 1
               
        if ((self.scintilActive[8]==1) & (self.scintilActive[11]==1)):
               coincidenze[10] += 1
               
        if ((self.scintilActive[9]==1) & (self.scintilActive[10]==1)):
               coincidenze[11] += 1
    #coincidenza quadrupla lunga
        if ((self.scintilActive[0]==1) | (self.scintilActive[1]==1)) &  \
           ((self.scintilActive[4]==1) | (self.scintilActive[5]==1)) &  \
           ((self.scintilActive[2]==1) | (self.scintilActive[3]==1)) &  \
           ((self.scintilActive[6]==1) | (self.scintilActive[7]==1)) :
            coincidenze[12] += 1
    #coincidenza quadrupla corta
        if (self.scintilActive[8]==1) & (self.scintilActive[9]==1) &  \
           (self.scintilActive[10]==1) & (self.scintilActive[11]==1):
            coincidenze[13] += 1
    #coincidenza di 8 scintillatori
        if ((self.scintilActive[0]==1) | (self.scintilActive[1]==1)) &  \
           ((self.scintilActive[4]==1) | (self.scintilActive[5]==1)) &  \
           ((self.scintilActive[2]==1) | (self.scintilActive[3]==1)) &  \
           ((self.scintilActive[6]==1) | (self.scintilActive[7]==1)) &  \
           (self.scintilActive[8]==1)  & (self.scintilActive[9]==1)  &  \
           (self.scintilActive[10]==1) & (self.scintilActive[11]==1) :  \
            coincidenze[14] += 1
    # larghezza della finestra temporale
        if self.nTrigger>1:    
            tmin = self.trigs[0].startTime
            tmax = tmin
            for k in range(self.nTrigger):
                tt= self.trigs[k].startTime
                if tt< tmin : tmin = tt
                if tt> tmax : tmax = tt
    #        isto_deltat.add_data(tmax-tmin)
        
    
    def plottaEvento(self, nevt):
        AstroPlanoGui_class.faiPlotN(self, nevt)
        
    
   # fine analisi    
                    


def stampa_coincidenze():
    nome=['Scint. lungo 0-1: ', 'Scint. lungo 2-3: ', 'Scint. lungo 4-5: ',\
          'Scint. lungo 6-7: ', 'Scint. lunghi sovrapposti 0-1 & 4-5: ', \
          'Scint. lunghi sovrapposti 2-3 & 6-7: ',\
          'Scint. lunghi inclinati   2-3 & 4-5: ', \
          'Scint. lunghi inclinati   0-1 & 6-7: ', \
          'Scint. corti sovrapposti  8 & 10   : ',\
          'Scint. corti sovrapposti  9 & 11   : ',\
          'Scint. corti inclinati    8 & 11   : ',\
          'Scint. corti inclinati    9 & 10   : ',\
          'Coincidenza quadrupla lunga        : ',\
          'Coincidenza quadrupla corta        : ',\
          'Coinc. totale                      : ']

    print ('\n\nConteggio totale trigger per ogni SiPM: ')
    for i in range(A_S.astrodata.N_SiPM):
        print ('%6d '%i,end='')
    print('\n')
    for i in range(A_S.astrodata.N_SiPM):
        print ('%6d '%cum_scint[i],end='')
  
    print('\n\n Coincidenze:')
    for i in range(N_COINC):
        print (' %2d) %s %6d '%(i,nome[i],coincidenze[i]))
 


# main program, legge i dati e li riorganizza in eventi per l'analisi
# successiva
def analisi_main (home='./',filedati='test.bin', N_eventi=9999999, debug=0):
    f = open(home+filedati, "rb")
    print('File aperto: %s%s'% (home,filedati))
    isto=[]
    for nh in range(A_S.astrodata.N_SiPM):
        isto.append(hi.myhist('Distribuzione di carica, scintillatore {}'.format(nh),
            'carica','N'))
    isto_deltat=hi.myhist('Larghezza finestra temporale evento', '$\Delta t$', 'N')
    isto_q6vs23= hi.myhist('Carica 6 se Q2 Q3 sopra soglia', 'Q(6)','N')
    isto_q7vs23= hi.myhist('Carica 7 se Q2 Q3 sopra soglia', 'Q(6)','N')
    sc23 = hi.myscatter('Carica SiPM 2  vs. 3', 'SiPM 2', 'SiPM 3', 'blue')
    sc67 = hi.myscatter('Carica SiPM 6  vs. 7', 'SiPM 2', 'SiPM 3', 'cyan')
    sc23vs67 = hi.myscatter('Carica 2+3 vs 6+7', '2+3', '6+7', 'red')
 
    lastTrigger = Trigger()
    ev= AstroPlanoEvento()
# tiene traccia dei trigger letti ma non ancora utilizzati, questo succede quando
# si completa un blocco temporale     
    leftover=0 
    ntot = 0
    while ntot <  N_eventi :
       if ntot%20000 == 0: 
           print ("Trigger n. %d"% ntot) 
       if ntot%1000 ==0:
           AstroPlanoGui_class.aggiornaGui() # per poter interagire
       if leftover ==0:
           ll=lastTrigger.leggiTrigger(f)
       leftover =0 #sfruttiamo il trigger precedente e azzeriamo leftover
       if ll == None: break  # fine dati (EOF)
       if ntot<10: lastTrigger.printTrigger()          
       nt = ev.addTriggerToEvent(lastTrigger, debug)
       if nt> 0: continue  #se nt==0 abbiamo letto un evento completo
       leftover =1
# abbiamo un evento completo lo possiamo analizzare   
       ev.analizza()
        #       isto[channel].add_data(totalCharge)
       #print('evento n. %d'%ntot)
       ev.plottaEvento(ntot)

# Rileggiamo l'evento e facciamo dei grafici per scintillatori sopra soglia
       qmin =20000
       q2=0
       q3=0
       q6=0
       q7=0
       myflag=False
       for tt in range(ev.nTrigger):
           if ev.trigs[tt].nSamples<10: myflag= True
           if ev.trigs[tt].channel==2:  q2 = ev.trigs[tt].totalCharge # carica scintillatore 2
           if ev.trigs[tt].channel==3:  q3 = ev.trigs[tt].totalCharge # carica scintillatore 3
           if ev.trigs[tt].channel==6:  q6 = ev.trigs[tt].totalCharge # idem 6
           if ev.trigs[tt].channel==7:  q7 = ev.trigs[tt].totalCharge # idem 7
           if myflag==True: 
               print("evento anomalo\n")
               ev.printEvento(debug)   
       if (q2>qmin or q3>qmin) and (q6 >1): isto_q6vs23.add_data(q6)
       if (q2>qmin or q3>qmin) and (q7 >1): isto_q7vs23.add_data(q7)
       if q2*q3>0: sc23.add_data(q2,q3)
       if q6*q7>0: sc67.add_data(q6,q7)
       q23= q2+q3
       q67=q6+q7
       if q23*q67>0: sc23vs67.add_data(q23,q67)
       
       ev.clearEvent()
       ntot += 1
       
    #fine del run
    print ("\nFine del run, N. eventi analizzati: %d"% ntot)
    stampa_coincidenze()  
    # valori iniziale dei parametri forse vanno ben per il SiPM numero 0        
      
#    for j in isto:
#        if j==0:
#            x0=[2000, 27000, 2000, 200, 65000, 3000]
#        elif j==1:
#            x0=[2500, 27000, 3000, 250, 65000, 10000]
#        elif j==2:
#            x0=[3000, 35000, 5000, 500, 65000, 3000]
#        elif j==3:
#            x0=[3000, 40000, 10000, 250, 75000, 10000]
#        elif j==4:
#            x0=[2000, 40000, 15000, 300, 65000, 10000]
#        elif j==5:
#            x0=[2000, 30000, 10000, 250, 55000, 10000]
#        elif j==6:
#            x0=[2200, 30000, 10000, 250, 65000, 10000]
#        elif j==7:
#            x0=[2000, 30000, 10000, 250, 65000, 10000]
#            
#        j.plot_histo(100, x0)
#        
#    isto_deltat.plot_histo(250)
#    isto_q6vs23.plot_histo(250)
#    isto_q7vs23.plot_histo(250)
#    
#    sc23.plot_scatter(100,100)
#    sc67.plot_scatter(100, 100)
#    sc23vs67.plot_scatter(100, 100)

# end while    
    f.close()
    
if __name__ == "__main__":
    fff= "AP_log_default.bin"
    analisi_main('./', fff, 999999, debug)    
    
    