# -*- coding: utf-8 -*-
"""
Created on Mon Jun 15 11:38:43 2020
@author: Flavio Fontanelli
"""
import tkinter as tk                     
from tkinter import ttk 
import tkinter.messagebox 
from  numpy import arange
import os
import time

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)

from tkinter.scrolledtext import ScrolledText
from time import sleep

import astro_detector_rp as detect
import analisi_class as analisi
import AP_DataRead_march22 as AP_DataRead
import astrosettings as A_S # global variables to be shared
import AstroSensori
import sys

bkgnd = 'black' # colore di background
forgnd ='white' # foreground
class  AstroGui():
    root  = None
# dimensione bottoni
    wb = 20
    hb = 2

# elementi grafici
    scroll=None
    e_leading=None
    e_trailing=None
    e_pedestal=None
    link_plot=None
    s_plotYN = None      # plot durante il monitoraggio
    go= True #disegna prossimo plot
    

    def __init__(self):
        self.root = tk.Tk() 
        AstroGui.root= self.root
        self.root.title("AstroPlano "+A_S.astrodata.VERSIONE) 
        self.root.geometry("1300x800+50+50")

        self.root.configure(background=bkgnd)  #, cursor='')  
        
        self.tabControl = ttk.Notebook(self.root) 
        self.myfont = ('calibri', 9)
        self.entry_width=10
        
        style = ttk.Style(self.root)
        style.configure('TLabel', background='green', foreground='red')
        style.configure('TFrame', background='black')
        style.configure('TButton', background='pink',foreground='red')
        style.configure('TRadioButton', background='pink',foreground='red',
                        activeforeground=bkgnd, selectcolor='green')
        
# ci sono 3 "tab" per configurazione, run e monitoraggio, sono ttk
        self.tab_config = ttk.Frame(self.tabControl) 
        self.tab_run = ttk.Frame(self.tabControl) 
        self.tab_monit = ttk.Frame(self.tabControl) 
        
        #   prima 'tab'    per controllo generale
        #-------------------------------------------------------      
        self.tabControl.add(self.tab_config, text ='Configurazione') 
        self.tabControl.add(self.tab_run,    text ='Acquisizione dati') 
        self.tabControl.add(self.tab_monit,  text ='Monitor dei dati acquisiti')
        self.tabControl.pack(expand = 1, fill ="both") # riempiamo tutta la schermata 
        
        self.drawConfigTab()
        self.drawRunTab()
        self.drawMonitTab()
        self.UpdatePTRH()
        
        
    def drawTempCorr(self): # self deve essere tab_config
    # label frame per correzione tensioni in funzione della temperatura
        self.lf_temp_corr = tk.LabelFrame(self.tab_config, text='Correzione per variazioni temperatura',
                   bg=bkgnd, fg=forgnd, padx=10, pady=10)
        self.lf_temp_corr.grid(row=2, column=1,sticky=tk.N+tk.S+tk.E+tk.W)

    #correzione della tensione si/no 
        self.s_tempcorr = tk.IntVar()
        self.s_tempcorr.set(A_S.astrodata.TempcoFlag)
        self.r_tempcorr_no= tk.Radiobutton(self.lf_temp_corr, text="Nessuna correzione ", value =0, padx=10, pady=2,
           width=self.wb, height=self.hb, bg=bkgnd, fg=forgnd, 
           indicatoron=False,activebackground='red', variable=self.s_tempcorr,
           activeforeground=bkgnd,selectcolor='green', anchor='w')
        self.r_tempcorr_no.grid(row=0, column=1,sticky=tk.W,columnspan=6)
        
        self.r_tempcorr_si= tk.Radiobutton(self.lf_temp_corr, text="Si correzione", value =1, padx=10, pady=2,
           width=self.wb, height=self.hb, bg=bkgnd, fg=forgnd, 
           indicatoron=False,activebackground='red', variable=self.s_tempcorr,
           activeforeground=bkgnd, selectcolor='green', anchor='w')
        self.r_tempcorr_si.grid(row=0, column=8,sticky=tk.W, columnspan=6)
        
    #temperatura di riferimento
        self.l_T_ref= tk.Label(self.lf_temp_corr, text='T. riferimento', relief='raised',
                       bg=bkgnd, fg=forgnd, padx=10, pady=8)
        self.l_T_ref.grid (row=1, column=1, sticky=tk.N+tk.S+tk.E+tk.W)
        self.e_T_ref= tk.Entry(self.lf_temp_corr,bg=bkgnd, fg=forgnd, 
                            font=self.myfont, width=self.entry_width)
        self.e_T_ref.grid(row=1, column=8, sticky=tk.N+tk.S+tk.E+tk.W)
        self.T_ref = A_S.astrodata.Treference   
        self.e_T_ref.insert(0,  self.T_ref)
        self.l_C= tk.Label(self.lf_temp_corr, text='C.', relief='raised',
                       bg=bkgnd, fg=forgnd, padx=10, pady=8)
        self.l_C.grid (row=1, column=9, sticky=tk.N+tk.S+tk.E+tk.W)
        
    # Coefficiente correzione temperatura
        self.l_T_coeff= tk.Label(self.lf_temp_corr, text='coeff correzione tensione vs. T', relief='raised',
                       bg=bkgnd, fg=forgnd, padx=10, pady=8)
        self.l_T_coeff.grid (row=2, column=1, sticky=tk.N+tk.S+tk.E+tk.W)
        self.e_T_coeff= tk.Entry(self.lf_temp_corr,bg=bkgnd, fg=forgnd, 
                            font=self.myfont, width=self.entry_width)
        self.e_T_coeff.grid(row=2, column=8, sticky=tk.N+tk.S+tk.E+tk.W)
        self.T_coeff = A_S.astrodata.Tempco
        self.e_T_coeff.insert(0,  self.T_coeff)
        self.l_mVsuC= tk.Label(self.lf_temp_corr, text='mV/C', relief='raised',
                       bg=bkgnd, fg=forgnd, padx=10, pady=8)
        self.l_mVsuC.grid (row=2, column=9, sticky=tk.N+tk.S+tk.E+tk.W)

                                        




    def drawConfigTab(self):
    # label frame per file di configurazione
        self.lf_config = tk.LabelFrame(self.tab_config, text='File di configurazione',relief='raised',
                   bg=bkgnd, fg=forgnd, padx=10, pady=10)
        self.lf_config.grid(row=1,column=0,sticky=tk.N+tk.S+tk.E+tk.W)

    # label frame per leading trailing, piedistallo, guadagno
        self.lf_record = tk.LabelFrame(self.tab_config, text='Parametri globali',relief='raised',
                   bg=bkgnd, fg=forgnd, padx=10, pady=10)
        self.lf_record.grid(row=2,column=0,sticky=tk.N+tk.S+tk.E+tk.W)
       
# riempo lf_config    
# percorso file configurazione
        self.l_path_file_config = tk.Label(self.lf_config, text='Path file parametri',relief='raised',
                    bg=bkgnd, fg=forgnd, padx=10, pady=10)
        self.l_path_file_config.grid(row=0, column=0, sticky=tk.N+tk.S+tk.E+tk.W)  
    # entry per il percorso nome file di config.
        self.e_path_file_config = tk.Entry(self.lf_config, bg=bkgnd, fg=forgnd, 
                      font=self.myfont)    
        self.e_path_file_config.grid(row=0, column=1, sticky=tk.N+tk.S+tk.E+tk.W)
        self.e_path_file_config.insert(0, A_S.astrodata.configfilepath)
        
        
# label file configurazione
        self.l_file_config = tk.Label(self.lf_config, text='Nome file parametri',relief='raised',
                    bg=bkgnd, fg=forgnd, padx=10, pady=10)
        self.l_file_config.grid(row=1, column=0, sticky=tk.N+tk.S+tk.E+tk.W)
   # entry per il nome file di config.
        self.e_file_config = tk.Entry(self.lf_config, bg=bkgnd, fg= forgnd, 
                      font=self.myfont)    
        self.e_file_config.grid(row=1, column=1, sticky=tk.N+tk.S+tk.E+tk.W)
        self.e_file_config.insert(0, A_S.astrodata.configfile)


        self.b_leggi = tk.Button(self.lf_config, text='Leggi file parametri',
                                 #bg=bkgnd, fg=forgnd,
                      width=self.wb, height=self.hb, command=self.LeggiConfigFile)
        self.b_leggi.grid(row=2, column=0, pady=11)

        self.b_scrivi = tk.Button(self.lf_config, text='Scrivi file parametri', bg=bkgnd, fg=forgnd,
                      width=self.wb, height=self.hb, command=self.ScriviConfigFile)
        self.b_scrivi.grid(row=3, column=0, pady=11)
        
        
    # riempo lf_record    
        self.l_leading = tk.Label(self.lf_record, text='N. leading',relief='raised',bg=bkgnd, fg=forgnd,
                      padx=10, pady=10)    # label
        self.l_leading.grid(row=6, column=0, sticky=tk.N+tk.S+tk.E+tk.W)
        
        self.e_leading = tk.Entry(self.lf_record,bg=bkgnd, fg=forgnd, font=self.myfont) #entry per leading
        self.e_leading.grid(row=6, column=1, sticky=tk.N+tk.S+tk.E+tk.W)
        self.e_leading.insert(0, A_S.astrodata.leading)
       
        self.l_trailing = tk.Label(self.lf_record, text='N. trailing',relief='raised',bg=bkgnd, fg=forgnd,
                      padx=10, pady=10)
        self.l_trailing.grid(row=7, column=0, sticky=tk.N+tk.S+tk.E+tk.W)

        self.e_trailing = tk.Entry(self.lf_record,bg=bkgnd, fg=forgnd, 
                          font=self.myfont) #entry per trailing
        self.e_trailing.grid(row=7, column=1, sticky=tk.N+tk.S+tk.E+tk.W)
        self.e_trailing.insert(0,A_S.astrodata.trailing)
        
        self.l_ped = tk.Label(self.lf_record, text='Piedistalli (hex)',relief='raised',bg=bkgnd, fg=forgnd,
                      padx=10, pady=10)
        self.l_ped.grid(row=8, column=0, sticky=tk.N+tk.S+tk.E+tk.W)
        self.e_pedestal = tk.Entry(self.lf_record,bg=bkgnd, fg=forgnd, 
                           font=self.myfont) #entry per piedistalli
        self.e_pedestal.grid(row=8, column=1, sticky=tk.N+tk.S+tk.E+tk.W)
        self.e_pedestal.insert(0, str('%X'%A_S.astrodata.pedestal))
       
    #guadagno basso/alto
        self.s_gain = tk.IntVar()
        self.s_gain.set(0)
        self.r_gain_low= tk.Radiobutton(self.lf_record, text="Gain low", value =0, padx=10, pady=2,
           width=self.wb, height=self.hb, bg=bkgnd, fg=forgnd, 
           indicatoron=False, activebackground='red', variable=self.s_gain,
           activeforeground=bkgnd, selectcolor='green', anchor='w')
        self.r_gain_low.grid(row=9, column=0,sticky=tk.W,columnspan=6)
        
        self.r_gain_high= tk.Radiobutton(self.lf_record, text="Gain high", value =1, padx=10, pady=2,
           width=self.wb, height=self.hb, bg=bkgnd, fg=forgnd, 
           indicatoron=False, activebackground='red', variable=self.s_gain,
           activeforeground=bkgnd, selectcolor='green', anchor='w')
        self.r_gain_high.grid(row=9, column=1, sticky=tk.W, columnspan=6)

        
    # label frame per alte tensioni
        self.lf_bias = tk.LabelFrame(self.tab_config, text='Tensioni di lavoro SiPM',relief='raised',
                   bg=bkgnd, fg=forgnd, padx=10, pady=10)
        self.lf_bias.grid(row=1,column=1,sticky=tk.N+tk.S+tk.E+tk.W)
        py_col = 5 # pady da usare per colonne dei 12 canali (piu' stretto)
        self.l_Vref= tk.Label(self.lf_bias, text='V ref.', relief='raised',bg=bkgnd, fg=forgnd,
                      padx=10, pady=py_col)
        self.l_Vref.grid(row=2, column=2, sticky=tk.N+tk.S+tk.E+tk.W)
        
        self.l_Vcorr= tk.Label(self.lf_bias, text='V corr.', relief='raised',bg=bkgnd, fg=forgnd,
                      padx=10, pady=py_col)
        self.l_Vcorr.grid(row=2, column=4, sticky=tk.N+tk.S+tk.E+tk.W)
       

        self.e_hv=[]
        self.e_hv_corr=[]
        for ch in range(A_S.astrodata.N_SiPM):
            self.l_ch= tk.Label(self.lf_bias, text='Ch. %2d'%(ch), relief='raised',bg=bkgnd, fg=forgnd,
                      padx=10, pady=py_col)
            self.l_ch.grid(row=3+ch, column=1, sticky=tk.N+tk.S+tk.E+tk.W)
            self.e_hv.append( tk.Entry(self.lf_bias, bg=bkgnd, fg=forgnd, 
                            font=self.myfont, width=self.entry_width) )
            self.e_hv[ch].grid(row=3+ch, column=2, sticky=tk.N+tk.S+tk.E+tk.W)
            self.e_hv[ch].insert(0, A_S.astrodata.SiPM_HV[ch])
            # aggiunta entry per tensioni corrette
            self.e_hv_corr.append( tk.Entry(self.lf_bias, bg=bkgnd, fg=forgnd, 
                            font=self.myfont, width=self.entry_width) )
            self.e_hv_corr[ch].grid(row=3+ch, column=4, sticky=tk.N+tk.S+tk.E+tk.W)
            self.e_hv_corr[ch].insert(0, " ??")
            
            
    # lframe per trigger threshold   -inizio
        self.lf_start_thr = tk.LabelFrame(self.tab_config, text='Soglie di trigger (inizio))',relief='raised',
                    bg=bkgnd, fg=forgnd, padx=10, pady=py_col)
        self.lf_start_thr.grid(row=1,column=2,sticky=tk.N+tk.S+tk.E+tk.W)
            
        self.e_thr_start=[None]*A_S.astrodata.N_SiPM
        
        # label invisibile per allineare i labelframe
        ldum = tk.Label(self.lf_start_thr, text=' ', relief='flat',bg=bkgnd, fg=bkgnd,
                      padx=10, pady=py_col)
        ldum.grid(row=1, column=2, sticky=tk.N+tk.S+tk.E+tk.W)

        for ch in range(A_S.astrodata.N_SiPM):
            self.e_thr_start[ch]= tk.Entry(self.lf_start_thr,bg=bkgnd, fg=forgnd, 
                            font=self.myfont, width=self.entry_width)
            self.e_thr_start[ch].grid(row=2+ch, column=2, sticky=tk.N+tk.S+tk.E+tk.W)
            self.e_thr_start[ch].insert(0, A_S.astrodata.thr_start[ch])
                                        
            self.l_mv= tk.Label(self.lf_start_thr, text='mV', relief='raised',bg=bkgnd, fg=forgnd,
                       padx=10, pady=py_col)
            self.l_mv.grid(row=2+ch, column=3, sticky=tk.N+tk.S+tk.E+tk.W)


    # l-frame per soglie di termine
        self.lf_stop_thr = tk.LabelFrame(self.tab_config, text='Soglie di trigger (fine))',relief='raised',
                    bg=bkgnd, fg=forgnd, padx=10, pady=py_col)
        self.lf_stop_thr.grid(row=1,column=3,sticky=tk.N+tk.S+tk.E+tk.W)
        ldum2 = tk.Label(self.lf_stop_thr, text=' ', relief='flat',bg=bkgnd, fg=bkgnd,
                      padx=10, pady=py_col)   #label invisibile
        ldum2.grid(row=2, column=4, sticky=tk.N+tk.S+tk.E+tk.W)
            
        self.e_thr_stop = [None]*A_S.astrodata.N_SiPM
        for ch in range(A_S.astrodata.N_SiPM):
            self.e_thr_stop[ch]= tk.Entry(self.lf_stop_thr,bg=bkgnd, fg=forgnd, 
                           font=self.myfont, width=self.entry_width) 
            self.e_thr_stop[ch].grid(row=3+ch, column=4, sticky=tk.N+tk.S+tk.E+tk.W)
            self.e_thr_stop[ch].insert(0, A_S.astrodata.thr_stop[ch])                                          
            self.l_mv2= tk.Label(self.lf_stop_thr, text='mV', relief='raised',bg=bkgnd, 
                            fg=forgnd, padx=8, pady=py_col)
            self.l_mv2.grid(row=3+ch, column=5, sticky=tk.N+tk.S+tk.E+tk.W)
        self.drawTempCorr()


    def drawDurataRun(self):
    #   durata del run
        self.lf_durata = tk.LabelFrame(self.lf_bottom,relief='raised',
                    bg=bkgnd, fg=forgnd, padx=10, pady=10)
        self.lf_durata.grid(row=0,column=2,sticky=tk.N+tk.S+tk.E+tk.W)
        
        self.l_durata= tk.Label(self.lf_durata, text="Durata del run",
                    relief='raised',bg=bkgnd, fg=forgnd, padx=10, pady=10)
        self.l_durata.grid(row=0, column=2, sticky=tk.N+tk.S+tk.W)
        self.e_durata=tk.Entry(self.lf_durata, bg=bkgnd, fg=forgnd,font=self.myfont,
                               width=self.entry_width)
        self.e_durata.grid(row=0,column=3,sticky=tk.N+tk.S+tk.W+tk.E)
        self.e_durata.insert(0, A_S.astrodata.durata) 
        
    # choice of time unit h/m
        AstroGui.s_time_unit = tk.IntVar()
        AstroGui.s_time_unit.set(A_S.astrodata.time_unit)
        self.r_minutes= tk.Radiobutton(self.lf_durata, text="minutes", value =0, padx=10, pady=2,
           width=self.wb, height=self.hb, bg=bkgnd, fg=forgnd, 
           indicatoron=True, activebackground='red', variable=AstroGui.s_time_unit,
           activeforeground=bkgnd, selectcolor='green', anchor='w')
        self.r_minutes.grid(row=0, column=4,sticky=tk.W)
        
        self.r_hours= tk.Radiobutton(self.lf_durata, text="hours", value =1, padx=10, pady=2,
           width=self.wb, height=self.hb, bg=bkgnd, fg=forgnd, 
           indicatoron=True, activebackground='red', variable=AstroGui.s_time_unit,
           activeforeground=bkgnd, selectcolor='green', anchor='w')
        self.r_hours.grid(row=0, column=5,sticky=tk.W)
        

    def CheckFileAlreadyExists(self):
    #controllo se il file di output esiste gia' leggendolo dalla GUI
    # se esiste avverte e permette di cambiargli nome (ritorna True)
    # altrimenti (non esiste oppure msgbox ritorna True)
        mypath = self.e_path_outfile.get()
        myname = self.e_outfile.get()
        es = os.path.isfile(mypath+myname)
        if es == False: return False   # il file di output non esiste
        MsgBox = tkinter.messagebox.askquestion ("Il file %s%s esiste gia'!"%(mypath,myname), 
             'Lo vuoi sovrascrivere?',icon = 'warning')
        if MsgBox == 'yes':
           return False   #esiste ma lo sovrascrivo
        else:
           return True     # non esiste 
  
        
    def drawRunTab(self):
#------------------------------------------------------------------------------------------
# seconda tab: controllo acquisizione       
# labelframe per pressione temperatura e umidita' relativa
        self.lf_tph = tk.LabelFrame(self.tab_run, text="Pressione, Temperatura e umidita' relativa",
                        relief='raised', bg=bkgnd, fg=forgnd, padx=10, pady=10)
        self.lf_tph.grid(row=0, column=0, sticky=tk.W+tk.N)
    # label temperatura
        self.l_t = tk.Label(self.lf_tph, text='Internal temperature',relief='raised',bg=bkgnd, 
                             fg=forgnd, padx=10, pady=10)
        self.l_t.grid(row=0, column=0, sticky=tk.N+tk.S+tk.E+tk.W)
    # entry per la temperatura.
        self.e_t = tk.Entry(self.lf_tph, bg=bkgnd, fg=forgnd, 
                        font=self.myfont)    
        self.e_t.grid(row=0, column=1, sticky=tk.N+tk.S+tk.E+tk.W)
        self.e_t.insert(0, '????')

    # label pressione
        self.l_p = tk.Label(self.lf_tph, text='Pressure',relief='raised',bg=bkgnd, 
                            fg=forgnd, padx=10, pady=10)
        self.l_p.grid(row=0, column=2, sticky=tk.N+tk.S+tk.E+tk.W)
    # entry per la pressione.
        self.e_p = tk.Entry(self.lf_tph, bg=bkgnd, fg=forgnd, 
                       font=self.myfont)    
        self.e_p.grid(row=0, column=3, sticky=tk.N+tk.S+tk.E+tk.W)
        self.e_p.insert(0, '????')

    # label umidita'
        self.l_rh = tk.Label(self.lf_tph, text='Internal relative humidity',relief='raised',bg=bkgnd, 
                             fg=forgnd, padx=10, pady=10)
        self.l_rh.grid(row=0, column=4, sticky=tk.N+tk.S+tk.E+tk.W)
    # entry per l'umidita'.
        self.e_rh = tk.Entry(self.lf_tph, bg=bkgnd, fg=forgnd, 
                        font=self.myfont)    
        self.e_rh.grid(row=0, column=5, sticky=tk.N+tk.S+tk.E+tk.W)
        self.e_rh.insert(0, '??')

#sensori di temperatura vicini a SiPM (MCP9808)
        self.lf_T = tk.LabelFrame(self.tab_run, text="Temperatura dei 4 sensori",
                        relief='raised', bg=bkgnd, fg=forgnd, padx=10, pady=10)
        self.lf_T.grid(row=1, column=0, sticky=tk.W+tk.N)
#        
        self.l_T0 = tk.Label(self.lf_T, text='T0',relief='raised',bg=bkgnd, 
                             fg=forgnd, padx=10, pady=10)
        self.l_T0.grid(row=0, column=0, sticky=tk.N+tk.S+tk.E+tk.W)
        
        self.e_T0 = tk.Entry(self.lf_T, bg=bkgnd, fg=forgnd, font=self.myfont)
        self.e_T0.grid(row=0, column=1, sticky=tk.W+tk.N+tk.S)
        self.e_T0.insert(0, '??')
#        
        self.l_T1 = tk.Label(self.lf_T, text='T1',relief='raised',bg=bkgnd, 
                             fg=forgnd, padx=10, pady=10)
        self.l_T1.grid(row=0, column=2, sticky=tk.N+tk.S+tk.E+tk.W)
        
        self.e_T1 = tk.Entry(self.lf_T, bg=bkgnd, fg=forgnd, font=self.myfont)
        self.e_T1.grid(row=0, column=3, sticky=tk.W+tk.N+tk.S)
        self.e_T1.insert(0, '??')
#        
        self.l_T2 = tk.Label(self.lf_T, text='T2',relief='raised',bg=bkgnd, 
                             fg=forgnd, padx=10, pady=10)
        self.l_T2.grid(row=0, column=4, sticky=tk.N+tk.S+tk.E+tk.W)
        
        self.e_T2 = tk.Entry(self.lf_T, bg=bkgnd, fg=forgnd, font=self.myfont)
        self.e_T2.grid(row=0, column=5, sticky=tk.W+tk.N+tk.S)
        self.e_T2.insert(0, '??')
#        
        self.l_T1 = tk.Label(self.lf_T, text='T3',relief='raised',bg=bkgnd, 
                             fg=forgnd, padx=10, pady=10)
        self.l_T1.grid(row=0, column=6, sticky=tk.N+tk.S+tk.E+tk.W)
        
        self.e_T3 = tk.Entry(self.lf_T, bg=bkgnd, fg=forgnd, font=self.myfont)
        self.e_T3.grid(row=0, column=7, sticky=tk.W+tk.N+tk.S)
        self.e_T3.insert(0, '??')    
          
# ricupero info correzione temperatura 
        A_S.astrodata.TempcoFlag = self.s_tempcorr.get()
        A_S.astrodata.Treference = float( self.e_T_ref.get() )
         
# frame per parte bassa della pagina
        self.lf_bottom=tk.Frame(self.tab_run, relief='raised', bg=bkgnd, 
                                padx=10, pady=10)
        self.lf_bottom.grid(row=2, column=0, sticky=tk.S+tk.W)
         
# percorso file dati in output
        self.l_path_outfile = tk.Label(self.lf_bottom, text='Path output file',relief='raised',
                    bg=bkgnd, fg=forgnd, padx=10, pady=10)
        self.l_path_outfile.grid(row=0, column=0, sticky=tk.N+tk.S+tk.E+tk.W) 
        
# entry per il percorso nome output file.
        self.e_path_outfile = tk.Entry(self.lf_bottom, bg=bkgnd, fg=forgnd, 
                      font=self.myfont)    
        self.e_path_outfile.grid(row=0, column=1, sticky=tk.N+tk.S+tk.E+tk.W)
        self.e_path_outfile.insert(0, A_S.astrodata.homedir)
        
        
# label file configurazione
        self.l_outfile = tk.Label(self.lf_bottom, text='Nome output file',relief='raised',
                    bg=bkgnd, fg=forgnd, padx=10, pady=10)
        self.l_outfile.grid(row=1, column=0, sticky=tk.N+tk.S+tk.E+tk.W)
   # entry per il nome file in output.
        self.e_outfile = tk.Entry(self.lf_bottom, bg=bkgnd, fg=forgnd, 
                      font=self.myfont)    
        self.e_outfile.grid(row=1, column=1, sticky=tk.N+tk.S+tk.E+tk.W)
        self.e_outfile.insert(0, A_S.astrodata.outfiledefault)
        
        
        # bottoni per iniziare ed interrompere il run
        self.lfonoff=tk.LabelFrame(self.lf_bottom, text="Control", relief='raised', bg=bkgnd, 
                               fg=forgnd, padx=10, pady=10)
        self.lfonoff.grid(row=2, column=0, sticky=tk.S+tk.W)
#
        self.B_inizia=tk.Button(self.lfonoff,text="Start Run",command=self.Connect,padx=10, pady=10, 
                bg=bkgnd, fg=forgnd, width=self.wb, height=self.hb)
        self.B_inizia.grid(row=3, column=0, pady=11)
        #
        self.B_pause=tk.Button(self.lfonoff,text="Pause Run",command=self.PauseRun,padx=10, pady=10, 
                bg=bkgnd, fg=forgnd, width=self.wb, height=self.hb)
        self.B_pause.grid(row=4, column=0, pady=11)
        #
        self.B_esci=tk.Button(self.lfonoff,text="Esci",command=self.esci,padx=10, pady=10, 
                bg=bkgnd, fg=forgnd, width=self.wb, height=self.hb)
        self.B_esci.grid(row=5, column=0, pady=11)
        
        self.drawDurataRun()
    # zona messaggi    
        self.flag_ini =1  # menu on, message on scroll
        self.lfscroll=tk.LabelFrame(self.lf_bottom, text='Messages', relief='raised', bg=bkgnd, 
                               fg=forgnd, padx=10, pady=10)
        self.lfscroll.grid(row=2, column=2, sticky=tk.N+tk.S+tk.E+tk.W, columnspan=2)                       
        self.scroll =ScrolledText(self.lfscroll, width = 62, height = 15,
                                   bg='beige',wrap=tk.WORD)
        self.scroll.grid(row=2, column=2,sticky=tk.N+tk.W+tk.S+tk.E, columnspan=2)
        A_S.astrodata.scroll =  self.scroll # per usarlo ovunque
# Making the text read only 
#         self.scroll.configure(state ='disabled') 
        


    def drawMonitTab(self):
# pad di monitor
        A_S.astrodata.monitfile = A_S.astrodata.outfile    #file di monitoring a priori = file di output

#   label frame principale entro cui va tutta la pagina
        self.lf_mon_file= tk.LabelFrame(self.tab_monit, text='Monitor',relief='raised',
                   bg=bkgnd, padx=10, pady=10, fg=forgnd)
        self.lf_mon_file.grid(row=0,column=0,sticky=tk.N+tk.W+tk.E+tk.S)
        
        
# label frame per file di input
        self.lf_input_mon_file= tk.LabelFrame(self.lf_mon_file,text ='File dati',relief='raised',
                    bg=bkgnd, padx=10, pady=10, fg=forgnd)
        self.lf_input_mon_file.grid(row=0,column=0,sticky=tk.N+tk.W) 
         
#   label e entry per  path e nome di input file
        self.l_path = tk.Label(self.lf_input_mon_file, text ='Path', relief='raised',
                        bg=bkgnd, fg=forgnd, padx=10, pady=10)
        self.l_path.grid(row=0, column=0, sticky=tk.N+tk.W+tk.E+tk.S)

        self.e_path = tk.Entry(self.lf_input_mon_file, bg=bkgnd, fg=forgnd, font=self.myfont)    
        self.e_path.grid(row=0, column=1, sticky=tk.N+tk.E+tk.W+tk.S, columnspan=99)
        self.mon_path= A_S.astrodata.monitpath
        self.e_path.insert(0, self.mon_path)

        self.l_mon_file = tk.Label(self.lf_input_mon_file,text='File input',relief='raised',
                        bg=bkgnd, fg=forgnd, padx=10, pady=10)
        self.l_mon_file.grid(row=1, column=0, sticky=tk.N+tk.W+tk.E+tk.S)

    # entry per il nome file di input da analizzare.
        self.e_mon_file = tk.Entry(self.lf_input_mon_file, bg=bkgnd, fg=forgnd, font=self.myfont)    
        self.e_mon_file.grid(row=1, column=1, sticky=tk.N+tk.E+tk.W+tk.S, columnspan=99)
        self.Input_file= A_S.astrodata.monitfile
        self.e_mon_file.insert(0, 'AP_log_default') # lo aggiusto dopo
         
        separ= ttk.Separator(self.lf_input_mon_file, orient=tk.HORIZONTAL)
        separ.grid(row=2,column=0, sticky=tk.E+tk.W, pady=10, columnspan=99)    

       # lettura file dei dati per monitor
        self.B_leggi_mon=tk.Button(self.lf_input_mon_file,text="Leggi file dati",
               command=self.preparaAnalisi, padx=10, pady=10,
                 bg=bkgnd, fg=forgnd, width=self.wb, height=self.hb)
        self.B_leggi_mon.grid(row=3, column=0, pady=11, sticky=tk.N+tk.W+tk.S)
        
       #  Arresto analisi
        self.B_stop_mon=tk.Button(self.lf_input_mon_file,text="Stop analisi",
               command=self.stopAnalisi, padx=10, pady=10,
                 bg=bkgnd, fg=forgnd, width=self.wb, height=self.hb)
        self.B_stop_mon.grid(row=3, column=1, pady=11, sticky=tk.N+tk.W+tk.S)

        self.controlloPlot()
          

    # zona plot
        self.lfplt = tk.LabelFrame(self.tab_monit, text='Plot',relief='raised',
                    bg=bkgnd, padx=10, pady=10, fg=forgnd)
        self.lfplt.grid(row=0,column=2,sticky=tk.N+tk.W+tk.S+tk.E) 

        self.lfgra = tk.LabelFrame(self.lfplt, text='Graphics',relief='sunken',
                    bg=bkgnd, fg=forgnd)
        self.lfgra.grid(row=2,column=0,sticky=tk.N+tk.W+tk.S+tk.E) 
        A_S.astrodata.link_plot = self.lfgra
        
        if A_S.real_sensors:
            self.UpdatePTRH()     
            A_S.astrodata.T_sensors[:] = AstroSensori.APLsens.T_sens[:]
            (t,p,h) = AstroSensori.APLsens.Ambiente()
            A_S.astrodata.Temperature = t
            A_S.astrodata.Pressure = p
            A_S.astrodata.RelHumid = h
            
            self.e_t.delete(0, tk.END)
            self.e_t.insert(0, '%5.1f'% A_S.astrodata.Temperature)
            self.e_p.delete(0, tk.END)
            self.e_p.insert(0, '%6.0f'% A_S.astrodata.Pressure)
            self.e_rh.delete(0, tk.END)
            self.e_rh.insert(0,'%4.0f'% A_S.astrodata.RelHumid)
 
        

    def controlloPlot(self):
        #frame per controllare i plot durante lettura file dati o monitor
        # label frame 
        self.lf_controlloPlot = tk.LabelFrame(self.lf_mon_file,text ='Controllo dei plot', 
                relief='raised', bg=bkgnd, padx=10, pady=10, fg=forgnd)
        self.lf_controlloPlot.grid(row=1,column=0,sticky=tk.N+tk.W) 
         
# label e entry per  numero minimo e  massimo del numero di trigger per gli eventi graficati
        self.l_minTrig = tk.Label(self.lf_controlloPlot, text ='N. trigger minimo', 
                relief='raised', bg=bkgnd, fg=forgnd, padx=10, pady=10)
        self.l_minTrig.grid(row=1, column=0, sticky=tk.N+tk.W+tk.E+tk.S)

# variabile della classe per memorizzare il numero minimo di trigger per fare un plot
        AstroGui.minTrigPlot =tk.StringVar()
        AstroGui.minTrigPlot.set('2')
        self.e_minTrig = tk.Entry(self.lf_controlloPlot, bg=bkgnd, fg=forgnd, font=self.myfont,
                    textvariable=AstroGui.minTrigPlot)    
        self.e_minTrig.grid(row=1, column=1, sticky=tk.N+tk.E+tk.W+tk.S, columnspan=99)
#        self.e_minTrig.delete(0, tk.END)
#        self.e_minTrig.insert(0, AstroGui.minTrigPlot.get() ) 
        
# idem per il massimo numero di trigger
        self.l_maxTrig = tk.Label(self.lf_controlloPlot, text ='N. trigger massimo', 
                relief='flat', bg=bkgnd, fg=forgnd, padx=10, pady=10)
        self.l_maxTrig.grid(row=2, column=0, sticky=tk.N+tk.W+tk.E+tk.S)
        AstroGui.maxTrigPlot = tk.StringVar()
        AstroGui.maxTrigPlot.set('12')
        self.e_maxTrig = tk.Entry(self.lf_controlloPlot, bg=bkgnd, fg=forgnd, font=self.myfont,
                    textvariable = AstroGui.maxTrigPlot)    
        self.e_maxTrig.grid(row=2, column=1, sticky=tk.N+tk.E+tk.W+tk.S, columnspan=99)

        
# scelta plot / no plot durante lettura file dati
        AstroGui.s_plotYN = tk.IntVar()
        AstroGui.s_plotYN.set(1)
        self.r_plotYN= tk.Radiobutton(self.lf_controlloPlot, text="No Plot", 
           value =0, padx=10, pady=2,
           width=self.wb, height=self.hb, bg=bkgnd, fg=forgnd, 
           indicatoron=False, activebackground='red', variable=AstroGui.s_plotYN,
           activeforeground=bkgnd, selectcolor='green', anchor='w')
        self.r_plotYN.grid(row=3, column=0,sticky=tk.W,columnspan=6)
        
        self.r_plotYN= tk.Radiobutton(self.lf_controlloPlot, text="Si Plot", 
           value =1, padx=10, pady=2,
           width=self.wb, height=self.hb, bg=bkgnd, fg=forgnd, 
           indicatoron=False, activebackground='red', variable=AstroGui.s_plotYN,
           activeforeground=bkgnd, selectcolor='green', anchor='w')
        self.r_plotYN.grid(row=3, column=1,sticky=tk.W,columnspan=6)
        
# scelta di mettere in pausa lettura dati e display plots
        AstroGui.s_pauseYN = tk.IntVar()
        AstroGui.s_pauseYN.set(1)
        self.r_pauseYN= tk.Radiobutton(self.lf_controlloPlot, text="pause", 
           value =0, padx=10, pady=2,
           width=self.wb, height=self.hb, bg=bkgnd, fg=forgnd, 
           indicatoron=False, activebackground='red', variable=AstroGui.s_pauseYN,
           activeforeground=bkgnd, selectcolor='green', anchor='w')
        self.r_pauseYN.grid(row=4, column=0,sticky=tk.W,columnspan=6)
        
        self.r_pauseYN= tk.Radiobutton(self.lf_controlloPlot, text="continue", 
           value =1, padx=10, pady=2,
           width=self.wb, height=self.hb, bg=bkgnd, fg=forgnd, 
           indicatoron=False, activebackground='red', variable=AstroGui.s_pauseYN,
           activeforeground=bkgnd, selectcolor='green', anchor='w')
        self.r_pauseYN.grid(row=4, column=1,sticky=tk.W,columnspan=6)



    def Connect(self):
    #callback of start run, legge i dati nella Gui e chiama StartRun
        # detect.chisono()
        if self.CheckFileAlreadyExists(): return

        # leggiamo i coefficienti per le correzioni di temperatura
        A_S.astrodata.TempcoFlag = self.s_tempcorr.get()   #correzione ? si/no
        A_S.astrodata.Treference = float( self.e_T_ref.get() )
        A_S.astrodata.Tempco = float(self.e_T_coeff.get())

        # non li potro' cambiare durante il run
        self.r_tempcorr_no.configure(state=tk.DISABLED)
        self.r_tempcorr_si.configure(state=tk.DISABLED)
        self.e_T_ref.configure(state=tk.DISABLED)
        self.e_T_coeff.configure(state=tk.DISABLED)
 
        A_S.astrodata.homedir = self.e_path_outfile.get().strip() # output file
        A_S.astrodata.outfile = self.e_outfile.get().strip()
        #se non c'e' estensione la pongo uguale a bin
        A_S.astrodata.outfile = A_S.cleanFilename(A_S.astrodata.outfile, 'bin')
        # copio il nome dell'output sul monitor
        A_S.astrodata.monitpath  = A_S.astrodata.homedir
        A_S.astrodata.monitfile = A_S.astrodata.outfile
        self.e_path.delete(0, tk.END)
        self.e_path.insert(0, A_S.astrodata.monitpath)
        self.e_mon_file.delete(0, tk.END)
        self.e_mon_file.insert(0, A_S.astrodata.monitfile)
        
        self.Astro_Plano = detect.astro_detector()
        aggiornaMessaggio("\nOutput file: %s%s\n" % (
               A_S.astrodata.homedir, A_S.astrodata.outfile) )
        self.UpdatePTRH()  # settiamo le tensioni
        
        for nch in range(A_S.astrodata.N_SiPM):  #threshold  start e stop campionamento
            A_S.astrodata.thr_start[nch]  = float(self.e_thr_start[nch].get())
            A_S.astrodata.thr_stop[nch]   = float(self.e_thr_stop[nch].get())
# come tensioni prendo quelle corrette per la temperatura FFX             
            A_S.astrodata.SiPM_HV_corr[nch] = float(self.e_hv[nch].get())
        A_S.astrodata.leading   = int(self.e_leading.get()) # N. campioni pre-trigger
        A_S.astrodata.trailing  = int(self.e_trailing.get()) # N. campioni post-trigger
        A_S.astrodata.gain =  int(self.s_gain.get()) # Guadagno basso o alto
        

#data e ora
        tempo= time.localtime(time.time())
        aggiornaMessaggio( "Inizia il run: %s \n"% time.asctime(tempo))
        # vediamo quanto tempo dovra' durare il run
        A_S.astrodata.durata = int(self.e_durata.get())
        A_S.astrodata.time_unit = int(AstroGui.s_time_unit.get())
        # if unit==0 run in minutes, if 1 it's hours
        tot_run_time = A_S.astrodata.durata
        if A_S.astrodata.time_unit==1: tot_run_time= tot_run_time*60
        aggiornaMessaggio('durata %d m. '%(tot_run_time))
        tot_run_time = tot_run_time *60000  #to milliseconds

        detect.astro_detector.StartRun (self)       #non e' bello, lo so
        # aggiorniamo le tensioni in base alla temperatura
        self.UpdatePTRH()  
  
        
# ho commentato, after viene utilizzata nel main,         
        # if A_S.real_sensors:
# # ad intervalli regolari aggiorno le tensioni dei SiPM
            # A_S.astrodata.MyGui.after = A_S.astrodata.MyGui.root.after(A_S.astrodata.HV_correct_interval * 1000, \
                        # Update_sens_HV, A_S.astrodata.MyGui)
        # else:   # la chiamiamo spesso (15 s)  per farne il debug
            # print ("sono in simulazione !!***************************\n\n")
            # A_S.astrodata.MyGui.after = A_S.astrodata.MyGui.root.after(15000, Update_sens_HV, \
                                            # A_S.astrodata.MyGui)  
                                            
# set timer to end run
        aggiornaMessaggio('Durata del run %d m \n'% (int(tot_run_time)/60000))
        self.root.after(tot_run_time, self.PauseRun)
        # la riga successiva disabilita il pannello di controllo (il primo)
        # pero' poi e' difficile controllare cio' che succede, quindi per ora lo lasciamo attivo
        #self.tabControl.tab(0, state="disabled")


    def PauseRun(self):
        tempo= time.localtime(time.time())
        aggiornaMessaggio("\nFine del run: %s \n"% time.asctime(tempo))
        
        # riabilito cambiamenti HV in funzione di T
        self.r_tempcorr_no.configure(state=tk.NORMAL)
        self.r_tempcorr_si.configure(state=tk.NORMAL)
        self.e_T_ref.configure(state=tk.NORMAL)
        self.e_T_coeff.configure(state=tk.NORMAL)
 

        # smetto di aggiornare le tensioni se cambia la temperatura
        if A_S.astrodata.MyGui.after != None: A_S.astrodata.MyGui.root.after_cancel( A_S.astrodata.MyGui.after)    
        detect.astro_detector.EndRun()
        #riabilito il controllo se lo avevo bloccato
        self.tabControl.tab(0, state="normal")



    def LeggiConfigFile(self):
        # read configuration file at beginning and if requested from gui
        # detect.chisono()
        A_S.astrodata.configfile =self.e_file_config.get().strip()
        A_S.astrodata.configfile = A_S.cleanFilename(A_S.astrodata.configfile, 'cfg')
#        tkinter.messagebox.showinfo( "Leggo", A_S.astrodata.configfile)
        with open(A_S.astrodata.configfilepath+ A_S.astrodata.configfile) as fp:
            parole=[]
            for line in fp:
                if line[0]=='*': continue # * indica che e' un commento
                parole=line.lower().strip().split()
                if parole[0]== 'leading':
                    A_S.astrodata.leading  = int(parole[1])
                    self.e_leading.delete(0, tk.END)
                    self.e_leading.insert(0,str(A_S.astrodata.leading))
                elif parole[0]== 'trailing':
                    A_S.astrodata.trailing = int(parole[1])
                    self.e_trailing.delete(0, tk.END)
                    self.e_trailing.insert(0, str(A_S.astrodata.trailing))
                elif parole[0] == 'pedestal':
                    A_S.astrodata.pedestal = int(parole[1], 16)
                    self.e_pedestal.delete(0,tk.END)
                    self.e_pedestal.insert(0, str('%X'%A_S.astrodata.pedestal))
                elif parole[0] == 'gain':
                    A_S.astrodata.gain = int(parole[1])
                    self.s_gain.set(A_S.astrodata.gain)
                   
                elif  parole[0] == 'tempcorr':
                    A_S.astrodata.TempcoFlag = int(parole[1])
                    self.s_tempcorr.set(A_S.astrodata.TempcoFlag)
                elif parole[0] == 'tref':    # T riferimento
                    A_S.astrodata.Treference = float(parole[1])
                    self.e_T_ref.delete(0, tk.END)
                    self.e_T_ref.insert( 0,str('%6.2f'%A_S.astrodata.Treference))
                elif parole[0] == 'tcoeff':   # coefficiente di correzione di V vs T, mV/C
                    A_S.astrodata.Tempco= float(parole[1])
                    self.e_T_coeff.delete(0, tk.END)
                    self.e_T_coeff.insert(0, str('%8.1f'% A_S.astrodata.Tempco) )

                elif parole[0] == 'channel':
                    nch = int(parole[1])
                    A_S.astrodata.SiPM_HV[nch]  = float(parole[3])
                    A_S.astrodata.thr_start[nch] = float(parole[5])
                    A_S.astrodata.thr_stop[nch]  = float(parole[7])
    #               print ("canale %d %f %f "%(nch, self.SiPM_HV[nch], self.thr_start))
                    self.e_hv[nch].delete(0, tk.END)
                    self.e_hv[nch].insert(0, str(A_S.astrodata.SiPM_HV[nch]))
                    self.e_thr_start[nch].delete(0, tk.END)
                    self.e_thr_start[nch].insert(0, str(A_S.astrodata.thr_start[nch]))
                    self.e_thr_stop[nch].delete(0, tk.END)
                    self.e_thr_stop[nch].insert(0, str(A_S.astrodata.thr_stop[nch]))
                else:
                    print("_______\n\n")
                    print("Attenzione keyword sconosciuta nel file di configurazione\n")
                    print("Keyword is %s ---------------------------\n"% parole[0])
                    sys.exit("Bad configuration file!")  
                    
                    
        aggiornaMessaggio( "Ho letto il file di configurazione\n")
                   
                   
                   
    def ScriviConfigFile(self):
#        global file_configurazione
        aggiornaMessaggio( "Scrivo file di configurazione\n")
        #leggo i valori presenti sul display
        A_S.astrodata.leading  = int(self.e_leading.get())
        A_S.astrodata.trailing =  int(self.e_trailing.get())
        A_S.astrodata.pedestal =  int(self.e_pedestal.get(),16)
        A_S.astrodata.gain =  int(self.s_gain.get())
        
        A_S.astrodata.TempcoFlag = int(self.s_tempcorr.get())
    # T riferimento
        A_S.astrodata.Treference = float(self.e_T_ref.get())
    # coefficiente di correzione di V vs T
        A_S.astrodata.Tempco =float( self.e_T_coeff.get() )
        
        
        for nch in range(A_S.astrodata.N_SiPM):
            A_S.astrodata.SiPM_HV[nch]   =  float(self.e_hv[nch].get())
            A_S.astrodata.thr_start[nch] =  float(self.e_thr_start[nch].get())
            A_S.astrodata.thr_stop[nch]  =  float(self.e_thr_stop[nch].get())
        
        A_S.astrodata.configfile = self.e_file_config.get()
        f = open(A_S.astrodata.configfilepath+A_S.astrodata.configfile, 'w')
        f.write('* AstroPlano - versione %s - File di configurazione \n'% A_S.astrodata.VERSIONE)
        f.write('leading %d \n'% A_S.astrodata.leading)
        f.write('trailing %d \n'% A_S.astrodata.trailing)
        f.write('pedestal %X \n'% A_S.astrodata.pedestal)
        f.write('gain %d \n'% A_S.astrodata.gain)
        f.write('tempcorr %d \n'%A_S.astrodata.TempcoFlag)
        f.write('tref %6.2f \n'% A_S.astrodata.Treference)
        f.write('tcoeff %8.4f \n'% A_S.astrodata.Tempco)
        for nch in range(A_S.astrodata.N_SiPM):
            f.write ('Channel %2d HV: %7.3f    Thr_start: %7.3f  Thr_stop: %7.3f \n' %
                (nch, A_S.astrodata.SiPM_HV[nch], \
                A_S.astrodata.thr_start[nch], A_S.astrodata.thr_stop[nch]))
        f.close()
        
        
        
    def reset(self):
        tkinter.messagebox.showinfo('reset',"reset")
        
        
    def esci(self):
        # chiusura dell'interfaccia grafica
        A_S.guiActive= False
        self.root.destroy()
     
     
    def UpdatePTRH(self):
    # aggiorna display della P, T, RH (sensore ambientale)
    # idem per i sensori di temperatura legati ai SiPM e finalmente
    # aggiorna anche le tensioni effettive e il display relativo
    #
    # aggiorna pressione temperatura e umidità relativa
        
        at = AstroSensori.APLsens
        (A_S.astrodata.Temperature, A_S.astrodata.Pressure, 
         A_S.astrodata.RelHumid) = at.Ambiente()        #leggo i sensori ambientali

        self.e_t.delete(0, tk.END)          # aggiorno GUI
        self.e_t.insert(0, ' %5.1f  C'% A_S.astrodata.Temperature) 
         
        self.e_p.delete(0, tk.END)
        self.e_p.insert(0, ' %8.0f  hPa'% A_S.astrodata.Pressure)
         
        self.e_rh.delete(0, tk.END)
        self.e_rh.insert(0,' %4.0f %%'% A_S.astrodata.RelHumid)
        
     # sensori di temperatura collegati con i SiPM
        A_S.astrodata.T_sensors[0] = AstroSensori.APLsens.Tsipm_sens(0)
        self.e_T0.delete(0, tk.END)
        self.e_T0.insert(0, '%5.1f'%A_S.astrodata.T_sensors[0])
        
        A_S.astrodata.T_sensors[1] = AstroSensori.APLsens.Tsipm_sens(1)
        self.e_T1.delete(0, tk.END)
        self.e_T1.insert(0, '%5.1f'%A_S.astrodata.T_sensors[1])

        A_S.astrodata.T_sensors[2] = AstroSensori.APLsens.Tsipm_sens(2)
        self.e_T2.delete(0, tk.END)
        self.e_T2.insert(0, '%5.1f'% A_S.astrodata.T_sensors[2])

        A_S.astrodata.T_sensors[3] = AstroSensori.APLsens.Tsipm_sens(3)
        self.e_T3.delete(0, tk.END)
        self.e_T3.insert(0, '%5.1f'%A_S.astrodata.T_sensors[3])
        
        # aggiorno le tensioni se sto acquisendo dati
        if A_S.astrodata.Stato == A_S.RUNNING:
            self.Update_HV()
        return        

        
        
    def Update_HV(self):
     
        if  A_S.astrodata.TempcoFlag  == 0:     return      # non devo fare nulla
        
#        Tav = (A_S.astrodata.T_sensors[0]+ A_S.astrodata.T_sensors[1]+\
#               A_S.astrodata.T_sensors[2]+ A_S.astrodata.T_sensors[3])*0.25 
        T_high =(A_S.astrodata.T_sensors[2]+ A_S.astrodata.T_sensors[3])/2.
        T_low =(A_S.astrodata.T_sensors[0]+ A_S.astrodata.T_sensors[1])/2.
        
   # la correzione e' media e lineare, non individuale sui sipm, con mV --> V
#        deltav = A_S.astrodata.Tempco *0.001*(Tav-A_S.astrodata.Treference)   
        deltav_high = A_S.astrodata.Tempco *0.001*(T_high-A_S.astrodata.Treference)   
        deltav_low = A_S.astrodata.Tempco *0.001*(T_low-A_S.astrodata.Treference)   

        adesso=time.strftime("\n      %a %d-%m-%Y @ %H:%M:%S")+"\n"
        A_S.astrodata.logf.write(adesso)

#        aggiornaMessaggio ("T media : %6.2f, T ref: %5.2f, T coef: %6.4f, Delta V: %6.3f \n" %
#          (Tav, A_S.astrodata.Treference, A_S.astrodata.Tempco, deltav) )

        aggiornaMessaggio ("T2: %6.1f , T3: %6.1f , T media alta: %6.1f , Delta V alta: %6.3f \n" %
          (A_S.astrodata.T_sensors[2], A_S.astrodata.T_sensors[3], T_high, deltav_high) )
        aggiornaMessaggio ("T0: %6.1f , T1: %6.1f , T media bassa: %6.1f , Delta V bassa: %6.3f \n" %
          (A_S.astrodata.T_sensors[0], A_S.astrodata.T_sensors[1], T_low, deltav_low) )
          
        # scrivo la pressione sul log file
        aggiornaMessaggio ("Pressione: %7.1f hPa"% A_S.astrodata.Pressure)
        for nch in range(A_S.astrodata.N_SiPM):
            # tensioni nominali
            A_S.astrodata.SiPM_HV[nch] = float(self.e_hv[nch].get())
            A_S.astrodata.SiPM_HV[nch] = round( A_S.astrodata.SiPM_HV[nch], 4)
            # tensioni corrette per temperatura
            if nch in (4,5,6,7,10,11):  # scintillatori bassi
                A_S.astrodata.SiPM_HV_corr[nch] = round( A_S.astrodata.SiPM_HV[nch] + deltav_low, 4)
            elif nch in (0,1,2,3,8,9):  # scintillatori alti
                A_S.astrodata.SiPM_HV_corr[nch] = round( A_S.astrodata.SiPM_HV[nch] + deltav_high, 4)
            else:
                aggiornaMessaggio(" errore interno !!\n\n NON CORREGGO ATTENZIONE\n\n")
            # aggiorno log file con nuove tensioni
            aggiornaMessaggio ("SiPM n. %d :  V corretta: %7.3f"% (nch, A_S.astrodata.SiPM_HV_corr[nch]))
        # aggiorno il display con le nuove tensioni
            self.e_hv_corr[nch].delete(0, tk.END)
            self.e_hv_corr[nch].insert(0, A_S.astrodata.SiPM_HV_corr[nch])
        
        if A_S.astrodata.Stato == A_S.RUNNING:
            detect.astro_detector.SetHV ()
            aggiornaMessaggio(" Ho Corretto le tensioni di bias")
# se non devo correggere le tensioni non faccio nulla.
    # else:   #nessuna correzione, ripristino valori nominali
    #     for nch in range(A_S.astrodata.N_SiPM):
    #         A_S.astrodata.SiPM_HV[nch]  = float(self.e_hv[nch].get())   # mV
    #     # aggiorno il display con le nuove tensioni
    #         self.e_hv_corr[nch].delete(0, tk.END)
    #         self.e_hv_corr[nch].insert(0, A_S.astrodata.SiPM_HV[nch])
    #     if A_S.astrodata.Stato == A_S.RUNNING:
    #         detect.astro_detector.SetHV ()
    #         aggiornaMessaggio(" Non effettuo nessuna correzione alle tensioni di bias")
    '''
    def preparaAnalisi(self):
        # callback della GUI, legge path e filename e li passa all'analisi
        A_S.astrodata.monitpath = self.e_path.get()
        A_S.astrodata.monitfile = self.e_mon_file.get()
#        self.B_nextPlot.configure(state ='normal') 
        A_S.astrodata.stop_analisi= False
        
#        analisi.analisi_main(A_S.astrodata.monitpath, A_S.astrodata.monitfile)  
        MyData = AP_DataRead.AP_DataRead()
        filedati_in = A_S.astrodata.monitpath+ A_S.astrodata.monitfile+ '.bin'
        MyData.OpenInputFile(filedati_in)
        evento =AP_DataRead.Evento()
        last_trigger = AP_DataRead.Trigger()

        while MyData.ntot_trigger <  AP_DataRead.NEVMAX  or AP_DataRead.NEVMAX <0:      
            # leggo i dati relativi al singolo trigger (un SIPM)
            rc=last_trigger.LeggiTrigger() 
            if rc == None: break  # fine dati (EOF)
            if MyData.ntot_trigger % 10000 == 0: print ("Trigger n. %d"% MyData.ntot_trigger)   
            if A_S.mydebug > 1: 
                last_trigger.PrintTrigger()  
            if last_trigger.frag_flag==0: 
                MyData.ntot_trigger +=1 # contatore totale n. trigger
            else:
                MyData.fragmented += 1  # conteggio trigger frammentati
                
            evento.CreaEvento(last_trigger)
            if evento.buf_complete : 
    #            MyData.scrivi_evento()
                evento.buf_complete= False  # lo abbiamo usato, 
                
        #fine del run
        MyData.Close_IO_Files ()
    '''
    def preparaAnalisi(self):
        # callback della GUI, legge path e filename e li passa all'analisi
        A_S.astrodata.monitpath = self.e_path.get()
        A_S.astrodata.monitfile = self.e_mon_file.get()
#        self.B_nextPlot.configure(state ='normal') 

        analisi.analisi_main(A_S.astrodata.monitpath, A_S.astrodata.monitfile)  

 
    def stopAnalisi(self):
        # callback della GUI per arrestare analisi
        A_S.astrodata.stop_analisi= True  # Arresto lettura file dei dati per monitoring
                
def aggiornaGui():
#    detect.chisono()
    AstroGui.root.update_idletasks()
    sleep(0.2)
    AstroGui.root.update()
    sleep(0.2)
#    ch=input ("batti un carattere per continuare")

    
def aggiornaMessaggio(msg, show=True):
    #scrive sul log file, se show== true mostra su display
    # detect.chisono()
    tempo= time.localtime(time.time())
    ora = time.asctime(tempo)
    if A_S.astrodata.logf ==None :
        print ("logfile non definito!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    else:
        A_S.astrodata.logf.write("\n%s\n%s "%(msg,ora))
        A_S.astrodata.logf.flush()
    if not show: return
    
    if A_S.astrodata.guiActive:
        try:
            A_S.astrodata.scroll.configure(state ='normal') # posso scrivere 
            A_S.astrodata.scroll.insert(tk.INSERT,msg)
            # AstroGui.root.update_idletask() fa casino
            #A_S.astrodata.scroll.configure(state ='disabled') # nessuno puo' modificare
        except:
            print ("\nNo grafica! time: %s\n%s\n" %(msg, ora))
        

def faiPlotN(evento, nevt):
    # detect.chisono()
    if __name__ != "__main__":    
        if AstroGui.s_plotYN.get() ==0: return  # no plot
    nt= evento.nTrigger
    #selezione degli eventi con numero di trigger nei limiti indicati
    if __name__ != "__main__":
        if int(AstroGui.minTrigPlot.get() ) >nt: return
        if int(AstroGui.maxTrigPlot.get() ) <nt: return
    # creo variabili statiche per evitare di ricreare la figura per ogni evento
    if not hasattr(AstroGui, "graphIniFlag"):
        AstroGui.graphIniFlag=1
        AstroGui.f = Figure(figsize=(7, 6), dpi=100) 
        AstroGui.f.suptitle("Evento n. %d"%nevt) # titolo n. evento
        AstroGui.canvas = FigureCanvasTkAgg(AstroGui.f, master=AstroGui.link_plot)
    else: # se esiste gia' la cancello ma la riutilizzo
        AstroGui.f.clear()
        AstroGui.f.suptitle("Evento n. %d"%nevt) # titolo n. evento
      
    if nt==1:
        nr=1
        nc=1
    elif nt==2:
        nr=2
        nc=1
    elif nt<5:
        nr=2
        nc=2
    elif nt<7:
        nr=3
        nc=2
    elif nt<10:
        nr=3
        nc=3
    else:
        nr=4
        nc=3
       
    index=1
    # tutti i plot dei SiPM interessati
    for trg in evento.trigs:
        lab_N_SiPM = "SiPM n. %d" % trg.channel
        x1= arange(0., 4.*trg.nSamples, 4.)
        graph_area = AstroGui.f.add_subplot(nr,nc, index)
        graph_area.plot(x1, trg.samples, linestyle='--',marker='.', label=lab_N_SiPM)
        legend = graph_area.legend(loc='upper right', shadow=True, fontsize=7)
        # Put a nicer background color on the legend.
        legend.get_frame().set_facecolor('C0')
        graph_area.set_xlabel("Time (ns)", fontsize=7)
        #etichetta su asse y solo per plot a estrema sinista
        if (index%nr) ==1: graph_area.set_ylabel("Samples", fontsize=7)
        index += 1
        
    canvas = FigureCanvasTkAgg(AstroGui.f, master= A_S.astrodata.link_plot)
    canvas.draw()
    canvas.get_tk_widget().grid(row=0, column=0, sticky=tk.N+tk.W)
    # navigation toolbar
    toolbarFrame = tk.Frame(master = A_S.astrodata.link_plot)
    toolbarFrame.grid(row=1,column=0)
    toolbar = NavigationToolbar2Tk(canvas, toolbarFrame)

	# placing the toolbar on the Tkinter window
    canvas.get_tk_widget().grid(row=2,column=0)

    # vediamo se nel frattempo qualcuno ha schiacciato qualche bottone  
    # tipicamente per aggiungere togliere i plot  o mettere n=in pausa  
    aggiornaGui()  
    sleep(0.3)
    # per passare al prossimo plot controllo di non essere in pausa
    while  AstroGui.s_pauseYN.get() == 0:
        sleep(0.5)
        aggiornaGui()
        sleep (0.5)
    return
    

def Update_sens_HV(self):
# funzione chiamata periodicamente per aggiornare il display delle tensioni
# e delle temperature se abilitato
    if A_S.real_sensors:
        at = AstroSensori.APLsens()
        for indt in range(4): # leggo i 4 sensori di temperatura
            A_S.astrodata.T_sensors[indt] = AstroSensori.APLsens.Tsipm_sens(indt)
            aggiornaMessaggio("\nSensore temperatura n.: %2d  T= %5.1f"% \
                  (indt,A_S.astrodata.T_sensors[indt]), True)
        self.UpdatePTRH()
        AstroGui.root.after(A_S.astrodata.HV_correct_interval*1000, Update_sens_HV, self)
    else:   # tutto uguale per il momento
#        Tsens = AstroSensori.APLsens.Tsipm_sens(0)  # solo sensore 0
#        print ("Tsens %f"%Tsens)
        self.UpdatePTRH()
        AstroGui.root.after(A_S.astrodata.HV_correct_interval*1000, Update_sens_HV, self)
        
    
# qui inizia il main -----------------------------------------------

if __name__ == "__main__":
    A_S.astrodata.MyGui= AstroGui()
    if A_S:real_sensors:  A_S.astrodata.MyGui.root.after(2000, Update_sens_HV, A_S.astrodata.MyGui)
    A_S.astrodata.MyGui.root.mainloop() 
    
    
