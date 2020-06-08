#!/usr/bin/python
# -*- coding: utf-8 -*-
import binascii #pour convertir l'hexa en string
#import socket #pour afficher gérer les sockets (utilisé ici que pour afficher une erreur de timeout)
import base64
import paho.mqtt.client as paho

broker = "YOUR BROKER IP or ADDRESS"
port = YOUR BROKER Port 1883
def on_publish(client,userdata,result):             #create function for callback
    print("data published \n")
    pass
client1= paho.Client("mirror2mqtt")                           #create client object
#client1.on_publish = on_publish                          #assign function to callback
client1.connect(broker,port)                                 #establish connection
client1.loop_start()

#ouverture du port hidraw0 (port du mir:ror) en mode lecture octet par octet (rb)
mirror = open("/dev/mirror", "rb")

erreur_generale = False
while erreur_generale == False:
  #on lit les données envoyées par le mir:ror
  try:
    donnee = mirror.read(16)
  except Exception as e:
    print ("Erreur inconnue (lecture du  mir:ror) : %s" % e)
    erreur_generale = True

  #on test les données renvoyées par le mir:ror
  if donnee != '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00':
    try:
      rfid_id = binascii.hexlify(donnee)[4:]
    except Exception as e:
      print ("Erreur inconnue (conversion binaire-string) : %s" % e)

    #on test les 2 premiers octets pour savoir si une puce RFID est posée ou retirée
    if donnee[0:2] == '\x02\x01': #puce posée
      client1.publish("/MIRROR/" + str(rfid_id) , "ON",qos=1, retain=True)
      print ("Puce %s posée." % rfid_id)

    elif donnee[0:2] == '\x02\x02': #puce retirée
      print ("Puce %s retirée." % rfid_id)
      client1.publish("/MIRROR/" + str(rfid_id) , "OFF",qos=1, retain=True)

    #on test le ler octet, s'il vaut 1, alors une action à été faite sur le mir:ror
    if donnee[0] == '\x01':

      if donnee[1] == '\x04':
        print ("Le mir:ror est retourné face vers le haut")
        client1.publish("/MIRROR","UP",qos=1, retain=True)

      if donnee[1] == '\x05':
        print ("Le mir:ror est retourné face vers le bas")
        client1.publish("/MIRROR","DOWN",qos=1, retain=True)
