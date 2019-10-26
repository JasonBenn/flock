from django.core.management.base import BaseCommand
from tqdm import tqdm

from flock.algorithm import get_location_to_people
from flock.models import GroundTruth


class Command(BaseCommand):
    def handle(self, *args, **options):
        correct = []
        incorrect = []
        for truth in tqdm(GroundTruth.objects.all()):
            location_to_people = get_location_to_people(truth.created_at, True)
            # print("Looking for:", truth.person, truth.location)
            # print("Found:", location_to_people)
            if location_to_people.get(truth.person) == truth.location:
                correct.append(truth)
            else:
                incorrect.append(truth)
        print(len(correct), len(incorrect))
