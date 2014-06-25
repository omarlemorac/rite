# -*- coding: utf-8 -*-
#!usr/bin/python 
#!home/debian/.python-eggs/Adafruit_BBIO-0.0.19-py2.7-linux-armv7l.egg-tmp/Adafruit_BBIO
 
import Adafruit_BBIO.ADC as ADC
import Adafruit_BBIO.GPIO as GPIO 
from app import app
from flask import render_template, send_from_directory, request, redirect, url_for
import os
from config import weekdays, irrigation


last_temper = 0

_config_file = 'config.xml'

days = {  'lu':u'Lunes'
        , 'ma':u'Martes'
        , 'mi':u'Miercoles'
        , 'ju':u'Jueves'
        , 'vi':u'Viernes'
        , 'sa':u'Sabado'
        , 'do':u'Domingo'}

riego = {'as':u'Aspersión', 'go':u'Goteo'}

def read_temp():
    """
    Obtiene la temperatura desde el dispositivo
    """
    t = 1000
    try: 
        ADC.setup()
        t = int((ADC.read('P9_40')*1800)/10)
    except:
        pass 
    return t 

def base_path():
    return os.path.dirname(__file__)

@app.route('/cur_temp')
def cur_temp():
    return str(read_temp())

def read_temp_params():
    import xml.etree.ElementTree as ET
    tree = ET.parse(os.path.join(base_path(), os.pardir, _config_file))
    root = tree.getroot()
    params = {'aspersion':{},'goteo':{}}
    opAutoEl = root.find('operacionAutomatica')
    tempEl = opAutoEl.find('temperatura')
    riegoEl = tempEl.find('riego')
    aspersionEl = riegoEl.find('aspersion')
    goteoEl = riegoEl.find('goteo')
    params['aspersion'].setdefault('tmax',aspersionEl.attrib['maxima'])
    params['aspersion'].setdefault('tmin',aspersionEl.attrib['minima'])
    params['aspersion'].setdefault('inte',aspersionEl.attrib['intervalo'])
    params['goteo'].setdefault('tmax',goteoEl.attrib['maxima'])
    params['goteo'].setdefault('tmin',goteoEl.attrib['minima'])
    params['goteo'].setdefault('inte',goteoEl.attrib['intervalo'])
    return params

def read_params():
    import xml.etree.ElementTree as ET
    tree = ET.parse(os.path.join(base_path(), os.pardir, _config_file))
    root = tree.getroot()
    params = {'opManual': {'dispositivos': {}}, 'opAuto':{}}
    params['operacion'] = root.find('operacion').text
    opManualEl = root.find('operacionManual')
    dispositivosEl = opManualEl.find('dispositivos')
    params['opManual']['dispositivos'].setdefault('cisterna',
         dispositivosEl.find('cisterna').text)
    params['opManual']['dispositivos'].setdefault('aspersor',
        dispositivosEl.find('aspersor').text)
    params['opManual']['dispositivos'].setdefault('goteo',
        dispositivosEl.find('goteo').text)
    
    opAutoEl = root.find('operacionAutomatica')
    modoEl = opAutoEl.find('modo')
    params['opAuto'].setdefault('modo', modoEl.text) 
    return params


@app.route('/')
@app.route('/index')
@app.route('/config.html')
def index():
    read_params()
    #print((read_params()))
    return render_template("config.html", title='Home',
           file=read_params(), params=read_params())




@app.route('/test.html')
def testpage():
    read_params()
    return render_template("prog.html")


@app.route('/saveconfig', methods=['POST', 'GET'])
def saveconfig():
    import xml.etree.ElementTree as ET
    tree = ET.parse(os.path.join(base_path(), os.pardir, 'config.xml'))
    root = tree.getroot()
    opManualEl = root.find('operacionManual')
    dispositivosEl = opManualEl.find('dispositivos')
    opAutoEl = root.find('operacionAutomatica')
    modoEl = opAutoEl.find('modo')

    if request.args.get('operacion', None):
        root.find('operacion').text = 'auto'
    else:
        root.find('operacion').text = 'manual'

    if request.args.get('modoAuto', None):
        modoEl.text = 'horario'
    else:
        modoEl.text = 'temperatura'

    if request.args.get('aspersor', None):
        dispositivosEl.find('aspersor').text = 'on'
    else:
        dispositivosEl.find('aspersor').text = 'off'

    if request.args.get('goteo', None):
        dispositivosEl.find('goteo').text = 'on'
    else:
        dispositivosEl.find('goteo').text = 'off'
        
    tree.write(os.path.join(base_path(), os.pardir, 'config.xml'))
    return redirect(url_for('index'))

@app.route('/savetemp', methods=['POST', 'GET'])
def savetemp():
    import xml.etree.ElementTree as ET
    import json
    tree = ET.parse(os.path.join(base_path(), os.pardir, 'config.xml'))
    root = tree.getroot()
    opAutoEl = root.find('operacionAutomatica')
    opRiego = opAutoEl.find('temperatura').find('riego')
    if request.form['temp_riego_id'] == 'asp_temp':
        tempEl = opRiego.find('aspersion')
    elif request.form['temp_riego_id'] == 'got_temp':
        tempEl = opRiego.find('goteo')
    else: json.dumps({'success':0})
    
    tempEl.attrib['maxima'] = request.form['temp_riego_max']
    tempEl.attrib['minima'] = request.form['temp_riego_min']
    tempEl.attrib['intervalo'] = request.form['temp_riego_itv']
    
    tree.write(os.path.join(base_path(), os.pardir, 'config.xml'))  
    return json.dumps({'success':1,
                       'temp_riego_id':request.form['temp_riego_id'],
                       'temp_riego_max':request.form['temp_riego_max'],
                       'temp_riego_min':request.form['temp_riego_min'],
                       'temp_riego_itv':request.form['temp_riego_itv']
                       })
    

def add_schedule(s_dct, tree):
    root = tree.getroot() 
    opAutoEl = root.find('operacionAutomatica')
    schEl = opAutoEl.find('horario')
    
    from xml.etree.ElementTree import SubElement as S
    
    pEl = S(schEl,"programacion")
    pEl.set("id", s_dct["uuid"])
    S(pEl, "horaInicio").text = s_dct['hourini'].encode('utf-8', 'ignore')
    S(pEl, "horaFin").text = s_dct['hourend'].encode('utf-8', 'ignore')
    S(pEl, "dia").text = s_dct["dia"].decode('utf-8', 'ignore')[:2].lower()
    S(pEl, "riego").text = s_dct["riego"].decode('utf-8', 'ignore')[:2].lower()
    
    tree.write('config.xml')
    
    import json
    return json.dumps({'success':1
                       ,'uuid':request.form["uuid"].encode('utf-8', 'ignore')
                       ,'hourini':request.form["hourini"].encode('utf-8', 'ignore')
                       ,'hourend':request.form["hourend"].encode('utf-8', 'ignore')
                       ,'dia':request.form["dia"].encode('utf-8', 'ignore')
                       ,'action':request.form["riego"].encode('utf-8', 'ignore')
                       })


def read_schedule():
    import xml.etree.ElementTree as ET #Importa la libreria que maneja xml
    tree = ET.parse(os.path.join(base_path(), os.pardir, _config_file)) #Declara el objeto que lee el archivo "parse"
    root = tree.getroot() #saca la raiz del xml
    opAutoEl = root.find('operacionAutomatica') #dentro de la raiz encuentra el tag 'operacionAutomatica'
    schEl = opAutoEl.find('horario') #dentro del tag 'operacionAutomatica' encuentra el tag 'horario'
    
    sch_ls = []
    
    for ael in schEl.iter('programacion'): #busca los tags programacion
        ael_dct = {'id':ael.attrib['id']} #saca el id
        for apel in ael: #todos los elementos del elemento programacion
            if(apel.tag == 'dia'):
                #ael_dct.setdefault(apel.tag, days[apel.text])
                ael_dct.setdefault("dia", weekdays[int(apel.text)])
            elif (apel.tag == 'riego'):
                #ael_dct.setdefault(apel.tag, riego[apel.text])
                ael_dct.setdefault(apel.tag, irrigation[int(apel.text)])
            else:
                ael_dct.setdefault(apel.tag, apel.text)
        sch_ls.append(ael_dct)
    
    return sch_ls 


def delete_schedule(s_id):
    import json
    
    import xml.etree.ElementTree as ET
    tree = ET.parse(os.path.join(base_path(), os.pardir, _config_file))
    root = tree.getroot()
    opAutoEl = root.find('operacionAutomatica')
    schEl = opAutoEl.find('horario')
    for ael in schEl.iter('programacion'):
        if ael.attrib['id'] == s_id:
            schEl.remove(ael)
            
    tree.write('config.xml')
    
    return json.dumps({'success':1, 'uuid':s_id})


def upsert_proxy(s_dct):
    import xml.etree.ElementTree as ET
    tree = ET.parse(os.path.join(base_path(), os.pardir, 'config.xml'))
    
    if s_dct['action'] == 'save':
        return add_schedule(s_dct, tree)
    elif s_dct['action'] == 'delete':
        return delete_schedule(s_dct['uuid'])


@app.route('/saveschedule', methods=['POST'])
def saveschedule():
    '''
    with open("saveschedule.txt", "w") as text_file:
        text_file.write( """
            <html>
            <body>
            %s, %s
            </body>
            </html>
    """ % (request.form, request.form["riego"].encode('utf-8', 'ignore')))
    '''
    
    with open("saveschedule.txt", "w") as text_file:
        text_file.write( """
            <html>
            <body>
            %s
            </body>
            </html>
    """ % (request.form))
    
    return upsert_proxy(request.form)


@app.route('/prog')
def prog():
    read_params()
    return render_template("prog.html", title='Programación',
           file=read_params()
           , schedule=read_schedule()
           , weekdays=weekdays
           , irrigation=irrigation
           , temper = read_temp_params())

@app.route('/logs')
@app.route('/logs.html')
def logs():
    import config as CN
    import os
    return render_template("logs.html", title='Logs', files=os.listdir(CN.log_dir))


@app.route('/static/<path:filename>')
def base_static(filename):
    return send_from_directory(app.root_path + '/static/', filename)

