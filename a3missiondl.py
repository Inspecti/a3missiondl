import os
import sys
import getpass
import re
import urllib
import json
import requests

# -------------------------------------------
# Settings
# -------------------------------------------

steamcmd_path = "steamcmd" # path to steamcmd binary
steam_user = "" # steam username, query asks for username if not set 
steam_password = "" # steam password, query asks for password if not set

a3_server_dir = "/var/arma/arma3" # Absolute path to server root dir
a3_workshop_id = "107410" # Arma 3 workshop ID

a3_workshop_dir = "{}/steamapps/workshop/content/{}".format(a3_server_dir, a3_workshop_id)
a3_mpmissions_dir = "/var/arma/arma3/mpmissions" # Absolute path to mpmissions

# -------------------------------------------

if len(sys.argv) < 2:
    print("Please input Steam workshop url as an argument!")
    exit()

if len(sys.argv) > 2:
    print("Please input only one Steam workshop url as an argument!")
    exit() # use sys.exit() for multithreading

if steam_user == "":
    print("No Steam username provided, please enter username:")
    steam_user = input("Username: ")
    if steam_user == "" or steam_user == None: 
        print("Please enter valid steam username!")
        exit()

if steam_password == "":
    print("No Steam user password provided, please enter password for user {}".format(steam_user))
    steam_password = getpass.getpass()
    if steam_password == "":
        print("No password provided, exiting.")
        exit()

mission_workshop_url = sys.argv[1]


def get_workshop_id_from_url(mission_workshop_url):
    if "/?id=" in mission_workshop_url:
        mission_workshop_id = mission_workshop_url.split("/?id=")[1]
        if "%" in mission_workshop_id:
            mission_workshop_id = mission_workshop_id.split("&")[0]
    if "/discussions/" in mission_workshop_url:
        mission_workshop_id = mission_workshop_url.split("/discussions/")[1]
    if "/comments/" in mission_workshop_url:
        mission_workshop_id = mission_workshop_url.split("/comments/")[1]
    if "/changelog/" in mission_workshop_url:
        mission_workshop_id = mission_workshop_url.split("/changelog/")[1]

    if mission_workshop_id == "" or mission_workshop_id is None:
        print("Could not find valid workshop ID from url!")
        exit()
    
    return(mission_workshop_id)

def get_mission_filename(mission_workshop_id): 
    url = "https://api.steampowered.com/ISteamRemoteStorage/GetPublishedFileDetails/v1/"
    contents = { "format": "json",
                 "itemcount": "1",
                 "publishedfileids[0]": mission_workshop_id }
    
    print("Getting file info from Steam workshop...")

    json_response = requests.post(url, data=contents).json()

    mission_filename = urllib.parse.unquote(json_response["response"]["publishedfiledetails"][0]["filename"])

    mission_filename = re.sub(r'[^A-Za-z0-9\s\.]+', '', mission_filename)
    mission_filename = re.sub(r'\s+', '_', mission_filename)

    return mission_filename.lower()

def download_mission_file(mission_workshop_id, a3_workshop_dir, a3_workshop_id):
    workshop_download_path = os.path.join(a3_workshop_dir, mission_workshop_id)
    #if os.path.isdir(workshop_download_path):
    #    #TODO: delete, redownload and relink if dir and link already exists
    #    return 0

    command = ( f"steamcmd +login {steam_user} {steam_password} +force_install_dir {a3_server_dir} " 
                f"+workshop_download_item {a3_workshop_id} {mission_workshop_id} validate +quit" )
    
    print("Downloading mission with steamcmd...")
    os.system(command)

    downloaded_files = []

    if os.path.isdir(workshop_download_path):
        downloaded_files = os.listdir(workshop_download_path)

    if len(downloaded_files) == 1:
        mission_downloaded_filename = downloaded_files[0]
    else:
        mission_downloaded_filename = None
        print("Downloaded multiple files, please rename files manually. Exiting...")
        raise RuntimeError
        exit()

    return os.path.join(workshop_download_path, mission_downloaded_filename)

def create_symlinks(mission_downloaded_filepath, mission_filename, a3_mpmissions_dir):
    target_path =  mission_downloaded_filepath
    link_path = os.path.join(a3_mpmissions_dir, mission_filename)
    print(f"Creating symlink from {target_path} to {link_path}")
    os.symlink(target_path, link_path)

try:
    mission_workshop_id  = get_workshop_id_from_url(mission_workshop_url)
    mission_filename = get_mission_filename(mission_workshop_id)
    mission_downloaded_filepath = download_mission_file(mission_workshop_id, a3_workshop_dir, a3_workshop_id)
    create_symlinks(mission_downloaded_filepath, mission_filename, a3_mpmissions_dir)
except Exception as e:
    print(e)
    print("Failed to get mission. Is the url valid?")