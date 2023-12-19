import copy
import random

from utils import img as img_utils



def get_mutation(tiles, tiles_weights, image_names, x, y):
    """Get preferential mutation of a tile."""
    image_name = image_names[y][x]
    i = [ind for ind, tile in enumerate(tiles) if tile == image_name][0]
    tiles_filterd = [tile for ind, tile in enumerate(tiles) if ind != i]
    weights_filterd = [w for ind, w in enumerate(tiles_weights) if ind != i]

    return random.choices(tiles_filterd, weights=weights_filterd)[0]



def get_offspring(
    tiles, tiles_weights, image_names, image_names_lower_layer, dict_mergeable, mutation_rate, n_x, n_y
):
    """Generate one offspring."""
    new_image_names = copy.deepcopy(image_names)
    for y in range(n_y):
        for x in range(n_x):
            if image_names_lower_layer[y][x].endswith("center.png"):
                # Can only mutate places where there's foundation in the lower
                # level.
                penalty = get_penalty(image_names, x, y, dict_mergeable, n_x, n_y)
                if random.random() < mutation_rate[penalty]:
                    new_image_names[y][x] = get_mutation(
                        tiles, tiles_weights, image_names, x, y
                    )

    return new_image_names



def get_best_offspring(
    tiles, tiles_weights, image_names, image_names_lower_layer, dict_mergeable, mutation_rate, n_x, n_y, num_offsprings
):
    offsprings = [
        get_offspring(
            tiles, tiles_weights, image_names, image_names_lower_layer, dict_mergeable, mutation_rate, n_x, n_y
        ) for _ in range(num_offsprings)
    ]
    fitness = [get_fitness(o, dict_mergeable, n_x, n_y) for o in offsprings]
    max_fitness = max(fitness)
    offsprings_with_max_fitness = [
        o for o, f in zip(offsprings, fitness) if f == max_fitness
    ]
    return random.choice(offsprings_with_max_fitness)



def get_fitness(image_names, dict_mergeable, n_x, n_y):
    total_penalty = 0
    for y in range(n_y):
        for x in range(n_x):
            total_penalty += get_penalty(
                image_names, x, y, dict_mergeable, n_x, n_y
            )

    return -1 * total_penalty


def get_penalty(image_names, x, y, dict_mergeable, n_x, n_y):
    nn_t = None if y == 0 else image_names[y - 1][x]
    nn_b = None if y == n_y - 1 else image_names[y + 1][x]
    nn_l = None if x == 0 else image_names[y][x - 1]
    nn_r = None if x == n_x - 1 else image_names[y][x + 1]

    img = image_names[y][x]
    penalty = 0
    if nn_t != None and img_utils.is_mergeable_to_bottom_with_dict(
        nn_t, img, dict_mergeable
    ) == False:
        penalty += 1

    if nn_b != None and img_utils.is_mergeable_to_bottom_with_dict(
        img, nn_b, dict_mergeable
    ) == False:
        penalty += 1

    if nn_l != None and img_utils.is_mergeable_to_right_with_dict(
        nn_l, img, dict_mergeable
    ) == False:
        penalty += 1

    if nn_r != None and img_utils.is_mergeable_to_right_with_dict(
        img, nn_r, dict_mergeable
    ) == False:
        penalty += 1

    return penalty
