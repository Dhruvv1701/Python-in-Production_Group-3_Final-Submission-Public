def valid_ppr_connection(G, s, t):

    type_s = G.nodes[s]["type"].strip().lower()
    type_t = G.nodes[t]["type"].strip().lower()

    return (
            (type_s == "product" and type_t == "process") or
            (type_s == "process" and type_t == "product") or
            (type_s == "resource" and type_t == "process")
    )