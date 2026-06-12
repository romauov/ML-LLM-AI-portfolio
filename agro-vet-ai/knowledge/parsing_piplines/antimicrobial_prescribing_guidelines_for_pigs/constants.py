import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

SOURCE_DOCUMENT = "Antimicrobial prescribing guidelines for pigs"
KNOWLEDGE_PATH = 'knowledge/data/antimicrobial_prescribing_guidelines_for_pigs'
JSON_BOOK = os.path.join(
    PROJECT_ROOT,
    KNOWLEDGE_PATH,
    f'antimicrobial-prescribing-guidelines-for-pigs книга.json'
)

IMAGES_PATH = os.path.join(KNOWLEDGE_PATH, 'parsed_images')

EXCLUDED_PAGES = [*range(0, 9), *range(55, 60)]
CHAPTERS = {
    (9, 13): 'Core principles of appropriate use of antimicrobial agents',
    (13, 26): '1. Antimicrobial stewardship guidelines for veterinarians working with pigs',
    (26, 29): '2. Lameness in neonatal pigs in the first week of life',
    (29, 35): '3. Diseases where the main clinical sign is diarrhoea in newborn pigs up to four days of age',
    (35, 38): '4. Diseases where the main clinical sign is diarrhoea from five days of age until weaning',
    (38, 44): '5. Diseases where the main clinical sign is diarrhoea after weaning',
    (44, 48): '6. Diseases where the main clinical sign is coughing',
    (48, 52): '7. Diseases where the main clinical sign is sudden death in pigs between weaning and ten weeks of age',
    (52, 55): '8. Diseases where the main clinical signs are skin lesions',
}
