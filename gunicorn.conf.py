# Lido automaticamente pelo gunicorn ("gunicorn app:app" no Render).
# A análise da foto do prato pelo Gemini pode demorar mais de 30 s
# (o limite por omissão do gunicorn), por isso subimos para 60 s.
timeout = 60
