MESSAGES = {
    "es": {
        "user_prompt":             "Tú: ",
        "agent_reply":             "\n{agent} ({role}): {reply}\n",
        "startup":                 "{agent} se encuentra activo. Escribe '{exit_cmd}' para terminar la sesion. Como puedo ayudarte hoy?",
        "exit_command":            "salir",
        "confirm_yes":             "si",
        "model_error":             "{agent}: Error al obtener respuesta del modelo: {error}",
        "analyzing_memory":        "\n{agent}: Analizando la conversacion para actualizar la memoria...\n",
        "invalid_model_response":  "{agent}: Respuesta del modelo invalida - {error}. No se actualizo la memoria.",
        "proposed_facts":          "{agent}: Hechos nuevos detectados:\n\n{facts}\n",
        "retire_facts_header":     "{agent}: Hechos a retirar:",
        "confirm_changes":         "{agent}: Confirmas estos cambios? (si/no): ",
        "memory_updated":          "{agent}: Memoria actualizada.",
        "no_changes":              "{agent}: No se realizaron actualizaciones en la memoria.",
        "ask_name":                "{agent}: Por favor escribe que nombre quieres que use para referirme a ti: ",
        "language_detected":       "{agent}: Detecté que prefieres comunicarte en español. ¿Correcto? (si/no): ",
        "language_confirmed":      "{agent}: Perfecto, me comunicaré contigo en español.",
        "language_ask":            "{agent}: ¿En qué idioma prefieres comunicarte? (es/en): ",
        "onboarding_done":         "{agent}: Disculpa {name}, ahora sí, ¿cómo puedo ayudarte hoy?",
        "ask_location":            "{agent}: Para poder darte un mejor apoyo, ¿podrías confirmarme en qué ciudad estás ubicado, por favor? ",
        "ask_location_clarify":    "{agent}: Esa ciudad existe en varios lugares. ¿En qué país o región está, por favor? ",
        "memory_anomaly_notice":   "\n{agent}: Nota — detecté un patrón inusual en la conversación (demasiados cambios de memoria propuestos a la vez) y no guardé nada por seguridad.",
    },
    "en": {
        "user_prompt":             "You: ",
        "agent_reply":             "\n{agent} ({role}): {reply}\n",
        "startup":                 "{agent} is active. Type '{exit_cmd}' to end the session. How can I help you today?",
        "exit_command":            "exit",
        "confirm_yes":             "yes",
        "model_error":             "{agent}: Error getting response from model: {error}",
        "analyzing_memory":        "\n{agent}: Analyzing conversation to update memory...\n",
        "invalid_model_response":  "{agent}: Invalid model response - {error}. Memory not updated.",
        "proposed_facts":          "{agent}: New facts detected:\n\n{facts}\n",
        "retire_facts_header":     "{agent}: Facts to retire:",
        "confirm_changes":         "{agent}: Confirm these changes? (yes/no): ",
        "memory_updated":          "{agent}: Memory updated.",
        "no_changes":              "{agent}: No memory updates were made.",
        "ask_name":                "{agent}: Please write down the name you'd like me to use when referring to you: ",
        "language_detected":       "{agent}: I detected you prefer communicating in English. Correct? (yes/no): ",
        "language_confirmed":      "{agent}: Got it, I will communicate with you in English.",
        "language_ask":            "{agent}: What language do you prefer? (es/en): ",
        "onboarding_done":         "{agent}: Sorry about that, {name}. Now, how can I help you today?",
        "ask_location":            "{agent}: To support you better, could you please confirm which city you're located in? ",
        "ask_location_clarify":    "{agent}: That city exists in several places. Which country or region is it in, please? ",
        "memory_anomaly_notice":   "\n{agent}: Note — I detected an unusual pattern in the conversation (too many memory changes proposed at once) and saved nothing, as a precaution.",
    },
}

# Localized day/month names for datetime formatting. Maintained manually while supported languages <= 3. If languages grow beyond 3, replace with the `babel` library (pip install babel) which uses the Unicode CLDR database and eliminates manual maintenance.
WEEKDAYS = {
    "es": ["lunes","martes","miércoles","jueves","viernes","sábado","domingo"],
    "en": ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"],
}
MONTHS = {
    "es": ["enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre"],
    "en": ["January","February","March","April","May","June","July","August","September","October","November","December"],
}

def msg(key, language, **kwargs):
    return MESSAGES[language][key].format(**kwargs)