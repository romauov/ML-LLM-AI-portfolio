import os
import json

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

SOURCE_DOCUMENT = (
    "Ravindra Nath Sharma - Avian Pathology 2020"
)
KNOWLEDGE_PATH = 'knowledge/data/avian_pathology'
JSON_BOOK = os.path.join(
    PROJECT_ROOT,
    KNOWLEDGE_PATH,
    f'{SOURCE_DOCUMENT}.json'
)

IMAGES_PATH = os.path.join(KNOWLEDGE_PATH, 'parsed_images')

CHAPTERS = {
    (37, 41): 'Taxonomy of Avian Species',
    (41, 46): 'Immunity and Inflammation in Birds',
    (49, 57): 'Avian Salmonellosis',
    (57, 61): 'Paratyphoid Infections',
    (61, 63): 'Arizonosis',
    (63, 73): 'Avian Mycoplasmosis',
    (73, 81): 'Colibacillosis / Escherichia Coli Infections',
    (81, 84): 'Fowl Cholera',
    (85, 87): 'Riemerella Anatipestifer Infection',
    (87, 89): 'Erysipelas',
    (89, 90): 'Yersinia Pseudotuberculosis (Pasteurella Pseudotuberculosis)',
    (91, 94): 'Campylobacter Infections',
    (95, 97): 'Spirochetosis',
    (97, 99): 'Avian Intestinal Spirochetosis',
    (99, 103): 'Clostridial Infections',
    (103, 105): 'Infectious Coryza (Fowl Coryza)',
    (105, 107): 'Ornithobacterium Rhinotracheale Infection',
    (107, 109): 'Bardetellosis (Turkey Coryza)',
    (109, 112): 'Mycobacteriosis',
    (113, 118): 'Chlamydiosis',
    (119, 121): 'Omphalitis (Navel ill, Mushy chick disease)',
    (121, 123): 'Staphylococcosis',
    (123, 125): 'Streptococcus',
    (125, 127): 'Enterococcosis',
    (129, 135): 'Newcastle Disease (ND; Avian Pneumoencephalitis)',
    (135, 138): 'Pneumovirus Infections',
    (139, 143): 'Infectious Laryngotracheitis (Laryngotracheitis, ILT; LT)',
    (143, 153): 'Infectious Anemia (Chicken Anemia Agent [CAA] infection)',
    (153, 154): 'Adenovirus Infections of Chickens',
    (155, 157): 'Quail Bronchitis (QB)',
    (157, 160): 'Inclusion Body Hepatitis (IBH; Adenoviral Infection)',
    (161, 162): 'Hydropericardium Syndrome (HS)',
    (163, 166): 'EGG Drop Syndrome 1976 (EDS 76)',
    (167, 170): 'Viral Arthritis',
    (171, 175): 'Fowl Pox (Pox; Avian Pox)',
    (175, 180): 'Infectious Bursal Disease (IBD; Gumboro Disease)',
    (181, 188): 'Marek’s Disease',
    (189, 194): 'Avian Leukosis (LL) (Lymphoid Leukosis, LL)',
    (195, 197): 'Myelocytomatosis',
    (197, 199): 'Reticuloendotheliosis',
    (199, 201): 'Avian Nephritis',
    (201, 205): 'Avian Influenza (AI; Influenza; Fowl Plague)',
    (205, 208): 'Avian Encephalomyelitis',
    (209, 211): 'Coronaviral Enteritis of Turkeys (CVE) (Blue comb disease, mud fever, transmissible enteritis, infectious enteritis)',
    (211, 213): 'Hemorrhagic Enteritis of Turkeys (HE; BLOODY GUT)',
    (213, 216): 'Duck Virus Enteritis (DVE, Duck Plague)',
    (217, 221): 'Duck Virus Hepatitis (DVH)',
    (221, 224): 'Eastern Equine Encephalitis (Eee) Virus Infection',
    (224, 227): 'West Nile Virus (WNV)',
    (229, 232): 'Aspergillosis (Brooder pneumonia)',
    (233, 235): 'Candidiasis (Thrush; Mycosis of Digestive Tract)',
    (235, 237): 'Cryptococcosis',
    (237, 238): 'Dermatophytosis (FAVUS)',
    (239, 241): 'Mycotoxicosis',
    (243, 252): 'Coccidiosis',
    (252, 255): 'Cryptosporidiosis',
    (255, 257): 'Histomoniasis (Black Head; Enterohepatitis)',
    (257, 259): 'Trichomoniasis',
    (259, 261): 'Toxoplasmosis',
    (261, 263): 'Nematodes (Round Worms)',
    (263, 265): 'Tapeworms (Cestodes)',
    (265, 267): 'Blood Borne Parasite',
    (267, 271): 'Ectoparasites',
    (273, 278): 'Vitamin Deficiency',
    (279, 282): 'Mineral Deficiency',
    (285, 286): 'Bumble Foot (Pododermatitis/ Planter absces)',
    (287, 288): 'Cage Layer Fatigue (Osteoporosis)',
    (289, 290): 'Stunting Runting Syndrome',
    (291, 293): 'Ascites Syndrome (Water belly, Right ventricular failure, Hypertension syndrome)',
    (293, 294): 'Hypoglycemia-Spiking Mortality Syndrome of Broiler Chickens (HSMS)',
    (295, 296): 'Proventricular Dilatation of Broiler Chickens',
    (297, 301): 'Round Heart Disease of Chickens and Turkeys (Dilated cardiomyopathy)'
}

# ===== EXCLUDED_PAGES ===== 
_included_pages = set()
for (start, end) in CHAPTERS.keys():
    _included_pages.update(range(start, end))

_all_pages = set(range(1, 306))

EXCLUDED_PAGES = sorted(_all_pages - _included_pages)

# ===== IMAGE PAGES =====
_image_pages = []
with open(JSON_BOOK, 'r', encoding='utf-8') as f:
    data = json.load(f)

for i in range(len(data['pages'])):
    page_index = data['pages'][i]['index']
    markdown_text = data['pages'][i].get('markdown', '')

    # Проверяем наличие "Fig." или "Fig ." в тексте
    if 'Fig.' in markdown_text or 'Fig ' in markdown_text:
        _image_pages.append(page_index + 1)

IMAGE_PAGES = sorted(set(_image_pages))