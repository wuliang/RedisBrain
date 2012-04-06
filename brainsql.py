# -*- coding: utf8 -*-
import os
import sqlite3

   
class BrainSql:

    def __init__(self, filename):
        if not os.path.exists(filename):
            self.init(filename)

        self.conn = sqlite3.connect(filename)
        self.conn.row_factory = sqlite3.Row
        self.conn.text_factory = str

        
    def commit(self):
        ret = self.conn.commit()
        return ret
        
    def close(self):
        
        self.conn.cursor().close()
        self.conn.close()


    def insert_chinese_frequency(self,  ch,  freq):        
        c = self.conn.cursor()        
        q = "INSERT INTO CharacterFrequency (ChineseCharacter, Score) VALUES (?, ?)"
        c.execute(q, (ch,  freq))                
        return        

    def fetch_chinese_frequency(self, ch):

        c = self.conn.cursor()
        q = "SELECT * FROM CharacterFrequency WHERE ChineseCharacter = ?"
        rows = c.execute(q, (ch, )).fetchall()
        return rows
        
   
    def init(self, filename):
        self.conn = sqlite3.connect(filename)
        c = self.conn.cursor()    
        c.execute("""
    CREATE TABLE CharacterFrequency (
  ChineseCharacter VARCHAR(1) NOT NULL,    
  Score INTEGER NOT NULL DEFAULT 0, 
  PRIMARY KEY (ChineseCharacter)) """)
  
        self.commit()
        self.close()
