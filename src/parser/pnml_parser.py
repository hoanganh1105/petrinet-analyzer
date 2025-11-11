import xml.etree.ElementTree as ET
from collections import defaultdict


import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

def draw_petri_net(pn, marking=None, figsize=(10, 7), title="Petri Net Visualization (Enhanced)"):
    if marking is None:
        marking = pn.M0

    G = nx.DiGraph()

    # Add nodes & edges
    for pid in pn.places:
        G.add_node(pid, type='place')
    for tid in pn.transitions:
        G.add_node(tid, type='trans')
    for arc in pn.arcs:
        G.add_edge(arc.source, arc.target)

    # Compute layout
    # Gán thuộc tính subset cho từng node
    for n in G.nodes:
        G.nodes[n]["subset"] = 0 if n in pn.places else 1

# Sau đó gọi layout bình thường
    pos = nx.multipartite_layout(G, subset_key="subset")

    # Adjust position spread
    for k, v in pos.items():
        pos[k] = (v[0], v[1]*2.5)

    plt.figure(figsize=figsize)
    ax = plt.gca()
    plt.title(title, fontsize=16, fontweight='bold', pad=20)

    # Draw edges
    nx.draw_networkx_edges(G, pos, arrowstyle='-|>', arrowsize=20, width=2.0, edge_color='gray')

    # Draw places
    place_nodes = [p for p in pn.places]
    place_labels = {p: f"{pn.places[p].name}\n({marking[pn.place_index[p]]})" for p in place_nodes}
    nx.draw_networkx_nodes(G, pos, nodelist=place_nodes,
                           node_color="#89CFF0", node_size=1800,
                           edgecolors='black', linewidths=1.8, node_shape='o')
    nx.draw_networkx_labels(G, pos, labels=place_labels, font_size=10, font_weight='bold')

    # Draw transitions
    trans_nodes = [t for t in pn.transitions]
    trans_labels = {t: pn.transitions[t].name for t in trans_nodes}
    nx.draw_networkx_nodes(G, pos, nodelist=trans_nodes,
                           node_color="#FFA500", node_size=1200,
                           edgecolors='black', linewidths=1.8, node_shape='s')
    nx.draw_networkx_labels(G, pos, labels=trans_labels, font_size=10, font_weight='bold')

    # Legend
    legend_p = mpatches.Patch(color="#89CFF0", label="Places (circles)")
    legend_t = mpatches.Patch(color="#FFA500", label="Transitions (squares)")
    plt.legend(handles=[legend_p, legend_t], loc="lower center", bbox_to_anchor=(0.5, -0.08),
               ncol=2, frameon=False, fontsize=10)

    plt.axis('off')
    plt.tight_layout()
    plt.show()




def local_name(elem):
    """Return tag without namespace."""
    return elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag

class Place:
    def __init__(self, id, name, initial_marking=0):
        self.id = id
        self.name = name
        self.marking = int(initial_marking)

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
        # raw dicts keyed by id
        self.places = {}        # id -> Place
        self.transitions = {}   # id -> Transition
        self.arcs = []          # list of Arc

        # derived (populated by finalize())
        self.place_index = {}   # place_id -> idx (0..n-1)
        self.trans_index = {}   # trans_id -> idx (0..m-1)
        self.index_place = {}   # idx -> place_id
        self.index_trans = {}   # idx -> trans_id

        self.M0 = tuple()       # initial marking as tuple of ints length n
        self.Pre = []           # list length m; each is set of place indices (pre-set)
        self.Post = []          # list length m; each is set of place indices (post-set)

    def finalize(self, check_1safe=True):
        """Build indices and Pre/Post arrays. Optionally check 1-safeness assumption."""
        # build indices
        self.place_index = {pid: i for i, pid in enumerate(sorted(self.places.keys()))}
        self.index_place = {i: pid for pid, i in self.place_index.items()}
        self.trans_index = {tid: i for i, tid in enumerate(sorted(self.transitions.keys()))}
        self.index_trans = {i: tid for tid, i in self.trans_index.items()}

        n = len(self.place_index)
        m = len(self.trans_index)
        # initial marking vector (tuple)
        M0_list = [0]*n
        for pid, p in self.places.items():
            idx = self.place_index[pid]
            M0_list[idx] = int(p.marking)
        self.M0 = tuple(M0_list)

        # build Pre/Post as sets of place indices
        self.Pre = [set() for _ in range(m)]
        self.Post = [set() for _ in range(m)]
        for arc in self.arcs:
            src = arc.source
            tgt = arc.target
            # if arc from place -> transition
            if src in self.place_index and tgt in self.trans_index:
                pidx = self.place_index[src]
                tidx = self.trans_index[tgt]
                self.Pre[tidx].add(pidx)
            # if arc from transition -> place
            elif src in self.trans_index and tgt in self.place_index:
                tidx = self.trans_index[src]
                pidx = self.place_index[tgt]
                self.Post[tidx].add(pidx)
            else:
                # this should have been caught earlier by verify
                pass

        if check_1safe:
            # quick 1-safe check on initial marking (only)
            if any(x not in (0,1) for x in self.M0):
                print("⚠️ Warning: initial marking is not 0/1 for some places (not 1-safe at start).")

    def places_count(self):
        return len(self.place_index)

    def trans_count(self):
        return len(self.trans_index)

    def enabled(self, trans_idx, marking):
        """Check if transition index trans_idx is enabled at marking (tuple/list)."""
        # for 1-safe: enabled iff all pre places have token == 1
        pre = self.Pre[trans_idx]
        for p in pre:
            if marking[p] == 0:
                return False
        return True

    def fire(self, trans_idx, marking):
        """Return new marking (tuple) firing trans_idx from marking. Does not modify inputs."""
        post = self.Post[trans_idx]
        pre = self.Pre[trans_idx]
        new = list(marking)
        # remove tokens from pre-set (for P/T nets with weight=1)
        for p in pre:
            new[p] -= 1
            # keep non-negative
            if new[p] < 0:
                raise ValueError("Firing produced negative token count")
        for p in post:
            new[p] += 1
        return tuple(new)

    def get_enabled_transitions(self, marking):
        """Return list of transition indices enabled at marking."""
        return [t for t in range(self.trans_count()) if self.enabled(t, marking)]

def read_pnml(filename):
    tree = ET.parse(filename)
    root = tree.getroot()

    # find first net element (namespace-agnostic)
    net = None
    for elem in root.iter():
        if local_name(elem) == 'net':
            net = elem
            break
    if net is None:
        raise ValueError("No <net> element found in PNML")

    pn = PetriNet()

    # collect places, transitions, arcs
    for elem in net:
        tag = local_name(elem)
        if tag == 'place':
            pid = elem.get('id')
            # name
            name_text = pid
            name_elem = elem.find('./{*}name') or elem.find('name')
            if name_elem is not None:
                txt = name_elem.find('./{*}text') or name_elem.find('text')
                if txt is not None and txt.text is not None:
                    name_text = txt.text.strip()
            # initial marking
            marking = 0
            marking_elem = elem.find('./{*}initialMarking') or elem.find('initialMarking')
            if marking_elem is not None:
                txt = marking_elem.find('./{*}text') or marking_elem.find('text')
                if txt is not None and txt.text is not None:
                    try:
                        marking = int(txt.text.strip())
                    except:
                        marking = 0
            if pid in pn.places:
                raise ValueError(f"Duplicate place id {pid}")
            pn.places[pid] = Place(pid, name_text, marking)

        elif tag == 'transition':
            tid = elem.get('id')
            name_text = tid
            name_elem = elem.find('./{*}name') or elem.find('name')
            if name_elem is not None:
                txt = name_elem.find('./{*}text') or name_elem.find('text')
                if txt is not None and txt.text is not None:
                    name_text = txt.text.strip()
            if tid in pn.transitions:
                raise ValueError(f"Duplicate transition id {tid}")
            pn.transitions[tid] = Transition(tid, name_text)

        elif tag == 'arc':
            aid = elem.get('id')
            src = elem.get('source')
            tgt = elem.get('target')
            if aid is None or src is None or tgt is None:
                raise ValueError(f"Malformed arc element: missing id/source/target")
            pn.arcs.append(Arc(aid, src, tgt))
        else:
            # ignore other tags (toolspecific, etc.)
            pass

    # verify arcs refer to known nodes
    valid_nodes = set(list(pn.places.keys()) + list(pn.transitions.keys()))
    for arc in pn.arcs:
        if arc.source not in valid_nodes:
            raise ValueError(f"Arc {arc.id} has source {arc.source} which does not exist")
        if arc.target not in valid_nodes:
            raise ValueError(f"Arc {arc.id} has target {arc.target} which does not exist")

    # finalize derived structures
    pn.finalize(check_1safe=True)
    return pn

# ---------------- Example usage ----------------
if __name__ == "__main__":
    pn = read_pnml("test1.pnml")
    print("places:", pn.places_count(), "transitions:", pn.trans_count())
    print("M0:", pn.M0)
    draw_petri_net(pn, marking=pn.M0, title="Example Petri Net (initial marking)")

