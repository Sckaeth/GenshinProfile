from math import sqrt
from PIL import Image, ImageDraw, ImageFont, ImageChops
import cv2
import numpy as np


# Gets the most dominant colour in an image, but slightly darkened for improved contrast.
def get_colour(image):
    image = image.resize((image.size[0]//8, image.size[1]//8), resample=Image.Resampling.LANCZOS)
    image = np.array(image)[:, :, :-1]
    pixels = np.float32(image.reshape(-1, 3))
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 200, .1)

    empty_var, labels, palette = cv2.kmeans(pixels, 5, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
    empty_var, counts = np.unique(labels, return_counts=True)

    counts[np.argmax(counts)] = 0
    dominant = palette[np.argmax(counts)]

    # If any colours are very close to black or white, the next dominant colour is picked.
    while all(rgb_value >= 240 for rgb_value in dominant) or all(rgb_value <= 20 for rgb_value in dominant):
        counts[np.argmax(counts)] = 0
        dominant = palette[np.argmax(counts)]

    # If the dominant colour is bright, it is lowered by 20 RGB points.
    # If it is dark, it is brightened by 20 RGB points.
    dominant -= 20
    if np.average(dominant) <= 127.5:
        dominant += 30

    return tuple(dominant)


# Generates a line, with its colour set as a gradient, that has rounded edges.
# Rounded edges work for most small widths.
# Breaks on any widths above 8 or on any diagonal lines.
def add_gradient_line(image, start_colour, end_colour, loc, width):
    draw = ImageDraw.Draw(image)

    # Finds if any horizontal or vertical changes occur.
    horizontal = 0 if loc[2] - loc[0] == 0 else 1
    vertical = 0 if loc[3] - loc[1] == 0 else 1

    # Calculates the values to shift the circles by.
    h_shift = width/2
    v_shift = 1 if width - 5 < 0 else 0
    v_shift = -1 if width - 6 > 0 else v_shift

    # Draws two ellipses for rounded edges.
    draw.ellipse((loc[0] - 2 + (v_shift * vertical), loc[1] - h_shift + 1, loc[0] + h_shift, loc[1] + h_shift),
                 fill=tuple(start_colour))
    draw.ellipse((loc[2] - 2 + (v_shift * vertical), loc[3] - h_shift + 1, loc[2] + h_shift, loc[3] + h_shift),
                 fill=tuple(end_colour))

    # Finds the RGB values to step by for each pixel.
    line_length = int(sqrt((loc[2] - loc[0])**2 + (loc[3] - loc[1])**2))
    step_colour = [(start_rgb - end_colour[index])/line_length for index, start_rgb in enumerate(start_colour)]

    # Iterates through every pixel to draw it in.
    current_colour = start_colour
    for pixel in range(0, line_length):
        current_colour = [current_colour[index] - step_colour[index] for index in range(0, 3)]

        pixel_h = pixel * horizontal
        pixel_v = pixel * vertical

        draw.line((loc[0] + pixel_h, loc[1] + pixel_v,  loc[0] + horizontal + pixel_h, loc[1] + vertical + pixel_v),
                  fill=tuple(map(int, current_colour)),
                  width=width)


# Draws a circle with the specified parameters.
def draw_circle(mode, fill, outline, width, size, alpha=255):
    # The size is initially set to 3x the requested size so that smoother curves can be created.
    large_size = (size[0] * 3, size[1] * 3)
    circle = Image.new(mode, large_size)

    draw = ImageDraw.Draw(circle)
    draw.ellipse((0, 0) + large_size, fill=fill, outline=outline, width=width)
    circle = circle.resize(size, resample=Image.Resampling.LANCZOS)

    # If the opacity needs to be changed, it is changed if the mode is compatible.
    if mode != 'L' and alpha < 255:
        new_alpha = circle.getchannel('A')
        new_alpha = new_alpha.point(lambda a_value: alpha if a_value > 0 else 0)

        circle.putalpha(new_alpha)

    return circle


# Draws a designated object a given amount of times, with an input horizontal and vertical offset.
# offset -> [0] is h_offset, [1] is v_offset
# object_num -> [0] is maximum object, [1] is maximum object per row
def draw_multi(image, icon, alpha, loc, size, object_num, offset):
    # Reduces the opacity of the input icon, if required.
    if alpha < 255:
        new_alpha = icon.getchannel('A')
        new_alpha = new_alpha.point(lambda a_value: 64 if a_value > 1 else 0)
        icon.putalpha(new_alpha)

    # Resizes the input shadow image to the requested size.
    icon = icon.resize(size, resample=Image.Resampling.LANCZOS)

    # Initialises the offset values.
    h_offset = -offset[0]
    v_offset = 0
    for item in range(0, object_num[0]):
        # Calculates the offset based on the current circle number.
        h_offset += offset[0]
        if item != 0 and item % object_num[1] == 0:
            h_offset = 0
            v_offset += offset[1]

        # Calculates the new location based on the offsets given.
        new_loc = (loc[0] + h_offset, loc[1] + v_offset)

        # Pastes the object to the required location.
        image.paste(icon, new_loc, icon)


# Draws a designated circle a given amount of times, with a given horizontal and vertical offset.
# A number of circles per row must also be specified.
# offset -> [0] is h_offset, [1] is v_offset
# circle_num -> [0] is maximum circles, [1] is maximum circles per row
def draw_multi_c(image, icon, bg_colour, border_colour, alpha, width, loc, size, circle_num, offset, d_shadow=False):
    # Draws a circle with the requested parameters.
    circle = draw_circle('RGBA', bg_colour, border_colour, width, icon.size, alpha)

    # Creates a drop-shadow if one is needed.
    if d_shadow:
        shadow = draw_circle('RGBA', '#000000', 0, 20, icon.size, 64)
        shadow = shadow.resize((size[0] + 6, size[1]), resample=Image.Resampling.LANCZOS)

    # Resizes the circle to the input size.
    circle = circle.resize(size, resample=Image.Resampling.LANCZOS)

    # Initialises the offset values.
    h_offset = -offset[0]
    v_offset = 0
    for item in range(0, circle_num[0]):
        # Calculates the offset based on the current circle number.
        h_offset += offset[0]
        if item != 0 and item % circle_num[1] == 0:
            h_offset = 0
            v_offset += offset[1]

        # Calculates the new location based on the offsets given.
        new_loc = (loc[0] + h_offset, loc[1] + v_offset)

        # Pastes the circle and a shadow, if required, to the required location.
        if d_shadow:
            image.paste(shadow, (new_loc[0] - 3, new_loc[1] + 5), shadow)
        image.paste(circle, new_loc, circle)


# Adds an icon to the image. If a drop-shadow is required, it is added.
def add_icon(image, icon, loc, size, d_shadow=None):
    # Adds a drop-shadow if it is requested.
    if d_shadow is not None:
        # Reduces the opacity of the shadow image.
        new_alpha = d_shadow.getchannel('A')
        new_alpha = new_alpha.point(lambda a_value: 64 if a_value > 1 else 0)
        d_shadow.putalpha(new_alpha)

        # Resizes the input shadow image to the requested size.
        d_shadow = d_shadow.resize(size, resample=Image.Resampling.LANCZOS)
        image.paste(d_shadow, (loc[0], loc[1] + 5), d_shadow)

    icon = icon.resize(size, resample=Image.Resampling.LANCZOS)
    image.paste(icon, loc, icon)


# Places a circular icon without any background, border or shadows.
# This is typically used in conjunction with draw_multi_c() to improve efficiency.
def add_icon_c(image, icon, loc, size):
    # Resizes the icon to a smaller size.
    icon = icon.resize(size, resample=Image.Resampling.LANCZOS)

    # Converts the icon to a rounded image.
    mask = draw_circle('L', 255, 255, 0, icon.size)
    mask = ImageChops.darker(mask, icon.split()[-1])
    icon.putalpha(mask)

    # Places the icon on the background image.
    image.paste(icon, loc, icon)


# Adds a circular icon to the image. Adds a drop-shadow if needed.
# This is a function for icons with borders.
def add_icon_cf(image, icon, bg_colour, border_colour, alpha, width, loc, size, d_shadow=False):
    # Generates a background and border.
    icon_bg = draw_circle('RGBA', bg_colour, 0, 0, icon.size, alpha)
    border = draw_circle('RGBA', 0, border_colour, width, icon.size)

    # Creates a drop-shadow if one is needed.
    if d_shadow:
        shadow = draw_circle('RGBA', '#000000', 0, width, icon.size, 64)

    # Resizes the icon (and everything else) to the input size.
    icon_bg = icon_bg.resize(size, resample=Image.Resampling.LANCZOS)
    icon = icon.resize(size, resample=Image.Resampling.LANCZOS)
    border = border.resize(size, resample=Image.Resampling.LANCZOS)

    # Converts the icon to a rounded image.
    mask = draw_circle('L', 255, 255, 0, icon.size)
    mask = ImageChops.darker(mask, icon.split()[-1])
    icon.putalpha(mask)

    # Places a drop-shadow if one is requested.
    if d_shadow:
        shadow = shadow.resize((size[0] + 6, size[1]), resample=Image.Resampling.LANCZOS)
        image.paste(shadow, (loc[0] - 3, loc[1] + 5), shadow)

    # Places the icon on the background image.
    image.paste(icon_bg, loc, icon_bg)
    image.paste(icon, loc, icon)
    image.paste(border, loc, border)


# Draws any input text at the given parameters.
def add_text(image, colour, text, loc, size, font='./assets/zh-cn.ttf'):
    draw = ImageDraw.Draw(image)

    # Draws the text.
    font = ImageFont.truetype(font, size=size)
    draw.text(loc, text, fill=colour, font=font)


# Draws the user statistics.
def draw_statistics(image, user_info):
    offset = -50
    info_names = {'rank': 'Adventure Rank', 'abyss': 'Spiral Abyss', 'achievements': 'Achievements'}

    # Finds the maximum length of the values.
    max_len = 0
    for key in info_names:
        value_len = len(user_info[key])
        if value_len > max_len:
            max_len = value_len

    # Iterates through the statistics to draw them into the image.
    for key in info_names:
        offset += 50
        value = user_info[key]
        name = info_names[key]

        add_text(image, '#F0D6A9', name, (35, 230 + offset), 15)

        # Offsets the value with spaces to right-align them all.
        value = ("  " * (max_len - len(value))) + value
        add_text(image, '#F0D6A9', value, (170, 230 + offset), 15)


# Draws either the characters or namecards showcase.
def draw_showcase(image, s_type, showcase):
    v_offset = 0
    if s_type == 'namecards':
        # Initialises the showcase to Nones, if it is empty, so that we can print empty objects instead of nothing.
        if len(showcase) == 0:
            showcase = [None] * 9

        # If the amount of namecards is under 9, extra namecards initialised as None are added to add empty slots.
        if len(showcase) < 9:
            showcase += [None] * (9 - len(showcase))

        # Draws a shadow on all the namecard locations beforehand. This is to save time.
        d_shadow = Image.open(f"./assets/namecard_icon_shadow.png").convert('RGBA')
        draw_multi(image, d_shadow, 64, (320, 170), (96, 96), [9, 3], [173, 70])

        h_offset = -173
        for count in range(0,9):
            namecard = showcase[count]
            h_offset += 173
            if count != 0 and count % 3 == 0:
                h_offset = 0
                v_offset += 70

            # If the entire showcase is empty, we use a placeholder namecard icon instead.
            if namecard is None:
                icon = Image.open(f"./assets/images/UI_NameCardIcon_0.png")
            else:
                icon = Image.open(f"./assets/images/{namecard}.png")
            add_icon(image, icon, (320 + h_offset, 165 + v_offset), (96, 96))

    if s_type == 'characters':
        # Opens a dummy icon and draws every background and shadow first. This is to save time.
        d_icon = Image.open(f"./assets/images/UI_AvatarIcon_PlayerBoy.png")
        draw_multi_c(image, d_icon, '#9c8c72', 0, 255, 0, (300, 180), (96, 96), [9, 4], [130, 110], True)

        h_offset = -130
        for count, character in enumerate(showcase):
            h_offset += 130
            if count == 4:
                h_offset = 0
                v_offset = 110

            # If the entire showcase is empty, we skip the current character.
            if len(showcase) == 0:
                continue

            icon = Image.open(f"./assets/images/{character}.png")
            add_icon_c(image, icon, (300 + h_offset, 180 + v_offset), (96, 96))

        draw_multi_c(image, d_icon, 0, '#F0D6A9', 255, 20, (300, 180), (96, 96), [9, 4], [130, 110])


# Generates a profile for a user based on the given parameters.
def generate_profile(user_info, user_icon, namecard, showcase):
    profile_card = Image.open(f"./assets/images/{namecard}.png")
    user_icon = Image.open(f"./assets/images/{user_icon}.png")

    # Darkens entire namecard image.
    profile_card = profile_card.point(lambda colour: colour * 0.6)

    # Rounds the corners on the namecard.
    namecard_mask = Image.open('./assets/namecard_mask.png')
    namecard_mask = namecard_mask.convert('L')
    profile_card.putalpha(namecard_mask)

    # Draws the username and signature.
    # Signatures have a maximum length of 50, so we split them into two lines on the 26th character.
    signature = user_info['signature']
    if len(signature) > 25:
        signature = signature[:26] + '\n' + signature[26:]
    add_text(profile_card, '#CCB998', user_info['username'], (238, 50), 40)
    add_text(profile_card, '#A8977B', signature, (250, 110), 17)

    # Draws the user statistics.
    draw_statistics(profile_card, user_info)
    add_gradient_line(profile_card, [255, 255, 255], [240, 214, 169], (35, 365,  75, 365), 3)
    add_gradient_line(profile_card, [255, 255, 255], [240, 214, 169], (240, 110, 240, 150), 3)

    # Draws the user's main icon.
    bg_colour = get_colour(user_icon)
    add_icon_cf(profile_card, user_icon, bg_colour, '#F0D6A9', 255, 15, (40, 30), (160, 160))

    # Generates the showcase for namecards or characters.
    if showcase[0] != "":
        add_text(profile_card, '#F0D6A9', showcase[0].capitalize(), (695, 133), 15)
        add_gradient_line(profile_card, [255, 255, 255], [240, 214, 169], (697, 160, 780, 160), 3)
        draw_showcase(profile_card, showcase[0], showcase[1])

    # Draws the Genshin Impact logo in the top right.
    image = Image.open("./assets/genshin_impact_logo.png").convert("RGBA")
    image = image.resize((86, 31), resample=Image.Resampling.LANCZOS)
    profile_card.paste(image, (735, 15), image)

    return profile_card
