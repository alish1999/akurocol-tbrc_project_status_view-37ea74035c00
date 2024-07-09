# -*- coding: utf-8 -*-
from flask import Flask, session,redirect, request, flash, get_flashed_messages, make_response
from flask_login import LoginManager, current_user, login_user, logout_user
from jinja2 import Environment, PackageLoader
from sqlalchemy import create_engine, event, distinct as alchemy_distinct
from sqlalchemy.exc import StatementError,InvalidRequestError
from sqlalchemy.orm import sessionmaker, aliased, scoped_session
from functools import wraps
from datetime import timedelta
import requests, json, uuid, urllib, re, os, subprocess, boto3, bcrypt, math, random
import smtplib, datetime, schedule, time, openpyxl, logging, base64, traceback
logging.basicConfig(filename='tbrc_project_status_view_log.log',level=logging.DEBUG)
from . import akuro_runtime 

from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
from threading import Thread

import hashlib

def my_finalize(thing):
    return thing if thing is not None else ''
#el enviroment de jinja, note que los tokens de inicio y fin de flujo de control estan alterados
env = Environment(
    loader=PackageLoader(__name__, 'templates'),
    finalize=my_finalize
    )

labels = json.load(open('tbrc_project_status_view/labels.json', encoding ="utf-8"))
env.globals['labels'] = labels


copyright = json.load(open('tbrc_project_status_view/copyright.json', encoding ="utf-8"))
env.globals['copyright'] = copyright







### prueba de py3
env.globals['user'] = current_user

env.globals["flash_messages"] = get_flashed_messages
env.globals['current_user'] = current_user
env.globals["datetime"] = datetime


env.filters['cltx'] = akuro_runtime.cltx
env.filters['cltx2'] = akuro_runtime.clear_name_for_latex
env.filters['money'] = akuro_runtime.moneyprint
env.filters['shuffle'] = akuro_runtime.filter_shuffle
moneyprint = akuro_runtime.moneyprint
env.filters['dwImage'] = akuro_runtime.downloadimage
env.filters['number_to_literal'] = akuro_runtime.numero_a_moneda
env.filters['number_name'] = akuro_runtime.numero_a_letras
env.filters['get_month_literal'] = akuro_runtime.get_month_literal
env.filters['parse_json_string'] = akuro_runtime.parse_json_string
env.filters["format2"] = akuro_runtime.filter_format_attempt
env.filters["string_to_url_fragment"] = akuro_runtime.string_to_url_fragment
env.filters["safe_none"] = akuro_runtime.safe_none
env.filters["safe_date_format"] = akuro_runtime.safe_date_format
env.filters["group_and_sort"] = akuro_runtime.group_and_sort


app = Flask(__name__, static_url_path='/static',static_folder="../static") 

app.config['SESSION_TYPE'] = 'memcached'
app.config['SYSTEM_NAME'] = 'tbrc_project_status_view'
app.config['SECRET_KEY'] = '1349712tbrc_project_status_view3guedfjso'
app.config["SESSION_REFRESH_EACH_REQUEST"] = True

try:
    import credentials
except:
    pass

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = '/login'


engine = create_engine('sqlite:///tbrc_project_status_view.db', pool_recycle=200)


DBSession = sessionmaker(bind=engine)
session = scoped_session(DBSession)

app.permanent_session_lifetime = timedelta(minutes=30)



class WebServiceClient():
    def __init__(self,data):
        self.data = json.load(data)
        url = self.data["server_url"].split("://")
        self.protocol = url[0]
        self.domain = url[1]
        self.full_url = self.data["server_url"]
        
        for s in self.data["services"]:
            setattr(self,s,self.full_url+self.data["services"][s].replace("<","{").replace(">","}"))

    def imagepath(self,url):
        return self.full_url+"/"+url


emailconfig = json.load(open('tbrc_project_status_view/emailconfig.json')) 

def send_one_email(toaddrs, subject, content, fromaddr = None, attachements = None):
    import smtplib
    if fromaddr is None:
        fromaddr = emailconfig["from"]
    if attachements is None:
        attachements = []
        
    #Change according to your settings
    smtp_server = emailconfig["server"]
    smtp_username = emailconfig["user"]
    smtp_password = emailconfig["password"]
    smtp_port = emailconfig["port"]
    smtp_do_tls = True
    
    server = smtplib.SMTP(
        host = smtp_server,
        port = smtp_port,
        timeout = 10
    )
    server.set_debuglevel(10)
    server.starttls()
    server.ehlo()
    server.login(smtp_username, smtp_password)
    addresses = []
    for a in toaddrs:
        if a not in [None,"None",""," "]:
            parts = re.split(",|;",a)
            for p in parts:
                addresses.append(p.strip())
    for a in addresses:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = fromaddr
        msg['To'] = a
        for f in attachements:
            if isinstance(f, str):
                f_s = f
                if f[0] == "/":
                    f_s = f[1:]
                with open(f_s, "rb") as fil:
                    part = MIMEApplication(
                        fil.read(),
                        Name=os.path.basename(f)
                    )
            # After the file is closed
            part['Content-Disposition'] = 'attachment; filename="%s"' % os.path.basename(f)
            msg.attach(part)
        part2 = MIMEText(content.encode("utf-8"),'html', _charset="UTF-8")
        msg.attach(part2)
        server.sendmail(fromaddr, a, msg.as_string())
    print(server.quit())

services_conf={}


app.config['Webservices'] = services_conf
env.globals['Webservices'] = services_conf






system_config = None

def get_system_var(varname):
    try:
        return getattr(system_config, varname)
    except:
        return None


env.globals["system_config"] = get_system_var

def reload_config():
    global system_config
    try:
        system_config = session.query(SystemConfig).first()
        session.expunge(system_config)
    except:
        system_config = None



from .domain_classes import * 



reload_config()

env.filters['akuro_to_json'] = akuro_to_json
env.filters['categorize'] = akuro_runtime.categorize

@login_manager.user_loader
def load_user(user_id):
    session.rollback()
    user = session.query(User).filter(
        User.id==user_id
        ).first()
    return user
    

from functools import wraps
def check(url):
    def decor(f):
        @wraps(f)
        def decorated_view(*args, **kwargs):
            if not current_user.is_anonymous:
                if current_user.hasPermision(url):
                    return f(*args, **kwargs)
                else:
                    return "No esta autorizado para realizar esta acción"
            else:
                anon = session.query(Role).filter(Role.name=="Anon User").first()
                if anon is not None:
                    for p in anon.permissions_of_role:
                        if p.url == url:
                            return f(*args, **kwargs)
                return redirect("/login")
        return decorated_view
    return decor

def check_api_key(url):
    def decor(f):
        @wraps(f)
        def decorated_view(*args, **kwargs):
            return f(*args, **kwargs)
        return decorated_view
    return decor

@app.errorhandler(StatementError)
def errh(error):
    session.rollback()
    return str(error)
    






@app.route("/page/platformAdminPane")
@check('/page/platformAdminPane')
def page_platform_admin_pane():
    template = env.get_template('pages/platform_admin_pane.html') 
    return template.render() 

@app.route("/page/imageUploads", methods=["GET","POST"])
@check('/page/imageUploads')
def upload_image_uploads():
    if request.method == 'POST':
        result = [] 
        for file in request.files:
            file_to_upload = request.files[file]
            if file_to_upload!="":
                mime_type = file_to_upload.content_type
                tempname = str(uuid.uuid4()) + os.path.splitext(file_to_upload.filename)[1]
                file_to_upload.save("static/uploads/"+tempname)
                # get file size after saving
                size = os.path.getsize("static/uploads/"+tempname)
                # return json for js call back
                result.append({"name":tempname,"type": mime_type,"size": size,"url": "/static/uploads/"+tempname,"thumbnailUrl": "/static/uploads/"+tempname,"deleteUrl": "", "deleteType": "DELETE"})
            
        return json.dumps({"files": result})
    else:
        template = env.get_template('pages/image_uploads.html') 
        return template.render() 

@app.route("/page/bulkUploads", methods=["GET","POST"])
@check('/page/bulkUploads')
def upload_bulk_uploads():
    if request.method == 'POST':
        names = []
        for f in request.files.getlist('file'):
            if f.filename != "":
                tempname = str(uuid.uuid4()) + os.path.splitext(f.filename)[1]
                f.save(os.path.join("static/uploads/", tempname))
                names.append("/static/uploads/"+tempname)
        return json.dumps(names)

@app.route("/page/freddyWelcome")
@check('/page/freddyWelcome')
def page_freddy_welcome():
    template = env.get_template('pages/freddy_welcome.html') 
    return template.render() 

from flask_login import login_user, logout_user
@app.route("/login", methods=['GET','POST'])
def page_rbacLoginPage():
    error=False
    if request.method=='POST': 
        user = session.query(User).filter(User.username==request.form['username']).first()
        if user:
            if akuro_runtime.akuro_check_user(user.username, user.password, request.form["password"]):
                login_user(user)
                return redirect('/page/platformAdminPane')
            else:
                error=True
        else:
            error=True
    template = env.get_template('pages/rbac_login_page.html') 
    return template.render(error=error) 

from flask_login import logout_user
@app.route("/logout")
def logout():
    logout_user()
    return redirect("/login")


initdb(engine)






from . import final_user_views


system_name = "tbrc_project_status_view"





#Desarrollo realizado por akuro SAS. Contactenos en http://akuro.co
#Development made by akuro. contact Us at http://akuro.co
#  __    __    _______   ______    __    __     ______          _______    ______     _______                               
# /" |  | "\  /"     "| /" _  "\  /" |  | "\   /    " \        |   __ "\  /    " \   /"      \                              
#(:  (__)  :)(: ______)(: ( \___)(:  (__)  :) // ____  \       (. |__) :)// ____  \ |:        |                             
# \/      \/  \/    |   \/ \      \/      \/ /  /    ) :)      |:  ____//  /    ) :)|_____/   )                             
# //  __  \\  // ___)_  //  \ _   //  __  \\(: (____/ //       (|  /   (: (____/ //  //      /                              
#(:  (  )  :)(:      "|(:   _) \ (:  (  )  :)\        /       /|__/ \   \        /  |:  __   \                              
# \__|  |__/  \_______) \_______) \__|  |__/  \"_____/       (_______)   \"_____/   |__|  \___)                             
#                                                                                                                           
#      __       __   ___  ____  ____   _______     ______                                                                   
#     /""\     |/"| /  ")("  _||_ " | /"      \   /    " \                                                                  
#    /    \    (: |/   / |   (  ) : ||:        | // ____  \                                                                 
#   /' /\  \   |    __/  (:  |  | . )|_____/   )/  /    ) :)                                                                
#  //  __'  \  (// _  \   \\ \__/ //  //      /(: (____/ //                                                                 
# /   /  \\  \ |: | \  \  /\\ __ //\ |:  __   \ \        /                                                                  
#(___/    \___)(__|  \__)(__________)|__|  \___) \"_____/                                                                   
#                                                                                                                           
#  ______    ______    _____  ___  ___________   __       ______  ___________  _______  _____  ___      ______    ________  
# /" _  "\  /    " \  (\"   \|"  \("     _   ") /""\     /" _  "\("     _   ")/"     "|(\"   \|"  \    /    " \  /"       ) 
#(: ( \___)// ____  \ |.\\   \    |)__/  \\__/ /    \   (: ( \___))__/  \\__/(: ______)|.\\   \    |  // ____  \(:   \___/  
# \/ \    /  /    ) :)|: \.   \\  |   \\_ /   /' /\  \   \/ \        \\_ /    \/    |  |: \.   \\  | /  /    ) :)\___  \    
# //  \ _(: (____/ // |.  \    \. |   |.  |  //  __'  \  //  \ _     |.  |    // ___)_ |.  \    \. |(: (____/ //  __/  \\   
#(:   _) \\        /  |    \    \ |   \:  | /   /  \\  \(:   _) \    \:  |   (:      "||    \    \ | \        /  /" \   :)  
# \_______)\"_____/    \___|\____\)    \__|(___/    \___)\_______)    \__|    \_______) \___|\____\)  \"_____/  (_______/   
#                                                                                                                           
#  ______    ______    _____  ___  ___________   __       ______  ___________      ____  ____   ________                    
# /" _  "\  /    " \  (\"   \|"  \("     _   ") /""\     /" _  "\("     _   ")    ("  _||_ " | /"       )                   
#(: ( \___)// ____  \ |.\\   \    |)__/  \\__/ /    \   (: ( \___))__/  \\__/     |   (  ) : |(:   \___/                    
# \/ \    /  /    ) :)|: \.   \\  |   \\_ /   /' /\  \   \/ \        \\_ /        (:  |  | . ) \___  \                      
# //  \ _(: (____/ // |.  \    \. |   |.  |  //  __'  \  //  \ _     |.  |         \\ \__/ //   __/  \\                     
#(:   _) \\        /  |    \    \ |   \:  | /   /  \\  \(:   _) \    \:  |         /\\ __ //\  /" \   :)                    
# \_______)\"_____/    \___|\____\)    \__|(___/    \___)\_______)    \__|        (__________)(_______/                     
#                                                                                                                           
#      __       __   ___  ____  ____   _______     ______          ______    ______                                         
#     /""\     |/"| /  ")("  _||_ " | /"      \   /    " \        /" _  "\  /    " \                                        
#    /    \    (: |/   / |   (  ) : ||:        | // ____  \      (: ( \___)// ____  \                                       
#   /' /\  \   |    __/  (:  |  | . )|_____/   )/  /    ) :)      \/ \    /  /    ) :)                                      
#  //  __'  \  (// _  \   \\ \__/ //  //      /(: (____/ //_____  //  \ _(: (____/ //                                       
# /   /  \\  \ |: | \  \  /\\ __ //\ |:  __   \ \        /))_  ")(:   _) \\        /                                        
#(___/    \___)(__|  \__)(__________)|__|  \___) \"_____/(_____(  \_______)\"_____/                                         
#        