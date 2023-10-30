#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on  oct 2021

@author: Flavio Fontanelli e Stefano Grazzi
/* Channel geometry:
 *
 *  3 =============== 2
 *  1 =============== 0
 *     8           9
 *
 *  7 =============== 6
 *  5 =============== 4
 *     10         11
 *
 * controllata 9 giugno 2021
 * NOTE: check the actual cabling first!
 *
 */

"""
import inspect  # per conoscere nome della funzione chiamata
import subprocess
import time
import datetime
import os

import  astrosettings as A_S
import  AstroPlanoGui_class  as Gui
import switch as sw
import RPi.GPIO as GPIO
# no circular  from AstroPlanoGui_class import AstroGui
import  AstroSensori 
V_crit = A_S.astrodata.V_alarm # tensione critica della batteria per avviare spegnimento controllato 

def chisono():
    # funzione di debug per sapere in quale codice mi trovo.
    pass
#    print("Sono in: ", inspect.stack()[1][3])  #will give the caller of function name, if something called chisono
#    print("Sono in  ", inspect.currentframe().f_code.co_name)
    
if A_S.real_daq:
    class astro_detector:
        ip=0
        
        def PrintInfo(stringa, show=True):
            #scrive sul logfile, se show == True scrive anche su schermo
            if show or A_S.mydebug:
                print (stringa, flush=True)
                Gui.aggiornaMessaggio (stringa)
            try:
                A_S.astrodata.logf.write(stringa)
                A_S.astrodata.logf.flush()
            except AttributeError:
                print ("\n Non riesco a scrivere su log file !!\n")
                print (stringa)
                
        def addHeader():
        # scrive su file le condizioni di acquisizione
            A_S.astrodata.logf.write("\n***           Header        ***")
            adesso=time.strftime("\n      %a %d-%m-%Y @ %H:%M:%S")+"\n"
            A_S.astrodata.logf.write(adesso)
            A_S.astrodata.logf.write("\nVoltages \n")
            for item in A_S.astrodata.SiPM_HV:
                A_S.astrodata.logf.write("%s  " % item)
            A_S.astrodata.logf.write("\nStart threshold \n")
            for item in A_S.astrodata.thr_start:
                A_S.astrodata.logf.write("%s  " % item) 
            A_S.astrodata.logf.write("\nStop_threshold \n")
            for item in A_S.astrodata.thr_stop:
                A_S.astrodata.logf.write("%s  " % item) 
            A_S.astrodata.logf.write("\nLeading")            
            A_S.astrodata.logf.write("\n %s  " % A_S.astrodata.leading) 
            A_S.astrodata.logf.write("\nTrailing")
            A_S.astrodata.logf.write("\n %s  " % A_S.astrodata.trailing) 
            A_S.astrodata.logf.write("\nGain \n ")
            A_S.astrodata.logf.write(" %d " % A_S.astrodata.gain)
            A_S.astrodata.logf.write("\nMode \n ")
            A_S.astrodata.logf.write(" %d " % A_S.astrodata.mode)              
            A_S.astrodata.logf.write("\nPedestal\n ")
            A_S.astrodata.logf.write(" %X " % A_S.astrodata.pedestal) 													         
            A_S.astrodata.logf.write("\nTreference Tempco Correction_Flag\n ")
            A_S.astrodata.logf.write(" %5.1f  %7.3f  %d" % (A_S.astrodata.Treference, 
				A_S.astrodata.Tempco, A_S.astrodata.TempcoFlag))
            # T dei 4 sensori, flag di correzione, suo coefficiente
            A_S.astrodata.logf.write("\nSensori T dei SiPM: \n")
            for index in range(4):
                Tsens = AstroSensori.APLsens.Tsipm_sens(index)
                A_S.astrodata.T_sensors[index]= Tsens												 
                A_S.astrodata.logf.write(" %5.2f "% Tsens)

            # sensore ambientale: T, P, rh
   #         at = Gui.AstroGui.at
            (t,p,h)= AstroSensori.APLsens.Ambiente()
            A_S.astrodata.Temperature = t
            A_S.astrodata.Pressure = p
            A_S.astrodata.RelHumid = h
            A_S.astrodata.logf.write("\nSensore ambientale: T, P, rh\n {:.2f} {:.1f} {:.1f}".format(t, p, h))
            
            A_S.astrodata.logf.write("\nTensioni V del Sistema: \n")
            for v in range(4):
                Volt_values = AstroSensori.APLsens.V_values(v)
                A_S.astrodata.V_values[index]= Volt_values												 
                A_S.astrodata.logf.write(" %5.2f "% Volt_values)    
            if AstroSensori.APLsens.V_values(0) < V_crit: A_S.astrodata.logf.write("\n***   Attenzione!!!  Batteria quasi Esaurita !!! Inizio spegnimento controllato ***\n")    
            A_S.astrodata.logf.write("\n***      End of Header     ***\n")
            A_S.astrodata.logf.flush()

    
        def Get_ip():
            #cerco l'indirizzo ip della WB
            myCmd = 'arp -i eth0 > ./ip.txt'
            os.system(myCmd)
            fi=open ('./ip.txt','r')
            ipline = fi.readline()
            ips = 'NonValido'
            while ipline:
                ipline = fi.readline ()
                if 'ether' not in ipline: continue
                if '(incomplete)' in ipline: return -2
                ips=ipline.split()[0]
                A_S.astrodata.ip = ips
            fi.close()
            print ('\nIndirizzo IP della WaveBoard: %s '%ips)
            return 0
            
            
        def MySendComWB (commento, comando, delay):
            print (commento)
            comm = 'sshpass -p "root" ssh root@%s  \'%s >> test.out\'' % (A_S.astrodata.ip, comando)
            
            Gui.aggiornaMessaggio("\nEseguo: %s " % comm)
            print("Eseguiro %s"% comm)
                          
            os.system(comm)
            time.sleep(delay)
            
            
        def ReadParamWB(chan):
            comm ='./ReadParam -c %d '% chan
            if A_S.mydebug: print ("\nEseguo: %s " % comm)
            A_S.astrodata.MySendComWB('\nParametri dei canali', comm, 2)

        def Set_iob_delay():

            mycom = 'bash daq_set_iob_delay.sh -N "{0..11}" -F '+str(A_S.astrodata.iob_delay)
            if not A_S.mydebug:
                mycom = mycom + ' >/dev/null'
            astro_detector.MySendComWB('\nAggiusto i iob_delay ', mycom, 2)            
            
            
        def SetPedestal():
# il piedistallo e' uguale per tutti i canali
            mycom = 'bash daq_set_pedestal.sh -N "{0..11}" -P '+str(A_S.astrodata.pedestal)
            if not A_S.mydebug:
                mycom = mycom + ' >/dev/null'
            astro_detector.MySendComWB('\nAggiusto i piedistalli ', mycom, 2)
            
        def PowerOff():
            mycom = '/sbin/poweroff'       
            if A_S.mydebug: print ("\nEseguo: %s " % mycom)
            astro_detector.MySendComWB('\nSpegnimento Controllato WB', mycom, 5)
            
        def SetHV():
            print ("SetHV - Aggiorno HV \n")
            vdac = []
            for v in A_S.astrodata.SiPM_HV_corr:
                vdac.append(38000. * (1.5 - v / 50.0))
#                print(" Tensione:  %f, %f"%(v,(38000.*(1.5 -v / 50.0))))  
            mycom ='\nbash daq_set_hv.sh -N "{0..11}" -V "'
            for j in vdac:
                mycom = mycom + (' %d ' % j)
            if A_S.mydebug: mycom = mycom +' " '
            else: mycom = mycom + ' " >/dev/null'  #FFX elimino output
            astro_detector.MySendComWB('Eseguo daq_set_hv', mycom, 5)
    
    
        def StartRun (gui_self):
            astro_detector.addHeader()
            mycom= './DaqReadTcp 2>&1 >tcp_out.txt & '
            astro_detector.MySendComWB('DaqReadTcp', mycom, 2)
    # netcat per estrarre i dati
            Gui.aggiornaMessaggio ('\nStartRun: Ora nc (netcat) ------------------------', True)
            mycom = 'nc -v %s 5000 > %s%s &' % ( \
                A_S.astrodata.ip, A_S.astrodata.homedir, A_S.astrodata.outfile)
    
            Gui.aggiornaMessaggio('\neseguo comando:  %s '% mycom)
            os.system(mycom)    #netcat
            A_S.astrodata.Stato = A_S.READY
             # selezione la modalità di acquisizione, se mode=0-> normale, se mode=1 -> angolare
            if A_S.astrodata.mode == 0: 
                  GPIO.output(26, GPIO.LOW)
                  print ('Selezionata modalità normale \n')
            if A_S.astrodata.mode == 1: 
                  GPIO.output(26, GPIO.HIGH)
                  print ('Selezionata modalità angolare \n')
            #print ('Selezionata modalità %d \n', A_S.astrodata.mode)      
           
             # iob_delay
            astro_detector.Set_iob_delay()
             # piedistalli
            #astro_detector.MySendComWB (sw.mode.mes, A_S.astrodata.mode, 2)
            astro_detector.SetPedestal()
            
            # leggo temperature e Tensioni in caso di tensione batteria troppo bassa avvio spegnimento controllato
            print ("T0: %6.1f , T1: %6.1f , T2: %6.1f , T3: %6.1f\n" %
            (A_S.astrodata.T_sensors[0], A_S.astrodata.T_sensors[1], A_S.astrodata.T_sensors[2], A_S.astrodata.T_sensors[3]) )
        
            print ("Vbat: %6.1f , Vrp: %6.1f , Vp1: %6.1f , Vp2: %6.3f \n" % (AstroSensori.APLsens.V_values(0), AstroSensori.APLsens.V_values(1), AstroSensori.APLsens.V_values(2), AstroSensori.APLsens.V_values(3)) )  
            if AstroSensori.APLsens.V_values(0) < V_crit: 
                  print ("\n***   Attenzione!!!  Batteria quasi Esaurita !!! Inizio spegnimento controllato ***\n") 
                  GPIO.cleanup()
                  astro_detector.PowerOff()
                  os.system('shutdown -h now')  
            
            #alte tensioni
            astro_detector.SetHV ()
            #aspettiamo 10 s e poi eseguiamo daq_run_launch, prima era 20
            time.sleep(10)   # non puo' essere troppo piccolo (il file resta vuoto)
            
            # settiamo il guadagno uguale su tutti i canali,se gain==0 low
            # gain != 0   guadagno high
            if A_S.astrodata.gain == 0: 
                mycom = 'bash gslaFF.sh '
                ms ='Aggiusto il guadagno: G = 2  '
            else :  
                mycom = 'bash gshaFF.sh '              #apparentemente non esiste lo script ufficiale
                ms ='Aggiusto il guadagno: G = 80  '   # ./M4Comm -s "'\$gsha#'

            if not A_S.mydebug:  mycom += ' >/dev/null'
            astro_detector.MySendComWB (ms, mycom, 2)
            
            # aggiorniamo le tensioni se correzioni abilitate
            if A_S.astrodata.TempcoFlag != 0: 
                gui_self.Update_HV()
            #soglia iniziale e finale
            thrix= [None]*A_S.astrodata.N_CHAN
            thrfx= [None]*A_S.astrodata.N_CHAN
            for i in range(A_S.astrodata.N_CHAN):
    #             thrix[i]= int(self.piedistallo_default - soglia_iniz[i]/3300. * 16384.)
    #             thrfx[i]= int(self.piedistallo_default - soglia_fin[i]/3300.*16384.)
                thrix[i]= int(A_S.astrodata.pedestal - A_S.astrodata.thr_start[i]*14.611)
                thrfx[i]= int(A_S.astrodata.pedestal - A_S.astrodata.thr_stop[i]*14.611)
                
            #     stringa = "\nChan. %2d, V(SiPM): %.3f, Thr in.: %.3f (0x%X), fin.: %.3f (0x%X)" % \
            #         (i, tensioni[i], soglia_iniz[i], thrix[i], soglia_fin[i], thrfx[i])
            #     Gui.aggiornaMessaggio(stringa, False)
            # stringa = "\nN. dati prima del trigger %d (%d ns), dopo il trigger %d (%d ns)" % \
            #     (leading, leading*4, trailing, trailing*4) 
            # Gui.aggiornaMessaggio(stringa, False)
    
            mycom = 'bash daq_run_launch.sh -N "{0..11}" -S "'
            for si in thrix :
                mycom = mycom + (' 0x%X' % si)
            mycom = mycom +'" -P "'
            for sf in thrfx:
                mycom = mycom + (' 0x%X' % sf)
            mycom = mycom + ('" -L 0x%X  -T 0x%X  -I 0x0810 ' % ( \
			A_S.astrodata.leading, A_S.astrodata.trailing)) 
            #if not A_S.mydebug:
            mycom = mycom +' >/dev/null'
            astro_detector.MySendComWB('\nEseguo daq_run_launch', mycom, 5)
            A_S.astrodata.Stato = A_S.RUNNING
                  
        def EndRun():
            # chisono()
            mycom ='bash daq_run_stop.sh -N "{0..11}"'
            if not A_S.mydebug: mycom = mycom + ' > /dev/null'
            astro_detector.MySendComWB('\nEseguo daq_run_stop', mycom, 2)    #FFX  no output
            A_S.astrodata.Stato = A_S.READY

            mycom = 'bash daq_disable_hv.sh -N "{0..11}" '
            if not A_S.mydebug: mycom = mycom + ' > /dev/null'
            astro_detector.MySendComWB('\nSpengo i SiPM', mycom,1)   # FFX no output
            time.sleep(5)
            GPIO.cleanup()
            mycom = 'killall nc'
            astro_detector.MySendComWB('chiudo netcat (nc)', mycom, 1)
            mycom = 'killall DaqReadTcp'
            astro_detector.MySendComWB('chiudo DaqReadTcp', mycom, 1)
            print ('\nAcquisizione Terminata\n')
            
    
        # def CheckEnd(task):
        #     # controlliamo se il "task" e' concluso, provo ad aspettare, se rimane li' lo uccido
        #     #in particolare controlliamo se la presa dati precedente e' conclusa
        #     chisono()
        #     ntry=0
        #     ntrymax=5
        #     myCmd3='while sshpass -p "root" ssh root@%s ps axg|grep -vw grep| grep -w %s; do sleep 5; done' \
        #         %(A_S.astrodata.ip, task)
        #     while ntry < ntrymax:
        #         stringa = "\nEseguirò il comando:\n%s" % myCmd3
        #         Gui.aggiornaMessaggio(stringa, True)
        #         x=os.system(myCmd3)
        #         if x == 0: return  # sembra morto
        #         ntry= ntry+1
        #         Gui.aggiornaMessaggio ("\n %s ancora attivo: %s"% (task, x), True)
        #         time.sleep(10)
        #     Gui.aggiornaMessaggio("\n\n Il task %s non muore !! provo a continuare comunque! " \
        #                              % task, True)
    
            
        def __init__(self):
            if astro_detector.Get_ip() != 0: 
                print ("\n\n Waveboard non raggiungibile\n\n")
                exit()
            A_S.astrodata.outfile = A_S.cleanFilename(A_S.astrodata.outfile, '.bin')

            # copiamo la data del Raspberry sulla waveboard                
            adesso=datetime.datetime.now().timetuple()
            #formato vecchia scheda
            #ora_fmt = "%d-%02d-%02d %02d:%02d:%02d"% \
            #    (adesso.tm_year, adesso.tm_mon, \
            #     adesso.tm_mday, adesso.tm_hour, adesso.tm_min, adesso.tm_sec)

#        formato scheda nuova
            ora_fmt = "%d.%02d.%02d-%02d:%02d:%02d"% \
                (adesso.tm_year, adesso.tm_mon, \
                 adesso.tm_mday, adesso.tm_hour, adesso.tm_min, adesso.tm_sec)
            mycom ='date -s '+ora_fmt     
            # set date on WB
            astro_detector.MySendComWB('Aggiusto la data', mycom, 2)
            stringa ='\nAstroplano starting\nOggi: %s' % ora_fmt
            Gui.aggiornaMessaggio(stringa,True)
                 
                 
                 
            # copiamo la data del Raspberry sulla waveboard    
            cmd = "date --rfc-3339=seconds"
            line2 = subprocess.check_output(cmd, shell=True)
            print ("data RP: %s\n"%line2)                                         
            splitline2 = line2.split()
            ssplite = splitline2[1].split(b'+')
            date2 = datetime.datetime.strptime (splitline2[0].decode('ascii'), "%Y-%m-%d")
            hour2 = datetime.datetime.strptime (ssplite[0].decode('ascii'), "%H:%M:%S")
            stringa ='\nAstroplano starting\nOggi: %d  %d  %d , ore %2d:%2d:%2d' % \
                   (date2.day,date2.month,date2.year,hour2.hour,hour2.minute,hour2.second)
            Gui.aggiornaMessaggio(stringa,True)
                          
            # set date on WB
            mycom = 'date -s "%s-%s-%s %s:%s:%s"' % (date2.year, date2.month, date2.day, hour2.hour, 
                                                     hour2.minute, hour2.second)
            astro_detector.MySendComWB('Aggiusto la data della WB', mycom, 2)
            # messaggio a utente con data e ora
            stringa ='\nAstroplano starting\nOggi: %d  %d  %d , ore %2d:%2d:%2d' % \
                   (date2.day,date2.month,date2.year,hour2.hour,hour2.minute,hour2.second)
            Gui.aggiornaMessaggio(stringa,True)
                              
            
        def CloseAll ():
            Gui.aggiornaMessaggio('\nChiudo tutto\n\n', True)
            A_S.astrodata.logf.close()
            A_S.astrodata.Stato = A_S.astrodata.STARTED
            
            
# --------------------------------------------------------------------------      
#  simulazione -------------------------------------------------------------
#  -------------------------------------------------------------------------

if not A_S.real_daq:
    class astro_detector:
        
#        def PrintInfo(stringa, show=True):
#            #scrive sul logfile, se show == True scrive anche su schermo
#            if show or A_S.mydebug: print (stringa, flush=True)
#            try:
#                A_S.astrodata.logf.write(stringa)
#                A_S.astrodata.logf.flush()
#            except:
#                print ("\n No log file yet!\n")
#                print ("%s\n"% stringa)

        def addHeader():
        # scrive su file le condizioni di acquisizione
            chisono()
            A_S.astrodata.logf.write("***           Header  simulato      ***\n")
            adesso=time.strftime("      %a %d-%m-%Y @ %H:%M:%S")+"\n"
            A_S.astrodata.logf.write(adesso)
            A_S.astrodata.logf.write("\nVoltages \n")
            for item in A_S.astrodata.SiPM_HV:
                A_S.astrodata.logf.write("%s  " % item)
            A_S.astrodata.logf.write("\nStart threshold \n")
            for item in A_S.astrodata.thr_start:
                A_S.astrodata.logf.write("%s  " % item) 
            A_S.astrodata.logf.write("\nStop_threshold \n")
            for item in A_S.astrodata.thr_stop:
                A_S.astrodata.logf.write("%s  " % item) 
            A_S.astrodata.logf.write("\nLeading")            
            A_S.astrodata.logf.write("\n %s  " % A_S.astrodata.leading) 
            A_S.astrodata.logf.write("\nTrailing")
            A_S.astrodata.logf.write("\n %s  " % A_S.astrodata.trailing) 
            A_S.astrodata.logf.write("\nGain \n ")
            A_S.astrodata.logf.write(" %d " % A_S.astrodata.gain) 
            A_S.astrodata.logf.write("\nMode \n ")
            A_S.astrodata.logf.write(" %d " % A_S.astrodata.mode) 
            A_S.astrodata.logf.write("\nPedestal\n ")
            A_S.astrodata.logf.write(" %X " % A_S.astrodata.pedestal)
            
            A_S.astrodata.logf.write("\nTreference Tempco Correction_Flag")
            A_S.astrodata.logf.write(" %5.1f  %7.3f  %d" % (A_S.astrodata.Treference, 
                            A_S.astrodata.Tempco, A_S.astrodata.TempcoFlag))
            # T dei 4 sensori, flag di correzione, suo coefficiente
            A_S.astrodata.logf.write("\nSensori T dei SiPM: \n")
            for index in range(4):
                A_S.astrodata.Tsensors = AstroSensori.APLsens.Tsipm_sens(index)
                A_S.astrodata.logf.write(" %5.2f "% A_S.astrodata.Tsensors)
            # sensore ambientale: T, P, rh
            (A_S.astrodata.Temperature,A_S.astrodata.Pressure,A_S.astrodata.RelHumid)= \
                AstroSensori.APLsens.Ambiente()
            A_S.astrodata.logf.write("\nSensore ambientale: T, P, rh\n {:.2f} {:.1f} {:.1f}".format(\
                A_S.astrodata.Temperature,A_S.astrodata.Pressure,A_S.astrodata.RelHumid))   
            # V del sistema                
            for v in range(4):
                A_S.astrodata.Vsensors = AstroSensori.APLsens.V_values(v)
                A_S.astrodata.logf.write(" %5.2f "% A_S.astrodata.Vsensors)                
            if AstroSensori.APLsens.V_values(0) < V_crit: A_S.astrodata.logf.write("\n***   Attenzione!!!  Batteria quasi Esaurita !!! Inizio spegnimento controllato ***\n")    
            A_S.astrodata.logf.write("\n***      End of Header     ***\n")
            A_S.astrodata.logf.flush()


    
        def Get_ip():
            ips='168.1.1.1'
            print ('\n Falso indirizzo ip della WaveBoard: %s '%ips)
            A_S.astrodata.ip = ips
            return 0
            
            
        def MySendComWB (commento, comando, delay):
            print (commento)
            comm = 'sshpass -p "root" ssh root@%s  \'%s \' ' % \
                (A_S.astrodata.ip, comando)
            Gui.aggiornaMessaggio("\nEseguirei: %s " % comm, True)
    #        os.system(comm)
            time.sleep(delay)
            
            
        def ReadParamWB(chan):
            comm ='./ReadParam -c %d '% chan
            if A_S.mydebug: print ("\nEseguirei: %s " % comm)
            astro_detector.MySendComWB('\nParametri dei canali', comm, 2)
            
            
        def SetPedestal():
            chisono()
            tmp =" 0X%04X" % A_S.astrodata.pedestal
            mycom = 'bash daq_set_pedestal.sh -N "{0..11}" -P ' + tmp
            
            if not A_S.mydebug: mycom = mycom + ' >/dev/null'
            astro_detector.MySendComWB('\nAggiusto i piedistalli (fissati a %X)'% \
                                       A_S.astrodata.pedestal, mycom, 2)
            
            
        def SetHV():
            vdac = []
            for v in A_S.astrodata.SiPM_HV:
                vdac.append(38000. * (1.5 - v / 50.0))
            mycom ='\nbash daq_set_hv.sh -N "{0..11}" -V "'
            for j in vdac:
                mycom = mycom + (' %d ' % j)
            if A_S.mydebug: mycom = mycom +' " '
            else: mycom = mycom + ' " >/dev/null'  #FFX elimino output
            astro_detector.MySendComWB('Eseguirei daq_set_hv', mycom, 5)
    
    
        def StartRun ():
            # chisono()
            astro_detector.addHeader()
            #DaqreadTcp
            mycom= './DaqReadTcp  2>&1 >tcp_out.txt & '
            astro_detector.MySendComWB('DaqReadTcp', mycom, 2)
    # netcat per estrarre i dati
            Gui.aggiornaMessaggio('\nStartRun: Ora nc (netcat) ------------------------', 0)
            mycom = 'nc -v %s 5000 > %s%s &' % (A_S.astrodata.ip, \
                    A_S.astrodata.homedir, A_S.astrodata.outfile)
            print ('\nStartRun: netcat:  %s '% mycom)
    #        os.system(mycom)    #netcat

            A_S.astrodata.Stato = A_S.READY
            # piedistalli
            astro_detector.SetPedestal()
            
            #alte tensioni
            astro_detector.SetHV ()
            #aspettiamo 2 s  e poi eseguiamo daq_run_launch
            time.sleep(2)   # non puo' essere troppo piccolo (il file resta vuoto)
            
            # gsla su tutti i canali
            if A_S.mydebug:  mycom = 'bash gslaFF.sh '
            else:   mycom = 'bash gslaFF.sh >/dev/null'
            astro_detector.MySendComWB('Aggiusto il guadagno', mycom, 2)
            
            #soglia iniziale e finale
            thrix= [None]*A_S.astrodata.N_CHAN
            thrfx= [None]*A_S.astrodata.N_CHAN
            for i in range(A_S.astrodata.N_CHAN):
    #             thrix[i]= int(self.piedistallo_default - soglia_iniz[i]/3300. * 16384.)
    #             thrfx[i]= int(self.piedistallo_default - soglia_fin[i]/3300.*16384.)
                thrix[i]= int(A_S.astrodata.pedestal - A_S.astrodata.thr_start[i]*14.611)
                thrfx[i]= int(A_S.astrodata.pedestal - A_S.astrodata.thr_stop[i] *14.611)
                
            #     stringa = "\nChan. %2d, V(SiPM): %.3f, Thr in.: %.3f (0x%X), fin.: %.3f (0x%X)" % \
            #         (i, tensioni[i], soglia_iniz[i], thrix[i], soglia_fin[i], thrfx[i])
            #      Gui.aggiornaMessaggio(stringa, False)
            #     stringa = "\nN. dati prima del trigger %d (%d ns), dopo il trigger %d (%d ns)" % \
            #     (leading, leading*4, trailing, trailing*4) 
            #      Gui.aggiornaMessaggio(stringa, False)
    
            mycom = 'bash daq_run_launch.sh -N "{0..11}" -S "'
            for si in thrix :
                mycom = mycom + (' 0X%4X' % si)
            mycom = mycom +'" -P "'
            for sf in thrfx:
                mycom = mycom + (' 0X%4X' % sf)
            mycom = mycom + ('" -L 0X%X  -T 0X%X  -I 0X0810 ' % \
                        (A_S.astrodata.leading, A_S.astrodata.trailing)) 
            if not A_S.mydebug: mycom = mycom +' >/dev/null'
            astro_detector.MySendComWB('\nEseguirei daq_run_launch', mycom, 5)
            A_S.astrodata.Stato = A_S.RUNNING

    
                  
        def EndRun():
            # chisono()
            mycom ='bash daq_run_stop.sh -N "{0..11}"'
            if not A_S.mydebug: mycom = mycom + ' > /dev/null'
            astro_detector.MySendComWB('\nEseguirei daq_run_stop', mycom, 2)    #FFX  no output
            
            mycom = 'bash daq_disable_hv.sh -N "{0..11}" '
            if not A_S.mydebug: mycom = mycom + ' > /dev/null'
            astro_detector.MySendComWB('\nSpegnerei i SiPM', mycom,1)   # FFX no output
            
            mycom = 'killall DaqReadTcp'
            astro_detector.MySendComWB('chiuderei DaqReadTcp', mycom, 1)
            print ('\nAcquisizione Terminata\n')
            
            A_S.astrodata.Stato = A_S.READY

    
        # def CheckEnd(task):
        #     # controlliamo se il "task" e' concluso, provo ad aspettare, se rimane li' lo uccido
        #     #in particolare controlliamo se la presa dati precedente e' conclusa
        #     ntry=0
        #     ntrymax=5
        #     myCmd3='while sshpass -p "root" ssh root@%s ps axg|grep -vw grep| grep -w %s; do sleep 5; done' \
        #         % (A_S.astrodata.ip, task)
        #     while ntry < ntrymax:
        #         stringa = "\nEseguirò il comando:\n%s" % myCmd3
        #         Gui.aggiornaMessaggio(stringa, True)
        #         x=os.system(myCmd3)
        #         if x == 0: return  # sembra morto
        #         ntry= ntry+1
        #         Gui.aggiornaMessaggio ("\n %s ancora attivo: %s"% (task, x), True)
        #         time.sleep(10)
        #     Gui.aggiornaMessaggio("\n\n Il task %s non muore !! provo a continuare comunque! "\
        #                              % task, True)
    
            
        def __init__(self):
            chisono()
            if astro_detector.Get_ip() != 0: 
                print ("\n\n Waveboard non raggiungibile\n\n")
                exit()
            
            print(A_S.astrodata.homedir)
                  
            A_S.astrodata.outfile = A_S.astrodata.outfile + '.bin'
            
            
            # copiamo la data del Raspberry sulla waveboard                
            adesso=datetime.datetime.now().timetuple()
            ora_fmt = "%d-%2d-%2d %2d:%2d:%2d"% \
                (adesso.tm_year, adesso.tm_mon, 
                 adesso.tm_mday, adesso.tm_hour, adesso.tm_min, adesso.tm_sec)
            mycom ='date -s '+ora_fmt     
            # set date on WB
            
            #astro_detector.MySendComWB('Aggiusto la data', mycom, 2)
            stringa ='\nAstroplano starting\nOggi: %s' % ora_fmt
            Gui.aggiornaMessaggio(stringa,True)
                 

            # copiamo la data del Raspberry sulla waveboard, non funziona sul PC  
            # cmd = "date --rfc-3339=seconds"
            # line2 = subprocess.check_output(cmd, shell=True)
            # splitline2 = line2.split()
            # ssplite = splitline2[1].split(b'+')
            # date2 = datetime.datetime.strptime (splitline2[0].decode('ascii'), "%Y-%m-%d")
            # hour2 = datetime.datetime.strptime (ssplite[0].decode('ascii'), "%H:%M:%S")
            # stringa ='\nAstroplano starting\nOggi: %d  %d  %d , ore %2d:%2d:%2d' % \
            #        (date2.day,date2.month,date2.year,hour2.hour,hour2.minute,hour2.second)
            #  Gui.aggiornaMessaggio(stringa,True)
                          
            # # set date on WB
            # mycom = 'date -s "%s-%s-%s %s:%s:%s"' % (date2.year, date2.month, date2.day, hour2.hour, hour2.minute, hour2.second)
    #        self.MySendComWB('Aggiusto la data', mycom, 2)
    
            
        def CloseAll ():            
            Gui.aggiornaMessaggio('\nChiudo tutto\n\n', True)
            astro_detector.logf.close()
