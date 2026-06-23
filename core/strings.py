import config

MESSAGES = {
    "es": {
        "no_memory_file":         "No se encontró el archivo de memoria.",
        "user_prompt":   "Tú: ",
        "agent_reply":   "\n{agent} ({role}): {reply}\n",
        "startup":                 "{agent} activo. Escribe '{exit_cmd}' para terminar.",
        "exit_command":            "salir",
        "confirm_yes":             "si",
        "model_error":             "{agent}: Error al obtener respuesta del modelo: {error}",
        "memory_file_not_found":   "{agent}: No se encontró el archivo de memoria '{path}'.",
        "analyzing_memory":        "\n{agent}: Analizando la conversacion para actualizar la memoria...\n",
        "invalid_model_response":  "{agent}: Respuesta del modelo invalida - {error}. No se actualizo la memoria.",
        "proposed_changes":        "{agent}: Cambios propuestos en '{section}':\n\n{updates}\n",
        "confirm_changes":         "Confirmas estos cambios? (si/no): ",
        "save_error":              "{agent}: Error al guardar la memoria: {error}",
        "memory_updated":          "{agent}: Memoria actualizada.",
        "no_section":              "{agent}: No se pudo determinar la sección a actualizar.",
        "no_changes":              "{agent}: No se realizaron actualizaciones en la memoria.",
    },
    "en": {
        "no_memory_file":         "Memory file not found.",
        "user_prompt":   "You: ",
        "agent_reply":   "\n{agent} ({role}): {reply}\n",
        "startup":                 "{agent} active. Type '{exit_cmd}' to quit.",
        "exit_command":            "exit",
        "confirm_yes":             "yes",
        "model_error":             "{agent}: Error getting response from model: {error}",
        "memory_file_not_found":   "{agent}: Memory file '{path}' not found.",
        "analyzing_memory":        "\n{agent}: Analyzing conversation to update memory...\n",
        "invalid_model_response":  "{agent}: Invalid model response - {error}. Memory not updated.",
        "proposed_changes":        "{agent}: Proposed changes to '{section}':\n\n{updates}\n",
        "confirm_changes":         "Confirm these changes? (yes/no): ",
        "save_error":              "{agent}: Error saving memory: {error}",
        "memory_updated":          "{agent}: Memory updated.",
        "no_section":              "{agent}: Could not determine which section to update.",
        "no_changes":              "{agent}: No memory updates were made.",
    },
}

def msg(key, **kwargs):
    return MESSAGES[config.LANGUAGE][key].format(**kwargs)
