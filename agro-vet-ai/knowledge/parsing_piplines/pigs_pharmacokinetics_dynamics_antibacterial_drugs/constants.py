import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

SOURCE_DOCUMENT = (
    "Examination of the pharmacokinetic/pharmacodynamic relationships of orally administered antimicrobials and "
    "their correlation with the therapy of various bacterial and mycoplasmal infections in pigs"
)
KNOWLEDGE_PATH = 'knowledge/data/pigs_pharmacokinetics_dynamics_antibacterial_drugs'
JSON_BOOK = os.path.join(
    PROJECT_ROOT,
    KNOWLEDGE_PATH,
    f'{SOURCE_DOCUMENT}.json'
)

IMAGES_PATH = os.path.join(
    PROJECT_ROOT,
    KNOWLEDGE_PATH,
    f'parsed_images'
)
EXCLUDED_PAGES = [*range(1, 15), *range(130, 145)]
CHAPTERS = {
    (15, 34): 'Chapter 1. Antimicrobial use in pigs and their pharmacokinetic / pharmacodynamic (PK/PD) relationships',
    (34, 77): 'Chapter 2. PK/PD relationship analysis and integration for respiratory infections',
    (77, 127): 'Chapter 3. PK/PD integration for enteric diseases',
    (127, 130): 'Chapter 4. Overall Conclusions and Discussion',
}
