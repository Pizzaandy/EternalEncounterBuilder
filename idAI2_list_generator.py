from entities_parser import *

fp = 'randomizer_example.txt'
segments = generate_entity_segments(fp, "idAI2")
output_str = ""
names_str = ""
filter_list = ["masterlevel", "_ai_", "cinematic"]
entity_count = 0
for seg in segments:
    name = ""
    new_name = ""
    skip_segment = False
    for line in seg.splitlines():
        if "entityDef" in line:
            name = line.replace("{", "").replace("entityDef","").strip()
            if name.startswith(tuple(filter_list)):
                skip_segment = True
            new_name = "custom" + name.rstrip("0123456789_").lstrip("gameplay").lstrip("game")
            seg = seg.replace(name, new_name, 1)
            break
    if skip_segment:
        continue
    if name == "":
        print("No entityDef found!")
    if new_name and new_name in names_str:
        continue
    names_str += "// " + new_name + "\n"
    output_str += seg + "\n"
    entity_count += 1

output_str = f"// Automatically added {entity_count} idAI2 entities from the base game:\n\n" + names_str + "\n" + output_str
output_file = open("idAI2_base.txt", "w")
output_file.write(output_str)
output_file.close()

print(names_str)