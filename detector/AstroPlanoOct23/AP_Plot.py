# -*- coding: utf-8 -*-
"""
Created on 15 marzo 2022
@author: F. Fontanelli

Classe per fare i plot per l'acquisizione
"""

import matplotlib.pyplot as plt

# stato di ritorno dalle funzioni
BAD = False
GOOD = True
MyDebug = 0

# altro non cambiare se non sai quello che fai
SAMPLING_TIME =4  # 4 ns periodo di campionamento (f=250 MHz)

plt.ion()   

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
     
        
     
def PlotTrigger(channel, nsamples, samples):
    # grafica un trigger in funzione del tempo   
    tempi= list(range(0, nsamples*SAMPLING_TIME, SAMPLING_TIME))
    plt.plot(tempi, samples, '.', label='original data')
    plt.grid(visible=True, which='both', axis='both')
    plt.xlabel('ns')
    # plt.legend()
    plt.title("SiPM: %d" %  channel)
    plt.show()
    move_figure()
    plt.pause(0.05)


def chiedi():
    # chiede a utente se vuole procedere
    rc= input ("Batti 0 per continuare, 1 per smettere di plottare")
    try:   # cerco di recuperare input sbagliati senza abortire
        rc=int(rc)
    except:
        rc=0
    if rc == 1: 
        plt.close()
    return rc



if __name__ == "__main__":
    # ------------------------------------------------------------------
    import AP_DataReadOnly as AP_DataRead
    
    print ("\nProgramma di test per plot trigger per AstroPlano.  V3.0")
    print ("Marzo 2022   - Flavio Fontanelli \n")
    
    NEVMAX =100
    MyData = AP_DataRead.AP_DataRead(NEVMAX)
    inputPath ='../dati/'
    inputFile ='AP20211216-2351'
    filedati_in = inputPath+inputFile + '.bin'
    MyData.OpenInputFile(filedati_in)
    evento =AP_DataRead.Evento()
    last_trigger = AP_DataRead.Trigger()

    rc=0
    while MyData.ntot_trigger <  NEVMAX  or NEVMAX <0 or rc ==0:      
        # leggo i dati relativi al singolo trigger (un SIPM)
        rc=last_trigger.LeggiTrigger(MyData) 
        if rc == None: break  # fine dati (EOF)
        if MyData.ntot_trigger % 10000 == 0: print ("Trigger n. %d"% MyData.ntot_trigger)   
        if MyDebug > 1: 
            last_trigger.PrintTrigger()  
            
        evento.CreaEvento(last_trigger)
        if evento.buf_complete : 
            evento.PrintEvento()
            for tt in evento.trigger_list:
                tt.PlotTrigger(tt.channel, tt.nsamples, tt.samples)            
                if chiedi()==1: break
            evento.buf_complete= False  # lo abbiamo usato, 
            
    #fine del run
    MyData.Close_IO_Files ()
    
    print ("\nFine del run  ----------------------  ----------   ")
