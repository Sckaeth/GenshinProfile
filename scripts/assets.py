import requests, json
from os import path

json_urls = ["https://raw.githubusercontent.com/Dimbreath/GenshinData/master/ExcelBinOutput/AvatarExcelConfigData.json",
             "https://raw.githubusercontent.com/Dimbreath/GenshinData/master/ExcelBinOutput/AvatarCostumeExcelConfigData.json",
             "https://raw.githubusercontent.com/Dimbreath/GenshinData/master/ExcelBinOutput/MaterialExcelConfigData.json"]


# Checks if an image exists in the assets folder.
def check_file(file_name):
    return path.exists(f"./assets/images/{file_name}")


# Downloads a file from a given URL.
# The file is placed into a different location based on the input file type.
def download_file(file_type, url):
    response = requests.get(url)
    filepath = f"./assets/{file_type}/{url.split('/')[-1]}"
    open(filepath, "wb").write(response.content)


# Generates a JSON file containing every character and, if any exist, their associated costumes.
# Any assets that are not local already are downloaded.
def generate_characters():
    filepath = "./assets/json"
    avatars_json = json.load(open(f"{filepath}/AvatarExcelConfigData.json", "r"))
    costumes_json = json.load(open(f"{filepath}/AvatarCostumeExcelConfigData.json", "r"))
    characters = {}

    for character in avatars_json:
        # If the avatar_id is 10000001 it is not a valid character.
        avatar_id = character['featureTagGroupID']
        if avatar_id == 10000001:
            continue

        # Downloads any files that haven't already been downloaded.
        icon_name = f"{character['iconName']}.png"
        if not check_file(icon_name):
            download_file("images", f"https://enka.shinshin.moe/ui/{icon_name}")

        characters[avatar_id] = {'iconName': icon_name, 'costumes': {}}

    for costume in costumes_json:
        file_name = costume['FOINIGFDKIP']
        if file_name == "":
            continue

        avatar_id = costume['FMAJGGBGKKN']
        costume_id = costume['GMECDCKBFJM']
        characters[avatar_id]['costumes'][costume_id] = {'iconName': file_name}

    with open(f'{filepath}/Characters.json', 'w') as file:
        json.dump(characters, file, ensure_ascii=False, indent=4)


# Generates a JSON file containing every namecard.
# Any assets that are not local already are downloaded.
def generate_namecards():
    filepath = "./assets/json"
    materials_json = json.load(open(f"{filepath}/MaterialExcelConfigData.json", "r"))
    namecards = {}

    for material in materials_json:
        # Skip any materials that are not a namecard or have no materialType property.
        if "materialType" not in material:
            continue

        material_type = material['materialType']
        if material_type != "MATERIAL_NAMECARD":
            continue

        icon_name = f"{material['icon']}.png"
        image_name = f"{material['picPath'][1]}.png"

        if not check_file(icon_name):
            download_file("images", f"https://enka.shinshin.moe/ui/{icon_name}")
            print(icon_name)
        if not check_file(image_name):
            download_file("images", f"https://enka.shinshin.moe/ui/{image_name}")
            print(image_name)

        material_id = material['id']
        namecards[material_id] = {'iconName': icon_name, 'imageName': image_name}

    with open(f'{filepath}/Namecards.json', 'w') as file:
        json.dump(namecards, file, ensure_ascii=False, indent=4)

# Generates JSON files used by the application by simplifying pre-existing ones.
# Referenced assets that are not available locally are downloaded.
# Pre-existing JSONs sourced from https://github.com/Dimbreath/GenshinData/
def generate_json():
    # Downloads any required JSON files.
    for url in json_urls:
        download_file("json", url)

    # Generates a JSON file for characters.
    generate_characters()
    # Generates a JSON file for namecards.
    generate_namecards()


if __name__ == '__main__':
    generate_json()
