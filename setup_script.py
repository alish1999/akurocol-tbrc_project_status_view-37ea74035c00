from tbrc_project_status_view.domain_classes import *
from tbrc_project_status_view import app, session, labels, current_user, env, check, string, random
from tbrc_project_status_view import akuro_runtime


def setup():
    
    old_config = session.query(SystemConfig).first()
    if old_config is None:
        session.add(SystemConfig())
    
    
    #estados
    
    
    #crear el administrador
    admin = session.query(User).filter(User.username=="AkuroMaster").first()
    if admin is None:
        pass_ = u"EarthEather852!_!"
        print("Modo contraseña:")
        print("1: Contraseña default")
        print("2: Generar aleatoriamente")

        mode = input("Selecionar Modo: ")
        if mode == "2":
            letters = string.ascii_lowercase + string.ascii_uppercase + string.digits + string.punctuation
            temp = random.sample(letters,12)
            pass_ = "".join(temp)
            print(f"Nueva contraseña \"{pass_}\"")
        admin = User(username="AkuroMaster",password=akuro_runtime.unicode_password_hash(pass_))
        session.add(admin)
    #crear el rol del asminisrador
    role = session.query(Role).filter(Role.name=="Akuro Administrator").first()
    if role is None:
        role = Role(name="Akuro Administrator")
        session.add(role)
    #agregar rol al administrador
    if admin not in role.user_set:
        role.user_set.append(admin)
    #crear el anon
    anon = session.query(User).filter(User.username=="").first()
    if anon is None:
        anon = User(username="",password=akuro_runtime.unicode_password_hash(u""))
        session.add(anon)

    #crear el rol de anon
    role_anon = session.query(Role).filter(Role.name=="Anon User").first()
    if role_anon is None:
        role_anon = Role(name="Anon User")
        session.add(role_anon)

    #agregar el rol al susuario anon
    if anon not in role_anon.user_set:
        role_anon.user_set.append(anon)

    #todos los roles
    session.commit()
    all_roles = session.query(Role).all()

    print("Modo:")
    print("1: todo al admin")
    print("2: determinar interactivamente")

    mode = input("Selecionar Modo: ")
    roles_to_add = []
    if mode == "1":
        print("seleccione el rol del administrador")
        for i in range(len(all_roles)):
            print (i, "-", all_roles[i].name)
        role_index = input("Selecionar Rol: ")
        role_index = int(role_index)
        roles_to_add.append(all_roles[role_index])
        
    elif mode == "2":
        pass
    else:
        return 0
        exit()

    #agregar urls nuevas
    for rule in app.url_map.iter_rules():
        old_permission = session.query(Permission).filter(Permission.url == rule.rule).first()
        if old_permission is None:
            print ("Nueva Regla!", rule.rule)
            permission = Permission(url=rule.rule)
            if mode == "2":
                print("seleccione los roles para agregar separados por punto")
                for i in range(len(all_roles)):
                    print (i, "-", all_roles[i].name)
                role_index = input("Selecionar Roles: ")
                if role_index not in  [""," ",None]:
                    role_index = role_index.split(".")
                    roles_to_add = []
                    for ind in role_index:
                        roles_to_add.append(all_roles[int(ind)])
            for role_to_add in roles_to_add:
                role_to_add.permissions_of_role.append(permission)
            session.add(permission)

    session.commit()
    return "Success"
    return "Already DEployed"
    

setup()