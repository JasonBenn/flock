from datetime import timedelta

from django.core.management.base import BaseCommand
from tqdm import tqdm

from flock.algorithm import get_location_to_people
from flock.models import GroundTruth


class Command(BaseCommand):
    def handle(self, *args, **options):
        correct = []
        incorrect = []
        for truth in tqdm(GroundTruth.objects.all()):
            location_to_people = get_location_to_people(truth.created_at + timedelta(minutes=5), True)
            if truth.fixed_at or truth.person in location_to_people.get(truth.location, []):
                correct.append(truth)
            else:
                incorrect.append(truth)
        print(f"{len(correct) / len(correct + incorrect)*100:.0f}% correct! ({len(correct)}/{len(incorrect)})")
