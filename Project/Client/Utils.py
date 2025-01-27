#utils.py

Commands =  ["USER", "PASS", "ACCT", "CWD", "CDUP",
                "SMNT", "REIN", "QUIT", "PORT", "PASV",
                "TYPE", "STRU", "MODE", "LIST", "RETR", "STOR"
                "STOU", "APPE", "ALLO", "REST", "RNFR",
                "RNTO", "ABOR", "DELE", "RMD", "MKD",
                "PWD", "NLST", "SITE", "SYST",
                "STAT", "HELP", "NOOP",]

def levenshtein_distance(s1, s2):
    if len(s1) == 0:
        return len(s2)
    if len(s2) == 0:
        return len(s1)
    if s1[0] == s2[0]:
        return levenshtein_distance(s1[1:], s2[1:])
    
    insert_cost = levenshtein_distance(s1, s2[1:])
    delete_cost = levenshtein_distance(s1[1:], s2)
    replace_cost = levenshtein_distance(s1[1:], s2[1:])
    
    return 1 + min(insert_cost, delete_cost, replace_cost)

def Calculate_Lev(command):
    lev = 1000000000000
    sug = ""
    for c in Commands:
        newLev = levenshtein_distance(c, command)
        if newLev < lev:
            lev = newLev
            sug = c
    return sug
