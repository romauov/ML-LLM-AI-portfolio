import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

SOURCE_DOCUMENT = (
    "Poultry_Health_A_Guide_for_Professionals_2021"
)
KNOWLEDGE_PATH = 'knowledge/data/poultry_health_guide'
JSON_BOOK = os.path.join(
    PROJECT_ROOT,
    KNOWLEDGE_PATH,
    f'{SOURCE_DOCUMENT}.json'
)

IMAGES_PATH = os.path.join(KNOWLEDGE_PATH, 'parsed_images')

EXCLUDED_PAGES = [*range(1, 15), *range(334, 351)]
CHAPTERS = {
    (15, 22): 'Basic Anatomy and Physiology',
    (22, 34): 'The Immune System of the Chicken',
    (34, 39): 'The Genetics of Disease Resistance in Poultry',
    (39, 43): 'The Poultry Industry',
    (43, 49): 'The Broiler Industry and Management of Broilers and Broiler Parents',
    (49, 56): 'The Commercial Layer Industry, Management and Disease',
    (56, 66): 'Backyard (Pet) Poultry',
    (66, 73): 'The Turkey Industry and Disease',
    (73, 80): 'The Duck Industry and Diseases',
    (80, 86): 'Diseases of Gamebirds',
    (86, 93): 'Hatchery Practice',
    (93, 100): 'Feeding Poultry and Potential Problems Associated with Die',
    (100, 106): 'Skeletal Problem', # good
    (106, 109): 'Mycobacterium and Avian Tuberculosis',
    (109, 114): 'Avian Pathogenic Escherichia col',
    (114, 119): 'Campylobacter',
    (119, 126): 'Salmonella',
    (126, 134): 'Clostridium and Necrotic Enteriti',
    (134, 145): 'Pasteurella and Related Organisms',
    (145, 152): 'Brachyspira – Avian Intestinal Spirochaetosis',
    (152, 160): 'Mycoplasmas',
    (160, 164): 'Miscellaneous Bacterial Infections',
    (164, 169): 'Avian Reoviruses – Viral Arthritis',
    (169, 172): 'Infectious Avian Encephalomyelitis',
    (172, 181): 'Adenoviruses',
    (181, 186): 'Infectious Laryngotracheitis',
    (186, 192): 'Infectious Bursal Disease',
    (192, 198): 'Avian Astroviruses',
    (198, 207): 'Avian Influenza',
    (207, 214): 'Newcastle Disease',
    (214, 222): 'Avian Metapneumovirus Infection',
    (222, 229): 'Infectious Bronchitis',
    (229, 237): 'Chicken Anaemia Virus and Circoviruses',
    (237, 241): 'Avian Leukosis and Reticuloendotheliosis',
    (241, 245): 'Marek’s Disease',
    (245, 250): 'Fowlpox',
    (250, 257): 'Coccidiosis',
    (257, 263): 'Histomoniasis (Blackhead Disease)',
    (263, 271): 'Other Important Parasites',
    (271, 277): 'The Chicken Microbiota and How to Modulate It',
    (277, 288): 'Biosecurity',
    (288, 295): 'Poultry Chemotherapy and Antimicrobials',
    (295, 306): 'Vaccination Strategies and Application of Vaccines',
    (306, 311): 'How to Carry Out a Field Investigation',
    (311, 328): 'Laboratory Diagnosis of Poultry Diseases',
    (328, 334): 'Legislation'
}
