import xml.etree.ElementTree as ET

class Place:
    def __init__(self, id, name, initial_marking=0):
        self.id = id
        self.name = name
        self.marking = initial_marking

class Transition:
    def __init__(self, id, name):
        self.id = id
        self.name = name

class Arc:
    def __init__(self, id, source, target):
        self.id = id
        self.source = source
        self.target = target

class PetriNet:
    def __init__(self):
        self.places = {}
        self.transitions = {}
        self.arcs = []

def read_pnml(filename):
    tree = ET.parse(filename)
    root = tree.getroot()
    net = root.find('net')
    pn = PetriNet()

    # Đọc các places
    for place_elem in net.findall('place'):
        pid = place_elem.get('id')
        
        name_elem = place_elem.find('name')
        name_text = name_elem.find('text').text if name_elem is not None and name_elem.find('text') is not None else pid
        
        marking_elem = place_elem.find('initialMarking')
        marking_text = marking_elem.find('text').text if marking_elem is not None and marking_elem.find('text') is not None else '0'
        
        pn.places[pid] = Place(pid, name_text, int(marking_text))

    # Đọc các transitions
    for trans_elem in net.findall('transition'):
        tid = trans_elem.get('id')
        name_elem = trans_elem.find('name')
        name_text = name_elem.find('text').text if name_elem is not None and name_elem.find('text') is not None else tid
        pn.transitions[tid] = Transition(tid, name_text)

    # Đọc các arcs
    for arc_elem in net.findall('arc'):
        aid = arc_elem.get('id')
        src = arc_elem.get('source')
        tgt = arc_elem.get('target')
        pn.arcs.append(Arc(aid, src, tgt))

    return pn

def verify_petri_net(pn):
    valid_nodes = set(pn.places.keys()) | set(pn.transitions.keys())
    for arc in pn.arcs:
        if arc.source not in valid_nodes:
            print(f"❌ Lỗi: arc {arc.id} có source {arc.source} không tồn tại")
        if arc.target not in valid_nodes:
            print(f"❌ Lỗi: arc {arc.id} có target {arc.target} không tồn tại")

def print_petri_net(pn):
    print("Places:")
    for p in pn.places.values():
        print(f"  {p.id} ({p.name}) - initial tokens: {p.marking}")

    print("\nTransitions:")
    for t in pn.transitions.values():
        print(f"  {t.id} ({t.name})")

    print("\nArcs:")
    for a in pn.arcs:
        print(f"  {a.id}: {a.source} -> {a.target}")

if __name__ == "__main__":
    pn = read_pnml("example.pnml")
    verify_petri_net(pn)
    print_petri_net(pn)
