# -*- coding: utf-8 -*-
"""
Created on Sat Nov 28 11:43:56 2020

@author: Julien
"""

# Summary:
# Class représentant un client tcp. 

import os
import socket
import threading

HOST = "127.0.0.1"
PORT = 52030
BUFFER_SIZE=2048
END = False

# Thread qui gère la réception des données du serveur. 
class ReceiveResponseFromServerThread(threading.Thread):
    def __init__(self, clientSocket, sender_client):
        threading.Thread.__init__(self)
        self.cSocket = clientSocket
        self.my_sender_address = str(sender_client.getsockname())
        self.Sender_client = sender_client
        self.pseudo = ''
        self.etat = True
        print("Thread pour la réception des données initialisé")
        
    # Methode exécutée quand le Thread est lancé.
    def run(self):
        global END
        msg = ''
        try:
            while True:
                data = self.cSocket.recv(BUFFER_SIZE) # Instruction "bloquante". Tant que le Thread ne reçoit pas de message, il ne passe pas à la ligne suivante. 
                msg = data.decode()
                print(msg) if msg != "#Kill" else print("-----btzzzzz-------")
                if "#Response TrfD#" in msg:
                    m = msg.split('/')
                    received_f = m[1]    
                    f = open(received_f, 'wb')
                    while True:
                        data = self.cSocket.recv(BUFFER_SIZE)
                        if b"#End TrfD#" in data:
                            break                      
                        f.write(data) # Write data to a file
                    f.close()
                if "#Kill" in msg:
                    print("Saisissez vos derniers mots:")
                    send_message("#Exit",self.Sender_client)
                    self.cSocket.close()
                    self.Sender_client.close()
                    self.etat = False
                    END = True
        except:
            self.cSocket.close()
            #print("Fin du thread")
                
                
            
# Fonction pour la connexion au serveur.
def connect_to_server(HOST, PORT):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((HOST, PORT))
    print ("Connexion vers " + HOST + " : " + str(PORT) + " réussie.")
    return client


# Fonction pour envoyer un message au serveur. 
def send_message(message, client):
    message = message.encode('UTF-8')
    n = client.send(message)
    if n!=len(message):
        print("Erreur envoi")
        
       
# Fonction pour envoyer un fichier.
def send_file(filename, socket):    
    if os.path.exists(filename):
        send_message("#TrfU Request# - " + filename, socket) 
        f = open(filename, 'rb')
        while True:
            l = f.read(BUFFER_SIZE)
            while (l):
                socket.send(l)
                l = f.read(BUFFER_SIZE)
            if not l:
                f.close()
                send_message("#End TrfU#", socket)
                print("File is uploaded on server")
                break
    else:
        print("Fichier introuvable.")
        
# Fonction pour envoyer un fichier.
def send_private_file(recipient, filename, socket):
    if os.path.exists(filename):
        send_message("#TrfU private Request# - " + recipient + "-" + filename, socket)                
        f = open(filename, 'rb')
        while True:
            l = f.read(BUFFER_SIZE)
            while (l):
                socket.send(l)
                l = f.read(BUFFER_SIZE)
            if not l:
                f.close()
                send_message("#End TrfU#", socket)
                print("File is uploaded on server")
                break
    else:
         print("Fichier introuvable.")
  

def main():
    receiver_client = connect_to_server(HOST, PORT) # création du socket pour la réception des données. 
    sender_client = connect_to_server(HOST, PORT) # création du socket pour l'envoie des données. 
    
    #my_sender_address = str(sender_client.getsockname())
    print("Mon adresse d'envoie : " + str(sender_client.getsockname()))
    
    receiveResponseFromServerThread = ReceiveResponseFromServerThread(receiver_client, sender_client) # Création du Thread qui va gérer la réception des données. 
    receiveResponseFromServerThread.start() # Démarrage du thread. 
    
    # L'émission de message se fait dans le main. 
    while not END:       
        #message = input("Moi : ")
        message = input()
        if not END:
            if "TrfU" not in message: 
                send_message(message, sender_client)
        else:
            print ("Malheureusement le serveur est fermé pour toi, mais intéressant.")
            break
        if message == "#Help":
            print("Liste de toutes les commandes clients : \n")
            print("#Exit : permet de quitter le chat client\n")
            print("#ListU : permet d'obtenir la liste des utilisateurs présents sur le serveur\n")
            print("#ListF : permet d'obtenir la liste des fichiers du serveur\n")
            print("#TrfU <nom du fichier>: permet de transférer un fichier du client vers le serveur\n")
            print("#TrfU private <destinataire> <nom du fichier>: permet de transférer un fichier du client vers le serveur dans un dossier privé.\n")
            print("#TrfD <nom du fichier> : permet de transférer un fichier du server vers le client \n")
            print("#Private <user> : permet le chat privé entre deux utilisateurs\n")
            print("#Public : permet le retour au chat public\n")
            print("#Poke <user>/<message>: permet d'envoyer un message en privé à un utilisateur en restant dans le mode Public\n")
            print("#Ring <user> : permet de savoir si un utilisateur est connecté")
        if message == "#Exit":
            print ("Déconnexion")
            sender_client.close()
            receiver_client.close()
            break
        if "#TrfU private" in message:
            msg = message.split(' ')
            recipient = msg[2]
            filename = msg[3]
            send_private_file(recipient, filename, sender_client)
        
        
        elif "#TrfU" in message:
            msg = message.split(' ')
            if msg[1]:
                filename = msg[1]       
            send_file(filename, sender_client)
           
        
                               
    
    
    
    
main()