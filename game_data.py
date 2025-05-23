# List of valid races and origins
valid_races = ["Human", "Orc", "Naiad", "Elf", "Dwarf", "Maithar", "Urthar"]
valid_origins = ["Lowborn", "Highborn", "Rural", "Marauder"]
valid_actions = ["Attack", "Flee"] # Note: This might be combat specific, consider if it belongs elsewhere or is general enough.
valid_star_signs = ["Aegis", "Seraph", "Eclipse", "Lumos", "Verdant", "Tempest", "Solstice", "Nexus", "Ember", "Astral"]

# Random name lists for character generation
random_names = {
    "Human": {
        "male": ["Aldric", "Gareth", "Theron", "Marcus", "Cedric", "Dorian", "Lysander", "Cassius", "Tristan", "Roderick"],
        "female": ["Lyanna", "Seraphina", "Cordelia", "Evangeline", "Rosalind", "Isadora", "Vivienne", "Celeste", "Aurelia", "Morgana"],
        "neutral": ["Rynn", "Sage", "River", "Phoenix", "Rowan", "Quinn", "Ash", "Vale", "Storm", "Ember"]
    },
    "Elf": {
        "male": ["Aelindra", "Thalorin", "Silvyr", "Caelum", "Elowen", "Fenris", "Galion", "Ithilien", "Legolas", "Nimrodel"],
        "female": ["Arwen", "Galadriel", "Elaria", "Nimue", "Tauriel", "Celebrian", "Idril", "Luthien", "Melian", "Varda"],
        "neutral": ["Elrond", "Glorfindel", "Lindir", "Erestor", "Haldir", "Orophin", "Rumil", "Thranduil", "Gil-galad", "Elendil"]
    },
    "Dwarf": {
        "male": ["Thorin", "Gimli", "Balin", "Dwalin", "Gloin", "Oin", "Bifur", "Bofur", "Bombur", "Nori"],
        "female": ["Disa", "Mira", "Nala", "Vera", "Kira", "Zara", "Tova", "Hilda", "Brenna", "Freya"],
        "neutral": ["Dain", "Fili", "Kili", "Ori", "Dori", "Fundin", "Groin", "Nain", "Telchar", "Azog"]
    },
    "Orc": {
        "male": ["Grishnak", "Ugluk", "Azog", "Bolg", "Lurtz", "Gothmog", "Gorbag", "Shagrat", "Snaga", "Mauhur"],
        "female": ["Grasha", "Urka", "Morghul", "Nazga", "Burzum", "Ghash", "Skarr", "Vex", "Grimm", "Thok"],
        "neutral": ["Saruman", "Sauron", "Morgoth", "Balrog", "Witch-king", "Mouth", "Lieutenant", "Captain", "Chieftain", "Warlord"]
    },
    "Naiad": {
        "male": ["Nereon", "Triton", "Oceanus", "Poseidon", "Proteus", "Glaucus", "Phorcys", "Pontus", "Aegaeon", "Thaumas"],
        "female": ["Thetis", "Amphitrite", "Galatea", "Nereid", "Oceanid", "Naiad", "Undine", "Siren", "Mermaid", "Selkie"],
        "neutral": ["Aqua", "Marina", "Coral", "Pearl", "Tide", "Wave", "Current", "Depth", "Flow", "Drift"]
    },
    "Maithar": {
        "male": ["Kael", "Zephyr", "Orion", "Atlas", "Phoenix", "Draco", "Vega", "Sirius", "Altair", "Rigel"],
        "female": ["Lyra", "Nova", "Stella", "Luna", "Vega", "Andromeda", "Cassiopeia", "Bellatrix", "Electra", "Mira"],
        "neutral": ["Cosmos", "Nebula", "Quasar", "Pulsar", "Comet", "Meteor", "Galaxy", "Starlight", "Void", "Infinity"]
    },
    "Urthar": {
        "male": ["Ragnar", "Bjorn", "Erik", "Olaf", "Gunnar", "Leif", "Sven", "Thor", "Odin", "Freyr"],
        "female": ["Astrid", "Ingrid", "Sigrid", "Helga", "Brunhilde", "Freydis", "Gudrun", "Ragnhild", "Solveig", "Thora"],
        "neutral": ["Raven", "Wolf", "Bear", "Frost", "Storm", "Thunder", "Lightning", "Ice", "Snow", "Winter"]
    }
}