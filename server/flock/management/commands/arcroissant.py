import datetime
import random
from typing import List, Optional

from django.core.management.base import BaseCommand
from pgspecial.main import chunks

from flock.models import Floor
from flock.models import Person
from flock.utils import group_by, post_slack, squeeze_values

Group = List[Person]


def couple_in_same_group(group: Group) -> Optional[Person]:
    grouped_by_rooms = group_by(group, lambda x: x.room).values()
    return next((x for x in grouped_by_rooms if len(x) > 1), None)


def swap_groups(group_a: Group, group_a_person: Person, group_b: Group, group_b_person: Person):
    group_a.pop(group_a.index(group_a_person))
    group_b.pop(group_b.index(group_b_person))
    group_a.append(group_b_person)
    group_b.append(group_a_person)


def get_random_groups(n=4) -> List[Group]:
    people = list(Person.objects.exclude(floor=Floor.NOT_HOUSEMATE).exclude(active=False))
    random.shuffle(people)
    groups = [people[x : x + n] for x in range(0, len(people), n)]

    # Balance groups.
    while max([len(x) for x in groups]) - min([len(x) for x in groups]) > 1:
        group_lengths = [len(x) for x in groups]
        max_group = next(x for x in groups if len(x) == max(group_lengths))
        min_group = next(x for x in groups if len(x) == min(group_lengths))
        min_group.append(max_group.pop())

    # Swap people in the same room.
    couples = squeeze_values({i: couple_in_same_group(x) for (i, x) in enumerate(groups)})
    print(f"{len(couples)} couples")
    if len(couples) % 2 == 1:
        random_group_index = next(iter(set(range(len(groups))) - set(couples.keys())))
        couples[random_group_index] = groups[random_group_index][:2]

    for (group_a_index, group_b_index) in chunks(list(couples.keys()), 2):
        print("Swapping...")
        person_a = couples[group_a_index][0]
        person_b = couples[group_b_index][0]
        swap_groups(groups[group_a_index], person_a, groups[group_b_index], person_b)

    return groups


emojis = [
    "grapes",
    "melon",
    "watermelon",
    "strawberry",
    "tangerine",
    "lemon",
    "banana",
    "pineapple",
    "potato",
    "bread",
    "carrot",
    "pretzel",
    "pancakes",
    "cheese_wedge",
    "hotdog",
    "cookie",
    "bacon",
    "mushroom",
    "burrito",
    "taco",
    "cut_of_meat",
    "eggplant",
    "popcorn",
    "pizza",
    "canned_food",
    "custard",
    "honey_pot",
    "beer",
    "tropical_drink",
    "candy",
]


def get_random_emojis(n) -> List[str]:
    random.shuffle(emojis)
    return emojis[:n]


class Command(BaseCommand):
    def handle(self, *args, **options):
        week = int(datetime.date.today().strftime("%V"))

        if week % 2 == 0:
            groups = get_random_groups(2)
        else:
            groups = get_random_groups(4)

        group_strs = [", ".join([person.name for person in group]) for group in groups]
        group_str = "\n".join(
            [f":{emoji}: {group_str}" for emoji, group_str in zip(get_random_emojis(len(groups)), group_strs)]
        )
        post_slack(
            f"Happy Archive Day! Arcroissant groups this week:\n\n{group_str}", "general", "Arcroissant", "croissant"
        )
