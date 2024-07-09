import json

def get_collection(name):
    return json.load(open(f"collections/{name}.json", encoding="utf-8"))

def general_data_collection():
    return get_collection("general_data")

def main_page_data_collection():
    return get_collection("main_page_data")

def stats_page_data_collection(p,v):
    return get_collection("stats_page_data")


def budget_page_data_collection(p,v):
    return get_collection("budget_page_data")

def schedule_page_data_collection(p,v):
    return get_collection("schedule_page_data")

def orfi_page_data_collection(p,v):
    return get_collection("orfi_page_data")


def architect_page_data_collection(p,v):
    return get_collection("architect_page_data")


def create_user_page_data_collection():
    return get_collection("create_user_page_data")
