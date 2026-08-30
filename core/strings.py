MESSAGES = {
    "es": {
        "user_prompt":             "Tú: ",
        "agent_reply":             "\n{agent} ({role}): {reply}\n",
        "startup":                 "{agent} se encuentra activo. Escribe '{exit_cmd}' para terminar la sesion. Como puedo ayudarte hoy?",
        "exit_command":            "salir",
        "model_error":             "{agent}: Ocurrió un error al procesar tu mensaje. Por favor intenta de nuevo.",
        "ask_name":                "{agent}: Por favor escribe que nombre quieres que use para referirme a ti.",
        "language_detected":       "{agent}: Detecté que prefieres comunicarte en español. ¿Es correcto?",
        "language_confirmed":      "{agent}: Perfecto, me comunicaré contigo en español.",
        "language_ask":            "{agent}: ¿En qué idioma prefieres comunicarte?",
        "ask_name_or_code":        "Veo que no habíamos hablado antes. Si ya me usas en otro canal, pega aquí tu código de vinculación. Si no, empecemos: ¿qué nombre quieres que use para referirme a ti?",
        "link_success":            "{agent}: ¡Listo, {name}! Este canal quedó vinculado a tu perfil, así que sigo con todo lo que ya sabía de ti. ¿En qué te ayudo?",
        "link_failed":             "{agent}: Ese código no es válido o ya venció. Puedes pegar uno nuevo, o si prefieres empezar de cero dime qué nombre quieres que use.",
        "onboarding_done":         "{agent}: Disculpa {name}, ahora sí, ¿cómo puedo ayudarte hoy?",
        "ask_location":            "{agent}: Para poder darte un mejor apoyo, ¿podrías confirmarme en qué ciudad y país estás ubicado, por favor?",
        "ask_location_clarify":    "{agent}: Esa ciudad existe en varios lugares. ¿En qué país o región está, por favor?",
        "confirm_profile":         "{agent}: Perfecto, esto es lo que tengo de ti antes de crear tu perfil:\nA. Nombre: {name}\nB. Ubicación: {city} (zona horaria {timezone})\nSi algo no está bien, dime la letra y lo corregimos. Si todo está correcto, lo guardo así.",
        "service_unavailable":     "{agent}: Al parecer el servicio no está disponible en este momento, así que no puedo continuar con tu registro. Por favor inténtalo de nuevo en unos 5 minutos.",
        "message_too_long":        "Tu mensaje es demasiado largo (máximo {limit} caracteres). ¿Podrías acortarlo, por favor?",
        "rate_limited":            "Estás enviando mensajes demasiado rápido. Por favor espera un momento antes de continuar.",
        "send_failed":             "Al parecer se presentaron problemas con el envío de mensajes. Si quieres puedes enviar tu mensaje de nuevo.",
        "audio_transcript":        "🎙️ {text}",
        "audio_too_long":          "Ese audio es muy largo (máximo {minutes} minutos). ¿Podrías enviarme uno más corto, por favor?",
        "audio_failed":            "Tuve un problema técnico y no pude procesar ese audio. ¿Puedes intentarlo de nuevo, por favor?",
        "audio_no_speech":         "No escuché nada en ese audio. ¿Puedes grabarlo de nuevo o escribírmelo?",
        "account_deactivated":     "Hola. Tu cuenta se encuentra suspendida y por eso no puedo seguir respondiendo tus mensajes. Tu información se borrará de forma definitiva el {deadline}. Si cambiaste de opinión, escribe al administrador de {agent} antes de esa fecha para restaurar tu acceso.",
    },
    "en": {
        "user_prompt":             "You: ",
        "agent_reply":             "\n{agent} ({role}): {reply}\n",
        "startup":                 "{agent} is active. Type '{exit_cmd}' to end the session. How can I help you today?",
        "exit_command":            "exit",
        "model_error":             "{agent}: An error occurred while processing your message. Please try again.",
        "ask_name":                "{agent}: Please write down the name you'd like me to use when referring to you.",
        "language_detected":       "{agent}: I detected you prefer communicating in English. Is that correct?",
        "language_confirmed":      "{agent}: Got it, I will communicate with you in English.",
        "language_ask":            "{agent}: What language do you prefer?",
        "ask_name_or_code":        "I see we haven't talked before. If you already use me on another channel, paste your link code here. If not, let's start: what name would you like me to use for you?",
        "link_success":            "{agent}: All set, {name}! This channel is now linked to your profile, so I keep everything I already knew about you. How can I help?",
        "link_failed":             "{agent}: That code is not valid or has expired. You can paste a new one, or if you'd rather start fresh, tell me the name you'd like me to use.",
        "onboarding_done":         "{agent}: Sorry about that, {name}. Now, how can I help you today?",
        "ask_location":            "{agent}: To support you better, could you please confirm which city and country you're located in?",
        "ask_location_clarify":    "{agent}: That city exists in several places. Which country or region is it in, please?",
        "confirm_profile":         "{agent}: Great, this is what I have about you before creating your profile:\nA. Name: {name}\nB. Location: {city} (timezone {timezone})\nIf something is wrong, tell me the letter and we'll fix it. If everything is right, I'll save it as is.",
        "service_unavailable":     "{agent}: The service seems to be unavailable right now, so I can't continue with your registration. Please try again in about 5 minutes.",
        "message_too_long":        "Your message is too long (maximum {limit} characters). Could you please shorten it?",
        "rate_limited":            "You're sending messages too quickly. Please wait a moment before continuing.",
        "send_failed":             "It seems there were problems sending the messages. If you want, you can send your message again.",
        "audio_transcript":        "🎙️ {text}",
        "audio_too_long":          "That audio is too long (maximum {minutes} minutes). Could you send me a shorter one, please?",
        "audio_failed":            "I had a technical problem and could not process that audio. Could you try again, please?",
        "audio_no_speech":         "I didn't hear anything in that audio. Can you record it again or write it to me?",
        "account_deactivated":     "Hello. Your account is suspended, so I can't keep answering your messages. Your information will be permanently erased on {deadline}. If you changed your mind, write to the administrator of {agent} before that date to restore your access.",
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