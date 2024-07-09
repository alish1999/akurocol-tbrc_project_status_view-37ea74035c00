import json, uuid, os, math, datetime
from urllib.parse import urlparse
from .domain_classes import session, Collection, Budget, Project, Bill, Contact
from .domain_classes import current_user, User, Orfi, OrfiFile, BudgetFile, Role
from .domain_classes import GalleryFolder, GalleryItem, RecoverToken

from . import maps, akuro_runtime, env as back_env, send_one_email
from sqlalchemy import func

from flask import redirect, request, flash, get_flashed_messages, make_response, abort
from flask_login import login_user, logout_user



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
        ret = "$"+",".join(a) if simbol else ",".join(a)
        if not decimals:
            ret = ret
        else:
            ret = ret + "." + parts[1]
        if neg:
            ret = "-" + ret
        return ret
    except:
        return "0"

def sn(val):
    if val is None:
        return 0.0
    else:
        return val
    
def sd(val, format):
    if val is not None:
        try:
            return val.strftime(format)
        except:
            return ""
    return ""

def clear_number(val):
    return val.replace("$","").replace(" ","").replace(",","")

def get_collection(name):
    res = session.query(Collection).filter(Collection.collection_name == name).first()
    return json.loads(res.collection_data)

VISUALIZATION_STRING = "visualization"
EDITION_STRING = "edition"
MODE_NAME = "mode"

def change_mode():
    mode = request.args.get(MODE_NAME)
    if mode in [None,""," ","None"]:
        mode = VISUALIZATION_STRING
    if not allow_mode_change():
        mode = VISUALIZATION_STRING
    response = make_response(redirect(request.referrer))
    response.set_cookie(MODE_NAME, mode)
    return response

def allow_mode_change():
    if not current_user.is_authenticated:
        if request.path not in ["/public-login","/pass-change","/set-new-pass","/"]:
            abort(make_response(redirect("/public-login")))
    else:
        found = False
        for rol in current_user.roles_of_user:
            if rol.name == "TBRC Viewer":
                found = True
        if len(current_user.roles_of_user) == 1 and found:
            return False
        return True

def get_mode():
    if not allow_mode_change():
        return VISUALIZATION_STRING
    mode = request.cookies.get(MODE_NAME)
    if mode in [None,""," ","None"]:
        mode = VISUALIZATION_STRING
    return mode

def general_data_collection():
    data = get_collection("general_data")
    data["project_links"] = []
    data["profile_pic"] = "/static/images/default.png" 
    data["tbrc_edit_mode_image"] = "/static/frontend/images/edit_mode_on.png" if get_mode() == EDITION_STRING else "/static/frontend/images/edit_mode_off.png"
    data["tbrc_edit_mode_link"] = f"/changeMode?mode={VISUALIZATION_STRING}" if get_mode() == EDITION_STRING else  f"/changeMode?mode={EDITION_STRING}"
    data["tbrc_edit_mode_target"] = "_self" 
    data["edit_mode_allowed"] = allow_mode_change()
    data["edit_mode_on"] = get_mode() == EDITION_STRING
    data["tbrc_pass_change_submit_errors"] = [{"link_label":x} for x in get_flashed_messages()]
    data["tbrc_set_pass_action"] = "/saveNewPass?token="+request.args.get("token","no")
    #print("aaa",data["tbrc_pass_change_submit_errors"] )

    try:
        #print(current_user)
        if current_user.profile_picture not in [""," ",None, "None"]:
            data["profile_pic"] = current_user.profile_picture
        data["profile_name"] = current_user.user_full_name
        data["profile_subtitle"] = current_user.username
    except Exception as e:
        #print(e)
        pass
    if request.path.startswith("/stats/") or request.path.startswith("/budget/") or request.path.startswith("/schedule/") or request.path.startswith("/orfi/") or request.path.startswith("/architect/") or request.path.startswith("/contacts/") or request.path.startswith("/gallery/"):
        splits = request.path.split("/")[1:]
        urls = "/".join(splits[1:])
        data["project_links"] = [
            {
                "link_href":f"/stats/{urls}",
                "link_target":"_self",
                "link_label":"Dashboard"
            },
            {
                "link_href":f"/budget/{urls}",
                "link_target":"_self",
                "link_label":"Budget"
            },
            {
                "link_href":f"/schedule/{urls}",
                "link_target":"_self",
                "link_label":"Schedule"
            },
            {
                "link_href":f"/orfi/{urls}",
                "link_target":"_self",
                "link_label":"Orfi"
            }
        ]
        data["show_history"] = True
        data["history_links"] = [{
            "link_href":f"/{splits[0]}/{splits[1]}/{x.id}",
            "link_target":"_self",
            "link_label": x.version_timestamp.strftime("%m/%d/%Y")
        } for x in []]
        data["contacts_links"] = [{
            "link_href":f"#",
            "link_target":"_self",
            "link_label": f"<b>{x.contact_role}</b> - {x.contact_name} - {x.contact_email}"
        } for x in session.query(Contact).join(Contact.contact_project).filter(Project.project_url==splits[1]).all()]
        
        data["gallery_link"] = {
            "link_href":f"/gallery/{urls}",
            "link_target":"_self",
            "simple_link_image": "/static/frontend/images/dashboard_link.png"
        }
        data["contacts_link"] = {
            "link_href":f"/contacts/{urls}",
            "link_target":"_self",
            "simple_link_image": "/static/frontend/images/contacts.png"
        }
    return data

def get_pagination_filters_and_links(query, page_size, root, qs):
    page = int(request.args.get("page","1"))

    count = query.count()

    query = query.limit(page_size)
    query = query.offset((page-1)*page_size)

    total_pages = math.ceil(float(count)/float(page_size))

    qs_s = f""
    if qs is not None:
        qs_s += f"&search={qs}"

    prev = None if page <=1 else f"{root}page={page-1}{qs_s}"
    next = None if page >= total_pages else f"{root}page={page+1}{qs_s}"
    total = total_pages
    current_page = page
    

    return query, prev, next, total, current_page




def main_page_data_collection():
    if not current_user.is_authenticated:
        abort(make_response(redirect("/public-login")))
    data = get_collection("main_page_data")
    projects = session.query(Project)
    projects = projects.join(Project.user_set)

    if request.values.get('project_search') not in [None,"None",""," "]:
        for part in request.values.get('project_search').split(" "):
            projects = projects.filter(Project.project_name.ilike("%"+part+"%")|Project.project_description.ilike("%"+part+"%"))
    projects = projects.filter(User.id == current_user.id)
    
    projects, prev, next, total, current_page = get_pagination_filters_and_links(projects, 5, "?", None)
    projects = projects.all()

    data["main_page_paginator_prev"] = prev
    data["main_page_paginator_next"] = next
    data["main_page_paginator_current"] = current_page
    data["main_page_paginator_total"] = total

    data["main_page_projects"] = [{
        "project_href":{
            "link_label":f"{x.project_name}",
            "link_href":f"/stats/{x.project_url}",
            "link_target":"_self",
        },
        "project_name":f"{x.project_name}",
        "project_subtitle":f"{x.project_description}",
        "project_edit_link":{
            "simple_link_image":"/static/frontend/images/Button.png",
            "link_href":f"/edit-project/{x.project_url}",
            "link_target":"_self",
        },
        "project_gallery_link":{
            "link_label":"View gallery",
            "link_href":f"/gallery/{x.project_url}",
            "link_target":"_self",
        }
    } for x in projects]

    return data

def stats_page_data_collection(p):
    data = get_collection("stats_page_data")
    project = session.query(Project)
    project = project.filter(Project.project_url == p)
    project = project.first()
    if project is None:
        abort(404)

    data["stats_page_title"] = project.project_name
    data["stats_page_description"] = project.project_address


    ### calculos generales:
    budgets = session.query(
        func.sum(Budget.budget_amount).label("cost_budget"), 
        func.max(Budget.budget_is_hard_cost).label("cost_is_schedule"),
        func.sum(Budget.budget_total_duration).label("budget_total_duration"),
        func.sum(Budget.budget_progress).label("budget_progress"),
    )
    budgets = budgets.join(Budget.budget_project)
    budgets = budgets.filter(Project.project_url == p)
    budgets = budgets.group_by(Budget.id)
    budgets = budgets.all()


    budget = 0.0
    total_time = 0.0
    total_hard_costs_budget = 0.0
    for c in budgets:
        budget += sn(c.cost_budget)
        if c.cost_is_schedule:
            total_hard_costs_budget += sn(c.cost_budget)
            total_time += sn(c.budget_total_duration)


    bills = session.query(
        func.sum(Budget.budget_amount).label("cost_budget"), 
        func.sum(Bill.bill_paid_to_date).label("cost_paid_to_date"),
        func.max(Budget.budget_is_hard_cost).label("cost_is_schedule")
    )
    bills = bills.join(Budget.budget_project)
    bills = bills.outerjoin(Budget.bill_set)
    bills = bills.filter(Project.project_url == p)
    bills = bills.group_by(Budget.id)
    bills = bills.all()

    print(bills)


    payed_to_date = 0.0
    payed_to_date_hard_cost = 0.0
    for c in bills:
        payed_to_date += sn(c.cost_paid_to_date)
        if c.cost_is_schedule:
            payed_to_date_hard_cost += sn(c.cost_paid_to_date)
    
    data["stats_page_budget_start"] = ""
    data["stats_page_budget_end"] =  moneyprint(budget, simbol=True)
    data["stats_page_budget_current_percentage"] = min(int(payed_to_date/budget*100),100) if budget> 0 else "-"
    data["stats_page_budget_current_value"] = moneyprint(payed_to_date, simbol=True)
    data["stats_page_budget_end2"] = str("{:.2f}".format(payed_to_date/budget*100))+"%" if budget> 0 else "-"
    data["stats_page_budget_color"] = "#A48C50"
    data["stats_page_budget_link"] = {
        "link_href":f"/budget/{p}",
        "simple_link_image":"/static/frontend/images/icon-budget.png",
        "link_target":"_self"
    }

    total_progress = payed_to_date_hard_cost/total_hard_costs_budget*total_time if total_hard_costs_budget > 0 else 0

    data["stats_page_schedule_start"] = ""
    data["stats_page_schedule_end"] =  f"{total_time} Months"
    data["stats_page_schedule_current_percentage"] = min(int(payed_to_date_hard_cost/total_hard_costs_budget*100),100) if total_hard_costs_budget> 0 else "-"
    data["stats_page_schedule_current_value"] = "{:.2f}".format(total_progress)+" Months" if total_progress> 0 else "-"
    data["stats_page_schedule_end2"] = f"{int(payed_to_date_hard_cost/total_hard_costs_budget*100)}%" if total_hard_costs_budget > 0 else "-"

    data["stats_page_schedule_color"] = "#864F4F"
    data["stats_page_schedule_link"] = {
        "link_href":f"/schedule/{p}",
        "simple_link_image":"/static/frontend/images/icon-schedule.png",
        "link_target":"_self"
    }

    orfis = project.orfi_set
    total = 0
    completed = 0
    missing = 0 
    past = False

    for o in orfis:
        total += 1
        if o.orfi_resolved:
            completed += 1
        else:
            missing += 1
            past = past or (o.orfi_due < datetime.datetime.now() if o.orfi_due is not None else False)

    data["stats_page_orfi_start"] = ""
    data["stats_page_orfi_end"] = total
    data["stats_page_orfi_current_percentage"] = total if total == 0 else int(missing/total*100)
    data["stats_page_orfi_current_value"] = missing
    data["stats_page_orfi_end2"] = total
    data["stats_page_orfi_color"] = "#74836B" if not past else "#ff0000"
    data["stats_page_orfi_link"] = {
        "link_href":f"/orfi/{p}",
        "simple_link_image":"/static/frontend/images/icon-orfi.png",
        "link_target":"_self"
    }

    data["stats_page_gallery_link"] = {
        "link_href":f"/gallery/{p}",
        "link_label":"View gallery",
        "link_target":"_self"
    }

    #ni idea de como cargar los orfis
    return data


def budget_page_data_collection(p):
    data = get_collection("budget_page_data")
    project = session.query(Project)
    project = project.filter(Project.project_url == p)
    project = project.first()
    if project is None:
        abort(404)

    data["budget_page_title"] = f"{project.project_name} Budget"
    budgets = session.query(Budget)
    budgets = budgets.join(Budget.budget_project)
    budgets = budgets.filter(Project.project_url == p)
    budgets, prev, next, total, current_page = get_pagination_filters_and_links(budgets, 15, "?", None)
    budgets = budgets.all()

    data["budget_page_paginator_prev"] = prev
    data["budget_page_paginator_next"] = next
    data["budget_page_paginator_current"] = current_page
    data["budget_page_paginator_total"] = total


    costs = []
    b:Budget
    for b in budgets:
        paid = 0.0
        for bill in b.bill_set:
            paid += sn(bill.bill_paid_to_date)
        perc = int((paid / float(b.budget_amount))*100)
        costs.append({
            "budget_item_id":b.id,
            "budget_item_total": moneyprint(b.budget_amount, simbol=True),
            "budget_item_total_raw":b.budget_amount,
            "budget_item_paid":moneyprint(paid, simbol=True),
            "budget_item_paid_raw":paid,
            "budget_item_time_raw":b.budget_total_duration,
            "budget_item_percentage":f"{perc} %",
            "budget_item_hard_cost_value":b.budget_is_hard_cost,
            "budget_item_company_value":b.budget_company,
            "budget_item_email_value":b.budget_email,
            "budget_item_phone_value":b.budget_phone,
            "budget_item_budget_value":b.budget_amount,
            "budget_item_title_value":b.budget_name,
            "budget_item_files_link":f"/contractor-files/{b.id}",
            "budget_item_name":f"{b.budget_name}",
            "budget_item_link":{
                "link_href":f"/architect/{p}?budget={b.id}",
                "link_label":"See more", #esto a donde va?
                "link_target":"_self",
                "simple_link_image":"/static/frontend/images/arrow_circle_up.svg"
            },
            "budget_item_files_link":{
                "link_href":f"/contractor-files/{b.id}",
                "link_label":"Go to contractor's files", #esto a donde va?
                "link_target":"_self",
            }    
        })
    data["budget_page_items"] = costs
    return data


def save_budget_contact_data():
    id_ = request.form.get("current_category_id")
    if id_ is not None:
        budget = session.query(Budget).filter(Budget.id == id_).first()
        budget.budget_company = request.form.get("budget_contact_company")
        budget.budget_email = request.form.get("budget_contact_email")
        budget.budget_phone = request.form.get("budget_contact_phone")
        budget.budget_is_hard_cost = request.form.get("budget_contact_is_hard") == "on"
        session.commit()
        return redirect(request.referrer)
    else:
        project_id = urlparse(request.referrer).path.split("/")[-1]
        proj = session.query(Project).filter(Project.project_url == project_id).first()
        budget = Budget()
        budget.budget_company = request.form.get("new_budget_contact_company")
        budget.budget_email = request.form.get("new_budget_contact_email")
        budget.budget_phone = request.form.get("new_budget_contact_phone")
        budget.budget_is_hard_cost = request.form.get("new_budget_contact_is_hard") == "on"
        budget.budget_project = proj
        budget.budget_name = ""
        budget.budget_amount = 1
        session.add(budget)
        session.commit()
        return redirect(request.referrer)

def save_budget_money_data():
    id_ = request.form.get("current_category_id")
    if id_ is not None:
        budget = session.query(Budget).filter(Budget.id == id_).first()
        budget.budget_name = request.form.get("budget_caregory_name")
        budget.budget_amount = clear_number(request.form.get("budget_caregory_money"))
        budget.budget_total_duration = clear_number(request.form.get("budget_caregory_time"))
        session.commit()
        return redirect(request.referrer)

def delete_budget_action():
    id_ = request.form.get("current_category_id")
    if id_ is not None:
        budget = session.query(Budget).filter(Budget.id == id_).first()
        session.delete(budget)
        session.commit()
        return redirect(request.referrer)

def schedule_page_data_collection(p):
    data = get_collection("schedule_page_data")
    project = session.query(Project)
    project = project.filter(Project.project_url == p)
    project = project.first()
    if project is None:
        abort(404)
    data["schedule_page_title"] = f"{project.project_name} Schedule"
    budgets = session.query(Budget)
    budgets = budgets.join(Budget.budget_project)
    budgets = budgets.filter(Budget.budget_is_hard_cost == True)
    budgets = budgets.filter(Project.project_url == p)
    budgets, prev, next, total, current_page = get_pagination_filters_and_links(budgets, 15, "?", None)
    budgets = budgets.all()

    data["schedule_page_paginator_prev"] = prev
    data["schedule_page_paginator_next"] = next
    data["schedule_page_paginator_current"] = current_page
    data["schedule_page_paginator_total"] = total 

    costs = []
    c:Budget
    for c in budgets:
        if c.budget_is_hard_cost:
            paid = 0.0
            budget = 0.0
            pending = 0.0
            for bill in c.bill_set:
                paid += sn(bill.bill_paid_to_date)
                budget += sn(bill.bill_amount)
                pending += sn(bill.bill_amount) - sn(bill.bill_paid_to_date)

            p_cmpleted = 0 
            budget_progress = 0
            try:
                p_cmpleted = int((paid)/float(c.budget_amount)*100)
                budget_progress = (p_cmpleted/100.0)*c.budget_total_duration
            except:
                p_cmpleted = 0

            
            costs.append({
                "schedule_item_id":c.id,
                "schedule_item_name":f"{c.budget_name}",
                "schedule_item_budget":f"${moneyprint(c.budget_amount)}",
                "schedule_item_paid_to_date":f"{moneyprint(paid)}",                
                "schedule_item_completion":f"{p_cmpleted} %",
                "schedule_item_total_duration":f"{c.budget_total_duration}",
                "schedule_item_progress":"{:.2f}".format(budget_progress),
            })
    data["schedule_page_items"] = costs
    return data

def orfi_page_data_collection(p):
    data = get_collection("orfi_page_data")
    project = session.query(Project)
    project = project.filter(Project.project_url == p)
    project = project.first()
    if project is None:
        abort(404)
    orfis = session.query(Orfi)
    orfis = orfis.filter(Orfi.orfi_project_id == project.id)

    orfis, prev, next, total, current_page = get_pagination_filters_and_links(orfis, 15, "?", None)
    orfis = orfis.all()

    data["orfi_page_paginator_prev"] = prev
    data["orfi_page_paginator_next"] = next
    data["orfi_page_paginator_current"] = current_page
    data["orfi_page_paginator_total"] = total 

    orfi_data = []
    o:Orfi
    for o in orfis:
        orfi_data.append({
            "orfi_item_id":o.id,
            "orfi_item_due_data":o.orfi_due.strftime("%Y-%m-%d") if o.orfi_due is not None else "",
            "orfi_item_resolved":"/static/frontend/images/ok.png" if o.orfi_resolved else "/static/frontend/images/not_ok.png",
            "orfi_item_resolved_raw":o.orfi_resolved,
            "orfi_item_date":o.orfi_creation.strftime("%m/%d/%Y") if o.orfi_creation is not None else "",
            "orfi_item_asigned":o.orfi_asigned_to,
            "orfi_item_question":o.orfi_title,
            "orfi_item_link":{
                "link_href":f"/orfi-files/{o.id}",
                "link_label":"🗀 Go to Folder ",
                "link_target":"_blank",
                "simple_link_image":"/static/frontend/images/forward_to_inbox.svg"
            }
        })
    data["orfi_page_items"] = orfi_data
    return data

def save_orfi_data():
    id_ = request.form.get("current_orfi_id")
    if id_ is not None:
        orfi = session.query(Orfi).filter(Orfi.id == id_).first()
        orfi.orfi_due = akuro_runtime.try_date(request.form.get("orfi_due_date"))
        orfi.orfi_resolved = request.form.get("orfi_resolved") == "on"
        orfi.orfi_asigned_to = request.form.get("orfi_asigned_to")
        orfi.orfi_title = request.form.get("orfi_question")
        session.commit()
        return redirect(request.referrer)
    else:
        project_id = urlparse(request.referrer).path.split("/")[-1]
        proj = session.query(Project).filter(Project.project_url == project_id).first()
        orfi = Orfi()
        orfi.orfi_creation = datetime.datetime.now()
        orfi.orfi_due = akuro_runtime.try_date(request.form.get("new_orfi_due_date"))
        orfi.orfi_resolved = request.form.get("new_orfi_resolved") == "on"
        orfi.orfi_asigned_to = request.form.get("new_orfi_asigned_to")
        orfi.orfi_title = request.form.get("new_orfi_question")
        orfi.orfi_project_id = proj.id
        session.add(orfi)
        session.commit()
        return redirect(request.referrer)


def save_orfi_file():
    id_ = request.form.get("current_orfi_id")
    orfi = session.query(Orfi).filter(Orfi.id == id_).first()
    fil = OrfiFile()
    fil.orfi_file_name = urlparse(request.form.get("orfi_new_file")).path.split("/")[-1]
    fil.orfi_file_file = request.form.get("orfi_new_file")
    fil.orfi_file_orfi = orfi
    session.add(fil)
    session.commit()
    return redirect(request.referrer)

def delete_orfi_action():
    id_ = request.form.get("current_orfi_id")
    if id_ is not None:
        orfi = session.query(Orfi).filter(Orfi.id == id_).first()
        session.delete(orfi)
        session.commit()
        return redirect(request.referrer)




def architect_page_data_collection(p):
    data = get_collection("architect_page_data")
    project = session.query(Project)
    project = project.filter(Project.project_url == p)
    project = project.first()
    if project is None:
        abort(404)
    costs = []
    #preguntar si los agrupo
    budget_param = request.args.get('budget')
    bills = session.query(Bill)
    bills = bills.filter(Bill.bill_budget)
    bills = bills.filter(Budget.id == budget_param)
    bills, prev, next, total, current_page = get_pagination_filters_and_links(bills, 15, f"?budget={budget_param}&", None)
    bills = bills.all()

    data["architect_page_paginator_prev"] = prev
    data["architect_page_paginator_next"] = next
    data["architect_page_paginator_current"] = current_page
    data["architect_page_paginator_total"] = total 

    budget = session.query(Budget)
    budget = budget.filter(Budget.id == budget_param)
    budget = budget.first()
    budget:Budget

    data["architect_page_title"] = f"{project.project_name} {budget.budget_name}"
    c:Bill
    for c in bills:
        percentage = 0
        try:
            percentage = int(c.bill_paid_to_date/c.bill_amount*100)
        except:
            percentage = 0
        costs.append({
            "architect_item_id":c.id,
            "architect_item_vendor":budget.budget_company,
            "architect_item_due_date":sd(c.bill_date, "%m/%d/%Y"),
            "architect_item_due_date_raw":sd(c.bill_date, "%Y-%m-%d"),
            "architect_item_code":c.bill_invoice,
            "architect_item_total":moneyprint(c.bill_amount, simbol=True),
            "architect_item_total_raw":sn(c.bill_amount),
            "architect_item_paid":moneyprint(c.bill_paid_to_date, simbol=True),
            "architect_item_paid_raw":sn(c.bill_paid_to_date),
            "architect_item_pending":moneyprint(sn(c.bill_amount) - sn(c.bill_paid_to_date), simbol=True),
            "architect_item_percetage":f"{percentage} %"
        })
    data["architect_page_items"] = costs
    data["architect_modal_action"] = f"/saveArchitectData?budget={budget_param}"
    data["architect_delete_action"] = f"/deleteArchitectAction?budget={budget_param}"
    data["architect_page_files_link"] = {
        "link_href":f"/contractor-files/{budget.id}",
        "link_target":"_self",
        "link_label":"Contractor's files"
    }
    data["architect_dropdown_links"] = [
        {
            "link_href":project.project_contact,
            "link_target":"_blank",
            "link_label":"<img src='/static/frontend/images/contact_ico.png'> Contact"
        },
        {
            "link_href":project.project_invoices,
            "link_target":"_blank",
            "link_label":"<img src='/static/frontend/images/invoices_ico.png'> Invoices"
        },{
            "link_href":project.project_contract,
            "link_target":"_blank",
            "link_label":"<img src='/static/frontend/images/contract_ico.png'> Contract"
        },{
            "link_href":project.project_comms,
            "link_target":"_blank",
            "link_label":"<img src='/static/frontend/images/comms_ico.png'> Comms"
        }
    ]
    return data


def save_architect_data():
    id_ = request.form.get("current_bill_id")
    if id_ is not None:
        bill = session.query(Bill).filter(Bill.id == id_).first()
        bill.bill_date = akuro_runtime.try_date(request.form.get("bill_date"))
        bill.bill_invoice = request.form.get("bill_invoice")
        bill.bill_amount = clear_number(request.form.get("bill_amount"))
        bill.bill_paid_to_date = clear_number(request.form.get("bill_paid"))
        session.commit()
        return redirect(request.referrer)
    else:
        bud_id = request.args.get("budget")
        bill = Bill()
        bill.bill_date = akuro_runtime.try_date(request.form.get("new_bill_date"))
        bill.bill_invoice = request.form.get("new_bill_invoice")
        bill.bill_amount = clear_number(request.form.get("new_bill_amount"))
        bill.bill_paid_to_date = clear_number(request.form.get("new_bill_paid"))
        bill.bill_budget_id = bud_id
        session.add(bill)
        session.commit()
        return redirect(request.referrer)


def delete_architect_action():
    id_ = request.form.get("current_bill_id")
    if id_ is not None:
        bill = session.query(Bill).filter(Bill.id == id_).first()
        session.delete(bill)
        session.commit()
        return redirect(request.referrer)


def contacts_page_data_collection(p):
    data = get_collection("contacts_page_data")
    project = session.query(Project)
    project = project.filter(Project.project_url == p)
    project = project.first()
    if project is None:
        abort(404)
    costs = []
    #preguntar si los agrupo
    data["contacts_page_title"] = f"Directory"
    contacts = session.query(Budget)
    contacts = contacts.filter(Budget.budget_project_id == project.id)
    contacts, prev, next, total, current_page = get_pagination_filters_and_links(contacts, 15, f"?", None)

    contacts = contacts.all()

    data["contacts_page_paginator_prev"] = prev
    data["contacts_page_paginator_next"] = next
    data["contacts_page_paginator_current"] = current_page
    data["contacts_page_paginator_total"] = total 

    for c in contacts:
        c:Budget
        costs.append({
            "contacts_item_id":c.id,
            "contacts_item_name":c.budget_name2,
            "contacts_item_company":f"{c.budget_company}",
            "contacts_item_role":c.budget_name,
            "contacts_item_email":c.budget_email,
            "contacts_item_phone":c.budget_phone,
        })
    data["contacts_page_items"] = costs
    return data


def save_contacts_data():
    id_ = request.form.get("current_contacts_id")
    if id_ is not None:
        contact = session.query(Budget).filter(Budget.id == id_).first()
        contact:Budget
        contact.budget_name2 = request.form.get("contacts_name")
        contact.budget_company = request.form.get("contacts_company")
        contact.budget_email = request.form.get("contacts_email")
        contact.budget_phone = request.form.get("contacts_phone")
        session.commit()
        return redirect(request.referrer)

def delete_contacts_action():
    id_ = request.form.get("current_contacts_id")
    if id_ is not None:
        contact = session.query(Contact).filter(Contact.id == id_).first()
        session.delete(contact)
        session.commit()
        return redirect(request.referrer)

def gallery_page_data_collection(p):
    data = get_collection("gallery_page_data")
    project = session.query(Project)
    project = project.filter(Project.project_url == p)
    project = project.first()
    if project is None:
        abort(404)
    costs = []
    #preguntar si los agrupo
    data["gallery_page_title"] = f"{project.project_name} Gallery"
    data["gallery_page_description"] = f"{project.project_description}"
    for c in project.gallery_folder_set:
        costs.append({
            "gallery_item_id":c.id,
            "gallery_item_name":c.gallery_folder_name,
            "gallery_item_description":c.gallery_folder_description,
            "gallery_item_link":{
                "link_href":f"/gallery-view/{c.id}",
                "link_target":"_blank",
                "link_label":"Open folder ⧉"
            }
        })
    data["gallery_page_items"] = costs
    return data


def save_gallery_folder():
    id_ = request.form.get("gallery_item_hidden_id")
    if id_ is not None:
        folder = session.query(GalleryFolder).filter(GalleryFolder.id == id_).first()
        folder.gallery_folder_name = request.form.get("gallery_item_new_name")
        folder.gallery_folder_description = request.form.get("gallery_item_new_description")
        session.commit()
        return redirect(request.referrer)
    else:
        project_id = urlparse(request.referrer).path.split("/")[-1]
        proj = session.query(Project).filter(Project.project_url == project_id).first()
        folder = GalleryFolder()
        folder.gallery_folder_name = request.form.get("new_folder_name")
        folder.gallery_folder_description = request.form.get("new_folder_description")
        folder.gallery_folder_project_id = proj.id
        session.add(folder)
        session.commit()
        return redirect(request.referrer)

def delete_gallery_folder():
    id_ = request.form.get("gallery_item_hidden_id")
    if id_ is not None:
        folder = session.query(GalleryFolder).filter(GalleryFolder.id == id_).first()
        session.delete(folder)
        session.commit()
        return redirect(request.referrer)

def project_edit_page_data_collection(project_url):
    data  = get_collection("project_edit_page_data")
    if project_url != "-1":
        project = session.query(Project)
        project = project.filter(Project.project_url == project_url)
        project = project.first()
        if project is None:
            abort(404)
        project:Project
        data["project_edit_name_value"] = project.project_name
        data["project_edit_projects_value"] = [{
            "option_value": x.id,
            "option_label": x.username,
            "option_selected": x in project.user_set
        } for x in session.query(User).all()]
        data["project_edit_description_value"] = project.project_description
        data["project_edit_address_value"] = project.project_address
        data["show_delete_in_project"] = True
        return data
    else:
        data["project_edit_name_value"] = ""
        data["project_edit_projects_value"] = [{
            "option_value": x.id,
            "option_label": x.username,
            "option_selected": False
        } for x in session.query(User).all()]
        data["project_edit_description_value"] = ""
        data["project_edit_address_value"] = ""
        data["project_edit_page_title"] = "Create Project"
        data["show_delete_in_project"] = False
        return data

def set_url(proj):
    proj_start = 0
    proj_sucess = False
    while not proj_sucess:
        proj_new_url = akuro_runtime.string_to_url_fragment(proj.project_name)
        if proj_start != 0:
            proj_new_url = proj_new_url + "-" + str(proj_start)
        old = session.query(Project).filter(Project.project_url == proj_new_url).first()
        if old is None:
            proj.project_url = proj_new_url
            proj_sucess = True
        else:
            proj_start += 1

def save_project_data():
    project_url = request.referrer.split("/")[-1]
    if project_url == "-1":
        project = Project()
    else:
        project = session.query(Project)
        project = project.filter(Project.project_url == project_url)
        project = project.first()
    if project is None:
        abort(404)
    delete = request.form.get("project_edit_delete_button", "") == "project_edit_delete_button"
    if not delete:
        project:Project
        project.project_name = request.form.get("proj_name")
        set_url(project)
        project.project_description  = request.form.get("proj_description")
        project.project_address  = request.form.get("proj_address")
        users = session.query(User).filter(User.id.in_(request.form.getlist("proj_projects"))).all()
        project.user_set = users
        session.commit()
    else:
        session.delete(project)
        session.commit()
    return redirect("/home")


def create_user_page_data_collection():
    data = get_collection("create_user_page_data")
    return data

def save_user():
    if request.method == 'POST':
        user = User(
            username = request.form.get("new_user_email"),
            password = akuro_runtime.unicode_password_hash(request.form.get("new_user_password")),
            profile_picture = "/static/images/default.png",
            user_full_name = request.form.get("new_user_fullname"),
            roles_of_user = session.query(Role).filter(Role.id.in_(request.form.getlist("new_user_roles"))).all()
        )
        
        session.add(user)
        session.commit()
        return redirect("/home")
    
def change_start():
    error = False
    success = False
    user = None
    if request.method == 'POST':
        user = session.query(User).filter(User.username == request.form.get("pass_change_email")).first()
        if user is None:
            flash("User not found")
        else:
            try:
                token_instance = RecoverToken()
                token_instance.token_string= str(uuid.uuid4())
                token_instance.token_expires = datetime.datetime.now() + datetime.timedelta(minutes = 30)
                token_instance.token_user = user
                session.add(token_instance)
                session.commit()
                template_recover_user = back_env.get_template('emails/recover_user.html')
                recover_user_mails = [
                    user.username
                ]
                msg_recover_user = template_recover_user.render(recover_token_instance = token_instance, mails = recover_user_mails)
                #print(msg_recover_user)
                send_one_email(
                    recover_user_mails, 
                    "Email Recovery | TBRC",
                    msg_recover_user
                )
                success = True
                flash("A mail was sent with instructions")
            except Exception as e:
                error = True
                flash(str(e))
    return redirect("/pass-change")


def save_new_pass():
    token_val = request.args.get('token')
    try:
        token_instance = session.query(RecoverToken)
        token_instance = token_instance.filter(token_val==RecoverToken.token_string)
        token_instance = token_instance.filter(RecoverToken.token_expires>datetime.datetime.now())
        token_instance = token_instance.first()
        if token_instance is None:
            raise Exception("Token no encontrado o expirado")            
        user = token_instance.token_user
        if not user:
            raise Exception("Usuario no encontrado")
        
        if request.form["set_pass_password"] != request.form["set_pass_password_re"]:
            raise Exception("Las contraseñas no coinciden")
        
        
        user.password = akuro_runtime.unicode_password_hash(request.form["set_pass_password"])
        session.delete(token_instance)
        session.commit()
        return redirect("/public-login")
    except Exception as e:
        flash(str(e))
        return redirect(f"/set-new-pass?token={token_val}")

def orfi_file_upload():
    if request.method == 'POST':
        result = [] 
        for file in request.files:
            file_to_upload = request.files[file]
            if file_to_upload!="":
                mime_type = file_to_upload.content_type
                names = os.path.splitext(file_to_upload.filename)
                tempname = akuro_runtime.string_to_url_fragment(names[0]) + names[1]
                file_to_upload.save("static/uploads/"+tempname)
                # get file size after saving
                size = os.path.getsize("static/uploads/"+tempname)
                # return json for js call back
                result.append({"name":tempname,"type": mime_type,"size": size,"url": "/static/uploads/"+tempname,"thumbnailUrl": "/static/uploads/"+tempname,"deleteUrl": "", "deleteType": "DELETE"})
            
        return json.dumps({"files": result})

def files_page_data_collection(orfi_param):
    data = get_collection("files_page_data")
    if request.path.find("/orfi-files/") > -1:
        files = session.query(OrfiFile)
        files = files.filter(OrfiFile.orfi_file_orfi_id == orfi_param)
        files = files.all()

        orfi = session.query(Orfi)
        orfi = orfi.filter(Orfi.id == orfi_param)
        orfi = orfi.first()
        #preguntar si los agrupo
        data["files_page_title"] = f"{orfi.orfi_project.project_name} Files"
        data["files_page_description"] = f"{orfi.orfi_project.project_description}"
        costs = []
        c:OrfiFile
        for c in files:
            costs.append({
                "files_item_id":f"OrfiFile-{c.id}",
                "files_item_name":c.orfi_file_name,
                "files_item_link":{
                    "link_href":c.orfi_file_file,
                    "link_target":"_blank",
                    "link_label":"Download File ⧉"
                }
            })
        data["files_page_items"] = costs
        return data
    elif request.path.find("/contractor-files/") > -1:
        files = session.query(BudgetFile)
        files = files.filter(BudgetFile.budget_file_budget_id == orfi_param)
        files = files.all()

        budget = session.query(Budget)
        budget = budget.filter(Budget.id == orfi_param)
        budget = budget.first()
        #preguntar si los agrupo
        data["files_page_title"] = f"{budget.budget_project.project_name} Files"
        data["files_page_description"] = f"{budget.budget_project.project_description}"
        costs = []
        c:BudgetFile
        for c in files:
            costs.append({
                "files_item_id":f"BudgetFile-{c.id}",
                "files_item_name":c.budget_file_name,
                "files_item_link":{
                    "link_href":c.budget_file_file,
                    "link_target":"_blank",
                    "link_label":"Download File ⧉"
                }
            })
        data["files_page_items"] = costs
        return data


def save_file_action():
    orfi_id = urlparse(request.referrer).path.split("/")[-1]
    type_ = urlparse(request.referrer).path.split("/")[-2]
    id_ = request.form.get("files_item_hidden_id")
    if id_ is not None:
        pass #no tienen edicion en estos 
    else:
        if type_ == "orfi-files":
            proj = session.query(Orfi).filter(Orfi.id == orfi_id).first()
            file = OrfiFile()
            file.orfi_file_name = request.form.get("new_file_name")
            file.orfi_file_file = request.form.get("new_file_file")
            file.orfi_file_orfi_id = proj.id
            session.add(file)
            session.commit()
        elif type_ == "contractor-files":
            proj = session.query(Budget).filter(Budget.id == orfi_id).first()
            file = BudgetFile()
            file.budget_file_name = request.form.get("new_file_name")
            file.budget_file_file = request.form.get("new_file_file")
            file.budget_file_budget_id = proj.id
            session.add(file)
            session.commit()
        return redirect(request.referrer)


def delete_file_action():
    id_ = request.form.get("files_item_hidden_id")
    type_ = urlparse(request.referrer).path.split("/")[-2]
    if id_ is not None:
        if type_ == "orfi-files":
            id_ = id_.replace("OrfiFile-","")
            fil = session.query(OrfiFile).filter(OrfiFile.id == id_).first()
            session.delete(fil)
            session.commit()
        elif type_ == "contractor-files":
            id_ = id_.replace("BudgetFile-","")
            fil = session.query(BudgetFile).filter(BudgetFile.id == id_).first()
            session.delete(fil)
            session.commit()
        return redirect(request.referrer)


def edit_file_action():
    orfi_id = urlparse(request.referrer).path.split("/")[-1]
    type_ = urlparse(request.referrer).path.split("/")[-2]
    id_ = request.form.get("files_item_hidden_id")
    if id_ is not None:
        if type_ == "orfi-files":
            id_ = id_.replace("OrfiFile-","")
            proj = session.query(Orfi).filter(Orfi.id == orfi_id).first()
            file = session.query(OrfiFile).filter(OrfiFile.id == id_).first()
            file.orfi_file_name = request.form.get("files_item_file_name_input")
            file.orfi_file_file = request.form.get("files_item_new_file")
            file.orfi_file_orfi_id = proj.id
            session.add(file)
            session.commit()
        elif type_ == "contractor-files":
            id_ = id_.replace("BudgetFile-","")
            proj = session.query(Budget).filter(Budget.id == orfi_id).first()
            file = session.query(OrfiFile).filter(OrfiFile.id == id_).first()
            file.budget_file_name = request.form.get("files_item_file_name_input")
            file.budget_file_file = request.form.get("files_item_new_file")
            file.budget_file_budget_id = proj.id
            session.add(file)
            session.commit()
        return redirect(request.referrer)

def map_gallery_item(g:GalleryItem):
    return {
        "gallery_view_item_id":g.id,
        "gallery_view_item_name":g.gallery_item_name,
        "gallery_view_item_image_small":g.gallery_item_link,
        "gallery_view_item_image_big":g.gallery_item_link
    }

def gallery_view_page_data_collection(p):
    data = get_collection("gallery_view_page_data")
    folder = session.query(GalleryFolder).filter(GalleryFolder.id == p).first()
    if folder is None:
        abort(404)
    data["gallery_view_page_title"] = f"{folder.gallery_folder_project.project_name} - {folder.gallery_folder_name}"
    data["gallery_view_page_description"] = f"{folder.gallery_folder_description}"
    data["gallery_view_page_items"] = list(map(map_gallery_item, folder.gallery_item_set))
    return data

def save_gallery_view_image():
    folder_id = urlparse(request.referrer).path.split("/")[-1]
    folder = session.query(GalleryFolder).filter(GalleryFolder.id == folder_id).first()
    image = GalleryItem()
    image.gallery_item_name = request.form.get("new_image_name")
    image.gallery_item_link = request.form.get("new_image_file")
    image.gallery_item_folder_id = folder.id
    session.add(image)
    session.commit()
    return redirect(request.referrer)

def delete_gallery_view_image():
    id_ = request.form.get("gallery_view_item_hidden_id")
    if id_ is not None:
        image = session.query(GalleryItem).filter(GalleryItem.id == id_).first()
        session.delete(image)
        session.commit()
        return redirect(request.referrer)


def edit_gallery_view_image():
    id_ = request.form.get("gallery_view_item_hidden_id")
    if id_ is not None:
        image = session.query(GalleryItem).filter(GalleryItem.id == id_).first()
        image.gallery_item_name = request.form.get("edit_image_name")
        session.commit()
        return redirect(request.referrer)


def save_schedule_data():
    id_ = request.form.get("current_schedule_id")
    if id_ is not None:
        budget = session.query(Budget).filter(Budget.id == id_).first()
        budget.budget_total_duration = clear_number(request.form.get("schedule_input_time"))
        #budget.budget_progress = request.form.get("schedule_input_progress")
        session.commit()
        return redirect(request.referrer)


def session_start():
    error=False
    if request.method=='POST': 
        user = session.query(User).filter(User.username==request.form['login_email']).first()
        if user:
            if akuro_runtime.akuro_check_user(user.username, user.password, request.form["login_password"]):
                login_user(user)
                return redirect('/home')
            else:
                error=True
        else:
            error=True
    flash("Incorrect login data")
    return redirect('/public-login')

def public_logout():
    logout_user()
    return redirect("/")
