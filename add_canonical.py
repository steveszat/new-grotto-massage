import os

BASE_URL = "https://newgrottomassage.com"

for file in os.listdir("."):
    if file.endswith(".html"):
        path = os.path.join(".", file)

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        # Skip if already has canonical
        if 'rel="canonical"' in content:
            continue

        url = BASE_URL + ("/" if file == "index.html" else f"/{file}")

        canonical_tag = f'    <link rel="canonical" href="{url}" />\n'

        content = content.replace("</head>", canonical_tag + "</head>")

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

print("Done.")