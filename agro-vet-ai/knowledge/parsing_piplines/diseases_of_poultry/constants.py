import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

SOURCE_DOCUMENT = 'Diseases of Poultry'
KNOWLEDGE_PATH = 'knowledge/data/diseases_of_poultry'
JSON_BOOK_1 = os.path.join(
    PROJECT_ROOT,
    KNOWLEDGE_PATH,
    'Diseases_of_Poultry_14th_Edition_part_1.json'
)
JSON_BOOK_2 = os.path.join(
    PROJECT_ROOT,
    KNOWLEDGE_PATH,
    'Diseases_of_Poultry_14th_Edition_part_2.json'
)

IMAGES_PATH = os.path.join(KNOWLEDGE_PATH, 'parsed_images')

EXCLUDED_PAGES = [
    *range(0, 30),
    *range(96, 106),  # references
    *range(126, 136),  # references
    *range(171, 194),  # references
    *range(209, 216),  # references
    *range(232, 237),  # references
    *range(271, 284),  # references
    *range(301, 311),  # references
    *range(335, 348),  # references
    *range(380, 391),  # references
    *range(407, 409),  # references
    *range(424, 428),  # references
    *range(460, 473),  # references
    *range(513, 525),  # references
    *range(562, 575),  # references
    *range(686, 743),  # references
    *range(766, 781),  # references
    *range(792, 797),  # references
    *range(837, 858),  # references
    *range(900, 917),  # references
    *range(929, 934),  # references
    *range(968, 993),  # references
    *range(1014, 1022),  # references
    *range(1084, 1113),  # references
    *range(1130, 1135),  # references
    *range(1158, 1161),  # references
    *range(1184, 1184),  # references
    *range(1217, 1219),  # references
    *range(1271, 1282),  # references
    *range(1311, 1313),  # references
    *range(1343, 1357),  # references
    *range(1373, 1376),  # references
    *range(1399, 1410),  # references
    *range(1429, 1438),  # references
    *range(1438, 1452)
]

CHAPTERS = {
    (3, 79): '1 Principles of Disease Prevention, Diagnosis, and Control',
    (79, 109): '2 Host Factors for Disease Resistance',
    (109, 167): '3 Newcastle Disease, Other Avian Paramyxoviruses, and Avian Metapneumovirus Infections',
    (167, 189): '4 Infectious Bronchitis',
    (189, 210): '5 Infectious Laryngotracheitis',
    (210, 257): '6 Influenza',
    (257, 284): '7 Infectious Bursal Disease',
    (284, 321): '8 Chicken Infectious Anemia and Circovirus Infections in Commercial Flocks',
    (321, 364): '9 Adenovirus Infections',
    (364, 382): '10 Pox',
    (382, 401): '11 Avian Reovirus Infections',
    (401, 446): '12 Viral Enteric Infections',
    (446, 498): '13 Viral Infections of Waterfowl',
    (498, 548): '14 Other Viral Infections',
    (548, 719): '15 Neoplastic Diseases',
    (719, 754): '16 Salmonella Infections',
    (754, 770): '17 Campylobacteriosis',
    (770, 831): '18 Colibacillosis',
    (831, 890): '19 Pasteurellosis and Other Respiratory Bacterial Infections',
    (890, 907): '20 Infectious Coryza and Related Bacterial Infections',
    (907, 966): '21 Mycoplasmosis',
    (966, 995): '22 Clostridial Diseases',
    (995, 1086): '23 Other Bacterial Diseases',
    (1086, 1111): '24 Avian Chlamydiosis',
    (1111, 1137): '25 Fungal Infections',
    (1137, 1157): '26 External Parasites and Poultry Pests',
    (1157, 1192): '27 Internal Parasites',
    (1192, 1257): '28 Protozoal Infections',
    (1257, 1286): '29 Nutritional Diseases',
    (1286, 1330): '30 Developmental, Metabolic, and Other Noninfectious Disorders',
    (1330, 1349): '31 Mycotoxicoses',
    (1349, 1385): '32 Toxins and Poisons',
    (1385, 1452): '33 Emerging Diseases and Diseases of Complex or Unknown Etiology',
}
