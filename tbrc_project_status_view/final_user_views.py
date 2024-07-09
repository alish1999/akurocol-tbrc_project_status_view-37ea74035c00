# -*- coding: utf-8 -*-
from flask import Flask, redirect, request, get_flashed_messages, url_for, Response
from jinja2 import Environment, PackageLoader, FileSystemLoader
from datetime import datetime, timedelta
import json
try:
    from . import data_collections
    from . import app
except:
    print("Usando datos de testing")
    import data_collections
    app = Flask(__name__)
    app.config['SYSTEM_NAME'] = "testing"
    
env = None

if app.config['SYSTEM_NAME'] == "testing":
    env = Environment(loader=FileSystemLoader('templates'))
else:
    env = Environment(loader=PackageLoader(__name__,'templates/final_user_views'))


def no_duplicate_lines(content):
    lines = content.split("\n")
    for idx, l in enumerate(lines):
        lines[idx] = l.strip()
    new_lines = []
    for l in lines:
        if l not in new_lines:
            new_lines.append(l)
    return "\n".join(new_lines)

env.filters['no_duplicate_lines'] = no_duplicate_lines


env.globals["flash_messages"] = get_flashed_messages
env.globals["general_data_collection"] = data_collections.general_data_collection
env.globals["main_page_data_collection"] = data_collections.main_page_data_collection
env.globals["stats_page_data_collection"] = data_collections.stats_page_data_collection
env.globals["budget_page_data_collection"] = data_collections.budget_page_data_collection
env.globals["schedule_page_data_collection"] = data_collections.schedule_page_data_collection
env.globals["orfi_page_data_collection"] = data_collections.orfi_page_data_collection
env.globals["architect_page_data_collection"] = data_collections.architect_page_data_collection
env.globals["contacts_page_data_collection"] = data_collections.contacts_page_data_collection
env.globals["gallery_page_data_collection"] = data_collections.gallery_page_data_collection
env.globals["project_edit_page_data_collection"] = data_collections.project_edit_page_data_collection
env.globals["create_user_page_data_collection"] = data_collections.create_user_page_data_collection
env.globals["files_page_data_collection"] = data_collections.files_page_data_collection
env.globals["gallery_view_page_data_collection"] = data_collections.gallery_view_page_data_collection






















@app.route('/home')
def home():
    template = env.get_template('main_page.html')
    return template.render()

@app.route('/stats/<project_url>')
def stats(project_url):
    template = env.get_template('stats_page.html')
    return template.render(project_url = project_url)

@app.route('/budget/<project_url>')
def budget(project_url):
    template = env.get_template('budget_page.html')
    return template.render(project_url = project_url)

@app.route('/schedule/<project_url>')
def schedule(project_url):
    template = env.get_template('schedule_page.html')
    return template.render(project_url = project_url)

@app.route('/orfi/<project_url>')
def orfi(project_url):
    template = env.get_template('orfi_page.html')
    return template.render(project_url = project_url)

@app.route('/ajax/orfiFileUpload', methods=["POST"])
def ajax_orfi_file_upload():
    return data_collections.orfi_file_upload()

@app.route('/architect/<project_url>')
def architect(project_url):
    template = env.get_template('architect_page.html')
    return template.render(project_url = project_url)

@app.route('/contacts/<project_url>')
def contacts(project_url):
    template = env.get_template('contacts_page.html')
    return template.render(project_url = project_url)

@app.route('/gallery/<project_url>')
def gallery(project_url):
    template = env.get_template('gallery_page.html')
    return template.render(project_url = project_url)

@app.route('/edit-project/<project_url>')
def edit_project(project_url):
    template = env.get_template('project_edit_page.html')
    return template.render(project_url = project_url)

@app.route('/create-user')
def create_user():
    template = env.get_template('create_user_page.html')
    return template.render()

@app.route('/')
def start():
    template = env.get_template('presentation_template.html')
    return template.render()

@app.route('/public-login')
def public_login():
    template = env.get_template('login_template.html')
    return template.render()

@app.route('/orfi-files/<project_url>')
def orfi_files(project_url):
    template = env.get_template('files_page.html')
    return template.render(project_url = project_url)

@app.route('/contractor-files/<project_url>')
def contractor_files(project_url):
    template = env.get_template('files_page.html')
    return template.render(project_url = project_url)

@app.route('/gallery-view/<gallery_ident>')
def gallery_view(gallery_ident):
    template = env.get_template('gallery_view_page.html')
    return template.render(gallery_ident = gallery_ident)

@app.route('/pass-change')
def pass_change():
    template = env.get_template('request_password_change.html')
    return template.render()

@app.route('/set-new-pass')
def set_new_pass():
    template = env.get_template('set_new_password.html')
    return template.render()

@app.route('/sessionStart', methods=["POST"])
def session_start():
    return data_collections.session_start()

@app.route('/publicLogout')
def public_logout():
    return data_collections.public_logout()

@app.route('/saveProjectData', methods=["POST"])
def save_project_data():
    return data_collections.save_project_data()

@app.route('/saveUser', methods=["POST"])
def save_user():
    return data_collections.save_user()

@app.route('/saveBudgetContactData', methods=["POST"])
def save_budget_contact_data():
    return data_collections.save_budget_contact_data()

@app.route('/saveBudgetMoneyData', methods=["POST"])
def save_budget_money_data():
    return data_collections.save_budget_money_data()

@app.route('/deleteBudgetAction', methods=["POST"])
def delete_budget_action():
    return data_collections.delete_budget_action()

@app.route('/saveArchitectData', methods=["POST"])
def save_architect_data():
    return data_collections.save_architect_data()

@app.route('/deleteArchitectAction', methods=["POST"])
def delete_architect_action():
    return data_collections.delete_architect_action()

@app.route('/saveOrfiData', methods=["POST"])
def save_orfi_data():
    return data_collections.save_orfi_data()

@app.route('/saveOrfiFile', methods=["POST"])
def save_orfi_file():
    return data_collections.save_orfi_file()

@app.route('/deleteOrfiAction', methods=["POST"])
def delete_orfi_action():
    return data_collections.delete_orfi_action()

@app.route('/saveContactsData', methods=["POST"])
def save_contacts_data():
    return data_collections.save_contacts_data()

@app.route('/deleteContactsAction', methods=["POST"])
def delete_contacts_action():
    return data_collections.delete_contacts_action()

@app.route('/saveGalleryFolder', methods=["POST"])
def save_gallery_folder():
    return data_collections.save_gallery_folder()

@app.route('/deleteGalleryFolder', methods=["POST"])
def delete_gallery_folder():
    return data_collections.delete_gallery_folder()

@app.route('/saveFileAction', methods=["POST"])
def save_file_action():
    return data_collections.save_file_action()

@app.route('/deleteFileAction', methods=["POST"])
def delete_file_action():
    return data_collections.delete_file_action()

@app.route('/editFileAction', methods=["POST"])
def edit_file_action():
    return data_collections.edit_file_action()

@app.route('/changeMode')
def change_mode():
    return data_collections.change_mode()

@app.route('/saveGalleryViewImage', methods=["POST"])
def save_gallery_view_image():
    return data_collections.save_gallery_view_image()

@app.route('/deleteGalleryViewImage', methods=["POST"])
def delete_gallery_view_image():
    return data_collections.delete_gallery_view_image()

@app.route('/editGalleryViewImage', methods=["POST"])
def edit_gallery_view_image():
    return data_collections.edit_gallery_view_image()

@app.route('/changeStart', methods=["POST"])
def change_start():
    return data_collections.change_start()

@app.route('/saveNewPass', methods=["POST"])
def save_new_pass():
    return data_collections.save_new_pass()

@app.route('/saveScheduleData', methods=["POST"])
def save_schedule_data():
    return data_collections.save_schedule_data()


if __name__== "__main__":
    app.run(debug=True, port=8080)
    



