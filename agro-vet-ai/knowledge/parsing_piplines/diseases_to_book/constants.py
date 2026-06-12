import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

AVIAN_PATH = os.path.join(PROJECT_ROOT, 'knowledge/data/avian_diseases/list')
AVIAN_IMAGES_PATH = os.path.join(AVIAN_PATH, 'parsed_images')
AVIAN_DOCUMENT_NAME = "Сборник: Болезни птиц"
AVIAN_CONTENTS = [
    'Инфекционный бронхит птиц, Avian Infectious Bronchitis (IB), Infectious Bronchitis',
    'Птичий грипп, Avian Influenza (AI), Highly Pathogenic Avian Influenza (HPAI)',
    'Инфекция метапневмовируса птиц, Avian Metapneumovirus Infection, Turkey Rhinotracheitis Virus (TRTV)',
    'Вирусная инфекция анемии цыплят, Chicken Anemia Virus Infection (CAV), Infectious Anemia of Chickens',
    'Кокцидиоз птиц, Coccidiosis, Avian Coccidiosis',
    'Инфекционная бурсальная болезнь, Infectious Bursal Disease (IBD), Gumboro Disease',
    'Инфекционная кориза птиц, Infectious Coryza, Avibacterium paragallinarum Infection',
    'Инфекционный ларинготрахеит, Infectious Laryngotracheitis (ILT), Avian Laryngotracheitis',
    'Микоплазмоз птиц, Mycoplasmosis, Chronic Respiratory Disease (CRD)',
    'Ньюкаслская болезнь, Newcastle Disease (ND), Avian Paramyxovirus Type 1 Infection',
    'Реовирусная инфекция птиц, Reoviral Infection, Avian Reovirus Infection',
]

SWINE_PATH = os.path.join(PROJECT_ROOT, 'knowledge/data/swine_diseases/source')
SWINE_IMAGES_PATH = os.path.join(SWINE_PATH, 'parsed_images')
SWINE_DOCUMENT_NAME = "Сборник: Болезни свиней"
