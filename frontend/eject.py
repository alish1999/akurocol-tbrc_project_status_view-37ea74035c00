import shutil
import glob


shutil.copytree('templates', '../tbrc_project_status_view/templates/final_user_views', dirs_exist_ok=True)
templates_list = glob.glob("../tbrc_project_status_view/templates/final_user_views/*")

def replace_static_for_frontend(path):
    filedata = ""
    with open(path, 'r', encoding="utf-8") as file :
        filedata = file.read()

    filedata = filedata.replace("/static/frontend/","/static/")
    filedata = filedata.replace("/static/","/static/frontend/")

    with open(path, 'w', encoding="utf-8") as file :
        file.write(filedata)

##mover los templates
for template in templates_list:
    replace_static_for_frontend(template)

#mover los estaticos
shutil.copytree('static', '../static/frontend', dirs_exist_ok=True)

#mover el runserver
shutil.copyfile('final_user_views.py', '../tbrc_project_status_view/final_user_views.py')
