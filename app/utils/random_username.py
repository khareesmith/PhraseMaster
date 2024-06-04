import random

def generate_random_username():
    """
    Generate a random username using a combination of adjectives and nouns.
    """
    adjectives = [
        "Sassy", "Mystic", "Jolly", "Brave", "Wonderful", "Popular", "Adventurous",
        "Observant", "Sleepy", "Defiant", "Handy", "Gentle", "Smart", "Fabulous",
        "Impossible", "Wacky", "Helpful", "Mighty", "Super", "Tough", "Cheerful",
        "Clever", "Daring", "Eager", "Faithful", "Gleeful", "Heroic", "Inventive",
        "Jovial", "Kind", "Lively", "Merry", "Noble", "Optimistic", "Playful",
        "Quick", "Radiant", "Sincere", "Talented", "Upbeat", "Vibrant", "Wise",
        "Youthful", "Zany", "Brilliant", "Charming", "Diligent", "Enthusiastic",
        "Friendly", "Generous", "Humble", "Imaginative", "Joyful", "Keen", "Luminous",
        "Modest", "Nurturing", "Observant", "Patient", "Quirky", "Resilient",
        "Spirited", "Trustworthy", "Unique", "Valiant", "Witty",
        "Bright", "Curious", "Determined", "Energetic", "Fearless", "Gracious",
        "Hilarious", "Insightful", "Jubilant", "Kindhearted", "Loyal", "Magnetic",
        "Nimble", "Optimistic", "Passionate", "Quick-witted", "Resourceful", "Savvy",
        "Thoughtful", "Understanding", "Vigorous", "Whimsical", "Xtreme", "Youthful",
        "Zealous", "Courageous", "Dependable", "Efficient", "Funky", "Genuine", "Harmonic",
        "Amusing", "Blissful", "Calm", "Creative", "Dreamy", "Enchanting", "Exuberant",
        "Fearless", "Funny", "Grateful", "Harmonious", "Idealistic", "Inspiring", "Joyous",
        "Knowledgeable", "Legendary", "Magical", "Neighborly", "Open-minded", "Peaceful", 
        "Artistic", "Athletic", "Bold", "Careful", "Compassionate", "Confident", "Considerate",
        "Curious", "Dedicated", "Empathetic", "Faithful", "Focused", "Gentle", "Gregarious",
        "Honest", "Helpful", "Independent", "Inquisitive", "Intuitive", "Kind", "Loyal",
        "Meticulous", "Nurturing", "Organized", "Patient", "Perceptive", "Playful", "Protective"
    ]

    nouns = [
        "Banana", "Muffin", "Penguin", "Dragon", "Pizza", "Airplane", "Moon",
        "Cowboy", "Jacket", "Mountain", "Hill", "Pencil", "Tree", "Lightbulb",
        "Cookie", "Hot Dog", "Quesadilla", "Robot", "Guitar", "Flute", "Tiger",
        "Galaxy", "Wizard", "Unicorn", "Rocket", "Lion", "Tornado", "Phoenix",
        "Cactus", "Glacier", "Volcano", "Zeppelin", "Sphinx", "Octopus",
        "Mushroom", "Bison", "Kangaroo", "Parrot", "Butterfly", "Chameleon", "Narwhal",
        "Sailboat", "Rainbow", "Comet", "Nebula", "Squirrel", "Hamster", "Alligator",
        "Koala", "Wombat", "Starfish", "Mermaid", "Sundial", "Windmill", "Yeti",
        "Panda", "Owl", "Firefly", "Panther", "Sunflower", "Asteroid", "Cheetah",
        "Hedgehog", "Jellyfish", "Turtle", "Seahorse", "Dolphin", "Llama", "Giraffe",
        "Kite", "Bicycle", "Castle", "Suitcase", "Car", "Boat", "Train", "Flower",
        "Bridge", "Building", "Camera", "Dinosaur", "Feather", "Globe", "Hat", "Igloo",
        "Jungle", "Kangaroo", "Laptop", "Microphone", "Necklace", "Ocean", "Piano",
        "Quilt", "Robot", "Spaceship", "Telephone", "Umbrella", "Vase", "Whistle",
        "Xylophone", "Yacht", "Zebra", "Airship", "Backpack", "Compass", "Drum",
        "Easel", "Flag", "Glasses", "Headphones", "Island", "Joystick", "Kettle",
        "Lantern", "Map", "Notebook", "Orchid", "Paintbrush", "Quicksand", "Rhinoceros",
        "Skateboard", "Trampoline", "Ukulele", "Volleyball", "Waterfall", "Xylophone",
        "Yogurt", "Zipper", "Anvil", "Barrel", "Clock", "Dumbbell", "Egg", "Fork",
        "Gong", "Harp", "Ink","Lemon", "Magnet", "Olive",
        "Pickle", "Quiver", "Racket", "Saxophone", "Toaster", "Ukelele", "Violin",
        "Wrench", "X-ray", "Yo-yo", "Zigzag", "Comet", "Cloud", "Galaxy", "Star",
        "Planet", "Meteor", "Voyager", "Explorer", "Albatross", "Badger", "Cat", "Dog",
        "Elephant", "Falcon", "Gorilla", "Hawk", "Iguana", "Jaguar", "Koala", "Leopard",
        "Manatee", "Narwhal", "Otter", "Panther","Raccoon", "Squirrel", "Tiger", "Vulture",
        "Walrus", "Xenopus", "Yak", "Zebra", "Apple", "Blueberry", "Carrot", "Donut", "Eggplant",
        "Fig", "Grape", "Honeydew", "Ice Cream", "Jelly", "Kiwi", "Lemon", "Mango", "Nectarine",
        "Orange", "Peach", "Raspberry", "Strawberry", "Tangerine","Vanilla", "Watermelon",
        "Yam", "Zucchini", "Aurora", "Blossom", "Creek", "Dawn", "Earth", "Forest", "Grove",
        "Horizon", "Iceberg", "Jungle", "Kelp", "Lagoon", "Mountain", "Nest", "Oasis", "Prairie",
        "Quartz", "River", "Sky", "Tree", "Undergrowth", "Vine", "Waterfall", "Xeric",
        "Yarrow", "Zenith"
    ]
    
    random_username = random.choice(adjectives) + " " + random.choice(nouns)
    return random_username

def generate_random_usernames():
    """
    Generate a list of three random usernames.
    """
    random_usernames = [generate_random_username() for _ in range(3)]
    return random_usernames