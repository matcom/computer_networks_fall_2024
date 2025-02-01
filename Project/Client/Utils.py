#utils.py

Commands =  ["USER", "PASS", "ACCT", "CWD", "CDUP","SMNT", "REIN", "QUIT", "PORT", "PASV",
"TYPE", "STRU", "MODE", "LIST", "RETR", "STOR", "STOU", "APPE", "ALLO", "REST", "RNFR",
"RNTO", "ABOR", "DELE", "RMD", "MKD", "PWD", "NLST", "SITE", "SYST",
"STAT", "HELP", "NOOP",]

# Método que divide la entrada en command y arg
def recv_cmd(entry):    
    if not entry:
        return None, None
        
    cmd = entry[0].upper()
    args = ' '.join(entry[1:])  # Unir los argumentos en un solo string
        
    return cmd, args

# Método para validar argumentos
def validate_args(cmd , args):
    if not args:
        raise ValueError(f"Error: No arguments provided for the command {cmd}.")

# Calcular distancia de levenshtein
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

# Devuelve el comando mas parecido al ingresado
def Get_suggestion(command):
    lev = 1000000000000
    sug = ""
    for c in Commands:
        newLev = levenshtein_distance(c, command)
        if newLev < lev:
            lev = newLev
            sug = c
    return sug
