# -*- coding: utf-8 -*-
#!usr/bin/python 
#!home/debian/.python-eggs/Adafruit_BBIO-0.0.19-py2.7-linux-armv7l.egg-tmp/Adafruit_BBIO 
import Adafruit_BBIO.GPIO as GPIO
import sys, os
from daemon import Daemon
import config as CN
from datetime import datetime as DT
from config import last_signal_time
from time import sleep



class RiteDaemon(Daemon):
    def logger(self):
        import csv
        from app.views import read_temp
        
        fn = os.path.join(CN.log_dir, "tmpr_%s.csv" % DT.now().strftime('%Y%m%d'))
        if read_temp() > CN.min_temp_2_log:
            now = DT.now()
            row = ( now.strftime('%Y')
                   ,now.strftime('%m')
                   ,now.strftime('%d')
                   ,now.strftime('%H')
                   ,now.strftime('%M')
                   ,now.strftime('%S')
                   ,read_temp() )
            with open(fn, "a") as ifile:
                writer = csv.writer(ifile, delimiter=';', quotechar='"')
                writer.writerow(row)
                
            
    def asp_on(self, logfile):
        GPIO.output("P8_11",GPIO.HIGH)
        logfile.write("Encendida cisterna a las %s\n" % DT.now())
        sleep(CN.espera_cisterna)
        GPIO.output("P8_12",GPIO.HIGH)
        logfile.write("Encendido aspersor a las %s\n" % DT.now())
    
    def got_on(self, logfile):
        GPIO.output("P8_11",GPIO.HIGH)
        logfile.write("Encendida cisterna a las %s\n" % DT.now())
        sleep(CN.espera_cisterna)
        GPIO.output("P8_13",GPIO.HIGH)
        logfile.write("Encendido goteo a las %s\n" % DT.now())
    
    def asp_off(self, logfile):
        GPIO.output("P8_11",GPIO.LOW)
        logfile.write("Apagada cisterna a las %s\n" % DT.now())
        sleep(CN.espera_cisterna)
        GPIO.output("P8_12",GPIO.LOW)
        logfile.write("Apagado aspersor a las %s\n" % DT.now())
    
    def got_off(self, logfile):
        GPIO.output("P8_11",GPIO.LOW)
        logfile.write("Apagada cisterna a las %s\n" % DT.now())
        sleep(CN.espera_cisterna)
        GPIO.output("P8_13",GPIO.LOW)
        logfile.write("Apagado goteo a las %s\n" % DT.now())
        
    def manual_logic(self, device, st, logfile):
        from time import sleep
        from config import func_manual
         
        global func_manual
        if device == 'aspersor':
            if st == 'on':
                logfile.write("Estado en la parametrizacion 1 %s %s\n" % (st, func_manual['aspersor']))
                if func_manual['aspersor'] == 'off': #si esta encendido no lo vuelve a encender
                    func_manual['aspersor'] = 'on'
                    self.asp_on(logfile) 
            elif st == 'off':
                logfile.write("Estado en la parametrizacion 2 %s %s\n" % (st, func_manual['aspersor']))
                if func_manual['aspersor'] == 'on': #si esta encendido no lo vuelve a encender
                    func_manual['aspersor'] = 'off'
                    self.asp_off(logfile)
        
        elif device == 'goteo':
            if st == 'on':
                if func_manual['goteo'] == 'off': #si esta encendido no lo vuelve a encender
                    func_manual['goteo'] = 'on'
                    self.got_on(logfile) 
            elif st == 'off':
                if func_manual['goteo'] == 'on': #si esta apagado no hace nada
                    func_manual['goteo'] = 'off'
                    self.got_off(logfile)
    
    def read_schedule(self):
        import xml.etree.ElementTree as ET #Importa la libreria que maneja xml
        from app import views as V
        tree = ET.parse(os.path.join(V.base_path(), os.pardir, V._config_file)) #Declara el objeto que lee el archivo "parse"
        root = tree.getroot() #saca la raiz del xml
        opAutoEl = root.find('operacionAutomatica') #dentro de la raiz encuentra el tag 'operacionAutomatica'
        schEl = opAutoEl.find('horario') #dentro del tag 'operacionAutomatica' encuentra el tag 'horario'
        
        sch_ls = []
        
        for ael in schEl.iter('programacion'): #busca los tags programacion
            ael_dct = {'id':ael.attrib['id']} #saca el id
            for apel in ael: #todos los elementos del elemento programacion
                ael_dct.setdefault(apel.tag, apel.text)
                
            sch_ls.append(ael_dct)
        
        return sch_ls 

            
    def sche_logic(self, logfile):

        now = DT.now().strftime(CN.time_format)
        wd = DT.now().weekday()
        
        global last_signal_time
        for sh in self.read_schedule():
            """
            logfile.write("prog: %s\n" % sh)
            hi = '00:00AM'
            if sh['horaInicio'][0:2] == "12" and sh['horaInicio'][5:7] == 'AM':
                hi = "00:%s" % sh['horaInicio'][3:]
            else:
                hi = sh['horaInicio'] 
            
            hf = '00:00AM'
            if sh['horaFin'][0:2] == "12" and sh['horaFin'][5:7] == 'AM':
                hf = "00:%s" % sh['horaFin'][3:]
            else:
                hf = sh['horaFin']
            """      
            hi = sh['horaInicio']
            hf = sh['horaFin']
            
            logfile.write(u"dia '%s' '%s' %s\n" % (sh['dia'], wd, str(wd) == str(sh['dia'])))
            logfile.write(u"hora '%s' '%s' %s\n" % (hi, now, now == hi))
            logfile.write(u"signal '%s' '%s' %s\n" % (hi, last_signal_time, hi != last_signal_time))
            
            if str(wd) == str(sh['dia']) and str(now) == str(hi) and last_signal_time != hi:
                #Encender
                if int(sh['riego']) == 0:
                    self.asp_on(logfile)
                    logfile.write("Encender Aspersion")
                elif int(sh['riego']) == 1:
                    self.got_on(logfile)
                    logfile.write("Encender Goteo")
                        
                try:
                    logfile.write(u"Encender %s" % CN.irrigation[int(sh['riego'])].encode('utf-8', 'ignore'))
                except UnicodeDecodeError:
                    logfile.write(u"Encender %s" % int(sh['riego']))
                last_signal_time = hi
            
            if str(wd) == str(sh['dia']) and str(now) == str(hf) and last_signal_time != hf:
                #Apagar
                if int(sh['riego']) == 0:
                    self.asp_off(logfile)
                    logfile.write("Apagar Aspersion")
                elif int(sh['riego']) == 1:
                    self.got_off(logfile)
                    logfile.write("Apagar Goteo")
                    
                try:
                    logfile.write(u"Apagar %s" % CN.irrigation[int(sh['riego'])].encode('utf-8', 'ignore'))
                except UnicodeDecodeError:
                    logfile.write(u"Apagar %d" % int(sh['riego']))
                last_signal_time = hf
    
    def temp_logic(self, params, logfile):
        from app.views import read_temp
        try:
            cur_temp = int(read_temp())
        except:
            cur_temp = 0
        #logfile.write('\nInicia Temperatura %d %d %d\n ' % (cur_temp, int(params['aspersion']['tmin']), int(params['aspersion']['tmax'])))
        
        if cur_temp > int(params['aspersion']['tmin']) and cur_temp < int(params['aspersion']['tmax']):
            logfile.write("\n%s Iniciar aspersion. Temperatura actual %d" % (DT.now(), cur_temp))
            self.asp_on(logfile)
            #sleep(int(params['aspersion']['inte']) * 60)
            sleep(int(params['aspersion']['inte']) * 60)
            self.asp_off(logfile)
            logfile.write("\n%s Finalizada aspersion. Temperatura actual %d" % (DT.now(), cur_temp))
        
        if cur_temp > int(params['goteo']['tmin']) and cur_temp < int(params['goteo']['tmax']):
            logfile.write("\n%s Iniciar goteo. Temperatura actual %d" % (DT.now(), cur_temp))
            #sleep(int(params['goteo']['inte']) * 60)
            self.got_on(logfile)
            sleep(int(params['goteo']['inte']) * 60)
            self.got_off(logfile)
            logfile.write("\n%s Finalizada goteo. Temperatura actual %d" % (DT.now(), cur_temp))
            
            
    def run(self):        
        from app.views import read_params, read_temp_params, read_temp
        #Inicializa los IOs
        with open(CN.logs_dir, "a") as mylog:
            GPIO.setup("P8_11", GPIO.OUT)
            GPIO.setup("P8_12", GPIO.OUT)
            GPIO.setup("P8_13", GPIO.OUT)
            mylog.write("Inicializadas librerias GPIO")
            self.got_on(mylog)
            sleep(3)
            self.got_off(mylog)    
        while(1):
            sleep(1)
            params = read_params()
            self.logger()
            with open(CN.logs_dir, "a") as mylog:
                mylog.write("\n%s la temperatura es: %s\n" % (DT.now(), read_temp()))
                mylog.write("Operacion %s:\n" % params['operacion'])
                if params['operacion'] == 'auto':
                    mylog.write("Operacion automatica en modo: %s\n" % params['opAuto']['modo'])
                    if params['opAuto']['modo'] == 'horario':
                        mylog.write('Horarios:\n')
                        self.sche_logic(mylog)
                    elif params['opAuto']['modo'] == 'temperatura':
                        mylog.write('Temperatura %s \n' % read_temp_params() )
                        self.temp_logic(read_temp_params(), mylog) 
                elif params['operacion'] == 'manual':
                    aspersor_st = params['opManual']['dispositivos']['aspersor']
                    self.manual_logic('aspersor',aspersor_st, mylog)
                    goteo_st = params['opManual']['dispositivos']['goteo']
                    self.manual_logic('goteo', goteo_st, mylog)
                        
                    
                    
 
if __name__ == "__main__":
    daemon = RiteDaemon(
                        os.path.join(os.getcwd(), 'rite-daemon.pid')
                      , stderr = os.path.join(os.getcwd(), 'rite.err.log')
                      , stdout = os.path.join(os.getcwd(), 'rite.out.log')
                      , stdin = os.path.join(os.getcwd(), 'rite.in.log')
                      )
    
    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            daemon.start()
        elif 'stop' == sys.argv[1]:
            daemon.stop()
        elif 'restart' == sys.argv[1]:
            daemon.restart()
        else:
            print "Unknown command"
            sys.exit(2)
            sys.exit(0)
    else:
            print "usage: %s start|stop|restart" % sys.argv[0]
            sys.exit(2)