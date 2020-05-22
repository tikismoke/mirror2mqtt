#!/usr/bin/python
# -*- coding: utf-8 -*-
import binascii #pour convertir l'hexa en string
# from urllib2 import Request, urlopen, URLError, HTTPError #pour pouvoir appeler une url
import socket #pour afficher gérer les sockets (utilisé ici que pour afficher une erreur de timeout)
from xml.dom.minidom import parse #pour pouvoir parser un fichier XML  avec minidom
import base64
import paho.mqtt.client as paho

#ouvre le fichier XML en utilisant le parser 'minidom'
DOMTree = parse("/home/pi/mirrorpy/mirror.xml")
#construit l'arbre de la structure du fichier XML et le stock dans une variable
collection = DOMTree.documentElement
#récupére tous les éléments qui ont pour tag 'rfid' de l'arbre
puces = collection.getElementsByTagName("rfid")

#crée deux listes, une pour les puces posée et une pour les puces retirée
liste_puces_posee = []
liste_puces_retire = []

#on parcourt l'arbre qui contient toutes les puces et rempli les listes en fonction de l'action et de l'état indiqué dans le fichier XML
for puce in puces:
  id_puce = puce.getAttribute("id")
#  descriptif = puce.getElementsByTagName('descriptif')[0].childNodes[0].nodeValue
  etat = puce.getElementsByTagName('etat')[0].childNodes[0].nodeValue
  action = puce.getElementsByTagName('action')[0].childNodes[0].nodeValue
  url = puce.getElementsByTagName('url')[0].childNodes[0].nodeValue
#  username = puce.getElementsByTagName('login')[0].childNodes[0].nodeValue
#  password = puce.getElementsByTagName('password')[0].childNodes[0].nodeValue
#  commentaire = puce.getElementsByTagName('commentaire')[0].childNodes[0].nodeValue
  #detail_puce = [id_puce, [descriptif, url, commentaire]]
#  detail_puce = [id_puce, url, username, password]
  detail_puce = [id_puce, url]

  if etat == 'actif':
    if action == 'pose':
      liste_puces_posee.append(detail_puce)
    if action == 'retire':
      liste_puces_retire.append(detail_puce)

broker="YOURBROKERIPHERE"
port=1883
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
      #liste des puces qui doivent faire une action quand la pose sur le mir:ror

      puce_definie_dans_xml = False
      #'puces_posee' va prendre les valeurs successives des éléments de 'liste_puces_posee'
      #for i, puces_posee, username, password in liste_puces_posee:
      for i, puces_posee in liste_puces_posee:
        if rfid_id == format(i):
          client1.publish("/MIRROR/" + str(rfid_id) , "ON",qos=1, retain=True)
          requete = Request(format(puces_posee))
          #base64string = base64.b64encode('%s:%s' % (username, password))
          #requete.add_header("Authorization", "Basic %s" % base64string)  
          try:
            #on essaye d'appeler la requête
            url = urlopen(requete, timeout = 1)
          except HTTPError as e:
            print ('Le serveur n''a pas pu répondre à la demande.')
            print ('Error code: ', e.code)
          except URLError as e:
            try:
              if e.reason.errno == 111:
                print ("Connexion refusée.")
              if isinstance(e.reason, socket.timeout):
                print ("Temps de connexion dépassé.")
            except:
              print ("Erreur  : %s" % e.reason)

          puce_definie_dans_xml = True

      if puce_definie_dans_xml == False:
        client1.publish("/MIRROR/" + str(rfid_id) , "ON",qos=1, retain=True)
        print ("Puce %s posée." % rfid_id)

    elif donnee[0:2] == '\x02\x02': #puce retirée
      #liste des puces qui doivent faire une action quand la retire sur le mir:ror

      puce_definie_dans_xml = False
      #'puces_retire' va prendre les valeurs successives des éléments de 'liste_puces_retire'
      #for i, puces_retire, username, password in liste_puces_retire:
      for i, puces_retire in liste_puces_retire:
        if rfid_id == format(i):
          client1.publish("/MIRROR/" + str(rfid_id) , "OFF",qos=1, retain=True)
          requete = Request(format(puces_retire))
          #base64string = base64.b64encode('%s:%s' % (username, password))
          #requete.add_header("Authorization", "Basic %s" % base64string)
          try:
            #on essaye d'appeler la requête
            url = urlopen(requete, timeout = 1)
          except HTTPError as e:
            print ('Le serveur n''a pas pu répondre à la demande.')
            print ('Error code: ', e.code)
          except URLError as e:
            try:
              if e.reason.errno == 111:
                print ("Connexion refusée.")
              if isinstance(e.reason, socket.timeout):
                print ("Temps de connexion dépassé.")
            except:
              print ("Erreur  : %s" % e.reason)

          puce_definie_dans_xml = True

      if puce_definie_dans_xml == False:
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
