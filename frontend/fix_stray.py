content = open("app.js", encoding="utf-8").read()
bad = "}\\n\n// Reviews"
good = "}\n\n// Reviews"
count = content.count(bad)
print(f"Found {count} occurrence(s) of the broken sequence")
if count > 0:
    content = content.replace(bad, good)
    open("app.js", "w", encoding="utf-8").write(content)
    print("app.js: fixed")
