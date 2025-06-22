## @file protocol.py
# @brief Hilfsfunktionen für das SLCP-Protokoll.

def escape(param):
    """! Escaped Leerzeichen in einem Parameter.
    @param param Der zu escapende Parameter.
    @return Der escapete Parameter.
    """
    return param.replace(' ', '\\ ')

def unescape(param):
    """! Unescaped Leerzeichen in einem Parameter.
    @param param Der zu unescapende Parameter.
    @return Der unescapete Parameter.
    """
    return param.replace('\\ ', ' ')

def parse_message(message):
    """! Parst eine Nachricht und berücksichtigt dabei escapete Leerzeichen.
    @param message Die zu parsende Nachricht.
    @return Eine Liste der Parameter.
    """
    params = []
    current_param = ""
    i = 0
    while i < len(message):
        if message[i] == '\\' and i + 1 < len(message) and message[i+1] == ' ':
            current_param += ' '
            i += 2
        elif message[i] == ' ':
            params.append(current_param)
            current_param = ""
            i += 1
        else:
            current_param += message[i]
            i += 1
    params.append(current_param)
    return params