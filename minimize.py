from xml.etree import ElementTree as ET
from collections import defaultdict

LIMIT = 3

def prune_global(elem, counts):
    for child in list(elem):
        t = child.tag
        counts[t] += 1
        if counts[t] > LIMIT:
            elem.remove(child)
        else:
            prune_global(child, counts)

tree = ET.parse("eskisehir.net.xml")
root = tree.getroot()
prune_global(root, defaultdict(int))
tree.write("output.net.xml", encoding="utf-8", xml_declaration=True)
