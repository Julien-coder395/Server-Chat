"""
Created on Sat Nov 28 12:14:33 2020

@author: Julien
"""

# Summary
# Cette classe représente un serveur TCP multi-thread. Il peut gérer la connexion de plusieurs clients.

import os
import socket
import threading
import database_sqlite_access as dao
from datetime import datetime
import random #for CommandThread
import time

HOST = "127.0.0.1"
PORT = 52030
BUFFER_SIZE = 2048
SERVERADDRESS = ">>>"
CONNECTED_CLIENTS = 0
connected_clients = [] # liste qui va contenir tous les clients connectés. 
lst_files = []
SERVER_SWITCH = True

AUTOCONNEXION = False
if AUTOCONNEXION == True:
    USERNAME = "michel"
    PASSWORD = "esilv"
    
# Classe représentant un client connecté au serveur.
class Client():
    def __init__(self, clientAddress, senderSocket, receiverSocket, clientNumber):
        self.address = clientAddress
        self.senderSocket = senderSocket # Socket utilisé par le client pour envoyer des données.
        self.receiverSocket = receiverSocket # Socket utilisé par le client pour recevoir des données. 
        self.number = clientNumber
        self.pseudo = ""
        self.privateMode = False # Variables pour gérer la communication privée.
        self.correspondentPseudo = ""

    def __str__(self):
        return self.pseudo
    
# Thread représentant un client connecté au serveur.
class ClientThread(threading.Thread):
    def __init__(self, client):
        threading.Thread.__init__(self)
        self.Client = client
        print("New connection added: ", clientAddress)
       
    # Methode exécutée quand le Thread est lancé. 
    def run(self):
        global connected_clients
        print("Connection from : ", self.Client.address)
        authentication_result = ask_authentication(self.Client)
        if authentication_result and authentication_result[0]:
            self.Client.pseudo = authentication_result[1]
            write_in_log_file("Connexion de " + self.Client.pseudo + " / Adresse IP : " + str(self.Client.address)  + " à " + str(datetime.now()))
            while True:
                data = self.Client.senderSocket.recv(BUFFER_SIZE) # Instruction "bloquante". Tant que le Thread ne reçoit pas de message, il ne passe pas à la ligne suivante. 
                data = data.decode()
                print(self.Client.pseudo + " : " + data)
                write_in_chat_file(self.Client.pseudo + " : " + data)
                #data: "input du client" 
                
                if data.startswith(("#Poke","#poke")):
                    warning = "[WARNING]Le format est du type: #Poke 'pseudo'/'message'".encode('UTF-8')
                    if "/" not in data or " " not in data:
                        n = self.Client.receiverSocket.send(warning)
                    else:
                        private_features = data.split('/')
                        private=private_features[0]
                        msg='\033[32m' + private_features[1] + '\033[0m'
                        priv = private.split(' ')
                        self.Client.correspondentPseudo = priv[1]
                        if user_is_connected(self.Client.correspondentPseudo):
                            print(self.Client.correspondentPseudo  + " est bien connecté")
                            msg1 = ('\033[32m' + str(SERVERADDRESS)+self.Client.pseudo+" -> "+self.Client.correspondentPseudo+" : "+msg + '\033[0m').encode('UTF-8')
                            n = self.Client.receiverSocket.send(msg1)
                            poke_initialisation(self.Client.pseudo, self.Client.correspondentPseudo,msg)
                        else:
                            msg = (str(SERVERADDRESS) + " : L'utilisateur n'est pas connecté ou erreur de saisie. ").encode('UTF-8')
                            n = self.Client.receiverSocket.send(msg)
                            if n!= len(msg):
                                print("Erreur envoi indication utilisateur pas connecté")
                            print(self.Client.correspondentPseudo + " n'est pas connecté. Impossible d'établir la connexion privée")
                
                if "#Private" in data:
                    private_features = data.split(' ')
                    if len(private_features) > 0:
                        self.Client.correspondentPseudo = private_features[1]
                    else:
                        self.Client.correspondentPseudo = input("Saisir son pseudo")
                    print("Mode privée activée pour ", self.Client.pseudo, " avec ", self.Client.correspondentPseudo)
                    write_in_log_file("Mode privée activée pour " + self.Client.pseudo + " avec " + self.Client.correspondentPseudo + " à " + str(datetime.now()))
                    if user_is_connected(self.Client.correspondentPseudo):
                        print(self.Client.correspondentPseudo  + " est bien connecté")
                        self.Client.privateMode = True
                        private_connection_initialisation(self.Client.pseudo, self.Client.correspondentPseudo)
                    else:
                        msg = (str(SERVERADDRESS) + " : L'utilisateur n'est pas connecté. ").encode('UTF-8')
                        n = self.Client.receiverSocket.send(msg)
                        if n!= len(msg):
                            print("Erreur envoi indication utilisateur pas connecté")
                        print(self.Client.correspondentPseudo + " n'est pas connecté. Impossible d'établir la connexion privée")

                if "#Public" in data:
                    self.Client.privateMode = False
                    return_in_public_mode(self.Client.correspondentPseudo)
                    print("Mode public activée pour ", self.Client.pseudo)
                    write_in_log_file("Retour au mode public pour " + self.Client.pseudo + 
                                      " et " + self.Client.correspondentPseudo + ", initié par " + self.Client.pseudo + " à " + str(datetime.now()))
                
                if data == "#ListU":
                    msg = (str(SERVERADDRESS) + list_users()).encode('UTF-8')
                    n = self.Client.receiverSocket.send(msg)
                    
                if data == "#ListF":
                    msg = (str(SERVERADDRESS) + list_files_v2()).encode('UTF-8')
                    n = self.Client.receiverSocket.send(msg)
                    
                if "#Ring" in data:
                    private_features = data.split(' ')
                    if len(private_features) > 0:
                        self.Client.correspondentPseudo = private_features[1]
                    else:
                        self.Client.correspondentPseudo = input("Saisir son pseudo:")
                    if user_is_connected(self.Client.correspondentPseudo):
                        msg = (str(SERVERADDRESS) + " : "+self.Client.correspondentPseudo+" est connecté. ").encode('UTF-8')
                        n = self.Client.receiverSocket.send(msg)
                    else:
                        msg = (str(SERVERADDRESS) + " : "+self.Client.correspondentPseudo+" n'est pas connecté. ").encode('UTF-8')
                        n = self.Client.receiverSocket.send(msg)
                    
                if "#TrfD" in data:
                    file_features = data.split(' ')
                    filename = file_features[1]
                    if filename in lst_files:
                        send_file(filename, self.Client)
                    else:
                        msg = (str(SERVERADDRESS) + " Fichier non existant. ").encode('UTF-8')
                        self.Client.receiverSocket()
                
                if "#TrfU Request#" in data:
                    d = data.split('-')
                    filename = d[1].strip()
                    receive_file(self.Client, filename)
                    
                if data == '#Exit':
                    print("Déconnexion de :", self.Client.pseudo)
                    time.sleep(1)
                    self.Client.senderSocket.close()
                    self.Client.receiverSocket.close()
                    connected_clients.remove(self.Client)
                    write_in_log_file("Déconnexion de " + self.Client.pseudo + " à " + str(datetime.now()))
                    break
                
                if "#TrfU private Request#" in data:
                    d = data.split('-')
                    recipient = d[1].strip()
                    filename = d[2].strip()                    
                    receive_private_file(self.Client, filename, recipient)
                
                if self.Client.privateMode == False:
                    send_all(data, self.Client.pseudo) # Envoie du message reçu à tout les clients connectés. 
                elif self.Client.privateMode == True:
                    send_private(data, self.Client.pseudo, self.Client.correspondentPseudo)


# Fonction pour écrire dans le fichier de log.       
def write_in_log_file(message):
    message += "\n"
    filename = "LogFile.txt"
    f = open(filename, "a")
    f.write(message)
    f.close()

def write_in_chat_file(message):
    message += "\n"
    filename = "ChatFile.txt"
    f = open(filename, "a")
    f.write(message)
    f.close()
    
def list_users():
    L='Liste des utilisateurs connectés : \n'
    for client in connected_clients:
        L=L+client.pseudo+' \n'
    return L
       
def list_files():
    L='Liste des fichiers du serveur : \n'
    for files in lst_files:
        L=L+files+' \n'
    return L

def list_files_v2():
    L='Liste des fichiers du serveur : \n'
    files = os.listdir()
    files.remove('database_sqlite_access.py')
    if 'LogFile.txt' in files:
        files.remove('LogFile.txt')
    if 'ChatFile.txt' in files:
        files.remove('ChatFile.txt')
    if '__pycache__' in files:
        files.remove('__pycache__')
    if 'server_chat_database.db' in files:
        files.remove('server_chat_database.db')
    if 'server_multi_thread.py' in files:
        files.remove('server_multi_thread.py')
    for file in files:
        L=L+file+' \n'
    return L
    
def receive_file(client, filename):
    lst_files.append(filename)
    f = open(filename, 'wb')
    while True:
        data = client.senderSocket.recv(BUFFER_SIZE)
        if b"#End TrfU#" in data:
            break                      
        f.write(data) # Write data to a file
    f.close()
    
def send_file(filename, client):
    send_msg_to_client(client.receiverSocket, (str(SERVERADDRESS) + " #Response TrfD# /" + filename).encode('UTF-8'))
    f = open(filename, 'rb')
    while True:
        l = f.read(BUFFER_SIZE)
        while (l):
            client.receiverSocket.send(l)
            l = f.read(BUFFER_SIZE)
        if not l:
            f.close()
            send_msg_to_client(client.receiverSocket, (str(SERVERADDRESS) + " #End TrfD#").encode('UTF-8'))
            break

 
def receive_private_file(client, filename, recipient):
    if not os.path.exists(recipient):
        os.makedirs(recipient)
    os.chdir(recipient)
    f = open(filename, 'wb')
    while True:
        data = client.senderSocket.recv(BUFFER_SIZE)
        if b"#End TrfU#" in data:
            break                      
        f.write(data) # Write data to a file
    f.close()
    os.chdir("..")
    
    if user_is_connected(recipient):
        for client in connected_clients:
            if client.pseudo == recipient:             
                send_msg_to_client(client.receiverSocket, (str(SERVERADDRESS) + " Un fichier privé vient de vous être envoyé. Consulter votre dossier personnel pour consulter ce fichier.").encode('UTF-8'))


def user_is_connected(correspondent):
    for client in connected_clients:
        if client.pseudo == correspondent:
            return True
    return False

def poke_initialisation(initiator, correspondent, msg):
    for client in connected_clients:
        if client.pseudo == correspondent:
            if(initiator==correspondent):
                msg3=(str(SERVERADDRESS)+"Bah alors on se sent seul ?").encode('UTF-8')
                n=client.receiverSocket.send(msg3)
                return
            else:
                client.correspondentPseudo = initiator
                msg2 = (str(SERVERADDRESS)+client.correspondentPseudo+" -> "+client.pseudo+" : "+msg).encode('UTF-8')
                n = client.receiverSocket.send(msg2)
                if n!= len(msg2):
                    print("Erreur envoi lors de l'initialisation de la communication privée")
                return

# initiator = pseudo (string) du client qui initie la communication privée.
# correspondent = pseudo (string) du correspondant.
def private_connection_initialisation(initiator, correspondent):
    for client in connected_clients:
        if client.pseudo == correspondent:
            client.privateMode = True
            client.correspondentPseudo = initiator
            msg = ('\033[34m' + str(SERVERADDRESS) + " : Connection privée initiée par " + initiator + '\033[0m').encode('UTF-8')
            n = client.receiverSocket.send(msg)
            if n!= len(msg):
                print("Erreur envoi lors de l'initialisation de la communication privée")
            return


def return_in_public_mode(correspondent):
    for client in connected_clients:
        if client.pseudo == correspondent:
            client.privateMode = False
            client.correspondentPseudo = ""
            msg = (str(SERVERADDRESS) + " Retour à la conversation publique").encode('UTF-8')
            n = client.receiverSocket.send(msg)
            if n!= len(msg):
                print("Erreur envoi lors du retour à la conversation publique")
            return

# Thread permettant l'exécution de commande sur le serveur.
class CommandThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        
    def run(self):
        global SERVER_SWITCH 
        start = True
        while start:
            print(surprise())
            print("If you need help or learn more about it: #Help")
            working = True
            while(working):
                action_on_server = input("Your action on the server : ")
                action_on_server = action_on_server.rstrip() #Void Blank
                
                if action_on_server in ["#Help", "#help"]:
                    helpCommand()
                    
                if action_on_server in ["close","#Exit","#exit"]:
                    working, start = False, False
                    close_all_client_Thread()
                    SERVER_SWITCH = False
                    
                    
                if action_on_server == "hello":
                    print("hello")
                    
                if action_on_server.startswith(("#Kill","#kill")):
                    killCommand(action_on_server)
                
                if action_on_server in ["#ListU","#listU","#Listu","#listu"]:
                    print("la liste des utilisateurs:")
                    for i in connected_clients:
                        ourClient = ["Wonderful", "Strongest", "Richest","Smart"]
                        print(ourClient[random.randint(0,len(ourClient)-1)]," ",i)
                
                if action_on_server.startswith(("#Alert","#alert")):
                    alertCommand(action_on_server)
                
                if action_on_server in ["#ListF","#Listf"]:
                    print(list_files_v2())                    
                # else:
                #     print("Il n'y a pas de fichier disponible")
                        
                if action_on_server.startswith(("#Private", "#private")):
                    privateCommand(action_on_server)
        

# Méthode permettant d'envoyer un message à tous les clients connectés.
# Methode de Broadcast en quelque sorte. 
# sender = pseudo du client qui envoie le message.
def send_all(message, sender):
    Liste=["#TrfU private","#Poke","#ListU","#Private","#Public","#Ring","#ListF","#Help"]
    for i in Liste:
        if i in message:
            return
    sent_msg = str(sender) + " : "  + message
    sent_msg = sent_msg.encode('UTF-8')
    for client in connected_clients:
        if client.privateMode == False:
            if sender != client.pseudo:
                n = client.receiverSocket.send(sent_msg)
                if n != len(sent_msg):
                    print("Erreur envoi.")
                    
                    
# Méthode permettant d'envoyer un message privé.
# sender = pseudo (string) du client qui envoie le message.   
# correspodent = pseudo (string) du correspondant.
def send_private(message, sender, correspondent):
    Liste=["#Poke","#ListU","#Private","#Public","#Ring","#ListF","#Help"]
    for i in Liste:
        if i in message:
            return
    sent_msg = str(sender) + " : "  + message
    sent_msg = sent_msg.encode('UTF-8')
    for client in connected_clients:
        if client.pseudo == correspondent:
            n = client.receiverSocket.send(sent_msg)
            if n != len(sent_msg):
                print("Erreur envoi.")
                return


# Reçoit un message encodé et l'envoie à un client.
def send_msg_to_client(socket, msg):
    n = socket.send(msg)
    result = True
    if n!= len(msg):
        print("Erreur envoi.")
        result = False
    return result


def helpCommand():
    print("#Exit: Shuting the server down.")
    print("#Kill<user>: Kicking an user by putting his nickname.")
    print("#ListU: Showing the list of all users on the server.")
    print("#ListF: Showing the list of all the files on the server.")
    print("#Private<user>: Speaking privately with an user by his nickname.")
    print("#Alert <all users>: Alerting all users with a message or nothing.")

def killCommand(action_on_server, raison = ""):
    userPseudo = ""
                    
    if (action_on_server == "#Kill" or
                            action_on_server == "#kill"):
                        userPseudo = input("User pseudo: ")
    else:
                        userPseudo = action_on_server.split(" ")[1]
    reason = input("reason:") if raison == "" else raison
    for client in connected_clients:
        if client.pseudo == userPseudo:
            #connected_clients.remove(client)
            print("###KILL### :",userPseudo, " kicked for ",reason)
            send_msg_to_client(client.receiverSocket,"#Kill".encode('UTF-8'))
            #client.working = False
            return 0
    print("Je ne trouve pas le client comportant le pseudo: ",userPseudo )
                    
            
    #Manque la facon de l'éjecter
    
                    
def alertCommand(message):
    if message in ["#Alert","#alert"]:
        message = input("Saisie de ton message: ")
    else:
        
        message = message[7:]
    finalMessage = ("\033[31m"+
        "\n ####################ALERT######################## \n"+
                        message + " \n " +
                        "####################ALERT########################"
                        + "\033[0m")
    send_all(finalMessage, "Admin")

def privateCommand(message):
    pseudo = ""
    if message in ["#Private","#private"]:
        pseudo = input("Saisie le pseudo de la personne:")
    else:
        pseudo = message.split(" ")[1]  
    for c in connected_clients:
        if c.pseudo == pseudo:
            message = input("Saisie de ton message: ")
            finalMessage = ("[Private from admin]: " + message).encode('UTF-8')
            send_msg_to_client(c.receiverSocket,finalMessage)
            return 0
    print("pseudo invalide")

def close_all_client_Thread():
    alertCommand("#Alert             ____fermeture du serveur____")
    for c in connected_clients:
        killCommand("#Kill " + c.pseudo,"MAINTENANCE")
    
    return 0

def surprise():
    message =(
        "                                                 \n"+
        "                                                 \n"+                                         
        "                            **.                  \n"+                                           
        "            ####(         %#####*                \n"+                                         
        "             #####       .%#####                 \n"+                                          
        "              /###%       (###*                  \n"+                                           
        "               .####*      (#                    \n"+                                           
        "                 %####                           \n"+                                           
        "                  (###%                          \n"+                                           
        "                   ,###%                         \n"+                                           
        "                     %#%                         \n"+                                           
        "                      #                          \n"+                                           
        "                                                 \n"+
        "                                                 \n"+                                           
        " WELCOME       TO          OUR        SERVER     \n")                                                                                            
                                                                                                       
    return(message)

# Demande d'authentification du serveur au client.
# socketForReceive = socket de réception du client (va être utilisé pour l'envoie de donnée)
# socketForSend = socket du client pour envoyer des données (va être utilisé pour la réception des données)
def ask_authentication(client):
    
    global USERNAME, PASSWORD, AUTOCONNEXION
    
    #PHASE AUTOCONNEXION 
    if AUTOCONNEXION == True:
        try:
            conn = dao.initialisation()
            result_authentication = dao.authentication(conn, USERNAME, PASSWORD)
            if result_authentication[0]:
                    print("CONNEXION AUTOMATIQUE REUSSIT")
                    dao.close(conn)
                    connected_clients.append(client)
                    return (True, USERNAME)
        except:
            print("Déconnexion client pendant phase authentification")
            write_in_log_file("Déconnexion client pendant phase authentification")         
            
    #PHASE UTILISATEUR    
    else:
        try:
            conn = dao.initialisation()
            
            do = True
            while do:
                msg = (str(SERVERADDRESS) + " Avez-vous un compte ? (oui/non)").encode('UTF-8')
                if not send_msg_to_client(client.receiverSocket, msg):
                    dao.close(conn)
                    return False 
                
                rsp = client.senderSocket.recv(2048)
                rsp = rsp.decode()
                if rsp == "oui" or rsp == "non":          
                    do = False
                  
            if rsp == "oui":
                msg = (str(SERVERADDRESS) + " Saisissez votre identifiant").encode('UTF-8')
                if not send_msg_to_client(client.receiverSocket, msg):
                    dao.close(conn)
                    return False
                username = client.senderSocket.recv(2048)
                username = username.decode().strip()
                if dao.check_if_user_exist(conn, username):
                    msg = (str(SERVERADDRESS) + " Saisissez votre mot de passe").encode('UTF-8')
                    if not send_msg_to_client(client.receiverSocket, msg):
                            dao.close(conn)
                            return False
                    password = client.senderSocket.recv(2048)
                    password = password.decode().strip()
                    do = False
                else:
                    msg = (str(SERVERADDRESS) + " Utilisateur non existant.\n Si vous souhaitez créer un compte déconnectez-vous.\n Puis répondez 'non' à la première question.").encode('UTF-8')
                    if not send_msg_to_client(client.receiverSocket, msg):
                        dao.close(conn)
                        return False
                    return False
            
                result_authentication = dao.authentication(conn, username, password)
                if result_authentication[0]:
                    msg = (str(SERVERADDRESS) + " Authentification réussie $*$*$*$ - " + username).encode('UTF-8')
                    dao.close(conn)
                    if not send_msg_to_client(client.receiverSocket, msg):                
                        return False
                    connected_clients.append(client)
                    return (True, username)
                else:
                    msg = (str(SERVERADDRESS) + " Authentification a échoué.\nVous n'êtes pas connecté au serveur.\nQuittez avec '#Exit' et recommencez.").encode('UTF-8')
                    dao.close(conn)
                    if not send_msg_to_client(client.receiverSocket, msg):            
                        return False         
                    return False
                
            elif rsp == "non":
                do = True
                while do:
                    msg = (str(SERVERADDRESS) + " Saissiez le username/password avec un slash entre les deux : ").encode('UTF-8')       
                    if not send_msg_to_client(client.receiverSocket, msg):
                        dao.close(conn)
                        return False
                    response = client.senderSocket.recv(2048)  # Réception des identifiants créées par l'utilisateur.
                    response = response.decode()
                    if '/' in response:
                        response = response.split('/') # Décomposition du message.
                        username = response[0].strip() # Suppression des éventuelles espaces inutiles.
                        password = response[1].strip() 
                        result_add_user = dao.add_user(conn, username, password)
                   
                        if result_add_user == "Utilisateur ajouté": # Ajout de l'utilisateur dans SQLite.
                            connected_clients.append(client)
                            msg = (str(SERVERADDRESS) + " Création utilisateur réussie.\nVous pouvez commencer à chatter.").encode('UTF-8')       
                            dao.close(conn)
                            if not send_msg_to_client(client.receiverSocket, msg):                       
                                return False
                            return (True, username)
                        elif "UNIQUE constraint failed: users.username" in str(result_add_user):
                            msg = (str(SERVERADDRESS) + " Utilisateur déjà existant.\Choississez-en un autre.").encode('UTF-8')       
                            if not send_msg_to_client(client.receiverSocket, msg):
                                dao.close(conn)
                                return False
        except:
            print("Déconnexion client pendant phase authentification")
            write_in_log_file("Déconnexion client pendant phase authentification")
        
def load_files():
    files = os.listdir()
    files.remove('database_sqlite_access_v3.py')
    if 'LogFile.txt' in files:
        files.remove('LogFile.txt')
    if 'ChatFile.txt' in files:
        files.remove('ChatFile.txt')
    if '__pycache__' in files:
        files.remove('__pycache__')
    return files

def load_files_secure():
    files = os.listdir()
    removelist = ['database_sqlite_access.py','LogFile.txt','ChatFile.txt','__pycache__']
    for elmt in removelist:
        if elmt in files:
            files.remove(elmt)
    return files 

## Main ##    
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Création du serveur. 
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT)) # Bind avec l'addresse et le numéro de port. 
print("Server started")
print("Waiting for client request...")

commandThread = CommandThread() # Creation du Thread qui va gérer les commandes pour le serveur. 
commandThread.start() # Démarrage du Thread. 

lst_files = load_files_secure()

while SERVER_SWITCH:
    server.listen(1)
    
    # Gestion du socket receiver_client. Uniquement besoin de l'ajouter dans la liste des clients connectés. 
    clientSocketReceive, clientAddress = server.accept() # Instruction bloquante. Passage à la ligne suivante quand un client se connecte.    
     
    # Gestion du socket sender_client. Uniquement besoin de créer un Thread.
    clientSocketSender, clientAddress = server.accept() # Instruction bloquante. Passage à la ligne suivante quand un client se connecte.    
    
    # Instanciation du client.
    new_client = Client(clientAddress, clientSocketSender, clientSocketReceive, CONNECTED_CLIENTS)
    #connected_clients.append(new_client) # Ajout à la liste des clients connectés.
    
    # Instanciation du Thread.         
    newThread = ClientThread(new_client) # Création du Thread pour ce nouveau client. 
    newThread.start() # Démarrage du Thread. 
          
    CONNECTED_CLIENTS = CONNECTED_CLIENTS + 1