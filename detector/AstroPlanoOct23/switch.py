import time
import RPi.GPIO as GPIO
import astrosettings as sw
import astro_detector_rp as result

relay_ch = 26

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)


GPIO.setup(relay_ch, GPIO.OUT)
class mode:
	mes = 'Attendo selezione modalità'
	if sw.astrodata.mode == 0:
		GPIO.output(relay_ch, GPIO.LOW)
		print ('Selezionata modalità normale \n')
		mes = 'Selezionata modalità normale \n'
		#result.astro_detector.MySendComWB (mes, sw.astrodata.mode, 2)

	if sw.astrodata.mode == 1:
		GPIO.output(relay_ch, GPIO.HIGH)
		print ('Selezionata modalità angolare \n')
		mes = 'Selezionata modalità angolare \n'
		#result.astro_detector.MySendComWB (mes, sw.astrodata.mode, 2)
#GPIO.cleanup()
