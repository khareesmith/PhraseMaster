import random
from typing import List

ADJECTIVES: List[str] = [
    "Adventurous", "Amusing", "Artistic", "Athletic", "Bold", "Blissful", "Brave", "Bright",
    "Brilliant", "Calm", "Careful", "Charming", "Cheerful", "Clever", "Compassionate", "Confident",
    "Considerate", "Courageous", "Creative", "Curious", "Daring", "Dedicated", "Defiant", "Dependable",
    "Determined", "Diligent", "Dreamy", "Eager", "Efficient", "Energetic", "Enchanting", "Enthusiastic",
    "Faithful", "Fabulous", "Fearless", "Focused", "Friendly", "Funky", "Funny", "Generous", "Gentle",
    "Genuine", "Gleeful", "Gracious", "Grateful", "Gregarious", "Handy", "Harmonic", "Harmonious", "Helpful",
    "Heroic", "Hilarious", "Honest", "Humble", "Idealistic", "Imaginative", "Impossible", "Independent",
    "Inquisitive", "Insightful", "Inspiring", "Intuitive", "Inventive", "Jolly", "Joyful", "Joyous", "Jovial",
    "Jubilant", "Keen", "Kind", "Kindhearted", "Knowledgeable", "Legendary", "Lively", "Loyal", "Luminous",
    "Magical", "Magnetic", "Merry", "Mighty", "Modest", "Mystic", "Neighborly", "Nimble", "Noble", "Nurturing",
    "Observant", "Open-minded", "Optimistic", "Organized", "Passionate", "Patient", "Peaceful", "Perceptive",
    "Playful", "Popular", "Protective", "Quick", "Quick-witted", "Quirky", "Radiant", "Resilient", "Resourceful",
    "Savvy", "Sassy", "Sincere", "Sleepy", "Smart", "Spirited", "Super", "Talented", "Thoughtful", "Tough",
    "Trustworthy", "Understanding", "Unique", "Upbeat", "Valiant", "Vibrant", "Vigorous", "Whimsical", "Wise",
    "Witty", "Wonderful", "Wacky", "Xtreme", "Youthful", "Zealous", "Zany", "Ambitious", "Authentic", "Balanced",
    "Blissful", "Breezy", "Bubbly", "Capable", "Chill", "Confident", "Considerate", "Crafty", "Dynamic",
    "Earnest", "Empowered", "Enlightened", "Exquisite", "Fascinating", "Fearless", "Festive", "Fortunate",
    "Gentle", "Gracious", "Hardworking", "Harmonious", "Heartfelt", "Impressive", "Ingenious", "Intuitive",
    "Luminous", "Magnificent", "Mindful", "Noble", "Nurturing", "Outstanding", "Persistent", "Philosophical",
    "Plucky", "Proactive", "Radiant", "Reliable", "Remarkable", "Respectful", "Scholarly", "Sociable",
    "Stellar", "Strategic", "Strong", "Supportive", "Tactful", "Tenacious", "Trailblazing", "Trustworthy",
    "Unstoppable", "Versatile", "Visionary", "Warmhearted", "Welcoming", "Well-rounded", "Winsome"
    ]

NOUNS: List[str] = [
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

# Generate a random username
def generate_random_username() -> str:
    """
    Generate a random username using a combination of adjectives and nouns.

    Returns:
        str: A randomly generated username.

    Note:
        This function can generate at least 40,000 unique usernames.
    """
    return f"{random.choice(ADJECTIVES)} {random.choice(NOUNS)}"

# Generate a list of three random usernames
def generate_random_usernames(count: int = 3) -> List[str]:
    """
    Generate a list of unique random usernames.

    Args:
        count (int, optional): The number of unique usernames to generate. Defaults to 3.

    Returns:
        List[str]: A list of unique randomly generated usernames.

    Raises:
        ValueError: If count is greater than the number of possible unique combinations.
    """
    max_combinations = len(ADJECTIVES) * len(NOUNS)
    if count > max_combinations:
        raise ValueError(f"Cannot generate {count} unique usernames. Maximum is {max_combinations}.")

    usernames = set()
    while len(usernames) < count:
        usernames.add(generate_random_username())
    return list(usernames)