def update_gdoc(pdf_items: dict[str, dict[str, any]], config: dict[str, any]) -> None:
    """Take the set of charts and text extracted from the PDF and insert it
    into the Google Doc.
    """

    # Debug stand-in code
    for team, i in pdf_items.items():
        for dashboard, j in i.items():
            for name, content in j["images"].items():
                print(f"{team} {dashboard} {name}:  {content.width}x{content.height}")
            for k, text in enumerate(j["text"]):
                print(f"{team} {dashboard} text blob #{k}:  {len(text)} characters")
