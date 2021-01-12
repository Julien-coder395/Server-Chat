# -*- coding: utf-8 -*-
"""
Created on Sat Dec  5 10:39:47 2020

@author: Julien
"""

import sqlite3
from sqlite3 import Error

# Création de la connexion à la base de données.
def initialisation():     
    db_file = r"./server_chat_database.db"
    try:
        conn = sqlite3.connect(db_file)
        print("Initialisation avec la BDD réussie.\nVersion de SQLite : ", sqlite3.version)      
    except Error as e:
        print("exception from dao", e)
        conn.close()
    return conn


def authentication(conn, username, password):
    status_message = ''
    authentication_result = False
    curseur = conn.cursor()
    curseur.execute("SELECT * FROM users WHERE username=? ;", (username,))
    resultats = curseur.fetchall()
    if resultats:
        if password == resultats[0][2]:
            status_message = "Authentification réussie"
            authentication_result = True
        else:
            status_message = "Authentification échouée"
    else:
        status_message = "Utilisateur non existant"
    return (authentication_result, status_message)


def add_user(conn, username, password):
    result = ""
    try:
        conn.execute("INSERT INTO users (username, password) VALUES(?, ?)", (username, password,))
        conn.commit()
        result = "Utilisateur ajouté"
    except Error as e:
        print("exception from dao", e)
        result = e
    return result


def check_if_user_exist(conn, username):
    result = False
    curseur = conn.cursor()
    try:
        curseur.execute("SELECT * FROM users WHERE username=? ;", (username,))
        resultats = curseur.fetchall()
        if resultats:
            result = True
    except Error as e:
        result = False
        print("exception from dao", e)
    return result
    
    
def close(conn):
    try:
        conn.close()
    except Error as e:
        print("exception from dao", e)