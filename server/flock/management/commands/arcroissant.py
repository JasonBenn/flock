import datetime
import random
from typing import List

from django.core.management.base import BaseCommand

from flock.models import Floor
from flock.models import Person
from flock.utils import post_slack


def get_random_groups(n=4) -> List[List[Person]]:
    people = list(Person.objects.exclude(floor=Floor.NOT_HOUSEMATE).exclude(active=False))
    random.shuffle(people)
    groups = [people[x : x + n] for x in range(0, len(people), n)]

    # Balance groups.
    while max([len(x) for x in groups]) - min([len(x) for x in groups]) > 1:
        group_lengths = [len(x) for x in groups]
        max_group = next(x for x in groups if len(x) == max(group_lengths))
        min_group = next(x for x in groups if len(x) == min(group_lengths))
        min_group.append(max_group.pop())

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
