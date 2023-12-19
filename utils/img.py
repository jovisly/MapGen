import os
import random

from PIL import Image, ImageOps


def get_weights(tiles, weights, default_weight):
    return [
        weights[os.path.basename(t)]
        if os.path.basename(t) in weights else default_weight for t in tiles
    ]



def get_tiles(folder):
    tiles = os.listdir(folder)
    tiles = [os.path.join(folder, t) for t in tiles if t != ".DS_Store"]
    return tiles



def select_tile_by_weight(tiles, weights):
    return random.choices(tiles, weights=weights)[0]



def color_diff(c1, c2):
    total_diff = (
        abs(c1[0] - c2[0]) +
        abs(c1[1] - c2[1]) +
        abs(c1[2] - c2[2]) +
        abs(c1[3] - c2[3])
    )
    return total_diff / 4



def img_to_rgba(img, tile_size):
    result = Image.new('RGBA', (tile_size, tile_size))
    result.paste(im=img, box=(0, 0))
    return result



def is_mergeable_to_right(f1, f2, tile_size, thresh=0.03):
    """Determine if two images can be merged with img2 to the right of img1."""
    img1 = Image.open(f1)
    img2 = Image.open(f2)
    data1 = list(img_to_rgba(img1, tile_size).getdata())
    data2 = list(img_to_rgba(img2, tile_size).getdata())

    total_diff = 0
    for i in range(tile_size):
        p1 = data1[tile_size - 1 + tile_size * i]
        p2 = data2[tile_size * i]
        total_diff += color_diff(p1, p2)

    avg_diff = (total_diff / tile_size) / 255
    if avg_diff > thresh:
        return False
    else:
        return True


def is_mergeable_to_bottom(f1, f2, tile_size, thresh=0.02):
    """Determine if two images can be merged with img2 to the bottom of img1."""
    img1 = Image.open(f1)
    img2 = Image.open(f2)
    data1 = list(img_to_rgba(img1, tile_size).getdata())
    data2 = list(img_to_rgba(img2, tile_size).getdata())

    total_diff = 0
    for i in range(tile_size):
        p1 = data1[tile_size * (tile_size - 1) + i]
        p2 = data2[i]
        total_diff += color_diff(p1, p2)

    avg_diff = (total_diff / tile_size) / 255
    if avg_diff > thresh:
        return False
    else:
        return True


def get_dict_mergeable(tiles, tile_size):
    """Given a list of tiles, construct dictionary on how they can merge."""
    dict_mergeable = {}
    for tk in tiles:
        list_mergeable_right = [
            tv for tv in tiles if is_mergeable_to_right(tk, tv, tile_size)
        ]
        list_mergeable_bottom = [
            tv for tv in tiles if is_mergeable_to_bottom(tk, tv, tile_size)
        ]

        dict_mergeable[tk] = {
            "right": list_mergeable_right,
            "bottom": list_mergeable_bottom
        }

    return dict_mergeable



def is_mergeable_to_bottom_with_dict(f1, f2, dict_mergeable):
    if f2 in dict_mergeable[f1]["bottom"]:
        return True
    else:
        return False



def is_mergeable_to_right_with_dict(f1, f2, dict_mergeable):
    if f2 in dict_mergeable[f1]["right"]:
        return True
    else:
        return False



def merge_all_images(images, tile_size, n_x, n_y, prob_flip=0):
    result = Image.new('RGBA', (tile_size * n_x, tile_size * n_y))

    for y in range(n_y):
        for x in range(n_x):
            if images[y][x] is not None:
                img = Image.open(images[y][x]).convert("RGBA")
                if random.random() < prob_flip:
                    img = ImageOps.mirror(img)
                result.paste(im=img, box=(tile_size * x, tile_size * y), mask=img)

    return result




def get_left_image(images, x, y):
    if x == 0:
        return None
    else:
        return images[y][x - 1]


def get_top_image(images, x, y):
    if y == 0:
        return None
    else:
        return images[y-1][x]


def find_image(
    tiles, weights, default_weight, left_image, top_image, dict_mergeable
):
    found = False
    if top_image == None:
        allowed_images_by_top = tiles
    else:
        allowed_images_by_top = dict_mergeable[top_image]["bottom"]

    if left_image == None:
        allowed_images_by_left = tiles
    else:
        allowed_images_by_left = dict_mergeable[left_image]["right"]

    allowed_images = [
        i for i in allowed_images_by_top if i in allowed_images_by_left
    ]
    allowed_images_weights = get_weights(
        allowed_images, weights, default_weight
    )

    return random.choices(allowed_images, weights=allowed_images_weights)[0]

