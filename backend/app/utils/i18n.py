"""
Multilingual disease name mappings
"""
from app.config import settings
from app.logging_config import get_logger

logger = get_logger("utils.i18n")

DISEASE_NAMES = {
    "en": {
        "apple_scab": "Apple Scab",
        "black_rot": "Black Rot",
        "cedar_apple_rust": "Cedar Apple Rust",
        "powdery_mildew": "Powdery Mildew",
        "healthy_apple": "Healthy Apple",
        "other": "Other"
    },
    "hi": {
        "apple_scab": "सेब का दाग",
        "black_rot": "काला सड़न",
        "cedar_apple_rust": "देवदार सेब रस्ट",
        "powdery_mildew": "पाउडरी फफूंद",
        "healthy_apple": "स्वस्थ सेब",
        "other": "अन्य"
    }
}

DISEASE_DESCRIPTIONS = {
    "en": {
        "apple_scab": "Dark olive-green to black velvety spots on leaves",
        "black_rot": "Purple-ringed lesions or frog-eye patterns on leaves",
        "cedar_apple_rust": "Bright orange or yellow spots on upper leaf surface",
        "powdery_mildew": "Dusty white-to-light-gray powdery fungal coating",
        "healthy_apple": "Pristine, unblemished foliage with clean vein structures",
        "other": "Background elements, weeds, or non-target vegetation"
    },
    "hi": {
        "apple_scab": "पत्तियों पर गहरे जैतूनी-हरे से काले मखमली धब्बे",
        "black_rot": "पत्तियों पर बैंगनी छल्ले वाले घाव या मेंढक-आंख पैटर्न",
        "cedar_apple_rust": "पत्ती की ऊपरी सतह पर चमकीले नारंगी या पीले धब्बे",
        "powdery_mildew": "धूल भरी सफेद से हल्के भूरे रंग की फफूंदी परत",
        "healthy_apple": "स्वच्छ शिरा संरचनाओं वाली निर्दोष पत्तियां",
        "other": "पृष्ठभूमि तत्व, खरपतवार, या गैर-लक्षित वनस्पति"
    }
}

def get_disease_name(class_name: str, lang: str = "en") -> str:
    return DISEASE_NAMES.get(lang, DISEASE_NAMES["en"]).get(class_name, class_name)

def get_disease_description(class_name: str, lang: str = "en") -> str:
    return DISEASE_DESCRIPTIONS.get(lang, DISEASE_DESCRIPTIONS["en"]).get(class_name, "")

def get_all_names(lang: str = "en") -> dict:
    return DISEASE_NAMES.get(lang, DISEASE_NAMES["en"])
