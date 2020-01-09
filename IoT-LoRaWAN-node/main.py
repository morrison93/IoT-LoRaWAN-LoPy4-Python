##################################################### Identification ########################################################
####################################### Elaborado por: Rodrigo da Silva Freitas Rocha #######################################
#################################################### Aluno nº 73952 #########################################################
#################################### Curso: Engenharia de Telecomunicações e Informática ####################################
#################### Colaboração com: Instituto Superior Técnico e Madeira Iteractive Technologies Institute ################
#############################################################################################################################

##################################################### Libraries Import ######################################################
import machine
import socket
import ubinascii
import struct
import os
import time
import config
import pycom
import gc
from machine import Pin, SD, WDT, UART, RTC
from network import LoRa
from micropyGPS import MicropyGPS
from util import *
from pysense import Pysense
from SI7006A20 import SI7006A20
from LTR329ALS01 import LTR329ALS01
from MPL3115A2 import MPL3115A2,PRESSURE,ALTITUDE
from struct import *

################################################ Variables Definition ##################################################

global sd
global SD_ON_BOOT
global SD_READ
global SEMAFORO
global STRING_READ
global GPS_READ

# p_test = Pin('P11', mode=Pin.OUT, pull=Pin.PULL_DOWN)  # test PIN
# p_test.value(0)

# rtc = RTC()
# rtc.init((2019, 7, 10, 0, 0, 0, 0, 0))


LOG_FILENAME = 'node.log'
SEMAFORO = True
SD_READ = False
SD_ON_BOOT = False
sd = None
GPS_READ=False
WIFI_SSID = 'M-ITI'
WIFI_PASS = 'M1T1-W1F1'
py = Pysense()
mpp = MPL3115A2(py,mode=PRESSURE)   # Returns PRESSURE in Pascals
si = SI7006A20(py)                  # temp, humidity
lt = LTR329ALS01(py)                # light
#li = LIS2HH12(py)                   # accelerometer Para apagar
gps_parser = MicropyGPS()           # GPS lib
GPS_TRIES = 400                      # GPS tries to connect
wdt = WDT(timeout=90000)
GPS_pin = Pin('P2', mode=Pin.OUT, pull=Pin.PULL_DOWN)
GPS_pin.value(0)
gc.enable()                         # enable garbage collection

################################################ Setup Functions #####################################################

# Input: void
# Output: ------------
# Joins WLAN of choice
# def join_WLAN():
#     wlan = WLAN(mode=WLAN.STA)
#     nets = wlan.scan()
#
#     for net in nets:
#         if net.ssid == WIFI_SSID:
#             print('Network found!')
#             wlan.connect(net.ssid, auth=(net.sec, WIFI_PASS), timeout=5000)
#             # while not wlan.isconnected():
#             #     machine.idle()                              # save power while waiting
#             print('WLAN connection succeeded!')
#             #pycom.rgbled(0x007f00)                            # green = wlan.connect accepted
#             break

# Input: void
# Output: ------------
# Sinchronizes RTC
# def sync_RTC():
#     rtc=machine.RTC()
#     time.sleep(1)
#     pycom.rgbled(0x7f7f00)                                    # yellow = rtc.ntp_sync pending
#     print("Synchronizing RTC ...")
#     time.sleep(1)
#     rtc.ntp_sync('pool.ntp.org',3600)
#
#     while not rtc.synced():                                   # beware: maybe add counter if unsynced ntp doesn't lead to infinite loop
#         rtc.ntp_sync('pool.ntp.org',3600)
#         pycom.rgbled(0x7f0000)                                #red = <action> not forwarded
#         print("RTC still not synchronized...")
#         time.sleep(2.5)
#     return

# Input: void
# Output: ---------
# Mounts SD card
def mount_SD():
    global sd
    global SD_ON_BOOT
    print('Mount SD')
    sd = None
    try:
        sd = SD()
        if SD_ON_BOOT == False:
            os.mount(sd, '/sd')
            SD_ON_BOOT = True
    except Exception as e:
        print('No SDcard to mount: ' + str(e))

# Input: void
# Output: -------------
# Unmounts SD card
def unmount_SD():
    global sd
    sd = None
    try:
        os.unmount('/sd')
    except Exception as e:
        print('No sd card to unmount: ' + str(e))

################################################# Sensor Functions ###################################################

# Input: void
# Output: List that contains read values in fixed positions
# Sensor reading from in a determined instant t
def readSensor():
    global GPS_READ
    list=[]

    try:
        # acc_x = li.acceleration()[0]
        # acc_y = li.acceleration()[1]
        # acc_z = li.acceleration()[2]
        # pitch = li.pitch()                                        # [-90, 90]; Unidades: graus
        # roll = li.roll()                                          # [-180, 180]; Unidades: graus

        id=pycom.nvs_get('count')
        humid = int(round(si.humidity()*10))                      # arredondamento a uma casa decimal; Unidades: %
        temp = int(round((si.temperature()+273.15)*10))           # arredondamento a uma casa decimal; Unidades: K
        light = lt.light()[0]
        light1 = lt.light()[1]
        press=int(mpp.pressure()/100)                             # descodificação a /100; Unidades: kPa com 1 casa decimal
        batt = int(py.read_battery_voltage()*10)                  # Unidades: dV


        if GPS_READ == True:

            gps_counter = 0
            gps_uart = UART(1, baudrate=9600, pins=('G7', 'G6'))


            # a=rtc.now()
            # print("segundos passados:", a[5])
            # time.sleep(30 - a[5])
            # a=rtc.now()
            #print("segundos passados:", a[5])

            for gps_counter in range(GPS_TRIES):
                    print('updating gps' + '.'*(gps_counter + 1))
                    time.sleep(0.1)                                               # Reduzir isto / eliminar
                    update_gps(gps_uart)
                    if gps_parser.latitude[0] != 0:
                        break

            latitude=coord_deg_to_dec(gps_parser.latitude)
            longitude=coord_deg_to_dec(gps_parser.longitude)
            altitude=gps_parser.altitude

            # if '.' in str(gps_parser.timestamp[2]):
            #     gps_ts = list(gps_parser.timestamp)
            #     gps_ts_mills = int(str(gps_ts[2]).split('.')[1])
            #     gps_ts[2] = int(str(gps_ts[2]).split('.')[0])
            #     gps_ts = tuple(gps_ts)
            #     gps_date = get_date_str(gps_parser.date + gps_ts + (gps_ts_mills,))
            # else:
            #     gps_date = get_date_str(gps_parser.date + gps_parser.timestamp + (0,))

            # FALTA TIMESTAMP

            hour=gps_parser.timestamp[0]
            minute=gps_parser.timestamp[1]
            second=int(gps_parser.timestamp[2])


            list.append(id)             # i = 4 bytes
            list.append(humid)          # H = 2 bytes
            list.append(temp)           # H = 2 bytes
            list.append(light)          # f = 4 bytes
            list.append(light1)         # f = 4 bytes
            list.append(press)          # H = 2 bytes
            list.append(batt)           # B = 1 byte
            list.append(latitude)       # f = 4 bytes
            list.append(longitude)      # f = 4 bytes
            list.append(altitude)       # f = 4 bytes
            list.append(hour)           # B = 1 byte
            list.append(minute)         # B = 1 byte
            list.append(second)         # B = 1 byte
            return list                 # Total = 34 bytes

        else:
            list.append(id)             # i = 4 bytes
            list.append(humid)          # H = 2 bytes
            list.append(temp)           # H = 2 bytes
            list.append(light)          # f = 4 bytes
            list.append(light1)         # f = 4 bytes
            list.append(press)          # H = 2 bytes
            list.append(batt)           # B = 1 byte
            return list                 # Total = 19 bytes
    except Exception as e:
        print(str(e))

# Input: values from sensors, formats
# Output: returns bytes
# Encodes bytes with struct pack
def encoder(v, f):
    bytes=bytearray()
    values=v
    formats=f

    for i in range(len(values)):
	   bytes.extend(struct.pack(formats[i], values[i]))

    return bytes

# Input: bytearray
# Output: List of read values
# Decodes the bytearray into the original read values
def decoder(bytearray):
    global GPS_READ
    formatSize = {
	'b': 1,
	'B': 1,
	'H': 2,
	'h': 2,
	'f': 4,
	'I': 4,
	'i': 4,
    }

    if GPS_READ == True:
        headers = ['id','lat','long','alt','hour','min','sec','humid','temp','light','light1','press','batt']
        NR_VALS = 13
    else:
        headers = ['id','humid','temp','light','light1','press','batt']
        NR_VALS = 7

    fin_i=0
    curr_i = 0
    decoded_val=[]

    for i in range(NR_VALS):
 	  fin_i = curr_i + formatSize[formats[i]]
 	  subPkt = bytes2send[curr_i:fin_i]
 	  decoded_val.append(struct.unpack(formats[i], subPkt)[0])
 	  curr_i = fin_i

    return  decoded_val

# Input: gps_uart
# Output: Updated gps string
# Function that updates gps
def update_gps(gps_uart):
    try:
        if gps_uart.any() > 0:
            gps_line = gps_uart.readline()
            #printd(gps_line)
            # final_str = ''
            # for decimal in gps_line:
            #     final_str+= chr(decimal)
            # final_str = final_str.replace('\r','').replace('\n','')
            final_str = ''.join([chr(decimal) for decimal in gps_line]).replace('\r','').replace('\n','')
            #printd(final_str)
            for char in final_str:
                gps_parser.update(char)
    except:
        print('Error reading GPS')

# Input: filename, string
# Output: -------
# Writes string into designated string
def write_toSD(filename, string):
    try:
        if sd != None:
            str_toWrite=ubinascii.hexlify(string)
            with open('/sd/' + filename, 'a') as f:
                f.write(str_toWrite +'\n')
                f.close()
            return
    except Exception as e:
        print(str(e))
        return

# Input: filename
# Output: string read from filename
# Read first line from file in SD card
def read_fromSD(filename):
    try:
        global SD_READ
        if sd != None:
            print("Read SD")
            with open('/sd/' + filename, 'r') as f:
                str_read=f.readline()
                if str_read !='':
                    str_read=str_read.replace("\n", "")
                    str_read=str_read.encode()
                    str_read=ubinascii.unhexlify(str_read)
                    str_read=bytearray(str_read)
                    SD_READ=True
                    return str_read
                else:
                    SD_READ=False
                    str_read='No_msg_TX'
                    return str_read
    except Exception as e:
        print(str(e))
        return

# Input: filename
# Output: --------
# Deletes first line from SD card
def deline_fromSD(filename):
    try:
        if sd != None:
            f1=open('/sd/aux.log', 'w')
            with open('/sd/' + filename, 'r') as f:
                a=f.readline()
                while a != "":
                    a=f.readline()
                    f1.write(a)
                f1.close()
                f.close()
            os.remove("/sd/node.log")
            os.rename("/sd/aux.log", '/sd/' + LOG_FILENAME)
            return
    except Exception as e:
        print(str(e))
        return

# Input: LoRa instance
# Output: -------------------- (End of Cycle)
# LoRa callback responsible for managing events of transmission
def lora_cb(lora):
    global SD_READ
    global SEMAFORO
    global STRING_READ
    global GPS_READ
    events = lora.events()
    print(" --------------------------------- !!!! CALLBACK !!!! ----------------------------------------- ")

    if events & LoRa.TX_PACKET_EVENT:                                          # if TX successfull

        print("SD_READ: ",SD_READ)

        if SD_READ==False:                                                      # Nao fez leituras e consegue
            str_read=read_fromSD(LOG_FILENAME)
            STRING_READ=str_read
            if STRING_READ=='No_msg_TX':
                lora.nvram_save()

                print("Lora joined -> 1st send -> ack -> checkSD -> No msg in SD")
                time.sleep(0.1)

                if GPS_READ==True:
                    #py.setup_sleep(10)
                    py.setup_sleep(9479)
                    py.go_to_sleep(False)           # Estado 6
                else:
                    #py.setup_sleep(10)
                    py.setup_sleep(2520)
                    py.go_to_sleep(False)           # Estado 5

            else:
                print("Lora joined -> 1st send -> ack -> checkSD -> msg in SD -> 2nd send")
                deline_fromSD(LOG_FILENAME)
                SD_READ=True
                s.send(STRING_READ) # inconsistencia resolvida com variável global
                return

        else:                                                                   # Já fez leituras
            lora.nvram_save()
            print("Lora joined -> 1st send -> ack -> checkSD -> msg in SD -> 2nd send ->ack")
            time.sleep(0.1)

            if GPS_READ==True:
                #py.setup_sleep(10)
                py.setup_sleep(9792)
                py.go_to_sleep(False)               # Estado 10
            else:
                #py.setup_sleep(10)
                py.setup_sleep(2023)
                py.go_to_sleep(False)               # Estado 9


    elif events & LoRa.TX_FAILED_EVENT:
        if SD_READ == False:
            print("Lora joined -> 1st send -> Failed")
            write_toSD(LOG_FILENAME, bytes2send)
            lora.nvram_erase()
            time.sleep(0.1)

            if GPS_READ==True:
                #py.setup_sleep(10)
                py.setup_sleep(10310)
                py.go_to_sleep(False)       # Estado 4
            else:
                #py.setup_sleep(10)
                py.setup_sleep(3240)
                py.go_to_sleep(False)       # Estado 3


        else:
            print("Lora joined -> 1st send -> ack -> checkSD -> msg in SD -> 2nd send -> Failed")
            write_toSD(LOG_FILENAME, STRING_READ)

            lora.nvram_erase()
            time.sleep(0.1)

            if GPS_READ==True:
                #py.setup_sleep(10)
                py.setup_sleep(12454)
                py.go_to_sleep(False)           # Estado 8
            else:
                #py.setup_sleep(10)
                py.setup_sleep(3371)
                py.go_to_sleep(False)           # Estado 7



################################################ Testing Functions #####################################################

# Input: ------------
# Output: Populated SD card
# Populates SD card with simple payloads for test
def populate_SD():
    filename="node.log"
    try:
        if sd != None:
            str_toWrite='000000000000000000000000000000000000000000000000000000000000000000000000000000'
            str_toWrite1='010000000000000000000000000000000000000000000000000000000000000000000000000000'
            str_toWrite2='020000000000000000000000000000000000000000000000000000000000000000000000000000'
            str_toWrite3='030000000000000000000000000000000000000000000000000000000000000000000000000000'

            with open('/sd/' + filename, 'a') as f:
                f.write(str_toWrite +'\n')
                f.write(str_toWrite1 +'\n')
                f.write(str_toWrite2 +'\n')
                f.write(str_toWrite3 +'\n')
                f.close()
            return
    except Exception as e:
        print(str(e))
        return

# Input: ------------
# Output: ------------
# Deletes all lines from file in SD card
def del_allSD():
        try:
            if sd != None:
                f=open('/sd/aux.log', 'w')
                os.remove("/sd/node.log")
                os.rename("/sd/aux.log", '/sd/' + LOG_FILENAME)
                return
        except Exception as e:
            print(str(e))
            return

# Input: ------------
# Output: Variables in memory reset
# Reset ID and lora state
def var_Reset():
    lora.nvram_erase()
    del_allSD()
    pycom.nvs_erase('count')
    return

def test_Scenario3():
    lora.nvram_erase()
    del_allSD()
    pycom.nvs_erase('count')
    populate_SD()
    pycom.nvs_set('count', 4)

############################################## LoRaWAN Setup ########################################################

lora = LoRa(mode=LoRa.LORAWAN, region=LoRa.EU868)

lora.nvram_restore()
time.sleep(0.1)

if not lora.has_joined():

    print("Firstly join")

    dev_eui = ubinascii.unhexlify('70B3D54995F6E9F1') # these settings can be found from TTN  0AEA4FFFE784BC0
    app_eui = ubinascii.unhexlify('70B3D57ED0019C87') # these settings can be found from TTN
    app_key = ubinascii.unhexlify('169C2EF739EAAF4051CD16B8CDA3D56A') # these settings can be found from TTN

    # set the 3 default channels to the same frequency (must be before sending the OTAA join request)
    lora.add_channel(0, frequency=config.LORA_FREQUENCY, dr_min=0, dr_max=5)
    lora.add_channel(1, frequency=config.LORA_FREQUENCY, dr_min=0, dr_max=5)
    lora.add_channel(2, frequency=config.LORA_FREQUENCY, dr_min=0, dr_max=5)

    # join a network using OTAA
    try:

        lora.join(activation=LoRa.OTAA, auth=(dev_eui, app_eui, app_key), timeout=16000, dr=config.LORA_NODE_DR)  #timeout 16000

    # wait until the module has joined the network
        while not lora.has_joined():
            time.sleep(2.5)
            #pycom.rgbled(0x7f7f00)                                  # yellow = lora.join pending
            print('Not joined yet...')
        print('LoRa joined!')
        #pycom.rgbled(0x007f00)                                      # green = lora.join complete

    # remove all the non-default channels
        for i in range(3, 16):
            lora.remove_channel(i)

    # create a LoRa socket
        s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)

    # set the LoRaWAN data rate
        #s.setsockopt(socket.SOL_LORA, socket.SO_DR, config.LORA_NODE_DR)    # send unconfirmed messages
        s.setsockopt(socket.SOL_LORA, socket.SO_CONFIRMED, True)             # send confirmed messages
    # make the socket non-blocking
        s.setblocking(False)

        lora.nvram_save()
        time.sleep(0.1)

    except Exception as e:
        print(str(e))
else:
    print("Join already")
    s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
    s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
    s.setsockopt(socket.SOL_LORA, socket.SO_CONFIRMED, True)                #AHHHHHH POINT!!!!
    s.setblocking(False)

mount_SD()
lora.callback(trigger=(LoRa.TX_PACKET_EVENT | LoRa.TX_FAILED_EVENT), handler=lora_cb)

################################################ Main Cycle #########################################################
while (True):
    print("CICLO")
    global sd
    global SEMAFORO
    global STRING_READ
    global GPS_READ
    bytes2send = bytearray()                                 # bytearray que ira conter os valores em bytes a enviar
    values=[]
    a=pycom.nvs_get('count')
    decoded_val=[]

    if a%4==0:     # a cada 4 mensagens tira uma correcção GPS
        GPS_READ = True
        GPS_pin.value(1)
        formats=['H','H','H','f','f','H','B','f','f','f','B','B','B']  # id,lat,long,alt,hora,min,seg,humid,temp,light0,light1,press,bat = 34 + 13 = 47 bytes
    else:
        GPS_READ = False
        formats = ['H','H','H','f','f','H','B']  # id,humid,temp,light0,light1,press,bat = 19 + 13 = 32 bytes

    print("GPS_READ :", GPS_READ)


    values=readSensor()
    bytes2send=encoder(values, formats)
    GPS_pin.value(0)
    # print('bytes2send', bytes2send)
    decoded_val=decoder(bytes2send)
    print("Decoded values: ", decoded_val)

    a+=1
    pycom.nvs_set('count', a)

    if lora.has_joined():
        try:
            print("Lora joined -> 1st send")
            s.send(bytes2send)

            while (SEMAFORO == True):
                pass

        except Exception as e:
            print(str(e))

    if not lora.has_joined():
        print("Not joined -> Save message")
        write_toSD(LOG_FILENAME, bytes2send)
        time.sleep(0.1)

        if GPS_READ==True:
            #py.setup_sleep(10)
            py.setup_sleep(11032)
            py.go_to_sleep(False)           # Estado 1
        else:
            #py.setup_sleep(10)
            py.setup_sleep(2572)
            py.go_to_sleep(False)           # Estado 0

########################################################################################################################

################################################# TOD0 LIST ############################################################

    # Add features:
        # Implement WDT for safety reasons - Ultima coisa a fazer apenas quando saber ao certo quanto tempo demora um duty cycle
        #     wdt = WDT(timeout=2000)  # enable it with a timeout of 2 seconds
        #     wdt.feed()

    # Test wdt com sleep > 60 seg

    # Clean up!!! (delete prints and unnecessary code/comments and insert comments where needed)

################################################# Debugging section ####################################################

    # a=base64.b64encode(bytes2send)
    # print(a)

################################################# Handy commands #######################################################

    # lora.nvram_erase()
    # pycom.nvs_erase('count')

################################################# General color code ###################################################

    # pycom.rgbled(0x007f00) -> green = <action> accepted
    # pycom.rgbled(0x7f7f00) -> yellow = <action> pending
    # pycom.rgbled(0x7f0000) -> red = <action> gone wrong

    # END OF DEVELOPMENT pycom.heartbeat(False)
