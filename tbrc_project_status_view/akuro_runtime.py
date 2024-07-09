# -*- coding: utf-8 -*-
import urllib, os, json, datetime, hashlib, random, re, bcrypt, string 
from sqlalchemy.types import TypeDecorator, TEXT, VARCHAR
from wtforms import StringField, Field
from wtforms.widgets import PasswordInput, TextInput, CheckboxInput
from wtforms_sqlalchemy.fields import QuerySelectField, QuerySelectMultipleField
from werkzeug.datastructures import MultiDict
from urllib.request import urlretrieve
from collections import OrderedDict



def filter_format_attempt(value, *args, **kwargs):
    try:
        return value % (kwargs or args)
    except:
        return value
    
def filter_shuffle(seq):
    try:
        random.shuffle(seq)
        return seq
    except:
        return seq

def cltx(s):
    if s is None:
        return ""
    else:
        return s.replace("\\","\\\\").replace("#","\#").replace("$","\$").replace("%","\%").replace("_","\_").replace("&","\&")

def categorize(products, categories):
    results = []

    categories = sorted(categories, key=lambda x : x.category_name)
    for i in range(len(categories)):
        category = categories[i]
        results.append([category, []])
        for product in products:
            if category in product.category_products:
                results[i][1].append(product)

    return results
    
def unicode_password_hash(original):
    return bcrypt.hashpw(original.encode("utf-8"), bcrypt.gensalt())


def akuro_check_user(user, hash_, password_raw):
    try:
        hash_bytes = hash_
        if not isinstance(hash_bytes, bytes):
            hash_bytes = hash_.encode("utf-8")
        md5_hash = hashlib.md5(password_raw.encode("utf-8")).hexdigest()
        if hash_ == md5_hash:
            return True
        if bcrypt.checkpw(password_raw.encode("utf-8"), hash_bytes):
            return True
    except:
        return False
    return False
        

def moneyprint(money, simbol=False, decimals = True):
    try:
        if money is None:  
            money=0
        money = float(money)
        neg = money<0
        money = '%.2f' % money
        if neg:
            money = money[1:]
        parts = money.split(".")
        a=[]
        s = parts[0]
        for i in range(0,len(s)):
            if i%3==0:
                a.insert(0,s[max(len(s)-i-3,0):len(s)-i])
        ret = "$"+".".join(a) if simbol else ".".join(a)
        if not decimals:
            ret = ret
        else:
            ret = ret + "," + parts[1]
        if neg:
            ret = "-" + ret
        return ret
    except:
        return "0"

def date_tryparse(date, default=None):
    try:
        return datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
    except:
        if default is not None:
            return default
        else:
            return None

def downloadimage(image, path="temp/"):
    if image.startswith("/"):
        return image[1:]
    if image in [None,"None",""," "]:
        return ""
    filename = image.split("/")[-1]
    path = path+filename
    if not os.path.isfile(path):
        urlretrieve(image, path)
    return path
    


__author__ = 'efrenfuentes'


MONEDA_SINGULAR = 'peso'
MONEDA_PLURAL = 'pesos'

CENTIMOS_SINGULAR = 'centavo'
CENTIMOS_PLURAL = 'centavos'

MAX_NUMERO = 999999999999

UNIDADES = (
    'cero',
    'uno',
    'dos',
    'tres',
    'cuatro',
    'cinco',
    'seis',
    'siete',
    'ocho',
    'nueve'
)

DECENAS = (
    'diez',
    'once',
    'doce',
    'trece',
    'catorce',
    'quince',
    'dieciseis',
    'diecisiete',
    'dieciocho',
    'diecinueve'
)

DIEZ_DIEZ = (
    'cero',
    'diez',
    'veinte',
    'treinta',
    'cuarenta',
    'cincuenta',
    'sesenta',
    'setenta',
    'ochenta',
    'noventa'
)

CIENTOS = (
    '_',
    'ciento',
    'doscientos',
    'trescientos',
    'cuatroscientos',
    'quinientos',
    'seiscientos',
    'setecientos',
    'ochocientos',
    'novecientos'
)

def numero_a_letras(numero):
    numero_entero = int(numero)
    if numero_entero > MAX_NUMERO:
        raise OverflowError('Número demasiado alto')
    if numero_entero < 0:
        return 'menos %s' % numero_a_letras(abs(numero))
    letras_decimal = ''
    parte_decimal = int(round((abs(numero) - abs(numero_entero)) * 100))
    if parte_decimal > 9:
        letras_decimal = 'punto %s' % numero_a_letras(parte_decimal)
    elif parte_decimal > 0:
        letras_decimal = 'punto cero %s' % numero_a_letras(parte_decimal)
    if (numero_entero <= 99):
        resultado = leer_decenas(numero_entero)
    elif (numero_entero <= 999):
        resultado = leer_centenas(numero_entero)
    elif (numero_entero <= 999999):
        resultado = leer_miles(numero_entero)
    elif (numero_entero <= 999999999):
        resultado = leer_millones(numero_entero)
    else:
        resultado = leer_millardos(numero_entero)
    resultado = resultado.replace('uno mil', 'un mil')
    resultado = resultado.replace('ciento mil', 'cien mil')
    resultado = resultado.strip()
    resultado = resultado.replace(' _ ', ' ')
    resultado = resultado.replace('  ', ' ')
    if parte_decimal > 0:
        resultado = '%s %s' % (resultado, letras_decimal)
    return resultado

def numero_a_moneda(numero):
    if numero is None:
        numero = 0.0
    numero_entero = int(numero)
    parte_decimal = int(round((abs(numero) - abs(numero_entero)) * 100))
    centimos = ''
    if parte_decimal == 1:
        centimos = CENTIMOS_SINGULAR
    else:
        centimos = CENTIMOS_PLURAL
    moneda = ''
    if numero_entero == 1:
        moneda = MONEDA_SINGULAR
    else:
        moneda = MONEDA_PLURAL
    letras = numero_a_letras(numero_entero)
    letras = letras.replace('uno', 'un')
    letras_decimal = 'con %s %s' % (numero_a_letras(parte_decimal).replace('uno', 'un'), centimos)
    letras = '%s %s %s' % (letras, moneda, letras_decimal)
    return letras

def leer_decenas(numero):
    if numero < 10:
        return UNIDADES[numero]
    decena, unidad = divmod(numero, 10)
    if numero <= 19:
        resultado = DECENAS[unidad]
    elif numero <= 29:
        resultado = 'veinti%s' % UNIDADES[unidad]
    else:
        resultado = DIEZ_DIEZ[decena]
        if unidad > 0:
            resultado = '%s y %s' % (resultado, UNIDADES[unidad])
    return resultado

def leer_centenas(numero):
    centena, decena = divmod(numero, 100)
    if numero == 0:
        resultado = 'cien'
    else:
        resultado = CIENTOS[centena]
        if decena > 0:
            resultado = '%s %s' % (resultado, leer_decenas(decena))
    return resultado

def leer_miles(numero):
    millar, centena = divmod(numero, 1000)
    resultado = ''
    if (millar == 1):
        resultado = ''
    if (millar >= 2) and (millar <= 9):
        resultado = UNIDADES[millar]
    elif (millar >= 10) and (millar <= 99):
        resultado = leer_decenas(millar)
    elif (millar >= 100) and (millar <= 999):
        resultado = leer_centenas(millar)
    resultado = '%s mil' % resultado
    if centena > 0:
        resultado = '%s %s' % (resultado, leer_centenas(centena))
    return resultado

def leer_millones(numero):
    millon, millar = divmod(numero, 1000000)
    resultado = ''
    if (millon == 1):
        resultado = ' un millon '
    if (millon >= 2) and (millon <= 9):
        resultado = UNIDADES[millon]
    elif (millon >= 10) and (millon <= 99):
        resultado = leer_decenas(millon)
    elif (millon >= 100) and (millon <= 999):
        resultado = leer_centenas(millon)
    if millon > 1:
        resultado = '%s millones' % resultado
    if (millar > 0) and (millar <= 999):
        resultado = '%s %s' % (resultado, leer_centenas(millar))
    elif (millar >= 1000) and (millar <= 999999):
        resultado = '%s %s' % (resultado, leer_miles(millar))
    return resultado

def leer_millardos(numero):
    millardo, millon = divmod(numero, 1000000)
    return '%s millones %s' % (leer_miles(millardo), leer_millones(millon))


def parse_json_string(s, default = None):
    try:
        return json.loads(s)
    except:
        return default
    
    

class PasswordField(StringField):
    """
    Reescribe password field
    """
    widget = PasswordInput(hide_value=False)
    def _value(self):
        return u''

    def process_formdata(self, valuelist):
        if valuelist:
            if len(valuelist[0])<40:
                self.data = unicode_password_hash(valuelist[0])
            else:
                self.data = valuelist[0]
        else:
            self.data = "NONE"
            
class CommaSeparatedField(StringField):
    """
    Reescribe password field
    """
    widget = TextInput()
    
    def _value(self):
        return self.data

    def process_formdata(self, valuelist):
        if valuelist:
            self.data = ",".join(valuelist)
        else:
            self.data = ""
    

class FreezeMe(TypeDecorator):
    
    impl = TEXT

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = akuro_to_json(value,"__freeze__")
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            try:
                value = json.loads(value)
            except:
                value = ""
        return value
        
class TextToJSON(TypeDecorator):
    
    impl = TEXT

    def process_bind_param(self, value, dialect):
        if isinstance(value, str):
            return value
        else:
            try:
                return json.dumps(value)
            except:
                return ""
        return ""

    def process_result_value(self, value, dialect):
        if value is not None:
            try:
                value = json.loads(value)
            except:
                value = ""
        return value
        
class RandomString(TypeDecorator):
    impl = VARCHAR

    def process_bind_param(self, value, dialect):
        if value in ["",None," ","None"]:
            return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
        else:
            return value

    def process_result_value(self, value, dialect):
        return value
        

class TextToCOLS(TypeDecorator):
    
    impl = TEXT

    def process_bind_param(self, value, dialect):
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            try:
                val = []
                for row in value.split("\n"):
                    trw = row.replace("\\,","XXXXXXX")
                    cols = []
                    for col in trw.split(","):
                        cols.append(col.replace("XXXXXXX",",").strip())
                    val.append(cols)
                value = val
            except:
                value = []
        return value
        
class HourColumn(TypeDecorator):
    impl = VARCHAR

    def process_bind_param(self, value, dialect):
        temp = datetime.time(hour = 0, minute = 0)
        if isinstance(value, datetime.time):
            temp = value
        elif value not in  ["", " ",None,"None"]:
            temp =  datetime.datetime.strptime(value,"%H:%M:%S").time()
        return temp.strftime("%H:%M")

    def process_result_value(self, value, dialect):
        if value not in  ["", " ",None,"None"]:
            return datetime.datetime.strptime(value,"%H:%M").time()
        return datetime.time(hour = 0, minute = 0)

class HourField(StringField):
    """
    Reescribe text field
    """
    widget = TextInput()
    
    def _value(self):
        return self.data

    def process_formdata(self, valuelist):
        if valuelist:
            self.data = datetime.datetime.strptime(valuelist[0],"%H:%M").time()
        else:
            self.data = datetime.time(hour = 0, minute = 0)
            

class NullableBooleanField(Field):
    
    widget = CheckboxInput()
    false_values = (False,'false', '0')
    true_values = (True,'true', '1')

    def __init__(self, label=None, validators=None, false_values=None, true_values=None, **kwargs):
        super(NullableBooleanField, self).__init__(label, validators, **kwargs)
        if false_values is not None:
            self.false_values = false_values
        if true_values is not None:
            self.true_values = true_values


    def process_data(self, value):
        self.data = bool(value)

    def process_formdata(self, valuelist):
        if valuelist:
            if valuelist[0] in self.false_values:
                self.data = False
            elif valuelist[0] in self.true_values:
                self.data = True
        else:
            self.data = None

    def _value(self):
        if self.raw_data:
            return str(self.raw_data[0])
        else:
            return 'y'
            
def valid_password(passwd):
    SpecialSym =['$', '@', '#', '%', '!' , "?", ":", ";", "_", "-", "&", "*", "(", ")", "+", "=", "-", "{", "}", "[", "]", ";", ":", ",", "."] 
    errors = []
    if passwd in ["None", None, "", " ", "  ","   "]:
        errors.append(u'Tu contraseña no puede estar vacía')
        return errors
    if len(passwd) < 6: 
        errors.append(u'Debe Contener Mas de 6 carácteres')

    if len(passwd) > 20: 
        errors.append(u'no debe exceder los 20 carácteres')

    if not any(char.isdigit() for char in passwd): 
        errors.append(u'La contraseña debe tener almenos un número')

    if not any(char.isupper() for char in passwd): 
        errors.append(u'La contraseña debe tener almenos una mayúscula') 

    if not any(char.islower() for char in passwd): 
        errors.append(u'La contraseña debe tener almenos una minúscula')

    if not any(char in SpecialSym for char in passwd): 
        errors.append(u'Debe tener almenos una instancia de alguno de estos carácteres '+",".join(SpecialSym))
    return errors
    



class LOAD_ERROR():
    WARNING = 1
    FATAL = 0
    INFO = 2


def collapseErrors(errors):
    s_to_add = "<ul>"
    for e in errors:
        if e[0]==LOAD_ERROR.WARNING:
            s_to_add = s_to_add + "<li><span class=\"text-warning\">"+str(e[1])+"</span></li>"
        elif e[0]==LOAD_ERROR.FATAL:
            s_to_add = s_to_add + "<li><span class=\"text-danger\">"+str(e[1])+"</span></li>"
        elif e[0]==LOAD_ERROR.INFO:
            s_to_add = s_to_add + "<li><span class=\"text-info\">"+str(e[1])+"</span></li>"
    return s_to_add + "</ul>"


def collapseStrings(errors):
    s_to_add = ""
    for e in errors:
        if e[0]==LOAD_ERROR.WARNING:
            s_to_add = s_to_add + "Alerta: "+str(e[1])
        elif e[0]==LOAD_ERROR.FATAL:
            s_to_add = s_to_add + "Error: "+str(e[1])
        elif e[0]==LOAD_ERROR.INFO:
            s_to_add = s_to_add + "Info: "+str(e[1])
        s_to_add = s_to_add + "|"
    return s_to_add

def approveRow(errors):
    approved = True
    for e in errors:
        if e[0]==LOAD_ERROR.FATAL:
            approved = False
    return approved


def objectDictList(obj_list, field):
    data = {}
    for obj in obj_list:
        data[str(getattr(obj, field))] = obj
    return data
    
def standarizeString(s):
    s = s.lower().strip()
    s = re.sub(r"\s+", " ", s)
    return s
    
def objectDictListStandarized(obj_list, field):
    data = {}
    for obj in obj_list:
        key = standarizeString(str(getattr(obj, field)))
        data[key] = obj
    return data
    
month_string_literals = ["Enero","Febrero","Marzo","Abril","Mayo","Junio","Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]
def get_month_literal(month):
    try:
        return month_string_literals[month-1]
    except:
        return "ERROR"

def safe_name(name):
    name_fragment = "".join([c for c in name if c.isalpha() or c.isdigit() or c==' ' or c=='-' or c=='_']).rstrip()
    return name_fragment
        
def make_qr_code(value):
    path = "static/uploads/"+safe_name(value)+".png"
    if not os.path.exists(path):
        import segno
        qr = segno.make(value, micro=False)
        qr.save(path, scale=10)
    return "/"+path
        
    
    
def string_to_url_fragment(s):
    if s is None:
        return ""
    if not isinstance(s, str):
        return ""
    letters = s
    letters = letters.replace(u"á", "a")
    letters = letters.replace(u"é", "e")
    letters = letters.replace(u"í", "i")
    letters = letters.replace(u"ó", "o")
    letters = letters.replace(u"ú", "u")
    letters = letters.replace(u"ü", "u")
    letters = letters.replace(u"ñ", "n")
    letters = letters.replace(u"Á", "a")
    letters = letters.replace(u"É", "e")
    letters = letters.replace(u"Í", "i")
    letters = letters.replace(u"Ó", "o")
    letters = letters.replace(u"Ú", "u")
    letters = letters.replace(u"Ü", "u")
    letters = letters.replace(u"Ñ", "n")
    letters = re.sub('[ _-]+', '-', letters)
    letters = re.sub('[^a-zA-Z0-9\-]+', '', letters)
    letters = re.sub('[\-]+', '-', letters)
    return letters.lower()

def safe_none(text, default = None):
    if text is None:
        if default is not None:
            default
        return ""
    else:
        return text
        
def set_schedule_day(schedule,day):
    day = int(day)
    if day == 1:
        return schedule.every().monday
    elif day == 2:
        return schedule.every().tuesday
    elif day == 3:
        return schedule.every().wednesday
    elif day == 4:
        return schedule.every().thursday
    elif day == 5:
        return schedule.every().friday
    elif day == 6:
        return schedule.every().saturday
    elif day == 7:
        return schedule.every().sunday
    else:
        return schedule.every().day
        
def json_to_multidict(elm, prefix):
    new_dict = elm.copy()
    for k,v in elm.items():
        if v == False:
            del new_dict[k]
        elif v == True:
            new_dict[k] = "1"
        elif isinstance(v, (int, float)):
            new_dict[k] = str(v)
    return MultiDict(mapping = new_dict)


def safe_date_format(date, format_):
    if date is None:
        return ""
    try:
        return date.strftime(format_)
    except:
        try:
            return str(date)
        except:
            return ""
    return ""
    
def clear_name_for_latex(s):
    try:
        if s is None:
            return ""
        return  re.sub(r'[^.a-zA-Z0-9 áéíóúÁÉÍÓÚÑñÜü]', "", s)
    except Exception as e:
        return ""
        
        


class CacheElement():
    def __init__(self, content, expiration = None):
        self.content = content
        if expiration is None:
            self.expiration = datetime.datetime.now() + datetime.timedelta(minutes = 10)
        else: 
            self.expiration = expiration

    def get_value(self):
        if self.expiration > datetime.datetime.now():
            return self.content
        return None

class LocalCache():
    def __init__(self):
        self.elements = {}

    def add_element(self, key, value, expiration = None):
        self.elements[key] = CacheElement(value, expiration)

    def get_element(self, key):
        val = self.elements.get(key)
        if val is None:
            return None
        else:
            val2 = val.get_value()
            if val2 is None:
                del self.elements[key]
                return None
            else:
                return val2
    
    def remove_element(self, key):
        self.elements.pop(key, None)

    def remove_prefix(self, prefix):
        to_remove = []
        for key in self.elements:
            if key.startswith(prefix):
                to_remove.append(key)
        for key in to_remove:
            self.elements.pop(key, None)
            
    def purge(self):
        self.elements = []

def try_date(elm):
    if isinstance(elm, datetime.date):
        return elm
    elif isinstance(elm, datetime.datetime):
        return elm.date()
    elif isinstance(elm, str):
        try:
            elm = datetime.datetime.strptime(elm, '%Y-%m-%d')
            return elm.date()
        except:
            try:
                elm = datetime.datetime.strptime(elm, '%d/%m/%Y')
                return elm.date()
            except:
                return None
    return None
    
def try_hour(elm):
    if isinstance(elm, datetime.time):
        return elm
    elif isinstance(elm, datetime.datetime):
        return elm.time()
    elif isinstance(elm, str):
        try:
            elm = datetime.datetime.strptime(elm, '%H:%M')
            return elm.time()
        except:
            try:
                elm = datetime.datetime.strptime(elm, '%H:%M')
                return elm.time()
            except:
                return None
    return None
    
def parse_date_or_now(val):
    try:
        return datetime.datetime.strptime(val, "%Y-%m-%d")
    except:
        return datetime.datetime.now()

def group_and_sort(values, keys):
    elms = OrderedDict()
    for elm in values:
        key = ",".join([str(getattr(elm, k)) for k in keys])
        if elms.get(key) is None:
            elms[key] = []
        elms[key].append(elm)
    return elms.items()
