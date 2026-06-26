import config

MESSAGES = {
    "es": {
        "user_prompt":   "Tú: ",
        "agent_reply":   "\n{agent} ({role}): {reply}\n",
        "startup":                 "{agent} activo. Escribe '{exit_cmd}' para terminar.",
        "exit_command":            "salir",
        "confirm_yes":             "si",
        "model_error":             "{agent}: Error al obtener respuesta del modelo: {error}",
        "analyzing_memory":        "\n{agent}: Analizando la conversacion para actualizar la memoria...\n",
        "invalid_model_response":  "{agent}: Respuesta del modelo invalida - {error}. No se actualizo la memoria.",
        "proposed_facts":          "{agent}: Hechos nuevos detectados:\n\n{facts}\n",
        "retire_facts_header":     "Hechos a retirar:",
        "confirm_changes":         "Confirmas estos cambios? (si/no): ",
        "memory_updated":          "{agent}: Memoria actualizada.",
        "no_changes":              "{agent}: No se realizaron actualizaciones en la memoria.",
    },
    "en": {
        "user_prompt":   "You: ",
        "agent_reply":   "\n{agent} ({role}): {reply}\n",
        "startup":                 "{agent} active. Type '{exit_cmd}' to quit.",
        "exit_command":            "exit",
        "confirm_yes":             "yes",
        "model_error":             "{agent}: Error getting response from model: {error}",
        "analyzing_memory":        "\n{agent}: Analyzing conversation to update memory...\n",
        "invalid_model_response":  "{agent}: Invalid model response - {error}. Memory not updated.",
        "proposed_facts":          "{agent}: New facts detected:\n\n{facts}\n",
        "retire_facts_header":     "Facts to retire:",
        "confirm_changes":         "Confirm these changes? (yes/no): ",
        "memory_updated":          "{agent}: Memory updated.",
        "no_changes":              "{agent}: No memory updates were made.",
    },
}

def msg(key, **kwargs):
    return MESSAGES[config.LANGUAGE][key].format(**kwargs)
