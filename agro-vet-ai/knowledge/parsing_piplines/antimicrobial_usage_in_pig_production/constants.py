import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

SOURCE_DOCUMENT = "antimicrobial usage in pig production"
KNOWLEDGE_PATH = 'knowledge/data/antimicrobial_usage_in_pig_production'
JSON_BOOK = os.path.join(
    PROJECT_ROOT,
    KNOWLEDGE_PATH,
    f'ANTIMICROBIAL USAGE IN PIG PRODUCTION.json'
)

IMAGES_PATH = os.path.join(KNOWLEDGE_PATH, 'parsed_images')

EXCLUDED_PAGES = [*range(0, 14), *range(244, 306)]
CHAPTERS = {
    (15, 23): 'Pig production and antimicrobial usage',
    (23, 30): 'Check: Quantifying antimicrobial usage',
    (30, 49): 'Improve: Herd management & biosecurity',
    (49, 53): 'Reduce: Action & psychology',
    (70, 72): 'Scientific Aims',
    (72, 115): 'Assigning Defined Daily Doses Animal: A European multi-country experience for antimicrobial products authorized for usage in pigs',
    (119, 139): 'Alternatives to the use of antimicrobial agents in pig production: a multi-country expert-ranking of perceived effectiveness',
    (145, 170): 'The biosecurity status and its associations with production and management characteristics in farrow- to-finish pig herds',
    (173, 192): 'Evaluation of the relationship between the biosecurity status, production parameters, herd characteristics and antimicrobial usage in farrow-to-finish pig production in four EU countries',
    (197, 221): 'Reducing antimicrobial usage in pig production without jeopardizing production parameters',
    (225, 228): 'Antimicrobial usage in pig production: Belgium versus EU',
    (228, 233): 'The way forward: Antimicrobial usage quantification',
    (233, 241): 'The way forward: Biosecurity & Herd management',
    (241, 244): 'The way forward: Coaching',
}
