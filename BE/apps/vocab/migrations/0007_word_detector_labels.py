"""Words the detector now recognises (AI/classes.yaml `extra`, served by the pretrained Open Images model): their
yolo_label, as in BE/seed/concepts/words.csv. Only the label changes, translations stay as reviewed."""
from django.db import migrations

SAME = """flower tree mushroom pumpkin grape mango lemon pear peach potato cucumber coconut milk coffee tea juice beer
cheese candy cookie hamburger salad shrimp crab fish bee ant ladybug snail spider snake lizard frog turtle
crocodile dinosaur penguin owl parrot eagle swan goose kangaroo deer fox goat camel panda squirrel hedgehog
leopard rhinoceros dolphin whale shark jellyfish starfish taxi ambulance helicopter rocket house stairs tent
flag shirt pants jeans shorts skirt dress suit coat jacket shoes boots sandals socks scarf belt gloves face hair
eye ear nose mouth hand arm leg foot desk bookshelf wardrobe drawer curtain mirror towel plate kettle candle fan
box envelope coin balloon doll hammer ladder flashlight eraser ruler calculator tablet camera headphones printer
football volleyball guitar piano violin drum flute""".split()
LABELS = {**{s: s for s in SAME}, "ice-cream": "ice cream", "french-fries": "french fries",
          "mouse-animal": "mouse animal", "hippo": "hippopotamus", "swimming-pool": "swimming pool",
          "high-heels": "high heels", "light-bulb": "light bulb", "washing-machine": "washing machine",
          "seat-belt": "seat belt"}


def forwards(apps, schema_editor):
    Word = apps.get_model("vocab", "Word")
    for slug, label in LABELS.items():
        Word.objects.filter(slug=slug, yolo_label="").update(yolo_label=label)


def backwards(apps, schema_editor):
    Word = apps.get_model("vocab", "Word")
    for slug, label in LABELS.items():
        Word.objects.filter(slug=slug, yolo_label=label).update(yolo_label="")


class Migration(migrations.Migration):
    dependencies = [("vocab", "0006_word_candidate")]

    operations = [migrations.RunPython(forwards, backwards)]
