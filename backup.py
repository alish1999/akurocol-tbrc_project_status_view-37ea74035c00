# -*- coding: utf-8 -*-

import schedule, time, datetime, os, hashlib, json, requests, subprocess, codecs
from google.cloud import storage
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base, DeclarativeMeta
from sqlalchemy import *
from pathlib import PureWindowsPath

def convert(path):
    return PureWindowsPath(os.path.normpath(PureWindowsPath(path).as_posix())).as_posix()


engine = create_engine('sqlite:///backup_control.db', pool_recycle=200)

DBSession = sessionmaker(bind=engine)
session = scoped_session(DBSession)
Base = declarative_base()

class Checksum(Base):
    __tablename__ = 'checksum'
    name = Column(String(800), primary_key=True)
    remote_name = Column(String(800), primary_key=True)
    #basic types of fields
    hash = Column(String(800))
    uploaded = Column(Boolean())
    last_upload = Column(DateTime())


Base.metadata.bind = engine
Base.metadata.create_all(engine)
session.commit()


def process_single_file(full_path, remote_name, force_upload):
    try:                
        with open(full_path, 'rb') as f:
            hasher = str(hashlib.md5(f.read()).hexdigest())
            # save in checksums_current_table         
            old = session.query(Checksum).filter(Checksum.name == full_path).first()
            if old is None:
                new_ = Checksum(name = full_path, remote_name = remote_name, hash = hasher, uploaded = False, last_upload = None)
                session.add(new_)
            else:
                if old.hash != hasher or force_upload:
                    old.uploaded = False
    except Exception as e:
        print(f'ERROR: Could not open {full_path}: {e}')                                    
    
def process_batch(batch):
    try:
        # loop each file in the batch
        for file_path in batch:                
            process_single_file(convert(file_path), convert(file_path), True)
        session.commit()
    except:
        print(f'ERROR: Could not save {file_path}')    

def load_list_of_files(directory, batch_size=500):    
    # process in batches to avoid running out of memory
    with os.scandir(directory) as entries:        
        batch = []        
        for entry in entries:            
            if entry.is_file():                
                batch.append(convert(entry.path))
                if len(batch) >= batch_size:
                    process_batch(batch)
                    batch = []
            elif entry.is_dir():
                load_list_of_files(convert(entry.path))
        if batch:
            process_batch(batch)

def job():
    # Instantiates a client
    storage_client = storage.Client.from_service_account_json('backup_config.json')
    
    fork = ""

    try:
        from shard import copy_name
        fork = copy_name
    except:
        pass

    service_name = 'tbrc_project_status_view' # Modify this when autogenerating
    bucket = None

    try:
        bucket = storage_client.get_bucket(service_name+fork)
    except:
    # Creates the new bucket
        bucket = storage_client.create_bucket(service_name+fork)
        print('Bucket ' + bucket.name + ' created.')
    
    
    # Uploads LOG
    log_filename = service_name + '_log.log'
    log_new_name = "backup_"+service_name+"_log_"+datetime.date.today().strftime("%Y-%m-%d")+".log"
    process_single_file(log_filename, log_new_name, True)
    
    # Uploads the db
    db_filename = service_name + '.db'
    db_new_name = "backup_"+service_name+"_"+datetime.date.today().strftime("%Y-%m-%d")+".db"
    process_single_file(db_filename, db_new_name, True)

    
    # Uploads files from the uploads folder
    directory = convert('./static/uploads')        

    # SQLite Process
    try:     
        # load the list of files from directory        
        load_list_of_files(directory)        
        # get the list of files from the database in batches of 1000
        for row in session.query(Checksum).filter(Checksum.uploaded == False).yield_per(1000):
            full_path = row.name
            hash = row.hash
            filename = full_path[len(directory):]
            # check if the file is already in the bucket
            try:
                # upload file
                new_name = row.remote_name
                blob = bucket.blob(new_name)
                blob.upload_from_filename(full_path)
                row.uploaded = True
                row.last_upload = datetime.datetime.now()
                print('File ' + filename + ' uploaded to ' + new_name)
            except Exception as e:
                print(f"File {filename} cant be uploaded : {e}")
               
        session.commit()
        session.close()
    except Exception as e:
        print(f'ERROR: Could not connect to the database.')
    
    try:
        # Post updates to Akuro service
        payload = {
            'service': service_name+fork,
            'db_url': 'https://storage.googleapis.com/'+service_name+fork+'/'+db_new_name+'.db' if db_new_name is not None else "",
            'log_url': 'https://storage.googleapis.com/'+service_name+fork+'/'+log_new_name+'_log.log' if log_new_name is not None else ""
        }
        response = requests.post('https://mailservice.akuro.co/post_backup_update', json = payload)
    except:
        pass

schedule.every().day.at("05:50").do(job)


if __name__ == '__main__':    
    while True:
        schedule.run_pending()
        time.sleep(1)