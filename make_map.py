import os
import random
import subprocess

from PIL import Image
from utils import img as img_utils
from utils import genetic_algorithm as ga

from params import *

# Parameters for GA
NUM_OFFSPRINGS = 200
NUM_ITERATIONS = 2000
MUTATION_RATE = {
    0: 0.02,
    1: 0.1,
    2: 0.2,
    3: 0.5,
    4: 0.8,
}

TILE_SIZE = 128
N_X = 8
N_Y = 16 * 4

NUM_OUTPUTS = 10

DEFAULT_WEIGHT = 10

def construct_layer_1(
    n_x=N_X,
    n_y=N_Y,
    tile_size=TILE_SIZE,
    folder=FOLDER_LAYER1,
    weights=WEIGHTS_LAYER1,
    default_weight=DEFAULT_WEIGHT
):
    tiles = img_utils.get_tiles(folder)
    tiles_weights = img_utils.get_weights(tiles, weights, default_weight)

    # Construct dictionary to define tiles that can be merged.
    dict_mergeable = img_utils.get_dict_mergeable(tiles, tile_size)
    image_seed = img_utils.select_tile_by_weight(tiles, tiles_weights)

    # Initialize with all None's
    images = [[None] * n_x for i in range(n_y)]
    # For layer1, we simply grow the grid one by one.
    for y in range(n_y):
        for x in range(n_x):
            if x == 0 and y == 0:
                # When x == 0 and y == 0, we are at seed location.
                images[0][0] = image_seed
            else:
                left_image = img_utils.get_left_image(images, x, y)
                top_image = img_utils.get_top_image(images, x, y)
                found_image = img_utils.find_image(
                    tiles,
                    weights,
                    default_weight,
                    left_image,
                    top_image,
                    dict_mergeable
                )
                images[y][x] = found_image

    return images


def save_images(images, outfile, tile_size=TILE_SIZE, n_x=N_X, n_y=N_Y, prob_flip=0):
    result = img_utils.merge_all_images(images, tile_size, n_x, n_y, prob_flip)
    result.save(outfile)


def construct_layer_2(
    images_layer_1,
    folder=FOLDER_LAYER2,
    weights=WEIGHTS_LAYER2,
    default_weight=DEFAULT_WEIGHT,
    tile_size=TILE_SIZE,
    n_x=N_X,
    n_y=N_Y,
    num_offsprings=NUM_OFFSPRINGS,
    num_iterations=NUM_ITERATIONS,
    mutation_rate=MUTATION_RATE,
):
    tiles = img_utils.get_tiles(folder)
    tiles_weights = img_utils.get_weights(tiles, weights, default_weight)
    dict_mergeable = img_utils.get_dict_mergeable(tiles, tile_size)

    # Initialize second layer. If layer1 has a none-center tile, layer2 must be
    # empty.
    images = [[None] * n_x for i in range(n_y)]
    for y in range(n_y):
        for x in range(n_x):
            if not images_layer_1[y][x].endswith("center.png"):
                images[y][x] = os.path.join(folder, "empty.png")
            else:
                images[y][x] = img_utils.select_tile_by_weight(
                    tiles, tiles_weights
                )

    # Evolve.
    fitness = ga.get_fitness(images, dict_mergeable, n_x, n_y)
    num_iter = 0
    while fitness != 0 and num_iter < num_iterations:
        images = ga.get_best_offspring(
            tiles,
            tiles_weights,
            images,
            images_layer_1,
            dict_mergeable,
            mutation_rate,
            n_x,
            n_y,
            num_offsprings
        )
        fitness = ga.get_fitness(images, dict_mergeable, n_x, n_y)
        # print(fitness)
        num_iter += 1

    print(f"Total iteration for layer2: {num_iter}")

    if num_iter == num_iterations:
        return None
    else:
        return images


def save_background(
    outfile,
    file=FILE_BACKGROUND,
    tile_size=TILE_SIZE,
    n_x=N_X,
    n_y=N_Y
):
    images = [[file] * n_x for i in range(n_y)]
    result = img_utils.merge_all_images(images, tile_size, n_x, n_y)
    result.save(outfile)


def construct_object_layer(
    imgs_layer_1,
    imgs_layer_2,
    n_x=N_X,
    n_y=N_Y,
    objects=OBJECTS,
    objects_disallowed=OBJECTS_DISALLOWED,
):
    images = [[None] * n_x for i in range(n_y)]
    for y in range(n_y):
        for x in range(n_x):
            list_objs = []
            for obj, probs in objects.items():
                img_layer_1 = imgs_layer_1[y][x]
                img_layer_2 = imgs_layer_2[y][x]
                if not img_layer_2.endswith("empty.png") and img_layer_2 not in objects_disallowed:
                    prob = probs[2]
                elif img_layer_2.endswith("empty.png") and not img_layer_1.endswith("empty.png") and img_layer_1 not in objects_disallowed:
                    prob = probs[1]
                elif img_layer_2.endswith("empty.png") and img_layer_1.endswith("empty.png"):
                    prob = probs[0]
                else:
                    prob = 0

                if random.random() < prob:
                    list_objs.append(obj)

            if len(list_objs) > 0:
                images[y][x] = random.choice(list_objs)

    return images



if __name__ == "__main__":
    for i in range(NUM_OUTPUTS):
        imgs_layer_1 = construct_layer_1()
        imgs_layer_2 = construct_layer_2(imgs_layer_1)
        # Only continue if we can successfully construct layer 2.
        if imgs_layer_2 is not None:
            imgs_object_layer = construct_object_layer(
                imgs_layer_1, imgs_layer_2
            )
            # show_images(imgs_layer_1)

            save_images(imgs_layer_1, "layer1.png")
            save_images(imgs_layer_2, "layer2.png")
            save_images(imgs_object_layer, "object-layer.png", prob_flip=0.5)

            save_background("background.png")
            subprocess.run([
                "convert",
                "background.png",
                "layer1.png",
                "-composite",
                "layer2.png",
                "-composite",
                "object-layer.png",
                "-composite",
                f"./outputs/output_{i}.png"
            ])

    subprocess.run([
        "rm",
        "-f",
         "background.png",
         "layer1.png",
         "layer2.png",
         "object-layer.png"
    ])

