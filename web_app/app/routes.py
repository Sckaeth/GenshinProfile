from flask import send_file, request, render_template, send_from_directory, json
from app import app
from app.api import profiles
import cloudscraper
from io import BytesIO
import time


# Sends the profile card based on the input parameters.
def send_image(user_info, user_icon, namecard, showcase, bg_colour, size):
    start = time.process_time()
    image = profiles.generate_profile(user_info, user_icon, namecard, showcase, bg_colour, size)

    image_out = BytesIO()
    image.save(image_out, 'PNG')
    image_out.seek(0)

    return send_file(image_out, mimetype='image/png')


# Sends a placeholder error image if any invalid parameters are entered.
def send_error_image(showcase):
    if showcase == "":
        showcase = "profile"

    return send_file(f"error_{showcase}.png", mimetype="image/png")


# Gets the filename required for images based on their file type and IDs.
def get_filename(f_type, f_ids, i_type):
    # Sets the identifier to grab the names from.
    if i_type == "icon":
        identifier = 'iconName'
    if i_type == "image":
        identifier = 'imageName'

    # Gets the json required based on the input file type.
    filepath = "./app/api/assets/json"
    if f_type == "characters":
        data_json = json.load(open(f"{filepath}/Characters.json", "r"))
    if f_type == "namecards":
        data_json = json.load(open(f"{filepath}/Namecards.json", "r"))

    # Stores the icon names into a list by iterating through the input file IDs.
    data_list = []
    for f_id in f_ids:
        # If the length of f_id is over 1, it contains a costume ID too.
        if f_id[0] in data_json:
            if len(f_id) > 1:
                data = data_json[f_id[0]]['costumes'][f_id[1]]
            else:
                data = data_json[f_id[0]]

            # Appends the icon's name into the list.
            data_list.append(str(data[identifier]))

        else:
            if f_type == "characters":
                data_list.append("UI_AvatarIcon_PlayerBoy")
            if f_type == "namecards":
                if i_type == "icon":
                    data_list.append("UI_NameCardIcon_0")
                if i_type == "image":
                    data_list.append("UI_NameCardPic_0_P")

    return data_list


# Generates a profile card for users if they enter the following parameters:
# userid -> the user's Genshin Impact UserID.
# showcase -> 'characters' or 'namecards' or '' for the type of showcase the user wants.
# icon -> the colour the user wants to use for their main icon, this is set to the most dominant colour if empty.
@app.route('/genshin', methods=['GET'])
def get_profile():
    # Gets the three parameters from the request to the website.
    userid = request.args.get('userid', '')
    showcase = request.args.get('showcase', '')
    bg_colour = request.args.get('icon', '')
    size = request.args.get('size', '1')

    # If the showcase's value is not valid, the user is redirected elsewhere.
    if showcase not in ['characters', 'namecards', '']:
        return send_error_image('')
    # If an invalid userid is entered, the user is redirected elsewhere.
    if len(userid) != 9 or not userid.isnumeric():
        return send_error_image(showcase)
    # Converts the size to a float if it is possible.
    try:
        size = float(size)
    except ValueError:
        return send_error_image(showcase)
    if size > 1 or size <= 0:
        return send_error_image(showcase)

    # Adds a hashtag to the input colour value.
    bg_colour = "#" + bg_colour

    # Gets the user's data from the Enka Network API. If the user does not exist, the user is redirected elsewhere.
    user_data = cloudscraper.create_scraper(browser={'browser': 'firefox','platform': 'windows','mobile': False})
    user_data = user_data.get(f"https://enka.shinshin.moe/u/{userid}/__data.json").json()
    if 'playerInfo' not in user_data:
        return send_error_image(showcase)
    user_data = user_data['playerInfo']

    # Grabs the player's user icon and namecard names.
    if 'avatarId' not in user_data['profilePicture'] or 'nameCardId' not in user_data:
        return send_error_image(showcase)

    user_icon = user_data['profilePicture']
    user_icon['avatarId'] = [str(user_icon['avatarId'])]

    # The icon for a skin is used if the user is using a skin in their icon.
    if 'costumeId' in user_icon:
        user_icon['avatarId'].append(str(user_icon['costumeId']))

    user_icon = get_filename('characters', [user_icon['avatarId']], "icon")[0]
    namecard = get_filename('namecards', [[str(user_data['nameCardId'])]], "image")[0]

    # Gets the showcase icon names based on the input showcase type.
    showcase = (showcase, [])
    if not showcase[0] == "":
        if showcase[0] == "namecards":
            if "showNameCardIdList" in user_data:
                showcase_list = user_data["showNameCardIdList"]
                for count, data in enumerate(showcase_list):
                    showcase_list[count] = [str(data)]
            else:
                showcase_list = []
        if showcase[0] == "characters":
            if "showAvatarInfoList" in user_data:
                showcase_list = user_data["showAvatarInfoList"]
                for count, data in enumerate(showcase_list):
                    showcase_list[count] = [str(data['avatarId'])]
                    if 'costumeId' in data:
                        showcase_list[count].append(str(data['costumeId']))
            else:
                showcase_list = []

        showcase = (showcase[0], get_filename(showcase[0], showcase_list, "icon"))

    # If the following values aren't defined, they are replaced with a placeholder value.
    user_info = {'username': '?',
                 'signature': '(No signature)',
                 'rank': '?',
                 'abyss': '?',
                 'achievements': '?'}
    if 'nickname' in user_data:
        user_info['username'] = user_data['nickname']
    if 'signature' in user_data:
        user_info['signature'] = user_data['signature']
    if 'level' in user_data:
        user_info['rank'] = str(user_data['level'])
    if 'towerFloorIndex' in user_data:
        user_info['abyss'] = str(user_data['towerFloorIndex']) + "-" + str(user_data['towerLevelIndex'])
    if 'finishAchievementNum' in user_data:
        user_info['achievements'] = str(user_data['finishAchievementNum'])

    return send_image(user_info, user_icon, namecard, showcase, bg_colour, size)


@app.route('/')
def main_page():
    return render_template('index.html')