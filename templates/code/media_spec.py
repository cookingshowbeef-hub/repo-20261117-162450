"""Where the pictures come from.

BROLL: stock-video searches, run one set at a time with `doc.py <prj> search <set>`; vet the contact sheets by eye, then
`doc.py <prj> pick px:123="what it shows" ...` and `doc.py <prj> fetch`. Search for what the LINE says, not for the place name alone:
"wheelbarrow", "boiling water thrown in freezing air", "chalk writing on a blackboard".
TOPICS: Wikimedia Commons photos, `doc.py <prj> commons`. Each topic: ([queries], how many to keep, must-mention regex, min width).
A photo is kept only if its title, description or categories match the regex, so a picture can't be passed off as the place.
"""

BROLL = {
    "intro": ["night road snow", "headlights fog"],
    "story": ["old typewriter typing", "handwriting old paper"],
}

PLACE = r"place|место"           # names of the film's place in the languages its photos are captioned in

TOPICS = {
    "place": (["Place name", "Place name winter"], 40, PLACE, 1200),
    "person": (["Person name", "Person name portrait"], 10, r"person name", 400),
}
