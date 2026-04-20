from ..models import PresetConfig, SocialTier

# --- GLOBALE REGELN FÜR ZEITREISE-PRESETS ---
# Diese Regeln gelten automatisch für alle Presets in dieser Datei.
TIME_PORTAL_GLOBAL_FORBIDDEN = [
    # Technologie & Material
    "Zippers", "Velcro", "Plastic", "Nylon", "Polyester", "Rubber soles",
    "Wristwatches", "Glasses", "Modern jewelry", "Machine stitching",
    
    # Ästhetik & Haare
    "Modern hairstyles", "Pixie cut", "Bob cut", "Fade cut", "Messy bun", 
    "Hairspray look", "Makeup contouring", "Lip gloss", "Botox face",
    
    # Bild-Stil
    "Sepia", "Vintage filter", "Film grain overlay", "Vignette", 
    "Ruins (unless specified)", "Museum display"
]

presets = {
    "Steinzeit": PresetConfig(
        name="Paleolithic Era (Time Portal)", 
        version="3.0-Tiered",
        preset_intent="Capture the raw Stone Age. NO WOVEN FABRIC. NO METAL. Clothing is raw animal hide/fur only.",
        recommended_use="Jäger & Sammler. Authentische Darstellung ohne Zivilisation.",
        camera="Fujifilm GFX 100S", 
        lens="50mm f/1.4", 
        film_stock="Digital RAW", 
        lighting="Natural Light or Firelight",
        capture_profile={"Style": "Documentary Realism"},
        global_forbidden=["Woven Fabric", "Metal", "Agriculture", "Roads", "Modern Teeth"],
        default_tier="hunter",
        social_tiers=[
            SocialTier(
                tier_id="hunter", 
                keywords=["hunter", "gatherer", "jäger", "sammler", "frau", "mann"], 
                description="A standard member of a hunter-gatherer tribe.",
                textiles=["Raw, untanned animal hides with fur", "Leather thongs"], 
                colors=["Natural brown, grey, white"],
                headwear=["None", "Simple bone/feather ornaments"], 
                footwear=["Barefoot", "Simple hide wrappings"],
                props=["Flint spearhead", "Wooden spear", "Bone needle", "Stone axe"], 
                locations=["Cave entrance", "Forest", "Rocky outcrop"],
                forbidden=[]
            )
        ]
    ),

    "Altes Ägypten": PresetConfig(
        name="Ancient Egypt (Time Portal)", 
        version="2.0-Tiered",
        preset_intent="Capture authentic life in Ancient Egypt (New Kingdom), adapting to social class.",
        recommended_use="Alltag am Nil. Beschreibe den Status (Bauer, Priester, Pharao).",
        camera="Hasselblad H6D-100c", 
        lens="80mm f/2.8", 
        film_stock="Digital RAW", 
        lighting="Harsh Desert Sun or Oil Lamps",
        capture_profile={"Style": "Documentary"},
        global_forbidden=["Ruins", "Camels", "Iron/Steel", "Cotton", "Silk", "Modern Hairstyles"],
        default_tier="commoner",
        social_tiers=[
            SocialTier(
                tier_id="commoner", 
                keywords=["commoner", "peasant", "farmer", "worker", "craftsman", "bauer", "arbeiter"], 
                description="A poor worker or farmer by the Nile.",
                textiles=["Coarse, undyed (off-white) linen"], 
                colors=["Natural beige"],
                headwear=["Shaved head", "Simple linen head-cloth"], 
                footwear=["Barefoot", "Reed sandals"],
                props=["Clay pottery", "Reed baskets", "Wooden farming tools"], 
                locations=["Mudbrick village", "Fields by the Nile"],
                forbidden=["Gold", "Lapis Lazuli", "Fine pleated linen"]
            ),
            SocialTier(
                tier_id="noble", 
                keywords=["noble", "priest", "priestess", "pharaoh", "queen", "adel", "priester", "pharao"], 
                description="A high-status individual in a temple or palace.",
                textiles=["Fine, pleated white linen", "Sheer fabrics"], 
                colors=["White, with accents of blue, red"],
                headwear=["Heavy black braided wig", "Royal headdress"], 
                footwear=["Elaborate sandals"],
                props=["Gold Usekh collar", "Lapis Lazuli jewelry", "Bronze mirror"], 
                locations=["Polished stone temple", "Throne room"],
                forbidden=["Mud", "Farming tools"]
            )
        ]
    ),

    "Altes Rom": PresetConfig(
        name="Ancient Rome (Time Portal)", 
        version="3.0-Tiered",
        preset_intent="Capture authentic life in Imperial Rome, adapting to social class. NO FANTASY LEATHER.",
        recommended_use="Straßen, Senat, Alltag. Beschreibe den Status (Bürger, Senator, Soldat).",
        camera="Leica SL2", 
        lens="50mm f/0.95", 
        film_stock="Digital RAW", 
        lighting="Harsh Sun or Oil Lamps",
        capture_profile={"Style": "Street/Documentary"},
        global_forbidden=["Ruins", "Modern Italy", "Fantasy Armor", "Knitted Fabric"],
        default_tier="plebeian",
        social_tiers=[
            SocialTier(
                tier_id="plebeian", 
                keywords=["plebeian", "citizen", "worker", "craftsman", "bürger", "arbeiter"], 
                description="A common citizen in the bustling, dirty streets of Rome.",
                textiles=["Coarse wool tunic"], 
                colors=["Undyed off-white, earth tones"],
                headwear=["None"], 
                footwear=["Leather sandals (caligae)"],
                props=["Clay amphorae", "Woven baskets", "Simple tools"], 
                locations=["Crowded market street", "Insulae apartments"],
                forbidden=["Toga", "Purple cloth", "Silk"]
            ),
            SocialTier(
                tier_id="patrician", 
                keywords=["patrician", "senator", "noble", "patrizier"], 
                description="A wealthy patrician or senator in a formal setting.",
                textiles=["Fine wool toga", "Linen undertunic"], 
                colors=["White, with purple stripe (toga praetexta)"],
                headwear=["None"], 
                footwear=["Fine leather sandals"],
                props=["Papyrus scrolls", "Marble busts", "Mosaic floors"], 
                locations=["Marble villa", "Senate house (Curia)"],
                forbidden=["Peasant tools", "Mudbrick"]
            ),
            SocialTier(
                tier_id="legionary", 
                keywords=["legionary", "soldier", "centurion", "legionär", "soldat"], 
                description="A Roman legionary soldier on duty.",
                textiles=["Wool tunic (red)"], 
                colors=["Red, brown"],
                headwear=["Iron helmet (galea)"], 
                footwear=["Hobnailed sandals (caligae)"],
                props=["Segmented armor (lorica segmentata)", "Shield (scutum)", "Short sword (gladius)"], 
                locations=["Fortress wall", "Marching on a stone road"],
                forbidden=["Toga", "Civilian life props"]
            )
        ]
    ),

    "Altes Griechenland": PresetConfig(
        name="Ancient Greece (Time Portal)", 
        version="3.0-Tiered",
        preset_intent="Capture authentic life in Classical Greece, adapting to social class. POLYCHROMY (painted world).",
        recommended_use="Agora, Tempel, Schlachtfeld. Beschreibe den Status (Bürger, Philosoph, Hoplit).",
        camera="Hasselblad X2D 100C", 
        lens="50mm f/1.8", 
        film_stock="Digital RAW", 
        lighting="Harsh Attic Light",
        capture_profile={"Style": "Documentary"},
        global_forbidden=["Ruins", "White marble statues", "Steel", "Medieval armor"],
        default_tier="citizen",
        social_tiers=[
            SocialTier(
                tier_id="citizen", 
                keywords=["citizen", "philosopher", "orator", "bürger", "philosoph"], 
                description="A citizen or philosopher in public life.",
                textiles=["Linen or light wool chiton/himation"], 
                colors=["White, saffron, light blue"],
                headwear=["None"], 
                footwear=["Barefoot", "Simple leather sandals"],
                props=["Papyrus scrolls", "Walking stick", "Clay kylix (cup)"], 
                locations=["Agora (market)", "Painted stoa"],
                forbidden=["Armor", "Weapons"]
            ),
            SocialTier(
                tier_id="hoplite", 
                keywords=["hoplite", "soldier", "spartan", "soldat"], 
                description="A hoplite soldier in formation.",
                textiles=["Linen tunic (linothorax reinforcement)"], 
                colors=["Red, white"],
                headwear=["Bronze Corinthian helmet"], 
                footwear=["Leather sandals"],
                props=["Bronze cuirass", "Round shield (Hoplon)", "Long spear (Dory)"], 
                locations=["Battlefield", "Phalanx formation"],
                forbidden=["Toga", "Scrolls"]
            )
        ]
    ),

    "Mittelalter": PresetConfig(
        name="High Middle Ages (Time Portal)", 
        version="2.0-Tiered",
        preset_intent="Capture authentic life in High Middle Ages (c. 1250, N. Europe), adapting to social class.",
        recommended_use="Dörfer, Höfe, Schlachten. Beschreibe den Status (Bauer, Ritter, König).",
        camera="Sony A7S III", 
        lens="50mm f/1.2", 
        film_stock="Digital RAW", 
        lighting="Natural/Candlelight",
        capture_profile={"Style": "Gritty Documentary"},
        global_forbidden=["Plate Armor (anachronistic)", "Fantasy elements", "Cleanliness", "Modern boots", "Modern belt buckles", "Factory-made belts"],
        default_tier="peasant",
        social_tiers=[
            SocialTier(
                tier_id="peasant", 
                keywords=["peasant", "farmer", "craftsman", "bauer", "handwerker"], 
                description="A peasant or craftsman in a muddy village.",
                textiles=["Coarse wool tunic", "Linen undertunic"], 
                colors=["Undyed, earth tones"],
                headwear=["Linen coif or hood"], 
                footwear=["Leather turnshoes"],
                props=["Wooden bucket", "Iron tools", "Clay pottery", "Simple leather belt (tied, no buckle)"], 
                locations=["Muddy village street", "Thatched-roof hut"],
                forbidden=["Silk", "Velvet", "Crowns", "Swords", "Metal buckles"]
            ),
            SocialTier(
                tier_id="noble", 
                keywords=["noble", "knight", "king", "queen", "adel", "ritter", "könig", "herrscher", "königin"], 
                description="A noble or knight at court or in the field.",
                textiles=["Fine wool, silk trim, velvet, fur"], 
                colors=["Vibrant plant/insect dyes (red, blue)"],
                headwear=["Circlet", "Linen veil (women)"], 
                footwear=["Pointed leather shoes"],
                props=["Sword", "Tapestries", "Gold goblet", "Chainmail hauberk", "Leather belt with historical ring buckle"], 
                locations=["Stone castle interior", "Tournament field"],
                forbidden=["Farming tools", "Mudbrick huts", "Modern belt buckles"]
            )
        ]
    )
}
