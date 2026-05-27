def recall_project_structure():
    content = None
    with open("./assets/strucuture.md", "r", encoding="utf-8") as f:
        content = f.read()

    if content is not None:
        return content
